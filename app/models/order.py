class Order():
    def __init__(self):
        pass

class KrakenOrder(Order):
    def __init__(self, txid='', order_data={}):
        self.txid = txid
        
        if order_data != {}:
            for key, value in order_data.items():
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
            else:
                if value != self.txid:
                    print(f"Recieved different txid when updating: recieved={value}, original={self.txid}")
