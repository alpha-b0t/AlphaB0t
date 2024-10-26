import inspect
from constants import CLASS_NAMES

class Grid():
    def __init__(self, level_num, limit_price, quantity, side, status, order=None):
        self.classname = self.__class__.__name__
        self.level_num = level_num
        self.limit_price = limit_price
        self.quantity = quantity
        self.side = side
        self.status = status
        self.order = order
    
    def __repr__(self):
        return f"{{{self.classname} level_num: {self.level_num}, limit_price: {self.limit_price}, quantity: {self.quantity}, side: {self.side}, status: {self.status}, order: {self.order}}}"
    
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
