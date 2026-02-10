class PositionManager:
    def track_position(self, entry_price: float, quantity: float):
        """Track position with stop loss and take profit"""
        raise NotImplementedError
        
    def calculate_pnl(self, current_price: float) -> float:
        """Calculate profit/loss"""
        raise NotImplementedError