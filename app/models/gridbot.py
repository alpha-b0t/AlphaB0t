from app.models.exchange import Exchange, KrakenExchange, CoinbaseExchange, RobinhoodCryptoExchange
from app.models.grid import Grid
from app.models.ohlc import OHLC
from app.models.order import KrakenOrder
from app.helpers.format import round_down_to_cents
import time

class GRIDBot():
    def __init__(self, exchange, pair, days_to_run, mode, upper_price, lower_price, level_num, cash, stop_loss, take_profit):
        self.exchange = exchange
        self.pair = pair
        self.days_to_run = days_to_run
        self.mode = mode
        self.upper_price = upper_price
        self.lower_price = lower_price
        self.level_num = level_num
        self.cash = cash
        self.stop_loss = stop_loss
        self.take_profit = take_profit
    
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def pause(self):
        pass
    
    def resume(self):
        pass
    
    def update(self):
        pass

    def simulate_trading(self):
        pass

class KrakenGRIDBot(GRIDBot):
    def __init__(self, api_key, api_sec, pair, days_to_run, mode, upper_price, lower_price, level_num, cash, stop_loss, take_profit, base_currency, latency):
        self.exchange = KrakenExchange(api_key, api_sec, mode)

        self.pair = pair
        self.days_to_run = days_to_run
        self.mode = mode
        self.upper_price = upper_price
        self.lower_price = lower_price
        self.level_num = level_num
        self.cash = cash
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.base_currency = base_currency
        self.latency = latency

        asset_info_response = self.exchange.get_tradable_asset_pairs(self.pair)

        for key, value in asset_info_response['result'].items():
            pair_key = key
        
        asset_info = asset_info_response['result'][pair_key]

        # Price precision
        self.pair_decimals = asset_info['pair_decimals']

        # Volume precision in base currency
        self.lot_decimals = asset_info['lot_decimals']

        self.cost_decimals = asset_info['cost_decimals']
        self.ordermin = asset_info['ordermin']
        self.costmin = asset_info['costmin']
        self.tick_size = asset_info['tick_size']
        self.pair_status = asset_info['status']

        # TODO: Implement
        self.closed_orders = []
        self.profit = 0
        self.percent_change = 0
        self.fee = 0
        self.holdings = 0
        self.available_quote_currency_cash = 0

        self.check_config()
    
    def check_config(self):
        """Throws an error if the configurations are not correct."""
        # TODO: Implement
        assert self.mode in ['live', 'test']
        assert self.stop_loss > 0
        assert self.take_profit > 0
        assert self.take_profit > self.stop_loss
        assert self.days_to_run > 0
        assert self.cash > 0
        assert self.latency > 0
    
    def init_grid(self):
        """Initializes grids."""
        self.grids = []

        cash_per_level = round_down_to_cents(self.cash / self.level_num)

        # Determine what the prices are at each level
        prices = []
        for i in range(self.level_num):
            prices += [round(self.lower_price + i*(self.upper_price - self.lower_price)/(self.level_num-1), self.pair_decimals)]
        
        # Get latest OHLC data
        ohlc_response = self.exchange.get_ohlc_data(self.pair)

        ohlc = ohlc_response['result']

        keys = list(ohlc.keys())

        for i in range(len(keys)):
            if keys[i] != 'last':
                self.ohlc_asset_key = keys[i]
                break
        
        self.latest_ohlc = OHLC(ohlc[self.ohlc_asset_key][-1])

        # Mark orders as buys and sells
        side = []
        for i in range(self.level_num):
            if self.latest_ohlc.close > prices[i]:
                side += ['buy']
            else:
                side += ['sell']
        
        # Determine which grid line is closest to the current price
        min_dist = float('inf')
        self.closest_grid = -1

        for i in range(self.level_num):
            dist = abs(prices[i] - self.latest_ohlc.close)

            if dist < min_dist:
                min_dist = dist
                self.closest_grid = i
        
        # Mark the closest grid line as inactive
        status = ['active' for i in range(self.level_num)]
        status[self.closest_grid] = 'inactive'

        for i in range(self.level_num):
            self.grids += [Grid(i, prices[i], cash_per_level, side[i], status[i])]
        
        # Determine amount of dollars to buy initial amount of cryptocurrency
        grid_level_initial_buy_count = 0
        for i in range(len(self.grids)):
            if self.grids[i].side == 'sell' and self.grids[i].status == 'active':
                grid_level_initial_buy_count += 1
        
        initial_buy_amount = grid_level_initial_buy_count * cash_per_level

        # Place a buy order for the initial amount to sell
        print(f"Adding a buy order for {round(initial_buy_amount / self.latest_ohlc.close, self.lot_decimals)} {self.pair} @ limit {self.latest_ohlc.close}")

        self.exchange.add_order(
            ordertype='limit',
            type='buy',
            volume=round(initial_buy_amount / self.latest_ohlc.close, self.lot_decimals),
            pair=self.pair,
            price=self.latest_ohlc.close,
            oflags='post',
        )

        # Place limit buy orders and limit sell orders
        for i in range(len(self.grids)):
            if self.grids[i].status == 'active':
                if self.grids[i].side == 'buy':
                    side = 'buy'
                elif self.grids[i].side == 'sell':
                    side = 'sell'
                
                print(f"Adding a {side} order for {round(self.grids[i].cash_per_level/self.grids[i].limit_price, self.lot_decimals)} {self.pair} @ limit {self.grids[i].limit_price}")

                order_response = self.exchange.add_order(
                    ordertype='limit',
                    type=side,
                    volume=round(self.grids[i].cash_per_level/self.grids[i].limit_price, self.lot_decimals),
                    pair=self.pair,
                    price=self.grids[i].limit_price,
                    oflags='post'
                )

                self.grids[i].order = KrakenOrder(order_response.get('result', {}).get('txid', ''), order_response.get('result', {}))
            else:
                self.grids[i].order = KrakenOrder()
    
    def get_account_cash_balance(self, pair: str) -> float:
        """Retrieves the cash balance of the pair/currency, net of pending withdrawals."""
        account_balances = self.exchange.get_account_balance()
        
        return float(account_balances['result'].get(pair, 0))
    
    def get_available_trade_balance(self) -> dict:
        """Retrieves the balance(s) available for trading."""
        extended_balances = self.exchange.get_extended_balance()
        
        available_balances = {}

        for asset, extended_balance in extended_balances['result'].items():
            available_balances[asset] = extended_balance[asset]['balance'] + extended_balance[asset].get('credit', 0) - extended_balance[asset].get('credit_used', 0) - extended_balance[asset]['hold_trade']
        
        return available_balances
    
    def start(self):
        try:
            print("Initializing grid...")
            self.init_grid()

            print("Finished grid initialization.")
            print("\n\nGrids:")
            for i in range(len(self.grids)):
                print(self.grids[i])

            # TODO: Get balances

            print(f"\n\nOHLC: {self.latest_ohlc}")

            # TODO: Implement stop_loss check in while loop
            while self.latest_ohlc.close > self.stop_loss:
                print("\n\nUpdating orders...")
                self.update_orders()
                
                print("Finished updating orders.")
                print("\n\nGrids:")
                for i in range(len(self.grids)):
                    print(self.grids[i])
                # TODO: Get balances

                # TODO: Update the output

                # Wait for a certain amount of time
                print(f"\n\nSleeping for {self.latency} seconds...")
                print("=========================================")
                time.sleep(self.latency)

                # Get latest OHLC data
                print("\n\nFetching OHLC data...")
                ohlc_response = self.exchange.get_ohlc_data(self.pair)
                ohlc = ohlc_response.get('result')
                self.latest_ohlc = OHLC(ohlc[self.ohlc_asset_key][-1])
                print(f"\n\nOHLC: {self.latest_ohlc}")
            
        except KeyboardInterrupt as e:
            print("User ended execution of program.")
        
        except Exception as e:
            raise e
    
    def update_orders(self):
        # Fetch order info for each txid
        txid = ''
        for i in range(len(self.grids)):
            if self.grids[i].order.txid != '':

                if i != len(self.grids) - 1:
                    txid += self.grids[i].order.txid + ','
                else:
                    txid += self.grids[i].order.txid
        
        orders_response = self.exchange.get_orders_info(txid, trades=True)

        orders = orders_response.get('result')

        # Update each order
        for i in range(len(self.grids)):
            if self.grids[i].order.txid != '':
                self.grids[i].order.update(orders.get(self.grids[i].order.txid, {}))
        
        for i in range(len(self.grids)):
            if self.grids[i].status == 'active' and self.grids[i].order.txid != '':
                if self.grids[i].order.status == 'closed':
                    print(f"Order filled: {self.grids[i].order}")

                    if self.grids[i].side == 'buy':
                        # Add filled order to list of closed orders
                        self.closed_orders += [self.grids[i].order]
                        
                        # The filled order was a buy order, place a sell order on the level above it

                        # Set the filled level to inactive and adjust the closest grid
                        self.grids[i].status = 'inactive'
                        self.closest_grid = i

                        # Place a sell order on the grid line above it
                        if self.grids[i+1].status != 'inactive':
                            raise Exception('Unable to replace an open order with a new order.')
                        
                        self.grids[i+1].side = 'sell'
                        self.grids[i+1].status = 'active'

                        print(f"Adding a sell order for {round(self.grids[i+1].cash_per_level/self.grids[i+1].limit_price, self.lot_decimals)} {self.pair} @ limit {self.grids[i+1].limit_price}")

                        order_response = self.exchange.add_order(
                            ordertype='limit',
                            type='sell',
                            volume=round(self.grids[i+1].cash_per_level/self.grids[i+1].limit_price, self.lot_decimals),
                            pair=self.pair,
                            price=self.grids[i+1].limit_price,
                            oflags='post'
                        )

                        self.grids[i+1].order = KrakenOrder(order_response.get('result').get('txid', ''), order_response.get('result', {}))
                    else:
                        # Add filled order to list of closed orders
                        self.closed_orders += [self.grids[i].order]
                        
                        # The filled order was a sell order, place a buy order on the level below it

                        # Set the filled level to inactive and adjust the closest grid
                        self.grids[i].status = 'inactive'
                        self.closest_grid = i

                        # Place a buy order on the grid line below it
                        if self.grids[i-1].status != 'inactive':
                            raise Exception('Unable to replace an open order with a new order.')
                        
                        self.grids[i-1].side = 'buy'
                        self.grids[i-1].status = 'active'

                        print(f"Adding a buy order for {round(self.grids[i-1].cash_per_level/self.grids[i-1].limit_price, self.lot_decimals)} {self.pair} @ limit {self.grids[i-1].limit_price}")
                        
                        order_response = self.exchange.add_order(
                            ordertype='limit',
                            type='buy',
                            volume=round(self.grids[i-1].cash_per_level/self.grids[i-1].limit_price, self.lot_decimals),
                            pair=self.pair,
                            price=self.grids[i-1].limit_price,
                            oflags='post'
                        )

                        self.grids[i-1].order = KrakenOrder(order_response.get('result').get('txid', ''), order_response.get('result', {}))
    
    def stop(self):
        pass
    
    def pause(self):
        pass
    
    def resume(self):
        pass
    
    def update(self):
        pass

    def simulate_trading(self):
        pass
