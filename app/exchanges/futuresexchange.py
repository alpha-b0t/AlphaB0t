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
    """Kraken Futures REST v3 exchange adapter.

    The public method names/signatures are kept compatible with the original
    project interface, while the implementation maps them onto Kraken Futures
    REST v3 endpoints.

    ``mode="test"`` uses Kraken's separate Futures demo environment.  It is
    not a validation flag: orders sent to the demo API are actually submitted
    to the demo account.
    """

    PROD_BASE_URL = "https://futures.kraken.com/derivatives/api/v3"
    DEMO_BASE_URL = "https://demo-futures.kraken.com/derivatives/api/v3"
    CHARTS_BASE_URL = "https://futures.kraken.com/api/charts/v1"
    HISTORY_BASE_URL = "https://futures.kraken.com/api/history/v3"

    def __init__(self, exchange_config: ExchangeConfig={}):
        super().__init__()
        self.classname = self.__class__.__name__

        if type(exchange_config) == dict:
            # Reloading via FuturesExchange.from_json().
            print(f"Reloading {self.classname}...")
            return

        self.exchange_config = {}
        assert exchange_config.mode.lower() in ["live", "test"]

        self.api_key = exchange_config.api_key
        self.api_sec = exchange_config.api_sec
        self.mode = exchange_config.mode.lower()

        self.api_base_url = (
            self.DEMO_BASE_URL if self.mode == "test" else self.PROD_BASE_URL
        )
        self.charts_base_url = (
            self.CHARTS_BASE_URL.replace(
                "https://futures.kraken.com",
                "https://demo-futures.kraken.com",
            )
            if self.mode == "test"
            else self.CHARTS_BASE_URL
        )
        self.history_base_url = (
            self.HISTORY_BASE_URL.replace(
                "https://futures.kraken.com",
                "https://demo-futures.kraken.com",
            )
            if self.mode == "test"
            else self.HISTORY_BASE_URL
        )

        self._nonce = 0
        self._session = __import__("requests").Session()

    def __repr__(self):
        api_key_display = "''" if getattr(self, "api_key", "") == "" else "******"
        api_sec_display = "''" if getattr(self, "api_sec", "") == "" else "******"
        return (
            f"{{{self.classname} api_key: {api_key_display}, "
            f"api_sec: {api_sec_display}, mode: {self.mode}, "
            f"api_base_url: {self.api_base_url}}}"
        )

    # ------------------------------------------------------------------
    # Low-level HTTP/authentication
    # ------------------------------------------------------------------

    def _next_nonce(self):
        """Return a strictly increasing millisecond nonce."""
        import time
        now = int(time.time() * 1000)
        self._nonce = max(now, self._nonce + 1)
        return str(self._nonce)

    @staticmethod
    def _encode_params(params):
        """URL-encode parameters exactly once, preserving insertion order."""
        import urllib.parse

        if not params:
            return ""
        return urllib.parse.urlencode(
            [(k, v) for k, v in params.items() if v is not None],
            doseq=True,
        )

    def get_signature(self, endpoint_path, nonce, post_data=""):
        """Generate Kraken Futures v3 ``Authent``.

        Since 30 September 2025 Kraken requires the new v3 algorithm:
        SHA256(urlencoded-post-data + nonce + endpoint path), followed by
        HMAC-SHA512 using the base64-decoded API secret.
        """
        import base64
        import hashlib
        import hmac

        message = (
            post_data.encode("utf-8")
            + str(nonce).encode("utf-8")
            + endpoint_path.encode("utf-8")
        )
        digest = hashlib.sha256(message).digest()
        secret = base64.b64decode(self.api_sec)
        return base64.b64encode(
            hmac.new(secret, digest, hashlib.sha512).digest()
        ).decode("utf-8")

    def _request(
        self,
        method,
        path,
        params=None,
        authenticated=False,
        base_url=None,
        timeout=15,
        headers=None,
    ):
        """Make a Futures REST request and return decoded JSON."""
        import requests

        params = dict(params or {})
        base_url = base_url or self.api_base_url
        url = base_url.rstrip("/") + "/" + path.lstrip("/")
        endpoint_path = "/" + path.lstrip("/")

        request_headers = {"Accept": "application/json"}
        if headers:
            request_headers.update(headers)

        if authenticated:
            if not self.api_key or not self.api_sec:
                raise ValueError("Kraken Futures API credentials are required.")

            nonce = self._next_nonce()
            post_data = self._encode_params(params)
            request_headers["APIKey"] = self.api_key
            request_headers["Authent"] = self.get_signature(
                endpoint_path, nonce, post_data
            )
            # Kraken's v3 auth flow does not require nonce as a parameter,
            # but does require it as an input to Authent.
            request_headers["Nonce"] = nonce

        try:
            if method.upper() == "GET":
                response = self._session.get(
                    url, params=params, headers=request_headers, timeout=timeout
                )
            elif method.upper() == "POST":
                response = self._session.post(
                    url, params=params, headers=request_headers, timeout=timeout
                )
            elif method.upper() == "PUT":
                response = self._session.put(
                    url, params=params, headers=request_headers, timeout=timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Kraken Futures request failed: {method.upper()} {path}: {exc}"
            ) from exc

        try:
            result = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"Kraken Futures returned non-JSON response "
                f"(HTTP {response.status_code}): {response.text[:500]}"
            ) from exc

        self.handle_response_errors(result)
        return result

    @staticmethod
    def handle_response_errors(result):
        """Raise a useful exception for Kraken Futures error responses."""
        if not isinstance(result, dict):
            return result

        if result.get("result") == "error":
            error = result.get("error") or result.get("errors")
            raise RuntimeError(f"Kraken Futures API error: {error}")

        # Some endpoints expose errors without result="error".
        errors = result.get("errors")
        if errors:
            raise RuntimeError(f"Kraken Futures API errors: {errors}")

        return result

    def public_request(self, uri_path, query_parameters=None):
        return self._request(
            "GET",
            uri_path,
            query_parameters,
            authenticated=False,
        )

    def authenticated_request(self, uri_path, data=None, method="GET"):
        return self._request(
            method,
            uri_path,
            data,
            authenticated=True,
        )

    def _history_request(self, path, params=None):
        return self._request(
            "GET",
            path,
            params,
            authenticated=True,
            base_url=self.history_base_url,
        )

    # ------------------------------------------------------------------
    # Public market data
    # ------------------------------------------------------------------

    def get_exchange_time(self):
        # Futures market-data responses include Kraken's serverTime.
        # Unlike Spot, Futures does not document the Spot /0/public/Time
        # endpoint, so use a lightweight public market-data call.
        result = self.public_request("/tickers")
        return {
            "result": result.get("result", "success"),
            "serverTime": result.get("serverTime"),
        }

    def get_exchange_status(self):
        # Current Futures API exposes instrument status rather than the
        # Spot-style SystemStatus endpoint.
        try:
            return self.public_request("/instruments")
        except RuntimeError:
            return self.public_request("/tickers")

    def get_asset_info(
        self,
        asset: str,
        aclass: Optional[str] = None,
        expirationDate: Optional[str] = None,
        strikePrice: Optional[str] = None,
        futuresType: Optional[str] = None,
        info: Optional[str] = None,
    ):
        """Return Futures instrument metadata.

        ``asset`` is matched against symbol/underlying.  The extra arguments
        are accepted for compatibility with the Spot/options-style interface.
        """
        result = self.public_request("/instruments")
        instruments = result.get("instruments", [])

        if not asset:
            return result

        needle = asset.lower()
        matches = [
            item for item in instruments
            if needle in str(item.get("symbol", "")).lower()
            or needle in str(item.get("underlying", "")).lower()
            or needle == str(item.get("type", "")).lower()
        ]

        if info:
            matches = [
                item for item in matches
                if info.lower() in str(item).lower()
            ]

        return {
            "result": result.get("result", "success"),
            "instruments": matches,
            "serverTime": result.get("serverTime"),
        }

    def get_tradable_asset_pairs(
        self,
        pair: str,
        info: Optional[str] = None,
        expirationDate: Optional[str] = None,
        strikePrice: Optional[str] = None,
        futuresType: Optional[str] = None,
    ):
        """Return tradeable Futures contracts matching ``pair``."""
        result = self.public_request("/instruments")
        instruments = result.get("instruments", [])

        if pair:
            needle = pair.lower()
            instruments = [
                item for item in instruments
                if needle in str(item.get("symbol", "")).lower()
                or needle in str(item.get("underlying", "")).lower()
            ]

        instruments = [
            item for item in instruments
            if item.get("tradeable", True)
        ]

        if futuresType:
            instruments = [
                item for item in instruments
                if str(item.get("type", "")).lower() == futuresType.lower()
            ]

        return {
            "result": result.get("result", "success"),
            "instruments": instruments,
            "serverTime": result.get("serverTime"),
        }

    def get_ticker_info(self, symbol: str, info: Optional[str] = None):
        """Get one Futures ticker, or all tickers if symbol is empty."""
        if symbol:
            # Current API provides a dedicated ticker-by-symbol endpoint.
            try:
                return self.public_request(
                    "/ticker", {"symbol": symbol}
                )
            except RuntimeError:
                # Older v3 deployments expose only /tickers.
                result = self.public_request("/tickers")
                tickers = [
                    x for x in result.get("tickers", [])
                    if str(x.get("symbol", "")).lower() == symbol.lower()
                ]
                return {
                    "result": result.get("result", "success"),
                    "tickers": tickers,
                    "serverTime": result.get("serverTime"),
                }

        return self.public_request("/tickers")

    def get_ohlc_data(
        self,
        symbol: str,
        expirationDate: str = None,
        strikePrice: str = None,
        futuresType: str = None,
        interval: str = "hour",
        span: str = "week",
        bounds: str = "regular",
        info: Optional[str] = None,
    ):
        """Return Futures candles.

        For this adapter ``symbol`` is the Futures symbol.  ``interval`` may
        be e.g. ``1m``, ``5m``, ``1h``, ``1d``; ``span`` is accepted for
        compatibility but is not itself sent to Kraken.
        """
        tick_type = "trade"
        if bounds in {"mark", "spot", "trade"}:
            tick_type = bounds

        resolution_map = {
            "minute": "1m",
            "1minute": "1m",
            "5minute": "5m",
            "15minute": "15m",
            "30minute": "30m",
            "hour": "1h",
            "4hour": "4h",
            "12hour": "12h",
            "day": "1d",
            "week": "1w",
        }
        resolution = resolution_map.get(str(interval).lower(), interval)

        # API charts use epoch seconds.
        import time
        now = int(time.time())
        span_seconds = {
            "hour": 3600,
            "day": 86400,
            "week": 7 * 86400,
            "month": 30 * 86400,
            "year": 365 * 86400,
        }.get(str(span).lower())

        params = {"from": now - span_seconds, "to": now} if span_seconds else {}
        return self._request(
            "GET",
            f"/{tick_type}/{symbol}/{resolution}",
            params,
            authenticated=False,
            base_url=self.charts_base_url,
        )

    def get_order_book(self, symbol: str, info: Optional[str] = None):
        """Fetch the Futures order book."""
        params = {"symbol": symbol} if symbol else {}
        return self.public_request("/orderbook", params)

    def get_recent_trades(
        self,
        symbol: str,
        interval: str = "5minute",
        span: str = "day",
        bounds: str = "trading",
        info: Optional[str] = None,
    ):
        """Fetch recent public Futures trades."""
        params = {"symbol": symbol}
        if info:
            params["lastTime"] = info
        return self.public_request("/history", params)

    def get_recent_spreads(self, symbol: str):
        """Fetch recent bid/ask spread analytics for a Futures symbol."""
        import time

        now = int(time.time())
        return self._request(
            "GET",
            f"/analytics/{symbol}/spreads",
            {"since": now - 3600, "interval": 60, "to": now},
            authenticated=False,
            base_url=self.charts_base_url,
        )

    # ------------------------------------------------------------------
    # Trading
    # ------------------------------------------------------------------

    def add_order(
        self,
        symbol: str,
        quantity: int,
        expirationDate: str = None,
        strike: float = None,
        futuresType: str = None,
        price: float = None,
        side: str = "buy",
        positionEffect: str = "open",
        timeInForce: str = "gtc",
        creditOrDebit: Optional[str] = None,
        account_number: Optional[str] = None,
        jsonify: bool = True,
        **kwargs,
    ):
        """Place a Futures order.

        The original adapter signature is retained.  ``symbol`` must be the
        actual Kraken Futures symbol (e.g. ``PI_XBTUSD``).

        Additional Kraken parameters can be supplied through ``kwargs``:
        ``orderType``, ``limitPrice``, ``stopPrice``, ``cliOrdId``,
        ``triggerSignal``, ``reduceOnly``, ``processBefore``, ``algoId``,
        ``trailingStopMaxDeviation``, ``trailingStopDeviationUnit``,
        ``limitPriceOffsetValue`` and ``limitPriceOffsetUnit``.
        """
        if not symbol:
            raise ValueError("symbol is required")
        if quantity is None or float(quantity) <= 0:
            raise ValueError("quantity must be greater than zero")
        if side.lower() not in {"buy", "sell"}:
            raise ValueError("side must be 'buy' or 'sell'")

        # Map the legacy interface to Kraken's current order vocabulary.
        order_type = kwargs.pop("orderType", None)
        if order_type is None:
            tif = str(timeInForce).lower()
            order_type = "ioc" if tif == "ioc" else "lmt"

        payload = {
            "orderType": order_type,
            "symbol": symbol,
            "side": side.lower(),
            "size": quantity,
        }

        if price is not None:
            payload["limitPrice"] = price

        # A positionEffect of close is naturally represented by reduceOnly.
        if "reduceOnly" in kwargs:
            payload["reduceOnly"] = kwargs.pop("reduceOnly")
        else:
            payload["reduceOnly"] = str(positionEffect).lower() in {
                "close", "reduce", "reduceonly"
            }

        passthrough = {
            "limitPrice", "stopPrice", "cliOrdId", "triggerSignal",
            "processBefore", "trailingStopMaxDeviation",
            "trailingStopDeviationUnit", "limitPriceOffsetValue",
            "limitPriceOffsetUnit", "broker", "algoId",
        }
        for key in list(kwargs):
            if key in passthrough:
                payload[key] = kwargs.pop(key)

        # The legacy parameters cannot express Kraken Futures contract
        # expiration/strike because those are encoded in symbol.
        return self.authenticated_request(
            "/sendorder",
            payload,
            method="POST",
        )

    def add_order_batch(self, orders):
        """Submit a batch of Kraken Futures order-management actions.

        ``orders`` should be the structure expected by Kraken's batch endpoint.
        This intentionally does not reshape the caller's objects.
        """
        if not isinstance(orders, (list, tuple, dict)):
            raise TypeError("orders must be a list, tuple, or dict")

        import json

        batch = orders if isinstance(orders, dict) else {"batchOrder": list(orders)}
        payload = {"json": json.dumps(batch, separators=(",", ":"))}
        return self.authenticated_request(
            "/batchorder",
            payload,
            method="POST",
        )

    def edit_order(self, order_id: str, new_order_params: dict):
        """Edit an open order."""
        if not order_id:
            raise ValueError("order_id is required")
        payload = dict(new_order_params or {})
        payload.setdefault("orderId", order_id)
        return self.authenticated_request(
            "/editorder",
            payload,
            method="POST",
        )

    def cancel_order(self, order_id):
        """Cancel one open order by Kraken order ID."""
        if not order_id:
            raise ValueError("order_id is required")
        return self.authenticated_request(
            "/cancelorder",
            {"order_id": order_id},
            method="POST",
        )

    def cancel_order_batch(self, order_ids):
        """Cancel multiple orders using Kraken's batch order endpoint."""
        if not order_ids:
            return {"result": "success", "orders": []}

        # Kraken's batch endpoint supports cancel actions; accepting either
        # plain IDs or already-formed action objects makes this adapter useful
        # with both styles.
        actions = []
        for order_id in order_ids:
            if isinstance(order_id, dict):
                actions.append(order_id)
            else:
                actions.append({"order": "cancel", "order_id": order_id})

        return self.add_order_batch(actions)

    # ------------------------------------------------------------------
    # Account data
    # ------------------------------------------------------------------

    def get_account_balance(self):
        """Fetch Futures wallet/account balances."""
        return self.authenticated_request("/accounts")

    def get_extended_balance(self):
        """Return the complete Futures account structure."""
        return self.get_account_balance()

    def get_trade_balance(self, asset=None):
        """Return account collateral/equity information.

        Futures does not expose Spot's TradeBalance endpoint.  ``asset`` is
        retained for compatibility and, if supplied, filters the returned
        account dictionary by key where possible.
        """
        result = self.get_account_balance()
        if not asset:
            return result

        accounts = result.get("accounts", {})
        matches = {
            key: value
            for key, value in accounts.items()
            if asset.lower() in key.lower()
        }
        return {
            "result": result.get("result", "success"),
            "accounts": matches,
            "serverTime": result.get("serverTime"),
        }

    def get_open_orders(self):
        """Fetch all open Futures orders."""
        return self.authenticated_request("/openorders")

    def get_closed_orders(self):
        """Fetch historical order events, including closed orders."""
        return self._history_request("/orders")

    def get_orders_info(self, info: Optional[str] = None):
        """Fetch status for specific order IDs.

        ``info`` may be one order ID, a comma-separated list, or a list passed
        through the optional ``order_ids`` keyword in a future extension.
        """
        if not info:
            return self.get_open_orders()

        if isinstance(info, (list, tuple)):
            order_ids = list(info)
        else:
            order_ids = [x for x in str(info).split(",") if x]

        # Current Futures endpoint accepts orderIds as repeated query params.
        return self.authenticated_request(
            "/orders/status",
            {"orderIds": order_ids},
            method="POST",
        )

    def get_trades_info(self, info: Optional[str] = None):
        """Fetch current/recent user fills."""
        params = {}
        if info:
            params["lastFillTime"] = info
        return self.authenticated_request("/fills", params)

    def get_trades_history(self, info: Optional[str] = None):
        """Fetch historical execution events for the account."""
        params = {}
        if info:
            params["since"] = info
        return self._history_request("/executions", params)

    def get_trade_volume(self):
        """Return recent Futures fills and their aggregate contract volume.

        Kraken's Futures fee-schedule endpoints were deprecated in 2026.
        Consequently this method reports actual filled contract volume rather
        than pretending Futures has the old Spot ``TradeVolume`` response.
        """
        result = self.authenticated_request("/fills")
        fills = result.get("fills", [])
        total_size = sum(float(fill.get("size", 0) or 0) for fill in fills)
        return {
            "result": result.get("result", "success"),
            "fills": fills,
            "total_filled_contracts": total_size,
            "serverTime": result.get("serverTime"),
        }

    def get_holdings_and_bought_price(self):
        """Return open positions and their average/opening price."""
        result = self.authenticated_request("/openpositions")
        positions = result.get("openPositions", [])

        holdings = {}
        for position in positions:
            symbol = position.get("symbol")
            if symbol:
                holdings[symbol] = {
                    "side": position.get("side"),
                    "quantity": position.get("size", 0),
                    "bought_price": position.get("price"),
                    "fill_time": position.get("fillTime"),
                    "unrealized_funding": position.get("unrealizedFunding"),
                }

        return {
            "result": result.get("result", "success"),
            "holdings": holdings,
            "openPositions": positions,
            "serverTime": result.get("serverTime"),
        }

    def get_cash_and_equity(self):
        """Return the most useful cash/equity fields from Futures accounts."""
        result = self.get_account_balance()
        accounts = result.get("accounts", {})

        cash = 0.0
        equity = 0.0

        for account in accounts.values():
            auxiliary = account.get("auxiliary", {})
            # USD is the conventional quote/collateral field for USD Futures.
            cash += float(
                auxiliary.get("usd", auxiliary.get("pv", 0)) or 0
            )
            equity += float(
                auxiliary.get("pv", auxiliary.get("usd", 0)) or 0
            )

        return {
            "result": result.get("result", "success"),
            "cash": cash,
            "equity": equity,
            "accounts": accounts,
            "serverTime": result.get("serverTime"),
        }

    def get_holdings_capital(self):
        """Estimate current market value/notional of open Futures positions."""
        positions_result = self.authenticated_request("/openpositions")
        positions = positions_result.get("openPositions", [])

        instruments_result = self.public_request("/instruments")
        instruments = {
            str(x.get("symbol", "")).lower(): x
            for x in instruments_result.get("instruments", [])
        }

        values = {}
        total = 0.0

        for position in positions:
            symbol = position.get("symbol")
            if not symbol:
                continue

            size = abs(float(position.get("size", 0) or 0))
            instrument = instruments.get(symbol.lower(), {})
            contract_size = float(instrument.get("contractSize", 1) or 1)

            ticker = self.get_ticker_info(symbol)
            ticker_obj = ticker
            if "ticker" in ticker:
                ticker_obj = ticker["ticker"]
            elif ticker.get("tickers"):
                ticker_obj = ticker["tickers"][0] if ticker["tickers"] else {}

            price = (
                ticker_obj.get("markPrice")
                or ticker_obj.get("last")
                or ticker_obj.get("lastPrice")
                or ticker_obj.get("lastPrice")
                or position.get("price")
            )
            if price is None:
                continue
            price = float(price)

            instrument_type = str(instrument.get("type", "")).lower()
            if "inverse" in instrument_type:
                market_value = size * contract_size / price
            else:
                market_value = size * contract_size * price

            values[symbol] = {
                "side": position.get("side"),
                "size": size,
                "price": price,
                "contractSize": contract_size,
                "market_value": market_value,
            }
            total += market_value

        return {
            "result": positions_result.get("result", "success"),
            "holdings": values,
            "total": total,
            "serverTime": positions_result.get("serverTime"),
        }

    # ------------------------------------------------------------------
    # Safety helpers useful to a trading bot
    # ------------------------------------------------------------------

    def cancel_all_orders(self, symbol=None):
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self.authenticated_request(
            "/cancelallorders", params, method="POST"
        )

    def cancel_all_orders_after(self, timeout):
        return self.authenticated_request(
            "/cancelallordersafter",
            {"timeout": int(timeout)},
            method="POST",
        )
