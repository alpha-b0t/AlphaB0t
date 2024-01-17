# MoonTrader-backend

## Tech stack

### Frontend
- TypeScript
- Angular

### Backend
- Python
- Flask
- C++

### Database
- PostgreSQL
- Postico

### Version control
- Git

### DevOps
- Github
- Jira
- Confluence
- AWS
- Docker
- Redocly

### Payments
- Stripe

## Getting started

To run the application locally, run the following command in your terminal:
```
flask --app app run --debug
```

To compile C++ code to the C++17 standard, run the following command in your terminal:
```
make
```
The compiled C++ code will go in the bin folder.

To clear the compiled C++ code, run the following command in your terminal
```
make clean
```

To run the C++ code (i.e. run `main()` in main.cpp), run the following command in your terminal
```
make run-main
```

### Example .env file
```
# Database Configuration
DATABASE_USERNAME=
DATABASE_PASSWORD=
DATABASE_PORT=
DATABASE_NAME=

# Exchange Configuration
EXCHANGE=Kraken
API_KEY=
API_SEC=
API_PASSPHRASE=

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=
STRIPE_SECRET_KEY=

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

## Useful links
- https://www.reddit.com/r/CryptoCurrency/comments/10uqzbu/how_to_crypto_grid_trading_201/?rdt=63963
- https://medium.com/coinmonks/what-is-a-grid-trading-bot-3b58f3ec059b#:~:text=Grid%20Trading%20Bot%20is%20a,grid%20level%2C%20and%20vice%20versa.
- https://levelup.gitconnected.com/creating-a-crypto-trading-bot-for-fun-and-profit-fbf8d74de8c6
- https://www.binance.com/en/support/faq/binance-spot-grid-trading-parameters-688ff6ff08734848915de76a07b953dd
- https://www.postgresql.org/download/macosx/
- https://postgresapp.com/
- https://eggerapps.at/postico2/
- https://flask.palletsprojects.com/en/2.3.x/tutorial/layout/
- https://flask.palletsprojects.com/en/2.3.x/tutorial/factory/
- https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/
- https://flask-cors.corydolphin.com/en/latest/api.html#api-docs

## Profitable grid parameters
1. 2023-10-13
```
EXCHANGE=Robinhood
CRYPTO=LINK
BACKTEST_INTERVAL=day
BACKTEST_SPAN=3month
BACKTEST_BOUNDS=24_7
UPPER_PRICE=8.30
LOWER_PRICE=5.90
LEVEL_NUM=6
```

backtesting results:
{'initial_cash_balance': 1000, 'initial_crypto_equity': 0, 'initial_balance': 1000, 'final_cash_balance': 666.6800000000001, 'final_crypto_equity': 60.05000000000002, 'final_balance': 1098.79, 'current_cash_balance': 666.6800000000001, 'current_crypto_equity': 60.05000000000002, 'profit': 103.72000000000003, 'percent_change': 10.372000000000003, 'crypto': 'LINK', 'interval': 'day', 'span': '3month', 'bounds': '24_7'}

2. 2023-10-13
```
EXCHANGE=Robinhood
CRYPTO=LINK
BACKTEST_INTERVAL=day
BACKTEST_SPAN=year
BACKTEST_BOUNDS=24_7
UPPER_PRICE=8.10
LOWER_PRICE=5.25
LEVEL_NUM=4
```

backtesting results:
{'initial_cash_balance': 1000, 'initial_crypto_equity': 0, 'initial_balance': 1000, 'final_cash_balance': 1000.0, 'final_crypto_equity': 51.09000000000002, 'final_balance': 1367.6399999999999, 'current_cash_balance': 1000.0, 'current_crypto_equity': 51.09000000000002, 'profit': 418.3699999999999, 'percent_change': 41.83699999999998, 'crypto': 'LINK', 'interval': 'day', 'span': 'year', 'bounds': '24_7'}

## Optimization

I am trying to make my Python cryptocurrency spot grid trading bot more profitable. I have three parameters: `level_num` (the number of levels/grids), `upper_price` (the price of the highest grid/level), and `lower_price` (the price of the lowest grid/level). How do I algorithmically determine the most profitable values for these three parameters?

Creating a profitable cryptocurrency spot grid trading bot involves a combination of strategy, risk management, and market analysis. The choice of parameters like `level_num`, `upper_price`, and `lower_price` can significantly impact your bot's performance. To algorithmically determine the most profitable values for these parameters, you can follow these steps:

1. Historical Data Analysis:
   - Collect historical price data for the cryptocurrency pair you want to trade.
   - Calculate key statistics like volatility, average daily range, and price trends.

2. Define Your Strategy:
   - Determine your trading strategy and objectives (e.g., profit targets, risk tolerance, and holding periods).
   - Decide whether you want to trade in a trending or range-bound market.

3. Simulate Grid Strategies:
   - Develop a backtesting framework to simulate different grid trading strategies with varying `level_num`, `upper_price`, and `lower_price`.
   - Test a range of parameter values to identify profitable combinations.
   - Measure performance metrics such as return on investment (ROI), maximum drawdown, and win rate for each strategy.

4. Risk Management:
   - Implement risk management rules to protect your capital, such as setting stop-loss orders, position sizing, and maximum exposure limits.

5. Optimize Parameters:
   - Use optimization techniques (e.g., grid search or genetic algorithms) to find the best combination of parameters that maximize your defined performance metrics.
   - Be cautious about overfitting your model to historical data, as past performance does not guarantee future results.

6. Continuous Monitoring:
   - Regularly monitor the bot's performance in a paper trading or test environment to assess its profitability in real-time market conditions.

7. Adapt to Market Conditions:
   - Adjust your bot's parameters as market conditions change. Cryptocurrency markets can be highly volatile, and a static grid may not always be the most profitable.

8. Backtest Across Different Time Periods:
   - Ensure that your strategy performs well across various historical periods to confirm its robustness.

9. Consider Liquidity:
   - Take into account the liquidity of the cryptocurrency pair you're trading. Some pairs may not be suitable for grid trading due to low liquidity, as grid trading relies on frequent trading.

10. External Factors:
    - Keep an eye on external factors such as news events, regulatory changes, and market sentiment that could affect the cryptocurrency market.

11. Security:
    - Ensure that your trading bot is secure and follows best practices to protect your assets.

12. Review and Iterate:
    - Regularly review and fine-tune your bot's strategy based on real-world results. Be prepared to iterate and adjust as necessary.

Remember that there's no one-size-fits-all solution, and the most profitable parameter values may change over time. Successful grid trading bots require a combination of sound strategy, risk management, and adaptability to changing market conditions. It's essential to keep learning and refining your approach as you gain more experience in cryptocurrency trading.

Talk about number 3 and number 5 in more detail.

Certainly, let's delve into more detail about steps 3 and 5, which involve simulating grid trading strategies and optimizing parameters.

**Step 3: Simulate Grid Strategies**

Simulating grid trading strategies involves developing a backtesting framework to test various parameter combinations and assess their performance using historical data. Here's how to approach this step in more detail:

- **Data Collection**: Obtain historical price data for the cryptocurrency pair you intend to trade. You may use exchange APIs, third-party data providers, or data available on cryptocurrency market websites.

- **Backtesting Framework**: Create a software or script that simulates your grid trading strategy. This framework should allow you to input parameters like `level_num`, `upper_price`, and `lower_price` and execute trades based on those parameters.

- **Performance Metrics**: Define performance metrics to measure how well your grid trading strategy is performing. Common metrics include ROI (Return on Investment), maximum drawdown (the largest peak-to-trough decline), and win rate (the percentage of profitable trades).

- **Historical Data Split**: Divide your historical data into two parts: a training set and a testing set. The training set is used to optimize parameters, while the testing set is used to evaluate the performance of the chosen parameters.

- **Grid Trading Simulation**: Simulate grid trading using different combinations of parameters. Start with a range of `level_num`, `upper_price`, and `lower_price` values to see how they affect your performance metrics.

- **Analysis and Comparison**: Analyze the results of each simulation. Compare the performance metrics of different parameter combinations to identify which sets of values are more profitable and less risky.

- **Avoid Overfitting**: Be cautious not to overfit your model to the training data. Ensure that your strategy is robust and performs well across different market conditions, not just the historical period used for training.

**Step 5: Optimize Parameters**

Optimizing parameters involves using various techniques to find the best combination of `level_num`, `upper_price`, and `lower_price` that maximize your defined performance metrics. Here's how to perform parameter optimization in more detail:

- **Grid Search**: Perform a grid search by systematically testing a predefined range of values for each parameter. For example, you might test `level_num` from 10 to 50, `upper_price` from 1% to 5% above the current price, and `lower_price` from 1% to 5% below the current price.

- **Genetic Algorithms**: Consider using genetic algorithms or other optimization algorithms that can search for parameter combinations more efficiently and dynamically. Genetic algorithms mimic the process of natural selection to find optimal solutions.

- **Objective Function**: Define an objective function that combines your performance metrics (e.g., maximizing ROI while minimizing drawdown) to evaluate the overall performance of a parameter combination.

- **Cross-Validation**: Use cross-validation techniques to validate your parameter optimization results. Cross-validation involves splitting your data into multiple subsets and testing parameter combinations on each subset to ensure robustness.

- **Iterative Process**: Parameter optimization is often an iterative process. You may need to go through multiple rounds of testing and optimization to refine your strategy.

- **Regular Updates**: Continue to update your parameter values as market conditions change. What's profitable today may not be the case tomorrow, so adaptability is key.

Parameter optimization is a crucial step in grid trading bot development because it fine-tunes your strategy for the specific market conditions and goals you have set. By systematically testing different parameter values and using optimization techniques, you increase the likelihood of finding parameter combinations that can make your grid trading bot more profitable while managing risk.

Talk to me more about grid search and genetic algorithms. Can you write the algorithms in Python?

Certainly, I can provide a high-level explanation of grid search and genetic algorithms, and I'll also provide Python code examples to help you better understand how to implement them. Keep in mind that the Python code provided is a simplified version for educational purposes and may require customization for your specific use case.

### Grid Search

**Grid Search** is a simple and brute-force method for hyperparameter optimization. It involves specifying a range of values for each hyperparameter and exhaustively testing all possible combinations.

Here's a Python example of how to perform grid search:

```python
from itertools import product

# Define the parameter ranges
level_num_values = [10, 20, 30, 40, 50]
upper_price_values = [1.02, 1.03, 1.04, 1.05]
lower_price_values = [0.98, 0.97, 0.96, 0.95]

# Iterate through all combinations
best_params = None
best_performance = 0  # Initialize with a low value

for level_num, upper_price, lower_price in product(level_num_values, upper_price_values, lower_price_values):
    # Simulate grid trading with the current parameters
    performance = simulate_grid_trading(level_num, upper_price, lower_price)
    
    # Check if the current performance is better
    if performance > best_performance:
        best_params = (level_num, upper_price, lower_price)
        best_performance = performance

print("Best Parameters:", best_params)
print("Best Performance:", best_performance)
```

In this example, we define ranges for `level_num`, `upper_price`, and `lower_price`. We then use `itertools.product` to iterate through all possible combinations of these parameters, running the `simulate_grid_trading` function to measure performance. The combination with the best performance is selected as the best parameter set.

### Genetic Algorithms

**Genetic Algorithms** are a more sophisticated approach that mimics the process of natural selection to find optimal solutions. They work by evolving a population of candidate solutions over several generations.

Here's a Python example of how to implement a basic genetic algorithm for parameter optimization:

```python
import random

# Define the genetic algorithm parameters
population_size = 50
generations = 100
mutation_rate = 0.1

# Define the parameter ranges
level_num_values = [10, 20, 30, 40, 50]
upper_price_values = [1.02, 1.03, 1.04, 1.05]
lower_price_values = [0.98, 0.97, 0.96, 0.95]

# Initialize a random population
population = [(random.choice(level_num_values), random.uniform(1.02, 1.05), random.uniform(0.95, 0.98)) for _ in range(population_size)]

# Main optimization loop
for generation in range(generations):
    # Evaluate the fitness of each individual in the population
    fitness_scores = [simulate_grid_trading(*params) for params in population]

    # Select the top-performing individuals
    selected_indices = sorted(range(population_size), key=lambda i: fitness_scores[i], reverse=True)
    selected_population = [population[i] for i in selected_indices]

    # Crossover and mutation
    new_population = []
    for _ in range(population_size):
        parent1, parent2 = random.choices(selected_population, k=2)
        child = [random.choice(parent1[i], parent2[i]) for i in range(3)]
        if random.random() < mutation_rate:
            child = mutate(child)
        new_population.append(child)

    # Replace the old population with the new population
    population = new_population

# The best parameter set is the one with the highest fitness score
best_params = population[0]
best_performance = simulate_grid_trading(*best_params)
print("Best Parameters:", best_params)
print("Best Performance:", best_performance)
```

In this genetic algorithm example, we start with a random population of parameter sets. In each generation, we evaluate their fitness, select the top performers, perform crossover and mutation to create a new generation, and repeat this process for multiple generations. The best parameter set is the one with the highest fitness score.
