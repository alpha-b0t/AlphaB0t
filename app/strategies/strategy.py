from app.strategies.grid import Grid
from app.strategies.ohlc import OHLC
from app.strategies.order import KrakenOrder
from config import StrategyConfig # Needed for children of parent class Strategy
import inspect
import time
from constants import CLASS_NAMES

class Strategy():
    # TODO: Finish implementing (along with StrategyConfig in config.py)
    def __init__(self):
        self.classname = self.__class__.__name__
    
    def calculate_position_size(self, balance: float, price: float) -> float:
        """Calculate how much to buy/sell"""
        raise NotImplementedError
    
    def get_required_data(self) -> list:
        """Return required data types (OHLCV, indicators, etc.)"""
        raise NotImplementedError
        
    def update_indicators(self, new_data: dict):
        """Update internal indicators with new data"""
        raise NotImplementedError
        
    def get_parameters(self) -> dict:
        """Return current strategy parameters"""
        raise NotImplementedError
    
    @classmethod
    def from_json(cls, json_data):
        # Get the parameters of the __init__ method
        init_params = inspect.signature(cls.__init__).parameters

        # Extract known attributes
        known_attributes = {param for param in init_params if param != 'self'}
        known_data = {k: v for k, v in json_data.items() if k in known_attributes}

        # Extract additional attributes
        additional_data = {k: v for k, v in json_data.items() if k not in known_attributes}

        # Create instance with known attributes
        instance = cls(**known_data)

        # Set additional attributes
        for key, value in additional_data.items():
            if isinstance(value, dict) and 'classname' in value and value['classname'] in CLASS_NAMES:
                exec(f'setattr(instance, key, {value["classname"]}.from_json(value))')
            else:
                setattr(instance, key, value)
        
        return instance

class GridStrategy(Strategy):
    def __init__(self, strategy_config: StrategyConfig={}):
        super().__init__()
        self.classname = self.__class__.__name__
        if type(strategy_config) == dict:
            # Reloading
            print(f"Reloading {self.classname}...")
            return
        
        self.strategy_config = {}
    
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