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
                    buy_frequency_days=buy_frequency_days, weight_type=weight_type, debug=False)

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

    cerebro.plot(volume=False) # iplot=False, style='bar' , stdstats=False
