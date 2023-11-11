class OHLC:
    def __init__(self, ohlc_data: list):
        self.time = ohlc_data[0]
        self.open = float(ohlc_data[1])
        self.high = float(ohlc_data[2])
        self.low = float(ohlc_data[3])
        self.close = float(ohlc_data[4])
        self.vwap = float(ohlc_data[5])
        self.volume = float(ohlc_data[6])
        self.count = ohlc_data[7]
