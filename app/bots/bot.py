import inspect
from constants import CLASS_NAMES
import json
from app.helpers.json_util import CustomEncoder
import time
import uuid
import os

# The following imports are needed for loading the objects from JSON
from app.exchanges.cmc_api import CoinMarketCapAPI
from app.exchanges.exchange import Exchange, CoinbaseExchange, RobinhoodCryptoExchange
from app.exchanges.optionexchange import OptionExchange, RobinhoodOptionExchange
from app.strategies.grid import Grid
from app.strategies.ohlc import OHLC
from app.strategies.order import Order, KrakenOrder
from app.models.result import Result
from app.strategies.strategy import Strategy, GridStrategy, LSTMStrategy
from app.riskmanager import RiskManager
from app.positionmanager import PositionManager
from config import RequestConfig, BotConfig, GRIDBotConfig, CoinMarketCapAPIConfig, ExchangeConfig, StrategyConfig, RiskManagerConfig
# Don't need to import class inherited from Bot

class Bot():
    # Responsible for placing orders, executing strategy, managing risk through RiskManager, and monitoring orders and positions through PositionManager
    def __init__(self, bot_config: BotConfig={}, exchange: Exchange={}, strategy: Strategy={}, risk_manager: RiskManager={}):
        self.classname = self.__class__.__name__
        if type(bot_config) == dict and type(exchange) == dict and type(strategy) == dict and type(risk_manager) == dict:
            # Reloading
            print(f"Reloading {self.classname}...")
            return
        
        self.exchange = exchange
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.position_manager = PositionManager()

        self.name = bot_config.name
        self.pair = bot_config.pair
        self.mode = bot_config.mode
        self.base_currency = bot_config.base_currency
        self.latency = bot_config.latency_in_sec
        self.max_error_count = bot_config.max_error_count
        self.error_latency = bot_config.error_latency_in_sec
        self.cancel_orders_upon_exit = bot_config.cancel_orders_upon_exit

        # Generate a unique UUID for this bot
        self.uuid = str(uuid.uuid4())
        print(f"Generated Bot UUID: {self.uuid}")
        
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
        
        self.open_order_txids = []
        self.open_orders = []
        self.closed_orders = []
        self.realized_gain = 0
        self.realized_gain_percent = 0
        self.unrealized_gain = 0
        self.unrealized_gain_percent = 0
        self.fee = 0
        self.account_balances = {}

        # Fetch balances
        if self.exchange.api_key != '' and self.exchange.api_sec != '':
            self.fetch_balances()

        if self.mode != 'test':
            if self.risk_manager.peak_balance > self.account_trade_balances[self.base_currency]:
                raise Exception(f"Your stated portfolio balance, {self.risk_manager.peak_balance} {self.base_currency}, is greater than your balance of {self.base_currency} availabe for trading, {self.account_trade_balances[self.base_currency]}.")
    
    def __repr__(self):
        name_display = self.name if self.name else "''"
        realized = round(self.position_manager.realized_pnl, 4) if hasattr(self, 'position_manager') else 0
        unrealized = round(self.get_unrealized_gain(), 4)
        return (
            f"{{{self.__class__.__name__} name: {name_display}, pair: {self.pair}, "
            f"mode: {self.mode}, strategy: {self.strategy.__class__.__name__}, "
            f"runtime: {round(self.get_runtime())}s, "
            f"realized_pnl: {realized} {self.base_currency}, "
            f"unrealized_pnl: {unrealized} {self.base_currency}}}"
        )
    
    def run(self, max_iterations: int | None = None):
        """
        Strategy → generates signal
        ↓
        RiskManager → calculates position size
        ↓
        RiskManager → validates order
        ↓
        Exchange → executes order
        ↓
        PositionManager → tracks position
        ↓
        PositionManager → monitors stop/TP
        """

        print(f"\n{'='*50}")
        print(f"Bot '{self.name}' starting. Mode: {self.mode}")
        print(f"Pair: {self.pair} | Strategy: {self.strategy.__class__.__name__} | Exchange: {self.exchange.__class__.__name__}")
        print(f"Pulling every {self.latency}s")
        print(f"{'='*50}\n")

        try:
            iteration = 0
            while True:
                if max_iterations is not None and iteration >= max_iterations:
                    break

                # ── 1. Fetch latest price ──────────────────────────────────────
                self.fetch_latest_ohlc()
                print(f"\nCurrent price: {self.latest_ohlc.close}")
                
                # ── 2. Monitor open position stop/TP via PositionManager ───────
                if self.position_manager.position is not None:
                    unrealized = self.position_manager.calculate_pnl(self.latest_ohlc.close)
                    print(f"Open position unrealized PnL: {round(unrealized, 4)} {self.base_currency}")

                    if self.position_manager.check_exit_conditions(self.latest_ohlc.close):
                        print(f"Position exit condition met at {self.latest_ohlc.close}. Closing.")
                        pos = self.position_manager.position
                        order_type = 'sell' if pos.side == 'long' else 'buy'
                        quantity = pos.quantity
                        self.place_exit_order(
                            price=self.latest_ohlc.close,
                            order_type=order_type,
                            quantity=quantity,
                        )
                        pnl = self.position_manager.close_position(self.latest_ohlc.close)
                        print(f"Position closed. PnL: {round(pnl, 4)} {self.base_currency}")
                        print(f"Total realized PnL: {round(self.position_manager.realized_pnl, 4)} {self.base_currency}")
                        time.sleep(self.latency)
                        continue
                
                # ── 3. Generate signal ─────────────────────────────────────────
                strategy_signal = self.strategy.generate_signal()
                print(f"Signal: {strategy_signal}")

                assert strategy_signal in ['BUY', 'SELL', 'HOLD']

                if strategy_signal == 'HOLD':
                    time.sleep(self.latency)
                    continue

                # Skip if we already have an open position in the same direction
                if self.position_manager.position is not None:
                    existing_side = self.position_manager.position.side
                    if (strategy_signal == 'BUY' and existing_side == 'long') or \
                       (strategy_signal == 'SELL' and existing_side == 'short'):
                        print(f"  Already have a {existing_side} position. Skipping signal.")
                        time.sleep(self.latency)
                        continue

                    # Opposite signal: close existing position first
                    print(f"  Opposite signal received. Closing existing {existing_side} position.")
                    pos = self.position_manager.position
                    order_type = 'sell' if pos.side == 'long' else 'buy'
                    quantity = pos.quantity
                    self.place_exit_order(
                        price=self.latest_ohlc.close,
                        order_type=order_type,
                        quantity=quantity,
                    )
                    pnl = self.position_manager.close_position(self.latest_ohlc.close)
                    print(f"  Position closed. PnL: {round(pnl, 4)} {self.base_currency}")

                
                # ── 4. Fetch balance for sizing ────────────────────────────────
                self.fetch_balances()
                available_balance = self.account_trade_balances[self.base_currency]


                # ── 5. RiskManager: calculate position size ────────────────────
                side = 'long' if strategy_signal == 'BUY' else 'short'
                
                position_size, stop_loss = self.risk_manager.calculate_position_size(
                    balance=available_balance,
                    entry_price=self.latest_ohlc.close,
                    side=side
                )

                if position_size <= 0:
                    print(f"RiskManager returned zero position size. Skipping.")
                    time.sleep(self.latency)
                    continue

                # Enforce exchange minimum volume / notional constraints where possible
                notional = position_size * self.latest_ohlc.close
                if position_size < self.ordermin or round(notional, self.pair_decimals) < self.costmin:
                    print(
                        f"Position size ({position_size}) and/or notional ({round(notional, self.pair_decimals)}) below exchange minimums "
                        f"(ordermin={self.ordermin}, costmin={self.costmin}). Skipping."
                    )
                    time.sleep(self.latency)
                    continue

                take_profit = (abs(self.latest_ohlc.close - stop_loss) * self.strategy.risk_to_reward_ratio) + self.latest_ohlc.close


                # ── 6. RiskManager: validate order ─────────────────────────────
                # Construct order
                order_type = strategy_signal.lower()

                order_dict = {
                    'ordertype': 'limit',
                    'type': order_type,
                    'side': side,
                    'volume': position_size,
                    'price': self.latest_ohlc.close,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit
                }

                if not self.risk_manager.validate_order(order_dict, available_balance):
                    # RiskManager rejected order (drawdown / position size / risk limit). Skipping.
                    time.sleep(self.latency)
                    continue


                # ── 7. Execute order via Exchange ──────────────────────────────
                # Uses conditional close (stop-loss-limit) for downside protection on buys.
                print(f"Placing {strategy_signal} order | qty: {round(position_size, 6)} @ ~{self.latest_ohlc.close}")
                for attempt in range(self.max_error_count):
                    try:
                        # Spot / crypto flow (any Exchange subclass)
                        if isinstance(self.exchange, Exchange):
                            if order_dict['type'] == 'buy':
                                # Add a stop loss limit conditional close for downside protection
                                open_position_order_response = self.exchange.add_order(
                                    ordertype=order_dict['ordertype'],
                                    type=order_dict['type'],
                                    volume=order_dict['volume'],
                                    pair=self.pair,
                                    price=order_dict['price'],
                                    oflags='post',
                                    closeordertype='stop-loss-limit',
                                    closeprice=order_dict['price'],  # trigger price
                                    closeprice2=order_dict['stop_loss'],  # stop-loss limit
                                )
                            else:
                                open_position_order_response = self.exchange.add_order(
                                    ordertype=order_dict['ordertype'],
                                    type=order_dict['type'],
                                    volume=order_dict['volume'],
                                    pair=self.pair,
                                    price=order_dict['price'],
                                    oflags='post',
                                )
                        # Basic options flow (any OptionExchange subclass)
                        elif isinstance(self.exchange, OptionExchange):
                            # NOTE: This is a minimal starting implementation.
                            # It assumes `self.pair` is an option symbol understood by Robinhood
                            # and treats BUY as opening / increasing exposure and SELL as reducing it.
                            action = 'buy' if strategy_signal == 'BUY' else 'sell'
                            # Quantity must be an int for most options APIs
                            quantity = max(1, int(round(position_size)))
                            option_type = getattr(self, "option_type", "call")

                            open_position_order_response = self.exchange.add_order(
                                symbol=self.pair,
                                quantity=quantity,
                                option_type=option_type,
                                price=self.latest_ohlc.close,
                                action=action,
                            )
                        else:
                            raise Exception("Invalid Exchange: Exchange is not spot / crypto or option exchange")

                        break
                    except Exception as e:
                        print(f"Error making API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                        if attempt == self.max_error_count - 1:
                            print(f"Failed to make API request after {self.max_error_count} attempts")
                            raise e
                        else:
                            time.sleep(self.error_latency)
                
                # Normalize txid(s) and store them
                raw_txids = open_position_order_response.get('result', {}).get('txid', [])
                if isinstance(raw_txids, str):
                    open_position_txids = [raw_txids]
                else:
                    open_position_txids = list(raw_txids or [])

                self.open_order_txids.extend(open_position_txids)

                # Track the open order objects for introspection / debugging
                if open_position_txids:
                    # TODO: Abstract KrakenOrder into Order class
                    from app.strategies.order import KrakenOrder

                    for txid in open_position_txids:
                        self.open_orders.append(
                            KrakenOrder(txid=txid, order_data=open_position_order_response.get('result', {}))
                        )

                # Confirm order exists on the exchange before placing a separate TP order
                order_confirmed = False
                if open_position_txids:
                    txid_query = ",".join(open_position_txids)
                    for attempt in range(self.max_error_count):
                        try:
                            order_info = self.exchange.get_orders_info(txid_query, trades=False)
                            if order_info.get("result"):
                                order_confirmed = True
                            break
                        except Exception as e:
                            print(f"Error confirming open order (attempt {attempt + 1}/{self.max_error_count}): {e}")
                            if attempt == self.max_error_count - 1:
                                print("Proceeding without explicit confirmation of open order.")
                            else:
                                time.sleep(self.error_latency)

                # Place a separate order for TP once the main order is acknowledged
                if order_dict['type'] == 'buy':
                    # Only Exchange-style spot orders currently support a separate TP order.
                    if isinstance(self.exchange, Exchange):
                        if not order_confirmed:
                            print("Skipping separate TP order because base order could not be confirmed.")
                        else:
                            for attempt in range(self.max_error_count):
                                try:
                                    take_profit_type = 'sell'
                                    take_profit_order_response = self.exchange.add_order(
                                        ordertype="take-profit-limit",
                                        type=take_profit_type,
                                        volume=order_dict['volume'],
                                        pair=self.pair,
                                        price=order_dict['price'],  # trigger
                                        price2=order_dict['take_profit'],  # TP limit
                                        oflags='post',
                                    )
                                    break
                                except Exception as e:
                                    print(f"Error making TP API request (attempt {attempt + 1}/{self.max_error_count}): {e}")

                                    if attempt == self.max_error_count - 1:
                                        print(f"Failed to make TP order after {self.max_error_count} attempts")
                                        raise e
                                    else:
                                        time.sleep(self.error_latency)

                            take_profit_txid = take_profit_order_response.get('result', {}).get('txid', [])
                            if isinstance(take_profit_txid, str):
                                take_profit_txids = [take_profit_txid]
                            else:
                                take_profit_txids = list(take_profit_txid or [])

                            if take_profit_txids:
                                self.open_order_txids.extend(take_profit_txids)
                
                if len(self.open_order_txids) > 0:
                    print(f"Order(s) placed. txids: {self.open_order_txids}")
                else:
                    print(f"Order submitted (test mode — no txid returned).")


                # ── 8. PositionManager: open position ──────────────────────────
                # Add position to PositionManager
                self.position_manager.open_position(
                    ticker=self.pair,
                    side=side,
                    entry_price=self.latest_ohlc.close,
                    quantity=position_size,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )

                print("Position added")

                print(f"{self.position_manager}")

                time.sleep(self.latency)

                # PositionManager monitors stop/TP
                iteration += 1
        except KeyboardInterrupt as e:
            print(f"Unexpected error: {e}")
            print("User ended execution of program.")
            print(f"Exporting bot to database as {self.name}.json...")
            self.stop()
            print(f"Successfully exported bot.")
        
        except Exception as e:
            print(f"Unexpected error: {e}")
            print(f"Bot: {self}")
            print(f"Exporting bot to database as {self.name}.json...")
            self.stop()
            print(f"Successfully exported bot.")
            raise e
        
        print(f"\nBot '{self.name}' finished.")
        print(f"Total realized PnL: {round(self.position_manager.realized_pnl, 4)} {self.base_currency}")
        print(f"Closed positions: {len(self.position_manager.closed_positions)}")

    def place_exit_order(self, price: float, order_type: str, quantity: float):
        """
        Place a market exit order on the exchange to close an existing position.
        """
        print(f"Placing exit {order_type.upper()} order | qty: {round(quantity, 6)} @ ~{price}")

        for attempt in range(self.max_error_count):
            try:
                # Spot / crypto flow (any Exchange subclass)
                if isinstance(self.exchange, Exchange):
                    exit_order_response = self.exchange.add_order(
                        ordertype='market',
                        type=order_type,
                        volume=quantity,
                        pair=self.pair,
                        price=price,
                    )
                # Basic options flow (any OptionExchange subclass)
                elif isinstance(self.exchange, OptionExchange):
                    action = order_type
                    qty_int = max(1, int(round(quantity)))
                    option_type = getattr(self, "option_type", "call")
                    exit_order_response = self.exchange.add_order(
                        symbol=self.pair,
                        quantity=qty_int,
                        option_type=option_type,
                        price=price,
                        action=action,
                    )
                else:
                    raise Exception("Invalid Exchange: Exchange is not spot / crypto or option exchange")

                txids = exit_order_response.get('result', {}).get('txid', [])
                if isinstance(txids, list):
                    self.open_order_txids.extend(txids)
                elif txids:
                    self.open_order_txids.append(txids)

                if txids:
                    print(f"Exit order placed. txids: {txids}")
                else:
                    print("Exit order submitted (test mode — no txid returned).")
                break
            except Exception as e:
                print(f"Error placing exit order (attempt {attempt + 1}/{self.max_error_count}): {e}")

                if attempt == self.max_error_count - 1:
                    print(f"Failed to place exit order after {self.max_error_count} attempts")
                    raise e
                else:
                    time.sleep(self.error_latency)

    def get_runtime(self):
        return time.time() - self.start_time
    
    def check_config(self):
        """Throws an error if the configurations are not correct."""
        # TODO: Implement
        assert self.mode in ['live', 'test']
        assert self.latency > 0
        assert self.max_error_count >= 1
        assert self.error_latency > 0
    
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
        if hasattr(self, "ohlc_asset_key"):
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
        else:
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

            for key in ohlc.keys():
                if key != 'last':
                    pair_key = key
                    break
            
            self.ohlc_asset_key = pair_key

            self.latest_ohlc = OHLC(ohlc[pair_key][-1])
    
    def get_realized_gain(self):
        return self.position_manager.realized_pnl
    
    def get_unrealized_gain(self):
        self.fetch_latest_ohlc()
        return self.position_manager.calculate_pnl(self.latest_ohlc.close)
    
    def stop(self):
        # First remove LSTM model from LSTMStrategy due to not being able to export LSTM model
        if self.strategy.classname == "LSTMStrategy" and hasattr(self.strategy, "model"):
            del self.strategy.model
        self.to_json_file(f'app/bots/local/{self.name}.json')
    
    def pause(self):
        raise NotImplementedError("Not Implemented.")
    
    def update(self):
        raise NotImplementedError("Not Implemented.")
    
    def simulate_trading(self):
        raise NotImplementedError("Not Implemented.")
    
    def to_json_file(self, filename):
        # Ensure the folder exists
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
                # If the data is a dictionary with a 'classname' key, create an instance of the class
                try:
                    obj = globals()[data['classname']](*[data[attr] for attr in inspect.signature(globals()[data['classname']]).parameters.keys() if attr != 'self'])
                except KeyError as e:
                    print(f"\nglobals().keys(): {globals()}\n")
                    # print(f"globals()[data['classname']]: {globals()[data['classname']]}")
                    raise e
                for key, value in data.items():
                    if key != 'classname':
                        # Recursively set additional attributes
                        setattr(obj, key, cls.recursive_object_creation(value))
                return obj
            else:
                print(f"REGULAR: data: {data}")
                # If the data is a regular dictionary, recursively handle its values
                return {k: cls.recursive_object_creation(v) for k, v in data.items()}
        elif isinstance(data, list):
            # If the data is a list, recursively handle each element in the list
            return [cls.recursive_object_creation(item) for item in data]
        else:
            # Base case: return data as is
            return data
