from dotenv import dotenv_values
import inspect
from constants import CLASS_NAMES

class AppConfig():
    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)

        self.DATABASE_USERNAME = env_config['DATABASE_USERNAME']
        self.DATABASE_PASSWORD = env_config['DATABASE_PASSWORD']
        self.DATABASE_PORT = env_config['DATABASE_PORT']
        self.DATABASE_NAME = env_config['DATABASE_NAME']
    
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

class RequestConfig():
    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)

        self.request = env_config['REQUEST']
    
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

class GRIDBotConfig():
    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)

        self.exchange_name = env_config['EXCHANGE']
        self.name = env_config['NAME']
        self.pair = env_config['PAIR']
        self.base_currency = env_config['BASE_CURRENCY']
        self.days_to_run = int(env_config['DAYS_TO_RUN'])
        self.mode = env_config['MODE']

        if self.mode is None or self.mode == '':
            self.mode = 'test'
        
        self.upper_price = float(env_config['UPPER_PRICE'])
        self.lower_price = float(env_config['LOWER_PRICE'])
        self.level_num = int(env_config['LEVEL_NUM'])
        self.quantity_per_grid = float(env_config['QUANTITY_PER_GRID'])
        self.total_investment = float(env_config['TOTAL_INVESTMENT'])
        self.stop_loss = float(env_config['STOP_LOSS'])
        self.take_profit = float(env_config['TAKE_PROFIT'])
        self.latency_in_sec = float(env_config['LATENCY_IN_SEC'])
        self.max_error_count = int(env_config['MAX_ERROR_COUNT'])
        self.error_latency_in_sec = float(env_config['ERROR_LATENCY_IN_SEC'])
        self.init_buy_error_latency_in_sec = float(env_config['INIT_BUY_ERROR_LATENCY_IN_SEC'])
        self.init_buy_error_max_count = int(env_config['INIT_BUY_ERROR_MAX_COUNT'])
        self.cancel_orders_upon_exit = env_config['CANCEL_ORDERS_UPON_EXIT']
    
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

class CoinMarketCapAPIConfig():
    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)

        self.cmc_api_key = env_config['CMC_API_KEY']
    
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

class ExchangeConfig():
    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)

        self.exchange_name = env_config['EXCHANGE']
        self.api_key = env_config['API_KEY']

        if self.api_key is None:
            self.api_key = ''

        self.api_sec = env_config['API_SEC']

        if self.api_sec is None:
            self.api_sec = ''
        
        self.api_passphrase = env_config['API_PASSPHRASE']

        if self.api_passphrase is None:
            self.api_passphrase = ''
        
        self.mode = env_config['MODE']

        if self.mode is None or self.mode == '':
            self.mode = 'test'
    
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

class StrategyConfig():
    # TODO: Finish implementing
    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)

        self.exchange_name = env_config['EXCHANGE']
        self.api_key = env_config['API_KEY']

        if self.api_key is None:
            self.api_key = ''

        self.api_sec = env_config['API_SEC']

        if self.api_sec is None:
            self.api_sec = ''
        
        self.api_passphrase = env_config['API_PASSPHRASE']

        if self.api_passphrase is None:
            self.api_passphrase = ''
        
        self.mode = env_config['MODE']

        if self.mode is None or self.mode == '':
            self.mode = 'test'
    
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
