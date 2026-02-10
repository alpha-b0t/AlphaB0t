class RiskManager:
    def validate_order(self, order: dict) -> bool:
        """Validate order against risk rules"""
        raise NotImplementedError
        
    def calculate_max_position(self, balance: float) -> float:
        """Calculate maximum position size"""
        raise NotImplementedError
        
    def check_drawdown(self, current_balance: float) -> bool:
        """Check if drawdown limits are breached"""
        raise NotImplementedError