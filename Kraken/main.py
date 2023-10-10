from authenticated_kraken import get_kraken_signature, kraken_authenticated_request, get_nonce
from public_kraken import kraken_public_request
import os

if __name__ == '__main__':
    api_sec = "kQH5HW/8p1uGOVjbgWA7FunAmGO8lsSUXNsu3eow76sz84Q18fWxnyRzBHCd3pd5nE9qa99HAZtuZuj6F1huXg=="

    data = {
        "nonce": "1616492376594", 
        "ordertype": "limit", 
        "pair": "XBTUSD",
        "price": 37500, 
        "type": "buy",
        "volume": 1.25
    }

    signature = get_kraken_signature("/0/private/AddOrder", data, api_sec)
    print("API-Sign: {}".format(signature))

    # Fetch time information
    time_response = kraken_public_request('/0/public/Time')

    # Fetch system status
    status_response = kraken_public_request('/0/public/SystemStatus')

    # Fetch asset information
    asset_response = kraken_public_request('/0/public/Assets')

    asset_pair_response = kraken_public_request('/0/public/AssetPairs', {'pair': 'XXBTZUSD,XETHXXBT'})
    ticker_info_response = kraken_public_request('/0/public/Ticker', {'pair': 'XBTUSD'})
    ohlc_response = kraken_public_request('/0/public/OHLC', {'pair': 'XBTUSD'})
    order_book_response = kraken_public_request('/0/public/Depth', {'pair': 'XBTUSD'})
    recent_trades_response = kraken_public_request('/0/public/Trades', {'pair': 'XBTUSD', 'count': '1'})
    recent_spreads_repsonse = kraken_public_request('/0/public/Spread', {'pair': 'XBTUSD'})

    # Read Kraken API key and secret stored in environment variables
    api_url = "https://api.kraken.com"
    api_key = os.environ['KRAKEN_API_KEY']
    api_sec = os.environ['KRAKEN_API_SEC']

    # Construct the request and print the result
    resp = kraken_authenticated_request(
        uri_path='/0/private/TradeBalance',
        data={
            "nonce": get_nonce(),
            "asset": "USD"
        },
        api_key=api_key,
        api_sec=api_sec
    )

    print(resp.json())