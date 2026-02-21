import inspect
from constants import CLASS_NAMES
from config import RiskManagerConfig

class RiskManager:
    def __init__(self, riskmanager_config: RiskManagerConfig = {}):
        self.classname = self.__class__.__name__
        self.risk_per_trade = riskmanager_config.risk_per_trade
        self.max_position_pct = riskmanager_config.max_position_pct
        self.max_drawdown_pct = riskmanager_config.max_drawdown_pct

        self.peak_balance = riskmanager_config.portfolio_balance

    def validate_order(self, order: dict, balance: float) -> bool:
        """
        Validate:
        - drawdown has not been exceeded
        - position value does not exceed max_position_pct of balance
        - dollar risk on the trade does not exceed risk_per_trade of balance

        order must contain: 'price', 'quantity', 'stop_price'
        """
        if not self.check_drawdown(balance):
            return False

        position_value = order['price'] * order['quantity']

        if position_value > balance * self.max_position_pct:
            return False

        risk_amount = abs(order['price'] - order['stop_price']) * order['quantity']
        if risk_amount > balance * self.risk_per_trade:
            return False

        return True

    def calculate_max_position(self, balance: float) -> float:
        """Maximum capital allocation in dollars."""
        return balance * self.max_position_pct
    
    def calculate_position_size(
        self,
        balance: float,
        entry_price: float,
        side: str,  # 'long' or 'short'
    ):
        """
        Derive stop price and position size entirely from RiskManager parameters.

        Stop price is set so that if hit, the loss equals exactly risk_per_trade * balance.
        For a long:  stop_loss = entry_price * (1 - risk_per_trade)
        For a short: stop_loss = entry_price * (1 + risk_per_trade)

        Position size is then:
            quantity = risk_amount / risk_per_unit

        And is capped so the total position value never exceeds max_position_pct * balance.

        Returns quantity, stop_loss.
        """
        assert side in ['long', 'short']

        risk_amount = balance * self.risk_per_trade

        if side == 'long':
            stop_loss = entry_price * (1 - self.risk_per_trade)
        else:
            stop_loss = entry_price * (1 + self.risk_per_trade)

        risk_per_unit = abs(entry_price - stop_loss)

        if risk_per_unit == 0:
            return 0.0, stop_loss

        quantity = risk_amount / risk_per_unit

        # Cap against max position size
        max_quantity = self.calculate_max_position(balance) / entry_price
        quantity = min(quantity, max_quantity)

        return quantity, stop_loss

    def check_drawdown(self, current_balance: float) -> bool:
        """Returns False if drawdown exceeded"""
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance

        drawdown = (self.peak_balance - current_balance) / self.peak_balance if self.peak_balance > 0 else 0

        return drawdown <= self.max_drawdown_pct
    
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
