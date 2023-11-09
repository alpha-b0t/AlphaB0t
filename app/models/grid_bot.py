from app.models.exchange import Exchange, KrakenExchange, CoinbaseExchange, RobinhoodCryptoExchange
from app.models.grid import Grid
from app.helpers.format import round_down_to_cents

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

        self.check_inputs()

        self.init_grid()
    
    def check_inputs(self):
        # TODO: Implement
        assert True
    
    def init_grid(self):
        # TODO: Implement
        self.grids = []

        cash_per_level = round_down_to_cents(self.cash / self.level_num)

        # Determine what the prices are at each level
        prices = []
        for i in range(self.level_num):
            prices.append(self.lower_price + i*(self.upper_price - self.lower_price)/(self.level_num-1))
        
        # Get latest OHLC data
        ohlc_data_response = self.exchange.get_ohlc_data(self.pair)

        ohlc_data = ohlc_data_response["result"]

        keys = list(ohlc_data.keys())

        for i in range(len(keys)):
            if keys[i] != 'last':
                key = keys[i]
                break
        
        # latest_ohlc looks like [int time, str open, str high, str low, str close, str vwap, str volume, int count]
        latest_ohlc = ohlc_data[key][0]
        latest_close = float(latest_ohlc[4])

        # Mark orders as buys and sells
        side = []
        for i in range(self.level_num):
            if latest_close > prices[i]:
                side.append('buy')
            else:
                side.append('sell')
        
        # Determine which grid line is closest to the current price
        min_dist = float('inf')
        self.closest_grid = -1

        for i in range(self.level_num):
            dist = abs(prices[i] - latest_close)

            if dist < min_dist:
                min_dist = dist
                self.closest_grid = i
        
        # Mark the closest grid line as inactive
        status = ['active' for i in range(self.level_num)]
        status[self.closest_grid] = 'inactive'

        for i in range(self.level_num):
            self.grids.append(Grid(i, prices[i], cash_per_level, side[i], status[i]))
        
        # TODO: Add orders to grids
    
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
