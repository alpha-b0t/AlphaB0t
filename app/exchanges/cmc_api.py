import requests
import inspect
from constants import CLASS_NAMES

class CoinMarketCapAPI():
    def __init__(self, api_key={}):
        self.classname = self.__class__.__name__
        if type(api_key) == dict:
            # Reloading
            print(f"Reloading {self.classname}...")
            return
        
        self.base_api = 'https://pro-api.coinmarketcap.com/v3'
        self.api_key = api_key
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': api_key
        }
    
    def __repr__(self):
        if self.api_key == '':
            api_key_display = "''"
        else:
            api_key_display = '******'
        
        return f"{{{self.classname} api_key: {api_key_display}, base_api: {self.base_api}}}"

    def get_fear_and_greed_latest(self):
        response = requests.get(url=f"{self.base_api}/fear-and-greed/latest", headers=self.headers)
        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def get_fear_and_greed_historical(self, start: int = -1, limit: int = 50):
        params = {}

        if limit != 50:
            params["limit"] = limit

        if start != -1:
            params["start"] = start

        response = requests.get(url=f"{self.base_api}/fear-and-greed/historical", params=params, headers=self.headers)
        result = response.json()
        self.handle_response_errors(result)
        return result
    
    def handle_response_errors(self, response):
        try:
            status = response.get('status', {})
            error_code = status.get('error_code', response.get('error_code', 0))
            if error_code != 0:
                error_message = status.get('error_message', response.get('error_message', 'Unknown error'))
                raise ValueError(f"CoinMarketCap API error {error_code}: {error_message}")
        except (AttributeError, TypeError) as e:
            print(f"response: {response}")
            raise ValueError(f"Unexpected response format: {e}")
    
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
