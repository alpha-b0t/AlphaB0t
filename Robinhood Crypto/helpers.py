import math

def confirm_grids(upper_price, lower_price, level_num, cash):
    print("Please confirm you want the following:")
    for i in range(level_num-1, -1, -1):
        if i == level_num-1:
            print("=============================================")
            print('grid_' + str(i) + ':')
            print('\tprice: $' + str(upper_price - (level_num-1-i)*(upper_price-lower_price)/(level_num-1)))
            print('\tcash: $' + str(cash/level_num))
            print("=============================================")
        else:
            print('grid_' + str(i) + ':')
            print('\tprice: $' + str(upper_price - (level_num-1-i)*(upper_price-lower_price)/(level_num-1)))
            print('\tcash: $' + str(cash/level_num))
            print("=============================================")

    
    response = input("Yes/Y or No/N: ")
    while response not in ['Yes', 'yes', 'y', 'Y', 'No', 'no', 'n', 'N']:
        response = input("Yes/Y or No/N: ")
    
    if response in ['Yes', 'yes', 'y', 'Y']:
        return True
    else:
        return False

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

def get_precision(text):
    """
    Returns the number of decimal places the number has
    
    text needs to contain one and only one '1' and one and only one '.'
    
    E.g. text: output
    '100.000000000000': -2
    '10.0000000000000': -1
    '1.00000000000000': 0
    '0.10000000000000': 1
    '0.01000000000000': 2
    '0.00100000000000': 3
    '0.00010000000000': 4
    """
    one = text.find('1')
    dot = text.find('.')
    
    if one < dot:
        return one - dot + 1
    else:
        return one - dot

def round_to_min_order_price_increment(value, text):
    return round(value, get_precision(text))

def round_to_min_order_quantity_increment(value, text):
    return round(value, get_precision(text))

def display_time(seconds, granularity=5):
    result = []
    
    intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
    )

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    
    
    return ', '.join(result[:granularity])

def display_cash(available_cash):
    """
    Returns a string containing the available cash amount
    """
    if available_cash < 0:
        text = '-$'
    else:
        text = '$'
    
    text += str(abs(round(available_cash, 2)))

    return text

def display_crypto_equity_and_cash(available_cash, crypto_holdings_capital):
    value = round(available_cash + crypto_holdings_capital, 2)
    
    if value < 0:
        text = '-$'
    else:
        text = '$'
    
    text += str(abs(value))

    return text

def display_bought_price(bought_price):
    """
    Returns a string listing the name of the crypto and its associated average bought price
    """
    text = ''

    for crypto, bought_price in bought_price.items():
        text += '\t' + crypto + ' average bought price: $' + str(bought_price)

    return text

def display_profit(profit):

    if profit >= 0:
        text = '+$'
    else:
        text = '-$'

    text += str(abs(round_down_to_cents(profit)))

    return text

def display_percent_change(percent_change):
    if percent_change >= 0:
        text = '+'
    else:
        text = '-'

    text += str(abs(round(percent_change, 2)))
    text += '%'

    return text

def display_holdings(holdings, prices):
    """
    Returns a string listing the amount of crypto held and the latest price to be printed out
    """
    text = ''
    i = 0

    for crypto, amount in holdings.items():
        text += '\t' + str(amount) + ' ' + crypto + " at $" + str(prices[i])
        i += 1
    
    return text

def print_grids(grids, cash_per_level):
    for i in range(len(grids)-1, -1, -1):
        if i == len(grids)-1:
            print("=============================================")
            print('grid_' + str(i))
            print('\tprice: $' + str(grids['order_' + str(i)]['price']))
            print('\tside:', grids['order_' + str(i)]['side'])
            print('\tstatus:', grids['order_' + str(i)]['status'])
            try:
                print('\torder:', grids['order_' + str(i)]['order'])
            except KeyError:
                print('\torder:', None)
            print('\tcash: $' + str(cash_per_level))
            print("=============================================")
        else:
            print('grid_' + str(i))
            print('\tprice: $' + str(grids['order_' + str(i)]['price']))
            print('\tside:', grids['order_' + str(i)]['side'])
            print('\tstatus:', grids['order_' + str(i)]['status'])
            try:
                print('\torder:', grids['order_' + str(i)]['order'])
            except KeyError:
                print('\torder:', None)
            print('\tcash: $' + str(cash_per_level))
            print("=============================================")
    print("=============================================")