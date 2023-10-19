import robin_stocks.robinhood as rh
import requests
import urllib.parse
import hashlib
import hmac
import base64
import time
import json

class Exchange():
    def __init__(self):
        pass
    
    def login(self):
        pass
    
    def logout(self):
        pass
    
    def get_balances(self):
        pass
    
    def get_latest_quote(self, symbol):
        pass
    
    def build_holdings(self):
        pass
    
    def get_holdings_and_bought_price(self):
        pass
    
    def get_cash_and_equity(self):
        pass
    
    def get_crypto_holdings_capital(self):
        pass
    
    def create_order(self):
        pass
    
    def cancel_order(self):
        pass

class KrakenExchange(Exchange):
    def __init__(self, api_key='', api_sec=''):
        super().__init__()
        self.api_key = api_key
        self.api_sec = api_sec
        self.api_base_url = 'https://api.kraken.com/0'

    def get_latest_quote(self, symbol, interval=1, since=0):
        """Get the latest quote of a cryptocurrency."""
        query_parameters = {
            "pair": symbol
        }

        if interval != 1:
            query_parameters["interval"] = interval
        
        if since != 0:
            query_parameters["since"] = since
        
        response = self.public_request('/public/OHLC', query_parameters)
        
        return response.json()
    
    def get_exchange_time(self):
        response = self.public_request('/public/Time')
        return response.json()
    
    def get_tradable_asset_pairs(self, pair='', info="info"):
        """Get tradable asset pairs."""
        query_parameters = {
            "pair": pair
        }

        if info != "info":
            query_parameters["info"] = info
        
        if pair != '':
            response = self.public_request('/public/AssetPairs', query_parameters)
        else:
            response = self.public_request('/public/AssetPairs')

        return response.json()
    
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
    
    def get_signature(self, urlpath, data, secret) -> str:

        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()
    
    def authenticated_request(self, uri_path, data={}):
        """
        This method sends an authenticated request to the Kraken API.

        :param uri_path: The API endpoint to send the request to.
        :type uri_path: str
        :param data: The data to send in the request body.
        :type data: dict
        :return: The response from the Kraken API.
        :rtype: requests.Response
        """
        if data.get("nonce") == None:
            data["nonce"] = self.get_nonce()
        
        headers = {}
        
        headers['API-Key'] = self.api_key
        headers['API-Sign'] = self.get_signature('/0'+uri_path, data, self.api_sec)

        req = requests.post(
            url=(self.api_base_url + uri_path),
            headers=headers,
            data=data
        )

        return req
    
    def get_nonce(self):
        return str(int(1000*time.time()))
    
    def get_exchange_status(self):
        response = self.public_request('/public/SystemStatus')
        return response.json()
    
    def add_order(self, ordertype, type, volume, pair, userref=0, price='', price2='', trigger='', timeinforce='GTC', starttm='', expiretm='', deadline=''):
        """Add an order."""
        # https://docs.kraken.com/rest/#tag/Trading/operation/addOrder
        payload = {
            "ordertype": ordertype,
            "type": type,
            "volume": volume,
            "pair": pair
        }

        if userref != 0:
            payload["userref"] = userref
        
        if price != '':
            payload["price"] = price
        
        if price2 != '':
            payload["price2"] = price2
        
        if trigger != '':
            payload["trigger"] = trigger
        
        if timeinforce != 'GTC':
            payload["timeinforce"] = timeinforce
        
        if starttm != '':
            payload["starttm"] = starttm
        
        if expiretm != '':
            payload["expiretm"] = expiretm
        
        if deadline != '':
            payload["deadline"] = deadline
        
        response = self.authenticated_request('/private/AddOrder', payload)

        return response.json()
    
    def add_order_batch(self, orders, pair, deadline=''):
        """Add a batch of orders at once."""
        payload = {
            "orders": orders,
            "pair": pair
        }

        if deadline != '':
            payload["deadline"] = deadline
        
        response = self.authenticated_request('/private/AddOrderBatch', payload)

        return response.json()
    
    def edit_order(self, txid, pair, userref=0, volume='', price='', price2='', deadline=''):
        """Edit an open order by its txid."""
        # https://docs.kraken.com/rest/#tag/Trading/operation/editOrder
        payload = {
            "txid": txid,
            "pair": pair
        }

        if userref != 0:
            payload["userref"] = userref
        
        if volume != '':
            payload["volume"] = volume
        
        if price != '':
            payload["price"] = price
        
        if price2 != '':
            payload["price2"] = price2
        
        if deadline != '':
            payload["deadline"] = deadline
        
        response = self.authenticated_request('/private/EditOrder', payload)

        return response.json()
    
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

        return response.json()
    
    def cancel_order_batch(self, orders):
        """Cancel a batch of orders at once."""

        # Here orders is a list of txids
        payload = {
            "orders": orders
        }

        response = self.authenticated_request('/private/CancelOrderBatch', payload)

        return response.json()
    
    def get_account_balance(self):
        """Retrieve all cash balances, net of pending withdrawals."""
        # https://docs.kraken.com/rest/#tag/Account-Data/operation/getAccountBalance
        response = self.authenticated_request('/private/Balance')
        return response.json()
    
    def get_extended_balance(self):
        """Retrieve all extended account balances, including credits and held amounts. Balance available for trading is calculated as: available balance = balance + credit - credit_used - hold_trade."""
        # https://docs.kraken.com/rest/#tag/Account-Data/operation/getExtendedBalance
        response = self.authenticated_request('/private/BalanceEx')
        return response.json()
    
    def get_trade_balance(self, asset='ZUSD'):
        """Retrieve a summary of collateral balances, margin position valuations, equity and margin level."""
        # https://docs.kraken.com/rest/#tag/Account-Data/operation/getTradeBalance
        payload = {
            "asset": asset
        }

        response = self.authenticated_request('/private/TradeBalance', payload)

        return response.json()
    
    def get_open_orders(self, trades=False, userref=0):
        """Retrieve information about currently open orders."""
        # https://docs.kraken.com/rest/#tag/Account-Data/operation/getOpenOrders
        payload = {
            "trades": trades
        }

        if userref != 0:
            payload["userref"] = userref
        
        response = self.authenticated_request('/private/OpenOrders', payload)

        return response.json()
    
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

        return response.json()
    
    def get_websockets_token(self):
        """Get a websocket token for Kraken's WebSockets API."""
        # https://docs.kraken.com/rest/#tag/Websockets-Authentication/operation/getWebsocketsToken
        response = self.authenticated_request('/private/GetWebSocketsToken')

        return response.json()

class CoinbaseExchange(Exchange):
    def __init__(self, api_key='', api_sec='', api_passphrase=''):
        super().__init__()
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
    def __init__(self):
        super().__init__()
    
    def login(self):
        """
        Logs the user in with username and password with verification by sms text. This method does not store the session.
        """
        time_logged_in = 60 * 60 * 24 * self.days_to_run
        
        rh.authentication.login(expiresIn=time_logged_in,
                                scope='internal',
                                by_sms=True,
                                store_session=False)
        
        print("login successful")
    
    def logout(self):
        """
        Attempts to log out the user unless already logged out.
        """
        try:
            rh.authentication.logout()
            
            print('logout successful')
        except:
            print('already logged out: logout() can only be called when currently logged in')