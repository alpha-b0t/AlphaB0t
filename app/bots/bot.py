import inspect
from constants import CLASS_NAMES
import json
from app.helpers.json_util import CustomEncoder

# The following imports are needed for loading the objects from JSON
from app.exchanges.cmc_api import CoinMarketCapAPI
from app.exchanges.exchange import Exchange, KrakenExchange, CoinbaseExchange, RobinhoodCryptoExchange, RobinhoodOptionExchange
from app.strategies.grid import Grid
from app.strategies.ohlc import OHLC
from app.strategies.order import Order, KrakenOrder
from app.models.result import Result
from app.strategies.strategy import Strategy, GridStrategy, LSTMStrategy
from app.riskmanager import RiskManager
from app.positionmanager import PositionManager
from config import AppConfig, RequestConfig, BotConfig, GRIDBotConfig, CoinMarketCapAPIConfig, ExchangeConfig, StrategyConfig, RiskManagerConfig
# Don't need to import class inherited from Bot

class Bot():
    # Responsible for placing orders, executing strategy, managing risk through RiskManager, and monitoring orders and positions through PositionManager
    def __init__(self, bot_config: BotConfig={}, exchange: Exchange={}, strategy: Strategy={}, risk_manager: RiskManager={}):
        self.classname = self.__class__.__name__
    
    def run(self):
        # TODO: Implement
        raise NotImplementedError("Not Implemented.")
    
    def get_runtime(self):
        raise NotImplementedError("Not Implemented.")
    
    def check_config(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_account_asset_balance(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_available_trade_balance(self):
        raise NotImplementedError("Not Implemented.")
    
    def fetch_balances(self):
        raise NotImplementedError("Not Implemented.")
    
    def fetch_latest_ohlc(self):
        raise NotImplementedError("Not Implemented.")
    
    def fetch_latest_ohlc_pair(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_realized_gain(self):
        raise NotImplementedError("Not Implemented.")
    
    def get_unrealized_gain(self):
        raise NotImplementedError("Not Implemented.")
    
    def stop(self):
        raise NotImplementedError("Not Implemented.")
    
    def pause(self):
        raise NotImplementedError("Not Implemented.")
    
    def update(self):
        raise NotImplementedError("Not Implemented.")
    
    def simulate_trading(self):
        raise NotImplementedError("Not Implemented.")
    
    def to_json_file(self, filename):
        data = vars(self)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4, cls=CustomEncoder)

    @classmethod
    def from_json_file(cls, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Get the parameters of the __init__ method
        init_params = inspect.signature(cls.__init__).parameters

        # Extract known attributes
        known_attributes = {param for param in init_params if param != 'self'}
        known_data = {k: v for k, v in data.items() if k in known_attributes}

        # Extract additional attributes
        additional_data = {k: v for k, v in data.items() if k not in known_attributes}

        # Create instance with known attributes
        instance = cls(**known_data)

        # Set known attributes (to be safe)
        for key, value in known_data.items():
            setattr(instance, key, cls.recursive_object_creation(value))

        # Set additional attributes
        for key, value in additional_data.items():
            setattr(instance, key, cls.recursive_object_creation(value))
        
        return instance
    
    @classmethod
    def recursive_object_creation(cls, data):
        if isinstance(data, dict):
            if 'classname' in data and data['classname'] in CLASS_NAMES:
                print(f"CLASS_NAMES: data['classname']: {data['classname']}")
                # If the data is a dictionary with a 'classname' key, create an instance of the class
                try:
                    obj = globals()[data['classname']](*[data[attr] for attr in inspect.signature(globals()[data['classname']]).parameters.keys() if attr != 'self'])
                except KeyError as e:
                    print(f"\nglobals().keys(): {globals()}\n")
                    # print(f"globals()[data['classname']]: {globals()[data['classname']]}")
                    raise e
                for key, value in data.items():
                    if key != 'classname':
                        # Recursively set additional attributes
                        setattr(obj, key, cls.recursive_object_creation(value))
                return obj
            else:
                print(f"REGULAR: data: {data}")
                # If the data is a regular dictionary, recursively handle its values
                return {k: cls.recursive_object_creation(v) for k, v in data.items()}
        elif isinstance(data, list):
            # If the data is a list, recursively handle each element in the list
            return [cls.recursive_object_creation(item) for item in data]
        else:
            # Base case: return data as is
            return data
