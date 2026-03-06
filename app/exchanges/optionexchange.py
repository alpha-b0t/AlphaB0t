from config import ExchangeConfig
import inspect
from constants import CLASS_NAMES
import robin_stocks.robinhood as rh
from app.strategies.helpers import round_down_to_cents

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
    
    def get_exchange_time(self):
        """Returns the current exchange time (as string)."""
        return rh.stocks.get_market_hours()

    def get_exchange_status(self):
        """Check if the exchange is open or closed."""
        market_hours = rh.markets.get_market_hours()
        if market_hours['is_open']:
            return "Open"
        else:
            return "Closed"

    def get_asset_info(self, pair):
        """Fetch asset information for a given option."""
        return rh.options.get_option_instrument_data(pair)

    def get_tradable_asset_pairs(self, pair, info):
        """Get tradable asset pairs."""
        return rh.options.find_tradable_options(symbol=pair)
    
    def get_ticker_info(self, pair):
        """Get ticker info for a given asset pair."""
        return rh.options.get_option_instrument_data(pair)

    def get_ohlc_data(self, pair, expirationDate, strikePrice, optionType):
        """Fetch OHLC (Open, High, Low, Close) data."""
        return rh.options.get_option_market_data(pair, expirationDate, strikePrice, optionType)

    def get_order_book(self, pair, count):
        """Fetch order book for an asset pair."""
        # Robinhood API does not support direct order books, you could adapt this method.
        return rh.options.get_option_instrument_data(pair)  # Placeholder for now.

    def get_recent_trades(self, pair, since, count):
        """Fetch recent trades."""
        return rh.stocks.get_recent_trades(pair, count)

    def get_recent_spreads(self, pair, since):
        """Fetch recent spreads."""
        # Robinhood API does not directly provide spread data, needs alternative calculation
        return rh.options.get_option_instrument(pair)  # Placeholder for now.

    def add_order(self, symbol, quantity, option_type, price, action):
        """Place an order for options trading."""
        """
        robin_stocks.robinhood.orders.order_buy_option_limit(positionEffect, creditOrDebit, price, symbol, quantity, expirationDate, strike, optionType='both', account_number=None, timeInForce='gtc', jsonify=True)[source]
        Submits a limit order for an option. i.e. place a long call or a long put.

        Parameters:
        positionEffect (str) – Either ‘open’ for a buy to open effect or ‘close’ for a buy to close effect.

        creditOrDebit (str) – Either ‘debit’ or ‘credit’.

        price (float) – The limit price to trigger a buy of the option.

        symbol (str) – The stock ticker of the stock to trade.

        quantity (int) – The number of options to buy.

        expirationDate (str) – The expiration date of the option in ‘YYYY-MM-DD’ format.

        strike (float) – The strike price of the option.

        optionType (str) – This should be ‘call’ or ‘put’

        account_number (Optional[str]) – the robinhood account number.

        timeInForce (Optional[str]) – Changes how long the order will be in effect for. ‘gtc’ = good until cancelled. ‘gfd’ = good for the day. ‘ioc’ = immediate or cancel. ‘opg’ execute at opening.

        jsonify (Optional[str]) – If set to False, function will return the request object which contains status code and headers.

        Returns:
        Dictionary that contains information regarding the buying of options, such as the order id, the state of order (queued, confired, filled, failed, canceled, etc.), the price, and the quantity.
        """
        if action == "buy":
            return rh.options.order_buy_option_limit(symbol, quantity, price)
        elif action == "sell":
            return rh.options.order_sell_option_limit(symbol, quantity, price)
        return None

    def add_order_batch(self, orders):
        """Add multiple orders at once."""
        # Robinhood does not natively support batch orders through this library
        results = []
        for order in orders:
            result = self.add_order(**order)
            results.append(result)
        return results

    def edit_order(self, order_id, new_price):
        """Edit an existing order."""
        return rh.orders.update_option_order(order_id, price=new_price)

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
        """Fetch account balance."""
        return rh.account.get_account()

    def get_extended_balance(self):
        """Fetch extended balance (cash, buying power, margin)."""
        return rh.account.get_margin()
    
    def get_trade_balance(self, asset):
        """Fetch trade balance for a given asset."""
        return rh.stocks.get_balance(asset)
    
    def get_open_orders(self):
        """Fetch all open orders."""
        return rh.orders.get_all_open_option_orders()

    def get_closed_orders(self):
        """Fetch all closed orders."""
        return rh.orders.get_all_closed_orders()

    def get_orders_info(self):
        """Fetch detailed information for all orders."""
        return rh.orders.get_all_option_positions()

    def get_trades_info(self):
        """Fetch detailed trade information."""
        return rh.stocks.get_all_trades()

    def get_trades_history(self):
        """Fetch historical trade data."""
        return rh.stocks.get_trade_history()

    def get_trade_volume(self):
        """Fetch the total volume of trades."""
        # No direct Robinhood method, but could be calculated from trade history.
        raise NotImplementedError

    def get_holdings_and_bought_price(self):
        """Fetch all holdings and the average bought price."""
        holdings = rh.stocks.get_all_positions()
        return [{"symbol": position['instrument']['symbol'], 
                 "quantity": position['quantity'], 
                 "avg_price": position['average_buy_price']} for position in holdings]

    def get_cash_and_equity(self):
        """Fetch cash and equity balances."""
        account_info = rh.account.get_account()
        return {
            "cash": account_info['cash'],
            "equity": account_info['equity']
        }

    def get_holdings_capital(self):
        """Fetch holdings balance using the market price."""
        capital = 0.00
        
        for asset_name, amount in self.holdings.items():
            capital += amount * float(self.get_latest_quote(asset_name)['mark_price'])
        
        return round_down_to_cents(capital)
