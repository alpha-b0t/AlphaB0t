from app.exchanges.exchange import KrakenExchange
from app.exchanges.cmc_api import CoinMarketCapAPI
from app.strategies.LSTM.json_helper import export_json_to_csv, export_data_to_json
from app.strategies.LSTM.clean_data import remove_duplicates_and_sort
from app.strategies.LSTM.model_constants import SINCE, INTERVAL
from config import ExchangeConfig, CoinMarketCapAPIConfig
import time
import json
import requests
from typing import Optional, Dict, Any, List

def fetch_data(pair, interval, since):
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
    export_data_to_json(data[0], "training_data.json")


def fetch_historical_data_http(
    symbol: str,
    interval: str = "1h",
    start_time_ms: Optional[int] = None,
    end_time_ms: Optional[int] = None,
    limit: int = 1000,
    filename: str = "training_data.json",
    base_url: str = "https://api.binance.com/api/v3/klines",
    extra_params: Optional[Dict[str, Any]] = None,
) -> List[list]:
    """
    Fetch historical OHLCV data directly via HTTP without using the app's Exchange classes.

    This is intended as a flexible, exchange-agnostic helper. By default it targets
    Binance's public kline endpoint, but you can point it at any compatible REST API
    by overriding `base_url` and `extra_params`.

    Args:
        symbol: Instrument identifier understood by the data provider (e.g. 'BTCUSDT').
        interval: Candle interval (e.g. '1m', '5m', '1h', '1d' for Binance).
        start_time_ms: Start timestamp in milliseconds since epoch. If None, the API's
            default behavior is used (usually "most recent candles").
        end_time_ms: End timestamp in milliseconds since epoch. If None, current
            time is used.
        limit: Maximum candles per HTTP request (Binance allows up to 1000).
        filename: Name of the JSON file to write under `app/strategies/LSTM/data`.
        base_url: Full URL of the HTTP endpoint returning klines/candles.
        extra_params: Optional dict of additional query parameters to send.

    Returns:
        A list of raw kline rows as returned by the provider (typically:
        [openTime, open, high, low, close, volume, closeTime, ...]).
    """
    if end_time_ms is None:
        end_time_ms = int(time.time() * 1000)

    params: Dict[str, Any] = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }

    if start_time_ms is not None:
        params["startTime"] = start_time_ms
    if end_time_ms is not None:
        params["endTime"] = end_time_ms

    if extra_params:
        params.update(extra_params)

    all_rows: List[list] = []
    current_start = start_time_ms

    request_num = 1
    while True:
        if current_start is not None:
            params["startTime"] = current_start

        print(f"Fetching Historical Data: Request #{request_num}")
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        batch = response.json()

        # Expecting a list of klines; break if nothing returned
        if not isinstance(batch, list) or len(batch) == 0:
            break

        all_rows.extend(batch)

        # If we received fewer than `limit` candles, we've likely reached the end.
        if len(batch) < limit:
            break

        # Advance start to the open time of the last candle + 1 ms to avoid duplicates
        last_open_time = int(batch[-1][0])
        next_start = last_open_time + 1
        if next_start >= end_time_ms:
            break

        current_start = next_start
        # Be gentle to the remote API
        time.sleep(0.2)
        request_num += 1

    # Persist raw rows as JSON for later processing
    export_data_to_json(all_rows, filename)

    return all_rows

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

def clean_training_data(
    input_filename: str = "training_data.json",
    output_filename: str = "cleaned_training_data.json"
) -> None:
    """
    Transform raw kline data from fetch_historical_data_http into the OHLCV format
    expected by the rest of the LSTM pipeline.

    Input JSON structure (written by fetch_historical_data_http):
        [
            [
                openTime,           # 0 (ms since epoch)
                open,               # 1
                high,               # 2
                low,                # 3
                close,              # 4
                volume,             # 5
                closeTime,          # 6
                quoteAssetVolume,   # 7
                numberOfTrades,     # 8
                takerBuyBaseVol,    # 9
                takerBuyQuoteVol,   # 10
                ignoreField         # 11
            ],
            ...
        ]

    Output JSON structure:
        {
            "result": {
                "data": [
                    [UNIX time, open, high, low, close, vwap, volume, count],
                    ...
                ]
            }
        }
    """
    raw_path = f"app/strategies/LSTM/data/{input_filename}"

    try:
        with open(raw_path, "r") as f:
            raw_rows = json.load(f)
    except Exception as e:
        print(f"Error loading raw training data from {raw_path}: {e}")
        raise e

    cleaned_rows: List[list] = []
    for row in raw_rows:
        if not isinstance(row, list) or len(row) < 6:
            continue

        open_time = int(row[0]) // 1000  # convert ms → seconds
        open_price = float(row[1])
        high = float(row[2])
        low = float(row[3])
        close = float(row[4])
        volume = float(row[5])
        count = int(row[8]) if len(row) > 8 else 0

        # Simple vwap approximation using OHLC
        # TODO: Improve
        vwap = (open_price + high + low + close) / 4.0

        cleaned_rows.append(
            [
                open_time,
                open_price,
                high,
                low,
                close,
                vwap,
                volume,
                count,
            ]
        )

    cleaned_payload = {
        "result": {
            "data": cleaned_rows
        }
    }

    export_data_to_json(cleaned_payload, output_filename)


def fetch_training_data():
    # Fetch training data
    csv_filename = "crypto_training_data.csv"

    # Convert interval
    # Interval in minutes (1, 5, 15, 30, 60, 240, 1440, 10080, 21600)
    # Need to convert to '1m', '5m', '1h', '1d' 
    # See https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#klinecandlestick-data
    conversions = {1:'1m', 3:'3m', 5:'5m', 15:'15m', 30:'30m', 60:'1h', 240:'4h', 1440:'1d', 10080:'1w'}
    converted_interval = conversions.get(int(INTERVAL), None)

    if converted_interval is None:
        raise ValueError(f"Provided interval {int(INTERVAL)} is not supported")
    
    # Fetch and persist raw training data
    fetch_historical_data_http(
        symbol=input("Enter Binance trading pair for fetching training data: "),
        interval=converted_interval,
        start_time_ms=int(SINCE) * 1000,
        filename="training_data.json",
    )

    # Clean training_data.json into canonical OHLCV layout
    clean_training_data("training_data.json", "cleaned_training_data.json")

    export_json_to_csv("cleaned_training_data.json", csv_filename)

    remove_duplicates_and_sort(csv_filename)

    if input("Fetch fear and greed index data? (y/n): ").lower() == 'y':
        fg_json_filename = input("Enter JSON filename to store fear and greed data (e.g. 'fear_and_greed_data.json'): ")
        fg_csv_filename = input("Enter CSV filename to store fear and greed data (e.g. 'fear_and_greed_data.csv'): ")
        fetch_fear_and_greed_data(
            start=-1,
            filename=fg_json_filename
        )

        export_json_to_csv(fg_json_filename, fg_csv_filename)
