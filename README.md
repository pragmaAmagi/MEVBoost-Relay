# MEV-Boost Data Collection and Analysis

This project collects and analyzes Maximal Extractable Value (MEV) data from Ethereum blocks, focusing on MEV-Boost related metrics. It fetches data from multiple sources, including Blockdaemon API, Flashbots, and Ultrasound relays, to provide insights into MEV activities across different block ranges.

## Features

- Fetches block data from Blockdaemon API.
- Retrieves MEV-related data from Flashbots and Ultrasound relays.
- Processes and enriches block data with MEV information.
- Calculates various metrics including average bid values, bid value variance, and relay wins.
- Implements rate limiting and error handling for robust API interactions.
- Outputs comprehensive JSON report with block-level details and overall metrics.
- **Data Visualization**: Generates visualizations using `matplotlib` to analyze the collected data.

## Requirements

- Python 3.6+
- `requests` library
- `matplotlib` library for data visualization

## Data Visualization Examples
![relay_wins_distribution](https://github.com/user-attachments/assets/fa218e9a-ebb9-4a8f-81ba-077b10688198)
![mev_visualization](https://github.com/user-attachments/assets/f0b5cc85-58df-406e-9359-c245fa53e8c7)
![gas_used_over_blocks](https://github.com/user-attachments/assets/caf7d6d1-4ffc-4210-a522-a69ef4036c9a)
![average_bid_histogram](https://github.com/user-attachments/assets/d1bf3e4a-aea2-4e4c-8863-973c7d835397)


## Installation

1. Clone this repository:
   ```
   git clone https://github.com/pragmaAmagi/MEVBoost-Relay.git
   cd MEVBoost-Relay
   ```

2. Install the required packages:
   ```
   pip install requests matplotlib
   ```

3. Set up your Blockdaemon API key in the `API_KEY` variable in the script.

## Usage

Run the main script:

```
python MEVBoost.py
```
This will process the predefined block ranges, collect data, calculate metrics, and save the results to `mev_boost_enrichment_with_metrics.json`.

After running the main script, you can visualize the results by running:

```
python visualize_data.py
```
This will generate various plots, including:
- A histogram of average bid values.
- A pie chart showing the distribution of relay wins.
- A line plot of gas used over blocks.

## Configuration

- Modify the `block_ranges` list in the `main()` function to analyze different block ranges.
- Adjust the `BLOCKDAEMON_URL`, `FLASHBOTS_URL`, and `ULTRASOUND_URL` constants if needed.

## Output

The script generates a JSON file (`mev_boost_enrichment_with_metrics.json`) containing:

- Detailed data for each processed block
- Overall metrics including:
  - Total slots processed
  - Average bid value
  - Average bid value variance
  - Flashbots and Ultrasound relay wins
  - Number of empty slots

## Key Metrics

- Block details (number, hash, timestamp, gas used/limit, transaction count)
- MEV-related data (average bid, max bid, bid count, winning relay)
- Gas usage percentages
- Bid value variance
- Empty slot detection

## Limitations

- The script uses estimated slot numbers based on block numbers, which may not always be accurate.
- Data availability is dependent on the uptime and responsiveness of the external APIs.

## Contributing

Contributions to improve the script or extend its functionality are welcome. Please submit a pull request or open an issue to discuss proposed changes.

## License

[MIT License](LICENSE)

## Disclaimer

This tool is for educational and research purposes only. Always ensure you comply with the terms of service of the APIs you're using.
