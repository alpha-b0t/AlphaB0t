class Position:
    def __init__(self, ticker: str, side: str, entry_price: float, quantity: float, status="Open", stop_loss=None, take_profit=None):
        self.classname = "Position"
        if side not in ("long", "short"):
            raise ValueError("side must be 'long' or 'short'")

        self.ticker = ticker
        self.side = side
        self.entry_price = float(entry_price)
        self.quantity = float(quantity)
        self.status = status
        self.stop_loss = stop_loss
        self.take_profit = take_profit
    
    def __repr__(self):
        return f"{{{self.classname} ticker: {self.ticker}, side: {self.side}, entry price: {self.entry_price}, quantity: {self.quantity}, status: {self.status}, stop loss: {self.stop_loss}, take profit: {self.take_profit}}}"

class PositionManager:
    def __init__(self):
        self.classname = "PositionManager"
        self.position = None
        self.realized_pnl: float = 0.0
        self.closed_positions = []
    
    def __repr__(self):
        return f"{{{self.classname} realized PnL: {self.realized_pnl}, num of closed positions: {len(self.closed_positions)}}}"

    def open_position(
        self,
        ticker: str,
        side: str,
        entry_price: float,
        quantity: float,
        status: str = "Open",
        stop_loss: float = None,
        take_profit: float = None,
    ):
        """Open a new position"""
        if self.position is not None:
            raise Exception("Position already open")

        self.position = Position(
            ticker=ticker,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            status=status
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

    def close_position(self, exit_price: float):
        """Close current position and realize PnL"""
        if self.position is None:
            return 0.0

        pnl = self._calculate_pnl(exit_price)
        self.realized_pnl += pnl
        self.position.status = "Closed"
        self.closed_positions += [self.position]
        self.position = None
        return pnl

    def calculate_pnl(self, current_price: float) -> float:
        """Unrealized PnL"""
        if self.position is None:
            return 0.0
        return self._calculate_pnl(current_price)

    def _calculate_pnl(self, price: float) -> float:
        if self.position.side == "long":
            return (price - self.position.entry_price) * self.position.quantity
        else:  # short
            return (self.position.entry_price - price) * self.position.quantity

    def check_exit_conditions(self, current_price: float) -> bool:
        """Return True if stop loss or take profit hit"""
        if self.position is None:
            return False

        if self.position.side == "long":
            if self.position.stop_loss and current_price <= self.position.stop_loss:
                return True
            if self.position.take_profit and current_price >= self.position.take_profit:
                return True
        else:  # short
            if self.position.stop_loss and current_price >= self.position.stop_loss:
                return True
            if self.position.take_profit and current_price <= self.position.take_profit:
                return True

        return False
