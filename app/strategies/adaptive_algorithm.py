import time
import random

def get_current_price(symbol):
    # Implement code to fetch the current price of a cryptocurrency from an API or exchange
    # Replace this with the appropriate API or exchange call
    return random.uniform(0.8, 1.2)  # Placeholder random price for demonstration

def place_order(symbol, price, quantity, side):
    # Implement code to place an order on the exchange or through an API
    # Replace this with the appropriate API or exchange call
    print(f"Placing {side} order for {quantity} {symbol} at ${price}")

def spot_grid_trading(symbol, grid_spacing, lower_price, upper_price, quantity):
    while True:
        current_price = get_current_price(symbol)
        if current_price > upper_price:
            place_order(symbol, current_price, quantity, "sell")
            upper_price += grid_spacing
        elif current_price < lower_price:
            place_order(symbol, current_price, quantity, "buy")
            lower_price -= grid_spacing
        time.sleep(10)  # Adjust the sleep interval based on your trading frequency

# Example usage
symbol = "BTC"  # Replace with the symbol of the cryptocurrency you want to trade
grid_spacing = 1000  # The price difference between each grid level
lower_price = 50000  # The lower boundary of the grid
upper_price = 60000  # The upper boundary of the grid
quantity = 0.01  # The quantity of cryptocurrency to trade at each grid level

spot_grid_trading(symbol, grid_spacing, lower_price, upper_price, quantity)
