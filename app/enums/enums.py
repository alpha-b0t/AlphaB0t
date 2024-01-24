from enum import Enum

class Mode(Enum):
    TEST = 0
    LIVE = 1
    DEMO = 2

class Exchange(Enum):
    KRAKEN = 0
    COINBASE = 1
    BINANCE = 2
    BINANCE_US = 3

class ExitAction(Enum):
    NOTHING = 0
    CANCEL_ALL = 1
    CANCEL_SELL_ONLY = 2
    CANCEL_BUY_ONLY = 3
