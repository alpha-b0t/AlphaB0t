import json
import csv
import os

def export_data_to_json(data, filename):
    # Ensure the 'data' folder exists
    folder = 'app/strategies/LSTM/data'
    os.makedirs(folder, exist_ok=True)

    filename = f'{folder}/{filename}'
    
    try:
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data successfully exported to {filename}")
    except Exception as e:
        print(f"Error exporting data to {filename}: {e}")

def export_json_to_csv(json_file, csv_file):
    with open(f'app/strategies/LSTM/data/{json_file}', 'r') as f:
        data = json.load(f)
    
    result = data.get('result', {})
    
    with open(f'app/strategies/LSTM/data/{csv_file}', 'w', newline='') as f:
        writer = csv.writer(f)
        
        writer.writerow(['UNIX time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'])

        for key, value in result.items():
            try:
                for row in value:
                    writer.writerow(row)
            except:
                # End of JSON
                return

if __name__ == '__main__':
    input_val = input('Is this for training data (Y) or prediction data (N)? ')

    if input_val in ['Y', 'y']:
        json_file = 'app/strategies/LSTM/data/training_data.json'
        csv_file = 'app/strategies/LSTM/data/crypto_training_data.csv'
    elif input_val in ['N', 'n']:
        json_file = 'app/strategies/LSTM/data/prediction_data.json'
        csv_file = 'app/strategies/LSTM/data/crypto_prediction_data.csv'
    else:
        raise Exception('Invalid input.')
    
    export_json_to_csv(json_file, csv_file)
