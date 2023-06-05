import robin_stocks.robinhood as rh
from order import *
import math
import time
from discord import SyncWebhook

DISCORD_URL = 'https://discord.com/api/webhooks/1114803095394861096/lMqJldCxv4nOEan2QWl9TeIfJErGiUUZ9G_ujTj7pKq57tu9VpsdKawOCtkCzEF-cX8d'

class SpotGridTradingBot():
    def __init__(self, config):
        """
        config = {
            'crypto': 'LTC',
            'days_to_run': 7,
            'mode': 'live_or_test',
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
            'latency_in_sec': 50,
            'is_static': False,
            'send_to_discord': True,
            'discord_latency_in_hours': 1
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
        
        # is_static determines if the sides of the grid lines can change from buy to sell or vice-versa
        self.is_static = bool(config['is_static'])

        self.send_to_discord = bool(config['send_to_discord'])

        if self.send_to_discord:
            self.discord_webhook = SyncWebhook.from_url(DISCORD_URL)
            self.discord_latency_in_hours = float(config['discord_latency_in_hours'])
            self.last_discord_post = None

        self.login()

        self.crypto_meta_data = rh.crypto.get_crypto_info(self.crypto)

        try:
            self.holdings, self.bought_price = self.get_holdings_and_bought_price()
            self.available_cash, self.equity = self.retrieve_cash_and_equity()

            self.initial_cash = self.available_cash
            self.initial_crypto_capital = self.get_crypto_holdings_capital()

            self.profit = 0.00
            self.percent_change = 0.00

            if self.mode == 'live':
                assert self.available_cash >= self.cash
        except Exception as ex:
            self.logout()

            raise ex
    
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
        assert config['mode'] in ['live', 'test']
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
        assert type(config['is_static']) == bool
        assert type(config['send_to_discord']) == bool
        assert type(config['discord_latency_in_hours']) == float or type(config['discord_latency_in_hours']) == int
        assert config['discord_latency_in_hours'] > 0

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
    
    def run(self, is_initialized=False):
        try:
            if not is_initialized:
                if self.is_static:
                    self.init_grid_static()
                else:
                    self.init_grid()
                
                if self.mode == 'live':
                    self.fetch_balances()
                else:
                    self.test_fetch_balances()
                
                self.update_output()

            # Check continue_trading
            while self.continue_trading():
                if self.mode == 'live':
                    if self.is_static:
                        self.update_orders_static()
                    else:
                        self.update_orders()
                else:
                    self.crypto_quote = self.get_latest_quote(self.crypto)
                    if self.is_static:
                        self.test_update_orders_static()
                    else:
                        self.test_update_orders()

                time.sleep(self.latency)

                if self.mode == 'live':
                    self.fetch_balances()
                else:
                    self.test_fetch_balances()
                
                self.update_output()
                
                if self.send_to_discord:
                    self.send_message_to_discord()
            
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
            self.run(True)
        
        except KeyError:
            # Robinhood Internal Error
            # 503 Service Error: Service Unavailable for url: https://api.robinhood.com/portfolios/
            # 500 Server Error: Internal Server Error for url: https://api.robinhood.com/portfolios/
            print("Robinhood Internal Error: KeyError: continuing trading")
            
            # Continue trading
            self.run(True)
        
        except Exception as ex:
            print("An unexpected error occured: cancelling open orders and logging out")
            
            cancel_all_orders()
            self.logout()
            
            raise ex
    
    def fetch_balances(self):
        """
        Updates available_cash, equity, holdings, bought_price, profit, and percent_change
        """
        self.available_cash, self.equity = self.retrieve_cash_and_equity()

        self.holdings, self.bought_price = self.get_holdings_and_bought_price()

        self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital

        try:
            self.percent_change = self.profit * 100 / (self.initial_cash + self.initial_crypto_capital)
        except ZeroDivisionError:
            self.percent_change = None
    
    def test_fetch_balances(self):
        """
        Updates equity, profit, and percent_change
        """
        _, self.equity = self.retrieve_cash_and_equity()
        
        self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital

        try:
            self.percent_change = self.profit * 100 / (self.initial_cash + self.initial_crypto_capital)
        except ZeroDivisionError:
            self.percent_change = None
        
    
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
                if self.percent_change is not None:
                    if self.percent_change >= -1 * self.loss_percentage:
                        return True
                    else:
                        print("Loss percentage exceeded " + str(self.loss_percentage) + "%: terminating automated trading")
                        
                        return False
                else:
                    return True
            else:
                print("Loss exceeded $" + str(self.loss_threshold) + ": terminating automated trading")
                
                return False
    
    def update_output(self):
        """
        Prints out the lastest information out to console
        """
        
        print("===========" + time.ctime() + "===========")
        
        print("mode: " + self.mode)
        print("is_static: " + str(self.is_static))
        print("runtime: " + self.display_time(self.get_runtime()))
        
        print("equity: $" + str(round(self.equity, 2)))
        
        print('crypto holdings:')
        print(self.display_holdings())

        print('crypto average bought price:')
        print(self.display_bought_price())
        
        print("crypto equity: $" + str(round(self.get_crypto_holdings_capital(), 2)))
        print("cash: " + self.display_cash())
        print("crypto equity and cash: " + self.display_crypto_equity_and_cash())
        
        print("profit: " + self.display_profit() + " (" + self.display_percent_change() + ")")

        print(self.crypto + " ask price: $" + str(self.round_to_min_order_price_increment(self.crypto_quote['ask_price'])))
        print(self.crypto + " market price: $" + str(self.round_to_min_order_price_increment(self.crypto_quote['mark_price'])))
        print(self.crypto + " bid price: $" + str(self.round_to_min_order_price_increment(self.crypto_quote['bid_price'])))

        spread = (self.crypto_quote['ask_price'] - self.crypto_quote['bid_price']) * 100 / self.crypto_quote['mark_price']
        print(self.crypto + " spread: " + str(round(spread, 2)) + "%")

        print("number of pending orders:", len(get_all_open_orders()))
        print("grids:")
        self.print_grids()
        print('\n')
    
    def round_down_to_cents(self, value):
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
    
    def round_to_min_order_price_increment(self, value):
        return round(value, self.get_precision(self.crypto_meta_data['min_order_price_increment']))
    
    def round_to_min_order_quantity_increment(self, value):
        return round(value, self.get_precision(self.crypto_meta_data['min_order_quantity_increment']))
    
    def get_latest_quote(self, crypto_symbol):
        """
        Returns a dictionary of the latest quote of the cryptocurrency.
        Dictionary Keys:
            ask_price
            ask_source
            bid_price
            bid_source
            mark_price
            high_price
            low_price
            open_price
            symbol
            id
            volume
            updated_at
        
        sample_api_response = {'ask_price': '27213.3353724',
                'ask_source': 'df727485bffb859b5a26383d2e315dc34497f50158f2391a2c4cc03e2e7b27fe',
                'bid_price': '27016.00727763',
                'bid_source': '9873d2c153944f73b1724c7dea2589207b0b46a177081fb8b0a7893bd480b74f',
                'mark_price': '27114.671325015',
                'high_price': '27343.1989937',
                'low_price': '27028.0141418',
                'open_price': '27151.5435720200005',
                'symbol': 'BTCUSD',
                'id': '3d961844-d360-45fc-989b-f6fca761d511',
                'volume': '0',
                'updated_at': '2023-06-03T20:30:31.058Z'
        }
        """
        data = rh.crypto.get_crypto_quote(crypto_symbol)
        data['ask_price'] = float(data['ask_price'])
        data['bid_price'] = float(data['bid_price'])
        data['mark_price'] = float(data['mark_price'])
        data['high_price'] = float(data['high_price'])
        data['low_price'] = float(data['low_price'])
        data['open_price'] = float(data['open_price'])
        return data
    
    def init_grid(self):
        # Start the clock
        self.start_time = time.time()

        # Initialize grids
        """
        self.grids = {
            'order_i': {
                'price': 35.32,
                'side': 'buy_or_sell',
                'status': 'active_or_inactive',
                'order': Order
            }
        }
        """
        self.grids = {}

        self.cash_per_level = self.round_down_to_cents(self.cash / self.level_num)

        # Determine what the prices are at each level
        for i in range(self.level_num):
            self.grids['order_' + str(i)] = {'price': self.round_to_min_order_price_increment(self.lower_price + i*(self.upper_price - self.lower_price)/(self.level_num-1))}

        # Get crypto quote
        self.crypto_quote = self.get_latest_quote(self.crypto)

        """
        Notes:
        - ask_price > bid_price due to spread (0.3-0.4%)
        - Everything below ask_price is buy
        - Everything above bid_price is sell
        - But if spread is very large and they overlap, ignore the overlapping level(s)
        """

        # Mark orders as buys and sells
        for i in range(len(self.grids)):
            if self.crypto_quote['ask_price'] > self.grids['order_' + str(i)]['price']:
                self.grids['order_' + str(i)]['side'] = 'buy'
            else:
                self.grids['order_' + str(i)]['side'] = 'sell'

        # Determine which grid line is closest to the current price
        min_dist = float('inf')
        self.closest_grid = -1

        for i in range(len(self.grids)):
            dist = abs(self.grids['order_' + str(i)]['price'] - self.crypto_quote['ask_price'])

            if dist < min_dist:
                min_dist = dist
                self.closest_grid = i
        
        # Mark the closest grid line as inactive
        self.grids['order_' + str(self.closest_grid)]['status'] = 'inactive'

        # Mark all the other grid lines as active
        for i in range(len(self.grids)):
            if i != self.closest_grid:
                self.grids['order_' + str(i)]['status'] = 'active'
        
        self.print_grids()

        # Determine amount of dollars to buy initial amount of cryptocurrency
        initial_buy_amount = (len(self.grids) - 1 - self.closest_grid) * self.cash_per_level

        # Place market order for cryptocurrency
        if self.mode == 'live':
            rh.orders.order_buy_crypto_by_price(self.crypto, initial_buy_amount, timeInForce='gtc', jsonify=True)
        else:
            print("Placing a market order for $" + str(initial_buy_amount) + " at an ask price of $" + str(self.crypto_quote['ask_price']))

            # Update available_cash, holdings, bought_price, profit, and percent_change to simulate the fulfillment of the limit buy order
            self.available_cash -= initial_buy_amount
            self.holdings[self.crypto] += self.round_to_min_order_quantity_increment(initial_buy_amount/self.crypto_quote['ask_price'])
            self.bought_price[self.crypto] = self.round_to_min_order_price_increment( ((self.bought_price[self.crypto] * self.holdings[self.crypto]) + (initial_buy_amount)) / (self.holdings[self.crypto] + self.round_to_min_order_quantity_increment(initial_buy_amount/self.crypto_quote['ask_price'])))
            self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital
            try:
                self.percent_change = self.profit * 100 / (self.initial_cash + self.initial_crypto_capital)
            except ZeroDivisionError:
                self.percent_change = None
        
        # Place buy orders and possibly sell orders
        for i in range(len(self.grids)):
            if self.grids['order_' + str(i)]['side'] == 'buy' and self.grids['order_' + str(i)]['status'] == 'active':
                if self.mode == 'live':
                    #self.grids['order_' + str(i)]['order'] = Order(rh.orders.order_buy_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids['order_' + str(i)]['price'], timeInForce='gtc', jsonify=True))
                    self.grids['order_' + str(i)]['order'] = Order(rh.orders.order_buy_crypto_limit(self.crypto, self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i)]['price']), self.grids['order_' + str(i)]['price'], timeInForce='gtc', jsonify=True))
                else:
                    print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids['order_' + str(i)]['price']))
                    self.grids['order_' + str(i)]['order'] = None
            elif self.grids['order_' + str(i)]['side'] == 'sell' and self.grids['order_' + str(i)]['status'] == 'active':
                if self.mode == 'live':
                    #self.grids['order_' + str(i)]['order'] = Order(rh.orders.order_sell_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids['order_' + str(i)]['price'], timeInForce='gtc', jsonify=True))
                    self.grids['order_' + str(i)]['order'] = Order(rh.orders.order_sell_crypto_limit(self.crypto, self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i)]['price']), self.grids['order_' + str(i)]['price'], timeInForce='gtc', jsonify=True))
                else:
                    print("Placing a limit sell order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids['order_' + str(i)]['price']))
                    self.grids['order_' + str(i)]['order'] = None
            else:
                self.grids['order_' + str(i)]['order'] = None
        
        print("finished grid initalization")
    
    def init_grid_static(self):
        # Start the clock
        self.start_time = time.time()

        # Initialize grids
        """
        self.grids = {
            'order_i': {
                'price': 35.32,
                'side': 'buy_or_sell',
                'status': 'active_or_inactive',
                'order': Order
            }
        }
        """
        self.grids = {}

        self.cash_per_level = self.round_down_to_cents(self.cash / self.level_num)

        # Determine what the prices are at each level
        for i in range(self.level_num):
            self.grids['order_' + str(i)] = {'price': self.round_to_min_order_price_increment(self.lower_price + i*(self.upper_price - self.lower_price)/(self.level_num-1))}

        # Get crypto quote
        self.crypto_quote = self.get_latest_quote(self.crypto)

        """
        Notes:
        - ask_price > bid_price due to spread (0.3-0.4%)
        - Everything below ask_price is buy
        - Everything above bid_price is sell
        - But if spread is very large and they overlap, ignore the overlapping level(s)
        """

        # Mark orders as buys and sells
        for i in range(len(self.grids)):
            if self.crypto_quote['ask_price'] > self.grids['order_' + str(i)]['price']:
                self.grids['order_' + str(i)]['side'] = 'buy'
            else:
                self.grids['order_' + str(i)]['side'] = 'sell'

        # Mark all buy grid lines as active and all sell grid lines as inactive
        for i in range(len(self.grids)):
            if self.grids['order_' + str(i)]['side'] == 'buy':
                self.grids['order_' + str(i)]['status'] = 'active'
            elif self.grids['order_' + str(i)]['side'] == 'sell':
                self.grids['order_' + str(i)]['status'] = 'inactive'
        
        self.print_grids()
        
        # Place buy orders
        for i in range(len(self.grids)):
            if self.grids['order_' + str(i)]['side'] == 'buy' and self.grids['order_' + str(i)]['status'] == 'active':
                if self.mode == 'live':
                    #self.grids['order_' + str(i)]['order'] = Order(rh.orders.order_buy_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids['order_' + str(i)]['price'], timeInForce='gtc', jsonify=True))
                    self.grids['order_' + str(i)]['order'] = Order(rh.orders.order_buy_crypto_limit(self.crypto, self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i)]['price']), self.grids['order_' + str(i)]['price'], timeInForce='gtc', jsonify=True))
                else:
                    print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids['order_' + str(i)]['price']))
                    self.grids['order_' + str(i)]['order'] = None
            else:
                self.grids['order_' + str(i)]['order'] = None
        
        print("finished grid initalization")
    
    def update_orders(self):
        for i in range(len(self.grids)):
            # Update each order
            if self.grids['order_' + str(i)]['status'] == 'active' and self.grids['order_' + str(i)]['order'] is not None:
                self.grids['order_' + str(i)]['order'].update()

                if self.grids['order_' + str(i)]['order'] is not None and self.grids['order_' + str(i)]['order'].is_filled():
                    if self.grids['order_' + str(i)]['side'] == 'buy' and self.closest_grid == i+1:
                        # If the filled order was a buy order, place a sell order on the level above it, assuming it was previously inactive

                        # Set the filled level to inactive and adjust the inactive index
                        self.grids['order_' + str(i)]['status'] = 'inactive'
                        self.closest_grid = i

                        # Place a sell order on grid line i+1
                        self.grids['order_' + str(i+1)]['side'] = 'sell'
                        self.grids['order_' + str(i+1)]['status'] = 'active'

                        #self.grids['order_' + str(i+1)]['order'] = Order(rh.orders.order_sell_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids['order_' + str(i+1)]['price'], timeInForce='gtc', jsonify=True))
                        self.grids['order_' + str(i+1)]['order'] = Order(rh.orders.order_sell_crypto_limit(self.crypto, self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i+1)]['price']), self.grids['order_' + str(i+1)]['price'], timeInForce='gtc', jsonify=True))
                        print("Placing a limit sell order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids['order_' + str(i+1)]['price']))
                    elif self.grids['order_' + str(i)]['side'] == 'sell' and self.closest_grid == i-1:
                        # If the filled order was a sell order, place a buy order on the level below it, assuming it was previously inactive

                        # Set the filled level to inactive and adjust the inactive index
                        self.grids['order_' + str(i)]['status'] = 'inactive'
                        self.closest_grid = i

                        # Place a buy order on grid line i
                        self.grids['order_' + str(i-1)]['side'] = 'buy'
                        self.grids['order_' + str(i-1)]['status'] = 'active'

                        #self.grids['order_' + str(i-1)]['order'] = Order(rh.orders.order_buy_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids['order_' + str(i-1)]['price'], timeInForce='gtc', jsonify=True))
                        self.grids['order_' + str(i-1)]['order'] = Order(rh.orders.order_buy_crypto_limit(self.crypto, self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i-1)]['price']), self.grids['order_' + str(i-1)]['price'], timeInForce='gtc', jsonify=True))
                        print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids['order_' + str(i-1)]['price']))
                    else:
                        raise Exception("Order was filled but either was not sell nor buy or ignored level was not correct or both")
    
    def update_orders_static(self):
        for i in range(len(self.grids)):
            # Update each active order
            if self.grids['order_' + str(i)]['status'] == 'active' and self.grids['order_' + str(i)]['order'] is not None:
                self.grids['order_' + str(i)]['order'].update()

                if self.grids['order_' + str(i)]['order'].is_filled():
                    self.grids['order_' + str(i)]['status'] = 'inactive'

                    if self.grids['order_' + str(i)]['side'] == 'buy':
                        # If the filled order was a buy order, place a sell order on the closest sell grid line above it

                        # Place a sell order on the closest sell grid line above it
                        sell_index = -1
                        for j in range(i, len(self.grids)):
                            if self.grids['order_' + str(j)]['side'] == 'sell' and self.grids['order_' + str(j)]['status'] == 'inactive':
                                sell_index = j
                                break
                        
                        self.grids['order_' + str(sell_index)]['status'] = 'active'

                        #self.grids['order_' + str(sell_index)]['order'] = Order(rh.orders.order_sell_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids['order_' + str(sell_index)]['price'], timeInForce='gtc', jsonify=True))
                        self.grids['order_' + str(sell_index)]['order'] = Order(rh.orders.order_sell_crypto_limit(self.crypto, self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(sell_index)]['price']), self.grids['order_' + str(sell_index)]['price'], timeInForce='gtc', jsonify=True))
                        print("Placing a limit sell order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids['order_' + str(sell_index)]['price']))
                    elif self.grids['order_' + str(i)]['side'] == 'sell':
                        # If the filled order was a sell order, place a buy order on the level below it, assuming it was previously inactive

                        # Place a buy order on the closest buy grid line below it
                        buy_index = -1
                        for j in range(len(self.grids)-1, -1, -1):
                            if self.grids['order_' + str(j)]['side'] == 'buy' and self.grids['order_' + str(j)]['status'] == 'inactive':
                                buy_index = j
                                break
                        
                        self.grids['order_' + str(buy_index)]['status'] = 'active'

                        #self.grids['order_' + str(buy_index)]['order'] = Order(rh.orders.order_buy_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids['order_' + str(buy_index)]['price'], timeInForce='gtc', jsonify=True))
                        self.grids['order_' + str(buy_index)]['order'] = Order(rh.orders.order_buy_crypto_limit(self.crypto, self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(buy_index)]['price']), self.grids['order_' + str(buy_index)]['price'], timeInForce='gtc', jsonify=True))
                        print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids['order_' + str(buy_index)]['price']))
                    else:
                        raise Exception("Order was filled but either was not sell nor buy or ignored level was not correct or both")
    
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
            holdings[self.crypto] = float(rh_holdings[self.crypto]['quantity'])
            
            bought_price[self.crypto] = float(rh_holdings[self.crypto]['average_buy_price'])
        except:
            holdings[self.crypto] = 0
            bought_price[self.crypto] = 0

        return holdings, bought_price
    
    def get_runtime(self):
        """
        Returns the runtime in seconds
        """
        return time.time() - self.start_time
    
    def retrieve_cash_and_equity(self):
        """
        Returns cash, equity as floats from robin_stocks.robinhood.account.build_user_profile()
        """
        rh_cash = rh.account.build_user_profile()
        
        cash = self.round_down_to_cents(float(rh_cash['cash']))
        equity = self.round_down_to_cents(float(rh_cash['equity']))
        
        return cash, equity
    
    def get_crypto_holdings_capital(self):
        """
        Returns the current dollar value of crypto assets using the market price
        """
        capital = 0.00
        
        for crypto_name, crypto_amount in self.holdings.items():
            capital += crypto_amount * float(self.get_latest_quote(crypto_name)['mark_price'])
        
        return self.round_down_to_cents(capital)
    
    def get_precision(self, text):
        """
        Returns the number of decimal places the number has
        
        text needs to contain one and only one '1' and one and only one '.'
        
        E.g. text: output
        '100.000000000000': -2
        '10.0000000000000': -1
        '1.00000000000000': 0
        '0.10000000000000': 1
        '0.01000000000000': 2
        '0.00100000000000': 3
        '0.00010000000000': 4
        """
        one = text.find('1')
        dot = text.find('.')
        
        if one < dot:
            return one - dot + 1
        else:
            return one - dot
    
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
    
    def display_cash(self):
        """
        Returns a string containing the available cash amount
        """
        if self.available_cash < 0:
            text = '-$'
        else:
            text = '$'
        
        text += str(abs(round(self.available_cash, 2)))

        return text
    
    def display_crypto_equity_and_cash(self):
        value = round(self.available_cash + self.get_crypto_holdings_capital(), 2)
        
        if value < 0:
            text = '-$'
        else:
            text = '$'
        
        text += str(abs(value))

        return text
    
    def display_holdings(self):
        """
        Returns a string listing the amount of crypto held and the latest price to be printed out
        """
        text = ''

        for crypto, amount in self.holdings.items():
            
            text += '\t' + str(amount) + ' ' + crypto + " at $" + str(float(self.get_latest_quote(crypto)['mark_price']))
        
        return text
    
    def display_bought_price(self):
        """
        Returns a string listing the name of the crypto and its associated average bought price
        """
        text = ''

        for crypto, bought_price in self.bought_price.items():
            text += '\t' + str(bought_price) + ' ' + crypto + ' average bought price: $' + str(self.bought_price[crypto])

        return text
    
    def display_profit(self):

        if self.profit >= 0:
            text = '+$'
        else:
            text = '-$'

        text += str(abs(self.round_down_to_cents(self.profit)))

        return text
    
    def display_percent_change(self):
        if self.percent_change is not None:
            if self.percent_change >= 0:
                text = '+'
            else:
                text = '-'

            text += str(abs(round(self.percent_change, 2)))
            text += '%'

            return text
        else:
            return 'None'
    
    def print_grids(self):
        for i in range(len(self.grids)-1, -1, -1):
            if i == len(self.grids)-1:
                print("=============================================")
                print('grid_' + str(i))
                print('\tprice: $' + str(self.grids['order_' + str(i)]['price']))
                print('\tside:', self.grids['order_' + str(i)]['side'])
                print('\tstatus:', self.grids['order_' + str(i)]['status'])
                try:
                    print('\torder:', self.grids['order_' + str(i)]['order'])
                except KeyError:
                    print('\torder:', None)
                print('\tcash: $' + str(self.cash_per_level))
                print("=============================================")
            else:
                print('grid_' + str(i))
                print('\tprice: $' + str(self.grids['order_' + str(i)]['price']))
                print('\tside:', self.grids['order_' + str(i)]['side'])
                print('\tstatus:', self.grids['order_' + str(i)]['status'])
                try:
                    print('\torder:', self.grids['order_' + str(i)]['order'])
                except KeyError:
                    print('\torder:', None)
                print('\tcash: $' + str(self.cash_per_level))
                print("=============================================")
        print("=============================================")
    
    def test_update_orders(self):
        # Update each order
        for i in range(len(self.grids)):
            # Ensure that there is an order and that it is active
            if self.grids['order_' + str(i)]['order'] is not None and self.grids['order_' + str(i)]['status'] == 'active':
                # Check to see if either as a buy or sell order that it has been filled
                if (self.grids['order_' + str(i)]['side'] == 'buy' and self.crypto_quote['ask_price'] <= self.grids['order_' + str(i)]['price']) or (self.grids['order_' + str(i)]['side'] == 'sell' and self.crypto_quote['bid_price'] >= self.grids['order_' + str(i)]['price']):
                    if self.grids['order_' + str(i)]['side'] == 'buy' and self.closest_grid == i+1:
                        # If the filled order was a buy order, place a sell order on the level above it, assuming it was previously inactive

                        # Update available_cash, holdings, bought_price, profit, and percent_change to simulate the fulfillment of the limit buy order
                        self.available_cash -= self.cash_per_level
                        self.holdings[self.crypto] += self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i)]['price'])
                        self.bought_price[self.crypto] = self.round_to_min_order_price_increment( ((self.bought_price[self.crypto] * self.holdings[self.crypto]) + (self.cash_per_level)) / (self.holdings[self.crypto] + self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i)]['price'])))
                        self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital
                        try:
                            self.percent_change = self.profit * 100 / (self.initial_cash + self.initial_crypto_capital)
                        except ZeroDivisionError:
                            self.percent_change = None

                        # Set the filled level to inactive and adjust the inactive index
                        self.grids['order_' + str(i)]['status'] = 'inactive'
                        self.closest_grid = i

                        # Place a sell order on grid line i+1
                        self.grids['order_' + str(i+1)]['side'] = 'sell'
                        self.grids['order_' + str(i+1)]['status'] = 'active'
                        
                        if self.mode == 'live':
                            #self.grids['order_' + str(i+1)]['order'] = Order(rh.orders.order_sell_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids['order_' + str(i+1)]['price'], timeInForce='gtc', jsonify=True))
                            self.grids['order_' + str(i+1)]['order'] = Order(rh.orders.order_sell_crypto_limit(self.crypto, self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i+1)]['price']), self.grids['order_' + str(i+1)]['price'], timeInForce='gtc', jsonify=True))
                        else:
                            print("Placing a limit sell order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids['order_' + str(i+1)]['price']))
                            self.grids['order_' + str(i+1)]['order'] = None
                    elif self.grids['order_' + str(i)]['side'] == 'sell' and self.closest_grid == i-1:
                        # If the filled order was a sell order, place a buy order on the level below it, assuming it was previously inactive

                        # Update available_cash, holdings, profit, and percent_change to simulate the fulfillment of the limit sell order
                        self.available_cash += self.cash_per_level
                        self.holdings[self.crypto] -= self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i)]['price'])
                        self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital
                        try:
                            self.percent_change = self.profit * 100 / (self.initial_cash + self.initial_crypto_capital)
                        except ZeroDivisionError:
                            self.percent_change = None

                        # Set the filled level to inactive and adjust the inactive index
                        self.grids['order_' + str(i)]['status'] = 'inactive'
                        self.closest_grid = i

                        # Place a buy order on grid line i
                        self.grids['order_' + str(i-1)]['side'] = 'buy'
                        self.grids['order_' + str(i-1)]['status'] = 'active'

                        if self.mode == 'live':
                            #self.grids['order_' + str(i-1)]['order'] = Order(rh.orders.order_buy_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids['order_' + str(i-1)]['price'], timeInForce='gtc', jsonify=True))
                            self.grids['order_' + str(i-1)]['order'] = Order(rh.orders.order_buy_crypto_limit(self.crypto, self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i-1)]['price']), self.grids['order_' + str(i-1)]['price'], timeInForce='gtc', jsonify=True))
                        else:
                            print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids['order_' + str(i-1)]['price']))
                            self.grids['order_' + str(i-1)]['order'] = None
                    else:
                        raise Exception("Order was filled but either was not sell nor buy or ignored level was not correct or both")
    
    def test_update_orders_static(self):
        # Update each order
        for i in range(len(self.grids)):
            # Ensure that there is an order and that it is active
            if self.grids['order_' + str(i)]['order'] is not None and self.grids['order_' + str(i)]['status'] == 'active':
                # Check to see if either as a buy or sell order that it has been filled
                if (self.grids['order_' + str(i)]['side'] == 'buy' and self.crypto_quote['ask_price'] <= self.grids['order_' + str(i)]['price']) or (self.grids['order_' + str(i)]['side'] == 'sell' and self.crypto_quote['bid_price'] >= self.grids['order_' + str(i)]['price']):
                    self.grids['order_' + str(i)]['status'] = 'inactive'

                    if self.grids['order_' + str(i)]['side'] == 'buy':
                        # If the filled order was a buy order, place a sell order on the closest sell grid line above it

                        # Update available_cash, holdings, bought_price, profit, and percent_change to simulate the fulfillment of the limit buy order
                        self.available_cash -= self.cash_per_level
                        self.holdings[self.crypto] += self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i)]['price'])
                        self.bought_price[self.crypto] = self.round_to_min_order_price_increment( ((self.bought_price[self.crypto] * self.holdings[self.crypto]) + (self.cash_per_level)) / (self.holdings[self.crypto] + self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i)]['price'])))
                        self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital
                        try:
                            self.percent_change = self.profit * 100 / (self.initial_cash + self.initial_crypto_capital)
                        except ZeroDivisionError:
                            self.percent_change = None

                        # Place a sell order on the closest sell grid line above it
                        sell_index = -1
                        for j in range(i, len(self.grids)):
                            if self.grids['order_' + str(j)]['side'] == 'sell' and self.grids['order_' + str(j)]['status'] == 'inactive':
                                sell_index = j
                                break
                        
                        self.grids['order_' + str(sell_index)]['status'] = 'active'
                        
                        if self.mode == 'live':
                            #self.grids['order_' + str(sell_index)]['order'] = Order(rh.orders.order_sell_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids['order_' + str(sell_index)]['price'], timeInForce='gtc', jsonify=True))
                            self.grids['order_' + str(sell_index)]['order'] = Order(rh.orders.order_sell_crypto_limit(self.crypto, self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(sell_index)]['price']), self.grids['order_' + str(sell_index)]['price'], timeInForce='gtc', jsonify=True))
                        else:
                            print("Placing a limit sell order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids['order_' + str(sell_index)]['price']))
                            self.grids['order_' + str(sell_index)]['order'] = None
                    elif self.grids['order_' + str(i)]['side'] == 'sell':
                        # If the filled order was a sell order, place a buy order on the level below it, assuming it was previously inactive

                        # Update available_cash, holdings, profit, and percent_change to simulate the fulfillment of the limit sell order
                        self.available_cash += self.cash_per_level
                        self.holdings[self.crypto] -= self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i)]['price'])
                        self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital
                        try:
                            self.percent_change = self.profit * 100 / (self.initial_cash + self.initial_crypto_capital)
                        except ZeroDivisionError:
                            self.percent_change = None

                        # Place a buy order on the closest buy grid line below it
                        buy_index = -1
                        for j in range(len(self.grids)-1, -1, -1):
                            if self.grids['order_' + str(j)]['side'] == 'buy' and self.grids['order_' + str(j)]['status'] == 'inactive':
                                buy_index = j
                                break
                        
                        self.grids['order_' + str(buy_index)]['status'] = 'active'

                        if self.mode == 'live':
                            #self.grids['order_' + str(buy_index)]['order'] = Order(rh.orders.order_buy_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids['order_' + str(buy_index)]['price'], timeInForce='gtc', jsonify=True))
                            self.grids['order_' + str(buy_index)]['order'] = Order(rh.orders.order_buy_crypto_limit(self.crypto, self.round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(buy_index)]['price']), self.grids['order_' + str(buy_index)]['price'], timeInForce='gtc', jsonify=True))
                        else:
                            print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids['order_' + str(buy_index)]['price']))
                            self.grids['order_' + str(buy_index)]['order'] = None
                    else:
                        raise Exception("Order was filled but either was not sell nor buy or ignored level was not correct or both")
    
    def send_message_to_discord(self):
        """
        Send out the lastest information out to the discord channel
        """
        if self.last_discord_post is None or time.time() - self.last_discord_post >= self.discord_latency_in_hours * 3600:
            message = ""
            message += "===========" + time.ctime() + "===========\n"
            message += "=============================================\n"
            message += "mode: " + self.mode + "\n"
            message += "is_static: " + str(self.is_static) + "\n"
            message += "runtime: " + self.display_time(self.get_runtime()) + "\n"
            message += "equity: $" + str(round(self.equity, 2)) + "\n"
            message += 'crypto holdings:\n'
            message += self.display_holdings() + '\n'
            message += 'crypto average bought price:\n'
            message += self.display_bought_price() + '\n'
            message += "crypto equity: $" + str(round(self.get_crypto_holdings_capital(), 2)) + '\n'
            message += "cash: " + self.display_cash() + '\n'
            message += "crypto equity and cash: " + self.display_crypto_equity_and_cash() + '\n'
            message += "profit: " + self.display_profit() + " (" + self.display_percent_change() + ")\n"

            message += self.crypto + " ask price: $" + str(self.round_to_min_order_price_increment(self.crypto_quote['ask_price'])) + '\n'
            message += self.crypto + " market price: $" + str(self.round_to_min_order_price_increment(self.crypto_quote['mark_price'])) + '\n'
            message += self.crypto + " bid price: $" + str(self.round_to_min_order_price_increment(self.crypto_quote['bid_price'])) + '\n'

            spread = (self.crypto_quote['ask_price'] - self.crypto_quote['bid_price']) * 100 / self.crypto_quote['mark_price']
            message += self.crypto + " spread: " + str(round(spread, 2)) + "%\n"

            message += "number of pending orders: " + str(len(get_all_open_orders())) + '\n'
            message += "grids:\n"

            for i in range(len(self.grids)-1, -1, -1):
                if i == len(self.grids)-1:
                    message += "=============================================\n"
                    message += 'grid_' + str(i) + '\n'
                    message += '\tprice: $' + str(self.grids['order_' + str(i)]['price']) + '\n'
                    message += '\tside: ' + self.grids['order_' + str(i)]['side'] + '\n'
                    message += '\tstatus: ' + self.grids['order_' + str(i)]['status'] + '\n'
                    try:
                        message += '\torder: ' + str(self.grids['order_' + str(i)]['order']) + '\n'
                    except KeyError:
                        message += '\torder: None\n'
                    message += '\tcash: $' + str(self.cash_per_level) + '\n'
                    message += "=============================================\n"
                else:
                    message += 'grid_' + str(i) + '\n'
                    message += '\tprice: $' + str(self.grids['order_' + str(i)]['price']) + '\n'
                    message += '\tside: ' + self.grids['order_' + str(i)]['side'] + '\n'
                    message += '\tstatus: ' + self.grids['order_' + str(i)]['status'] + '\n'
                    try:
                        message += '\torder: ' + str(self.grids['order_' + str(i)]['order']) + '\n'
                    except KeyError:
                        message += '\torder: None\n'
                    message += '\tcash: $' + str(self.cash_per_level) + '\n'
                    message += "=============================================\n"
            message += "=============================================\n"

            message += '\n'
            self.discord_webhook.send(message)
            self.last_discord_post = time.time()
            return
