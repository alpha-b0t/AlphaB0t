from config import RequestConfig, GRIDBotConfig, ExchangeConfig
from app.models.exchange import KrakenExchange, CoinbaseExchange, RobinhoodCryptoExchange
from app.models.gridbot import GRIDBot
from AI.get_data import fetch_data
from AI.json_helper import export_json_to_csv
from AI.clean_data import remove_duplicates_and_sort

if __name__ == '__main__':
    request_config = RequestConfig()
    
    if request_config.request in ['AI', 'ai']:
        pair = input('Enter crypto pair: ')
        interval = int(input('Enter interval (1, 5, 15, 30, 60, 240, 1440, 10080, 21600): '))
        since = 0
        json_filename = input("Enter JSON filename to store data (e.g. 'training_data.json'): ")
        csv_filename = input("Enter CSV filename to store data (e.g. 'crypto_training_data.csv'): ")

        fetch_data(
            pair=pair,
            interval=interval,
            since=since,
            filename=json_filename
        )

        export_json_to_csv(json_filename, csv_filename)

        remove_duplicates_and_sort(csv_filename)
    else:
        gridbot_config = GRIDBotConfig()
        exchange_config = ExchangeConfig()
        
        if exchange_config.exchange_name == 'RobinhoodCrypto':
            pass
        elif exchange_config.exchange_name == 'Kraken':

            if request_config.request in ['start', 'START', '', None, 'None']:
                # Initialize Kraken gridbot
                kraken_exchange = KrakenExchange(exchange_config)
                
                kraken_gridbot = GRIDBot(
                    gridbot_config=gridbot_config,
                    exchange=kraken_exchange
                )
                print(kraken_gridbot)

                # Start automated grid trading
                kraken_gridbot.start()
            elif request_config.request in ['load', 'LOAD']:
                # Load Kraken gridbot if it exists
                kraken_gridbot = GRIDBot.from_json_file(f'app/bots/{gridbot_config.name}.json')

                print(kraken_gridbot)

                # Restart automated grid trading
                kraken_gridbot.restart()
        elif exchange_config.exchange_name == "Coinbase":
            pass
