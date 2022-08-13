import backtrader as bt
from cryptowatsonindicators import strategies, datas, RwaIndicator
import pprint
pprint = pprint.PrettyPrinter(
    indent=2, sort_dicts=False, compact=False).pprint   # pprint with defaults

# Global variables
ticker_symbol = "BTCUSDT"      # currently only works with BTCUSDT
start_date = '01/01/2021'    # start date of the simulation
buy_frequency_days = 5       # Number of days between purchases
buy_amount = 100             # Amount purchased in standard DCA
weight_type = "fibs"         # "fibs" or "originaldca"
# use your binance keys or leave blank to use Binance's testnet
binance_api_key = ''
binance_secret_key = ''

# Enable / diable parts to bo tested
run_get_value_test = True
run_plot_test = True
run_backtrader_test = True

# Limit indicator series to start at specific date or None to use all the history
indicator_start_date = None
rwa = RwaIndicator(indicator_start_date, ticker_symbol,
                   binance_api_key, binance_secret_key)


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

    cerebro.addstrategy(strategies.RwaStrategy, buy_amount=buy_amount,
                        buy_frequency_days=buy_frequency_days, weight_type=weight_type, log=True, debug=False)

    # Get data feed
    ticker_data = datas.get_nasdaq_ticker_time_series(start_date=start_date)

    ticker_data_feed = bt.feeds.PandasData(
        dataname=ticker_data,
        datetime=0,
        high=None,
        low=None,
        open=1,     # uses the column 1 ('Value') as open price
        close=1,    # uses the column 1 ('Value') as close price
        volume=None,
        openinterest=None,
    )

    # Add the Data Feed to Cerebro
    cerebro.adddata(ticker_data_feed)

    # Add cash to the virtual broker
    # cerebro.broker.setcash(100000.0)    # default: 10k

    start_portfolio_value = cerebro.broker.getvalue()

    cerebro.run()

    end_portfolio_value = cerebro.broker.getvalue()
    pnl_value = end_portfolio_value - start_portfolio_value
    pnl_percent = (pnl_value / start_portfolio_value) * 100
    pnl_sign = '' if pnl_value < 0 else '+'

    # print("----------------------------------------")
    print(f"{'Start value:':<12} {start_portfolio_value:2f} USD")
    print(f"{'Final value:':<12} {end_portfolio_value:2f}  USD")
    print(f"{'PnL:':<11} {pnl_sign}{pnl_value:.2f} USD ({pnl_sign}{pnl_percent:.2f}%)")

    cerebro.plot(volume=False)  # iplot=False, style='bar' , stdstats=False


if __name__ == '__main__':
    if run_get_value_test == True:
        get_value_test()
    if run_plot_test == True:
        plot_test()
    if run_backtrader_test:
        backtrader_test()
