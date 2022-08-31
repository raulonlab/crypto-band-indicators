import pandas as pd
import backtrader as bt
from cryptowatson_indicators.backtrader import RebalanceStrategy, WeightedDCAStrategy, DCAStrategy, HodlStrategy
from cryptowatson_indicators.datas import TickerDataSource
from cryptowatson_indicators.indicators import FngBandIndicator, RainbowBandIndicator
from tabulate import tabulate
import matplotlib.pyplot as plt

from cryptowatson_indicators.utils.utils import LogColors
plt.rcParams['figure.figsize'] = [12, 6]
plt.rcParams['figure.dpi'] = 100 # 200
from dotenv import load_dotenv

load_dotenv()

# Fixed variables ################
initial_cash = 10000.0        # initial broker cash. Default 10000 usd
base_buy_amount  = 100            # Amount purchased in standard DCA
fng_weighted_multipliers = [1.5, 1.25, 1, 0.75, 0.5]    # buy amount multipliers (weighted) for each band
fng_rebalance_percents   = [85, 65, 50, 15, 10]         # rebalance percentages of BTC / total for each band
rwa_weighted_multipliers = [0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.3, 2.1, 3.4]
rwa_rebalance_percents = [10, 20, 30, 40, 50, 60, 70, 80, 90]
fng_indicator_params={}
rainbow_indicator_params={}

# Range variables (to compare optimization)
min_order_period_list = range(4, 8)              # Minimum period in days to place orders
indicator_params_list = [None,
                        {'ta_config': {'kind': 'sma', 'length': 4}},
                        {'ta_config': {'kind': 'wma', 'length': 3}},
                        ]
ma_class_list = [bt.ind.WeightedMovingAverage, 
                 bt.ind.MovingAverageSimple]     # smooth data with ma algorithm 

# Data sources
ticker_data_source = TickerDataSource().load()

def run(start, end, strategy_class, **kwargs):
    cerebro = bt.Cerebro(stdstats=False, optreturn=False, maxcpus=0, runonce=True, exactbars=False)
    cerebro.broker.set_coc(True)

    # Add strategy
    cerebro.optstrategy(strategy_class,
                        log=(False,),
                        debug=(False,),
                        **kwargs)

    # Add data feed
    cerebro.adddata(ticker_data_source.to_backtrade_feed(start, end))

    # Add cash to the virtual broker
    cerebro.broker.setcash(initial_cash)    # default: 10k

    run_result = cerebro.run()

    return run_result


def run_optimisation_between_dates(start, end):
    rebalance_run_results = list()
    wdca_run_results = list()

    # HODL
    run_result = run(start,
                    end,
                    strategy_class=HodlStrategy,
                    percent=(100,))
    rebalance_run_results.extend(map(lambda result: result[0], run_result))

    # Rebalance strategy with Fear and Greed indicator
    run_result = run(start,
                    end,
                    strategy_class=RebalanceStrategy,
                    indicator_class=(FngBandIndicator,),
                    indicator_params=indicator_params_list,
                    ma_class=ma_class_list,
                    min_order_period=min_order_period_list,
                    rebalance_percents=(fng_rebalance_percents,))
    rebalance_run_results.extend(map(lambda result: result[0], run_result))

    # Rebalance strategy with Rainbow indicator
    run_result = run(start,
                    end,
                    strategy_class=RebalanceStrategy,
                    indicator_class=(RainbowBandIndicator,),
                    # indicator_params=indicator_params_list,
                    ma_class=ma_class_list,
                    min_order_period=min_order_period_list,
                    rebalance_percents=(rwa_rebalance_percents,))
    rebalance_run_results.extend(map(lambda result: result[0], run_result))

    # Standard DCA
    run_result = run(start,
                    end,
                    strategy_class=DCAStrategy,
                    buy_amount=(base_buy_amount,),
                    min_order_period=min_order_period_list)
    wdca_run_results.extend(map(lambda result: result[0], run_result))

    # Weighted Av strategy with Fear and Greed indicator
    run_result = run(start,
                    end,
                    strategy_class=WeightedDCAStrategy,
                    indicator_class=(FngBandIndicator,),
                    indicator_params=indicator_params_list,
                    # ma_class=ma_class_list,   # Not used in Weighed Avg
                    base_buy_amount=(base_buy_amount,),
                    min_order_period=min_order_period_list,
                    weighted_multipliers=(fng_weighted_multipliers,))
    wdca_run_results.extend(map(lambda result: result[0], run_result))

    # Weighted Av strategy with Rainbow indicator
    run_result = run(start,
                    end,
                    strategy_class=WeightedDCAStrategy,
                    indicator_class=(RainbowBandIndicator,),
                    # indicator_params=indicator_params_list,
                    # ma_class=ma_class_list,   # Not used in Weighed Avg
                    base_buy_amount=(base_buy_amount,),
                    min_order_period=min_order_period_list,
                    weighted_multipliers=(rwa_weighted_multipliers,))
    wdca_run_results.extend(map(lambda result: result[0], run_result))


    # Sort results by pnl_value descendent (best value first
    sorted_rebalance_run_results = sorted(rebalance_run_results, key=lambda strategy: float(strategy.pnl_value), reverse=True)
    sorted_wdca_run_results = sorted(wdca_run_results, key=lambda strategy: float(strategy.pnl_value), reverse=True)

    # Print results
    column_keys = ['name', 'pnl_value', 'pnl_percent', 'params']
    column_headers = ['Strategy', 'PNL USDT', 'PNL %', 'Parameters']

    sorted_rebalance_run_details = map(lambda strategy: strategy.describe(keys=column_keys), sorted_rebalance_run_results)
    print(f"\n{LogColors.BOLD}Rebalance results:{LogColors.ENDC}")
    print(tabulate([details.values() for details in sorted_rebalance_run_details], 
                    tablefmt="fancy_grid", 
                    headers=column_headers, 
                    floatfmt="+.2f"))

    sorted_wdca_run_details = map(lambda strategy: strategy.describe(keys=column_keys), sorted_wdca_run_results)
    print(f"\n{LogColors.BOLD}Weighted DCA results:{LogColors.ENDC}")
    print(tabulate([details.values() for details in sorted_wdca_run_details], 
                    tablefmt="fancy_grid", 
                    headers=column_headers, 
                    floatfmt="+.2f"))
    
    # Plot results
    plot_results = True
    plot_only_winner = True

    if plot_results:
        for i in range(0, len(sorted_rebalance_run_results)):
            sorted_rebalance_run_results[i].plot(title_prefix='BEST: ' if i == 0 else '', title_suffix=f" ({sorted_rebalance_run_results[i].pnl_percent:+.2f}%)")

            if plot_only_winner:
                break
        
        for i in range(0, len(sorted_wdca_run_results)):
            sorted_wdca_run_results[i].plot(title_prefix='BEST: ' if i == 0 else '', title_suffix=f" ({sorted_wdca_run_results[i].pnl_percent:+.2f}%)")

            if plot_only_winner:
                break


if __name__ == '__main__':
    # start = '01/01/2020'
    # end = '31/07/2020'

    # print(f"\nResults between {start} and {end}")
    # print("--------------------------------------------")
    # run_optimisation_between_dates(start, end)


    # start = '01/08/2020'
    # end = '31/12/2020'

    # print(f"\nResults between {start} and {end}")
    # print("--------------------------------------------")
    # run_optimisation_between_dates(start, end)


    # start = '01/01/2021'
    # end = '31/07/2021'

    # print(f"\nResults between {start} and {end}")
    # print("--------------------------------------------")
    # run_optimisation_between_dates(start, end)


    start = '01/08/2021'
    end = '31/12/2021'

    print(f"\nResults between {start} and {end}")
    print("--------------------------------------------")
    run_optimisation_between_dates(start, end)
