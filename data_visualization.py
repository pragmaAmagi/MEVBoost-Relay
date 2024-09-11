import json
import matplotlib.pyplot as plt

def load_data(file_path):
    """Load the JSON data from the specified file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def plot_average_bid_histogram(average_bid_values):
    """Plot a histogram of average bid values."""
    plt.figure(figsize=(8, 6))
    plt.hist(average_bid_values, bins=30, color='blue', alpha=0.7)
    plt.title('Histogram of Average Bid Values')
    plt.xlabel('Average Bid (wei)')
    plt.ylabel('Frequency')
    plt.grid()
    plt.savefig('average_bid_histogram.png')
    print("Histogram saved as average_bid_histogram.png")

def plot_relay_wins(flashbots_wins, ultrasound_wins):
    """Plot a pie chart of relay wins."""
    labels = ['Flashbots', 'Ultrasound']
    sizes = [flashbots_wins, ultrasound_wins]
    colors = ['gold', 'lightcoral']
    explode = (0.1, 0)  # explode the 1st slice (Flashbots)

    plt.figure(figsize=(8, 6))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title('Relay Wins Distribution')
    plt.savefig('relay_wins_distribution.png')
    print("Pie chart saved as relay_wins_distribution.png")

def plot_gas_used(data):
    """Plot gas used over blocks."""
    block_numbers = [block['block_number'] for block in data['block_data']]
    gas_used = [block['gas_used'] for block in data['block_data']]

    plt.figure(figsize=(12, 6))
    plt.plot(block_numbers, gas_used, marker='o', linestyle='-', color='green')
    plt.title('Gas Used Over Blocks')
    plt.xlabel('Block Number')
    plt.ylabel('Gas Used')
    plt.grid()
    plt.savefig('gas_used_over_blocks.png')
    print("Gas used plot saved as gas_used_over_blocks.png")

def plot_metrics(data):
    """Plot the average bid value and the number of empty slots."""
    average_bid_values = [block['average_bid'] for block in data['block_data'] if block['average_bid'] is not None]
    empty_slots = [block['empty_slot'] for block in data['block_data']]

    plt.figure(figsize=(12, 6))

    # Plot average bid values
    plt.subplot(1, 2, 1)
    plt.plot(average_bid_values, marker='o', linestyle='-', color='b')
    plt.title('Average Bid Values')
    plt.xlabel('Block Index')
    plt.ylabel('Average Bid (wei)')
    plt.grid()

    # Plot empty slots
    plt.subplot(1, 2, 2)
    plt.bar(range(len(empty_slots)), empty_slots, color='r')
    plt.title('Empty Slots per Block')
    plt.xlabel('Block Index')
    plt.ylabel('Empty Slot (1 = Yes, 0 = No)')
    plt.xticks(range(len(empty_slots)), range(len(empty_slots)))

    plt.tight_layout()

    # Save the figure as a PNG file
    plt.savefig('mev_visualization.png')
    print("Visualization saved as mev_visualization.png")

    # Call additional plots
    plot_average_bid_histogram(average_bid_values)
    plot_relay_wins(data['overall_metrics']['flashbots_wins'], data['overall_metrics']['ultrasound_wins'])
    plot_gas_used(data)

if __name__ == "__main__":
    data = load_data('mev_boost_enrichment_with_metrics.json')
    plot_metrics(data)