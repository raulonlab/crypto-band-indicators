from datetime import timedelta
import backtrader as bt
from cryptowatsonindicators import FngIndicator, utils
from .base_strategy import OrderLoggerStrategy
import pprint
pprint = pprint.PrettyPrinter(indent=2, sort_dicts=False, compact=False).pprint   # pprint with defaults

# class FngIndicatorWrapper(bt.Indicator, FngIndicator):
#     lines = ('fng_value', 'fng_av', 'fng_ma')

#     params = (('ticker_symbol', 'BTCUSDT'),)

#     def __init__(self):
#         self.fng = FngIndicator()

#         fng_data_feed = bt.feeds.PandasData(
#             dataname=self.fng.indicator_data,
#             datetime=0,
#             high=None,
#             low=None,
#             open=None,
#             close=1,    # uses the column 1 ('Value') as close price
#             volume=None,
#             openinterest=None,
#         )


#     def next(self):
#         fng_value = self.fng.get_fng_value(at_date=self.data.datetime.date())

#         if not fng_value:
#             fng_value = self.last_valid_fng_value

#         self.lines.fng_value[0] = int(fng_value)
#         self.last_valid_fng_value = fng_value



class FngWeightedAverageStrategy(OrderLoggerStrategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        weighted_buy_amount=100,        # Amount purchased in standard DCA
        min_order_period=7,  # Number of days between buys
        weighted_multipliers=[1.5, 1.25, 1, 0.75, 0.5],     # weighted_buy_amount multiplier by fng index
    )

    def __init__(self):
        self.fng_value = self.data1.close
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

        fng_info = FngIndicator._get_fng_value_details(
            int(self.fng_value[0]))
        buy_dol_size = self.params.weighted_buy_amount * self.params.weighted_multipliers[fng_info.get('index', 2)] 
        buy_btc_size = buy_dol_size / self.price[0]
        self.log(
            f"{utils.Emojis.BUY} BUY {buy_btc_size:.6f} BTC = {buy_dol_size:.2f} USD, FnG: ({fng_info['fng_ordinal']}) {fng_info['name']}, BTC price: {self.price[0]:.4f}", log_color=utils.LogColors.BOLD)

        # Keep track of the created order to avoid a 2nd order
        self.order = self.buy(size=buy_btc_size)
    


class FngRebalanceStrategy(OrderLoggerStrategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        min_order_period=7,  # Number of days between buys
        rebalance_percents=[83.3, 66.6, 50, 33.3, 16.6],    # position percents by Fng index
    )

    def __init__(self):
        # Indicators
        self.fng_value = self.data1.close
        # self.fng_av = bt.indicators.WeightedAverage(self.data1, period = self.params.min_order_period)
        self.fng_ma = bt.indicators.WeightedMovingAverage(self.data1, period = self.params.min_order_period)

        self.price = self.data.close

        self.order = None

    def nextstart(self):
        # Do a initial rebalance with the first FnG value
        fng_info = FngIndicator._get_fng_value_details(
            int(self.fng_value[0]))
        
        self.log(
                f"R REBALANCE (FIRST). Current FnG: ({fng_info['fng_ordinal']}) {fng_info['name']}, No previous FnG", log_color=utils.LogColors.OKCYAN)
        self.rebalance(self.params.rebalance_percents[fng_info.get('fng_index')])

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

        # Print last n days fng and ma
        # print(f"\n-- {self.data.datetime.date()} ----------------")
        # for i in range(-1 * (self.params.min_order_period - 1), 0):
        #     previous_fng_info = FngIndicator._get_fng_value_details(int(self.fng_value[i]))
        #     print(f"{i:<2}: value: {self.fng_value[i]:<3}, index: {previous_fng_info.get('fng_index')}")

        
        # Option 1: Rebalance if the the MA (of period min_order_period) and current fng is major than previous reblance fng
        fng_info = FngIndicator._get_fng_value_details(
            int(self.fng_value[0]))
        # print(f"0 : value: {self.fng_value[0]:<3}, index: {fng_info.get('fng_index')}")
        fng_ma_info = FngIndicator._get_fng_value_details(int(self.fng_ma[0]))
        # print(f"ma: value: {self.fng_ma[0]:<3}, index: {fng_ma_info.get('fng_index')}")
        last_bar_executed_fng_info = FngIndicator._get_fng_value_details(int(self.fng_value[last_bar_executed_ago]))
        # print(f"last bar executed: value: {self.fng_value[last_bar_executed_ago]:<3}, index: {last_bar_executed_fng_info.get('fng_index')}")
        
        if fng_info.get('fng_index') == fng_ma_info.get('fng_index') and fng_info.get('fng_index') != last_bar_executed_fng_info.get('fng_index'):
            self.log(
                f"R REBALANCE. Current FnG: ({fng_info['fng_ordinal']}) {fng_info['name']}, Previous FnG: ({last_bar_executed_fng_info['fng_ordinal']}) {last_bar_executed_fng_info['name']}", log_color=utils.LogColors.OKCYAN)
            self.rebalance(self.params.rebalance_percents[fng_info.get('fng_index')])

        # Option 2: Rebalance if the average index in the last min_order_period changes
        # ...



    def rebalance(self, percent: float):
        current_value = self.broker.getvalue()
        # print(f"CURRENT VALUE: {current_value:.2f} USD")
        if self.position:
            current_position_value = self.position.size * self.price[0]
        else:
            current_position_value = 0
        
        rebalance_position_value = current_value * percent / 100    # desired position value in USDT
        
        order_dol_size = abs(rebalance_position_value) - current_position_value
        order_btc_size = order_dol_size / self.price[0]

        self.debug(f"  - current_position_value: {current_position_value:.2f} USD")
        self.debug(f"  - rebalance_position_value: {rebalance_position_value:.2f} USD")
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
