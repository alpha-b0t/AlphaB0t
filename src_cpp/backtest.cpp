#include <iostream>
#include <string>
#include <vector>
#include <cmath>

using namespace std;

const double MAKER_FEE = 0.0025;

class Grid {
    public:
        Grid(double price_level, string buy_sell, bool is_active) {
            double price = prive_level:
            string side = buy_sell;
            bool active = is_active;
        }
};

class Order {
    public:
        Order(double price_amount, string buy_sell, string status_value) {
            double price = price_amount;
            string side = buy_sell;
            string status = status_value;
        }
};

class OHLC {
    public:
        OHLC(double o, double h, double l, double c) {
            double open = o;
            double high = h;
            double low = l;
            double close = c;
        }
};

vector<double> optimize_grid_params(int max_level_num, double min_lower_price, double max_upper_price, double price_increment, vector<OHLC> prices);
double get_profit_from_backtest(int level_num, double lower_price, double upper_price, vector<OHLC> prices);
double min_fee1(double fee);
double min_fee2(double fee);

vector<double> optimize_grid_params(int max_level_num, double min_lower_price, double max_upper_price, double price_increment, vector<OHLC> prices) {
    double best_profit = -1;
    int best_level_num = 0;
    double best_lower_price(0), best_upper_price(0);

    double profit = 0;
    for (int level_num = 2; level_num <= max_level_num; ++level_num) {
        for (double lower_price = min_lower_price; lower_price <= max_upper_price - price_increment; lower_price += price_increment) {
            for (double upper_price = lower_price + price_increment; upper_price <= max_upper_price; upper_price += price_increment) {
                profit = get_profit_from_backtest(
                    level_num=level_num,
                    lower_price=lower_price,
                    upper_price=upper_price,
                    prices=prices
                );

                if (profit > best_profit) {
                    best_profit = profit;
                    best_level_num = level_num;
                    best_lower_price = lower_price;
                    best_upper_price = upper_price;
                }
            }
        }
    }
    
    vector<double> result = {static_cast<double>(best_level_num), best_lower_price, best_upper_price};
    return result;
}

double get_profit_from_backtest(int level_num, double lower_price, double upper_price, vector<OHLC> prices) {
    // TODO: Implement
    return 0.00;
}

double min_fee1(double fee) {
    return ((1.00 + fee) / (1.00 - fee)) - 1.00;
}

double min_fee2(double fee) {
    return (1.00 / pow((1.00 - fee), 2)) - 1.00;
}
