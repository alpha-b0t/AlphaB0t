from RobinhoodCrypto.gridbot import GRIDBot
from config import AppConfig, GRIDBotConfig, ExchangeConfig
from RobinhoodCrypto.helpers import confirm_grids
from app.models.exchange import Exchange, KrakenExchange, CoinbaseExchange, RobinhoodCryptoExchange
from app.models.gridbot import GRIDBot, KrakenGRIDBot
import subprocess

if __name__ == '__main__':
    gridbot_config = GRIDBotConfig()
    exchange_config = ExchangeConfig()

    if exchange_config.exchange == 'Robinhood':
    
        if confirm_grids(gridbot_config.upper_price, gridbot_config.lower_price, gridbot_config.level_num, gridbot_config.total_investment):
            grid_trader = GRIDBot(gridbot_config)

            simulation_metric = grid_trader.simulate_trading(
                pair='LINK',
                level_num=4,
                upper_price=8.10,
                lower_price=5.25,
                interval='day',
                span='year',
                bounds='24_7',
                stop_loss=100
            )

            print(f"Simulation performance: {simulation_metric}%")

            grid_trader.logout()
    elif exchange_config.exchange == 'Kraken':

        # Initialize Kraken gribot
        kraken_gridbot = KrakenGRIDBot(
            gridbot_config=gridbot_config,
            exchange_config=exchange_config
        )
        print(kraken_gridbot)

        # Start automated grid trading
        kraken_gridbot.start()
    else:
        # Run C++ executables
        cpp_executable = './bin/main'

        subprocess.run(cpp_executable, shell=True)