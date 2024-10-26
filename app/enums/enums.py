from enum import Enum

class BotMode(Enum):
    TEST = 0
    LIVE = 1
    PAPER = 2

class BotType(Enum):
    GRID = 0
    SENTIMENT = 1
    AI = 2
    DCA = 3

class ExchangeType(Enum):
    KRAKEN = 0
    COINBASE = 1
    BINANCE_US = 2
    ROBINHOOD_CRYPTO = 3

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
