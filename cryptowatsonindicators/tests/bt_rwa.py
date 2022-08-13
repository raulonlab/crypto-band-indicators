import backtrader as bt
from cryptowatsonindicators import strategies, datas

start_date = '01/01/2020'    # start date of the simulation
buy_frequency = 7            # Number of days between purchases
buy_amount = 100             # Amount purchased in standard DCA
weight_type = "fibs"         # "fibs" or "originaldca"

# Create a cerebro entity
cerebro = bt.Cerebro(stdstats=False)

# Add RWA strategy
# params:
# buy_amount = 100,       # Amount purchased in standard DCA
# buy_frequency_days = 3, # Number of days between buys
# weight_type = "fibs",    # "fibs" or "original"
# debug = True,            # Enable debug messages
cerebro.addstrategy(strategies.RwaStrategy, buy_amount=100,
                    buy_frequency_days=3, weight_type="fibs", debug=False)

# Get data
ticker_data = datas.get_nasdaq_ticker_time_series()

# Get only the n last tickers
ticker_data_filtered = ticker_data.tail(30)
# print('ticker_data_filtered: \n', ticker_data_filtered)

if __name__ == '__main__':
    data = bt.feeds.PandasData(
        dataname=ticker_data_filtered,
        datetime=0,
        high=None,
        low=None,
        open=1,
        close=1,    # uses the column 1 ('Value') as close price
        volume=None,
        openinterest=None,
    )

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Add cash to the virtual broker
    # cerebro.broker.setcash(100000.0)    # default: 10k

    start_portfolio_value = cerebro.broker.getvalue()
    cerebro.run()
    end_portfolio_value = cerebro.broker.getvalue()
    pnl = end_portfolio_value - start_portfolio_value

    print(f'Starting Portfolio Value: {start_portfolio_value:2f}')
    print(f'Final Portfolio Value: {end_portfolio_value:2f}')
    print(f'PnL: {pnl:.2f}')
