class Position:
    def __init__(self, side, entry_price, quantity, stop_loss=None, take_profit=None):
        self.side = side # "long" or "short"
        self.entry_price = entry_price
        self.quantity = quantity
        self.stop_loss = stop_loss
        self.take_profit = take_profit

class PositionManager:
    def __init__(self):
        self.position = None
        self.realized_pnl: float = 0.0

    def track_position(
        self,
        side: str,
        entry_price: float,
        quantity: float,
        stop_loss: float = None,
        take_profit: float = None,
    ):
        """Open a new position"""
        if self.position is not None:
            raise Exception("Position already open")

        self.position = Position(
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

    def close_position(self, exit_price: float):
        """Close current position and realize PnL"""
        if self.position is None:
            return 0.0

        pnl = self._calculate_pnl(exit_price)
        self.realized_pnl += pnl
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
