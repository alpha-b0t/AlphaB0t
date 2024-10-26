class TA():
    def __init__(self):
        pass

    @staticmethod
    def MA(data, period):
        """
        Moving average.

        Parameters:
        data (list of float): List of data values.
        period (int): The size of the moving average window.

        Returns:
        list of float: Moving average values. The first (period - 1) values will be None.
        """
        if period <= 0:
            raise ValueError("Period must be a positive integer.")
        if period > len(data):
            raise ValueError("Period must not be greater than the length of the data list.")

        ma = []
        for i in range(len(data)):
            if i < period - 1:
                ma.append(None)  # Not enough data points for MA
            else:
                window = data[i - period + 1:i + 1]
                ma.append(sum(window) / period)

        return ma
