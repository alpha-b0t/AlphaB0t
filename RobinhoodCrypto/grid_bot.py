import robin_stocks.robinhood as rh
from RobinhoodCrypto.order import *
from RobinhoodCrypto.error_queue import ErrorQueue, ErrorQueueLimitExceededError
import time
from discord import SyncWebhook
from RobinhoodCrypto.helpers import *
from config import GridBotConfig

class GridBot():
    def __init__(self, config: GridBotConfig):
        self.check_config(config)

        self.crypto = config.crypto
        self.days_to_run = config.days_to_run
        self.mode = config.mode

        self.backtest_interval = config.backtest_interval
        self.backtest_span = config.backtest_span
        self.backtest_bounds = config.backtest_bounds

        self.upper_price = config.upper_price
        self.lower_price = config.lower_price
        self.level_num = config.level_num
        self.cash = config.cash
        self.loss_threshold = config.loss_threshold
        self.loss_percentage = config.loss_percentage
        self.latency = config.latency_in_sec

        self.send_to_discord = config.send_to_discord

        if self.send_to_discord:
            self.discord_webhook = SyncWebhook.from_url(config.discord_url)
            self.discord_latency_in_hours = config.discord_latency_in_hours
            self.last_discord_post = None
        
        self.error_latency = config.error_latency_in_sec
        self.max_error_count = config.max_error_count
        
        self.error_queue = ErrorQueue(self.error_latency, self.max_error_count)
        
        self.init_buy_error_latency = config.init_buy_error_latency_in_sec
        self.init_buy_error_max_count = config.init_buy_error_max_count
        self.cancel_orders_upon_exit = config.cancel_orders_upon_exit

        self.login()

        self.crypto_meta_data = rh.crypto.get_crypto_info(self.crypto)

        try:
            self.holdings, self.bought_price = self.get_holdings_and_bought_price()
            self.available_cash, self.equity = self.get_cash_and_equity()

            self.initial_cash = self.available_cash
            self.initial_crypto_capital = self.get_crypto_holdings_capital()

            self.profit = 0.00
            self.percent_change = 0.00

            if self.mode == 'live':
                assert self.available_cash >= self.cash
        except Exception as e:
            self.logout()

            raise e
    
    def check_config(self, config: GridBotConfig):
        """
        Time: O(1)
        Space: O(1)
        Assures that the configuration is as expected. Raises an exception if an error is found.
        """
        assert isinstance(config.crypto, str)
        assert len(config.crypto) > 0
        assert isinstance(config.days_to_run, int)
        assert config.days_to_run >= 1
        assert isinstance(config.mode, str)
        assert config.mode in ['live', 'test']

        assert type(config.backtest_interval) == str
        assert config.backtest_interval in ['15second', '5minute', '10minute', 'hour', 'day', 'week']
        assert type(config.backtest_span) == str
        assert config.backtest_span in ['hour', 'day', 'week', 'month', '3month', 'year', '5year']
        assert type(config.backtest_bounds) == str
        assert config.backtest_bounds in ['Regular', 'trading', 'extended', '24_7']

        assert type(config.upper_price) == float or type(config.upper_price) == int
        assert config.upper_price > 0
        assert type(config.lower_price) == float or type(config.lower_price) == int
        assert config.lower_price > 0
        assert isinstance(config.level_num, int)
        assert config.level_num >= 2
        assert type(config.cash) == float or type(config.cash) == int
        assert config.cash > 0
        assert type(config.loss_threshold) == float or type(config.loss_threshold) == int
        assert config.loss_threshold > 0
        assert type(config.loss_percentage) == float or type(config.loss_percentage) == int
        assert config.loss_percentage > 0
        assert type(config.latency_in_sec) == float or type(config.latency_in_sec) == int
        assert config.latency_in_sec > 0
        assert type(config.send_to_discord) == bool
        
        if config.send_to_discord:
            assert type(config.discord_latency_in_hours) == float or type(config.discord_latency_in_hours) == int
            assert config.discord_latency_in_hours > 0
            assert type(config.discord_url) == str
            assert len(config.discord_url) > 0
        
        assert type(config.max_error_count) == int
        assert type(config.error_latency_in_sec) == float or type(config.error_latency_in_sec) == int
        assert config.error_latency_in_sec > 0

        if config.mode == 'live':
            assert type(config.init_buy_error_latency_in_sec) == int or type(config.init_buy_error_latency_in_sec) == float
            assert config.init_buy_error_latency_in_sec > 0
            assert type(config.init_buy_error_max_count) == int
            assert config.init_buy_error_max_count > 0
        
        assert type(config.cancel_orders_upon_exit) == str
        assert config.cancel_orders_upon_exit in ['all', 'buy', 'sell', 'none']
        
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
    
    def start(self, is_initialized=False):
        try:
            if not is_initialized:
                if self.send_to_discord:
                    self.send_start_message_to_discord()
                
                self.init_grid()
                
                if self.mode == 'live':
                    self.get_balances()
                else:
                    self.test_get_balances()
                
                self.error_queue.update()

            # Check continue_trading
            while self.continue_trading():
                # Get latest crypto prices
                self.crypto_quote = self.get_latest_quote(self.crypto)

                # Update the orders accordingly
                if self.mode == 'live':
                    self.update_orders()
                else:
                    self.test_update_orders()
                
                # Get balances
                if self.mode == 'live':
                    self.get_balances()
                else:
                    self.test_get_balances()
                
                # Update the output
                self.update_output()
                
                # Update discord if necessary
                if self.send_to_discord:
                    self.send_message_to_discord()
                
                # Refresh the error queue
                self.error_queue.update()

                # Wait for self.latency seconds
                time.sleep(self.latency)
            
            if self.send_to_discord:
                self.send_end_message_to_discord()
                self.send_loss_exceeded_message_to_discord()

            # Cancel all open crypto orders
            if self.cancel_orders_upon_exit == 'all':
                cancel_all_orders()
            elif self.cancel_orders_upon_exit == 'buy' or self.cancel_orders_upon_exit == 'sell':
                cancel_all_side_orders(self.cancel_orders_upon_exit)

            # Log out
            self.logout()
        
        except KeyboardInterrupt as e:
            print("User ended execution of program.")

            if self.send_to_discord:
                self.send_end_message_to_discord()
                self.send_error_message_to_discord(e, 'KeyboardInterrupt')
                self.discord_webhook
            
            if self.cancel_orders_upon_exit == 'all':
                cancel_all_orders()
            elif self.cancel_orders_upon_exit == 'buy' or self.cancel_orders_upon_exit == 'sell':
                cancel_all_side_orders(self.cancel_orders_upon_exit)
            
            self.logout()
        
        except TypeError as e:
            # Robinhood Internal Error
            # 503 Server Error: Service Unavailable for url: https://api.robinhood.com/marketdata/forex/quotes/76637d50-c702-4ed1-bcb5-5b0732a81f48/
            print("Robinhood Internal Error: TypeError: continuing trading")
            
            try:
                self.error_queue.update()
                self.error_queue.append(time.time())
            except ErrorQueueLimitExceededError as e:
                if self.send_to_discord:
                    self.send_end_message_to_discord()
                    self.send_error_message_to_discord(e, 'Too many TypeErrors occured')
                
                if self.cancel_orders_upon_exit == 'all':
                    cancel_all_orders()
                elif self.cancel_orders_upon_exit == 'buy' or self.cancel_orders_upon_exit == 'sell':
                    cancel_all_side_orders(self.cancel_orders_upon_exit)
                
                self.logout()
                
                raise e

            if self.send_to_discord:
                self.send_error_message_to_discord(e, 'TypeError')
            
            # Continue trading
            self.resume()
        
        except KeyError as e:
            # Robinhood Internal Error
            # 503 Service Error: Service Unavailable for url: https://api.robinhood.com/portfolios/
            # 500 Server Error: Internal Server Error for url: https://api.robinhood.com/portfolios/
            print("Robinhood Internal Error: KeyError: continuing trading")
            
            try:
                self.error_queue.update()
                self.error_queue.append(time.time())
            except ErrorQueueLimitExceededError as e:
                if self.send_to_discord:
                    self.send_end_message_to_discord()
                    self.send_error_message_to_discord(e, 'Too many KeyErrors occured')
                
                if self.cancel_orders_upon_exit == 'all':
                    cancel_all_orders()
                elif self.cancel_orders_upon_exit == 'buy' or self.cancel_orders_upon_exit == 'sell':
                    cancel_all_side_orders(self.cancel_orders_upon_exit)
                
                self.logout()
                
                raise e

            if self.send_to_discord:
                self.send_error_message_to_discord(e, 'KeyError')
            
            # Continue trading
            self.resume()
        
        except Exception as e:
            print("An unexpected error occured: cancelling open orders and logging out")

            if self.send_to_discord:
                self.send_end_message_to_discord()
                self.send_error_message_to_discord(e, 'Unknown')
            
            if self.cancel_orders_upon_exit == 'all':
                cancel_all_orders()
            elif self.cancel_orders_upon_exit == 'buy' or self.cancel_orders_upon_exit == 'sell':
                cancel_all_side_orders(self.cancel_orders_upon_exit)
            
            self.logout()
            
            raise e
    
    def stop(self):
        pass

    def resume(self):
        self.start(True)
    
    def backtest(self, crypto_symbol, initial_cash_balance=1000):
        """
        Returns a dictionary with the following keys:
            initial_cash_balance,
            initial_crypto_equity,
            initial_balance,
            final_cash_balance,
            final_crypto_equity,
            final_balance,
            current_cash_balance,
            current_crypto_equity,
            profit,
            percent_change,
            crypto,
            interval,
            span,
            bounds
        """
        try:
            print("starting backtesting...")

            result = {
                'initial_cash_balance': initial_cash_balance,
                'initial_crypto_equity': 0,
                'initial_balance': initial_cash_balance,
                'final_cash_balance': None,
                'final_crypto_equity': None,
                'final_balance': None,
                'current_cash_balance': initial_cash_balance,
                'current_crypto_equity': 0,
                'profit': 0,
                'percent_change': 0,
                'crypto': crypto_symbol,
                'interval': self.backtest_interval,
                'span': self.backtest_span,
                'bounds': self.backtest_bounds
            }

            # Get crypto historical data
            # https://robin-stocks.readthedocs.io/en/latest/robinhood.html#robin_stocks.robinhood.crypto.get_crypto_historicals
            try:
                crypto_historical_data = rh.crypto.get_crypto_historicals(
                    symbol=crypto_symbol,
                    interval=self.backtest_interval,
                    span=self.backtest_span,
                    bounds=self.backtest_bounds
                )
            except TypeError as e:
                print(f"Failed to fetch crypto historical data for {crypto_symbol} for the following parameters: interval={self.backtest_interval}, span={self.backtest_span}, bounds={self.backtest_span}.")
                raise e

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

            self.cash_per_level = round_down_to_cents(self.cash / self.level_num)

            # Determine what the prices are at each level
            for i in range(self.level_num):
                self.grids[f'order_{i}'] = {
                    'price': round_to_min_order_price_increment(self.lower_price + i*(self.upper_price - self.lower_price)/(self.level_num-1), self.crypto_meta_data['min_order_price_increment'])
                }

            # Get crypto quote
            self.crypto_quote = crypto_historical_data[0]

            """
            Notes:
            (1) ask_price > bid_price due to spread (0.3-0.4%)
            (2) Everything below ask_price is buy
            (3) Everything above bid_price is sell
            (4) But if spread is very large and they overlap, ignore the overlapping level(s)
            """

            # Mark orders as buys and sells
            for i in range(len(self.grids)):
                if float(self.crypto_quote['close_price']) > self.grids[f'order_{i}']['price']:
                    self.grids[f'order_{i}']['side'] = 'buy'
                else:
                    self.grids[f'order_{i}']['side'] = 'sell'

            # Determine which grid line is closest to the current price
            min_dist = float('inf')
            self.closest_grid = -1

            for i in range(len(self.grids)):
                dist = abs(self.grids[f'order_{i}']['price'] - float(self.crypto_quote['close_price']))

                if dist < min_dist:
                    min_dist = dist
                    self.closest_grid = i
            
            # Mark the closest grid line as inactive
            self.grids[f'order_{self.closest_grid}']['status'] = 'inactive'

            # Mark all the other grid lines as active
            for i in range(len(self.grids)):
                if i != self.closest_grid:
                    self.grids[f'order_{i}']['status'] = 'active'
            
            print_grids(self.grids, self.cash_per_level)

            # Determine amount of dollars to buy initial amount of cryptocurrency
            grid_level_initial_buy_count = 0

            for i in range(len(self.grids)):
                if self.grids[f'order_{i}']['side'] == 'sell' and self.grids[f'order_{i}']['status'] == 'active':
                    grid_level_initial_buy_count += 1
            
            initial_buy_amount = grid_level_initial_buy_count * self.cash_per_level

            print("Placing a market order for $" + str(initial_buy_amount) + " at an ask price of $" + str(self.crypto_quote['close_price']))

            # Update available_cash, holdings, bought_price, profit, and percent_change to simulate the fulfillment of the limit buy order
            result['current_cash_balance'] -= initial_buy_amount
            result['current_crypto_equity'] += round_to_min_order_quantity_increment(initial_buy_amount/float(self.crypto_quote['close_price']), self.crypto_meta_data['min_order_quantity_increment'])
            result['profit'] = result['current_cash_balance'] + round_down_to_cents(result['current_crypto_equity'] * float(self.crypto_quote['close_price'])) - result['initial_balance']
            result['percent_change'] = result['profit'] * 100 / result['initial_balance']

            # Place limit buy orders and possibly limit sell orders
            for i in range(len(self.grids)):
                if self.grids[f'order_{i}']['side'] == 'buy' and self.grids[f'order_{i}']['status'] == 'active':
                    print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[f'order_{i}']['price']))
                    self.grids[f'order_{i}']['order'] = None
                elif self.grids[f'order_{i}']['side'] == 'sell' and self.grids[f'order_{i}']['status'] == 'active':
                    print("Placing a limit sell order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[f'order_{i}']['price']))
                    self.grids[f'order_{i}']['order'] = None
                else:
                    self.grids[f'order_{i}']['order'] = None
            
            print("finished grid initalization")

            print(f"1/{len(crypto_historical_data)}")

            for i in range(1, len(crypto_historical_data)):
                print(f"{i+1}/{len(crypto_historical_data)}")

                # Check if backtesting should continue
                if result['profit'] >= -1 * self.loss_threshold and result['percent_change'] >= -1 * self.loss_percentage:
                    # Continue iterating
                    # Get the latest crypto prices
                    self.crypto_quote = crypto_historical_data[i]

                    # Update the orders accordingly
                    for i in range(len(self.grids)):
                        # Ensure that there is an order and that it is active
                        if self.grids[f'order_{i}']['status'] == 'active':
                            # Check to see if either as a buy or sell order that it has been filled
                            if (self.grids[f'order_{i}']['side'] == 'buy' and float(self.crypto_quote['close_price']) <= self.grids[f'order_{i}']['price']) or (self.grids[f'order_{i}']['side'] == 'sell' and float(self.crypto_quote['close_price']) >= self.grids[f'order_{i}']['price']):
                                if self.grids[f'order_{i}']['side'] == 'buy' and self.closest_grid == i+1:
                                    # If the filled order was a buy order, place a sell order on the level above it, assuming it was previously inactive

                                    # Update available_cash, holdings, bought_price, profit, and percent_change to simulate the fulfillment of the limit buy order
                                    result['current_cash_balance'] -= self.cash_per_level
                                    result['current_crypto_equity'] += round_to_min_order_quantity_increment(self.cash_per_level/self.grids[f'order_{i}']['price'], self.crypto_meta_data['min_order_quantity_increment'])
                                    result['profit'] = result['current_cash_balance'] + round_down_to_cents(result['current_crypto_equity'] * float(self.crypto_quote['close_price'])) - result['initial_balance']
                                    result['percent_change'] = result['profit'] * 100 / result['initial_balance']

                                    # Set the filled level to inactive and adjust the inactive index
                                    self.grids[f'order_{i}']['status'] = 'inactive'
                                    self.closest_grid = i

                                    # Place a sell order on grid line i+1
                                    self.grids[f'order_{i+1}']['side'] = 'sell'
                                    self.grids[f'order_{i+1}']['status'] = 'active'
                                    
                                    print("Placing a limit sell order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[f'order_{i+1}']['price']))
                                elif self.grids[f'order_{i}']['side'] == 'sell' and self.closest_grid == i-1:
                                    # If the filled order was a sell order, place a buy order on the level below it, assuming it was previously inactive

                                    # Update available_cash, holdings, profit, and percent_change to simulate the fulfillment of the limit sell order
                                    result['current_cash_balance'] += self.cash_per_level
                                    result['current_crypto_equity'] -= round_to_min_order_quantity_increment(self.cash_per_level/self.grids[f'order_{i}']['price'], self.crypto_meta_data['min_order_quantity_increment'])
                                    result['profit'] = result['current_cash_balance'] + round_down_to_cents(result['current_crypto_equity'] * float(self.crypto_quote['close_price'])) - result['initial_balance']
                                    result['percent_change'] = result['profit'] * 100 / result['initial_balance']

                                    # Set the filled level to inactive and adjust the inactive index
                                    self.grids[f'order_{i}']['status'] = 'inactive'
                                    self.closest_grid = i

                                    # Place a buy order on grid line i
                                    self.grids[f'order_{i-1}']['side'] = 'buy'
                                    self.grids[f'order_{i-1}']['status'] = 'active'

                                    print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[f'order_{i-1}']['price']))
                                else:
                                    # TODO: Implement
                                    raise Exception("Order was filled but either was not sell nor buy or ignored level was not correct or both")
                else:
                    print("Either loss threshold or loss percentage exceeded: terminating backtesting")
                    break

            result['final_cash_balance'] = result['current_cash_balance']
            result['final_crypto_equity'] = result['current_crypto_equity']
            result['final_balance'] = result['final_cash_balance'] + round_down_to_cents(result['final_crypto_equity'] * float(self.crypto_quote['close_price']))
            
            return result
        except Exception as e:
            print("An unexpected error occured: logging out")
            
            self.logout()

            raise e
    
    def get_balances(self):
        """
        Updates available_cash, equity, holdings, bought_price, profit, and percent_change
        """
        self.available_cash, self.equity = self.get_cash_and_equity()

        self.holdings, self.bought_price = self.get_holdings_and_bought_price()

        self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital

        self.percent_change = self.profit * 100 / self.cash
    
    def test_get_balances(self):
        """
        Updates equity, profit, and percent_change
        """
        _, self.equity = self.get_cash_and_equity()
        
        self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital

        self.percent_change = self.profit * 100 / self.cash
    
    def continue_trading(self):
        """
        Time: O(1)
        Space: O(1)
        Returns true if loss has not exceeded loss threshold or loss percentage threshold. If either loss threshold or loss percentage threshold have been passed then False is returned.
        """
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
        print(time.ctime())
        
        print("mode: " + self.mode)
        print("runtime: " + display_time(self.get_runtime()))
        
        print("equity: $" + str(round(self.equity, 2)))
        
        print('crypto holdings:')
        print(display_holdings(self.holdings, [self.get_latest_quote(crypto)['mark_price'] for crypto, amount in self.holdings.items()]))

        print('crypto average bought price:')
        print(display_bought_price(self.bought_price))
        
        print("crypto equity: $" + str(round(self.get_crypto_holdings_capital(), 2)))
        print("cash: " + display_cash(self.available_cash))
        print("crypto equity and cash: " + display_crypto_equity_and_cash(self.available_cash, self.get_crypto_holdings_capital()))
        
        print("profit: " + display_profit(self.profit) + " (" + display_percent_change(self.percent_change) + ")")

        print(self.crypto + " ask price: $" + str(round_to_min_order_price_increment(self.crypto_quote['ask_price'], self.crypto_meta_data['min_order_price_increment'])))
        print(self.crypto + " market price: $" + str(round_to_min_order_price_increment(self.crypto_quote['mark_price'], self.crypto_meta_data['min_order_price_increment'])))
        print(self.crypto + " bid price: $" + str(round_to_min_order_price_increment(self.crypto_quote['bid_price'], self.crypto_meta_data['min_order_price_increment'])))

        spread = (self.crypto_quote['ask_price'] - self.crypto_quote['bid_price']) * 100 / self.crypto_quote['mark_price']
        print(self.crypto + " spread: " + str(round(spread, 2)) + "%")

        print("number of pending orders:", len(get_all_open_orders()))
        print("grids:")
        print_grids(self.grids, self.cash_per_level)
        print('\n')
    
    def get_latest_quote(self, crypto_symbol):
        """
        Returns a dictionary of the latest quote of the cryptocurrency.
        Dictionary Keys:
            ask_price,
            ask_source,
            bid_price,
            bid_source,
            mark_price,
            high_price,
            low_price,
            open_price,
            symbol,
            id,
            volume,
            updated_at
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

        self.cash_per_level = round_down_to_cents(self.cash / self.level_num)

        # Determine what the prices are at each level
        for i in range(self.level_num):
            self.grids[f'order_{i}'] = {'price': round_to_min_order_price_increment(self.lower_price + i*(self.upper_price - self.lower_price)/(self.level_num-1), self.crypto_meta_data['min_order_price_increment'])}

        # Get crypto quote
        self.crypto_quote = self.get_latest_quote(self.crypto)

        """
        Notes:
        (1) ask_price > bid_price due to spread (0.3-0.4%)
        (2) Everything below ask_price is buy
        (3) Everything above bid_price is sell
        (4) But if spread is very large and they overlap, ignore the overlapping level(s)
        """

        # Mark orders as buys and sells
        for i in range(len(self.grids)):
            if self.crypto_quote['ask_price'] > self.grids[f'order_{i}']['price']:
                self.grids[f'order_{i}']['side'] = 'buy'
            else:
                self.grids[f'order_{i}']['side'] = 'sell'

        # Determine which grid line is closest to the current price
        min_dist = float('inf')
        self.closest_grid = -1

        for i in range(len(self.grids)):
            dist = abs(self.grids[f'order_{i}']['price'] - self.crypto_quote['ask_price'])

            if dist < min_dist:
                min_dist = dist
                self.closest_grid = i
        
        # Mark the closest grid line as inactive
        self.grids[f'order_{self.closest_grid}']['status'] = 'inactive'

        # Mark all the other grid lines as active
        for i in range(len(self.grids)):
            if i != self.closest_grid:
                self.grids[f'order_{i}']['status'] = 'active'
        
        print_grids(self.grids, self.cash_per_level)

        # Determine amount of dollars to buy initial amount of cryptocurrency
        grid_level_initial_buy_count = 0
        for i in range(len(self.grids)):
            if self.grids[f'order_{i}']['side'] == 'sell' and self.grids[f'order_{i}']['status'] == 'active':
                grid_level_initial_buy_count += 1
        
        initial_buy_amount = grid_level_initial_buy_count * self.cash_per_level

        # Place market order for cryptocurrency
        if self.mode == 'live':
            rh.orders.order_buy_crypto_by_price(self.crypto, initial_buy_amount, timeInForce='gtc', jsonify=True)
            #rh.orders.order_buy_crypto_limit(self.crypto, self.round_to_min_order_quantity_increment(initial_buy_amount/self.crypto_quote['ask_price']), self.round_to_min_order_price_increment(self.crypto_quote['ask_price']), timeInForce='gtc', jsonfiy=True)
        else:
            print("Placing a market order for $" + str(initial_buy_amount) + " at an ask price of $" + str(self.crypto_quote['ask_price']))

            # Update available_cash, holdings, bought_price, profit, and percent_change to simulate the fulfillment of the limit buy order
            self.available_cash -= initial_buy_amount
            self.holdings[self.crypto] += round_to_min_order_quantity_increment(initial_buy_amount/self.crypto_quote['ask_price'], self.crypto_meta_data['min_order_quantity_increment'])
            self.bought_price[self.crypto] = round_to_min_order_price_increment( ((self.bought_price[self.crypto] * self.holdings[self.crypto]) + (initial_buy_amount)) / (self.holdings[self.crypto] + round_to_min_order_quantity_increment(initial_buy_amount/self.crypto_quote['ask_price'], self.crypto_meta_data['min_order_quantity_increment'])), self.crypto_meta_data['min_order_price_increment'])
            self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital
            self.percent_change = self.profit * 100 / self.cash
        
        # Place limit buy orders and possibly limit sell orders
        for i in range(len(self.grids)):
            if self.grids[f'order_{i}']['side'] == 'buy' and self.grids[f'order_{i}']['status'] == 'active':
                if self.mode == 'live':
                    #self.grids[f'order_{i}']['order'] = Order(rh.orders.order_buy_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids[f'order_{i}']['price'], timeInForce='gtc', jsonify=True))
                    self.grids[f'order_{i}']['order'] = Order(rh.orders.order_buy_crypto_limit(self.crypto, round_to_min_order_quantity_increment(self.cash_per_level/self.grids[f'order_{i}']['price'], self.crypto_meta_data['min_order_quantity_increment']), self.grids[f'order_{i}']['price'], timeInForce='gtc', jsonify=True))
                else:
                    print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[f'order_{i}']['price']))
                    self.grids[f'order_{i}']['order'] = None
            elif self.grids[f'order_{i}']['side'] == 'sell' and self.grids[f'order_{i}']['status'] == 'active':
                if self.mode == 'live':
                    err_count = 0
                    while err_count < self.init_buy_error_max_count:
                        try:
                            #self.grids[f'order_{i}']['order'] = Order(rh.orders.order_sell_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids[f'order_{i}']['price'], timeInForce='gtc', jsonify=True))
                            self.grids[f'order_{i}']['order'] = Order(rh.orders.order_sell_crypto_limit(self.crypto, round_to_min_order_quantity_increment(self.cash_per_level/self.grids[f'order_{i}']['price'], self.crypto_meta_data['min_order_quantity_increment']), self.grids[f'order_{i}']['price'], timeInForce='gtc', jsonify=True))
                        except KeyError as ex:
                            err_count += 1
                            if err_count >= self.init_buy_error_max_count:
                                raise ex
                            else:
                                time.sleep(self.init_buy_error_latency)
                else:
                    print("Placing a limit sell order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[f'order_{i}']['price']))
                    self.grids[f'order_{i}']['order'] = None
            else:
                self.grids[f'order_{i}']['order'] = None
        
        print("finished grid initalization")
    
    def update_orders(self):
        for i in range(len(self.grids)):
            # Update each order
            if self.grids[f'order_{i}']['status'] == 'active' and self.grids[f'order_{i}']['order'] is not None:
                self.grids[f'order_{i}']['order'].update()

                if self.grids[f'order_{i}']['order'] is not None and self.grids[f'order_{i}']['order'].is_filled():
                    if self.grids[f'order_{i}']['side'] == 'buy' and self.closest_grid == i+1:
                        # If the filled order was a buy order, place a sell order on the level above it, assuming it was previously inactive

                        # Set the filled level to inactive and adjust the inactive index
                        self.grids[f'order_{i}']['status'] = 'inactive'
                        self.closest_grid = i

                        # Place a sell order on grid line i+1
                        self.grids[f'order_{i+1}']['side'] = 'sell'
                        self.grids[f'order_{i+1}']['status'] = 'active'

                        #self.grids[f'order_{i+1}']['order'] = Order(rh.orders.order_sell_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids[f'order_{i+1}']['price'], timeInForce='gtc', jsonify=True))
                        self.grids[f'order_{i+1}']['order'] = Order(
                            rh.orders.order_sell_crypto_limit(
                                self.crypto,
                                round_to_min_order_quantity_increment(self.cash_per_level/self.grids[f'order_{i+1}']['price'], self.crypto_meta_data['min_order_quantity_increment']),
                                self.grids[f'order_{i+1}']['price'],
                                timeInForce='gtc',
                                jsonify=True
                            )
                        )

                        print("Placing a limit sell order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[f'order_{i+1}']['price']))
                    elif self.grids[f'order_{i}']['side'] == 'sell' and self.closest_grid == i-1:
                        # If the filled order was a sell order, place a buy order on the level below it, assuming it was previously inactive

                        # Set the filled level to inactive and adjust the inactive index
                        self.grids[f'order_{i}']['status'] = 'inactive'
                        self.closest_grid = i

                        # Place a buy order on grid line i
                        self.grids[f'order_{i-1}']['side'] = 'buy'
                        self.grids[f'order_{i-1}']['status'] = 'active'

                        #self.grids[f'order_{i-1}']['order'] = Order(rh.orders.order_buy_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids[f'order_{i-1}']['price'], timeInForce='gtc', jsonify=True))
                        self.grids[f'order_{i-1}']['order'] = Order(
                            rh.orders.order_buy_crypto_limit(
                                self.crypto,
                                round_to_min_order_quantity_increment(self.cash_per_level/self.grids[f'order_{i-1}']['price'], self.crypto_meta_data['min_order_quantity_increment']),
                                self.grids[f'order_{i-1}']['price'],
                                timeInForce='gtc',
                                jsonify=True
                            )
                        )

                        print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[f'order_{i-1}']['price']))
                    else:
                        # TODO: Implement
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
        Time: O(1)
        Space: O(1)
        Returns the runtime in seconds
        """
        return time.time() - self.start_time
    
    def get_cash_and_equity(self):
        """
        Returns cash, equity as floats from robin_stocks.robinhood.account.build_user_profile()
        """
        rh_cash = rh.account.build_user_profile()
        
        cash = round_down_to_cents(float(rh_cash['cash']))
        equity = round_down_to_cents(float(rh_cash['equity']))
        
        return cash, equity
    
    def get_crypto_holdings_capital(self):
        """
        Returns the current dollar value of crypto assets using the market price
        """
        capital = 0.00
        
        for crypto_name, crypto_amount in self.holdings.items():
            capital += crypto_amount * float(self.get_latest_quote(crypto_name)['mark_price'])
        
        return round_down_to_cents(capital)
    
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
                        self.holdings[self.crypto] += round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i)]['price'], self.crypto_meta_data['min_order_quantity_increment'])
                        self.bought_price[self.crypto] = round_to_min_order_price_increment( ((self.bought_price[self.crypto] * self.holdings[self.crypto]) + (self.cash_per_level)) / (self.holdings[self.crypto] + round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i)]['price'], self.crypto_meta_data['min_order_quantity_increment'])), self.crypto_meta_data['min_order_price_increment'])
                        self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital
                        self.percent_change = self.profit * 100 / self.cash

                        # Set the filled level to inactive and adjust the inactive index
                        self.grids['order_' + str(i)]['status'] = 'inactive'
                        self.closest_grid = i

                        # Place a sell order on grid line i+1
                        self.grids['order_' + str(i+1)]['side'] = 'sell'
                        self.grids['order_' + str(i+1)]['status'] = 'active'
                        
                        if self.mode == 'live':
                            #self.grids['order_' + str(i+1)]['order'] = Order(rh.orders.order_sell_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids['order_' + str(i+1)]['price'], timeInForce='gtc', jsonify=True))
                            self.grids['order_' + str(i+1)]['order'] = Order(rh.orders.order_sell_crypto_limit(self.crypto, round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i+1)]['price'], self.crypto_meta_data['min_order_quantity_increment']), self.grids['order_' + str(i+1)]['price'], timeInForce='gtc', jsonify=True))
                        else:
                            print("Placing a limit sell order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids['order_' + str(i+1)]['price']))
                            self.grids['order_' + str(i+1)]['order'] = None
                    elif self.grids['order_' + str(i)]['side'] == 'sell' and self.closest_grid == i-1:
                        # If the filled order was a sell order, place a buy order on the level below it, assuming it was previously inactive

                        # Update available_cash, holdings, profit, and percent_change to simulate the fulfillment of the limit sell order
                        self.available_cash += self.cash_per_level
                        self.holdings[self.crypto] -= round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i)]['price'], self.crypto_meta_data['min_order_quantity_increment'])
                        self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital
                        self.percent_change = self.profit * 100 / self.cash

                        # Set the filled level to inactive and adjust the inactive index
                        self.grids['order_' + str(i)]['status'] = 'inactive'
                        self.closest_grid = i

                        # Place a buy order on grid line i
                        self.grids['order_' + str(i-1)]['side'] = 'buy'
                        self.grids['order_' + str(i-1)]['status'] = 'active'

                        if self.mode == 'live':
                            #self.grids['order_' + str(i-1)]['order'] = Order(rh.orders.order_buy_crypto_limit_by_price(self.crypto, self.cash_per_level, self.grids['order_' + str(i-1)]['price'], timeInForce='gtc', jsonify=True))
                            self.grids['order_' + str(i-1)]['order'] = Order(rh.orders.order_buy_crypto_limit(self.crypto, round_to_min_order_quantity_increment(self.cash_per_level/self.grids['order_' + str(i-1)]['price'], self.crypto_meta_data['min_order_quantity_increment']), self.grids['order_' + str(i-1)]['price'], timeInForce='gtc', jsonify=True))
                        else:
                            print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids['order_' + str(i-1)]['price']))
                            self.grids['order_' + str(i-1)]['order'] = None
                    else:
                        # TODO: Implement
                        raise Exception("Order was filled but either was not sell nor buy or ignored level was not correct or both")
    
    def send_message_to_discord(self):
        """
        Sends out the lastest information out to the discord channel
        """
        if self.last_discord_post is None or time.time() - self.last_discord_post >= self.discord_latency_in_hours * 3600:
            message = ""
            message += time.ctime() + "\n"
            message += "=============================================\n"
            message += "mode: " + self.mode + "\n"
            message += "runtime: " + display_time(self.get_runtime()) + "\n"
            message += "equity: $" + str(round(self.equity, 2)) + "\n"
            message += 'crypto holdings:\n'
            message += display_holdings(self.holdings, [self.get_latest_quote(crypto)['mark_price'] for crypto, amount in self.holdings.items()]) + '\n'
            message += 'crypto average bought price:\n'
            message += display_bought_price(self.bought_price) + '\n'
            message += "crypto equity: $" + str(round(self.get_crypto_holdings_capital(), 2)) + '\n'
            message += "cash: " + display_cash(self.available_cash) + '\n'
            message += "crypto equity and cash: " + display_crypto_equity_and_cash(self.available_cash, self.get_crypto_holdings_capital()) + '\n'
            message += "profit: " + display_profit(self.profit) + " (" + display_percent_change(self.percent_change) + ")\n"

            message += self.crypto + " ask price: $" + str(round_to_min_order_price_increment(self.crypto_quote['ask_price'], self.crypto_meta_data['min_order_price_increment'])) + '\n'
            message += self.crypto + " market price: $" + str(round_to_min_order_price_increment(self.crypto_quote['mark_price'], self.crypto_meta_data['min_order_price_increment'])) + '\n'
            message += self.crypto + " bid price: $" + str(round_to_min_order_price_increment(self.crypto_quote['bid_price'], self.crypto_meta_data['min_order_price_increment'])) + '\n'

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
    
    def send_start_message_to_discord(self):
        """
        Sends out a message to discord indicating the grid trading bot has been activated
        """
        message = "Grid Trading Bot: ACTIVATED"
        self.discord_webhook.send(message)
    
    def send_end_message_to_discord(self):
        """
        Sends out a message to discord indicating the grid trading bot has stopped
        """
        message = "Grid Trading Bot: STOPPED"
        self.discord_webhook.send(message)
    
    def send_error_message_to_discord(self, exception, error_type):
        message = "Exception Occured: " + error_type + '\n'
        message += str(exception)
        self.discord_webhook.send(message)
    
    def send_loss_exceeded_message_to_discord(self):
        message = "Either loss exceeded $" + str(self.loss_threshold) + " or loss percentage exceeded " + str(self.loss_percentage) + "%"
        self.discord_webhook.send(message)
