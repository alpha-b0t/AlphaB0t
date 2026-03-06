import pytest

from app.bots.bot import Bot
from app.riskmanager import RiskManager
from app.positionmanager import PositionManager
from app.strategies.strategy import Strategy
from app.strategies.ohlc import OHLC
from config import BotConfig, ExchangeConfig, RiskManagerConfig, StrategyConfig


class DummyExchange:
    def __init__(self):
        # Use non-empty keys so Bot.fetch_balances() is exercised,
        # but all calls stay inside this dummy class.
        self.api_key = "dummy"
        self.api_sec = "dummy"
        self.mode = "test"
        self.add_order_calls = []

    # Minimal surface used by Bot.__init__
    def get_tradable_asset_pairs(self, pair):
        return {
            "result": {
                "XXBTZUSD": {
                    "pair_decimals": 2,
                    "lot_decimals": 2,
                    "cost_decimals": 2,
                    "ordermin": "0.01",
                    "costmin": "10.0",
                    "tick_size": "0.5",
                    "status": "online",
                }
            }
        }

    def get_trade_volume(self, pair):
        return {
            "result": {
                "volume": "1000.0",
                "fees": {"XXBTZUSD": {"fee": "0.26"}},
                "fees_maker": None,
            }
        }

    def get_account_balance(self):
        return {"result": {"ZUSD": "1000.0"}}

    def get_extended_balance(self):
        return {
            "result": {
                "ZUSD": {
                    "balance": "1000.0",
                    "credit": "0",
                    "credit_used": "0",
                    "hold_trade": "0",
                }
            }
        }

    def get_ohlc_data(self, pair):
        # Return a single OHLC candle
        return {
            "result": {
                "XXBTZUSD": [
                    [0, "100.0", "105.0", "95.0", "102.0", "101.0", "10.0", 1]
                ],
                "last": 0,
            }
        }

    def add_order(
        self,
        ordertype,
        type,
        volume,
        pair,
        price,
        oflags=None,
        closeordertype=None,
        closeprice=None,
        closeprice2=None,
        price2=None,
    ):
        call = {
            "ordertype": ordertype,
            "type": type,
            "volume": volume,
            "pair": pair,
            "price": price,
            "oflags": oflags,
            "closeordertype": closeordertype,
            "closeprice": closeprice,
            "closeprice2": closeprice2,
            "price2": price2,
        }
        self.add_order_calls.append(call)
        return {"result": {"txid": ["ABC123"]}}


class DummyStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.risk_to_reward_ratio = 2.0
        self._next_signal = "HOLD"

    def set_signal(self, signal: str):
        self._next_signal = signal

    def generate_signal(self):
        return self._next_signal

    def get_required_data(self):
        return []

    def update_indicators(self, new_data: dict):
        pass


def make_bot(signal: str = "HOLD") -> Bot:
    bot_config = BotConfig("tests/test.env")
    risk_config = RiskManagerConfig("tests/test.env")

    # Force test mode to avoid real-trading assertions.
    bot_config.mode = "test"

    exchange = DummyExchange()
    strategy = DummyStrategy()
    strategy.set_signal(signal)
    risk_manager = RiskManager(risk_config)

    bot = Bot(bot_config, exchange, strategy, risk_manager)
    # Ensure we have a fresh PositionManager object (and not modified elsewhere)
    bot.position_manager = PositionManager()
    return bot


def test_run_hold_does_not_open_position():
    bot = make_bot("HOLD")

    bot.run(max_iterations=1)

    assert bot.position_manager.position is None


def test_run_buy_opens_position_and_places_order():
    bot = make_bot("BUY")

    bot.run(max_iterations=1)

    # Check that a position was opened
    assert bot.position_manager.position is not None
    assert bot.position_manager.position.side == "long"

    # Check that at least one order was placed on the exchange
    assert len(bot.exchange.add_order_calls) >= 1


