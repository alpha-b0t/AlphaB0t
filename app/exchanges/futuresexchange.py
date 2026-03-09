from config import ExchangeConfig
import inspect
from constants import CLASS_NAMES
import robin_stocks.robinhood as rh
from app.strategies.helpers import round_down_to_cents
from typing import Optional

class FuturesExchange:
    def __init__(self):
        self.classname = self.__class__.__name__

    def get_exchange_time(self):
        raise NotImplementedError("Not Implemented.")

    def get_exchange_status(self):
        raise NotImplementedError("Not Implemented.")

    def get_asset_info(self, asset, aclass):
        raise NotImplementedError("Not Implemented.")

    def get_tradable_asset_pairs(self, pair, info):
        raise NotImplementedError("Not Implemented.")

    def get_ticker_info(self, pair):
        raise NotImplementedError("Not Implemented.")

    def get_ohlc_data(self, pair, interval, since):
        raise NotImplementedError("Not Implemented.")

    def get_order_book(self, pair, count):
        raise NotImplementedError("Not Implemented.")

    def get_recent_trades(self, pair, since, count):
        raise NotImplementedError("Not Implemented.")

    def get_recent_spreads(self, pair, since):
        raise NotImplementedError("Not Implemented.")

    def add_order(self):
        raise NotImplementedError("Not Implemented.")

    def add_order_batch(self):
        raise NotImplementedError("Not Implemented.")

    def edit_order(self):
        raise NotImplementedError("Not Implemented.")

    def cancel_order(self):
        raise NotImplementedError("Not Implemented.")

    def cancel_order_batch(self):
        raise NotImplementedError("Not Implemented.")

    def get_account_balance(self):
        raise NotImplementedError("Not Implemented.")

    def get_extended_balance(self):
        raise NotImplementedError("Not Implemented.")

    def get_trade_balance(self, asset):
        raise NotImplementedError("Not Implemented.")

    def get_open_orders(self):
        raise NotImplementedError("Not Implemented.")

    def get_closed_orders(self):
        raise NotImplementedError("Not Implemented.")

    def get_orders_info(self):
        raise NotImplementedError("Not Implemented.")

    def get_trades_info(self):
        raise NotImplementedError("Not Implemented.")

    def get_trades_history(self):
        raise NotImplementedError("Not Implemented.")

    def get_trade_volume(self):
        raise NotImplementedError("Not Implemented.")

    def get_holdings_and_bought_price(self):
        raise NotImplementedError("Not Implemented.")

    def get_cash_and_equity(self):
        raise NotImplementedError("Not Implemented.")

    def get_holdings_capital(self):
        raise NotImplementedError("Not Implemented.")

    @classmethod
    def from_json(cls, json_data):
        # Get the parameters of the __init__ method
        init_params = inspect.signature(cls.__init__).parameters

        # Extract known attributes
        known_attributes = {param for param in init_params if param != 'self'}
        known_data = {k: v for k, v in json_data.items() if k in known_attributes}

        # Extract additional attributes
        additional_data = {k: v for k, v in json_data.items() if k not in known_attributes}

        # Create instance with known attributes
        instance = cls(**known_data)

        # Set additional attributes
        for key, value in additional_data.items():
            if isinstance(value, dict) and 'classname' in value and value['classname'] in CLASS_NAMES:
                exec(f'setattr(instance, key, {value["classname"]}.from_json(value))')
            else:
                setattr(instance, key, value)
        
        return instance

class KrakenFuturesExchange(FuturesExchange):
    def __init__(self, exchange_config: ExchangeConfig={}):
        super().__init__()
        self.classname = self.__class__.__name__
        if type(exchange_config) == dict:
            # Reloading
            print(f"Reloading {self.classname}...")
            return
        
        self.exchange_config = {}

        assert exchange_config.mode.lower() in ['live', 'test']
        self.api_key = exchange_config.api_key
        self.api_sec = exchange_config.api_sec
        self.mode = exchange_config.mode.lower()
    
    def __repr__(self):
        if self.api_key == '':
            api_key_display = "''"
        else:
            api_key_display = '******'
        
        if self.api_sec == '':
            api_sec_display = "''"
        else:
            api_sec_display = '******'
        
        return f"{{{self.classname} api_key: {api_key_display}, api_sec: {api_sec_display}, mode: {self.mode}}}"
    
    def get_exchange_time(self):
        raise NotImplementedError

    def get_exchange_status(self):
        raise NotImplementedError

    def get_asset_info(
        self,
        asset: str,
        aclass: Optional[str] = None,
        expirationDate: Optional[str] = None,
        strikePrice: Optional[str] = None,
        futuresType: Optional[str] = None,
        info: Optional[str] = None,
    ):
        """Fetch futures information for a given underlying symbol."""
        raise NotImplementedError

    def get_tradable_asset_pairs(
        self,
        pair: str,
        info: Optional[str] = None,
        expirationDate: Optional[str] = None,
        strikePrice: Optional[str] = None,
        futuresType: Optional[str] = None,
    ):
        """Get tradable futures contracts for an underlying symbol."""
        raise NotImplementedError
    
    def get_ticker_info(self, symbol: str, info: Optional[str] = None):
        """Get quote information for the underlying stock ticker."""
        raise NotImplementedError

    def get_ohlc_data(
        self,
        symbol: str,
        expirationDate: str,
        strikePrice: str,
        futuresType: str,
        interval: str = "hour",
        span: str = "week",
        bounds: str = "regular",
        info: Optional[str] = None,
    ):
        raise NotImplementedError

    def get_order_book(self, symbol: str, info: Optional[str] = None):
        """Fetch a level-II style order book for the underlying stock."""
        raise NotImplementedError

    def get_recent_trades(
        self,
        symbol: str,
        interval: str = "5minute",
        span: str = "day",
        bounds: str = "trading",
        info: Optional[str] = None,
    ):
        raise NotImplementedError

    def get_recent_spreads(self, symbol: str):
        raise NotImplementedError

    def add_order(
        self,
        symbol: str,
        quantity: int,
        expirationDate: str,
        strike: float,
        futuresType: str,
        price: float,
        side: str = "buy",
        positionEffect: str = "open",
        timeInForce: str = "gtc",
        creditOrDebit: Optional[str] = None,
        account_number: Optional[str] = None,
        jsonify: bool = True,
    ):
        """Place a limit order for a futures contract."""
        raise NotImplementedError

    def add_order_batch(self, orders):
        """Add multiple orders at once."""
        raise NotImplementedError

    def edit_order(self, order_id: str, new_order_params: dict):
        raise NotImplementedError

    def cancel_order(self, order_id):
        """Cancel an order."""
        raise NotImplementedError

    def cancel_order_batch(self, order_ids):
        """Cancel a batch of orders."""
        raise NotImplementedError

    def get_account_balance(self):
        """Fetch high-level account balance information."""
        raise NotImplementedError

    def get_extended_balance(self):
        """Fetch extended balance/profile information (e.g. portfolio cash)."""
        raise NotImplementedError
    
    def get_trade_balance(self, asset):
        """Fetch available cash that can be deployed for trading."""
        raise NotImplementedError
    
    def get_open_orders(self):
        """Fetch all open futures orders."""
        raise NotImplementedError

    def get_closed_orders(self):
        """Fetch all closed futures orders."""
        raise NotImplementedError

    def get_orders_info(self, info: Optional[str] = None):
        """Fetch detailed information for all futures orders."""
        raise NotImplementedError

    def get_trades_info(self, info: Optional[str] = None):
        """Fetch detailed trade information for futures orders."""
        raise NotImplementedError

    def get_trades_history(self, info: Optional[str] = None):
        """Fetch historical futures trade data."""
        raise NotImplementedError

    def get_trade_volume(self):
        """Fetch the total volume of filled futures contracts."""
        raise NotImplementedError

    def get_holdings_and_bought_price(self):
        """Fetch all positions and the average bought price."""
        raise NotImplementedError

    def get_cash_and_equity(self):
        """Fetch cash and equity balances."""
        raise NotImplementedError

    def get_holdings_capital(self):
        """Fetch holdings balance using the market price."""
        raise NotImplementedError
