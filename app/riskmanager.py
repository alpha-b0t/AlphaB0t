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
