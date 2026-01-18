from app.models.bot import Bot
from app.models.exchange import KrakenExchange
from app.models.ohlc import OHLC
from app.models.order import KrakenOrder
from app.exchanges.cmc_api import CoinMarketCapAPI
from app.helpers.techinical_analysis import TA
from config import SentimentBotConfig
import time
from datetime import datetime

class SentimentBot(Bot):
    def __init__(self, sentiment_config: SentimentBotConfig={}, exchange: KrakenExchange={}, sentiment_api: CoinMarketCapAPI={}):
        super().__init__()
        self.classname = self.__class__.__name__
        if type(sentiment_config) == dict and type(exchange) == dict and type(sentiment_api) == dict:
            # Reloading
            print(f"Reloading {self.classname}...")
            return
        
        # self.sentiment_config = sentiment_config
        self.exchange = exchange
        self.sentiment_api = sentiment_api

        self.name = sentiment_config.name
        self.pair = sentiment_config.pair
        self.days_to_run = sentiment_config.days_to_run
        self.mode = sentiment_config.mode
        self.total_investment = sentiment_config.total_investment
        self.stop_loss = sentiment_config.stop_loss
        self.take_profit = sentiment_config.take_profit
        self.base_currency = sentiment_config.base_currency
        self.latency = sentiment_config.latency_in_sec
        self.max_error_count = sentiment_config.max_error_count
        self.error_latency = sentiment_config.error_latency_in_sec
        self.init_but_error_latency = sentiment_config.init_buy_error_latency_in_sec
        self.init_buy_error_max_count = sentiment_config.init_buy_error_max_count
        self.cancel_orders_upon_exit = sentiment_config.cancel_orders_upon_exit

        # Initialize the timer
        self.start_time = time.time()

        # Perform validation on the configuration
        self.check_config()

        # Fetch information related to the pair
        for attempt in range(self.max_error_count):
            try:
                asset_info_response = self.exchange.get_tradable_asset_pairs(self.pair)
                break
            except Exception as e:
                print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")
                
                if attempt == self.max_error_count - 1:
                    print(f"Failed to make API request after {self.max_error_count} attempts")
                    raise e
                else:
                    time.sleep(self.error_latency)
        
        asset_info = asset_info_response.get('result')

        for key in asset_info.keys():
            pair_key = key
        
        pair_info = asset_info[pair_key]

        # Price precision
        self.pair_decimals = pair_info['pair_decimals']

        # Volume precision in base currency
        self.lot_decimals = pair_info['lot_decimals']

        self.cost_decimals = pair_info['cost_decimals']
        self.ordermin = float(pair_info['ordermin'])
        self.costmin = float(pair_info['costmin'])
        self.tick_size = pair_info['tick_size']
        self.pair_status = pair_info['status']

        if self.exchange.api_key != '' and self.exchange.api_sec != '':
            # Fetch fee schedule and trade volume info
            for attempt in range(self.max_error_count):
                try:
                    trade_volume_fee_response = self.exchange.get_trade_volume(self.pair)
                    break
                except Exception as e:
                    print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")
                    
                    if attempt == self.max_error_count - 1:
                        print(f"Failed to make API request after {self.max_error_count} attempts")
                        raise e
                    else:
                        time.sleep(self.error_latency)
            
            fee_info = trade_volume_fee_response.get('result')
            self.trade_volume = fee_info['volume']

            for key in fee_info['fees'].keys():
                pair_key = key
            
            if fee_info.get('fees_maker') is None:
                self.fee_taker = self.fee_maker = float(fee_info['fees'][pair_key]['fee'])
            else:
                self.fee_taker = float(fee_info['fees'][pair_key]['fee'])
                self.fee_maker = float(fee_info['fees_maker'][pair_key]['fee'])

        # TODO: Implement
        self.closed_orders = []
        self.gain = 0
        self.gain_percent = 0
        self.fee = 0

        # Fetch balances
        if self.exchange.api_key != '' and self.exchange.api_sec != '':
            self.fetch_balances()

        if self.mode != 'test':
            if self.total_investment > self.account_trade_balances[self.base_currency]:
                raise Exception(f"Your total investment, {self.total_investment} {self.base_currency}, is greater than your balance of {self.base_currency} availabe for trading, {self.account_trade_balances[self.base_currency]}.")
    
    def __repr__(self):
        if self.name == '':
            name_display = "''"
        else:
            name_display = self.name
        
        return f"{{{self.classname} name: {name_display}, pair: {self.pair}, mode: {self.mode}, runtime: {self.get_runtime()}s, gain: {self.gain} {self.base_currency}, gain_percent: {self.gain_percent}%, fee: {self.fee} {self.base_currency}, total_investment: {self.total_investment} {self.base_currency}}}"
    
    def get_runtime(self):
        return time.time() - self.start_time
    
    def check_config(self):
        """Throws an error if the configurations are not correct."""
        # TODO: Implement
        assert self.mode in ['live', 'test']
        assert self.stop_loss > 0
        assert self.take_profit > 0
        assert self.take_profit > self.stop_loss
        assert self.days_to_run > 0
        assert self.latency > 0
        assert self.max_error_count >= 1
        assert self.error_latency > 0
    
    def init(self):
        """Initializes strategy."""
        raise NotImplementedError("Not implemented.")
    
    def get_account_asset_balance(self, pair: str = 'ZUSD') -> float:
        """Retrieves the cash balance of the asset (i.e. pair or currency), net of pending withdrawals."""
        for attempt in range(self.max_error_count):
            try:
                account_balances_response = self.exchange.get_account_balance()

                account_balances = account_balances_response.get('result')

                return float(account_balances.get(pair, 0))
            except Exception as e:
                print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                if attempt == self.max_error_count - 1:
                    print(f"Failed to make API request after {self.max_error_count} attempts")
                    raise e
                else:
                    time.sleep(self.error_latency)
    
    def get_available_trade_balance(self) -> dict:
        """Retrieves the balance(s) available for trading."""
        for attempt in range(self.max_error_count):
            try:
                extended_balances_response = self.exchange.get_extended_balance()

                extended_balance = extended_balances_response.get('result')

                available_balances = {}

                for asset in extended_balance.keys():
                    available_balances[asset] = float(extended_balance[asset]['balance']) + float(extended_balance[asset].get('credit', 0)) - float(extended_balance[asset].get('credit_used', 0)) - float(extended_balance[asset]['hold_trade'])
                
                return available_balances
            except Exception as e:
                print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")
                
                if attempt == self.max_error_count - 1:
                    print(f"Failed to make API request after {self.max_error_count} attempts")
                    raise e
                else:
                    time.sleep(self.error_latency)
    
    def fetch_balances(self):
        """Fetches latest account balances and account balances available for trading."""
        for attempt in range(self.max_error_count):
            try:
                account_balances_response = self.exchange.get_account_balance()
                break
            except Exception as e:
                print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")
                
                if attempt == self.max_error_count - 1:
                    print(f"Failed to make API request after {self.max_error_count} attempts")
                    raise e
                else:
                    print("Fetching balances: ERROR WAIT")
                    time.sleep(self.error_latency)
        
        self.account_balances = account_balances_response.get('result')

        for asset in self.account_balances.keys():
            self.account_balances[asset] = float(self.account_balances[asset])
        
        self.account_trade_balances = self.get_available_trade_balance()
    
    def fetch_latest_ohlc(self):
        """Fetches latest OHLC data."""
        for attempt in range(self.max_error_count):
            try:
                ohlc_response = self.exchange.get_ohlc_data(self.pair)
                break
            except Exception as e:
                print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                if attempt == self.max_error_count - 1:
                    print(f"Failed to make API request after {self.max_error_count} attempts")
                    raise e
                else:
                    time.sleep(self.error_latency)
        
        ohlc = ohlc_response.get('result')
        self.latest_ohlc = OHLC(ohlc[self.ohlc_asset_key][-1])
    
    def get_realized_gain(self):
        # Updates self.gain, self.gain_percent, and self.fee
        gain = 0
        fee = 0

        try:
            for i in range(len(self.closed_orders)):
                if self.closed_orders[i].descr['type'] == 'buy':
                    gain -= float(self.closed_orders[i].vol_exec) * float(self.closed_orders[i].price)
                    gain -= float(self.closed_orders[i].fee)

                else:
                    gain += float(self.closed_orders[i].vol_exec) * float(self.closed_orders[i].price)
                    gain -= float(self.closed_orders[i].fee)
                
                fee += float(self.closed_orders[i].fee)
            
            self.gain = gain
            self.fee = fee
            self.gain_percent = gain * 100 / self.total_investment
        except Exception as e:
            print(f"Error updating gain: {e}")
            print(f"Closed orders: {self.closed_orders}")
    
    def start(self):
        try:
            print("\n\nInitializing...")
            self.init()

            # Fetch balances
            print("\n\nFetching balances...")
            self.fetch_balances()

            print(f"Account balances: {self.account_balances}")
            print(f"Account Trade Balances: {self.account_trade_balances}")
            print("Finished fetching balances.")

            print(f"\n\nOHLC: {self.latest_ohlc}")

            while self.latest_ohlc.close > self.stop_loss and self.latest_ohlc.close < self.take_profit:
                print("\n\nUpdating orders...")
                self.update_orders()
                print("Finished updating orders.")
                
                # Fetch balances
                print("\n\nFetching balances...")
                self.fetch_balances()

                print(f"Account balances: {self.account_balances}")
                print(f"Account Trade Balances: {self.account_trade_balances}")
                print("Finished fetching balances.")

                # TODO: Update the output

                # Wait for a certain amount of time
                print(f"\n\nSleeping for {self.latency} seconds...")
                print("=========================================")
                time.sleep(self.latency)
                print("Time:", datetime.now())
                self.get_realized_gain()
                print(self)

                # Get latest OHLC data
                print("\n\nFetching OHLC data...")

                self.fetch_latest_ohlc()

                print(f"\n\nOHLC: {self.latest_ohlc}")
            
        except KeyboardInterrupt as e:
            print("User ended execution of program.")
            print(f"Exporting SentimentBot to bot database as {self.name}.json...")
            self.stop()
            print(f"Successfully exported SentimentBot.")
        
        except Exception as e:
            print(f"SentimentBot: {self}")
            print(f"Grids: {self.grids}")
            print(f"Exporting SentimentBot to bot database as {self.name}.json...")
            self.stop()
            print(f"Successfully exported SentimentBot.")
            raise e
    
    def update_orders(self):
        # Fetch order info for each txid
        txid = ''
        for i in range(len(self.grids)):
            if self.grids[i].order.txid != '':
                txid += self.grids[i].order.txid + ','
        
        if txid != '':
            # Remove last comma in txid
            txid = txid[:-1]

            for attempt in range(self.max_error_count):
                try:
                    # The appropiate Kraken API endpoint might be get_trades_info() instead of get_orders_info()
                    orders_response = self.exchange.get_orders_info(txid, trades=True)
                    break
                except Exception as e:
                    print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                    if attempt == self.max_error_count - 1:
                        print(f"Failed to make API request after {self.max_error_count} attempts")
                        raise e
                    else:
                        time.sleep(self.error_latency)

            orders = orders_response.get('result')

            # Update each order
            for i in range(len(self.grids)):
                if self.grids[i].order.txid != '':
                    self.grids[i].order.update(orders.get(self.grids[i].order.txid, {}))
        
        # TODO: Implement
    
    def stop(self):
        self.to_json_file(f'app/bots/{self.name}.json')
    
    def restart(self):
        try:
            print("=========================================")
            print("Time:", datetime.now())
            self.get_realized_gain()
            print(self)

            # Get latest OHLC data
            print("\n\nFetching OHLC data...")

            self.fetch_latest_ohlc()

            print(f"\n\nOHLC: {self.latest_ohlc}")

            # Fetch balances
            print("\n\nFetching balances...")
            self.fetch_balances()

            print(f"Account balances: {self.account_balances}")
            print(f"Account Trade Balances: {self.account_trade_balances}")
            print("Finished fetching balances.")

            print(f"\n\nOHLC: {self.latest_ohlc}")

            while self.latest_ohlc.close > self.stop_loss and self.latest_ohlc.close < self.take_profit:
                print("\n\nUpdating orders...")
                self.update_orders()
                
                print("Finished updating orders.")

                print("\n\nGrids:")
                for i in range(len(self.grids)):
                    print(self.grids[i])
                
                # Fetch balances
                print("\n\nFetching balances...")
                self.fetch_balances()

                print(f"Account balances: {self.account_balances}")
                print(f"Account Trade Balances: {self.account_trade_balances}")
                print("Finished fetching balances.")

                # TODO: Update the output

                # Wait for a certain amount of time
                print(f"\n\nSleeping for {self.latency} seconds...")
                print("=========================================")
                time.sleep(self.latency)
                print("Time:", datetime.now())
                self.get_realized_gain()
                print(self)

                # Get latest OHLC data
                print("\n\nFetching OHLC data...")

                self.fetch_latest_ohlc()

                print(f"\n\nOHLC: {self.latest_ohlc}")
        
        except KeyboardInterrupt as e:
            print("User ended execution of program.")
            print(f"Exporting SentimentBot to bot database as {self.name}.json...")
            self.stop()
            print(f"Successfully exported SentimentBot.")
        
        except Exception as e:
            print(f"SentimentBot: {self}")
            print(f"Grids: {self.grids}")
            print(f"Exporting SentimentBot to bot database as {self.name}.json...")
            self.stop()
            print(f"Successfully exported SentimentBot.")
            raise e
