from RobinhoodCrypto.grid_bot import GridBot
from config import GridBotConfig
from RobinhoodCrypto.helpers import confirm_grids

if __name__ == '__main__':
    config = GridBotConfig()
    
    if confirm_grids(config.upper_price, config.lower_price, config.level_num, config.cash):
        grid_trader = GridBot(config)

        del config

        # grid_trader.start()
        
        grid_trader.backtest(grid_trader.crypto)
    else:
        del config