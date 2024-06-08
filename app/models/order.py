import inspect
from constants import CLASS_NAMES

class Order():
    def __init__(self):
        self.classname = 'Order'
    
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

class KrakenOrder(Order):
    def __init__(self, txid='', order_data={}):
        self.classname = 'KrakenOrder'
        self.txid = txid
        self.order_data = {}
        
        if order_data != {}:
            for key, value in order_data.items():
                if key != 'txid':
                    setattr(self, key, value)
    
    def __repr__(self):
        if self.txid == '':
            repr_str = f"{{Order txid: ''"
        else:
            repr_str = f"{{Order txid: {self.txid}"

        for key, value in self.__dict__.items():
            if key != 'txid':
                repr_str += f", {key}: {value}"
        
        repr_str += '}'
        return repr_str
    
    def update(self, order_data: dict):
        for key, value in order_data.items():
            if key != 'txid':
                setattr(self, key, value)
            elif value != self.txid:
                    print(f"Received different txid when updating: received={value}, original={self.txid}")
    
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
