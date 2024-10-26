from app.models.exchange import KrakenExchange
from config import ExchangeConfig
import time
import json

def export_data_to_json(data, filename):
    try:
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data successfully exported to {filename}")
    except Exception as e:
        print(f"Error exporting data to {filename}: {e}")

def fetch_data(pair, interval, since, filename):
    # Kraken OHLC API's settings
    intervals = [1, 5, 15, 30, 60, 240, 1440, 10080, 21600]
    max_data_points_per_response = 720

    assert interval in intervals

    current_time = since
    end_time = int(time.time())

    exchange_config = ExchangeConfig()
    kraken_exchange = KrakenExchange(exchange_config)

    data = {}
    while current_time <= end_time:
        time.sleep(5)
        response = kraken_exchange.get_ohlc_data(
            pair=pair,
            interval=interval,
            since=current_time
        )

        if data.get(0, None) != None:
            assert data[0].get("result", None) != None, "Error occured in response"

            for key, val in data[0]["result"].items():
                if key != "last":
                    # key is pair
                    for i in range(len(response["result"][key])):
                        data[0]["result"][key] += [response["result"][key][i]]
        else:
            data[0] = response

        try:
            current_time = response['result'][pair][-2][0]
        except:
            break
        time.sleep(5)
    export_data_to_json(data[0], f'AI/data/{filename}')