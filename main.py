from RobinhoodCrypto.gridbot import GRIDBot
from config import AppConfig, GRIDBotConfig, ExchangeConfig
from RobinhoodCrypto.helpers import confirm_grids
from app.models.exchange import Exchange, KrakenExchange, CoinbaseExchange, RobinhoodCryptoExchange
from app.models.gridbot import GRIDBot, KrakenGRIDBot
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
                stop_loss=100
            )

            print(f"Simulation performance: {simulation_metric}%")

            grid_trader.logout()
    elif exchange_config.exchange == 'Kraken':
        kraken_exchange = KrakenExchange(exchange_config.api_key, exchange_config.api_sec, exchange_config.mode)
        print(kraken_exchange)

        # Get account balance
        print("Account balance:")
        print(kraken_exchange.get_account_balance())
        
        # Get extended balance
        print("Extended balance:")
        print(kraken_exchange.get_extended_balance())

        # Get trade volume and fee schedule
        print("Trade volume and fee schedule:")
        print(kraken_exchange.get_trade_volume(grid_bot_config.pair))

        kraken_gridbot = KrakenGRIDBot(
            grid_bot_config.api_key,
            grid_bot_config.api_sec,
            grid_bot_config.pair,
            grid_bot_config.days_to_run,
            grid_bot_config.mode,
            grid_bot_config.upper_price,
            grid_bot_config.lower_price,
            grid_bot_config.level_num,
            grid_bot_config.cash,
            grid_bot_config.stop_loss,
            grid_bot_config.take_profit,
            grid_bot_config.base_currency,
            grid_bot_config.latency_in_sec
        )

        kraken_gridbot.start()
    else:
        # Run C++ executables
        cpp_executable = './bin/main'

        subprocess.run(cpp_executable, shell=True)