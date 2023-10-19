from RobinhoodCrypto.grid_bot import GRIDBot
from config import GRIDBotConfig
from RobinhoodCrypto.helpers import confirm_grids

if __name__ == '__main__':
    config = GRIDBotConfig()
    
    if confirm_grids(config.upper_price, config.lower_price, config.level_num, config.cash):
        grid_trader = GRIDBot(config)

        del config

        # grid_trader.start()

        simulation_metric = grid_trader.simulate_grid_trading('LINK', 4, 8.10, 5.25, 'day', 'year', '24_7', 100, 10)

        print(f"Simulation performance: {simulation_metric}%")

        grid_trader.logout()
    else:
        del config