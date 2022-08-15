import backtrader as bt
from cryptowatsonindicators import utils


class LoggerStrategy(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        log=True,              # Enable log messages
        debug=False,           # Enable debug messages
    )

    def log(self, txt, price=None, dt=None, log_color=None):
        if (self.params.log != True):
            return

        dt = dt or self.datas[0].datetime.date(0)
        if isinstance(dt, float):
            dt = bt.num2date(dt).date()

        log_parts = list(f"{dt.isoformat()}: {txt}")

        if price:
            log_parts.append(f". Price = {price:.2f}")

        if log_color:
            log_parts.insert(0, log_color)
            log_parts.append(utils.LogColors.ENDC)

        print(''.join(log_parts))

    def debug(self, txt, price=None, dt=None, log_color=utils.LogColors.DEBUG):
        if (self.params.debug != True):
            return

        self.log(txt=txt, price=price, dt=dt, log_color=log_color)


class OrderLoggerStrategy(LoggerStrategy):
    order = None
    last_bar_executed = None

    def notify_order(self, order):
        if not self.order:
            return

        if order.status in [order.Submitted]:
            self.debug(f'  SUBMITTED', dt=order.created.dt)
            self.order = order
            return
        elif order.status in [order.Accepted]:
            self.debug(f'  ACCEPTED', dt=order.created.dt)
            self.order = order
            return

        if order.status in [order.Completed]:
            order_status_log_prefix = '  ORDER COMPLETED'
            if order.isbuy():
                order_status_log_prefix = '  BUY COMPLETED'
            elif order.issell():
                order_status_log_prefix = '  SELL COMPLETED'

            self.log(f'{order_status_log_prefix}, size: {order.executed.size:.6f} BTC = {order.executed.value:.2f} USD, comm {order.executed.comm:.2f}, 1 BTC = {order.executed.price:.2f} USD',
                     log_color=utils.LogColors.BUY)

            self.last_bar_executed = len(self)

        elif order.status in [order.Canceled]:
            self.log(f'  CANCELED')
        elif order.status in [order.Margin]:
            self.log(f'  MARGIN')
        elif order.status in [order.Rejected]:
            self.log(f'  REJECTED')
        elif order.status in [order.Expired]:
            self.log(f'  EXPIRED')

        if self.position:
            self.debug(
                f"  CURRENT POSITION: {self.position.size:.6f} BTC = {(self.position.size * self.price[0]):.2f} USD, TOTAL: {self.broker.getvalue():.2f} USD")

        # Sentinel to None: new orders allowed
        self.order = None


    def get_last_bar_executed_ago(self):
        return (self.last_bar_executed - len(self)) if self.last_bar_executed is not None else None
