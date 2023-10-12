from bot import GridTradingBot
from order import *
from error_queue import ErrorQueue, ErrorQueueLimitExceededError
from config import GridTradingBotConfig
from helpers import confirm_grids

if __name__ == '__main__':
    config = GridTradingBotConfig()
    
    if confirm_grids(config.config['upper_price'], config.config['lower_price'], config.config['level_num'], config.config['cash']):
        grid_trader = GridTradingBot(config.config)
        del config
        grid_trader.start()
    else:
        del config
