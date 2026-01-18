EPOCHS = 50
BATCH_SIZE = 32

# Define the sequence length (number of time steps) for LSTM
# You can adjust this based on the nature of your data
SEQUENCE_LENGTH = 24

# Technical Indicator Parameters
MA_SHORT = 10      # Short-term Moving Average period
MA_LONG = 50       # Long-term Moving Average period
EMA_SHORT = 12     # Short-term Exponential Moving Average period
EMA_LONG = 26      # Long-term Exponential Moving Average period
RSI_PERIOD = 14    # Relative Strength Index period
MACD_FAST = 12     # MACD fast EMA period
MACD_SLOW = 26     # MACD slow EMA period
MACD_SIGNAL = 9    # MACD signal line period