import requests
import json
import time
from datetime import datetime
from requests.exceptions import RequestException
from functools import wraps
from statistics import mean, StatisticsError

# Constants for API URLs and key
BLOCKDAEMON_URL = "https://svc.blockdaemon.com/ethereum/mainnet/native"
API_KEY = s.getenv("BLOCKDAEMON_API_KEY")
FLASHBOTS_URL = "https://boost-relay.flashbots.net"
ULTRASOUND_URL = "https://relay-analytics.ultrasound.money"

# Rate limiting variable
last_request_time = 0

def rate_limit():
    """Implement rate limiting to avoid exceeding 5 requests per second."""
    global last_request_time
    current_time = time.time()
    if current_time - last_request_time < 0.2:
        time.sleep(0.2 - (current_time - last_request_time))
    last_request_time = time.time()

def retry_on_exception(retries=3, backoff_factor=0.3):
    """Decorator to retry a function on exception with exponential backoff."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return f(*args, **kwargs)
                except RequestException as e:
                    if attempt == retries - 1:
                        raise
                    time.sleep(backoff_factor * (2 ** attempt))
        return wrapper
    return decorator

@retry_on_exception(retries=3)
def get_block_by_number(block_number):
    """Fetch block data from the Blockdaemon API."""
    rate_limit()
    hex_block = hex(block_number)
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getBlockByNumber",
        "params": [hex_block, True]
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(BLOCKDAEMON_URL, params={'apiKey': API_KEY}, headers=headers, json=payload)
    if response.status_code == 200 and 'result' in response.json():
        return response.json()['result']
    return None

@retry_on_exception(retries=3)
def get_builder_blocks_received(relay_url, slot):
    """Fetch builder blocks received data from a relay."""
    rate_limit()
    url = f"{relay_url}/relay/v1/data/bidtraces/builder_blocks_received?slot={slot}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

@retry_on_exception(retries=3)
def get_proposer_payload_delivered(relay_url, slot):
    """Fetch proposer payload delivered data from a relay."""
    rate_limit()
    url = f"{relay_url}/relay/v1/data/bidtraces/proposer_payload_delivered?slot={slot}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

def get_mev_data_for_block(block_number):
    """Fetch MEV data for a given block number from Flashbots and Ultrasound relays."""
    estimated_slot = (block_number - 15537394) * 32 // 12 + 5193071
    flashbots_data = {'builder_blocks': None, 'proposer_payload': None}
    ultrasound_data = {'builder_blocks': None, 'proposer_payload': None}

    try:
        flashbots_data['builder_blocks'] = get_builder_blocks_received(FLASHBOTS_URL, estimated_slot)
        flashbots_data['proposer_payload'] = get_proposer_payload_delivered(FLASHBOTS_URL, estimated_slot)
    except RequestException as e:
        print(f"Error fetching Flashbots data for block {block_number}: {e}")

    try:
        ultrasound_data['builder_blocks'] = get_builder_blocks_received(ULTRASOUND_URL, estimated_slot)
        ultrasound_data['proposer_payload'] = get_proposer_payload_delivered(ULTRASOUND_URL, estimated_slot)
    except RequestException as e:
        print(f"Error fetching Ultrasound data for block {block_number}: {e}")

    return flashbots_data, ultrasound_data

def safe_get(dictionary, *keys):
    """Navigate nested dictionaries to access keys, returning None if any key isn't found."""
    for key in keys:
        try:
            dictionary = dictionary[key]
        except (KeyError, TypeError):
            return None
    return dictionary

def safe_mean(data):
    """Calculate the mean of a dataset, returning 'N/A' if there's not enough data."""
    # Filter out None values
    filtered_data = [x for x in data if x is not None]
    try:
        return mean(filtered_data) if filtered_data else "N/A"
    except StatisticsError:
        return "N/A"

def process_block(block_number):
    """Process a block by its number and enrich it with MEV data and metrics."""
    block_data = get_block_by_number(block_number)
    if not block_data:
        return None

    flashbots_data, ultrasound_data = get_mev_data_for_block(block_number)

    enriched_data = {
        'block_number': block_number,
        'block_hash': block_data['hash'],
        'timestamp': datetime.fromtimestamp(int(block_data['timestamp'], 16)),
        'gas_used': int(block_data['gasUsed'], 16),
        'gas_limit': int(block_data['gasLimit'], 16),
        'transaction_count': len(block_data['transactions']),
    }

    if 'baseFeePerGas' in block_data:
        enriched_data['base_fee_per_gas'] = int(block_data['baseFeePerGas'], 16)
    else:
        enriched_data['base_fee_per_gas'] = None

    all_bids = []
    winning_bid_value = 0
    winning_relay = None

    for relay, data in [('flashbots', flashbots_data), ('ultrasound', ultrasound_data)]:
        if data['builder_blocks']:
            all_bids.extend([int(bid['value'], 16) for bid in data['builder_blocks']])
        if data['proposer_payload']:
            bid_value = int(data['proposer_payload'][0]['value'], 16)
            if bid_value > winning_bid_value:
                winning_bid_value = bid_value
                winning_relay = relay

    if all_bids:
        enriched_data['average_bid'] = sum(all_bids) / len(all_bids)
        enriched_data['max_bid'] = max(all_bids)
        enriched_data['bid_count'] = len(all_bids)
        enriched_data['highest_bid_selected'] = winning_bid_value == enriched_data['max_bid']
    else:
        enriched_data['average_bid'] = None  # Explicitly set to None
        enriched_data['max_bid'] = None      # Explicitly set to None
        enriched_data['bid_count'] = 0
        enriched_data['highest_bid_selected'] = None

    if winning_bid_value > 0 and enriched_data['base_fee_per_gas'] is not None:
        total_reward = enriched_data['base_fee_per_gas'] * enriched_data['gas_used']
        enriched_data['mev_reward_percentage'] = (winning_bid_value / total_reward) * 100 if total_reward > 0 else 0
    else:
        enriched_data['mev_reward_percentage'] = None

    enriched_data['winning_relay'] = winning_relay
    enriched_data['gas_used_percentage'] = (enriched_data['gas_used'] / enriched_data['gas_limit']) * 100

    # Check if both max_bid and average_bid are not None before calculating variance
    if enriched_data['max_bid'] is not None and enriched_data['average_bid'] is not None:
        enriched_data['bid_value_variance'] = (enriched_data['max_bid'] - enriched_data['average_bid']) ** 2
    else:
        enriched_data['bid_value_variance'] = None
    
    enriched_data['empty_slot'] = enriched_data.get('bid_count', 0) == 0

    return enriched_data

def calculate_metrics(data):
    """Calculate overall metrics from the processed block data."""
    metrics = {
        'average_bid_value': [],
        'bid_value_variance': [],
        'flashbots_vs_ultrasound_wins': {'flashbots': 0, 'ultrasound': 0},
        'empty_slots': 0,
        'total_slots': len(data),
    }

    for block_data in data:
        if 'average_bid' in block_data:
            metrics['average_bid_value'].append(block_data['average_bid'])
        if 'bid_value_variance' in block_data and block_data['bid_value_variance'] is not None:
            metrics['bid_value_variance'].append(block_data['bid_value_variance'])
        if block_data.get('winning_relay') == 'flashbots':
            metrics['flashbots_vs_ultrasound_wins']['flashbots'] += 1
        elif block_data.get('winning_relay') == 'ultrasound':
            metrics['flashbots_vs_ultrasound_wins']['ultrasound'] += 1
        if block_data.get('empty_slot', False):
            metrics['empty_slots'] += 1

    return metrics

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def main():
    """Process block ranges, calculate metrics, and save the results."""
    all_block_data = []
    block_ranges = [(16000000, 16000300), (16010300, 16010300)]  # Example of blocks with more activity

    for start, end in block_ranges:
        for block_number in range(start, end + 1):
            block_data = process_block(block_number)
            if block_data:
                all_block_data.append(block_data)
                print(f"Processed block: {block_number}")

    overall_metrics = calculate_metrics(all_block_data)

    result = {
        'block_data': all_block_data,
        'overall_metrics': {
            'total_slots_processed': overall_metrics['total_slots'],
            'average_bid_value': safe_mean(overall_metrics['average_bid_value']),
            'average_bid_value_variance': safe_mean(overall_metrics['bid_value_variance']),
            'flashbots_wins': overall_metrics['flashbots_vs_ultrasound_wins']['flashbots'],
            'ultrasound_wins': overall_metrics['flashbots_vs_ultrasound_wins']['ultrasound'],
            'empty_slots': overall_metrics['empty_slots'],
        }
    }

    with open('mev_boost_enrichment_with_metrics.json', 'w') as f:
        json.dump(result, f, indent=2, cls=DateTimeEncoder)

    print("Data collection and metric calculation complete. Results saved to mev_boost_enrichment_with_metrics.json")

    print(f"Total slots processed: {overall_metrics['total_slots']}")
    print(f"Average bid value: {safe_mean(overall_metrics['average_bid_value'])} wei")
    print(f"Average bid value variance: {safe_mean(overall_metrics['bid_value_variance'])}")
    print(f"Flashbots wins: {overall_metrics['flashbots_vs_ultrasound_wins']['flashbots']}")
    print(f"Ultrasound wins: {overall_metrics['flashbots_vs_ultrasound_wins']['ultrasound']}")
    print(f"Number of empty slots: {overall_metrics['empty_slots']}")

if __name__ == "__main__":
    main()