import robin_stocks.robinhood as rh
import requests
import urllib.parse
import hashlib
import hmac
import base64
import time

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
    
    def create_buy_order(self):
        pass
    
    def cancel_buy_order(self):
        pass
    
    def create_sell_order(self):
        pass
    
    def cancel_sell_order(self):
        pass

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

class KrakenExchange(Exchange):
    def __init__(self, api_key, api_sec):
        super().__init__()
        self.api_key = api_key
        self.api_sec = api_sec
        self.base_url = "https://api.kraken.com"
    
    def login(self):
        pass
    
    def logout(self):
        pass

    def get_latest_quote(self, symbol):
        return self.kraken_public_request("/0/public/OHLC", query_parameters={"pair": symbol}).json()
    
    def kraken_public_request(self, uri_path, query_parameters={}):
        url = self.base_url + uri_path

        if query_parameters != {}:
            url += '?'
            key_count = 0
            for key in query_parameters.keys():
                if key_count != 0:
                    url += '&'
                
                url += f"{key}={query_parameters[key]}"
                key_count += 1
        
        response = requests.get(url)
        return response
    
    def get_kraken_signature(self, urlpath, data, secret) -> str:

        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()
    
    def kraken_authenticated_request(self, uri_path, data):
        headers = {}
        
        headers['API-Key'] = self.api_key
        headers['API-Sign'] = self.get_kraken_signature(uri_path, data, self.api_sec)     

        if data.get("nonce") == None:
            data["nonce"] = self.get_nonce()

        req = requests.post(
            url=(self.base_url + uri_path),
            headers=headers,
            data=data
        )

        return req
    
    def get_nonce(self):
        return str(int(1000*time.time()))
    
    def get_exchange_status(self):
        return self.kraken_public_request('/0/public/SystemStatus').json()