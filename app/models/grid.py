class Grid():
    def __init__(self, level_num, limit_price, cash_per_level, side, status, order=None):
        self.level_num = level_num
        self.limit_price = limit_price
        self.cash_per_level = cash_per_level
        self.side = side
        self.status = status
        self.order = None
