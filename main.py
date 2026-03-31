from config import RequestConfig, ExchangeConfig, StrategyConfig, RiskManagerConfig, BotConfig
from app.exchanges.exchange import KrakenExchange, BinanceExchange, BinanceUSExchange, CoinbaseExchange, RobinhoodCryptoExchange
from app.exchanges.futuresexchange import KrakenFuturesExchange
from app.bots.bot import Bot
from app.enums import RequestType, BotMode, StrategyType, ExchangeType, ExitAction
from app.riskmanager import RiskManager
from app.strategies.strategy import Strategy, LSTMStrategy
from app.strategies.LSTM.get_data import fetch_training_data
from app.strategies.LSTM.train_model import train_model
from dotenv import dotenv_values

if __name__ == '__main__':
    request_config = RequestConfig()

    # TODO: Consider getting rid of request as it is essentially useless
    if request_config.request == "RUN":
        bot_config = BotConfig()
        exchange_config = ExchangeConfig()
        strategy_config = StrategyConfig()
        risk_manager = RiskManager(RiskManagerConfig())
        
        # Set exchange
        if exchange_config.exchange_name == 'RobinhoodCrypto':
            raise NotImplementedError
        elif exchange_config.exchange_name == 'KrakenFutures':
            raise NotImplementedError
        elif exchange_config.exchange_name == 'Kraken':
            exchange = KrakenExchange(exchange_config)
        elif exchange_config.exchange_name == "Coinbase":
            raise NotImplementedError
        elif exchange_config.exchange_name == "Binance":
            raise NotImplementedError
        elif exchange_config.exchange_name == "Binance_US":
            raise NotImplementedError
        else:
            raise ValueError(f"Exchange name {exchange_config.exchange_name} not found")
        
        # Set strategy and bot
        if strategy_config.strategy == "LSTM":
            lstm_strategy = LSTMStrategy(strategy_config, exchange)

            lstm_bot = Bot(bot_config, exchange, lstm_strategy, risk_manager)

            lstm_bot.run()
        else:
            raise ValueError(f"Strategy {strategy_config.strategy} not valid")
    elif request_config.request == "BOT_LOAD":
            bot_config = BotConfig()

            # Load bot if it exists
            bot = Bot.from_json_file(f'app/bots/local/{bot_config.name}.json')

            # Restart trading
            bot.restart()
    elif request_config.request == "LSTM_TRAIN":
        train_model()
    elif request_config.request == "LSTM_TRAIN_FETCH":
        fetch_training_data()
    else:
        raise ValueError(f"Request {request_config.request} not valid")
