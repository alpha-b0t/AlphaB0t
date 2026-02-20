import inspect
import time
import json
from datetime import datetime
from constants import CLASS_NAMES
from app.helpers.json_util import CustomEncoder

# The following imports are needed for loading the objects from JSON
from app.exchanges.cmc_api import CoinMarketCapAPI
from app.exchanges.exchange import Exchange, KrakenExchange, CoinbaseExchange, RobinhoodCryptoExchange, RobinhoodOptionExchange
from app.strategies.grid import Grid
from app.strategies.ohlc import OHLC
from app.strategies.order import Order, KrakenOrder
from app.models.result import Result
from app.strategies.strategy import Strategy, GridStrategy, LSTMStrategy
from app.riskmanager import RiskManager
from app.positionmanager import PositionManager
from config import AppConfig, RequestConfig, BotConfig, GRIDBotConfig, CoinMarketCapAPIConfig, ExchangeConfig, StrategyConfig, RiskManagerConfig
# Don't need to import class inherited from Bot


class Bot():
    """
    General-purpose trading bot.
    Responsible for placing orders, executing strategy, managing risk through
    RiskManager, and monitoring orders and positions through PositionManager.
    """

    def __init__(
        self,
        bot_config: BotConfig = {},
        exchange: Exchange = {},
        strategy: Strategy = {},
        risk_manager: RiskManager = {},
    ):
        self.classname = self.__class__.__name__
        if type(bot_config) == dict:
            # Reloading from JSON
            return

        self.exchange = exchange
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.position_manager = PositionManager()

        self.name = bot_config.name
        self.pair = bot_config.pair
        self.mode = getattr(bot_config, 'mode', 'test')

        # Runtime bookkeeping
        self.start_time = time.time()
        self.is_running = False
        self.is_paused = False

        # P&L tracking
        self.realized_gain = 0.0
        self.fee = 0.0
        self.open_order_txid = None  # txid of the current open order (if any)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def run(self):
        """Main trading loop for the LSTM strategy bot."""
        print(f"[Bot] Starting {self.name} in {self.mode} mode...")
        self.is_running = True

        try:
            while self.is_running:
                if self.is_paused:
                    print("[Bot] Paused. Sleeping 5 s...")
                    time.sleep(5)
                    continue

                # 1. Get strategy signal
                signal = self.strategy.get_signal()
                print(f"[Bot] Signal: {signal} at {datetime.now()}")

                latest_ohlc = self.strategy.get_latest_ohlc()
                current_price = latest_ohlc.close

                # 2. Check exit conditions on open position
                if self.position_manager.check_exit_conditions(current_price):
                    print(f"[Bot] Exit condition triggered at price {current_price}. Closing position.")
                    self._close_position(current_price)

                # 3. Act on signal
                if signal == 'BUY' and self.position_manager.position is None:
                    self._open_long(current_price)
                elif signal == 'SELL' and self.position_manager.position is not None:
                    self._close_position(current_price)

                # 4. Log unrealized P&L
                unrealized = self.position_manager.calculate_pnl(current_price)
                print(f"[Bot] Unrealized PnL: {unrealized:.4f} | Realized: {self.realized_gain:.4f}")

                time.sleep(5)

        except KeyboardInterrupt:
            print("[Bot] Interrupted by user.")
        except Exception as e:
            print(f"[Bot] Error: {e}")
            raise
        finally:
            self.is_running = False
            self.stop()

    def _open_long(self, price: float):
        """Place a market buy order and open a position."""
        balance = self._get_balance()
        if balance is None:
            print("[Bot] Could not fetch balance; skipping BUY.")
            return

        quantity = self.risk_manager.calculate_position_size(
            balance=balance,
            entry_price=price,
            stop_loss=price * 0.98,  # 2% implicit stop-loss
        )
        max_qty = self.risk_manager.calculate_max_position(balance) / price
        quantity = min(quantity, max_qty)

        if quantity <= 0:
            print("[Bot] Calculated quantity is 0; skipping BUY.")
            return

        order = {"price": price, "quantity": quantity}
        if not self.risk_manager.validate_order(order, balance):
            print("[Bot] Risk manager rejected order.")
            return

        print(f"[Bot] Placing BUY order: {quantity:.6f} {self.pair} @ {price}")

        if self.mode == 'live':
            resp = self.exchange.add_order(
                ordertype='market',
                type='buy',
                volume=quantity,
                pair=self.pair,
            )
            txid = resp.get('result', {}).get('txid', [''])[0]
            self.open_order_txid = txid
        else:
            print("[Bot] (test mode - no real order placed)")

        self.position_manager.open_position(
            ticker=self.pair,
            side='long',
            entry_price=price,
            quantity=quantity,
            stop_loss=price * 0.98,
        )

    def _close_position(self, price: float):
        """Place a market sell order and close the position."""
        if self.position_manager.position is None:
            return

        quantity = self.position_manager.position.quantity
        print(f"[Bot] Placing SELL order: {quantity:.6f} {self.pair} @ {price}")

        if self.mode == 'live':
            self.exchange.add_order(
                ordertype='market',
                type='sell',
                volume=quantity,
                pair=self.pair,
            )
        else:
            print("[Bot] (test mode - no real order placed)")

        pnl = self.position_manager.close_position(price)
        self.realized_gain += pnl
        print(f"[Bot] Position closed. PnL this trade: {pnl:.4f}")

    def _get_balance(self) -> float:
        """Return available base-currency balance (or a simulated value in test mode)."""
        if self.mode != 'live':
            return 10000.0  # Simulated paper balance
        try:
            resp = self.exchange.get_account_balance()
            balances = resp.get('result', {})
            return float(balances.get('ZUSD', 0))
        except Exception as e:
            print(f"[Bot] Failed to fetch balance: {e}")
            return None

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def get_runtime(self) -> float:
        return time.time() - self.start_time

    def stop(self):
        """Persist bot state to disk."""
        self.is_running = False
        self.to_json_file(f'app/bots/local/{self.name}.json')
        print(f"[Bot] State saved to app/bots/local/{self.name}.json")

    def pause(self):
        self.is_paused = True
        print("[Bot] Paused.")

    def update(self):
        """Resume from paused state."""
        self.is_paused = False
        print("[Bot] Resumed.")

    def check_config(self):
        assert self.mode in ['live', 'test']

    # ------------------------------------------------------------------
    # P&L helpers
    # ------------------------------------------------------------------

    def get_account_asset_balance(self):
        return self._get_balance()

    def get_available_trade_balance(self):
        return self._get_balance()

    def fetch_balances(self):
        return self._get_balance()

    def fetch_latest_ohlc(self):
        return self.strategy.get_latest_ohlc()

    def fetch_latest_ohlc_pair(self, pair):
        raise NotImplementedError("Not Implemented.")

    def get_realized_gain(self) -> float:
        return self.realized_gain

    def get_unrealized_gain(self) -> float:
        if self.position_manager.position is None:
            return 0.0
        latest = self.strategy.get_latest_ohlc()
        return self.position_manager.calculate_pnl(latest.close)

    def simulate_trading(self):
        """Run strategy on historical data without placing real orders (paper mode)."""
        print("[Bot] Simulation not yet implemented for this strategy type.")

    # ------------------------------------------------------------------
    # Serialization (shared by all Bot subclasses)
    # ------------------------------------------------------------------

    def to_json_file(self, filename):
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        data = vars(self)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4, cls=CustomEncoder)

    @classmethod
    def from_json_file(cls, filename):
        with open(filename, 'r') as f:
            data = json.load(f)

        # Get the parameters of the __init__ method
        init_params = inspect.signature(cls.__init__).parameters

        # Extract known attributes
        known_attributes = {param for param in init_params if param != 'self'}
        known_data = {k: v for k, v in data.items() if k in known_attributes}

        # Extract additional attributes
        additional_data = {k: v for k, v in data.items() if k not in known_attributes}

        # Create instance with known attributes
        instance = cls(**known_data)

        # Set known attributes (to be safe)
        for key, value in known_data.items():
            setattr(instance, key, cls.recursive_object_creation(value))

        # Set additional attributes
        for key, value in additional_data.items():
            setattr(instance, key, cls.recursive_object_creation(value))

        return instance

    @classmethod
    def recursive_object_creation(cls, data):
        if isinstance(data, dict):
            if 'classname' in data and data['classname'] in CLASS_NAMES:
                print(f"CLASS_NAMES: data['classname']: {data['classname']}")
                try:
                    obj = globals()[data['classname']](*[data[attr] for attr in inspect.signature(globals()[data['classname']]).parameters.keys() if attr != 'self'])
                except KeyError as e:
                    print(f"\nglobals().keys(): {globals()}\n")
                    raise e
                for key, value in data.items():
                    if key != 'classname':
                        setattr(obj, key, cls.recursive_object_creation(value))
                return obj
            else:
                print(f"REGULAR: data: {data}")
                return {k: cls.recursive_object_creation(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.recursive_object_creation(item) for item in data]
        else:
            return data
