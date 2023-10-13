# spot-grid-trading-bot

## Useful links
- https://medium.com/coinmonks/what-is-a-grid-trading-bot-3b58f3ec059b#:~:text=Grid%20Trading%20Bot%20is%20a,grid%20level%2C%20and%20vice%20versa.
- https://levelup.gitconnected.com/creating-a-crypto-trading-bot-for-fun-and-profit-fbf8d74de8c6

## Profitable grid parameters
1. 2023-10-13
CRYPTO=LINK
BACKTEST_INTERVAL=day
BACKTEST_SPAN=3month
BACKTEST_BOUNDS=24_7
UPPER_PRICE=8.30
LOWER_PRICE=5.90
LEVEL_NUM=6

backtesting results:
{'initial_cash_balance': 1000, 'initial_crypto_equity': 0, 'initial_balance': 1000, 'final_cash_balance': 666.6800000000001, 'final_crypto_equity': 60.05000000000002, 'final_balance': 1098.79, 'current_cash_balance': 666.6800000000001, 'current_crypto_equity': 60.05000000000002, 'profit': 103.72000000000003, 'percent_change': 10.372000000000003, 'crypto': 'LINK', 'interval': 'day', 'span': '3month', 'bounds': '24_7'}

2. 2023-10-13
CRYPTO=LINK
BACKTEST_INTERVAL=day
BACKTEST_SPAN=year
BACKTEST_BOUNDS=24_7
UPPER_PRICE=8.10
LOWER_PRICE=5.25
LEVEL_NUM=4

backtesting results:
{'initial_cash_balance': 1000, 'initial_crypto_equity': 0, 'initial_balance': 1000, 'final_cash_balance': 1000.0, 'final_crypto_equity': 51.09000000000002, 'final_balance': 1367.6399999999999, 'current_cash_balance': 1000.0, 'current_crypto_equity': 51.09000000000002, 'profit': 418.3699999999999, 'percent_change': 41.83699999999998, 'crypto': 'LINK', 'interval': 'day', 'span': 'year', 'bounds': '24_7'}

## Example .env file
```
CRYPTO=LINK
DAYS_TO_RUN=30
MODE=test
BACKTEST_INTERVAL=day
BACKTEST_SPAN=year
BACKTEST_BOUNDS=24_7
UPPER_PRICE=8.10
LOWER_PRICE=5.25
LEVEL_NUM=4
CASH=1000
LOSS_THRESHOLD=100
LOSS_PERCENTAGE=10
LATENCY_IN_SEC=5.00
SEND_TO_DISCORD=false
DISCORD_LATENCY_IN_HOURS=0.25
DISCORD_URL="discord_url"
MAX_ERROR_COUNT=5
ERROR_LATENCY_IN_SEC=5
INIT_BUY_ERROR_LATENCY_IN_SEC=5
INIT_BUY_ERROR_MAX_COUNT=10
CANCEL_ORDERS_UPON_EXIT=none
```