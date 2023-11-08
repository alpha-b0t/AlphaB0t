from app.models.exchange import Exchange, KrakenExchange, CoinbaseExchange, RobinhoodCryptoExchange

class GRIDBot():
    def __init__(self, exchange, pair, days_to_run, mode, upper_price, lower_price, level_num, cash, stop_loss, take_profit):
        self.exchange = exchange
        self.pair = pair
        self.days_to_run = days_to_run
        self.mode = mode
        self.upper_price = upper_price
        self.lower_price = lower_price
        self.level_num = level_num
        self.cash = cash
        self.stop_loss = stop_loss
        self.take_profit = take_profit
    
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def pause(self):
        pass
    
    def resume(self):
        pass
    
    def update(self):
        pass

    def simulate_trading(self):
        pass

class KrakenGRIDBot(GRIDBot):
    def __init__(self, api_key, api_sec, pair, days_to_run, mode, upper_price, lower_price, level_num, cash, stop_loss, take_profit):
        self.exchange_name = "Kraken"
        
        self.exchange = KrakenExchange(api_key, api_sec, pair, mode)

        self.pair = pair
        self.days_to_run = days_to_run
        self.mode = mode
        self.upper_price = upper_price
        self.lower_price = lower_price
        self.level_num = level_num
        self.cash = cash
        self.stop_loss = stop_loss
        self.take_profit = take_profit
    
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def pause(self):
        pass
    
    def resume(self):
        pass
    
    def update(self):
        pass

    def simulate_trading(self):
        pass
