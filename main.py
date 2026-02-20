from config import RequestConfig, GRIDBotConfig, ExchangeConfig, StrategyConfig, RiskManagerConfig
from app.exchanges.exchange import KrakenExchange, CoinbaseExchange, RobinhoodCryptoExchange, RobinhoodOptionExchange
from app.bots.bot import Bot
from app.bots.gridbot import GRIDBot
from app.enums.enums import RequestType, BotMode, StrategyType, ExchangeType, ExitAction

if __name__ == '__main__':
    request_config = RequestConfig()

    # TODO: Consider getting rid of request as it is essentially useless
    if request_config.request in ['RUN', 'run']:
        gridbot_config = GRIDBotConfig()
        exchange_config = ExchangeConfig()
        strategy_config = StrategyConfig()
        riskmanager_config = RiskManagerConfig()
        
        if exchange_config.exchange_name == 'RobinhoodCrypto':
            pass
        elif exchange_config.exchange_name == 'RobinhoodOption':
            pass
        elif exchange_config.exchange_name == 'Kraken':
            kraken_exchange = KrakenExchange(exchange_config)

            if strategy_config.strategy in ['GRID', 'grid']:
                # Initialize Kraken gridbot
                
                kraken_gridbot = GRIDBot(
                    gridbot_config=gridbot_config,
                    exchange=kraken_exchange
                )
                print(kraken_gridbot)

                # Start automated grid trading
                kraken_gridbot.start()
            elif strategy_config.strategy in ['GRID_LOAD', 'grid_load']:
                # Load Kraken gridbot if it exists
                kraken_gridbot = GRIDBot.from_json_file(f'app/bots/local/{gridbot_config.name}.json')

                print(kraken_gridbot)

                # Restart automated grid trading
                kraken_gridbot.restart()
            elif strategy_config.strategy in ['LSTM', 'lstm']:
                kraken_lstm_bot = Bot()
        elif exchange_config.exchange_name == "Coinbase":
            pass
        elif exchange_config.exchange_name == "Binance_US":
            pass
        else:
            print(f"Exchange name {exchange_config.exchange_name} not found")
    else:
        print(f"Request {request_config.request} not valid")
