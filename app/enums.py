from enum import Enum

class RequestType(Enum):
    RUN = 0
    BOT_LOAD = 1
    LSTM_TRAIN = 2
    LSTM_TRAIN_FETCH = 3

class BotMode(Enum):
    TEST = 0
    LIVE = 1
    PAPER = 2

class StrategyType(Enum):
    GRID = 0
    LSTM = 1
    DCA = 2

class ExchangeType(Enum):
    KRAKEN = 0
    KRAKENFUTURES = 1
    COINBASE = 2
    BINANCE = 3
    BINANCE_US = 4
    ROBINHOOD_CRYPTO = 5

class ExitAction(Enum):
    NOTHING = 0
    CANCEL_ALL = 1
    CANCEL_SELL_ONLY = 2
    CANCEL_BUY_ONLY = 3

class OrderType(Enum):
    BUY = 0
    SELL = 1

class OrderStatusType(Enum):
    ACTIVE = 0
    INACTIVE = 1
    CLOSED = 2
