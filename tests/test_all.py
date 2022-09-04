import backtrader as bt
from crypto_band_indicators.backtrader import RebalanceStrategy, WeightedDCAStrategy, DCAStrategy, HodlStrategy
from crypto_band_indicators.datas import TickerDataSource
from crypto_band_indicators.indicators import FngBandIndicator, RainbowBandIndicator
from crypto_band_indicators import utils
import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = [12, 6]
plt.rcParams['figure.dpi'] = 100 # 200

# Global variables
strategy = "weighted_dca"    # Select strategy between "rebalance", "weighted_dca", "dca" and "hodl"
indicator = "fng"         # Select indicator between "fng" and "rainbow"
start = '01/08/2020'
end = '31/07/2021'
initial_cash = 10000.0        # initial broker cash. Default 10000 usd
min_order_period = 7              # Minimum period in days to place orders
base_buy_amount = 100            # Amount purchased in standard DCA

# Weighted multipliers and rebalance percents
fng_weighted_multipliers = [1.5, 1.25, 1, 0.75, 0.5]    # order amount multipliers (weighted) for each index
rainbow_weighted_multipliers = [0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.3, 2.1, 3.4]
fng_rebalance_percents = [85, 65, 50, 15, 10]   # rebalance percentages for each index
rainbow_rebalance_percents = [0, 10, 20, 30, 50, 70, 80, 80, 100]

# ticker and indicator ta_configs: smooths data variations by using a MA algorithm
ticker_ta_config = {'kind': 'sma', 'length': 3}  # Ex: {'kind': 'sma', 'length': 3} or None
indicator_ta_config = {'kind': 'wma', 'length': 3}  # Ex: {'kind': 'wma', 'length': 3} or None

# logging
backtrader_log = False
backtrader_debug = False

# Enable / diable parts to bo tested
run_backtrader_test = True
run_plot_backtrader_result_test = True

# Ticker data source
ticker_data_source = TickerDataSource().load()
ta_column = None
if ticker_ta_config is not None:
    ticker_data_source.append_ta_columns(ticker_ta_config)
    ta_column = ticker_data_source.get_ta_columns()[0]

def backtrader_test():
    cerebro = bt.Cerebro(stdstats=True, runonce=True)
    cerebro.broker.set_coc(True)

    indicator_class = FngBandIndicator if indicator == "fng" else RainbowBandIndicator

    if strategy == "weighted_dca":
        # WeightedDCAStrategy
        weighted_multipliers = fng_weighted_multipliers if indicator == "fng" else rainbow_weighted_multipliers
        cerebro.addstrategy(WeightedDCAStrategy, 
                            indicator_class=indicator_class,
                            indicator_ta_config=indicator_ta_config,
                            ta_column=ta_column, 
                            base_buy_amount=base_buy_amount,
                            min_order_period=min_order_period, 
                            weighted_multipliers=weighted_multipliers, 
                            log=backtrader_log, 
                            debug=backtrader_debug)
    elif strategy == "rebalance":
        rebalance_percents = fng_rebalance_percents if indicator == "fng" else rainbow_rebalance_percents
        cerebro.addstrategy(RebalanceStrategy, 
                            indicator_class=indicator_class,
                            indicator_ta_config=indicator_ta_config,
                            ta_column=ta_column, 
                            min_order_period=min_order_period,
                            rebalance_percents=rebalance_percents, 
                            log=backtrader_log, 
                            debug=backtrader_debug)
    elif strategy == "dca":
        cerebro.addstrategy(DCAStrategy, 
                            buy_amount=base_buy_amount, 
                            min_order_period=min_order_period,
                            multiplier=1, 
                            log=backtrader_log, 
                            debug=backtrader_debug)
    elif strategy == "hodl":
        cerebro.addstrategy(HodlStrategy, 
                            percent=100, 
                            log=backtrader_log, 
                            debug=backtrader_debug)
    else:
        error_message = f"Invalid strategy: '{strategy}'"
        print(f"Error: {error_message}")
        return

    # Add the data to Cerebro
    cerebro.adddata(ticker_data_source.to_backtrade_feed(start, end))

    # Add cash to the virtual broker
    cerebro.broker.setcash(initial_cash)    # default: 10k

    cerebro_results = cerebro.run()

    strategy_results = cerebro_results[0]
    start_btc_price, end_btc_price = ticker_data_source.get_value_start_end(
        start=start, end=end)
    pnl_color = f"{utils.LogColors.FAIL}" if strategy_results.pnl_value < 0 else f"{utils.LogColors.OK}"

    print(f"\nResults of {str(strategy_results)}")
    print("--------------------------------------------")
    print(f"{'Started:':<8} {strategy_results.start_value:>10.2f} USD (1 BTC = {start_btc_price:.2f} USD)")
    print(f"{'Ended:':<8} {strategy_results.end_value:>10.2f} USD (1 BTC = {end_btc_price:.2f} USD)")
    print(f"{'PnL:':<8} {pnl_color}{strategy_results.pnl_value:>+10.2f} USD ({strategy_results.pnl_percent:+.2f}%){utils.LogColors.ENDC}")

    if run_plot_backtrader_result_test:
        strategy_results.plot()


if __name__ == '__main__':
    if run_backtrader_test:
        backtrader_test()
