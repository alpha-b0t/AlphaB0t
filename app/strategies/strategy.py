from app.strategies.grid import Grid
from app.strategies.ohlc import OHLC
from app.strategies.order import KrakenOrder
from app.exchanges.exchange import Exchange
from tensorflow.keras.models import load_model
from config import StrategyConfig # Needed for children of parent class Strategy
import inspect
import time
from constants import CLASS_NAMES
import pandas as pd
from app.strategies.LSTM.get_data import fetch_data
from app.strategies.LSTM.json_helper import export_json_to_csv
from app.strategies.LSTM.clean_data import remove_duplicates_and_sort
from sklearn.preprocessing import StandardScaler
from app.strategies.LSTM.train_model import calculate_rsi
import numpy as np

class Strategy():
    # TODO: Finish implementing (along with StrategyConfig in config.py)
    def __init__(self):
        self.classname = self.__class__.__name__
    
    def generate_signal(self):
        """Returns signal 'BUY', 'SELL', or 'HOLD'."""
        raise NotImplementedError
    
    def get_required_data(self) -> list:
        """Return required data types (OHLCV, indicators, etc.)"""
        raise NotImplementedError
        
    def update_indicators(self, new_data: dict):
        """Update internal indicators with new data"""
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

class LSTMStrategy(Strategy):
    def __init__(self, strategy_config: StrategyConfig={}, exchange: Exchange={}):
        super().__init__()
        self.classname = self.__class__.__name__
        if type(strategy_config) == dict:
            # Reloading
            print(f"Reloading {self.classname}...")
            return
        
        self.strategy_config = {}
        self.exchange = exchange
        self.model_uuid = strategy_config.lstm_model_uuid
        self.pair = strategy_config.pair

        # Load the trained model
        try:
            self.model = load_model(f'app/strategies/LSTM/models/model_{self.model_uuid}.h5')
        except FileNotFoundError:
            print(f"Error: Model file not found for UUID {self.model_uuid}")
            exit(1)
        
        # Load the model metrics
        self.model_metrics = self.get_model_metrics()
    
    def get_required_data(self):
        raise NotImplementedError

    def get_model_metrics(self) -> dict:
        path = f'app/strategies/LSTM/data/model_{self.model_uuid}_metrics.csv'
        try:
            df = pd.read_csv(path)
            if df.empty:
                raise ValueError(f"No metrics found for model {self.model_uuid}")
            return df.iloc[0].to_dict()
        except FileNotFoundError:
            raise FileNotFoundError(f"No metrics CSV found for model UUID: {self.model_uuid}")
    
    def get_prediction_data(self):
        # TODO: Improve [fetch_data -> export_data_to_json -> remove_duplicates_and_sort] pipeline by removing unnecessary files and optimizing for speed
        fetch_data(
            pair=self.pair,
            interval=int(self.model_metrics['interval']),
            since=self.get_lookback_unix(int(self.model_metrics['interval']) * 60 * 2),
            filename='prediction_data.json'
        )

        export_json_to_csv('prediction_data.json', 'prediction_data.csv')

        remove_duplicates_and_sort('prediction_data.csv')

        # Load in the prediction data
        # Assumes the dataset has columns 'UNIX time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'
        data = pd.read_csv('app/strategies/LSTM/data/prediction_data.csv')

        # Calculate volatility for each data point
        # Volatility = (high - low) / close (intrabar volatility)
        data['volatility'] = (data['high'] - data['low']) / data['close']

        # Calculate Moving Averages
        data['ma_short'] = data['close'].rolling(window=self.model_metrics['ma_short']).mean()
        data['ma_long'] = data['close'].rolling(window=self.model_metrics['ma_long']).mean()

        # Calculate Exponential Moving Averages
        data['ema_short'] = data['close'].ewm(span=self.model_metrics['ema_short'], adjust=False).mean()
        data['ema_long'] = data['close'].ewm(span=self.model_metrics['ema_long'], adjust=False).mean()

        # Calculate Relative Strength Index (RSI)
        data['rsi'] = calculate_rsi(data, self.model_metrics['rsi_period'])

        # Calculate MACD (Moving Average Convergence Divergence)
        ema_fast = data['close'].ewm(span=self.model_metrics['macd_fast'], adjust=False).mean()
        ema_slow = data['close'].ewm(span=self.model_metrics['macd_slow'], adjust=False).mean()
        data['macd'] = ema_fast - ema_slow
        data['macd_signal'] = data['macd'].ewm(span=self.model_metrics['macd_signal'], adjust=False).mean()
        data['macd_histogram'] = data['macd'] - data['macd_signal']

        # Fill NaN values created by rolling/ewm calculations
        data = data.bfill()

        # Save the processed data before scaling for future reference (only used for verification and debugging)
        data.to_csv(f'app/strategies/LSTM/data/model_{self.model_uuid}_prediction_data.csv', index=False)
        print(f"Prediction data saved: app/strategies/LSTM/data/model_{self.model_uuid}_prediction_data.csv")

        prediction_data = pd.read_csv(f'app/strategies/LSTM/data/model_{self.model_uuid}_prediction_data.csv')
        prediction_data = data # FIX ME

        # Feature scaling
        sc = StandardScaler()
        scaled_prediction_data = sc.fit_transform(prediction_data)

        # Prepare the sequences
        X_prediction = []
        for i in range(len(scaled_prediction_data) - int(self.model_metrics['sequence_length'])):
            X_prediction.append(scaled_prediction_data[i:i+int(self.model_metrics['sequence_length'])])

        X_prediction = np.array(X_prediction)

        return X_prediction, prediction_data
    
    def get_price_prediction(self):
        X_prediction, prediction_data = self.get_prediction_data()

        predictions = self.model.predict(X_prediction)

        # Reshape the predictions to match scaler's inverse_transform input shape
        predictions_reshaped = predictions.reshape(-1, 1)

        # Use the appropiate scaler for inverse transform
        scaler_close = StandardScaler()
        scaler_close.fit(prediction_data[['close']])

        # Inverse transform the scaled predictions to get actual prices
        predictions_actual = scaler_close.inverse_transform(predictions_reshaped)
        print(f"Price Predictions: {predictions_actual}")
        return predictions_actual
    
    def get_lookback_unix(self, buffer_in_seconds: int = 5) -> int:
        # Interval is in minutes
        lookback_seconds = int(self.model_metrics['interval']) * int(self.model_metrics['sequence_length']) * 60 + buffer_in_seconds
        return int(time.time() - lookback_seconds)
    
    def generate_signal(self) -> str:
        price_predictions = self.get_price_prediction()
        latest_ohlc = self.get_latest_ohlc()
        
        # TODO: Edit buffer
        buffer = 0.02 # 2%
        
        print(f"Predicted change: {round(price_predictions[-1][0] - latest_ohlc.close, 2)}, ({round((price_predictions[-1][0] - latest_ohlc.close) * 100 / latest_ohlc.close, 2)}%)")
        if price_predictions[-1][0] > latest_ohlc.close * (1 + buffer):
            return 'BUY'
        elif price_predictions[-1][0] < latest_ohlc.close * (1 - buffer):
            return 'SELL'
        else:
            return 'HOLD'
    
    def get_latest_ohlc(self):
        """Get latest OHLC data."""
        # TODO: Add changeable number of attempts and error latency
        for attempt in range(5):
            try:
                ohlc_response = self.exchange.get_ohlc_data(self.pair)
                break
            except Exception as e:
                print(f"Error making API request (attempt {attempt + 1}/{5}): {e}")

                if attempt == 5 - 1:
                    print(f"Failed to make API request after {5} attempts")
                    raise e
                else:
                    time.sleep(5)
        
        ohlc = ohlc_response.get('result')

        for key in ohlc.keys():
            if key != 'last':
                self.ohlc_asset_key = key
                break
        
        return OHLC(ohlc[self.ohlc_asset_key][-1])