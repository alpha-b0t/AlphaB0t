import math

def round_down_to_cents(value):
    """
    Converts a float to two decimal places and rounds down

    E.g.
    26.537 -> 26.53
    26.531 -> 26.53
    -26.539 -> -26.53
    """
    if value < 0:
        return math.ceil(value * 100)/100.0
    else:
        return math.floor(value * 100)/100.0