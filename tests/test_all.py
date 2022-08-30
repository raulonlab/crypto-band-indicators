import backtrader as bt
from cryptowatson_indicators.backtrader import RebalanceStrategy, WeightedDCAStrategy, DCAStrategy, HodlStrategy
from cryptowatson_indicators.datas import TickerDataSource
from cryptowatson_indicators.indicators import FngBandIndicator, RainbowBandIndicator
from cryptowatson_indicators.utils.utils import LogColors
import pprint
pprint = pprint.PrettyPrinter(indent=2).pprint
import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = [12, 6]
plt.rcParams['figure.dpi'] = 100 # 200
from dotenv import load_dotenv

load_dotenv()

# Global variables
strategy = "weighted_dca"    # Select strategy between "weighted_dca", "rebalance", "dca" and "hodl"
indicator = "fng"         # Select indicator between "fng" and "rainbow"
ticker_symbol = "BTCUSDT"      # currently only works with BTCUSDT
start = '01/08/2020'
end = '31/07/2021'
initial_cash = 10000.0        # initial broker cash. Default 10000 usd
min_order_period = 7              # Minimum period in days to place orders
base_buy_amount = 100            # Amount purchased in standard DCA
ma_class = None
# ma_class = bt.ind.WeightedMovingAverage
# ma_class = bt.ind.MovingAverageSimple

fng_weighted_multipliers = [1.5, 1.25, 1, 0.75, 0.5]    # order amount multipliers (weighted) for each index
rainbow_weighted_multipliers = [0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.3, 2.1, 3.4]

fng_rebalance_percents = [85, 65, 50, 15, 10]   # rebalance percentages for each index
rainbow_rebalance_percents = [0, 10, 20, 30, 50, 70, 80, 80, 100]

# logging
log = True
debug = False

# Enable / diable parts to bo tested
run_backtrader_test = True
run_plot_backtrader_result_test = True

# Ticker data source
ticker_data_source = TickerDataSource().load()

def backtrader_test():
    cerebro = bt.Cerebro(stdstats=True, runonce=True)
    cerebro.broker.set_coc(True)

    band_indicator = FngBandIndicator() if indicator == "fng" else RainbowBandIndicator()

    if strategy == "weighted_dca":
        # WeightedDCAStrategy
        weighted_multipliers = fng_weighted_multipliers if indicator == "fng" else rainbow_weighted_multipliers
        cerebro.addstrategy(WeightedDCAStrategy, 
                            band_indicator=band_indicator,
                            base_buy_amount=base_buy_amount,
                            min_order_period=min_order_period, 
                            weighted_multipliers=weighted_multipliers, 
                            log=log, 
                            debug=debug)
    elif strategy == "rebalance":
        rebalance_percents = fng_rebalance_percents if indicator == "fng" else rainbow_rebalance_percents
        cerebro.addstrategy(RebalanceStrategy, 
                            band_indicator=band_indicator,
                            min_order_period=min_order_period,
                            rebalance_percents=rebalance_percents, 
                            ma_class=ma_class, 
                            log=log, 
                            debug=debug)
    elif strategy == "dca":
        cerebro.addstrategy(DCAStrategy, 
                            buy_amount=base_buy_amount, 
                            min_order_period=min_order_period,
                            multiplier=1, 
                            log=log, 
                            debug=debug)
    elif strategy == "hodl":
        cerebro.addstrategy(HodlStrategy, 
                            percent=100, 
                            log=log, 
                            debug=debug)
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
    pnl_color = f"{LogColors.FAIL}" if strategy_results.pnl_value < 0 else f"{LogColors.OK}"

    print(f"\nResults of {str(strategy_results)}")
    print("----------------------------------------")
    print(strategy_results.describe())
    print("----------------------------------------")
    print(f"{'Started:':<8} {strategy_results.start_value:>10.2f} USD (1 BTC = {start_btc_price:.2f} USD)")
    print(f"{'Ended:':<8} {strategy_results.end_value:>10.2f} USD (1 BTC = {end_btc_price:.2f} USD)")
    print(f"{'PnL:':<8} {pnl_color}{strategy_results.pnl_value:>+10.2f} USD ({strategy_results.pnl_percent:+.2f}%){LogColors.ENDC}")

    if run_plot_backtrader_result_test:
        strategy_results.plot()


if __name__ == '__main__':
    if run_backtrader_test:
        backtrader_test()
