from app.models.gridbot import KrakenGRIDBot
from app.models.exchange import KrakenExchange
from config import ExchangeConfig, GRIDBotConfig
import pytest

@pytest.mark.parametrize('total_investment, lower_price, upper_price, level_num, pair_decimals, expected_quantity', [
    (100, 25, 75, 2, 2, 4.0),
    (200, 100, 150, 2, 2, 2.0),
    (20, 5, 10, 2, 2, 4.0),
    (100, 25, 125, 3, 2, 2.0),
    (100, 25, 100, 4, 2, 2.0)
])
def test_kraken_calculate_max_quantity_per_grid(total_investment: float, lower_price, upper_price, level_num, pair_decimals, expected_quantity: float):
    # Arrange
    # Set up an ExchangeConfig and a GRIDBotConfig
    exchange_config = ExchangeConfig("tests/test.env")
    gridbot_config = GRIDBotConfig("tests/test.env")

    # Inject the parameters into the gridbot config
    gridbot_config.lower_price = lower_price
    gridbot_config.upper_price = upper_price
    gridbot_config.level_num = level_num
    gridbot_config.take_profit = upper_price + 0.01
    gridbot_config.stop_loss = lower_price - 0.01

    # Set up a KrakenGRIDBot
    kraken_gridbot = KrakenGRIDBot(gridbot_config, exchange_config)

    # Change the gridbot's pair decimals to match the input value
    kraken_gridbot.pair_decimals = pair_decimals

    # Act
    actual_quantity = kraken_gridbot.calculate_max_quantity_per_grid(total_investment)

    # Assert
    assert actual_quantity == expected_quantity

@pytest.mark.parametrize('quantity_per_grid, lower_price, upper_price, level_num, pair_decimals, expected_investment', [
    (0.5, 5, 10, 2, 2, 2.5),
    (1.0, 10, 50, 5, 2, 100),
    (1.0, 5, 15, 3, 2, 15)
])
def test_kraken_calculate_total_investment(quantity_per_grid: float, lower_price, upper_price, level_num, pair_decimals, expected_investment: float):
    # Arrange
    # Set up an ExchangeConfig and a GRIDBotConfig
    exchange_config = ExchangeConfig("tests/test.env")
    gridbot_config = GRIDBotConfig("tests/test.env")

    # Inject the parameters into the gridbot config
    gridbot_config.lower_price = lower_price
    gridbot_config.upper_price = upper_price
    gridbot_config.level_num = level_num
    gridbot_config.take_profit = upper_price + 0.01
    gridbot_config.stop_loss = lower_price - 0.01

    # Set up a KrakenGRIDBot
    kraken_gridbot = KrakenGRIDBot(gridbot_config, exchange_config)

    # Change the gridbot's pair decimals to match the input value
    kraken_gridbot.pair_decimals = pair_decimals

    # Act
    actual_investment = kraken_gridbot.calculate_total_investment(quantity_per_grid)

    # Assert
    assert actual_investment == expected_investment

# TODO: Test KrakenGRIDBot's calculate_profit method
