from bot import SpotGridTradingBot
from order import *

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

if __name__ == '__main__':
    config = {
        'crypto': 'ADA',
        'days_to_run': 7,
        'mode': 'test',
        'backtest': {
            'interval': '',
            'span': '',
            'bounds': '',
        },
        'upper_price': 0.3820,
        'lower_price': 0.3450,
        'level_num': 10,
        'cash': 100,
        'loss_threshold': 10.00,
        'loss_percentage': 10.00,
        'latency_in_sec': 60,
        'is_static': False,
        'send_to_discord': True,
        'discord_latency_in_hours': 0.25
    }
    
    if confirm_grids(config['upper_price'], config['lower_price'], config['level_num'], config['cash']):
        spot_grid_trader = SpotGridTradingBot(config)
        spot_grid_trader.run()
