from app.models.exchange import Exchange, KrakenExchange, CoinbaseExchange, RobinhoodCryptoExchange
from app.models.grid import Grid
from app.models.ohlc import OHLC
from app.models.order import KrakenOrder
from app.helpers.format import round_down_to_cents
from config import AppConfig, GRIDBotConfig, ExchangeConfig
import time
from datetime import datetime

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
    def __init__(self, gridbot_config: GRIDBotConfig, exchange_config: ExchangeConfig):
        self.exchange = KrakenExchange(exchange_config)

        self.name = gridbot_config.name
        self.pair = gridbot_config.pair
        self.days_to_run = gridbot_config.days_to_run
        self.mode = gridbot_config.mode
        self.upper_price = gridbot_config.upper_price
        self.lower_price = gridbot_config.lower_price
        self.level_num = gridbot_config.level_num
        self.quantity_per_grid = gridbot_config.quantity_per_grid
        self.total_investment = gridbot_config.total_investment
        self.stop_loss = gridbot_config.stop_loss
        self.take_profit = gridbot_config.take_profit
        self.base_currency = gridbot_config.base_currency
        self.latency = gridbot_config.latency_in_sec
        self.max_error_count = gridbot_config.max_error_count
        self.error_latency = gridbot_config.error_latency_in_sec
        self.init_but_error_latency = gridbot_config.init_buy_error_latency_in_sec
        self.init_buy_error_max_count = gridbot_config.init_buy_error_max_count
        self.cancel_orders_upon_exit = gridbot_config.cancel_orders_upon_exit

        # Initialize the timer
        self.start_time = time.time()

        # Perform validation on the configuration
        self.check_config()

        # Fetch information related to the pair
        for attempt in range(self.max_error_count):
            try:
                asset_info_response = self.exchange.get_tradable_asset_pairs(self.pair)
                break
            except Exception as e:
                print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")
                
                if attempt == self.max_error_count - 1:
                    print(f"Failed to make API request after {self.max_error_count} attempts")
                    raise e
                else:
                    time.sleep(self.error_latency)
        
        asset_info = asset_info_response.get('result')

        for key in asset_info.keys():
            pair_key = key
        
        pair_info = asset_info[pair_key]

        # Price precision
        self.pair_decimals = pair_info['pair_decimals']

        # Volume precision in base currency
        self.lot_decimals = pair_info['lot_decimals']

        self.cost_decimals = pair_info['cost_decimals']
        self.ordermin = float(pair_info['ordermin'])
        self.costmin = float(pair_info['costmin'])
        self.tick_size = pair_info['tick_size']
        self.pair_status = pair_info['status']

        # Check if either self.quantity_per_grid or self.total_investment is being used to determine total investment, quantity per grid
        if self.quantity_per_grid == 0:
            # Use self.total_investment to determine total investment, quantity per level
            self.quantity_per_grid = self.calculate_max_quantity_per_grid(self.total_investment)

            print(f"quantity per grid: {self.quantity_per_grid}")
        else:
            # Use self.quantity_per_grid to determine total investment, quantity per level
            self.total_investment = self.calculate_total_investment(self.quantity_per_grid)

            print(f"total investment: {self.total_investment}")
        
        if self.exchange.api_key != '' and self.exchange.api_sec != '':
            assert self.quantity_per_grid >= self.ordermin
            assert round(self.quantity_per_grid * self.lower_price, self.pair_decimals) >= self.costmin

            # Fetch fee schedule and trade volume info
            for attempt in range(self.max_error_count):
                try:
                    trade_volume_fee_response = self.exchange.get_trade_volume(self.pair)
                    break
                except Exception as e:
                    print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")
                    
                    if attempt == self.max_error_count - 1:
                        print(f"Failed to make API request after {self.max_error_count} attempts")
                        raise e
                    else:
                        time.sleep(self.error_latency)
            
            fee_info = trade_volume_fee_response.get('result')
            self.trade_volume = fee_info['volume']

            for key in fee_info['fees'].keys():
                pair_key = key
            
            if fee_info.get('fees_maker') is None:
                self.fee_taker = self.fee_maker = float(fee_info['fees'][pair_key]['fee'])
            else:
                self.fee_taker = float(fee_info['fees'][pair_key]['fee'])
                self.fee_maker = float(fee_info['fees_maker'][pair_key]['fee'])

        # TODO: Implement
        self.closed_orders = []
        self.profit = 0
        self.gain_percent = 0
        self.fee = 0

        # Fetch balances
        if self.exchange.api_key != '' and self.exchange.api_sec != '':
            self.fetch_balances()

        if self.mode != 'test':
            if self.total_investment > self.account_trade_balances[self.base_currency]:
                raise Exception(f"Your total investment, {self.total_investment} {self.base_currency}, is greater than your balance of {self.base_currency} availabe for trading, {self.account_trade_balances[self.base_currency]}.")
    
    def __repr__(self):
        if self.name == '':
            name_display = "''"
        else:
            name_display = self.name
        
        return f"{{KrakenGRIDBot name: {name_display}, pair: {self.pair}, mode: {self.mode}, runtime: {self.get_runtime()}s, profit: {self.profit} {self.base_currency}, gain_percent: {self.gain_percent}%, fee: {self.fee} {self.base_currency}, total_investment: {self.total_investment} {self.base_currency}}}"
    
    def get_runtime(self):
        return time.time() - self.start_time

    def check_exchange_api_permissions(self):
        # TODO: Implement
        pass
    
    def check_config(self):
        """Throws an error if the configurations are not correct."""
        # TODO: Implement
        assert self.mode in ['live', 'test']
        assert self.stop_loss > 0
        assert self.take_profit > 0
        assert self.take_profit > self.stop_loss
        assert self.days_to_run > 0

        if self.quantity_per_grid > 0:
            # Use self.quantity_per_grid to determine total investment, quantity per level
            assert self.total_investment == 0
        else:
            # Use self.total_investment to determine total investment, quantity per level
            assert self.quantity_per_grid == 0
            assert self.total_investment > 0
        
        assert self.latency > 0
        assert self.take_profit > self.upper_price
        assert self.upper_price > self.lower_price
        assert self.lower_price > self.stop_loss
        assert self.max_error_count >= 1
        assert self.level_num > 1
        assert self.error_latency > 0
    
    def init_grid(self):
        """Initializes grids."""
        self.grids = []

        # Determine what the prices are at each level
        prices = []
        for i in range(self.level_num):
            prices += [round(self.lower_price + i*(self.upper_price - self.lower_price)/(self.level_num-1), self.pair_decimals)]
        
        # Get latest OHLC data
        for attempt in range(self.max_error_count):
            try:
                ohlc_response = self.exchange.get_ohlc_data(self.pair)
                break
            except Exception as e:
                print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                if attempt == self.max_error_count - 1:
                    print(f"Failed to make API request after {self.max_error_count} attempts")
                    raise e
                else:
                    time.sleep(self.error_latency)
        
        ohlc = ohlc_response.get('result')

        for key in ohlc.keys():
            if key != 'last':
                self.ohlc_asset_key = key
                break
        
        self.latest_ohlc = OHLC(ohlc[self.ohlc_asset_key][-1])

        # Mark orders as buys and sells
        side = []
        for i in range(self.level_num):
            if self.latest_ohlc.close > prices[i]:
                side += ['buy']
            else:
                side += ['sell']
        
        # Determine which grid line is closest to the current price
        min_dist = float('inf')
        self.closest_grid = -1

        for i in range(self.level_num):
            dist = abs(prices[i] - self.latest_ohlc.close)

            if dist < min_dist:
                min_dist = dist
                self.closest_grid = i
        
        # Mark the closest grid line as inactive
        status = ['active' for i in range(self.level_num)]
        status[self.closest_grid] = 'inactive'

        for i in range(self.level_num):
            self.grids += [Grid(i, prices[i], round(self.quantity_per_grid, self.lot_decimals), side[i], status[i])]
        
        # Determine initial quantity to buy initial amount of cryptocurrency
        grid_level_initial_buy_count = 0
        for i in range(len(self.grids)):
            if self.grids[i].side == 'sell' and self.grids[i].status == 'active':
                grid_level_initial_buy_count += 1
        
        if grid_level_initial_buy_count > 0:
            initial_buy_amount = round(grid_level_initial_buy_count * self.quantity_per_grid, self.lot_decimals)

            # Place a buy order for the initial amount to sell
            print(f"Adding a buy order for {initial_buy_amount} {self.pair} @ limit {self.latest_ohlc.close}")

            for attempt in range(self.max_error_count):
                try:
                    initial_buy_order_response = self.exchange.add_order(
                        ordertype='limit',
                        type='buy',
                        volume=initial_buy_amount,
                        pair=self.pair,
                        price=self.latest_ohlc.close,
                        oflags='post'
                    )
                    break
                except Exception as e:
                    print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                    if attempt == self.max_error_count - 1:
                        print(f"Failed to make API request after {self.max_error_count} attempts")
                        raise e
                    else:
                        time.sleep(self.error_latency)
            
            # Fetch order info
            for attempt in range(self.max_error_count):
                try:
                    # The appropiate Kraken API endpoint might be get_trades_info() instead of get_orders_info()
                    initial_buy_order_update_response = self.exchange.get_orders_info(initial_buy_order_response['result']['txid'][0], trades=True)
                    break
                except Exception as e:
                    print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                    if attempt == self.max_error_count - 1:
                        print(f"Failed to make API request after {self.max_error_count} attempts")
                        raise e
                    else:
                        time.sleep(self.error_latency)
            
            # Wait until the initial limit buy order has been fulfilled if it hasn't been already
            while initial_buy_order_update_response['result'][initial_buy_order_response['result']['txid'][0]]['status'] != "closed":
                # Wait a certain amount of time for the order to fill
                print(f"Waiting for initial buy order for {initial_buy_amount} {self.pair} @ limit {self.latest_ohlc.close} to be fulfilled...")
                time.sleep(self.latency)
                
                # Fetch new order info
                for attempt in range(self.max_error_count):
                    try:
                        # The appropiate Kraken API endpoint might be get_trades_info() instead of get_orders_info()
                        initial_buy_order_update_response = self.exchange.get_orders_info(initial_buy_order_response['result']['txid'][0], trades=True)
                        break
                    except Exception as e:
                        print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                        if attempt == self.max_error_count - 1:
                            print(f"Failed to make API request after {self.max_error_count} attempts")
                            raise e
                        else:
                            time.sleep(self.error_latency)
            
            # Initial limit buy order has been fulfilled
            self.closed_orders += [KrakenOrder(initial_buy_order_update_response['result']['txid'][0], initial_buy_order_response['result'])]

        # Place limit buy orders and limit sell orders
        for i in range(len(self.grids)):
            if self.grids[i].status == 'active':
                if self.grids[i].side == 'buy':
                    side = 'buy'
                elif self.grids[i].side == 'sell':
                    side = 'sell'
                
                print(f"Adding a {side} order for {self.grids[i].quantity} {self.pair} @ limit {self.grids[i].limit_price}")

                for attempt in range(self.max_error_count):
                    try:
                        order_response = self.exchange.add_order(
                            ordertype='limit',
                            type=side,
                            volume=self.grids[i].quantity,
                            pair=self.pair,
                            price=self.grids[i].limit_price,
                            oflags='post'
                        )
                        break
                    except Exception as e:
                        print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                        if attempt == self.max_error_count - 1:
                            print(f"Failed to make API request after {self.max_error_count} attempts")
                            raise e
                        else:
                            time.sleep(self.error_latency)

                txid = order_response['result'].get('txid', [])
                if txid == []:
                    txid = ''
                else:
                    txid = txid[0]
                
                self.grids[i].order = KrakenOrder(txid, order_response.get('result'))
            else:
                self.grids[i].order = KrakenOrder()
    
    def get_account_asset_balance(self, pair: str = 'ZUSD') -> float:
        """Retrieves the cash balance of the asset (i.e. pair or currency), net of pending withdrawals."""
        for attempt in range(self.max_error_count):
            try:
                account_balances_response = self.exchange.get_account_balance()

                account_balances = account_balances_response.get('result')

                return float(account_balances.get(pair, 0))
            except Exception as e:
                print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                if attempt == self.max_error_count - 1:
                    print(f"Failed to make API request after {self.max_error_count} attempts")
                    raise e
                else:
                    time.sleep(self.error_latency)
    
    def get_available_trade_balance(self) -> dict:
        """Retrieves the balance(s) available for trading."""
        for attempt in range(self.max_error_count):
            try:
                extended_balances_response = self.exchange.get_extended_balance()

                extended_balance = extended_balances_response.get('result')

                available_balances = {}

                for asset in extended_balance.keys():
                    available_balances[asset] = float(extended_balance[asset]['balance']) + float(extended_balance[asset].get('credit', 0)) - float(extended_balance[asset].get('credit_used', 0)) - float(extended_balance[asset]['hold_trade'])
                
                return available_balances
            except Exception as e:
                print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")
                
                if attempt == self.max_error_count - 1:
                    print(f"Failed to make API request after {self.max_error_count} attempts")
                    raise e
                else:
                    time.sleep(self.error_latency)
    
    def fetch_balances(self):
        """Fetches latest account balances and account balances available for trading."""
        for attempt in range(self.max_error_count):
            try:
                account_balances_response = self.exchange.get_account_balance()
                break
            except Exception as e:
                print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")
                
                if attempt == self.max_error_count - 1:
                    print(f"Failed to make API request after {self.max_error_count} attempts")
                    raise e
                else:
                    time.sleep(self.error_latency)
        
        self.account_balances = account_balances_response.get('result')

        for asset in self.account_balances.keys():
            self.account_balances[asset] = float(self.account_balances[asset])
        
        self.account_trade_balances = self.get_available_trade_balance()
    
    def fetch_latest_ohlc(self):
        """Fetches latest OHLC data. self.init_grid() must be called before this function is to be called."""
        for attempt in range(self.max_error_count):
            try:
                ohlc_response = self.exchange.get_ohlc_data(self.pair)
                break
            except Exception as e:
                print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                if attempt == self.max_error_count - 1:
                    print(f"Failed to make API request after {self.max_error_count} attempts")
                    raise e
                else:
                    time.sleep(self.error_latency)
        
        ohlc = ohlc_response.get('result')
        self.latest_ohlc = OHLC(ohlc[self.ohlc_asset_key][-1])
    
    def calculate_profit(self):
        # Updates self.profit, self.gain_percent, and self.fee
        # Note that self.profit is realized profit, not unrealized profit
        profit = 0
        fee = 0

        try:
            for i in range(len(self.closed_orders)):
                if self.closed_orders[i].descr['type'] == 'buy':
                    profit -= float(self.closed_orders[i].vol_exec) * float(self.closed_orders[i].price)
                    profit -= float(self.closed_orders[i].fee)

                else:
                    profit += float(self.closed_orders[i].vol_exec) * float(self.closed_orders[i].price)
                    profit -= float(self.closed_orders[i].fee)
                
                fee += float(self.closed_orders[i].fee)
            
            self.profit = profit
            self.fee = fee
            self.gain_percent = profit * 100 / self.total_investment
        except Exception as e:
            print(f"Error updating profit: {e}")
            print(f"Closed orders: {self.closed_orders}")
    
    def calculate_max_quantity_per_grid(self, total_investment: float) -> float:
        prices = []
        for i in range(self.level_num - 1):
            prices += [round(self.lower_price + i*(self.upper_price - self.lower_price)/(self.level_num-1), self.pair_decimals)]
        
        average_price = sum(prices) / len(prices)

        return (total_investment / len(prices)) / average_price
    
    def calculate_total_investment(self, quantity_per_grid: float) -> float:
        total_investment = 0
        
        for i in range(self.level_num - 1):
            price = round(self.lower_price + i*(self.upper_price - self.lower_price)/(self.level_num-1), self.pair_decimals)
            
            total_investment += quantity_per_grid * price
        
        return total_investment
    
    def start(self):
        try:
            print("\n\nInitializing grid...")
            self.init_grid()

            print("Finished grid initialization.")
            print("\n\nGrids:")
            for i in range(len(self.grids)):
                print(self.grids[i])
            
            # Fetch balances
            print("\n\nFetching balances...")
            self.fetch_balances()

            print(f"Account balances: {self.account_balances}")
            print(f"Account Trade Balances: {self.account_trade_balances}")
            print("Finished fetching balances.")

            print(f"\n\nOHLC: {self.latest_ohlc}")

            while self.latest_ohlc.close > self.stop_loss and self.latest_ohlc.close < self.take_profit:
                print("\n\nUpdating orders...")
                self.update_orders()
                
                print("Finished updating orders.")

                print("\n\nGrids:")
                for i in range(len(self.grids)):
                    print(self.grids[i])
                
                # Fetch balances
                print("\n\nFetching balances...")
                self.fetch_balances()

                print(f"Account balances: {self.account_balances}")
                print(f"Account Trade Balances: {self.account_trade_balances}")
                print("Finished fetching balances.")

                # TODO: Update the output

                # Wait for a certain amount of time
                print(f"\n\nSleeping for {self.latency} seconds...")
                print("=========================================")
                time.sleep(self.latency)
                print("Time:", datetime.now())
                self.calculate_profit()
                print(self)

                # Get latest OHLC data
                print("\n\nFetching OHLC data...")

                self.fetch_latest_ohlc()

                print(f"\n\nOHLC: {self.latest_ohlc}")
            
        except KeyboardInterrupt as e:
            print("User ended execution of program.")
        
        except Exception as e:
            print(f"KrakenGRIDBot: {self}")
            print(f"Grids: {self.grids}")
            raise e
    
    def update_orders(self):
        # Fetch order info for each txid
        txid = ''
        for i in range(len(self.grids)):
            if self.grids[i].order.txid != '':
                txid += self.grids[i].order.txid + ','
        
        if txid != '':
            # Remove last comma in txid
            txid = txid[:-1]

            for attempt in range(self.max_error_count):
                try:
                    # The appropiate Kraken API endpoint might be get_trades_info() instead of get_orders_info()
                    orders_response = self.exchange.get_orders_info(txid, trades=True)
                    break
                except Exception as e:
                    print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                    if attempt == self.max_error_count - 1:
                        print(f"Failed to make API request after {self.max_error_count} attempts")
                        raise e
                    else:
                        time.sleep(self.error_latency)

            orders = orders_response.get('result')

            # Update each order
            for i in range(len(self.grids)):
                if self.grids[i].order.txid != '':
                    self.grids[i].order.update(orders.get(self.grids[i].order.txid, {}))
        
        for i in range(len(self.grids)):
            if self.grids[i].status == 'active' and self.grids[i].order.txid != '':
                if self.grids[i].order.status == 'closed':
                    print(f"Order filled: {self.grids[i].order}")

                    if self.grids[i].side == 'buy':
                        # Add filled order to list of closed orders
                        self.closed_orders += [self.grids[i].order]
                        
                        # The filled order was a buy order, place a sell order on the level above it

                        # Set the filled level to inactive and adjust the closest grid
                        self.grids[i].status = 'inactive'
                        self.closest_grid = i

                        # Place a sell order on the grid line above it if it is not the highest level
                        if i < len(self.grids) - 1:
                            if self.grids[i+1].status != 'inactive':
                                raise Exception('Unable to replace an open order with a new order.')
                            
                            self.grids[i+1].side = 'sell'
                            self.grids[i+1].status = 'active'

                            print(f"Adding a sell order for {self.grids[i+1].quantity} {self.pair} @ limit {self.grids[i+1].limit_price}")

                            # TODO: Add all order in once batch using self.exchange.add_order_batch to reduce API calls

                            for attempt in range(self.max_error_count):
                                try:
                                    add_order_response = self.exchange.add_order(
                                        ordertype='limit',
                                        type='sell',
                                        volume=self.grids[i+1].quantity,
                                        pair=self.pair,
                                        price=self.grids[i+1].limit_price,
                                        oflags='post'
                                    )
                                    break
                                except Exception as e:
                                    print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                                    if attempt == self.max_error_count - 1:
                                        print(f"Failed to make API request after {self.max_error_count} attempts")
                                        raise e
                                    else:
                                        time.sleep(self.error_latency)

                            txid = add_order_response['result'].get('txid', [])
                            if txid == []:
                                txid = ''
                            else:
                                txid = txid[0]
                            
                            self.grids[i+1].order = KrakenOrder(txid, add_order_response.get('result', {}))
                            
                            # Fetch order info for the newly added order using txid
                            for attempt in range(self.max_error_count):
                                try:
                                    # The appropiate Kraken API endpoint might be get_trades_info() instead of get_orders_info()
                                    order_response = self.exchange.get_orders_info(txid, trades=True)
                                    break
                                except Exception as e:
                                    print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                                    if attempt == self.max_error_count - 1:
                                        print(f"Failed to make API request after {self.max_error_count} attempts")
                                        raise e
                                    else:
                                        time.sleep(self.error_latency)
                            
                            order = order_response.get('result')

                            # Update the order info on record
                            self.grids[i+1].order.update(order.get(txid, {}))
                    else:
                        # Add filled order to list of closed orders
                        self.closed_orders += [self.grids[i].order]
                        
                        # The filled order was a sell order, place a buy order on the level below it

                        # Set the filled level to inactive and adjust the closest grid
                        self.grids[i].status = 'inactive'
                        self.closest_grid = i

                        # Place a buy order on the grid line below it if it is not the lowest level
                        if i > 0:
                            if self.grids[i-1].status != 'inactive':
                                raise Exception('Unable to replace an open order with a new order.')
                            
                            self.grids[i-1].side = 'buy'
                            self.grids[i-1].status = 'active'

                            print(f"Adding a buy order for {self.grids[i-1].quantity} {self.pair} @ limit {self.grids[i-1].limit_price}")
                            
                            # TODO: Add all order in once batch using self.exchange.add_order_batch to reduce API calls

                            for attempt in range(self.max_error_count):
                                try:
                                    add_order_response = self.exchange.add_order(
                                        ordertype='limit',
                                        type='buy',
                                        volume=self.grids[i-1].quantity,
                                        pair=self.pair,
                                        price=self.grids[i-1].limit_price,
                                        oflags='post'
                                    )
                                    break
                                except Exception as e:
                                    print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                                    if attempt == self.max_error_count - 1:
                                        print(f"Failed to make API request after {self.max_error_count} attempts")
                                        raise e
                                    else:
                                        time.sleep(self.error_latency)

                            txid = add_order_response['result'].get('txid', [])
                            if txid == []:
                                txid = ''
                            else:
                                txid = txid[0]
                            
                            self.grids[i-1].order = KrakenOrder(txid, add_order_response.get('result', {}))

                            # Fetch order info for the newly added order using txid
                            for attempt in range(self.max_error_count):
                                try:
                                    # The appropiate Kraken API endpoint might be get_trades_info() instead of get_orders_info()
                                    order_response = self.exchange.get_orders_info(txid, trades=True)
                                    break
                                except Exception as e:
                                    print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                                    if attempt == self.max_error_count - 1:
                                        print(f"Failed to make API request after {self.max_error_count} attempts")
                                        raise e
                                    else:
                                        time.sleep(self.error_latency)
                            
                            order = order_response.get('result')

                            # Update the order info on record
                            self.grids[i-1].order.update(order.get(txid, {}))
    
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
