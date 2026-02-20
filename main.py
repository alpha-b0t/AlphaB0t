from config import RequestConfig, GRIDBotConfig, ExchangeConfig, StrategyConfig, RiskManagerConfig, BotConfig
from app.exchanges.exchange import KrakenExchange, CoinbaseExchange, RobinhoodCryptoExchange, RobinhoodOptionExchange
from app.bots.bot import Bot
from app.bots.gridbot import GRIDBot
from app.enums.enums import RequestType, BotMode, StrategyType, ExchangeType, ExitAction
from app.riskmanager import RiskManager
from app.strategies.strategy import Strategy, GridStrategy, LSTMStrategy
from app.strategies.LSTM.get_data import fetch_training_data
from app.strategies.LSTM.train_model import train_model

if __name__ == '__main__':
    request_config = RequestConfig()

    # TODO: Consider getting rid of request as it is essentially useless
    if request_config.request in ['RUN', 'run']:
        bot_config = BotConfig()
        exchange_config = ExchangeConfig()
        strategy_config = StrategyConfig()
        riskmanager_config = RiskManagerConfig()

        risk_manager = RiskManager(riskmanager_config)
        
        if exchange_config.exchange_name == 'RobinhoodCrypto':
            pass
        elif exchange_config.exchange_name == 'RobinhoodOption':
            pass
        elif exchange_config.exchange_name == 'Kraken':
            kraken_exchange = KrakenExchange(exchange_config)

            if strategy_config.strategy in ['GRID', 'grid']:
                # Initialize Kraken gridbot
                kraken_gridbot = GRIDBot(
                    gridbot_config=GRIDBotConfig(),
                    exchange=kraken_exchange
                )
                print(kraken_gridbot)

                # Start automated grid trading
                kraken_gridbot.start()
            elif strategy_config.strategy in ['GRID_LOAD', 'grid_load']:
                gridbot_config = GRIDBotConfig()

                # Load Kraken gridbot if it exists
                kraken_gridbot = GRIDBot.from_json_file(f'app/bots/local/{gridbot_config.name}.json')

                print(kraken_gridbot)

                # Restart automated grid trading
                kraken_gridbot.restart()
            elif strategy_config.strategy in ['LSTM', 'lstm']:
                lstm_strategy = LSTMStrategy(strategy_config, kraken_exchange)

                kraken_lstm_bot = Bot(bot_config, kraken_exchange, lstm_strategy, risk_manager)

                kraken_lstm_bot.run()
            else:
                print(f"Strategy {strategy_config.strategy} not valid")
        elif exchange_config.exchange_name == "Coinbase":
            pass
        elif exchange_config.exchange_name == "Binance_US":
            pass
        else:
            print(f"Exchange name {exchange_config.exchange_name} not found")
    elif request_config.request in ['LSTM_TRAIN', 'lstm_train']:
        fetch_training_data()

        train_model()
    else:
        print(f"Request {request_config.request} not valid")
