import inspect
from constants import CLASS_NAMES

class OHLC:
    def __init__(self, ohlc_data: list=[]):
        self.classname = self.__class__.__name__
        if ohlc_data == []:
            # Reloading
            print(f"Reloading {self.classname}...")
            return
        
        self.ohlc_data = []
        
        self.time = ohlc_data[0]
        self.open = float(ohlc_data[1])
        self.high = float(ohlc_data[2])
        self.low = float(ohlc_data[3])
        self.close = float(ohlc_data[4])
        self.vwap = float(ohlc_data[5])
        self.volume = float(ohlc_data[6])
        self.count = ohlc_data[7]
    
    def __repr__(self):
        return f"{{{self.classname} time: {self.time}, open: {self.open}, high: {self.high}, low: {self.low}, close: {self.close}, vwap: {self.vwap}, volume: {self.volume}, count: {self.count}}}"
    
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
