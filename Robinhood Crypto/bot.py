import robin_stocks.robinhood as rh
from order import *
import math
import time as t

class SpotGridTradingBot():
    def __init__(self, config):
        """
        config = {
            'crypto': 'BTC',
            'days_to_run': 1,
            'mode': '',
            'backtest': {
                'interval': '',
                'span': '',
                'bounds': '',
            },
            'upper_price': 56.23,
            'lower_price': 23.56,
            'level_num': 10,
            'cash': 2000,
            'loss_threshold': 50.00,
            'loss_percentage': 5.00,
            'latency_in_sec': 50
        }
        """
        self.check_config(config)

        self.crypto = config['crypto']
        self.days_to_run = int(config['days_to_run'])
        self.mode = config['mode']
        # self.backtest_interval = config['backtest']['interval']
        # self.backtest_span = config['backtest']['span']
        # self.backtest_bounds = config['backtest']['bounds']
        self.upper_price = float(config['upper_price'])
        self.lower_price = float(config['lower_price'])
        self.level_num = int(config['level_num'])
        self.cash = float(config['cash'])
        self.loss_threshold = float(config['loss_threshold'])
        self.loss_percentage = float(config['loss_percentage'])
        self.latency = float(config['latency_in_sec'])

        self.login()

        try:
            self.holdings, self.bought_price = self.get_holdings_and_bought_price()
            self.available_cash, self.equity = self.retrieve_cash_and_equity()

            self.initial_cash = self.available_cash
            self.initial_crypto_capital = self.get_crypto_holdings_capital()

            self.profit = 0.00
            self.percent_change = 0.00

            assert self.available_cash >= self.cash
        except:
            self.logout()

            raise Exception
    
    def check_config(self, config):
        """
        TO-DO: IMPLEMENT
        Assures that the configuration is as expected. Raises an exception if an error is found.
        """
        assert isinstance(config['crypto'], str), 'crypto should be of type str'
        assert len(config['crypto']) > 0
        assert isinstance(config['days_to_run'], int), 'days_to_run should be of type int'
        assert config['days_to_run'] >= 1
        assert isinstance(config['mode'], str), 'mode should be of type str'
        # assert isinstance(config['backtest']['interval'], str), 'backtest.interval should be of type str'
        # assert isinstance(config['backtest']['span'], str), 'backtest.span should be of type str'
        # assert isinstance(config['backtest']['bounds'], str), 'backtest.bounds should be of type str'
        assert type(config['upper_price']) == float or type(config['upper_price']) == int
        assert config['upper_price'] > 0
        assert type(config['lower_price']) == float or type(config['lower_price']) == int
        assert config['lower_price'] > 0
        assert isinstance(config['level_num'], int), 'level_num should be of type int'
        assert config['level_num'] >= 2
        assert type(config['cash']) == float or type(config['cash']) == int
        assert config['cash'] > 0
        assert type(config['loss_threshold']) == float or type(config['loss_threshold']) == int
        assert config['loss_threshold'] > 0
        assert type(config['loss_percentage']) == float or type(config['loss_percentage']) == int
        assert config['loss_percentage'] > 0
        assert type(config['latency_in_sec']) == float or type(config['latency_in_sec']) == int
        assert config['latency_in_sec'] > 0

        print("configuration test: PASSED")
    
    def login(self):
        """
        Logs the user in with username and password with verification by sms text. This method does not store the session.
        """
        time_logged_in = 60 * 60 * 24 * self.days_to_run
        
        rh.authentication.login(expiresIn=time_logged_in,
                                scope='internal',
                                by_sms=True,
                                store_session=False)
        
        print("login successful")
    
    def logout(self):
        """
        Attempts to log out the user unless already logged out.
        """
        try:
            rh.authentication.logout()
            
            print('logout successful')
        except:
            print('already logged out: logout() can only be called when currently logged in')
    
    def run(self):
        try:
            self.init_levels_and_orders()

            # Check continue_trading
            while self.continue_trading():
                self.update_orders()

                t.sleep(self.latency)

                self.fetch_stats()
                self.update_output()
            
            # Cancel all open crypto orders
            cancel_all_orders()

            # Log out
            self.logout()
        
        except KeyboardInterrupt:
            print("User ended execution of program.")
            
            cancel_all_orders()
            self.logout()
        
        except TypeError:
            # Robinhood Internal Error
            # 503 Server Error: Service Unavailable for url: https://api.robinhood.com/marketdata/forex/quotes/76637d50-c702-4ed1-bcb5-5b0732a81f48/
            print("Robinhood Internal Error: TypeError: continuing trading")
            
            # Continue trading
            self.run()
        
        except KeyError:
            # Robinhood Internal Error
            # 503 Service Error: Service Unavailable for url: https://api.robinhood.com/portfolios/
            # 500 Server Error: Internal Server Error for url: https://api.robinhood.com/portfolios/
            print("Robinhood Internal Error: KeyError: continuing trading")
            
            # Continue trading
            self.run()
        
        except Exception:
            print("An unexpected error occured: cancelling open orders and logging out")
            
            cancel_all_orders()
            self.logout()
            
            raise Exception
    
    def fetch_stats(self):
        """
        Updates available_cash, equity, holdings, bought_price, profit, and percent_change
        """
        self.available_cash, self.equity = self.retrieve_cash_and_equity()

        self.holdings, self.bought_price = self.get_holdings_and_bought_price()

        self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital

        self.percent_change = self.profit * 100 / (self.initial_cash + self.initial_crypto_capital)
    
    def continue_trading(self, override=None):
        """
        Returns true if loss has not exceeded loss threshold or loss percentage threshold. If either loss threshold or loss percentage threshold have been passed then False is returned.
        If the bool parameter override is passed into the function, then override is returned by the function.
        """
        if override != None:
            assert type(override) == bool
            
            return override
        else:
            if self.profit >= -1 * self.loss_threshold:
                if self.percent_change >= -1 * self.loss_percentage:
                    return True
                else:
                    print("Loss percentage exceeded " + str(self.loss_percentage) + "%: terminating automated trading")
                    
                    return False
            else:
                print("Loss exceeded $" + str(self.loss_threshold) + ": terminating automated trading")
                
                return False
    
    def update_output(self):
        """
        Prints out the lastest information out to console
        """
        
        print("============================================")
        
        print("mode: " + self.mode)
        print("runtime: " + self.display_time(self.get_runtime()))
        
        print("equity: $" + str(round(self.equity, 2)))
        
        print('crypto holdings:')
        print(self.display_holdings())
        
        print("crypto equity: $" + str(round(self.get_crypto_holdings_capital(), 2)))
        print("cash: $" + str(round(self.available_cash, 2)))
        print("crypto equity and cash: $" + str(round(self.available_cash + self.get_crypto_holdings_capital(), 2)))
        
        print("profit: " + self.display_profit() + " (" + self.display_percent_change() + ")")

        print("number of pending orders:", len(get_all_open_orders()))
        print("levels:", self.levels)
    
    def round_down_to_2(self, value):
        """
        Converts a float to two decimal places and rounds down

        E.g.
        26.537 -> 26.53
        26.531 -> 26.53
        -26.539 -> -26.53
        """
        if value < 0:
            return math.ceil(value * 100)/100.0
        else:
            return math.floor(value * 100)/100.0
    
    def get_latest_quote(self, crypto_symbol):
        """
        Returns a dictionary of the latest quote of the cryptocurrency.
        Dictionary Keys:
            ask_price
            bid_price
            high_price
            id
            low_price
            mark_price
            open_price
            symbol
            volume
        """
        return rh.crypto.get_crypto_quote(crypto_symbol)
    
    def init_levels_and_orders(self):
        self.start_time = t.time()
        self.levels = {}
        self.levels[1] = {'price': self.lower_price}
        self.levels[10] = {'price': self.upper_price}

        self.amount_per_level = self.round_down_to_2(self.cash / self.level_num)

        # Determine what the prices are at each level
        for i in range(2, self.level_num):
            self.levels[i] = {'price': self.round_down_to_2(self.lower_price + (i-1)*(self.upper_price - self.lower_price)/(self.level_num-1))}
        
        print(self.levels)

        # Get crypto quote
        self.crypto_quote = self.get_latest_quote(self.crypto)

        """
        Notes:
        - ask_price > bid_price due to spread (0.3-0.4%)
        - Everything below ask_price is buy
        - Everything above bid_price is sell
        - But if spread is very large and they overlap, ignore the overlapping level(s)
        """

        # Mark buys and sells
        for i in range(len(self.levels)):
            if self.crypto_quote['ask_price'] > self.levels[i+1]['price']:
                self.levels[i+1]['side'] = 'buy'
            else:
                self.levels[i+1]['side'] = 'sell'
        
        print(self.levels)

        # Determine which level is closest to the current price
        min_dist = float('inf')
        self.closest_level_index = -1

        for i in range(len(self.levels)):
            dist = abs(self.levels[i+1]['price'] - self.crypto_quote['mark_price'])

            if dist < min_dist:
                min_dist = dist
                self.closest_level_index = i+1
        
        # Mark the closest level is inactive
        self.levels[self.closest_level_index]['status'] = 'inactive'

        # Mark teh other levels as active
        for i in range(len(self.levels)):
            if i+1 != self.closest_level_index:
                self.levels[i+1]['status'] = 'active'
        
        # Place buy and sell orders
        for i in range(len(self.levels)):
            if self.levels[i+1]['side'] == 'buy' and self.levels[i+1]['status'] == 'active':
                self.levels[i+1]['order'] = [Order(rh.orders.order_buy_crypto_limit_by_price(self.crypto, self.amount_per_level, self.levels[i+1]['price'], timeInForce='gtc', jsonify=True))]
            elif self.levels[i+1]['side'] == 'sell' and self.levels[i+1]['status'] == 'active':
                self.levels[i+1]['order'] = [Order(rh.orders.order_sell_crypto_limit_by_price(self.crypto, self.amount_per_level, self.levels[i+1]['price'], timeInForce='gtc', jsonify=True))]
            else:
                self.levels[i+1]['order'] = None
    
    def update_orders(self):
        # Update orders
        for i in range(len(self.levels)):
            self.levels[i+1]['order'].update()

            if self.levels[i+1]['order'].is_filled():
                if self.level[i+1]['side'] == 'buy' and self.closest_level_index == i+2:
                    # If the filled order was a buy order, place a sell order on the level above it, assuming it was previously inactive

                    # Set the filled level to inactive and adjust the inactive index
                    self.levels[i+1]['status'] = 'inactive'
                    self.closest_level_index = i+1

                    # Place a sell order on level i+2
                    self.levels[i+2]['side'] = 'sell'
                    self.levels[i+2]['status'] = 'active'
                    
                    self.levels[i+2]['order'] = [Order(rh.orders.order_sell_crypto_limit_by_price(self.crypto, self.amount_per_level, self.levels[i+2]['price'], timeInForce='gtc', jsonify=True))]
                elif self.level[i+1]['side'] == 'sell' and self.closest_level_index == i:
                    # If the filled order was a sell order, place a buy order on the level below it, assuming it was previously inactive

                    # Set the filled level to inactive and adjust the inactive index
                    self.levels[i+1]['status'] = 'inactive'
                    self.closest_level_index = i+1

                    # Place a buy order on level i
                    self.levels[i]['side'] = 'buy'
                    self.levels[i]['status'] = 'active'

                    self.levels[i]['order'] = [Order(rh.orders.order_buy_crypto_limit_by_price(self.crypto, self.amount_per_level, self.levels[i]['price'], timeInForce='gtc', jsonify=True))]
                else:
                    raise Exception
    
    def build_holdings(self):
        """
        Returns {
            'crypto1': {
                'price': '76.24',
                'quantity': '2.00',
                'average_buy_price': '79.26',
                },
            'crypto2': {
                'price': '76.24',
                'quantity': '2.00',
                'average_buy_price': '79.26',
                }}
        """
        
        holdings_data = rh.crypto.get_crypto_positions()
        
        build_holdings_data = dict()
        
        for i in range(len(holdings_data)):
            nested_data = dict()
            
            nested_data['price'] = self.get_latest_quote(holdings_data[i]["currency"]["code"])['mark_price']
            nested_data['quantity'] = holdings_data[i]["quantity"]
            
            try:
                nested_data['average_buy_price'] = str(float(holdings_data[i]["cost_bases"][0]["direct_cost_basis"]) / float(nested_data["quantity"]))
            except ZeroDivisionError:
                nested_data['average_buy_price'] = '-'
            
            build_holdings_data[holdings_data[i]["currency"]["code"]] = nested_data
        
        return build_holdings_data
    
    def get_holdings_and_bought_price(self):
        """
        Returns two dictionaries, holdings and bought_price, in the following format
        E.g.
            holdings = {'BTC': 1.25, 'ETH': 0.50}
            bought_price = {'BTC': 19784.21, 'ETH': 1923.61}
        """
        holdings = {self.crypto: 0}
        bought_price = {self.crypto: 0}
        
        rh_holdings = self.build_holdings()

        try:
            holdings[self.crypto] = round(float(rh_holdings[self.crypto]['quantity']), self.get_precision(self.crypto_meta_data[self.crypto]['min_order_quantity_increment']))
            
            bought_price[self.crypto] = round( float(rh_holdings[self.crypto]['average_buy_price']), self.get_precision(self.crypto_meta_data[self.crypto]['min_order_price_increment']))
        except:
            holdings[self.crypto] = 0
            bought_price[self.crypto] = 0

        return holdings, bought_price
    
    def get_runtime(self):
        """
        Returns the runtime in seconds
        """
        return t.time() - self.start_time
    
    def retrieve_cash_and_equity(self):
        """
        Returns cash, equity as floats from robin_stocks.robinhood.account.build_user_profile() rounded to two decimal places
        """
        rh_cash = rh.account.build_user_profile()
        
        cash = round(float(rh_cash['cash']), 2)
        equity = round(float(rh_cash['equity']), 2)
        
        return cash, equity
    
    def get_crypto_holdings_capital(self):
        """
        Returns the current dollar value of crypto assets rounded to two decimal places
        """
        capital = 0.00
        
        for crypto_name, crypto_amount in self.holdings.items():
            capital += crypto_amount * float(self.get_latest_quote(crypto_name)['mark_price'])
        
        return round(capital, 2)
    
    def display_time(self, seconds, granularity=5):
        result = []
        
        intervals = (
        ('weeks', 604800),  # 60 * 60 * 24 * 7
        ('days', 86400),    # 60 * 60 * 24
        ('hours', 3600),    # 60 * 60
        ('minutes', 60),
        ('seconds', 1),
        )
    
        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        
        
        return ', '.join(result[:granularity])
    
    def display_holdings(self):
        """
        Returns a string listing the amount of crypto held and the latest price to be printed out
        """
        text = ''

        for crypto, amount in self.holdings.items():
            
            text += '\t' + str(amount) + ' ' + crypto + " at $" + str(round(float(self.get_latest_quote(crypto)['mark_price']), self.get_precision(self.crypto_meta_data[crypto]['min_order_price_increment']))) + '\n'
        
        text = text[:-2]
        
        return text
    
    def display_profit(self):

        if self.profit >= 0:
            text = '+$'
        else:
            text = '-$'

        text += str(abs(round(self.profit, 2)))

        return text
    
    def display_percent_change(self):

        if self.percent_change >= 0:
            text = '+'
        else:
            text = '-'

        text += str(abs(round(self.percent_change, 2)))
        text += '%'

        return text


if __name__ == '__main__':
    config = {
        'crypto': 'BTC',
        'days_to_run': 1,
        'mode': '',
        'backtest': {
            'interval': '',
            'span': '',
            'bounds': '',
        },
        'upper_price': 100,
        'lower_price': 10,
        'level_num': 10,
        'cash': 10000,
        'loss_threshold': 50.00,
        'loss_percentage': 5.00,
        'latency_in_sec': 30
    }

    spot_grid_trader = SpotGridTradingBot(config)
    spot_grid_trader.run()
