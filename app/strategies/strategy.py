from config import StrategyConfig # Needed for children of parent class Strategy
import inspect
from constants import CLASS_NAMES

class Strategy():
    # TODO: Finish implementing (along with StrategyConfig in config.py)
    def __init__(self, exchange, params):
        self.classname = self.__class__.__name__
        self.exchange = exchange
        self.params = params
    
    def calculate_position_size(self, balance: float, price: float) -> float:
        """Calculate how much to buy/sell"""
        raise NotImplementedError
    
    def get_required_data(self) -> list:
        """Return required data types (OHLCV, indicators, etc.)"""
        raise NotImplementedError
        
    def update_indicators(self, new_data: dict):
        """Update internal indicators with new data"""
        raise NotImplementedError
        
    def get_parameters(self) -> dict:
        """Return current strategy parameters"""
        return self.params
    
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