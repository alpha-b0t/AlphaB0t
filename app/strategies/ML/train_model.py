import numpy as np
import pandas as pd
import tensorflow as tf
import uuid
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, LSTM, Dropout
from model_constants import EPOCHS, BATCH_SIZE, SEQUENCE_LENGTH, MA_SHORT, MA_LONG, EMA_SHORT, EMA_LONG, RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL

# Load in the training data
# Assumes the dataset has columns 'UNIX time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'
data = pd.read_csv('app/strategies/ML/data/crypto_training_data.csv')

# Generate a unique UUID for this model
model_uuid = str(uuid.uuid4())
print(f"Generated Model UUID: {model_uuid}")

# Calculate volatility for each data point
# Volatility = (high - low) / close (intrabar volatility)
data['volatility'] = (data['high'] - data['low']) / data['close']

# Calculate Moving Averages
data['ma_short'] = data['close'].rolling(window=MA_SHORT).mean()
data['ma_long'] = data['close'].rolling(window=MA_LONG).mean()

# Calculate Exponential Moving Averages
data['ema_short'] = data['close'].ewm(span=EMA_SHORT, adjust=False).mean()
data['ema_long'] = data['close'].ewm(span=EMA_LONG, adjust=False).mean()

# Calculate Relative Strength Index (RSI)
def calculate_rsi(data, period=RSI_PERIOD):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

data['rsi'] = calculate_rsi(data, RSI_PERIOD)

# Calculate MACD (Moving Average Convergence Divergence)
ema_fast = data['close'].ewm(span=MACD_FAST, adjust=False).mean()
ema_slow = data['close'].ewm(span=MACD_SLOW, adjust=False).mean()
data['macd'] = ema_fast - ema_slow
data['macd_signal'] = data['macd'].ewm(span=MACD_SIGNAL, adjust=False).mean()
data['macd_histogram'] = data['macd'] - data['macd_signal']

# Fill NaN values created by rolling/ewm calculations
data = data.fillna(method='bfill')

# Save the processed data before scaling for future reference
data.to_csv(f'app/strategies/ML/data/model_{model_uuid}_training_data.csv', index=False)
print(f"Training data saved: app/strategies/ML/data/model_{model_uuid}_training_data.csv")

# Feature scaling
sc = StandardScaler()
data_scaled = sc.fit_transform(data)

# Prepare the data
X, y = [], []
for i in range(len(data_scaled) - SEQUENCE_LENGTH):
    # Assuming 'close' is the target variable
    X.append(data_scaled[i:i+SEQUENCE_LENGTH])
    y.append(data_scaled[i+SEQUENCE_LENGTH, 4])

X, y = np.array(X), np.array(y)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Build the LSTM model
model = Sequential([
    LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])),
    Dropout(0.2),
    LSTM(units=50, return_sequences=True),
    Dropout(0.2),
    LSTM(units=50),
    Dropout(0.2),
    Dense(units=1)
])

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model
model.fit(X_train, y_train, epocs=EPOCHS, batch_size=BATCH_SIZE)

# Evaluate the model
loss = model.evaluate(X_test, y_test)
print(f'Test loss: {loss}')

# Make predictions
predictions = model.predict(X_test)

# Reshape predictions to match scaler's inverse_transform input_shape
predictions_reshaped = predictions.reshape(-1, 1)

# Use the appropiate scaler for inverse transform
scaler_close = StandardScaler()
scaler_close.fit(data[['close']])

# Inverse transform the scaled predictions to get actual prices
predictions_actual = scaler_close.inverse_transform(predictions_reshaped)

print(predictions_actual)

# Calculate evaluation metrics
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

mae = mean_absolute_error(y_test, predictions.flatten())
rmse = np.sqrt(mean_squared_error(y_test, predictions.flatten()))
r2 = r2_score(y_test, predictions.flatten())

# Save training statistics to CSV
metrics_data = {
    'model_uuid': [model_uuid],
    'timestamp': [datetime.now().isoformat()],
    'test_loss': [float(loss)],
    'mae': [float(mae)],
    'rmse': [float(rmse)],
    'r2_score': [float(r2)],
    'epochs': [EPOCHS],
    'batch_size': [BATCH_SIZE],
    'sequence_length': [SEQUENCE_LENGTH],
    'ma_short': [MA_SHORT],
    'ma_long': [MA_LONG],
    'ema_short': [EMA_SHORT],
    'ema_long': [EMA_LONG],
    'rsi_period': [RSI_PERIOD],
    'macd_fast': [MACD_FAST],
    'macd_slow': [MACD_SLOW],
    'macd_signal': [MACD_SIGNAL],
    'training_samples': [len(X_train)],
    'testing_samples': [len(X_test)],
}

metrics_df = pd.DataFrame(metrics_data)
metrics_df.to_csv(f'app/strategies/ML/data/model_{model_uuid}_metrics.csv', index=False)
print(f"Metrics saved: app/strategies/ML/data/model_{model_uuid}_metrics.csv")

# Save the trained model
model.save(f'app/strategies/ML/models/crypto_price_model_{model_uuid}.h5')
print(f'Model saved: app/strategies/ML/models/crypto_price_model_{model_uuid}.h5')
