import backtrader as bt
from cryptowatsonindicators import strategies, datas, FngIndicator
import pprint
pprint = pprint.PrettyPrinter(
    indent=2, sort_dicts=False, compact=False).pprint   # pprint with defaults

# Global variables
strategy             = "weighted_dca"    # Select strategy between "weighted_dca" and "rebalance"
ticker_symbol        = "BTCUSDT"      # currently only works with BTCUSDT
start_date           = '01/12/2021'   # start date of the simulation. Ex: '01/08/2020' or None
end_date             = None           # end date of the simulation. Ex: '01/08/2020' or None
initial_cash         = 10000.0        # initial broker cash. Default 10000 usd
min_order_period     = 5              # Minimum period in days to place orders
weighted_buy_amount  = 100            # Amount purchased in standard DCA
weighted_multipliers = [1.5, 1.25, 1, 0.75, 0.5]    # order amount multipliers (weighted) for each index
rebalance_percents   = [85, 65, 50, 15, 10]         # rebalance percentages for each index

# logging
log=True
debug=True

# Enable / diable parts to bo tested
run_get_value_test = False
run_plot_test = False
run_backtrader_test = True

# Limit indicator series to start at specific date or None to use all the history
indicator_start_date = None
fng = FngIndicator(indicator_start_date, ticker_symbol)


def get_value_test():
    # Get Current Fear and Greed index
    fng_value = fng.get_current_fng_value()
    fng_details = FngIndicator._get_fng_value_details(fng_value)
    print('Current FnG:')
    pprint(fng_details)

    # Get Fear and Greed index at date
    at_date = '01/02/2021'    # date when look up the Fng

    fng_value = fng.get_fng_value(at_date=at_date)
    fng_details = FngIndicator._get_fng_value_details(fng_value)
    print(f"FnG at {at_date}:")
    pprint(fng_details)


def plot_test():
    fng.plot_fng_and_ticker_price()


def backtrader_test():
    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    if strategy == "weighted_dca":
        cerebro.addstrategy(strategies.FngWeightedAverageStrategy, weighted_buy_amount=weighted_buy_amount,
                        min_order_period=min_order_period, weighted_multipliers=weighted_multipliers, log=log, debug=debug)
    elif strategy == "rebalance":
        cerebro.addstrategy(strategies.FngRebalanceStrategy, min_order_period=min_order_period, rebalance_percents=rebalance_percents, log=log, debug=debug)
    else:
        error_message = f"Invalid strategy: '{strategy}'"
        print(f"Error: {error_message}")
        return

    # Get data feed
    ticker_data = datas.get_nasdaq_ticker_time_series(start_date=start_date)
    fng_data = datas.get_fng_time_series(start_date=start_date)

    # Resample data series
    ticker_data, fng_data = datas.resample_time_series(ticker_data, fng_data, date_column_name='Date', start_date=start_date, end_date=end_date)

    # print('ticker_data: \n', ticker_data.tail())
    # print('fng_data: \n', fng_data.tail())
    # return

    ticker_data_feed = bt.feeds.PandasData(
        dataname=ticker_data,
        datetime=list(ticker_data.columns).index("Date"),
        high=None,
        low=None,
        open=list(ticker_data.columns).index("Value"),     # uses the column 1 ('Value') as open price
        close=list(ticker_data.columns).index("Value"),    # uses the column 1 ('Value') as close price
        volume=None,
        openinterest=None,
    )

    fng_data_feed = bt.feeds.PandasData(
        dataname=fng_data,
        datetime=list(fng_data.columns).index("Date"),
        high=None,
        low=None,
        open=None,
        close=list(fng_data.columns).index("Value"),    # uses the column 1 ('Value') as close price
        volume=None,
        openinterest=None,
    )

    # Add the data to Cerebro
    cerebro.adddata(ticker_data_feed)
    cerebro.adddata(fng_data_feed)

    # Add cash to the virtual broker
    cerebro.broker.setcash(initial_cash)    # default: 10k

    start_portfolio_value = cerebro.broker.getvalue()

    cerebro.run()

    position = cerebro.getbroker().getposition(data=ticker_data_feed)
    print('position: ', position.size, ' ', position.price)
    end_position_value = position.size * position.price
    end_portfolio_value = cerebro.broker.getvalue() + end_position_value
    
    pnl_value = end_portfolio_value - start_portfolio_value
    pnl_percent = (pnl_value / start_portfolio_value) * 100
    pnl_sign = '' if pnl_value < 0 else '+'

    # print("----------------------------------------")
    print(f"{'Start value:':<12} {start_portfolio_value:2f} USD")
    print(f"{'Final value:':<12} {end_portfolio_value:2f}  USD")
    print(f"{'PnL:':<11} {pnl_sign}{pnl_value:.2f} USD ({pnl_sign}{pnl_percent:.2f}%)")

    # cerebro.plot(volume=False)  # iplot=False, style='bar' , stdstats=False


if __name__ == '__main__':
    if run_get_value_test == True:
        get_value_test()
    if run_plot_test == True:
        plot_test()
    if run_backtrader_test:
        backtrader_test()
