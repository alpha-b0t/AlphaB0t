# AlphaB0t

![AlphaB0t-engine-logo](./images/126627933.png)

## ⚠️ Disclaimer

This project is for **educational and research purposes only**.

- This software is **not financial advice**
- **No profits or specific results are guaranteed**
- Trading financial instruments involves **significant risk**, including the **possible loss of all invested capital**
- Past performance (if any) is **not indicative of future results**
- This software may contain bugs, errors, or unintended behavior

By using this software, you acknowledge that you are solely responsible for any financial decisions and outcomes.  
Use this software **at your own risk**.

## High-Level Architecture
Essentially, the high-level architecture consists of four parts: a bot or automonous agent that executes the strategy it is given through the exchange it it connected to in the context of the mode the bot is assigned to, the strategy, the exchange, and the bot mode. To put it bluntly, one can swap out different bot modes, strategies, and exchanges for the bot.
![High-Level Architecture](./images/AlphaB0t_Architecture.jpeg)

## Getting started

```
poetry install
poetry env activate
```

To run the application locally, run the following command in your terminal:
```
poetry run flask --app app run --debug
```

To run the Python unit tests implemented in pytest, run the following command in your terminal:
```
poetry run pytest
```

### Example .env file
```
# Exchange Configuration
EXCHANGE=Kraken
API_KEY=
API_SEC=
API_PASSPHRASE=

# Request Configuration
REQUEST=

# CoinMarketCap API Key
CMC_API_KEY=

# GRID Bot Configuration
NAME=
PAIR=MOONUSD
BASE_CURRENCY=ZUSD
MODE=test
UPPER_PRICE=8.10
LOWER_PRICE=5.25
LEVEL_NUM=4
QUANTITY_PER_GRID=0
TOTAL_INVESTMENT=1000
STOP_LOSS=1.00
TAKE_PROFIT=10.00
DAYS_TO_RUN=30
LATENCY_IN_SEC=5.00
MAX_ERROR_COUNT=5
ERROR_LATENCY_IN_SEC=5
INIT_BUY_ERROR_LATENCY_IN_SEC=5
INIT_BUY_ERROR_MAX_COUNT=10
CANCEL_ORDERS_UPON_EXIT=none
```

### Setting up Kraken account

Create an API key with the following permissions:

Funds permissions:
- Query

Orders and trades:
- Query open orders & trades
- Query closed orders & trades
- Create & modify orders
- Cancel & close orders

Websocket Interface: On
