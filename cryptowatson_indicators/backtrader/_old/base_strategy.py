from datetime import date
from pprint import pprint
import backtrader as bt
import numpy as np
import pandas as pd
from cryptowatson_indicators import utils


class CryptoStrategy_old(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        log=True,              # Enable log messages
        debug=False,           # Enable debug messages
    )

    def __init__(self):
        self.order = None
        self.last_bar_executed = None
        self.executed_orders = list()

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

    def plot_axes(self, axes):
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

        order_data = pd.DataFrame(orders_list)
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

        return axes


class CheatOnOpenCryptoStrategy_old(CryptoStrategy_old):
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


class WeightedAverageStrategy_old(CryptoStrategy_old):
    # list of parameters which are configurable for the strategy
    params = dict(
        base_buy_amount=100,        # Amount purchased in standard DCA
        min_order_period=7,             # Number of days between buys
        weighted_multipliers=[1],
    )

    def plot_axes(self, axes, show_legend=True, show_params=False):
        # axes.margins(x=0)
        axes.set_ylabel('Weighted Average', fontsize='medium')

        steps_data_x = list()
        steps_data_y = list()
        for order in self.executed_orders:
            steps_data_x.append(bt.num2date(order.executed.dt).date())
            steps_data_y.append(float(order.info.weighted_multiplier))

        # Add extra last step with same last value
        steps_data_x.append(date.today())
        steps_data_y.append(steps_data_y[-1])

        # Plot rebalance steps
        axes.fill_between(steps_data_x, steps_data_y,
                          color=utils.PlotColors.GOLD, step="post", alpha=0.4, label='Weighted multiplier')
        axes.step(steps_data_x, steps_data_y,
                  color=utils.PlotColors.GOLD, where='post')

        axes.set(ylim=(0, max(steps_data_y)),
                 yticks=self.params.weighted_multipliers)

        if show_legend:
            axes.legend()

        if show_params:
            params_str = vars(self.params)
            # params_str = vars(
            #     {k: v for k, v in vars(self.params).items() if k in ['min_order_period', 'base_buy_amount', 'weighted_multipliers']})
            axes.annotate(params_str,
                          xy=(1.0, -0.2),
                          xycoords='axes fraction',
                          ha='right',
                          va="center",
                          fontsize='small')

        return axes


class RebalanceStrategy_old(CryptoStrategy_old):
    # list of parameters which are configurable for the strategy
    params = dict(
        min_order_period=7,  # Number of days between buys
        # position percents by indicator index
        rebalance_percents=[100],
    )

    def rebalance(self, percent: float):
        current_value = self.broker.getvalue()
        current_btc_price = self.data0.close[0]

        if self.position:
            current_position_value = self.position.size * current_btc_price
        else:
            current_position_value = 0

        rebalance_position_value = current_value * \
            percent / 100    # desired position value in USDT

        order_dol_size = abs(rebalance_position_value) - current_position_value
        order_btc_size = order_dol_size / current_btc_price

        self.debug(
            f"  - current_position_value: {current_position_value:.2f} USD")
        self.debug(
            f"  - rebalance_position_value: {rebalance_position_value:.2f} USD")
        self.debug(f"  - order_dol_size: {order_dol_size:.2f} USD")
        self.debug(f"  - order_btc_size: {order_btc_size:.6f} BTC")

        # Do nothing if rebalance value is the same than current value
        if int(rebalance_position_value) == int(current_position_value):
            self.log(
                f"  REBALANCE SKIPPED: already rebalanced at {percent}%", log_color=utils.LogColors.STRATEGY)
        # Buy
        elif rebalance_position_value > current_position_value:
            self.log(
                f"{utils.Emojis.BUY} BUY {order_btc_size:.6f} BTC = {order_dol_size:.2f} USD, 1 BTC = {current_btc_price:.2f} USD", log_color=utils.LogColors.BOLDBUY)
            # Keep track of the created order to avoid a 2nd order
            self.order = self.buy(size=abs(order_btc_size),
                                  rebalance_percent=percent)
            # self.order.addinfo(rebalance_percent=percent)

        # Sell
        else:
            self.log(
                f"{utils.Emojis.SELL} SELL {order_btc_size:.6f} BTC = {order_dol_size:.2f} USD, 1 BTC = {current_btc_price:.2f} USD", log_color=utils.LogColors.BOLDSELL)
            # Keep track of the created order to avoid a 2nd order
            self.order = self.sell(size=order_btc_size,
                                   rebalance_percent=percent)

    def plot_axes(self, axes, show_legend=True, show_params=False):
        # axes.margins(x=0)
        axes.set_ylabel('Rebalance', fontsize='medium')

        steps_data_x = list()
        steps_data_y = list()
        for order in self.executed_orders:
            steps_data_x.append(bt.num2date(order.executed.dt).date())
            steps_data_y.append(float(order.info.rebalance_percent))

        # Add extra last step with same last value
        steps_data_x.append(date.today())
        steps_data_y.append(steps_data_y[-1])

        # Plot rebalance steps
        axes.fill_between(steps_data_x, steps_data_y,
                          color=utils.PlotColors.GOLD, step="post", alpha=0.4, label='% BTC / Total')
        axes.step(steps_data_x, steps_data_y,
                  color=utils.PlotColors.GOLD, where='post')

        axes.set(ylim=(0, 100),
                 yticks=self.params.rebalance_percents)

        if show_legend:
            axes.legend()

        if show_params:
            params_str = vars(self.params)
            # params_str = vars(
            #     {k: v for k, v in vars(self.params).items() if k in ['min_order_period', 'rebalance_percents']})
            axes.annotate(params_str,
                          xy=(1.0, -0.2),
                          xycoords='axes fraction',
                          ha='right',
                          va="center",
                          fontsize='small')

        return axes
