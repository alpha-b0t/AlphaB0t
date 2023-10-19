from RobinhoodCrypto.grid_bot import GRIDBot
from config import GRIDBotConfig
from RobinhoodCrypto.helpers import confirm_grids

if __name__ == '__main__':
    config = GRIDBotConfig()
    
    if confirm_grids(config.upper_price, config.lower_price, config.level_num, config.cash):
        grid_trader = GRIDBot(config)

        # grid_trader.start()

        simulation_metric = grid_trader.simulate_trading(
            pair='LINK',
            level_num=4,
            upper_price=8.10,
            lower_price=5.25,
            interval='day',
            span='year',
            bounds='24_7',
            loss_threshold=100,
            loss_percentage=10
        )

        print(f"Simulation performance: {simulation_metric}%")

        grid_trader.logout()