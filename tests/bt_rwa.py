import backtrader as bt
from cryptowatson_indicators import TickerDataSource, RwaWeightedAverageStrategy, RwaRebalanceStrategy, RwaIndicator
import pprint
pprint = pprint.PrettyPrinter(indent=2).pprint

# Global variables
strategy = "rebalance"    # Select strategy between "weighted_dca" and "rebalance"
ticker_symbol = "BTCUSDT"      # currently only works with BTCUSDT
start = '01/01/2020'   # start date of the simulation. Ex: '01/08/2020' or None
end = None           # end date of the simulation. Ex: '01/08/2020' or None
initial_cash = 10000.0        # initial broker cash. Default 10000 usd
min_order_period = 5              # Minimum period in days to place orders
weighted_buy_amount = 100            # Amount purchased in standard DCA
# weighted_multipliers = [0, 0.1, 0.2, 0.35, 0.5, 0.75, 1, 2.5, 3]      # Default order amount multipliers (weighted) for each index
# Fibonacci order amount multipliers (weighted) for each index
weighted_multipliers = [0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.3, 2.1, 3.4]
# rebalance percentages for each index
rebalance_percents = [10, 20, 30, 40, 50, 60, 70, 80, 90]

# logging
log = True
debug = False

# Enable / diable parts to bo tested
run_get_value_test = True
run_plot_test = True
run_backtrader_test = True
run_plot_backtrader_result_test = True

# Data sources
ticker_data_source = TickerDataSource()

# Limit indicator series to start at specific date or None to use all the history
indicator_start_date = None
rwa = RwaIndicator(ticker_data_source.to_dataframe())


def get_value_test():
    # Get Current Rainbow band
    band_index = rwa.get_current_rainbow_band_index()
    rainbow_info = RwaIndicator._get_rainbow_info_by_index(band_index)
    print('Current Rainbow Band:')
    pprint(rainbow_info)

    # Get Rainbow band at date
    at_date = '01/02/2021'    # date when look up the Fng
    price_at_date = 30000     # Price of BTC at date

    band_index = rwa.get_rainbow_band_index(
        price=price_at_date, at_date=at_date)
    rainbow_info = RwaIndicator._get_rainbow_info_by_index(band_index)
    print(f"Rainbow Band at {at_date}:")
    pprint(rainbow_info)


def plot_test():
    rwa.plot_rainbow()


def backtrader_test():
    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    if strategy == "weighted_dca":
        cerebro.addstrategy(RwaWeightedAverageStrategy, weighted_buy_amount=weighted_buy_amount,
                            min_order_period=min_order_period, weighted_multipliers=weighted_multipliers, log=log, debug=debug)
    elif strategy == "rebalance":
        cerebro.addstrategy(RwaRebalanceStrategy, min_order_period=min_order_period,
                            rebalance_percents=rebalance_percents, log=log, debug=debug)
    else:
        error_message = f"Invalid strategy: '{strategy}'"
        print(f"Error: {error_message}")
        return

    # Get data feed
    ticker_data_feed = ticker_data_source.to_backtrade_feed(start, end)
    rwa_data_feed = ticker_data_source.to_backtrade_feed()

    # Add the Data Feed to Cerebro
    cerebro.adddata(ticker_data_feed)
    cerebro.adddata(rwa_data_feed)

    # Add cash to the virtual broker
    cerebro.broker.setcash(initial_cash)    # default: 10k

    start_portfolio_value = cerebro.broker.getvalue()

    cerebro.run()

    end_portfolio_value = cerebro.broker.getvalue()     # Value in USDT
    pnl_portfolio_value = end_portfolio_value - start_portfolio_value

    # position: size: BTC in portfolio, price: average BTC purchase price
    position = cerebro.getbroker().getposition(data=ticker_data_feed)
    start_btc_price, end_btc_price = ticker_data_source.get_value_start_end(
        start=start, end=end)

    # btc price and PnL at start
    start_pnl_value = pnl_portfolio_value + (position.size * start_btc_price)
    start_pnl_percent = (start_pnl_value / start_portfolio_value) * 100
    start_pnl_sign = '' if start_pnl_value < 0 else '+'

    # btc price and PnL at the end
    end_pnl_value = pnl_portfolio_value + (position.size * end_btc_price)
    end_pnl_percent = (end_pnl_value / start_portfolio_value) * 100
    end_pnl_sign = '' if end_pnl_value < 0 else '+'

    # btc price and PnL at the end
    avg_btc_price = position.price
    avg_pnl_value = pnl_portfolio_value + (position.size * avg_btc_price)
    avg_pnl_percent = (avg_pnl_value / start_portfolio_value) * 100
    avg_pnl_sign = '' if avg_pnl_value < 0 else '+'

    print("\nSIMULATION RESULT")
    print("------------------------")
    print(f"{'Started:':<12} {start_portfolio_value:<.2f} USD")
    print(f"{'Ended:':<12} {end_portfolio_value:<.2f} USD, {position.size:6f} BTC")
    print(f"{'PnL:':<12} {end_pnl_sign}{end_pnl_value:.2f} USD ({end_pnl_sign}{end_pnl_percent:.2f}%) at the latest price of {end_btc_price:.4f} USD")
    print(f"{'PnL:':<12} {avg_pnl_sign}{avg_pnl_value:.2f} USD ({avg_pnl_sign}{avg_pnl_percent:.2f}%) on average price of {avg_btc_price:.4f} USD")
    print(f"{'PnL:':<12} {start_pnl_sign}{start_pnl_value:.2f} USD ({start_pnl_sign}{start_pnl_percent:.2f}%) at the initial price of {start_btc_price:.4f} USD")

    if run_plot_backtrader_result_test:
        cerebro.plot(volume=False)  # iplot=False, style='bar' , stdstats=False


if __name__ == '__main__':
    if run_get_value_test == True:
        get_value_test()
    if run_plot_test == True:
        plot_test()
    if run_backtrader_test:
        backtrader_test()
