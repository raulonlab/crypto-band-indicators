from datetime import timedelta
import backtrader as bt
from cryptowatson_indicators.indicators import RwaIndicator
from cryptowatson_indicators import utils
from .base_strategy import OrderLoggerStrategy


class RwaIndicatorWrapper(bt.Indicator, RwaIndicator):
    lines = ('band_index',)

    params = (('ticker_symbol', 'BTCUSDT'), )

    def next(self):
        band_index = self.get_rainbow_band_index(
            price=self.data.close[0], at_date=self.data.datetime.date())

        # if not band_index:
        #     band_index = self.last_valid_band_index

        self.lines.band_index[0] = int(band_index)

        # self.last_valid_band_index = band_index


class RwaWeightedAverageStrategy(OrderLoggerStrategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        weighted_buy_amount=100,        # Amount purchased in standard DCA
        min_order_period=7,  # Number of days between buys
        # order amount multipliers (weighted) for each index
        weighted_multipliers=[0, 0.1, 0.2, 0.35, 0.5, 0.75, 1, 2.5, 3]
    )

    def __init__(self):
        self.rwa_band_index = RwaIndicatorWrapper(
            self.data1)

        self.price = self.data.close

        self.order = None

    def next(self):
        # if self.position and not self.printed:
        #     print("\n----------------------------------------------")
        #     print('self.broker.cash:', self.broker.cash)
        #     print("----------------------------------------------\n")
        #     print('self.position.size:', self.position.size)
        #     self.printed = True

        # An order is pending ... nothing can be done
        if self.order:
            self.debug(f"  ...skip: order in progress")
            return

        # Only buy every min_order_period days
        last_bar_executed_ago = self.get_last_bar_executed_ago()
        if (last_bar_executed_ago is not None and (self.data.datetime.date() - self.data.datetime.date(last_bar_executed_ago)) < timedelta(self.params.min_order_period)):
            self.debug(f"  ...skip: still to soon to buy")
            return

        rwa_info = RwaIndicator._get_rainbow_info_by_index(
            int(self.rwa_band_index[0]))

        buy_dol_size = self.params.weighted_buy_amount * \
            self.params.weighted_multipliers[rwa_info.get('band_index', 2)]
        buy_btc_size = buy_dol_size / self.price[0]
        self.log(
            f"{utils.Emojis.BUY} BUY {buy_btc_size:.6f} BTC = {buy_dol_size:.2f} USD, Band: {rwa_info['band_ordinal']} - {rwa_info['name']}, 1 BTC = {self.price[0]:.4f} USD", log_color=utils.LogColors.BOLDBUY)

        # Keep track of the created order to avoid a 2nd order
        self.order = self.buy(size=buy_btc_size)


class RwaRebalanceStrategy(OrderLoggerStrategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        min_order_period=7,  # Number of days between buys
        # rebalance percentages for each index
        rebalance_percents=[10, 20, 30, 40, 50, 60, 70, 80, 90]
    )

    def __init__(self):
        # Indicators
        self.rwa_band_index = RwaIndicatorWrapper(
            self.data1)
        self.rwa_ma = bt.indicators.WeightedMovingAverage(
            self.rwa_band_index.l.band_index, period=self.params.min_order_period, subplot=False)

        self.price = self.data.close

        self.order = None

    def nextstart(self):
        # Do a initial rebalance with the first FnG value
        rwa_info = RwaIndicator._get_rainbow_info_by_index(
            int(self.rwa_band_index[0]))

        self.log(
            f"R REBALANCE (FIRST). Current Band: {rwa_info['band_ordinal']} - {rwa_info['name']}, No previous Rainbow Band", log_color=utils.LogColors.OKCYAN)
        self.rebalance(
            self.params.rebalance_percents[rwa_info.get('band_index')])

    def next(self):
        # An order is pending ... nothing can be done
        if self.order:
            self.debug(f"  ...skip: order in progress")
            return
        # No previous bar executed... nothing can be done
        if self.last_bar_executed is None:
            self.debug(f"  ...skip: no previous bar executed yet")
            return

        # Only buy every min_order_period days
        last_bar_executed_ago = self.get_last_bar_executed_ago()
        if (self.data.datetime.date() - self.data.datetime.date(last_bar_executed_ago)) < timedelta(self.params.min_order_period):
            self.debug(f"  ...skip: still to soon to buy")
            return

        # Rebalance if the the MA (of period min_order_period) and current rwa is major than previous reblance rwa
        rwa_info = RwaIndicator._get_rainbow_info_by_index(
            int(self.rwa_band_index[0]))
        # print(f"0 : value: {self.rwa_band_index[0]:<3}, index: {rwa_info.get('band_index')}")
        rwa_ma_info = RwaIndicator._get_rainbow_info_by_index(
            int(self.rwa_ma[0]))
        # print(f"ma: value: {self.rwa_ma[0]:<3}, index: {rwa_ma_info.get('band_index')}")
        last_bar_executed_rwa_info = RwaIndicator._get_rainbow_info_by_index(
            int(self.rwa_band_index[last_bar_executed_ago]))
        # print(f"last bar executed: value: {self.rwa_band_index[last_bar_executed_ago]:<3}, index: {last_bar_executed_rwa_info.get('band_index')}")

        if rwa_info.get('band_index') == rwa_ma_info.get('band_index') and rwa_info.get('band_index') != last_bar_executed_rwa_info.get('band_index'):
            self.log(
                f"R REBALANCE. Current Band: {rwa_info['band_ordinal']} - {rwa_info['name']}, Previous Band: {last_bar_executed_rwa_info['band_ordinal']} - {last_bar_executed_rwa_info['name']}", log_color=utils.LogColors.OKCYAN)
            self.rebalance(
                self.params.rebalance_percents[rwa_info.get('band_index')])
        else:
            self.debug(
                f"  ...skip: condition not fullfilled. Current Band: {rwa_info['band_ordinal']}, MA Band: {rwa_ma_info['band_ordinal']},  Previous Band: {last_bar_executed_rwa_info['band_ordinal']}")

    def rebalance(self, percent: float):
        current_value = self.broker.getvalue()

        if self.position:
            current_position_value = self.position.size * self.price[0]
        else:
            current_position_value = 0

        rebalance_position_value = current_value * \
            percent / 100    # desired position value in USDT

        order_dol_size = abs(rebalance_position_value) - current_position_value
        order_btc_size = order_dol_size / self.price[0]

        self.debug(
            f"  - current_position_value: {current_position_value:.2f} USD")
        self.debug(
            f"  - rebalance_position_value: {rebalance_position_value:.2f} USD")
        self.debug(f"  - order_dol_size: {order_dol_size:.2f} USD")
        self.debug(f"  - order_btc_size: {order_btc_size:.6f} BTC")

        # Buy
        if rebalance_position_value > current_position_value:
            self.log(
                f"{utils.Emojis.BUY} BUY {order_btc_size:.6f} BTC = {order_dol_size:.2f} USD, 1 BTC = {self.price[0]:.2f} USD", log_color=utils.LogColors.BOLDBUY)
            # Keep track of the created order to avoid a 2nd order
            self.order = self.buy(size=abs(order_btc_size))

        # Sell
        else:
            self.log(
                f"{utils.Emojis.SELL} SELL {order_btc_size:.6f} BTC = {order_dol_size:.2f} USD, 1 BTC = {self.price[0]:.2f} USD", log_color=utils.LogColors.BOLDSELL)
            # Keep track of the created order to avoid a 2nd order
            self.order = self.sell(size=order_btc_size)
