import pandas as pd
import backtrader as bt
from cryptowatson_indicators.backtrader import RebalanceStrategy, HodlStrategy
from cryptowatson_indicators.datas import TickerDataSource
from cryptowatson_indicators.indicators import FngBandIndicator, RainbowBandIndicator
from tabulate import tabulate
import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = [12, 6]
plt.rcParams['figure.dpi'] = 100 # 200
from dotenv import load_dotenv

load_dotenv()

# Fixed variables ################
initial_cash = 10000.0        # initial broker cash. Default 10000 usd
fng_rebalance_percents = [85, 65, 50, 15, 10]   # rebalance percentages for each index
rainbow_rebalance_percents = [0, 10, 20, 30, 50, 70, 80, 80, 100]

# Range variables (to compare optimization)
min_order_period_list = range(4, 8)              # Minimum period in days to place orders
ma_class_list = [bt.ind.WeightedMovingAverage, bt.ind.MovingAverageSimple]

# Data sources
ticker_data_source = TickerDataSource().load()

def run_hodl(start, end):
    cerebro = bt.Cerebro(stdstats=False, maxcpus=1, runonce=True, exactbars=False)
    cerebro.broker.set_coc(True)

    # Add the data to Cerebro
    ticker_data_feed = ticker_data_source.to_backtrade_feed(start, end)
    cerebro.adddata(ticker_data_feed)

    cerebro.addstrategy(HodlStrategy, percent=100, log=False, debug=False)

    # Add cash to the virtual broker
    cerebro.broker.setcash(initial_cash)    # default: 10k

    cerebro_results = cerebro.run()

    return cerebro_results

def run_opt_rebalance(start, end, band_indicator, min_order_period, ma_class, rebalance_percents):
    cerebro = bt.Cerebro(stdstats=False, maxcpus=0, runonce=True, exactbars=False, optdatas=True)
    cerebro.broker.set_coc(True)

    # Add the data to Cerebro
    ticker_data_feed = ticker_data_source.to_backtrade_feed(start, end)
    cerebro.adddata(ticker_data_feed)

    cerebro.optstrategy(RebalanceStrategy,
                        band_indicator=band_indicator,  
                        min_order_period=min_order_period, 
                        ma_class=ma_class, 
                        rebalance_percents=rebalance_percents, 
                        log=(False,),
                        debug=(False,))

    # Add cash to the virtual broker
    cerebro.broker.setcash(initial_cash)    # default: 10k

    cerebro_results = cerebro.run(optreturn=False)

    return cerebro_results


def run_between_dates(start, end):
    results = list()

    # Hodl
    cerebro_results = run_hodl(start, end)
    for strategy in cerebro_results:
        results.append(strategy.describe())

    # With FnG indicator
    fng_indicator = FngBandIndicator()
    cerebro_results = run_opt_rebalance(start, end, min_order_period=min_order_period_list, ma_class=ma_class_list, band_indicator=(fng_indicator,), rebalance_percents=(fng_rebalance_percents,))
    for strategy_results in cerebro_results:
        for strategy in strategy_results:
            results.append(strategy.describe())

    # With Rainbow indicator
    rainbow_indicator = RainbowBandIndicator()
    cerebro_results = run_opt_rebalance(start, end, min_order_period=min_order_period_list, ma_class=ma_class_list, band_indicator=(rainbow_indicator,), rebalance_percents=(rainbow_rebalance_percents,))
    for strategy_results in cerebro_results:
        for strategy in strategy_results:
            results.append(strategy.describe())

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('pnl_value', ascending=False)

    results_df['pnl'] = results_df.apply(lambda row: f"{row['pnl_value']:+.2f}({row['pnl_percent']:+.2f})", axis=1)
    results_df['params'] = results_df.apply(lambda row: f"{row['min_order_period']:<2}|{row['rebalance_percents']}|{row['ma_class']}", axis=1)

    print_columns = ["name", "pnl", "params"]
    print(tabulate(results_df[print_columns], tablefmt="fancy_grid", headers=print_columns, showindex=False))


if __name__ == '__main__':
    # start = '01/01/2020'
    # end = '31/07/2020'

    # print(f"\nResults between {start} and {end}")
    # print("----------------------------------------")
    # run_between_dates(start, end)


    # start = '01/08/2020'
    # end = '31/12/2020'

    # print(f"\nResults between {start} and {end}")
    # print("----------------------------------------")
    # run_between_dates(start, end)


    # start = '01/01/2021'
    # end = '31/07/2021'

    # print(f"\nResults between {start} and {end}")
    # print("----------------------------------------")
    # run_between_dates(start, end)


    start = '01/08/2021'
    end = '31/12/2021'

    print(f"\nResults between {start} and {end}")
    print("----------------------------------------")
    run_between_dates(start, end)
