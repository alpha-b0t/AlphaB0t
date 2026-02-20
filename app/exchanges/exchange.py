from config import ExchangeConfig
import requests
import urllib.parse
import hashlib
import hmac
import base64
import time
import json
import inspect
from constants import CLASS_NAMES
import datetime
from typing import Any, Dict, Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
import robin_stocks.robinhood as rh
from app.strategies.helpers import round_down_to_cents

class Exchange():
    def __init__(self):
        self.classname = self.__class__.__name__
    
    def get_exchange_time(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_exchange_status(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_asset_info(self, asset, aclass):
        raise NotImplementedError("Not Implemented.")
    
    def get_tradable_asset_pairs(self, pair, info):
        raise NotImplementedError("Not Implemented.")
    
    def get_ticker_info(self, pair):
        raise NotImplementedError("Not Implemented.")

    def get_ohlc_data(self, pair, interval, since):
        raise NotImplementedError("Not Implemented.")
    
    def get_order_book(self, pair, count):
        raise NotImplementedError("Not Implemented.")
    
    def get_recent_trades(self, pair, since, count):
        raise NotImplementedError("Not Implemented.")
    
    def get_recent_spreads(self, pair, since):
        raise NotImplementedError("Not Implemented.")
    
    def add_order(self):
        raise NotImplementedError("Not Implemented.")
    
    def add_order_batch(self):
        raise NotImplementedError("Not Implemented.")
    
    def edit_order(self):
        raise NotImplementedError("Not Implemented.")
    
    def cancel_order(self):
        raise NotImplementedError("Not Implemented.")
    
    def cancel_order_batch(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_account_balance(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_extended_balance(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_trade_balance(self, asset):
        raise NotImplementedError("Not Implemented.")
    
    def get_open_orders(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_closed_orders(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_orders_info(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_trades_info(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_trades_history(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_trade_volume(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_holdings_and_bought_price(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_cash_and_equity(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_holdings_capital(self):
        raise NotImplementedError("Not Implemented.")
    
    @classmethod
    def from_json(cls, json_data):
        # Get the parameters of the __init__ method
        init_params = inspect.signature(cls.__init__).parameters

        # Extract known attributes
        known_attributes = {param for param in init_params if param != 'self'}
        known_data = {k: v for k, v in json_data.items() if k in known_attributes}

        # Extract additional attributes
        additional_data = {k: v for k, v in json_data.items() if k not in known_attributes}

        # Create instance with known attributes
        instance = cls(**known_data)

        # Set additional attributes
        for key, value in additional_data.items():
            if isinstance(value, dict) and 'classname' in value and value['classname'] in CLASS_NAMES:
                exec(f'setattr(instance, key, {value["classname"]}.from_json(value))')
            else:
                setattr(instance, key, value)
        
        return instance

class KrakenExchange(Exchange):
    def __init__(self, exchange_config: ExchangeConfig={}):
        super().__init__()
        self.classname = self.__class__.__name__
        if type(exchange_config) == dict:
            # Reloading
            print(f"Reloading {self.classname}...")
            return
        
        self.exchange_config = {}

        assert exchange_config.mode.lower() in ['live', 'test']
        self.api_key = exchange_config.api_key
        self.api_sec = exchange_config.api_sec
        self.mode = exchange_config.mode.lower()
        self.api_base_url = 'https://api.kraken.com/0'
    
    def __repr__(self):
        if self.api_key == '':
            api_key_display = "''"
        else:
            api_key_display = '******'
        
        if self.api_sec == '':
            api_sec_display = "''"
        else:
            api_sec_display = '******'
        
        return f"{{{self.classname} api_key: {api_key_display}, api_sec: {api_sec_display}, mode: {self.mode}, api_base_url: {self.api_base_url}}}"
    
    def handle_response_errors(self, response):
        """Given a response from Kraken, raises an error if there is an error returned or if there is not result."""
        try:
            if len(response['error']) > 0:
                for error_message in response['error']:
                    assert error_message[0] != 'E'

                    # Warning message
                    print(f"Warning: {error_message}")
            
            assert response.get('result') is not None
        except Exception as e:
            print(f"response: {response}")
            raise e
    
    # Public requests
    def public_request(self, uri_path, query_parameters=None):
        url = self.api_base_url + uri_path
        response = requests.get(url, params=query_parameters)
        return response
    
    def get_exchange_time(self):
        response = self.public_request('/public/Time')
        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_exchange_status(self):
        response = self.public_request('/public/SystemStatus')
        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_asset_info(self, asset='', aclass='currency'):
        """Get information about the assets that are available for deposit, withdrawal, trading and staking."""
        # https://docs.kraken.com/rest/#tag/Market-Data/operation/getAssetInfo
        if asset != '' or aclass != 'currency':
            query_parameters = {}

            if asset != '':
                query_parameters["asset"] = asset
            
            if aclass != 'currency':
                query_parameters["aclass"] = aclass
            
            response = self.public_request('/public/Assets', query_parameters)
        else:
            response = self.public_request('/public/Assets')
        
        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_tradable_asset_pairs(self, pair='', info='info'):
        """Get tradable asset pairs."""
        # https://docs.kraken.com/rest/#tag/Market-Data/operation/getTradableAssetPairs
        if pair != '' or info != 'info':
            query_parameters = {}
            
            if pair != '':
                query_parameters["pair"] = pair

            if info != 'info':
                query_parameters["info"] = info
            
            response = self.public_request('/public/AssetPairs', query_parameters)
        else:
            response = self.public_request('/public/AssetPairs')

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_ticker_info(self, pair=''):
        """Get ticker information. Note: Today's prices start at midnight UTC. Leaving the pair parameter blank will return tickers for all tradeable assets on Kraken."""
        # https://docs.kraken.com/rest/#tag/Market-Data/operation/getTickerInformation
        if pair != '':
            query_parameters = {
                "pair": pair
            }

            response = self.public_request('/public/Ticker', query_parameters)
        else:
            response = self.public_request('/public/Ticker')
        
        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_ohlc_data(self, pair, interval=1, since=0):
        """Get the latest quote of a cryptocurrency. Note: the last entry in the OHLC array is for the current, not-yet-committed frame and will always be present, regardless of the value of since."""
        # https://docs.kraken.com/rest/#tag/Market-Data/operation/getOHLCData
        query_parameters = {
            "pair": pair
        }

        if interval != 1:
            query_parameters["interval"] = interval
        
        if since != 0:
            query_parameters["since"] = since
        
        response = self.public_request('/public/OHLC', query_parameters)
        
        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_order_book(self, pair, count=100):
        """Get order book."""
        # https://docs.kraken.com/rest/#tag/Market-Data/operation/getOrderBook
        query_parameters = {
            "pair": pair
        }

        if count != 100:
            query_parameters["count"] = count
        
        response = self.public_request('/public/Depth', query_parameters)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_recent_trades(self, pair, since=0, count=1000):
        """Returns the last 1000 trades by default."""
        # https://docs.kraken.com/rest/#tag/Market-Data/operation/getRecentTrades
        query_parameters = {
            "pair": pair
        }

        if since != 0:
            query_parameters["since"] = since
        
        if count != 1000:
            query_parameters["count"] = count
        
        response = self.public_request('/public/Trades', query_parameters)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_recent_spreads(self, pair, since=0):
        """Returns the last ~200 top-of-book spreads for a given pair."""
        # https://docs.kraken.com/rest/#tag/Market-Data/operation/getRecentSpreads
        query_parameters = {
            "pair": pair
        }

        if since != 0:
            query_parameters["since"] = since
        
        response = self.public_request('/public/Spread', query_parameters)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    # Authenticated requests
    def authenticated_request(self, uri_path: str, data={}):
        """This method sends an authenticated request to the Kraken API."""
        data['nonce'] = self.get_nonce()
        
        headers = {}
        
        headers['API-Key'] = self.api_key
        headers['API-Sign'] = self.get_signature('/0'+uri_path, data)

        req = requests.post(
            url=(self.api_base_url + uri_path),
            headers=headers,
            data=data
        )

        return req
    
    def get_signature(self, urlpath: str, data) -> str:

        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        mac = hmac.new(base64.b64decode(self.api_sec), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()
    
    def get_nonce(self) -> str:
        """Returns nonce value as a string from a UNIX timestamp in milliseconds."""
        return str(int(1000*time.time()))
    
    def add_order(self, ordertype, type, volume, pair, userref=0, price='', price2='', trigger='', oflags='', timeinforce='GTC', starttm='', expiretm='', deadline='', validate='false'):
        """Add an order."""
        # https://docs.kraken.com/rest/#tag/Trading/operation/addOrder
        if self.mode == 'test':
            validate = True

        payload = {
            "ordertype": ordertype,
            "type": type,
            "volume": volume,
            "pair": pair,
            "validate": validate
        }

        if userref != 0:
            payload["userref"] = userref
        
        if price != '':
            payload["price"] = price
        
        if price2 != '':
            payload["price2"] = price2
        
        if trigger != '':
            payload["trigger"] = trigger

        if oflags != '':
            payload["oflags"] = oflags
        
        if timeinforce != 'GTC':
            payload["timeinforce"] = timeinforce
        
        if starttm != '':
            payload["starttm"] = starttm
        
        if expiretm != '':
            payload["expiretm"] = expiretm
        
        if deadline != '':
            payload["deadline"] = deadline
        
        response = self.authenticated_request('/private/AddOrder', payload)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def add_order_batch(self, orders, pair, deadline='', validate='false'):
        """Add a batch of orders at once."""
        # https://docs.kraken.com/rest/#tag/Trading/operation/addOrderBatch
        if self.mode == 'test':
            validate = True
        
        payload = {
            "orders": orders,
            "pair": pair,
            "validate": validate
        }

        if deadline != '':
            payload["deadline"] = deadline
        
        response = self.authenticated_request('/private/AddOrderBatch', payload)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def edit_order(self, txid, pair, userref=0, volume='', price='', price2='', oflags='', deadline='', validate='false'):
        """Edit an open order by its txid."""
        # https://docs.kraken.com/rest/#tag/Trading/operation/editOrder
        if self.mode == 'test':
            validate = True
        
        payload = {
            "txid": txid,
            "pair": pair,
            "validate": validate
        }

        if userref != 0:
            payload["userref"] = userref
        
        if volume != '':
            payload["volume"] = volume
        
        if price != '':
            payload["price"] = price
        
        if price2 != '':
            payload["price2"] = price2
        
        if oflags != '':
            payload["oflags"] = oflags
        
        if deadline != '':
            payload["deadline"] = deadline
        
        response = self.authenticated_request('/private/EditOrder', payload)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def cancel_order(self, txid):
        """
        Cancel an open order.
        
        txid: (str or int) Open order transaction ID (txid) or user reference (userref))
        """
        # https://docs.kraken.com/rest/#tag/Trading/operation/cancelOrder
        payload = {
            "txid": txid
        }

        response = self.authenticated_request('/private/CancelOrder', payload)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def cancel_order_batch(self, orders):
        """Cancel a batch of orders at once."""
        # https://docs.kraken.com/rest/#tag/Trading/operation/cancelOrderBatch
        # Here orders is a list of txids
        payload = {
            "orders": orders
        }

        response = self.authenticated_request('/private/CancelOrderBatch', payload)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_account_balance(self):
        """Retrieve all cash balances, net of pending withdrawals."""
        # https://docs.kraken.com/rest/#tag/Account-Data/operation/getAccountBalance
        response = self.authenticated_request('/private/Balance')
        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_extended_balance(self):
        """Retrieve all extended account balances, including credits and held amounts. Balance available for trading is calculated as: available balance = balance + credit - credit_used - hold_trade."""
        # https://docs.kraken.com/rest/#tag/Account-Data/operation/getExtendedBalance
        response = self.authenticated_request('/private/BalanceEx')
        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_trade_balance(self, asset='ZUSD'):
        """Retrieve a summary of collateral balances, margin position valuations, equity and margin level."""
        # https://docs.kraken.com/rest/#tag/Account-Data/operation/getTradeBalance
        payload = {
            "asset": asset
        }

        response = self.authenticated_request('/private/TradeBalance', payload)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_open_orders(self, trades=False, userref=0):
        """Retrieve information about currently open orders."""
        # https://docs.kraken.com/rest/#tag/Account-Data/operation/getOpenOrders
        payload = {
            "trades": trades
        }

        if userref != 0:
            payload["userref"] = userref
        
        response = self.authenticated_request('/private/OpenOrders', payload)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_closed_orders(self, trades=False, userref=0, start=0, end=0, ofs=0, closetime='both', consolidate_ticker=True):
        """Retrieve information about orders that have been closed (filled or cancelled)."""
        # https://docs.kraken.com/rest/#tag/Account-Data/operation/getClosedOrders
        payload = {
            "trades": trades
        }

        if userref != 0:
            payload["userref"] = userref
        
        if start != 0:
            payload["start"] = start
        
        if end != 0:
            payload["end"] = end
        
        if ofs != 0:
            payload["ofs"] = ofs
        
        if closetime != 'both':
            payload["closetime"] = closetime
        
        if consolidate_ticker != True:
            payload["consolidate_ticker"] = consolidate_ticker
        
        response = self.authenticated_request('/private/ClosedOrders', payload)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_orders_info(self, txid, userref=0, trades=False, consolidate_taker=True):
        """Retrieve information about specific orders."""
        # https://docs.kraken.com/rest/#tag/Account-Data/operation/getOrdersInfo
        payload = {
            "txid": txid
        }

        if userref != 0:
            payload["userref"] = userref
        
        if trades != False:
            payload["trades"] = trades
        
        if consolidate_taker != True:
            payload["consolidate_taker"] = consolidate_taker
        
        response = self.authenticated_request('/private/QueryOrders', payload)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_trades_info(self, txid, trades=False):
        """Retrieve information about specific trades/fills."""
        # https://docs.kraken.com/rest/#tag/Account-Data/operation/getTradesInfo
        payload = {
            "txid": txid
        }

        if trades != False:
            payload["trades"] = trades
        
        response = self.authenticated_request('/private/QueryTrades', payload)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_trades_history(self, type='all', trades=False, start=0, end=0, ofs='', consolidate_taker=True):
        """Retrieve information about trades/fills. 50 results are returned at a time, the most recent by default."""
        # https://docs.kraken.com/rest/#tag/Account-Data/operation/getTradeHistory
        payload = {
            "type": type
        }

        if trades != False:
            payload["trades"] = trades
        
        if start != 0:
            payload["start"] = start
        
        if end != 0:
            payload["end"] = end
        
        if ofs != '':
            payload["ofs"] = ofs
        
        if consolidate_taker != True:
            payload["consolidate_taker"] = consolidate_taker
        
        response = self.authenticated_request('/private/TradesHistory', payload)

        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_trade_volume(self, pair=''):
        """Returns 30 day USD trading volume and resulting fee schedule for any asset pair(s) provided."""
        # https://docs.kraken.com/rest/#tag/Account-Data/operation/getTradeVolume
        if pair != '':
            payload = {
                "pair": pair
            }

            response = self.authenticated_request('/private/TradeVolume', payload)
        else:
            response = self.authenticated_request('/private/TradeVolume')
        
        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_websockets_token(self):
        """Get a websocket token for Kraken's WebSockets API."""
        # https://docs.kraken.com/rest/#tag/Websockets-Authentication/operation/getWebsocketsToken
        response = self.authenticated_request('/private/GetWebSocketsToken')

        result = response.json()
        self.handle_response_errors(result)
        return result

class CoinbaseExchange(Exchange):
    def __init__(self, api_key='', api_sec='', api_passphrase=''):
        super().__init__()
        self.classname = self.__class__.__name__
        self.api_key = api_key
        self.api_sec = api_sec
        self.api_passphrase = api_passphrase
        self.api_base_url = 'https://api.exchange.coinbase.com'
    
    def public_request(self, uri_path, query_parameters={}):
        url = self.api_base_url + uri_path

        if query_parameters != {}:
            url += '?'
            first_key = True
            for key in query_parameters.keys():
                if not first_key:
                    url += '&'
                    first_key = False
                
                url += f"{key}={query_parameters[key]}"
        
        response = requests.get(url)
        return response
    
    def authenticated_request(self, method, uri_path, data={}):
        timestamp = self.get_exchange_time()['epoch']

        headers = {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": self.get_signature(
                timestamp=timestamp,
                method=method,
                path=f"{self.api_base_url}{uri_path}",
                body=json.dumps(data) if data != {} else ''
            ),
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-ACCESS-PASSPHRASE": self.api_passphrase
        }

        if method == "GET":
            response = requests.get(
                url=f"{self.api_base_url}{uri_path}",
                headers=headers,
                params=data
            )
        elif method == "POST":
            response = requests.post(
                url=f"{self.api_base_url}{uri_path}",
                headers=headers,
                data=data
            )
        elif method == "PUT":
            response = requests.put(
                url=f"{self.api_base_url}{uri_path}",
                headers=headers,
                data=data
            )
        elif method == "DELETE":
            response = requests.delete(
                url=f"{self.api_base_url}{uri_path}",
                headers=headers,
                data=data
            )
        else:
            raise ValueError("Unsupported HTTP method")
        
        return response

    def get_signature(self, timestamp, method, path, body=''):
        prehash_str = f"{timestamp}{method}{path}{body}"
        encoded_str = prehash_str.encode('utf-8')
        signature = hmac.new(self.api_sec.encode('utf-8'), encoded_str, hashlib.sha256).hexdigest()
        return signature
    
    def get_exchange_time(self):
        """Get the time from the exchange."""
        response = self.public_request('/time')
        return response.json()
    
    def get_currency(self, currency_id):
        """Get a single currency by id."""
        # https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getcurrency
        response = self.public_request(f"/currencies/{currency_id}")
        return response.json()
    
    def get_trading_pairs(self):
        """Gets a list of available currency pairs for trading."""
        # https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getproducts
        response = self.public_request('/products')
        return response.json()
    
    def get_product_info(self, product_id):
        """Gets information about a specific trading pair."""
        # https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getproduct
        response = self.public_request(f"/products/{product_id}")
        return response.json()
    
    def get_product_candles(self, product_id, granularity='', start='', end=''):
        """Gets historic rates for a product."""
        # https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getproductcandles
        query_parameters = {}

        if granularity != '':
            query_parameters["granularity"] = granularity
        
        if start != '':
            query_parameters["start"] = start
        
        if end != '':
            query_parameters["end"] = end
        
        if query_parameters != {}:
            response = self.public_request(f"/products/{product_id}/candles", query_parameters)
        else:
            response = self.public_request(f"/products/{product_id}/candles")
        
        return response.json()
    
    def get_fees(self):
        """Gets fee rates and 30 days trailing volume."""
        response = self.authenticated_request('GET', '/fees')
        return response.json()
    
    def create_order(self, type, side, product_id, profile_id='', stp='dc', stop='', stop_price='', price='', size='', funds='', time_in_force='GTC', cancel_after='', post_only=False, client_oid=''):
        """Creates an order."""
        payload = {
            "type": type,
            "side": side,
            "product_id": product_id
        }

        if profile_id != '':
            payload["profile_id"] = profile_id
        
        if stp != 'dc':
            payload["stp"] = stp
        
        if stop != '':
            payload["stop"] = stop
        
        if stop_price != '':
            payload["stop_price"] = stop_price
        
        if price != '':
            payload["price"] = price
        
        if size != '':
            payload["size"] = size
        
        if funds != '':
            payload["funds"] = funds
        
        if time_in_force != '':
            payload["time_in_force"] = time_in_force
        
        if cancel_after != '':
            payload["cancel_after"] = cancel_after
        
        if post_only != False:
            payload["post_only"] = post_only
        
        if client_oid != '':
            payload["client_oid"] = client_oid
        
        response = self.authenticated_request('POST', '/orders', payload)

        return response.json()
    
    def cancel_order(self, order_id, profile_id='', product_id=''):
        """Cancel a single open order by id."""
        query_parameters = {}

        if profile_id != '':
            query_parameters["profile_id"] = profile_id
        
        if product_id != '':
            query_parameters["product_id"] = product_id
        
        if query_parameters != {}:
            response = self.authenticated_request('DELETE', f"/orders/{order_id}", query_parameters)
        else:
            response = self.authenticated_request('DELETE', f"/orders/{order_id}")
        
        return response.json()

class RobinhoodCryptoExchange(Exchange):
    def __init__(self, exchange_config: ExchangeConfig={}):
        super().__init__()
        self.classname = self.__class__.__name__
        if type(exchange_config) == dict:
            # Reloading
            print(f"Reloading {self.classname}...")
            return
        
        self.exchange_config = {}

        assert exchange_config.mode.lower() in ['live', 'test']
        self.api_key = exchange_config.api_key
        self.api_sec = exchange_config.api_sec
        self.mode = exchange_config.mode.lower()

        private_bytes = base64.b64decode(exchange_config.api_sec)
        # Note that the cryptography library used here only accepts a 32 byte ed25519 private key
        self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes[:32])
        self.api_base_url = "https://trading.robinhood.com"
    
    @staticmethod
    def _get_current_timestamp() -> int:
        return int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())

    @staticmethod
    def get_query_params(key: str, *args: Optional[str]) -> str:
        if not args:
            return ""

        params = []
        for arg in args:
            params.append(f"{key}={arg}")

        return "?" + "&".join(params)

    def make_api_request(self, method: str, path: str, body: str = "") -> Any:
        timestamp = self._get_current_timestamp()
        headers = self.get_authorization_header(method, path, body, timestamp)
        url = self.api_base_url + path

        try:
            response = {}
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=json.loads(body), timeout=10)
            return response.json()
        except requests.RequestException as e:
            print(f"Error making API request: {e}")
            return None

    def get_authorization_header(
            self, method: str, path: str, body: str, timestamp: int
    ) -> Dict[str, str]:
        message_to_sign = f"{self.api_key}{timestamp}{path}{method}{body}"
        signature = self.private_key.sign(message_to_sign.encode("utf-8"))

        return {
            "x-api-key": self.api_key,
            "x-signature": base64.b64encode(signature).decode("utf-8"),
            "x-timestamp": str(timestamp),
        }

    def get_account(self) -> Any:
        path = "/api/v1/crypto/trading/accounts/"
        return self.make_api_request("GET", path)

    # The symbols argument must be formatted in trading pairs, e.g "BTC-USD", "ETH-USD". If no symbols are provided,
    # all supported symbols will be returned
    def get_trading_pairs(self, *symbols: Optional[str]) -> Any:
        query_params = self.get_query_params("symbol", *symbols)
        path = f"/api/v1/crypto/trading/trading_pairs/{query_params}"
        return self.make_api_request("GET", path)

    # The asset_codes argument must be formatted as the short form name for a crypto, e.g "BTC", "ETH". If no asset
    # codes are provided, all crypto holdings will be returned
    def get_holdings(self, *asset_codes: Optional[str]) -> Any:
        query_params = self.get_query_params("asset_code", *asset_codes)
        path = f"/api/v1/crypto/trading/holdings/{query_params}"
        return self.make_api_request("GET", path)

    # The symbols argument must be formatted in trading pairs, e.g "BTC-USD", "ETH-USD". If no symbols are provided,
    # the best bid and ask for all supported symbols will be returned
    def get_best_bid_ask(self, *symbols: Optional[str]) -> Any:
        query_params = self.get_query_params("symbol", *symbols)
        path = f"/api/v1/crypto/marketdata/best_bid_ask/{query_params}"
        return self.make_api_request("GET", path)

    # The symbol argument must be formatted in a trading pair, e.g "BTC-USD", "ETH-USD"
    # The side argument must be "bid", "ask", or "both".
    # Multiple quantities can be specified in the quantity argument, e.g. "0.1,1,1.999".
    def get_estimated_price(self, symbol: str, side: str, quantity: str) -> Any:
        path = f"/api/v1/crypto/marketdata/estimated_price/?symbol={symbol}&side={side}&quantity={quantity}"
        return self.make_api_request("GET", path)

    def place_order(
            self,
            client_order_id: str,
            side: str,
            order_type: str,
            symbol: str,
            order_config: Dict[str, str],
    ) -> Any:
        body = {
            "client_order_id": client_order_id,
            "side": side,
            "type": order_type,
            "symbol": symbol,
            f"{order_type}_order_config": order_config,
        }
        path = "/api/v1/crypto/trading/orders/"
        return self.make_api_request("POST", path, json.dumps(body))

    def cancel_order(self, order_id: str) -> Any:
        path = f"/api/v1/crypto/trading/orders/{order_id}/cancel/"
        return self.make_api_request("POST", path)

    def get_order(self, order_id: str) -> Any:
        path = f"/api/v1/crypto/trading/orders/{order_id}/"
        return self.make_api_request("GET", path)

    def get_orders(self) -> Any:
        path = "/api/v1/crypto/trading/orders/"
        return self.make_api_request("GET", path)

class RobinhoodOptionExchange(Exchange):
    def __init__(self, exchange_config: ExchangeConfig={}):
        super().__init__()
        self.classname = self.__class__.__name__
        if type(exchange_config) == dict:
            # Reloading
            print(f"Reloading {self.classname}...")
            return
        
        self.exchange_config = {}

        assert exchange_config.mode.lower() in ['live', 'test']
        self.api_key = exchange_config.api_key
        self.api_sec = exchange_config.api_sec
        self.mode = exchange_config.mode.lower()
    
    def __repr__(self):
        if self.api_key == '':
            api_key_display = "''"
        else:
            api_key_display = '******'
        
        if self.api_sec == '':
            api_sec_display = "''"
        else:
            api_sec_display = '******'
        
        return f"{{{self.classname} api_key: {api_key_display}, api_sec: {api_sec_display}, mode: {self.mode}}}"
    
    def login(self):
        try:
            rh.authentication.login(username=self.api_key, password=self.api_sec, store_session=False)
            print("successfully logged in")
        except Exception as e:
            print("login failed")
            raise e
    
    def logout(self):
        try:
            rh.authentication.logout()
            print("successfully logged out")
        except Exception as e:
            print("already logged out")
            raise e
    
    def get_exchange_time(self):
        """Returns the current exchange time (as string)."""
        return rh.stocks.get_market_hours()

    def get_exchange_status(self):
        """Check if the exchange is open or closed."""
        market_hours = rh.markets.get_market_hours()
        if market_hours['is_open']:
            return "Open"
        else:
            return "Closed"

    def get_asset_info(self, pair):
        """Fetch asset information for a given option."""
        return rh.options.get_option_instrument_data(pair)

    def get_tradable_asset_pairs(self, pair, info):
        """Get tradable asset pairs."""
        return rh.options.find_tradable_options(symbol=pair)
    
    def get_ticker_info(self, pair):
        """Get ticker info for a given asset pair."""
        return rh.options.get_option_instrument_data(pair)

    def get_ohlc_data(self, pair, expirationDate, strikePrice, optionType):
        """Fetch OHLC (Open, High, Low, Close) data."""
        return rh.options.get_option_market_data(pair, expirationDate, strikePrice, optionType)

    def get_order_book(self, pair, count):
        """Fetch order book for an asset pair."""
        # Robinhood API does not support direct order books, you could adapt this method.
        return rh.options.get_option_instrument_data(pair)  # Placeholder for now.

    def get_recent_trades(self, pair, since, count):
        """Fetch recent trades."""
        return rh.stocks.get_recent_trades(pair, count)

    def get_recent_spreads(self, pair, since):
        """Fetch recent spreads."""
        # Robinhood API does not directly provide spread data, needs alternative calculation
        return rh.options.get_option_instrument(pair)  # Placeholder for now.

    def add_order(self, symbol, quantity, option_type, price, action):
        """Place an order for options trading."""
        """
        robin_stocks.robinhood.orders.order_buy_option_limit(positionEffect, creditOrDebit, price, symbol, quantity, expirationDate, strike, optionType='both', account_number=None, timeInForce='gtc', jsonify=True)[source]
        Submits a limit order for an option. i.e. place a long call or a long put.

        Parameters:
        positionEffect (str) – Either ‘open’ for a buy to open effect or ‘close’ for a buy to close effect.

        creditOrDebit (str) – Either ‘debit’ or ‘credit’.

        price (float) – The limit price to trigger a buy of the option.

        symbol (str) – The stock ticker of the stock to trade.

        quantity (int) – The number of options to buy.

        expirationDate (str) – The expiration date of the option in ‘YYYY-MM-DD’ format.

        strike (float) – The strike price of the option.

        optionType (str) – This should be ‘call’ or ‘put’

        account_number (Optional[str]) – the robinhood account number.

        timeInForce (Optional[str]) – Changes how long the order will be in effect for. ‘gtc’ = good until cancelled. ‘gfd’ = good for the day. ‘ioc’ = immediate or cancel. ‘opg’ execute at opening.

        jsonify (Optional[str]) – If set to False, function will return the request object which contains status code and headers.

        Returns:
        Dictionary that contains information regarding the buying of options, such as the order id, the state of order (queued, confired, filled, failed, canceled, etc.), the price, and the quantity.
        """
        if action == "buy":
            return rh.options.order_buy_option_limit(symbol, quantity, price)
        elif action == "sell":
            return rh.options.order_sell_option_limit(symbol, quantity, price)
        return None

    def add_order_batch(self, orders):
        """Add multiple orders at once."""
        # Robinhood does not natively support batch orders through this library
        results = []
        for order in orders:
            result = self.add_order(**order)
            results.append(result)
        return results

    def edit_order(self, order_id, new_price):
        """Edit an existing order."""
        return rh.orders.update_option_order(order_id, price=new_price)

    def cancel_order(self, order_id):
        """Cancel an order."""
        return rh.orders.cancel_option_order(order_id)

    def cancel_order_batch(self, order_ids):
        """Cancel a batch of orders."""
        results = []
        for order_id in order_ids:
            result = self.cancel_order(order_id)
            results.append(result)
        return results

    def get_account_balance(self):
        """Fetch account balance."""
        return rh.account.get_account()

    def get_extended_balance(self):
        """Fetch extended balance (cash, buying power, margin)."""
        return rh.account.get_margin()
    
    def get_trade_balance(self, asset):
        """Fetch trade balance for a given asset."""
        return rh.stocks.get_balance(asset)
    
    def get_open_orders(self):
        """Fetch all open orders."""
        return rh.orders.get_all_open_option_orders()

    def get_closed_orders(self):
        """Fetch all closed orders."""
        return rh.orders.get_all_closed_orders()

    def get_orders_info(self):
        """Fetch detailed information for all orders."""
        return rh.orders.get_all_option_positions()

    def get_trades_info(self):
        """Fetch detailed trade information."""
        return rh.stocks.get_all_trades()

    def get_trades_history(self):
        """Fetch historical trade data."""
        return rh.stocks.get_trade_history()

    def get_trade_volume(self):
        """Fetch the total volume of trades."""
        # No direct Robinhood method, but could be calculated from trade history.
        raise NotImplementedError

    def get_holdings_and_bought_price(self):
        """Fetch all holdings and the average bought price."""
        holdings = rh.stocks.get_all_positions()
        return [{"symbol": position['instrument']['symbol'], 
                 "quantity": position['quantity'], 
                 "avg_price": position['average_buy_price']} for position in holdings]

    def get_cash_and_equity(self):
        """Fetch cash and equity balances."""
        account_info = rh.account.get_account()
        return {
            "cash": account_info['cash'],
            "equity": account_info['equity']
        }

    def get_holdings_capital(self):
        """Fetch holdings balance using the market price."""
        capital = 0.00
        
        for asset_name, amount in self.holdings.items():
            capital += amount * float(self.get_latest_quote(asset_name)['mark_price'])
        
        return round_down_to_cents(capital)
