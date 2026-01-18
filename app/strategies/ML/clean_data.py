import csv
from operator import itemgetter

def remove_duplicates_and_sort(csv_file):
    csv_file = f'app/strategies/ML/data/{csv_file}'

    # Read CSV file and load data into a list of dictionaries
    data = []
    with open(csv_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    
    # Remove duplicate rows based on all fields except 'UNIX time'
    unique_data = [dict(t) for t in {tuple((d['open'], d['high'], d['low'], d['close'], d['vwap'], d['volume'], d['count'])): d for d in data}.values()]

    # Filter unique_data further by matching 'UNIX time', taking the second one if they match
    # This is mostly used for the last frame, i.e. to get the most current data for the last data point
    filtered_data = []
    unix_times_seen = set()
    for row in reversed(unique_data):
        # Note: data is not sorted
        if row['UNIX time'] not in unix_times_seen:
            filtered_data.append(row)
            unix_times_seen.add(row['UNIX time'])

    # Sort data points by 'UNIX time'
    sorted_data = sorted(filtered_data, key=itemgetter('UNIX time'))

    # Write sorted and duplicate-free data back to CSV file
    with open(csv_file, 'w', newline='') as csvfile:
        fieldnames = ['UNIX time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted_data:
            writer.writerow(row)

if __name__ == '__main__':
    remove_duplicates_and_sort('crypto_training_data.csv')
