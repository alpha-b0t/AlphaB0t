import json
import csv

def export_json_to_csv(json_file, csv_file):
    with open(f'ML/data/{json_file}', 'r') as f:
        data = json.load(f)
    
    result = data.get('result', {})
    
    with open(f'ML/data/{csv_file}', 'w', newline='') as f:
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
        json_file = 'ML/data/training_data.json'
        csv_file = 'ML/data/crypto_training_data.csv'
    elif input_val in ['N', 'n']:
        json_file = 'ML/data/prediction_data.json'
        csv_file = 'ML/data/crypto_prediction_data.csv'
    else:
        raise Exception('Invalid input.')
    
    export_json_to_csv(json_file, csv_file)
