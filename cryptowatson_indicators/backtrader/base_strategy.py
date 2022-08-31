import os
import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from cryptowatson_indicators import utils


class CryptoStrategy(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        ma_class=None,          # Optional parameter to smooth ma to data
        log=bool(os.environ.get('ENABLE_LOG', False)),              # Enable log messages
        debug=bool(os.environ.get('ENABLE_DEBUG', False)),           # Enable debug messages
    )

    def __init__(self):
        self.order = None
        self.last_bar_executed = None
        self.executed_orders = list()
        self.start_value = 0
        self.start_cash = 0
        self.end_value = 0
        self.end_cash = 0
        self.pnl_value = 0
        self.pnl_percent = 0.0
        self.roi = 0.0

        self.ma = None      # If subclasses doesn't implement ma
    
    def start(self):
        self.start_value = self.broker.getvalue()
        self.start_cash = self.broker.get_cash()  # keep the starting cash

    def stop(self):
        # calculate the actual returns
        self.end_value = self.broker.getvalue()
        self.end_cash = self.broker.get_cash()
        self.pnl_value = self.end_value - self.start_value
        self.pnl_percent = (self.pnl_value / self.start_value) * 100
        self.roi = (self.end_value / self.start_value) - 1.0
        # print('ROI:        {:.2f}%'.format(100.0 * self.roi))
        # print('CryptoStrategy:stop():str(self): ', str(self))
    
    def describe(self, keys = None):
        self_dict = {'name': str(self), 'start_value': self.start_value, 'end_value': self.end_value, 'pnl_value': self.pnl_value, 'pnl_percent': self.pnl_percent }
        if keys is not None:
            self_dict = {key: self_dict[key] for key in keys}
        
        return self_dict

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
            log_color = utils.LogColors.ENDC
            if order.isbuy():
                self.executed_orders.append(order)
                order_status_log_prefix = '  BUY COMPLETED'
                log_color = utils.LogColors.BUY
            elif order.issell():
                self.executed_orders.append(order)
                order_status_log_prefix = '  SELL COMPLETED'
                log_color = utils.LogColors.SELL

            self.log(f'{order_status_log_prefix}, size: {order.executed.size:.6f} BTC = {order.executed.value:.2f} USD, comm {order.executed.comm:.2f}, 1 BTC = {order.executed.price:.2f} USD',
                     log_color=log_color)

            self.last_bar_executed = len(self)

        elif order.status in [order.Canceled]:
            self.log(f"  {'BUY' if order.isbuy() else 'SELL'} CANCELLED... ",
                     log_color=utils.LogColors.FAIL)
        elif order.status in [order.Margin]:
            self.log(f"  {'BUY' if order.isbuy() else 'SELL'} NOT EXECUTED: not enough cash to execute the order... ",
                     log_color=utils.LogColors.WARNING)
        elif order.status in [order.Rejected]:
            self.log(f"  {'BUY' if order.isbuy() else 'SELL'} REJECTED... ",
                     log_color=utils.LogColors.FAIL)
        elif order.status in [order.Expired]:
            self.log(f"  {'BUY' if order.isbuy() else 'SELL'} EXPIRED... ",
                     log_color=utils.LogColors.FAIL)

        if self.position:
            current_btc_price = self.data0.close[0]
            self.debug(
                f"  CURRENT POSITION: {self.position.size:.6f} BTC = {(self.position.size * current_btc_price):.2f} USD, TOTAL: {self.broker.getvalue():.2f} USD")

        # Sentinel to None: new orders allowed
        self.order = None

    def get_last_bar_executed_ago(self):
        return (self.last_bar_executed - (len(self) + 1)) if self.last_bar_executed is not None else None

    def plot_axes_orders(self, axes):
        # Build orders dataframe
        orders_list = list()
        for order in self.executed_orders:
            orders_list.append({
                'date': order.executed.dt,
                'size': order.executed.size,
                'value': order.executed.value,
                'price': order.executed.price,
                'type': 'buy' if order.isbuy() else 'sell'
            })

        order_data = pd.DataFrame(orders_list, columns=['date', 'size', 'value', 'price', 'type'])
        order_data['date'] = pd.to_datetime(order_data['date'].apply(
            lambda x: bt.num2date(x).date()))
        # Set index
        order_data = order_data.set_index('date', drop=True)

        buy_order_data = order_data[order_data['type'] == 'buy']
        sell_order_data = order_data[order_data['type'] == 'sell']
        axes.scatter(buy_order_data.index, buy_order_data['price'],
                     color='#33aa33', marker="^")
        axes.scatter(sell_order_data.index, sell_order_data['price'],
                     color='#aa3333', marker="v")
        
        # Add xticks on the top
        buy_sell_xaxis = axes.twiny()
        # https://matplotlib.org/stable/gallery/text_labels_and_annotations/date.html#sphx-glr-gallery-text-labels-and-annotations-date-py
        buy_sell_xaxis.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))
        # buy_sell_xaxis.tick_params(axis='x', labelrotation=45, direction='out', labelsize='x-small')
        buy_sell_xaxis.set(xlim=axes.get_xlim(), xticks=order_data.index.to_list())
        for label in buy_sell_xaxis.get_xticklabels(which='major'):
            label.set(rotation=45, horizontalalignment='left', fontsize='small')

        for order_date in buy_order_data.index.to_list():
          axes.axvline(order_date, color='green', linestyle = '--', linewidth = 0.5)  # alpha=0.5
        for order_date in sell_order_data.index.to_list():
          axes.axvline(order_date, color='red', linestyle = '--', linewidth = 0.5)  # alpha=0.5

        return axes


    def plot_axes_order_vlines(self, axes):
        # Build orders dataframe
        orders_list = list()
        for order in self.executed_orders:
            orders_list.append({
                'date': order.executed.dt,
                'type': 'buy' if order.isbuy() else 'sell'
            })

        order_data = pd.DataFrame(orders_list)
        order_data['date'] = pd.to_datetime(order_data['date'].apply(
            lambda x: bt.num2date(x).date()))
        # Set index
        order_data = order_data.set_index('date', drop=True)

        buy_order_data = order_data[order_data['type'] == 'buy']
        sell_order_data = order_data[order_data['type'] == 'sell']
        
        for order_date in buy_order_data.index.to_list():
          axes.axvline(order_date, color='green', linestyle = '--', linewidth = 0.5)  # alpha=0.5
        for order_date in sell_order_data.index.to_list():
          axes.axvline(order_date, color='red', linestyle = '--', linewidth = 0.5)  # alpha=0.5

        return axes

class CheatOnOpenCryptoStrategy(CryptoStrategy):
    def __init__(self):
        super().__init__()
        self.cheating = self.cerebro.p.cheat_on_open

    def nextstart(self):
        if self.cheating:
            return
        self.do_nextstart()

    def prenext(self):
        if self.cheating:
            return
        self.do_prenext()

    def next(self):
        if self.cheating:
            return
        self.do_next()

    def nextstart_open(self):
        if not self.cheating:
            return
        self.do_nextstart()

    def prenext_open(self):
        if not self.cheating:
            return
        self.do_prenext()

    def next_open(self):
        if not self.cheating:
            return
        self.do_next()

    def do_nextstart(self):
        pass

    def do_prenext(self):
        pass

    def do_next(self):
        pass


