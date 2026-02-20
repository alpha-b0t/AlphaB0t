class RiskManager:
    def __init__(
        self,
        portfolio_balance: float,
        risk_per_trade: float = 0.01,      # 1%
        max_position_pct: float = 0.2,     # 20% of balance
        max_drawdown_pct: float = 0.15     # 15% max drawdown
    ):
        self.risk_per_trade = risk_per_trade
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct

        self.peak_balance = portfolio_balance

    def validate_order(self, order: dict, balance: float) -> bool:
        """
        Validate:
        - position size
        - risk per trade
        - drawdown
        """
        if not self.check_drawdown(balance):
            return False

        position_value = order["price"] * order["quantity"]

        # Check max position size
        if position_value > balance * self.max_position_pct:
            return False

        # Risk-based validation (if stop_loss provided)
        if "stop_loss" in order and order["stop_loss"]:
            risk_amount = abs(order["price"] - order["stop_loss"]) * order["quantity"]
            if risk_amount > balance * self.risk_per_trade:
                return False

        return True

    def calculate_max_position(self, balance: float) -> float:
        """Maximum capital allocation"""
        return balance * self.max_position_pct

    def calculate_position_size(
        self,
        balance: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """
        Position size based on risk per trade.
        """
        risk_amount = balance * self.risk_per_trade
        risk_per_unit = abs(entry_price - stop_loss)

        if risk_per_unit == 0:
            return 0.0

        return risk_amount / risk_per_unit

    def check_drawdown(self, current_balance: float) -> bool:
        """Returns False if drawdown exceeded"""
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance

        drawdown = (self.peak_balance - current_balance) / self.peak_balance if self.peak_balance > 0 else 0

        return drawdown <= self.max_drawdown_pct
