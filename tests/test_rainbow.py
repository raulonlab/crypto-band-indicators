import backtrader as bt
from crypto_band_indicators.backtrader import RebalanceStrategy, WeightedDCAStrategy
from crypto_band_indicators.datas import TickerDataSource
from crypto_band_indicators.indicators import RainbowBandIndicator
from crypto_band_indicators.utils.utils import LogColors
import pprint
pprint = pprint.PrettyPrinter(indent=2).pprint
import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = [10, 6]
plt.rcParams['figure.dpi'] = 100 # 200

# Variables #########################
strategy = "weighted_dca"    # Select strategy between "weighted_dca" and "rebalance"
start = '01/01/2020'   # start date of the simulation. Ex: '01/08/2020' or None
end = '01/01/2022'           # end date of the simulation. Ex: '01/08/2020' or None
initial_cash = 10000.0        # initial broker cash. Default 10000 usd
min_order_period = 6              # Minimum period in days to place orders
base_buy_amount = 100            # Amount purchased in standard DCA
# weighted_multipliers = [0, 0.1, 0.2, 0.35, 0.5, 0.75, 1, 2.5, 3]      # Default order amount multipliers (weighted) for each index
weighted_multipliers = [0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.3, 2.1, 3.4]    # Fibonacci order amount multipliers (weighted) for each index
rebalance_percents = [10, 20, 30, 40, 50, 60, 70, 80, 90]   # rebalance percentages for each index
ma_class = None
# ma_class = bt.ind.WeightedMovingAverage
# ma_class = bt.ind.MovingAverageSimple

# logging
log = True
debug = False

# Enable / diable parts to bo tested
run_get_value_test = True
run_plot_test = True
run_backtrader_test = True
run_plot_backtrader_result_test = True

# Data sources
ticker_data_source = TickerDataSource().load()

# Rainbow indicator
rainbow = RainbowBandIndicator(ticker_data_source.to_dataframe())

def get_value_test():
    # Get Current Rainbow band
    rainbow_details = rainbow.get_band_details_at()
    print('Current Rainbow Band:')
    pprint(rainbow_details)

    # Get Rainbow band at date
    at_date = '01/02/2021'    # date when look up the Fng
    price_at_date = 30000     # Price of BTC at date

    rainbow_details = rainbow.get_band_details_at(
        price=price_at_date, at_date=at_date)
    print(f"Rainbow Band at {at_date}:")
    pprint(rainbow_details)


def plot_test():
    rainbow.plot_rainbow()


def backtrader_test():
    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)  # cheat_on_open=True, broker_coo=True
    cerebro.broker.set_coc(True)

    if strategy == "weighted_dca":
        cerebro.addstrategy(WeightedDCAStrategy, 
                            indicator_class=RainbowBandIndicator,
                            ma_class=ma_class,
                            base_buy_amount=base_buy_amount,
                            min_order_period=min_order_period, 
                            weighted_multipliers=weighted_multipliers, 
                            log=log, 
                            debug=debug)
    elif strategy == "rebalance":
        cerebro.addstrategy(RebalanceStrategy, 
                            indicator_class=RainbowBandIndicator,
                            ma_class=ma_class,
                            min_order_period=min_order_period,
                            rebalance_percents=rebalance_percents, 
                            log=log, 
                            debug=debug)
    else:
        error_message = f"Invalid strategy: '{strategy}'"
        print(f"Error: {error_message}")
        return

    # Get data feed
    ticker_data_feed = ticker_data_source.to_backtrade_feed(start, end)

    # Add the Data Feed to Cerebro
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
    pnl_color = f"{LogColors.FAIL}" if end_portfolio_value < start_portfolio_value else f"{LogColors.OK}"

    print(f"\nResults of {str(cerebro_results[0])}")
    print("--------------------------------------------")
    print(f"{'Started:':<8} {start_portfolio_value:>10.2f} USD (1 BTC = {start_btc_price:.2f} USD)")
    print(f"{'Ended:':<8} {end_portfolio_value:>10.2f} USD ({end_position.size:6f} BTC + {end_cash:.2f} USD in cash | 1 BTC = {end_btc_price:.2f} USD)")
    print(f"{'PnL:':<8} {pnl_color}{pnl_value:>10.2f} USD ({pnl_percent:.2f}%){LogColors.ENDC}")

    if run_plot_backtrader_result_test:
        cerebro_results[0].plot()


if __name__ == '__main__':
    if run_get_value_test == True:
        get_value_test()
    if run_plot_test == True:
        plot_test()
    if run_backtrader_test:
        backtrader_test()
