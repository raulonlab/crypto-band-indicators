import backtrader as bt

class BtcSentiment(bt.Strategy):
    params = (('period', 10), ('devfactor', 1),)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def __init__(self):
        self.btc_price = self.datas[0].close
        self.google_sentiment = self.datas[1].close
        self.bbands = bt.indicators.BollingerBands(
            self.google_sentiment, period=self.params.period, devfactor=self.params.devfactor)

        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, {order.executed.price:.2f}')
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def next(self):
        # Check for open orders
        if self.order:
            return

        # Long signal
        if self.google_sentiment > self.bbands.lines.top[0]:
            # Check if we are in the market
            if not self.position:
                self.log(
                    f'Google Sentiment Value: {self.google_sentiment[0]:.2f}')
                self.log(f'Top band: {self.bbands.lines.top[0]:.2f}')
                # We are not in the market, we will open a trade
                self.log(f'***BUY CREATE {self.btc_price[0]:.2f}')
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        # Short signal
        elif self.google_sentiment < self.bbands.lines.bot[0]:
            # Check if we are in the market
            if not self.position:
                self.log(
                    f'Google Sentiment Value: {self.google_sentiment[0]:.2f}')
                self.log(f'Bottom band: {self.bbands.lines.bot[0]:.2f}')
                # We are not in the market, we will open a trade
                self.log(f'***SELL CREATE {self.btc_price[0]:.2f}')
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

        # Neutral signal - close any open trades
        else:
            if self.position:
                # We are in the market, we will close the existing trade
                self.log(
                    f'Google Sentiment Value: {self.google_sentiment[0]:.2f}')
                self.log(f'Bottom band: {self.bbands.lines.bot[0]:.2f}')
                self.log(f'Top band: {self.bbands.lines.top[0]:.2f}')
                self.log(f'CLOSE CREATE {self.btc_price[0]:.2f}')
                self.order = self.close()
