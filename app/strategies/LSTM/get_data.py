from app.exchanges.exchange import KrakenExchange
from app.exchanges.cmc_api import CoinMarketCapAPI
from app.strategies.LSTM.json_helper import export_json_to_csv
from app.strategies.LSTM.clean_data import remove_duplicates_and_sort
from app.strategies.LSTM.model_constants import INTERVAL
from config import ExchangeConfig, CoinMarketCapAPIConfig
import time
from app.strategies.LSTM.json_helper import export_data_to_json

def fetch_data(pair, interval, since, filename):
    # Kraken OHLC API's settings
    # intervals is in minutes
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
    export_data_to_json(data[0], filename)

def fetch_fear_and_greed_data(start: int = -1, filename: str = 'fear_and_greed_data.json'):
    """
    Fetch all historical fear and greed index data from CoinMarketCap API for LSTM training.
    Automatically paginates through all available data since the start parameter.
    
    Args:
        start: Starting position for pagination (default: -1, which fetches from the most recent)
        filename: Output filename for the JSON data (default: 'fear_and_greed_data.json')
    """
    try:
        cmc_config = CoinMarketCapAPIConfig()
        cmc_api = CoinMarketCapAPI(api_key=cmc_config.cmc_api_key)
        
        all_data = []
        current_start = start
        api_limit = 50  # CMC API default limit per request
        
        while True:
            # Fetch fear and greed historical data with pagination
            response = cmc_api.get_fear_and_greed_historical(start=current_start, limit=api_limit)
            
            data_batch = response.get('data', [])
            
            if not data_batch:
                # No more data to fetch
                break
            
            all_data.extend(data_batch)
            
            print(f"Fetched {len(data_batch)} records (total: {len(all_data)})")
            
            # Prepare for next iteration
            if len(data_batch) < api_limit:
                # Fewer records returned than requested, we've reached the end
                break
            
            # Set start to the next position after the last fetched record
            current_start += api_limit
            time.sleep(2)  # Rate limiting between API calls
        
        # Create response object with all collected data
        combined_response = {
            'data': all_data,
            'status': response.get('status', {})
        }
        
        # Export data to JSON
        export_data_to_json(combined_response, filename)
        
        print(f"Fear and greed index data fetched successfully!")
        print(f"Total records fetched: {len(all_data)}")
    
    except Exception as e:
        print(f"Error fetching fear and greed data: {e}")
        raise e

def fetch_training_data(pair: str):
    # Fetch training data
    since = 0
    json_filename = "training_data.json"
    csv_filename = "training_data.csv"

    fetch_data(
        pair=pair,
        interval=int(INTERVAL),
        since=since,
        filename=json_filename
    )

    export_json_to_csv(json_filename, csv_filename)

    remove_duplicates_and_sort(csv_filename)

    if input("Fetch fear and greed index data? (y/n): ").lower() == 'y':
        fg_json_filename = input("Enter JSON filename to store fear and greed data (e.g. 'fear_and_greed_data.json'): ")
        fg_csv_filename = input("Enter CSV filename to store fear and greed data (e.g. 'fear_and_greed_data.csv'): ")
        fetch_fear_and_greed_data(
            start=since,
            filename=fg_json_filename
        )

        export_json_to_csv(fg_json_filename, fg_csv_filename)

if __name__ == "__main__":
    fetch_training_data("XBTUSD")