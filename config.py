from dotenv import dotenv_values
import inspect
from constants import CLASS_NAMES


def _parse_float(val) -> float:
    """Parse a float from .env value that may include inline comments."""
    if val is None:
        return 0.0
    return float(str(val).split('#')[0].strip())


def _from_json_mixin(cls, json_data):
    """Shared from_json logic for all config classes."""
    init_params = inspect.signature(cls.__init__).parameters
    known_attributes = {param for param in init_params if param != 'self'}
    known_data = {k: v for k, v in json_data.items() if k in known_attributes}
    additional_data = {k: v for k, v in json_data.items() if k not in known_attributes}
    instance = cls(**known_data)
    for key, value in additional_data.items():
        if isinstance(value, dict) and 'classname' in value and value['classname'] in CLASS_NAMES:
            exec(f'setattr(instance, key, {value["classname"]}.from_json(value))')
        else:
            setattr(instance, key, value)
    return instance


class AppConfig():
    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)

    @classmethod
    def from_json(cls, json_data):
        return _from_json_mixin(cls, json_data)


class RequestConfig():
    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)
        self.request = env_config['REQUEST']

    @classmethod
    def from_json(cls, json_data):
        return _from_json_mixin(cls, json_data)


class BotConfig():
    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)
        self.exchange_name = env_config['EXCHANGE']
        self.name = env_config['NAME']
        self.pair = env_config['PAIR']
        self.mode = env_config.get('MODE', 'test') or 'test'

    @classmethod
    def from_json(cls, json_data):
        return _from_json_mixin(cls, json_data)


class GRIDBotConfig(BotConfig):
    """Grid trading bot configuration. Inherits base fields from BotConfig."""

    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)

        # Shared with BotConfig
        self.exchange_name = env_config['EXCHANGE']
        self.name = env_config['NAME']
        self.pair = env_config['PAIR']
        self.base_currency = env_config['BASE_CURRENCY']
        self.days_to_run = int(env_config['DAYS_TO_RUN'])
        self.mode = env_config.get('MODE', 'test') or 'test'

        self.upper_price = _parse_float(env_config['UPPER_PRICE'])
        self.lower_price = _parse_float(env_config['LOWER_PRICE'])
        self.level_num = int(env_config['LEVEL_NUM'])
        self.quantity_per_grid = _parse_float(env_config['QUANTITY_PER_GRID'])
        self.total_investment = _parse_float(env_config['TOTAL_INVESTMENT'])
        self.stop_loss = _parse_float(env_config['STOP_LOSS'])
        self.take_profit = _parse_float(env_config['TAKE_PROFIT'])
        self.latency_in_sec = _parse_float(env_config['LATENCY_IN_SEC'])
        self.max_error_count = int(env_config['MAX_ERROR_COUNT'])
        self.error_latency_in_sec = _parse_float(env_config['ERROR_LATENCY_IN_SEC'])
        self.init_buy_error_latency_in_sec = _parse_float(env_config['INIT_BUY_ERROR_LATENCY_IN_SEC'])
        self.init_buy_error_max_count = int(env_config['INIT_BUY_ERROR_MAX_COUNT'])
        self.cancel_orders_upon_exit = env_config['CANCEL_ORDERS_UPON_EXIT']

    @classmethod
    def from_json(cls, json_data):
        return _from_json_mixin(cls, json_data)


class CoinMarketCapAPIConfig():
    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)
        self.cmc_api_key = env_config.get('CMC_API_KEY', '')

    @classmethod
    def from_json(cls, json_data):
        return _from_json_mixin(cls, json_data)


class ExchangeConfig():
    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)

        self.exchange_name = env_config['EXCHANGE']
        self.api_key = env_config.get('API_KEY') or ''
        self.api_sec = env_config.get('API_SEC') or ''
        self.api_passphrase = env_config.get('API_PASSPHRASE') or ''
        self.mode = env_config.get('MODE') or 'test'

    @classmethod
    def from_json(cls, json_data):
        return _from_json_mixin(cls, json_data)


class StrategyConfig():
    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)

        self.strategy = env_config.get('STRATEGY', '')
        # lstm_model_uuid is optional — only required when STRATEGY=LSTM
        self.lstm_model_uuid = env_config.get('LSTM_MODEL_UUID') or ''
        self.pair = env_config.get('PAIR', '')

    @classmethod
    def from_json(cls, json_data):
        return _from_json_mixin(cls, json_data)


class RiskManagerConfig():
    def __init__(self, filepath='.env'):
        self.classname = self.__class__.__name__
        env_config = dotenv_values(filepath)

        # Use _parse_float so inline comments like "0.01 # 1%" are handled safely
        self.risk_per_trade = _parse_float(env_config.get('RISK_PER_TRADE', '0.01'))
        self.max_position_pct = _parse_float(env_config.get('MAX_POSITION_PCT', '0.2'))
        self.max_drawdown_pct = _parse_float(env_config.get('MAX_DRAWDOWN_PCT', '0.15'))
        self.portfolio_balance = _parse_float(env_config.get('PORTFOLIO_BALANCE', '10000'))

    @classmethod
    def from_json(cls, json_data):
        return _from_json_mixin(cls, json_data)
