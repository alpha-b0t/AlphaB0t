import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import load_model
from model_constants import SEQUENCE_LENGTH

if __name__ == '__main__':
    # Ask user for the model UUID
    model_uuid = input("Enter the UUID of the model to use for prediction: ").strip()

    # Load in the prediction data
    # Assumes the dataset has columns 'UNIX time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'
    # plus volatility and other TA indicators (see the training data)
    prediction_data = pd.read_csv('app/strategies/LSTM/data/crypto_prediction_data.csv')

    scaler = StandardScaler()
    scaled_prediction_data = scaler.fit_transform(prediction_data)

    # Prepare the sequences
    X_prediction = []
    for i in range(len(scaled_prediction_data) - SEQUENCE_LENGTH):
        X_prediction.append(scaled_prediction_data[i:i+SEQUENCE_LENGTH])

    X_prediction = np.array(X_prediction)

    # Load the trained model
    try:
        model = load_model(f'app/strategies/LSTM/models/model_{model_uuid}.h5')
    except FileNotFoundError:
        print(f"Error: Model file not found for UUID {model_uuid}")
        exit(1)

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
    print(f"\nPredictions using model {model_uuid}:")
    print(predictions_actual)
