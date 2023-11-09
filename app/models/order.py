class Order():
    def __init__(self, ordertype, type, volume, pair, price):
        self.ordertype = ordertype
        self.type = type
        self.volume = volume
        self.pair = pair
        self.price = price

class KrakenOrder(Order):
    def __init__(self, ordertype, type, volume, pair, txid=0, userref=0, price='', price2='', trigger='', oflags='', timeinforce='', starttm='', expiretm='', deadline=''):
        self.ordertype = ordertype
        self.type = type
        self.volume = volume
        self.pair = pair
        self.txid = txid
        self.userref = userref
        self.price = price
        self.price2 = price2
        self.trigger = trigger
        self.oflags = oflags
        self.timeinforce = timeinforce
        self.starttm = starttm
        self.expiretm = expiretm
        self.deadline = deadline