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
    def __init__(self, api_key, api_sec, pair, days_to_run, mode, upper_price, lower_price, level_num, cash, stop_loss, take_profit, base_currency):
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
        self.base_currency = base_currency

        self.check_config()
    
    def check_config(self):
        """Throws an error if the configurations are not correct."""
        # TODO: Implement
        assert True
    
    def init_grid(self):
        """Initializes grids."""
        self.grids = []

        cash_per_level = round_down_to_cents(self.cash / self.level_num)

        # Determine what the prices are at each level
        prices = []
        for i in range(self.level_num):
            prices.append(self.lower_price + i*(self.upper_price - self.lower_price)/(self.level_num-1))
        
        # Get latest OHLC data
        ohlc_data_response = self.exchange.get_ohlc_data(self.pair)

        ohlc_data = ohlc_data_response['result']

        keys = list(ohlc_data.keys())

        for i in range(len(keys)):
            if keys[i] != 'last':
                key = keys[i]
                break
        
        # latest_ohlc looks like [int time, str open, str high, str low, str close, str vwap, str volume, int count]
        latest_ohlc = ohlc_data[key][-1]
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
        
        # Determine amount of dollars to buy initial amount of cryptocurrency
        grid_level_initial_buy_count = 0
        for i in range(len(self.grids)):
            if self.grids[i].side == 'sell' and self.grids[i].status == 'active':
                grid_level_initial_buy_count += 1
        
        initial_buy_amount = grid_level_initial_buy_count * self.cash_per_level

        # Place a buy order for the initial amount to sell
        self.exchange.add_order(
            ordertype='limit',
            type='buy',
            volume=initial_buy_amount / latest_close,
            pair=self.pair,
            price=latest_close,
            oflags='post',
        )

        # Place limit buy orders and limit sell orders
        for i in range(self.grids):
            if self.grids[i].status == 'active':
                if self.grids[i].side == 'buy':
                    self.grids[i].order = self.exchange.add_order(
                        ordertype='limit',
                        type='buy',
                        volume=self.grids[i].cash_per_level/self.grids[i].limit_price,
                        pair=self.pair,
                        price=self.grids[i].limit_price,
                        oflags='post'
                    )
                elif self.grids[i].side == 'sell':
                    self.grids[i].order = self.exchange.add_order(
                        ordertype='limit',
                        type='sell',
                        volume=self.grids[i].cash_per_level/self.grids[i].limit_price,
                        pair=self.pair,
                        price=self.grids[i].limit_price,
                        oflags='post'
                    )
    
    def get_account_cash_balance(self, pair: str) -> float:
        """Retrieves the cash balance of the pair/currency, net of pending withdrawals."""
        account_balances = self.exchange.get_account_balance()
        
        return float(account_balances['result'].get(pair, 0))
    
    def get_available_trade_balance(self) -> dict:
        """Retrieves the balance(s) available for trading."""
        extended_balances = self.exchange.get_extended_balance()
        
        available_balances = {}

        for asset, extended_balance in extended_balances['result'].items():
            available_balances[asset] = extended_balance['asset'].get('balance', 0) + extended_balance['asset'].get('credit', 0) - extended_balance['asset'].get('credit_used', 0) - extended_balance['asset'].get('hold_trade', 0)
        
        return available_balances
    
    def start(self):
        try:
            self.init_grid()
        except Exception as e:
            raise e
    
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
