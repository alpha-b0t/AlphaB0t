import robin_stocks.robinhood as rh
from Strategy.order import *
from Strategy.error_queue import ErrorQueue, ErrorQueueLimitExceededError
import time
from Strategy.helpers import *
from config import GRIDBotConfig
import random

class GRIDBot():
    def __init__(self, config: GRIDBotConfig):
        self.check_config(config)

        self.pair = config.pair
        self.days_to_run = config.days_to_run
        self.mode = config.mode

        self.upper_price = config.upper_price
        self.lower_price = config.lower_price
        self.level_num = config.level_num
        self.cash = config.cash
        self.stop_loss = config.stop_loss
        self.latency = config.latency_in_sec
        
        self.error_latency = config.error_latency_in_sec
        self.max_error_count = config.max_error_count
        
        self.error_queue = ErrorQueue(self.error_latency, self.max_error_count)
        
        self.init_buy_error_latency = config.init_buy_error_latency_in_sec
        self.init_buy_error_max_count = config.init_buy_error_max_count
        self.cancel_orders_upon_exit = config.cancel_orders_upon_exit

        self.login()

        self.crypto_meta_data = rh.crypto.get_crypto_info(self.pair)
        self.crypto_historical_data = None

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
    
    def check_config(self, config: GRIDBotConfig):
        """
        Time: O(1)
        Space: O(1)
        Assures that the configuration is as expected. Raises an exception if an error is found.
        """
        assert isinstance(config.pair, str)
        assert len(config.pair) > 0
        assert isinstance(config.days_to_run, int)
        assert config.days_to_run >= 1
        assert config.mode in ['live', 'test']

        assert type(config.upper_price) == float or type(config.upper_price) == int
        assert config.upper_price > 0
        assert type(config.lower_price) == float or type(config.lower_price) == int
        assert config.lower_price > 0
        assert isinstance(config.level_num, int)
        assert config.level_num >= 2
        assert type(config.cash) == float or type(config.cash) == int
        assert config.cash > 0
        assert type(config.stop_loss) == float or type(config.stop_loss) == int
        assert config.stop_loss > 0
        assert type(config.latency_in_sec) == float or type(config.latency_in_sec) == int
        assert config.latency_in_sec > 0
        assert type(config.max_error_count) == int
        assert type(config.error_latency_in_sec) == float or type(config.error_latency_in_sec) == int
        assert config.error_latency_in_sec > 0

        if config.mode == 'live':
            assert type(config.init_buy_error_latency_in_sec) == int or type(config.init_buy_error_latency_in_sec) == float
            assert config.init_buy_error_latency_in_sec > 0
            assert type(config.init_buy_error_max_count) == int
            assert config.init_buy_error_max_count > 0
        
        assert config.cancel_orders_upon_exit in ['all', 'buy', 'sell', 'none']
        
        print("Configuration test: PASSED")
    
    def login(self):
        """
        Logs the user in with username and password with verification by sms text. This method does not store the session.
        """
        time_logged_in = 60 * 60 * 24 * self.days_to_run
        
        rh.authentication.login(expiresIn=time_logged_in,
                                scope='internal',
                                by_sms=True,
                                store_session=False)
        
        print("Login successful")
    
    def logout(self):
        """
        Attempts to log out the user unless already logged out.
        """
        try:
            rh.authentication.logout()
            
            print('Logout successful')
        except:
            print('Already logged out: logout() can only be called when currently logged in')
    
    def start(self, is_initialized=False):
        try:
            if not is_initialized:
                self.init_grid()
                
                if self.mode == 'live':
                    self.get_balances()
                else:
                    self.test_get_balances()
                
                self.error_queue.refresh()

            # Check if the loss is acceptable
            while self.is_loss_acceptable():
                # Get latest crypto prices
                self.crypto_quote = self.get_latest_quote(self.pair)

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
                
                # Refresh the error queue
                self.error_queue.refresh()

                # Wait for self.latency seconds
                time.sleep(self.latency)

            # Cancel all open crypto orders
            if self.cancel_orders_upon_exit == 'all':
                cancel_all_orders()
            elif self.cancel_orders_upon_exit == 'buy' or self.cancel_orders_upon_exit == 'sell':
                cancel_all_side_orders(self.cancel_orders_upon_exit)

            # Log out
            self.logout()
        
        except KeyboardInterrupt as e:
            print("User ended execution of program.")
            
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
                self.error_queue.refresh()
                self.error_queue.append(time.time())
            except ErrorQueueLimitExceededError as e:
                if self.cancel_orders_upon_exit == 'all':
                    cancel_all_orders()
                elif self.cancel_orders_upon_exit == 'buy' or self.cancel_orders_upon_exit == 'sell':
                    cancel_all_side_orders(self.cancel_orders_upon_exit)
                
                self.logout()
                
                raise e
            
            # Continue trading
            self.resume()
        
        except KeyError as e:
            # Robinhood Internal Error
            # 503 Service Error: Service Unavailable for url: https://api.robinhood.com/portfolios/
            # 500 Server Error: Internal Server Error for url: https://api.robinhood.com/portfolios/
            print("Robinhood Internal Error: KeyError: continuing trading")
            
            try:
                self.error_queue.refresh()
                self.error_queue.append(time.time())
            except ErrorQueueLimitExceededError as e:                
                if self.cancel_orders_upon_exit == 'all':
                    cancel_all_orders()
                elif self.cancel_orders_upon_exit == 'buy' or self.cancel_orders_upon_exit == 'sell':
                    cancel_all_side_orders(self.cancel_orders_upon_exit)
                
                self.logout()
                
                raise e
            
            # Continue trading
            self.resume()
        
        except Exception as e:
            print("An unexpected error occured: cancelling open orders and logging out")
            
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
    
    def simulate_trading(self, pair: str, level_num: int, upper_price: float, lower_price: float, interval: str, span: str, bounds: str, stop_loss: float) -> float:
        """Simulates GRID trading using given parameters"""
        try:
            assert interval in ['15second', '5minute', '10minute', 'hour', 'day', 'week']
            assert span in ['hour', 'day', 'week', 'month', '3month', 'year', '5year']
            assert bounds in ['Regular', 'trading', 'extended', '24_7']

            print("Simulating GRID trading...")

            result = {
                'initial_cash_balance': 1000,
                'initial_crypto_equity': 0,
                'initial_balance': 1000,
                'current_cash_balance': 1000,
                'current_crypto_equity': 0,
                'final_cash_balance': 0,
                'final_crypto_equity': 0,
                'final_balance': 0,
                'profit': 0,
                'percent_change': 0,
            }

            if self.crypto_historical_data == None:
                # Get crypto historical data
                # https://robin-stocks.readthedocs.io/en/latest/robinhood.html#robin_stocks.robinhood.crypto.get_crypto_historicals
                try:
                    self.crypto_historical_data = rh.crypto.get_crypto_historicals(
                        symbol=pair,
                        interval=interval,
                        span=span,
                        bounds=bounds
                    )
                except TypeError as e:
                    print(f"Failed to fetch crypto historical data for {pair} for the following parameters: interval={interval}, span={span}, bounds={bounds}.")
                    raise e

            # Initialize grids
            """
            grids = {
                i: {
                    'price': 35.32,
                    'side': 'buy_or_sell',
                    'status': 'active_or_inactive',
                    'order': Order
                }
            }
            """
            grids = {}

            cash_per_level = round_down_to_cents(result['initial_cash_balance'] / level_num)

            # Determine what the prices are at each level
            for i in range(level_num):
                grids[i] = {
                    'price': round_to_min_order_price_increment(lower_price + i*(upper_price - lower_price)/(level_num-1), self.crypto_meta_data['min_order_price_increment'])
                }

            # Get crypto quote
            crypto_quote = self.crypto_historical_data[0]

            """
            Notes:
            (1) ask_price > bid_price due to spread (0.3-0.4%)
            (2) Everything below ask_price is buy
            (3) Everything above bid_price is sell
            (4) But if spread is very large and they overlap, ignore the overlapping level(s)
            """

            # Mark orders as buys and sells
            for i in range(len(grids)):
                if float(crypto_quote['close_price']) > grids[i]['price']:
                    grids[i]['side'] = 'buy'
                else:
                    grids[i]['side'] = 'sell'

            # Determine which grid line is closest to the current price
            min_dist = float('inf')
            closest_grid = -1

            for i in range(len(grids)):
                dist = abs(grids[i]['price'] - float(crypto_quote['close_price']))

                if dist < min_dist:
                    min_dist = dist
                    closest_grid = i
            
            # Mark the closest grid line as inactive
            grids[closest_grid]['status'] = 'inactive'

            # Mark all the other grid lines as active
            for i in range(len(grids)):
                if i != closest_grid:
                    grids[i]['status'] = 'active'
            
            display_grids(grids, cash_per_level)

            # Determine amount of dollars to buy initial amount of cryptocurrency
            grid_level_initial_buy_count = 0

            for i in range(len(grids)):
                if grids[i]['side'] == 'sell' and grids[i]['status'] == 'active':
                    grid_level_initial_buy_count += 1
            
            initial_buy_amount = grid_level_initial_buy_count * cash_per_level

            print("Placing a market order for $" + str(initial_buy_amount) + " at an ask price of $" + str(crypto_quote['close_price']))

            # Update available_cash, holdings, bought_price, profit, and percent_change to simulate the fulfillment of the limit buy order
            result['current_cash_balance'] -= initial_buy_amount
            result['current_crypto_equity'] += round_to_min_order_quantity_increment(initial_buy_amount/float(crypto_quote['close_price']), self.crypto_meta_data['min_order_quantity_increment'])
            result['profit'] = result['current_cash_balance'] + round_down_to_cents(result['current_crypto_equity'] * float(crypto_quote['close_price'])) - result['initial_balance']
            result['percent_change'] = result['profit'] * 100 / result['initial_balance']

            # Place limit buy orders and possibly limit sell orders
            for i in range(len(grids)):
                if grids[i]['side'] == 'buy' and grids[i]['status'] == 'active':
                    print("Placing a limit buy order for $" + str(cash_per_level) + " at a price of $" + str(grids[i]['price']))
                    grids[i]['order'] = None
                elif grids[i]['side'] == 'sell' and grids[i]['status'] == 'active':
                    print("Placing a limit sell order for $" + str(cash_per_level) + " at a price of $" + str(grids[i]['price']))
                    grids[i]['order'] = None
                else:
                    grids[i]['order'] = None
            
            print("Finished grid initalization")

            print("Iterating...")

            for i in range(1, len(self.crypto_historical_data)):
                # Check if backtesting should continue
                if result['profit'] >= -1 * stop_loss:
                    # Continue iterating
                    # Get the latest crypto prices
                    crypto_quote = self.crypto_historical_data[i]

                    # Update the orders accordingly
                    for i in range(len(grids)):
                        # Ensure that there is an order and that it is active
                        if grids[i]['status'] == 'active':
                            # Check to see if either as a buy or sell order that it has been filled
                            if (grids[i]['side'] == 'buy' and float(crypto_quote['close_price']) <= grids[i]['price']) or (grids[i]['side'] == 'sell' and float(crypto_quote['close_price']) >= grids[i]['price']):
                                if grids[i]['side'] == 'buy':
                                    if closest_grid == i+1:
                                        # If the filled order was a buy order, place a sell order on the level above it, assuming it was previously inactive

                                        # Update available_cash, holdings, bought_price, profit, and percent_change to simulate the fulfillment of the limit buy order
                                        result['current_cash_balance'] -= cash_per_level
                                        result['current_crypto_equity'] += round_to_min_order_quantity_increment(cash_per_level/grids[i]['price'], self.crypto_meta_data['min_order_quantity_increment'])
                                        result['profit'] = result['current_cash_balance'] + round_down_to_cents(result['current_crypto_equity'] * float(crypto_quote['close_price'])) - result['initial_balance']
                                        result['percent_change'] = result['profit'] * 100 / result['initial_balance']

                                        # Set the filled level to inactive and adjust the inactive index
                                        grids[i]['status'] = 'inactive'
                                        closest_grid = i

                                        # Place a sell order on grid line i+1
                                        grids[i+1]['side'] = 'sell'
                                        grids[i+1]['status'] = 'active'
                                        
                                        print("Placing a limit sell order for $" + str(cash_per_level) + " at a price of $" + str(grids[i+1]['price']))
                                    else:
                                        # TODO: Implement
                                        pass
                                elif grids[i]['side'] == 'sell':
                                    if closest_grid == i-1:
                                        # If the filled order was a sell order, place a buy order on the level below it, assuming it was previously inactive

                                        # Update available_cash, holdings, profit, and percent_change to simulate the fulfillment of the limit sell order
                                        result['current_cash_balance'] += cash_per_level
                                        result['current_crypto_equity'] -= round_to_min_order_quantity_increment(cash_per_level/grids[i]['price'], self.crypto_meta_data['min_order_quantity_increment'])
                                        result['profit'] = result['current_cash_balance'] + round_down_to_cents(result['current_crypto_equity'] * float(crypto_quote['close_price'])) - result['initial_balance']
                                        result['percent_change'] = result['profit'] * 100 / result['initial_balance']

                                        # Set the filled level to inactive and adjust the inactive index
                                        grids[i]['status'] = 'inactive'
                                        closest_grid = i

                                        # Place a buy order on grid line i
                                        grids[i-1]['side'] = 'buy'
                                        grids[i-1]['status'] = 'active'

                                        print("Placing a limit buy order for $" + str(cash_per_level) + " at a price of $" + str(grids[i-1]['price']))
                                    else:
                                        # TODO: Implement
                                        pass
                else:
                    print("Either loss threshold or loss percentage exceeded: terminating backtesting")
                    break

            result['final_cash_balance'] = result['current_cash_balance']
            result['final_crypto_equity'] = result['current_crypto_equity']
            result['final_balance'] = result['final_cash_balance'] + round_down_to_cents(result['final_crypto_equity'] * float(crypto_quote['close_price']))
            result['profit'] = result['final_balance'] - result['initial_balance']
            result['percent_change'] = result['profit'] * 100 / result['initial_balance']
            
            return result['percent_change']
        except Exception as e:
            print("An unexpected error occured: logging out")
            
            self.logout()

            raise e
    
    def optimize_parameters_genetic(self, level_num_values, upper_price_values, lower_price_values, population_size=50, generations=100, mutation_rate=0.1, survival_rate=0.5):
        # TODO: Need to refactor
        # Initialize a random population
        population = [(random.choice(level_num_values), random.uniform(upper_price_values[0], upper_price_values[-1]), random.uniform(lower_price_values[0], lower_price_values[-1])) for _ in range(population_size)]
        
        number_of_parents = int(population_size * survival_rate)

        # Main optimization loop
        for generation in range(generations):
            # Evaluate the fitness of each individual in the population
            fitness_scores = [self.simulate_grid_trading(*params) for params in population]

            # TODO: Need to refactor the selection process
            # Select the top-performing individuals to be parents
            selected_indices = sorted(range(population_size), key=lambda i: fitness_scores[i], reverse=True)
            selected_indices = selected_indices[:number_of_parents]
            selected_population = [population[i] for i in selected_indices]

            # Crossover and mutation
            new_population = []
            for _ in range(population_size):
                # Select two parents at random from the selected population to produce offspring
                parent1, parent2 = random.choices(selected_population, k=2)
                child = [random.choice(parent1[i], parent2[i]) for i in range(3)]

                # Mutate the child and add it to the new population
                child = self.mutate(child, level_num_values, upper_price_values, lower_price_values, mutation_rate)
                new_population.append(child)

            # Replace the old population with the new population
            population = new_population

        # The best parameter set is the one with the highest fitness score
        best_params = population[0]
        best_performance = self.simulate_grid_trading(*best_params)
        print("Best Parameters:", best_params)
        print("Best Performance:", best_performance)
    
    def mutate(self, genes, level_num_values, upper_price_values, lower_price_values, mutation_rate):
        """Mutate the individual's genetic sequence."""
        # TODO: Need to refactor
        for i in range(3):
            if random.random() < mutation_rate:
                if i == 0:
                    genes[i] = random.choice(level_num_values)
                elif i == 1:
                    genes[i] = random.uniform(upper_price_values[0], upper_price_values[-1])
                else:
                    genes[i] = random.uniform(lower_price_values[0], lower_price_values[-1])
        return genes
    
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
    
    def is_loss_acceptable(self):
        """
        Time: O(1)
        Space: O(1)
        Returns true if loss has not exceeded loss threshold or loss percentage threshold. If either loss threshold or loss percentage threshold have been passed then False is returned.
        """
        if self.profit >= -1 * self.stop_loss:
            return True
        else:
            print("Loss exceeded $" + str(self.stop_loss) + ": terminating automated trading")
            
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

        print(self.pair + " ask price: $" + str(round_to_min_order_price_increment(self.crypto_quote['ask_price'], self.crypto_meta_data['min_order_price_increment'])))
        print(self.pair + " market price: $" + str(round_to_min_order_price_increment(self.crypto_quote['mark_price'], self.crypto_meta_data['min_order_price_increment'])))
        print(self.pair + " bid price: $" + str(round_to_min_order_price_increment(self.crypto_quote['bid_price'], self.crypto_meta_data['min_order_price_increment'])))

        spread = (self.crypto_quote['ask_price'] - self.crypto_quote['bid_price']) * 100 / self.crypto_quote['mark_price']
        print(self.pair + " spread: " + str(round(spread, 2)) + "%")

        print("number of pending orders:", len(get_all_open_orders()))
        print("grids:")
        display_grids(self.grids, self.cash_per_level)
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
            i: {
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
            self.grids[i] = {'price': round_to_min_order_price_increment(self.lower_price + i*(self.upper_price - self.lower_price)/(self.level_num-1), self.crypto_meta_data['min_order_price_increment'])}

        # Get crypto quote
        self.crypto_quote = self.get_latest_quote(self.pair)

        """
        Notes:
        (1) ask_price > bid_price due to spread (0.3-0.4%)
        (2) Everything below ask_price is buy
        (3) Everything above bid_price is sell
        (4) But if spread is very large and they overlap, ignore the overlapping level(s)
        """

        # Mark orders as buys and sells
        for i in range(len(self.grids)):
            if self.crypto_quote['ask_price'] > self.grids[i]['price']:
                self.grids[i]['side'] = 'buy'
            else:
                self.grids[i]['side'] = 'sell'

        # Determine which grid line is closest to the current price
        min_dist = float('inf')
        self.closest_grid = -1

        for i in range(len(self.grids)):
            dist = abs(self.grids[i]['price'] - self.crypto_quote['ask_price'])

            if dist < min_dist:
                min_dist = dist
                self.closest_grid = i
        
        # Mark the closest grid line as inactive
        self.grids[self.closest_grid]['status'] = 'inactive'

        # Mark all the other grid lines as active
        for i in range(len(self.grids)):
            if i != self.closest_grid:
                self.grids[i]['status'] = 'active'
        
        display_grids(self.grids, self.cash_per_level)

        # Determine amount of dollars to buy initial amount of cryptocurrency
        grid_level_initial_buy_count = 0
        for i in range(len(self.grids)):
            if self.grids[i]['side'] == 'sell' and self.grids[i]['status'] == 'active':
                grid_level_initial_buy_count += 1
        
        initial_buy_amount = grid_level_initial_buy_count * self.cash_per_level

        # Place market order for cryptocurrency
        if self.mode == 'live':
            rh.orders.order_buy_crypto_by_price(self.pair, initial_buy_amount, timeInForce='gtc', jsonify=True)
        else:
            print("Placing a market order for $" + str(initial_buy_amount) + " at an ask price of $" + str(self.crypto_quote['ask_price']))

            # Update available_cash, holdings, bought_price, profit, and percent_change to simulate the fulfillment of the limit buy order
            self.available_cash -= initial_buy_amount
            self.holdings[self.pair] += round_to_min_order_quantity_increment(initial_buy_amount/self.crypto_quote['ask_price'], self.crypto_meta_data['min_order_quantity_increment'])
            self.bought_price[self.pair] = round_to_min_order_price_increment( ((self.bought_price[self.pair] * self.holdings[self.pair]) + (initial_buy_amount)) / (self.holdings[self.pair] + round_to_min_order_quantity_increment(initial_buy_amount/self.crypto_quote['ask_price'], self.crypto_meta_data['min_order_quantity_increment'])), self.crypto_meta_data['min_order_price_increment'])
            self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital
            self.percent_change = self.profit * 100 / self.cash
        
        # Place limit buy orders and limit sell orders
        for i in range(len(self.grids)):
            if self.grids[i]['side'] == 'buy' and self.grids[i]['status'] == 'active':
                if self.mode == 'live':
                    self.grids[i]['order'] = Order(rh.orders.order_buy_crypto_limit(self.pair, round_to_min_order_quantity_increment(self.cash_per_level/self.grids[i]['price'], self.crypto_meta_data['min_order_quantity_increment']), self.grids[i]['price'], timeInForce='gtc', jsonify=True))
                else:
                    print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[i]['price']))
                    self.grids[i]['order'] = None
            elif self.grids[i]['side'] == 'sell' and self.grids[i]['status'] == 'active':
                if self.mode == 'live':
                    err_count = 0
                    while err_count < self.init_buy_error_max_count:
                        try:
                            self.grids[i]['order'] = Order(rh.orders.order_sell_crypto_limit(self.pair, round_to_min_order_quantity_increment(self.cash_per_level/self.grids[i]['price'], self.crypto_meta_data['min_order_quantity_increment']), self.grids[i]['price'], timeInForce='gtc', jsonify=True))
                        except KeyError as ex:
                            err_count += 1
                            if err_count >= self.init_buy_error_max_count:
                                raise ex
                            else:
                                time.sleep(self.init_buy_error_latency)
                else:
                    print("Placing a limit sell order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[i]['price']))
                    self.grids[i]['order'] = None
            else:
                self.grids[i]['order'] = None
        
        print("Finished grid initalization")
    
    def update_orders(self):
        for i in range(len(self.grids)):
            # Update each order
            if self.grids[i]['status'] == 'active' and self.grids[i]['order'] is not None:
                self.grids[i]['order'].update()

                if self.grids[i]['order'] is not None and self.grids[i]['order'].is_filled():
                    if self.grids[i]['side'] == 'buy' and self.closest_grid == i+1:
                        # If the filled order was a buy order, place a sell order on the level above it, assuming it was previously inactive

                        # Set the filled level to inactive and adjust the inactive index
                        self.grids[i]['status'] = 'inactive'
                        self.closest_grid = i

                        # Place a sell order on grid line i+1
                        self.grids[i+1]['side'] = 'sell'
                        self.grids[i+1]['status'] = 'active'

                        self.grids[i+1]['order'] = Order(
                            rh.orders.order_sell_crypto_limit(
                                self.pair,
                                round_to_min_order_quantity_increment(self.cash_per_level/self.grids[i+1]['price'], self.crypto_meta_data['min_order_quantity_increment']),
                                self.grids[i+1]['price'],
                                timeInForce='gtc',
                                jsonify=True
                            )
                        )

                        print("Placing a limit sell order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[i+1]['price']))
                    elif self.grids[i]['side'] == 'sell' and self.closest_grid == i-1:
                        # If the filled order was a sell order, place a buy order on the level below it, assuming it was previously inactive

                        # Set the filled level to inactive and adjust the inactive index
                        self.grids[i]['status'] = 'inactive'
                        self.closest_grid = i

                        # Place a buy order on grid line i
                        self.grids[i-1]['side'] = 'buy'
                        self.grids[i-1]['status'] = 'active'

                        self.grids[i-1]['order'] = Order(
                            rh.orders.order_buy_crypto_limit(
                                self.pair,
                                round_to_min_order_quantity_increment(self.cash_per_level/self.grids[i-1]['price'], self.crypto_meta_data['min_order_quantity_increment']),
                                self.grids[i-1]['price'],
                                timeInForce='gtc',
                                jsonify=True
                            )
                        )

                        print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[i-1]['price']))
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
            }
        }
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
        holdings = {self.pair: 0}
        bought_price = {self.pair: 0}
        
        rh_holdings = self.build_holdings()

        try:
            holdings[self.pair] = float(rh_holdings[self.pair]['quantity'])
            
            bought_price[self.pair] = float(rh_holdings[self.pair]['average_buy_price'])
        except:
            holdings[self.pair] = 0
            bought_price[self.pair] = 0

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
            if self.grids[i]['order'] is not None and self.grids[i]['status'] == 'active':
                # Check to see if either as a buy or sell order that it has been filled
                if (self.grids[i]['side'] == 'buy' and self.crypto_quote['ask_price'] <= self.grids[i]['price']) or (self.grids[i]['side'] == 'sell' and self.crypto_quote['bid_price'] >= self.grids[i]['price']):
                    if self.grids[i]['side'] == 'buy' and self.closest_grid == i+1:
                        # If the filled order was a buy order, place a sell order on the level above it, assuming it was previously inactive

                        # Update available_cash, holdings, bought_price, profit, and percent_change to simulate the fulfillment of the limit buy order
                        self.available_cash -= self.cash_per_level
                        self.holdings[self.pair] += round_to_min_order_quantity_increment(self.cash_per_level/self.grids[i]['price'], self.crypto_meta_data['min_order_quantity_increment'])
                        self.bought_price[self.pair] = round_to_min_order_price_increment( ((self.bought_price[self.pair] * self.holdings[self.pair]) + (self.cash_per_level)) / (self.holdings[self.pair] + round_to_min_order_quantity_increment(self.cash_per_level/self.grids[i]['price'], self.crypto_meta_data['min_order_quantity_increment'])), self.crypto_meta_data['min_order_price_increment'])
                        self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital
                        self.percent_change = self.profit * 100 / self.cash

                        # Set the filled level to inactive and adjust the inactive index
                        self.grids[i]['status'] = 'inactive'
                        self.closest_grid = i

                        # Place a sell order on grid line i+1
                        self.grids[i+1]['side'] = 'sell'
                        self.grids[i+1]['status'] = 'active'
                        
                        if self.mode == 'live':
                            self.grids[i+1]['order'] = Order(rh.orders.order_sell_crypto_limit(self.pair, round_to_min_order_quantity_increment(self.cash_per_level/self.grids[i+1]['price'], self.crypto_meta_data['min_order_quantity_increment']), self.grids[i+1]['price'], timeInForce='gtc', jsonify=True))
                        else:
                            print("Placing a limit sell order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[i+1]['price']))
                            self.grids[i+1]['order'] = None
                    elif self.grids[i]['side'] == 'sell' and self.closest_grid == i-1:
                        # If the filled order was a sell order, place a buy order on the level below it, assuming it was previously inactive

                        # Update available_cash, holdings, profit, and percent_change to simulate the fulfillment of the limit sell order
                        self.available_cash += self.cash_per_level
                        self.holdings[self.pair] -= round_to_min_order_quantity_increment(self.cash_per_level/self.grids[i]['price'], self.crypto_meta_data['min_order_quantity_increment'])
                        self.profit = self.available_cash + self.get_crypto_holdings_capital() - self.initial_cash - self.initial_crypto_capital
                        self.percent_change = self.profit * 100 / self.cash

                        # Set the filled level to inactive and adjust the inactive index
                        self.grids[i]['status'] = 'inactive'
                        self.closest_grid = i

                        # Place a buy order on grid line i
                        self.grids[i-1]['side'] = 'buy'
                        self.grids[i-1]['status'] = 'active'

                        if self.mode == 'live':
                            self.grids[i-1]['order'] = Order(rh.orders.order_buy_crypto_limit(self.pair, round_to_min_order_quantity_increment(self.cash_per_level/self.grids[i-1]['price'], self.crypto_meta_data['min_order_quantity_increment']), self.grids[i-1]['price'], timeInForce='gtc', jsonify=True))
                        else:
                            print("Placing a limit buy order for $" + str(self.cash_per_level) + " at a price of $" + str(self.grids[i-1]['price']))
                            self.grids[i-1]['order'] = None
                    else:
                        # TODO: Implement
                        raise Exception("Order was filled but either was not sell nor buy or ignored level was not correct or both")
