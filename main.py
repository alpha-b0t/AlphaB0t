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
        kraken_exchange = KrakenExchange(exchange_config.api_key, exchange_config.api_sec, exchange_config.pair, exchange_config.mode)

        # Get extended balance
        print(kraken_exchange.get_extended_balance())

        # Get account balance
        print(kraken_exchange.get_account_balance())

        # Get trade balance
        print(kraken_exchange.get_trade_balance())

        # Get trade volume and fee schedule
        print(kraken_exchange.get_trade_volume(exchange_config.pair))

        # Add an order
        add_response = kraken_exchange.add_order(
            ordertype='limit',
            type='buy',
            volume=5,
            pair=exchange_config.pair,
            price='2',
            oflags='post',
            validate='true'
        )
        
        print(add_response)

        # Edit an order
        # edit_response = kraken_exchange.edit_order(
        #     txid=add_response['result']['txid'],
        #     pair=exchange_config.pair,
        #     price='1.5',
        #     oflags='post',
        #     validate='true'
        # )

        # print(edit_response)

        # Cancel an order
        # cancel_response = kraken_exchange.cancel_order('OQD3ML-T6SZR-TBJWL7')

        # print(cancel_response)
    else:
        # Run C++ executables
        cpp_executable = './bin/main'

        subprocess.run(cpp_executable, shell=True)