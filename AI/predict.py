import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import load_model
from constants import SEQUENCE_LENGTH

# Load in the prediction data
# Assumes the dataset has columns 'UNIX time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'
prediction_data = pd.read_csv('AI/data/crypto_prediction_data.csv')

scaler = StandardScaler()
scaled_prediction_data = scaler.fit_transform(prediction_data)

# Prepare the sequences
X_prediction = []
for i in range(len(scaled_prediction_data) - SEQUENCE_LENGTH):
    X_prediction.append(scaled_prediction_data[i:i+SEQUENCE_LENGTH])

X_prediction = np.array(X_prediction)

# Load the trained model
model = load_model('AI/models/crypto_price_model.h5')

# Predict using the model
predictions = model.predict(X_prediction)

# Reshape the predictions to match scaler's inverse_transform input shape
predictions_reshaped = predictions.reshape(-1, 1)

# Use the appropiate scaler for inverse transform
scaler_close = StandardScaler()
scaler_close.fit(prediction_data[['close']])

# Inverse transform the scaled predictions to get actual prices
predictions_actual = scaler_close.inverse_transform(predictions_reshaped)

# Now, predictions_actual contains the predicted close prices for the new data
print(predictions_actual)
