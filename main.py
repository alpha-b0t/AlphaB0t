from RobinhoodCrypto.grid_bot import GRIDBot
from config import AppConfig, GRIDBotConfig, ExchangeConfig
from RobinhoodCrypto.helpers import confirm_grids
from app.models.exchange import Exchange, KrakenExchange, CoinbaseExchange, RobinhoodCryptoExchange
import subprocess

if __name__ == '__main__':
    grid_bot_config = GRIDBotConfig()
    exchange_config = ExchangeConfig()

    if exchange_config.exchange == 'Robinhood':
    
        if confirm_grids(grid_bot_config.upper_price, grid_bot_config.lower_price, grid_bot_config.level_num, grid_bot_config.cash):
            grid_trader = GRIDBot(grid_bot_config)

            simulation_metric = grid_trader.simulate_trading(
                pair='LINK',
                level_num=4,
                upper_price=8.10,
                lower_price=5.25,
                interval='day',
                span='year',
                bounds='24_7',
                loss_threshold=100
            )

            print(f"Simulation performance: {simulation_metric}%")

            grid_trader.logout()
    elif exchange_config.exchange == 'Kraken':
        kraken_exchange = KrakenExchange(exchange_config.api_key, exchange_config.api_sec)

        print(kraken_exchange.get_extended_balance())
        print(kraken_exchange.get_account_balance())
        print(kraken_exchange.get_trade_balance())
        print(kraken_exchange.get_trade_volume('XBTUSD'))
    else:
        # Run C++ executables
        cpp_executable = './bin/main'

        subprocess.run(cpp_executable, shell=True)