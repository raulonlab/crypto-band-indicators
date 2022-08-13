from datetime import timedelta
import backtrader as bt
from cryptowatsonindicators import Rwa, utils

class RwaIndicator(bt.Indicator):
    lines = ('band_index', 'weight_multiplier')

    params = (('weight_type', 'fibs'),)

    def __init__(self):
        self.rwa = Rwa()


    def next(self):
        band = self.rwa.get_rainbow_band(
            price=self.data.close[0], at_date=self.data.datetime.date())
        
        self.lines.band_index[0] = int(band.get('band_index'))
        if self.params.weight_type == 'fibs':
            self.lines.weight_multiplier[0] = float(
                band.get('band_fib_multiplier'))
        else:
            self.lines.weight_multiplier[0] = float(
                band.get('band_original_multiplier'))


class RwaStrategy(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        buy_amount=100,        # Amount purchased in standard DCA
        buy_frequency_days=3,  # Number of days between buys
        weight_type="fibs",    # "fibs" or "original"
        log=True,              # Enable log messages
        debug=True,            # Enable debug messages
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

    def debug(self, txt, price=None, dt=None, log_color=utils.LogColors.LIGHT):
        if (self.params.debug != True):
            return
        
        self.log(txt=txt, price=price, dt=dt, log_color=log_color)

    def __init__(self):
        self.rwa = RwaIndicator(self.data, weight_type=self.params.weight_type)
        # self.bbands = bt.indicators.BollingerBands(self.data,
        #         period=self.params.period, devfactor=self.params.devfactor)

        self.price = self.datas[0].close

        # self.last_order_executed_at = self.data.datetime.date(-1 * self.params.buy_frequency_days)
        self.last_order_executed_at = None
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted]:
            self.debug(f'  SUBMITTED', dt=order.created.dt)
            self.order = order
            return
        elif order.status in [order.Accepted]:
            self.debug(f'  ACCEPTED', dt=order.created.dt)
            self.order = order
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'  COMPLETED (BUY), size: {order.executed.size:.6f} BTC, cost {order.executed.value:.2f}, comm {order.executed.comm:.2f}',
                         price=order.executed.price, log_color=utils.LogColors.OKGREEN)
            elif order.issell():
                self.log(f'  COMPLETED (SELL), size: {order.executed.size:.6f} BTC, cost {order.executed.value:.2f}, comm {order.executed.comm:.2f}',
                         price=order.executed.price, log_color=utils.LogColors.OKCYAN)
            self.bar_executed = len(self)
            self.last_order_executed_at = self.data.datetime.date()

        elif order.status in [order.Canceled]:
            self.debug(f'  CANCELED')
        elif order.status in [order.Margin]:
            self.debug(f'  MARGIN')
        elif order.status in [order.Rejected]:
            self.debug(f'  REJECTED')
        elif order.status in [order.Expired]:
            self.ldebugg(f'  EXPIRED')

        if self.position:
            self.log(
                f"{utils.Emojis.MONEY} {self.position.size:.6f} BTC, {(self.position.size * self.price[0]):.2f} USD")

        # Sentinel to None: new orders allowed
        self.order = None

    def next(self):
        # An order is pending ... nothing can be done
        if self.order:
            self.debug(f"  ...skip: order in progress")
            return

        # Only buy every buy_frequency_days days
        if self.last_order_executed_at is not None and (self.data.datetime.date() - self.last_order_executed_at) < timedelta(self.params.buy_frequency_days):
            # if self.position:
            #     self.order = self.close()
            self.debug(f"  ...skip: still to soon to buy")
            return

        # Long signal: it's time to buy!
        # if self.rwa.band_index[0] > self.rwa.band_index[-1]:
        # if not self.position:

        rwa_info = Rwa._get_rainbow_info_by_index(
            int(self.rwa.band_index[0]))
        buy_dol_size = self.params.buy_amount * self.rwa.weight_multiplier[0]
        buy_btc_size = buy_dol_size / self.price[0]
        self.log(
            f"{utils.Emojis.BUY} BUY {buy_btc_size:.6f} BTC = {buy_dol_size:.2f} USD, Band: ({rwa_info['band_ordinal']}) {rwa_info['band_name']}, BTC price: {self.price[0]:.4f}", log_color=utils.LogColors.BOLD)

        # Keep track of the created order to avoid a 2nd order
        # price=self.price[0], size=buy_btc_size, exectype=bt.Order.Close,
        self.order = self.buy(size=buy_btc_size)


# print datas examples
# Print band in the current line
# print('self.rwa[0]: ', self.rwa[0])
# print('self.rwa.band_index[0]: ', self.rwa.band_index[0])

# print(f"type(self.price) = {type(self.price)}")
# print(f"type(self.at_date) = {type(self.at_date)}")

# print('self.datas[0].datetime.date(0): ', self.datas[0].datetime.date(0))
# print('self.datas[0].datetime.date(): ', self.datas[0].datetime.date())
# print('self.data.datetime.date(): ', self.data.datetime.date())

# print('self.datas[0].close[0]: ', self.datas[0].close[0])
# print('self.data.lines.close[0]: ', self.data.lines.close[0])
# print('self.price[0]: ', self.price[0])
# print('self.datas[0].datetime.date(): ', self.datas[0].datetime.date())
# # print('self.datas[0].datetime[0]: ', self.datas[0].datetime[0])
# print('self.data.datetime.date(0): ',self.data.datetime.date(0))

# print('len(self.data.close): ',len(self.data.close))
# print('len(self.data.datetime): ',len(self.data.datetime))
# print('len(self.data.lines): ',len(self.data.lines))
# print('len(self.data): ',len(self.data))
# print('len(self): ',len(self))
