from dotenv import dotenv_values

class AppConfig():
    def __init__(self):
        env_config = dotenv_values(".env")

        self.DATABASE_USERNAME = env_config['DATABASE_USERNAME']
        self.DATABASE_PASSWORD = env_config['DATABASE_PASSWORD']
        self.DATABASE_PORT = env_config['DATABASE_PORT']
        self.DATABASE_NAME = env_config['DATABASE_NAME']

        del env_config

class GRIDBotConfig():
    def __init__(self):
        env_config = dotenv_values(".env")

        self.exchange = env_config['EXCHANGE']
        self.api_key = env_config['API_KEY']
        self.api_sec = env_config['API_SEC']
        self.api_passphrase = env_config['API_PASSPHRASE']
        self.pair = env_config['PAIR']
        self.days_to_run = int(env_config['DAYS_TO_RUN'])
        self.mode = env_config['MODE']
        self.upper_price = float(env_config['UPPER_PRICE'])
        self.lower_price = float(env_config['LOWER_PRICE'])
        self.level_num = int(env_config['LEVEL_NUM'])
        self.cash = float(env_config['CASH'])
        self.loss_threshold = float(env_config['LOSS_THRESHOLD'])
        self.latency_in_sec = float(env_config['LATENCY_IN_SEC'])
        self.send_to_discord = (env_config['SEND_TO_DISCORD'].lower() == 'true')

        if self.send_to_discord:
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
        env_config = dotenv_values(".env")

        self.exchange = env_config['EXCHANGE']
        self.api_key = env_config['API_KEY']
        self.api_sec = env_config['API_SEC']
        self.api_passphrase = env_config['API_PASSPHRASE']
        self.pair = env_config['PAIR']
        self.mode = env_config['MODE']

        del env_config