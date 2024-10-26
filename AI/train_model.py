import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, LSTM, Dropout
from model_constants import EPOCHS, BATCH_SIZE, SEQUENCE_LENGTH

# Load in the training data
# Assumes the dataset has columns 'UNIX time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'
data = pd.read_csv('AI/data/crypto_training_data.csv')

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

# Compare predictions with actual prices
# (You can use any suitable evaluation metric based on your requirement)

# Save the trained model
model.save('AI/models/crypto_price_model.h5')
print('Model saved successfully.')
