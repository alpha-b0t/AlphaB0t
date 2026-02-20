from config import RequestConfig, GRIDBotConfig, ExchangeConfig
from app.exchanges.exchange import KrakenExchange, CoinbaseExchange, RobinhoodCryptoExchange, RobinhoodOptionExchange
from app.bots.gridbot import GRIDBot
from app.strategies.LSTM.get_data import fetch_data, fetch_fear_and_greed_data
from app.strategies.LSTM.json_helper import export_json_to_csv
from app.strategies.LSTM.clean_data import remove_duplicates_and_sort
from app.strategies.LSTM.model_constants import INTERVAL

if __name__ == '__main__':
    request_config = RequestConfig()
    
    if request_config.request in ['LSTM', 'lstm']:
        pair = input('Enter crypto pair: ')
        since = 0
        json_filename = input("Enter JSON filename to store data (e.g. 'training_data.json'): ")
        csv_filename = input("Enter CSV filename to store data (e.g. 'crypto_training_data.csv'): ")

        fetch_data(
            pair=pair,
            interval=int(INTERVAL),
            since=since,
            filename=json_filename
        )

        export_json_to_csv(json_filename, csv_filename)

        remove_duplicates_and_sort(csv_filename)

        if input("Fetch fear and greed index data? (y/n): ").lower() == 'y':
            fg_json_filename = input("Enter JSON filename to store fear and greed data (e.g. 'fear_and_greed_data.json'): ")
            fg_csv_filename = input("Enter CSV filename to store fear and greed data (e.g. 'fear_and_greed_data.csv'): ")
            fetch_fear_and_greed_data(
                start=since,
                filename=fg_json_filename
            )

            export_json_to_csv(fg_json_filename, fg_csv_filename)

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
                kraken_gridbot = GRIDBot.from_json_file(f'app/bots/local/{gridbot_config.name}.json')

                print(kraken_gridbot)

                # Restart automated grid trading
                kraken_gridbot.restart()
        elif exchange_config.exchange_name == "Coinbase":
            pass
