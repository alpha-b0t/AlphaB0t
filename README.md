# spot-grid-trading-bot

## Useful links
- https://medium.com/coinmonks/what-is-a-grid-trading-bot-3b58f3ec059b#:~:text=Grid%20Trading%20Bot%20is%20a,grid%20level%2C%20and%20vice%20versa.
- https://levelup.gitconnected.com/creating-a-crypto-trading-bot-for-fun-and-profit-fbf8d74de8c6

## Example .env file
```
CRYPTO=LINK
DAYS_TO_RUN=30
MODE=test
BACKTEST_INTERVAL=5minute
BACKTEST_SPAN=3month
BACKTEST_BOUNDS=24_7
UPPER_PRICE=9.00
LOWER_PRICE=6.00
LEVEL_NUM=6
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