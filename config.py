from dotenv import dotenv_values

class AppConfig():
    def __init__(self):
        return

class GridBotConfig():
    def __init__(self):
        env_config = dotenv_values(".env")

        self.crypto = env_config['CRYPTO']
        self.days_to_run = int(env_config['DAYS_TO_RUN'])
        self.mode = env_config['MODE']
        self.backtest_interval = env_config['BACKTEST_INTERVAL']
        self.backtest_span = env_config['BACKTEST_SPAN']
        self.backtest_bounds = env_config['BACKTEST_BOUNDS']
        self.upper_price = float(env_config['UPPER_PRICE'])
        self.lower_price = float(env_config['LOWER_PRICE'])
        self.level_num = int(env_config['LEVEL_NUM'])
        self.cash = float(env_config['CASH'])
        self.loss_threshold = float(env_config['LOSS_THRESHOLD'])
        self.loss_percentage = float(env_config['LOSS_PERCENTAGE'])
        self.latency_in_sec = float(env_config['LATENCY_IN_SEC'])
        self.send_to_discord = (env_config['SEND_TO_DISCORD'].lower() == 'true')
        self.discord_latency_in_hours = float(env_config['DISCORD_LATENCY_IN_HOURS'])
        self.discord_url = env_config['DISCORD_URL']
        self.max_error_count = int(env_config['MAX_ERROR_COUNT'])
        self.error_latency_in_sec = float(env_config['ERROR_LATENCY_IN_SEC'])
        self.init_buy_error_latency_in_sec = float(env_config['INIT_BUY_ERROR_LATENCY_IN_SEC'])
        self.init_buy_error_max_count = int(env_config['INIT_BUY_ERROR_MAX_COUNT'])
        self.cancel_orders_upon_exit = env_config['CANCEL_ORDERS_UPON_EXIT']
        
        del env_config

class ExchangeConfig():
    def __init__(self):
        return