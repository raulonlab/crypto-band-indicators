import backtrader as bt
from crypto_band_indicators.backtrader import RebalanceStrategy, WeightedDCAStrategy
from crypto_band_indicators.datas import TickerDataSource, FngDataSource
from crypto_band_indicators.indicators import FngBandIndicator
from crypto_band_indicators import utils
import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = [12, 6]
plt.rcParams['figure.dpi'] = 100 # 200

# Variables #########################
strategy = "rebalance"    # Select strategy between "weighted_dca" and "rebalance"
start = '01/01/2021'   # start date of the simulation. Ex: '01/08/2020' or None
end = '31/08/2021'           # end date of the simulation. Ex: '01/08/2020' or None
initial_cash = 10000.0        # initial broker cash. Default 10000 usd
min_order_period = 6              # Minimum period in days to place orders
base_buy_amount = 100            # Amount purchased in standard DCA

# Weighted multipliers and rebalance percents
weighted_multipliers = [1.5, 1.25, 1, 0.75, 0.5]    # order amount multipliers (weighted) for each index
rebalance_percents = [85, 65, 50, 15, 10]   # rebalance percentages for each index

# ticker and indicator ta_configs: smooths data variations by using a MA algorithm
ticker_ta_config = {'kind': 'sma', 'length': 3}  # Ex: {'kind': 'sma', 'length': 3} or None
indicator_ta_config = {'kind': 'wma', 'length': 3}  # Ex: {'kind': 'wma', 'length': 3} or None

# logging
backtrader_log = True
backtrader_debug = False

# Enable / diable parts to bo tested
run_get_value_test = True
run_plot_test = True
run_backtrader_test = True
run_plot_backtrader_result_test = True

# Data sources
ticker_data_source = TickerDataSource().load()
ta_column = None
if ticker_ta_config is not None:
    ticker_data_source.append_ta_columns(ticker_ta_config)
    ta_column = ticker_data_source.get_ta_columns()[0]

# Fng Indicator 
fng = FngBandIndicator()

def get_value_test():
    # Get Current Fear and Greed index
    fng_details = fng.get_band_details_at()
    print('Current FnG:')
    print(fng_details)

    # Get Fear and Greed index at date
    at_date = '01/02/2021'    # date when look up the Fng

    fng_details = fng.get_band_details_at(at_date=at_date)
    print(f"FnG at {at_date}:")
    print(fng_details)


def plot_test():
    fng.plot_fng_and_ticker_price(
        ticker_data=ticker_data_source.to_dataframe())
    # fng.plot_fng()


def backtrader_test():
    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.set_coc(True)

    if strategy == "weighted_dca":
        cerebro.addstrategy(WeightedDCAStrategy, 
                            indicator_class=FngBandIndicator,
                            indicator_ta_config=indicator_ta_config,
                            ta_column=ta_column,
                            base_buy_amount=base_buy_amount,
                            min_order_period=min_order_period, 
                            weighted_multipliers=weighted_multipliers, 
                            log=backtrader_log, 
                            debug=backtrader_debug)
    elif strategy == "rebalance":
        cerebro.addstrategy(RebalanceStrategy, 
                            indicator_class=FngBandIndicator,
                            indicator_ta_config=indicator_ta_config,
                            ta_column=ta_column,
                            min_order_period=min_order_period,
                            rebalance_percents=rebalance_percents, 
                            log=backtrader_log, 
                            debug=backtrader_debug)
    else:
        error_message = f"Invalid strategy: '{strategy}'"
        print(f"Error: {error_message}")
        return

    # Get data feed
    ticker_data_feed = ticker_data_source.to_backtrade_feed(start, end)

    # Add the data to Cerebro
    cerebro.adddata(ticker_data_feed)

    # Add cash to the virtual broker
    cerebro.broker.setcash(initial_cash)    # default: 10k

    start_portfolio_value = cerebro.broker.getvalue()

    cerebro_results = cerebro.run()

    end_cash = cerebro.broker.getcash()
    end_portfolio_value = cerebro.broker.getvalue()     # Total value in USDT
    end_position = cerebro.getbroker().getposition(data=ticker_data_feed)
    start_btc_price, end_btc_price = ticker_data_source.get_value_start_end(
        start=start, end=end)

    pnl_value = end_portfolio_value - start_portfolio_value
    pnl_percent = (pnl_value / start_portfolio_value) * 100
    pnl_color = f"{utils.LogColors.FAIL}" if end_portfolio_value < start_portfolio_value else f"{utils.LogColors.OK}"

    print(f"\nResults of {str(cerebro_results[0])}")
    print("--------------------------------------------")
    print(f"{'Started:':<8} {start_portfolio_value:>10.2f} USD (1 BTC = {start_btc_price:.2f} USD)")
    print(f"{'Ended:':<8} {end_portfolio_value:>10.2f} USD ({end_position.size:6f} BTC + {end_cash:.2f} USD in cash | 1 BTC = {end_btc_price:.2f} USD)")
    print(f"{'PnL:':<8} {pnl_color}{pnl_value:>10.2f} USD ({pnl_percent:.2f}%){utils.LogColors.ENDC}")

    if run_plot_backtrader_result_test:
        cerebro_results[0].plot()


if __name__ == '__main__':
    if run_get_value_test == True:
        get_value_test()
    if run_plot_test == True:
        plot_test()
    if run_backtrader_test:
        backtrader_test()

