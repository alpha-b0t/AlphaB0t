class Order():
    def __init__(self):
        pass

class KrakenOrder(Order):
    def __init__(self, txid):
        self.txid = txid
