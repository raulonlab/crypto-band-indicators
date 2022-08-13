from datetime import timedelta
import backtrader as bt
from cryptowatsonindicators import RwaIndicator, utils


class RwaIndicatorWrapper(bt.Indicator, RwaIndicator):
    lines = ('band_index',)

    params = (('ticker_symbol', 'BTCUSDT'), )

    def next(self):
        band_index = self.get_rainbow_band_index(
            price=self.data.close[0], at_date=self.data.datetime.date())

        if not band_index:
            band_index = self.last_valid_band_index

        self.lines.band_index[0] = int(band_index)

        self.last_valid_band_index = band_index


class RwaStrategy(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        buy_amount=100,        # Amount purchased in standard DCA
        buy_frequency_days=3,  # Number of days between buys
        weight_type="fibs",    # "fibs" or "original"
        log=True,              # Enable log messages
        debug=False,            # Enable debug messages
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
        self.rwa = RwaIndicatorWrapper(
            self.data, weight_type=self.params.weight_type)

        self.price = self.datas[0].close

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
            self.debug(f"  ...skip: still to soon to buy")
            return

        rwa_info = RwaIndicator._get_rainbow_info_by_index(
            int(self.rwa.band_index[0]))
        multiplier = rwa_info['original_multiplier']
        if (self.params.weight_type == 'fibs'):
            multiplier = rwa_info['fibs_multiplier']

        buy_dol_size = self.params.buy_amount * multiplier
        buy_btc_size = buy_dol_size / self.price[0]
        self.log(
            f"{utils.Emojis.BUY} BUY {buy_btc_size:.6f} BTC = {buy_dol_size:.2f} USD, Band: ({rwa_info['band_ordinal']}) {rwa_info['name']}, BTC price: {self.price[0]:.4f}", log_color=utils.LogColors.BOLD)

        # Keep track of the created order to avoid a 2nd order
        self.order = self.buy(size=buy_btc_size)
