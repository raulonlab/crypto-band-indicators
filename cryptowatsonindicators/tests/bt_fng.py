import backtrader as bt
from cryptowatsonindicators import strategies, datas

start_date = '01/01/2021'    # start date of the simulation
buy_frequency_days = 5       # Number of days between purchases
buy_amount = 100             # Amount purchased in standard DCA
weight_type = ""             # TBD

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    cerebro.addstrategy(strategies.FngStrategy, buy_amount=buy_amount,
                    buy_frequency_days=buy_frequency_days, weight_type=weight_type, log=False, debug=False)

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
    cerebro.plot(volume=False) # iplot=False, style='bar' , stdstats=False
