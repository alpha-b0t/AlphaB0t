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

    def prepare_for_restart(self) -> None:
        """Override to reload non-serialized state (e.g. Keras model). No-op by default."""
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
        self.risk_to_reward_ratio = strategy_config.risk_to_reward_ratio

        # Load the trained model
        self.load_model()
        
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

    def prepare_for_restart(self) -> None:
        """Reload LSTM model and metrics after loading bot from JSON (model is not serialized)."""
        if getattr(self, "model", None) is not None:
            return
        
        # Load the trained model
        self.load_model()
        
        self.model_metrics = self.get_model_metrics()
    
    def load_model(self):
        # Load the trained model
        try:
            self.model = load_model(f'app/strategies/LSTM/models/model_{self.model_uuid}.h5')
        except FileNotFoundError:
            raise FileNotFoundError(f"Error: Model file not found for UUID {self.model_uuid}")
    
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
        buffer = 0.0005 # 0.05%
        
        print(f"Predicted change: {round(price_predictions[-1][0] - latest_ohlc.close, 2)}, ({'+' if price_predictions[-1][0] > latest_ohlc.close else ''}{round((price_predictions[-1][0] - latest_ohlc.close) * 100 / latest_ohlc.close, 2)}%)")
        if price_predictions[-1][0] >= latest_ohlc.close * (1 + buffer):
            return 'BUY'
        elif price_predictions[-1][0] <= latest_ohlc.close * (1 - buffer):
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