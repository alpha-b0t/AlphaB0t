from config import ExchangeConfig
import inspect
from constants import CLASS_NAMES
import robin_stocks.robinhood as rh
from app.strategies.helpers import round_down_to_cents
from typing import Optional

class OptionExchange:
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

class RobinhoodOptionExchange(OptionExchange):
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
    
    def login(self):
        try:
            rh.authentication.login(username=self.api_key, password=self.api_sec, store_session=False)
            print("successfully logged in")
        except Exception as e:
            print("login failed")
            raise e
    
    def logout(self):
        try:
            rh.authentication.logout()
            print("successfully logged out")
        except Exception as e:
            print("already logged out")
            raise e
    
    def get_exchange_time(self, market: str = "XNYS"):
        """
        Return today's market hours for the given market.

        Uses robin_stocks.robinhood.markets.get_market_today_hours, which is
        documented in the Robinhood "Getting Market Information" section
        (`get_market_today_hours` in [Robinhood Functions](https://robin-stocks.readthedocs.io/en/latest/robinhood.html)).
        """
        return rh.markets.get_market_today_hours(market)

    def get_exchange_status(self, market: str = "XNYS") -> str:
        """
        Check if the specified market is open or closed today.

        Wraps robin_stocks.robinhood.markets.get_market_today_hours and inspects
        the documented `is_open` field
        (`get_market_today_hours` in [Robinhood Functions](https://robin-stocks.readthedocs.io/en/latest/robinhood.html)).
        """
        hours = rh.markets.get_market_today_hours(market)
        return "Open" if hours.get("is_open") else "Closed"

    def get_asset_info(
        self,
        asset: str,
        aclass: Optional[str] = None,
        expirationDate: Optional[str] = None,
        strikePrice: Optional[str] = None,
        optionType: Optional[str] = None,
        info: Optional[str] = None,
    ):
        """Fetch option information for a given underlying symbol."""
        symbol = asset

        if expirationDate is None and strikePrice is None and optionType is None:
            return rh.options.get_chains(symbol, info=info)

        return rh.options.find_tradable_options(
            symbol=symbol,
            expirationDate=expirationDate,
            strikePrice=strikePrice,
            optionType=optionType,
            info=info,
        )

    def get_tradable_asset_pairs(
        self,
        pair: str,
        info: Optional[str] = None,
        expirationDate: Optional[str] = None,
        strikePrice: Optional[str] = None,
        optionType: Optional[str] = None,
    ):
        """Get tradable option contracts for an underlying symbol."""
        return rh.options.find_tradable_options(
            symbol=pair,
            expirationDate=expirationDate,
            strikePrice=strikePrice,
            optionType=optionType,
            info=info,
        )
    
    def get_ticker_info(self, symbol: str, info: Optional[str] = None):
        """Get quote information for the underlying stock ticker."""
        return rh.stocks.get_quotes(symbol, info=info)

    def get_ohlc_data(
        self,
        symbol: str,
        expirationDate: str,
        strikePrice: str,
        optionType: str,
        interval: str = "hour",
        span: str = "week",
        bounds: str = "regular",
        info: Optional[str] = None,
    ):
        """Fetch OHLC-style historical data for a specific option contract."""
        return rh.options.get_option_historicals(
            symbol=symbol,
            expirationDate=expirationDate,
            strikePrice=strikePrice,
            optionType=optionType,
            interval=interval,
            span=span,
            bounds=bounds,
            info=info,
        )

    def get_order_book(self, symbol: str, info: Optional[str] = None):
        """Fetch a level-II style order book for the underlying stock."""
        return rh.stocks.get_pricebook_by_symbol(symbol, info=info)

    def get_recent_trades(
        self,
        symbol: str,
        interval: str = "5minute",
        span: str = "day",
        bounds: str = "trading",
        info: Optional[str] = None,
    ):
        """Approximate recent trades via short-interval stock historical data."""
        return rh.stocks.get_stock_historicals(
            symbol, interval=interval, span=span, bounds=bounds, info=info
        )

    def get_recent_spreads(self, symbol: str):
        """Compute the current bid/ask spread for a stock from the pricebook."""
        book = rh.stocks.get_pricebook_by_symbol(symbol)
        bids = book.get("bids", []) or []
        asks = book.get("asks", []) or []

        best_bid = max((float(b["price"]) for b in bids), default=0.0)
        best_ask = min((float(a["price"]) for a in asks), default=0.0)

        return {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": best_ask - best_bid if best_ask and best_bid else 0.0,
        }

    def add_order(
        self,
        symbol: str,
        quantity: int,
        expirationDate: str,
        strike: float,
        optionType: str,
        price: float,
        side: str = "buy",
        positionEffect: str = "open",
        timeInForce: str = "gtc",
        creditOrDebit: Optional[str] = None,
        account_number: Optional[str] = None,
        jsonify: bool = True,
    ):
        """Place a limit order for an options contract."""
        if creditOrDebit is None:
            creditOrDebit = "debit" if side.lower() == "buy" else "credit"

        side_lower = side.lower()
        if side_lower == "buy":
            return rh.orders.order_buy_option_limit(
                positionEffect,
                creditOrDebit,
                price,
                symbol,
                quantity,
                expirationDate,
                strike,
                optionType=optionType,
                account_number=account_number,
                timeInForce=timeInForce,
                jsonify=jsonify,
            )
        elif side_lower == "sell":
            return rh.orders.order_sell_option_limit(
                positionEffect,
                creditOrDebit,
                price,
                symbol,
                quantity,
                expirationDate,
                strike,
                optionType=optionType,
                account_number=account_number,
                timeInForce=timeInForce,
                jsonify=jsonify,
            )
        else:
            raise ValueError("side must be either 'buy' or 'sell'")

    def add_order_batch(self, orders):
        """Add multiple orders at once."""
        # Robinhood does not natively support batch orders through this library
        results = []
        for order in orders:
            result = self.add_order(**order)
            results.append(result)
        return results

    def edit_order(self, order_id: str, new_order_params: dict):
        """
        Edit an existing option order by cancelling it and submitting a new one.

        Robinhood does not support in-place option order edits; the recommended
        pattern is cancel + re-create.
        """
        rh.orders.cancel_option_order(order_id)
        return self.add_order(**new_order_params)

    def cancel_order(self, order_id):
        """Cancel an order."""
        return rh.orders.cancel_option_order(order_id)

    def cancel_order_batch(self, order_ids):
        """Cancel a batch of orders."""
        results = []
        for order_id in order_ids:
            result = self.cancel_order(order_id)
            results.append(result)
        return results

    def get_account_balance(self):
        """Fetch high-level account balance information."""
        return rh.account.build_user_profile()

    def get_extended_balance(self):
        """Fetch extended balance/profile information (e.g. portfolio cash)."""
        return rh.profiles.load_account_profile(dataType="indexzero")
    
    def get_trade_balance(self, asset):
        """Fetch available cash that can be deployed for trading."""
        profile = rh.account.build_user_profile()
        return profile.get("cash")
    
    def get_open_orders(self):
        """Fetch all open option orders."""
        return rh.orders.get_all_open_option_orders()

    def get_closed_orders(self):
        """Fetch all closed option orders."""
        all_orders = rh.orders.get_all_option_orders()
        return [order for order in all_orders if order.get("state") != "open"]

    def get_orders_info(self, info: Optional[str] = None):
        """Fetch detailed information for all option orders."""
        return rh.orders.get_all_option_orders(info=info)

    def get_trades_info(self, info: Optional[str] = None):
        """Fetch detailed trade information for option orders."""
        return rh.orders.get_all_option_orders(info=info)

    def get_trades_history(self, info: Optional[str] = None):
        """Fetch historical option trade data."""
        return rh.orders.get_all_option_orders(info=info)

    def get_trade_volume(self):
        """Fetch the total volume of filled option contracts."""
        orders = rh.orders.get_all_option_orders()
        volume = 0.0
        for order in orders:
            if order.get("state") == "filled":
                try:
                    volume += float(order.get("quantity", 0))
                except (TypeError, ValueError):
                    continue
        return volume

    def get_holdings_and_bought_price(self):
        """Fetch all stock holdings and the average bought price."""
        positions = rh.account.get_all_positions()
        results = []
        for position in positions:
            instrument_url = position.get("instrument")
            symbol = rh.stocks.get_symbol_by_url(instrument_url) if instrument_url else None
            results.append(
                {
                    "symbol": symbol,
                    "quantity": position.get("quantity"),
                    "avg_price": position.get("average_buy_price"),
                }
            )
        return results

    def get_cash_and_equity(self):
        """Fetch cash and equity balances."""
        account_info = rh.account.build_user_profile()
        return {
            "cash": account_info.get("cash"),
            "equity": account_info.get("equity"),
        }

    def get_holdings_capital(self):
        """Fetch holdings balance using the market price."""
        holdings = rh.account.build_holdings()
        total_equity = 0.0
        for info in holdings.values():
            try:
                total_equity += float(info.get("equity", 0))
            except (TypeError, ValueError):
                continue

        return round_down_to_cents(total_equity)
