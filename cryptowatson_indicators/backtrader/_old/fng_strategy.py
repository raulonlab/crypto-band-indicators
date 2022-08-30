from datetime import timedelta
from pprint import pprint
import backtrader as bt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from cryptowatson_indicators.indicators import FngBandIndicator
from cryptowatson_indicators import utils
from .base_strategy import RebalanceStrategy_old, WeightedAverageStrategy_old


class FngIndicatorWrapper(bt.Indicator):
    lines = ('fng_index', 'fng_ma_index', )

    params = dict(
        ma_period=7,    # moving average period
    )

    def __init__(self):
        # self.addminperiod(self.params.ma_period)

        self.fng = FngBandIndicator()

        # MA of the strategy data
        # self.ma = bt.indicators.WeightedMovingAverage(
        #      self.data, period=self.params.ma_period, subplot=False)


    def next(self):
        bar_fng_value = self.fng.get_value_at(self.data.datetime.date())
        bar_fng_info = FngBandIndicator._get_fng_value_details(bar_fng_value)

        self.lines.fng_index[0] = int(bar_fng_info.get('fng_index'))
        self.lines.fng_ma_index[0] = self.lines.fng_index[0]    # TODO: Calculate fng MA


    def plot_axes(self, axes, start=None, end=None):
        return self.fng.plot_axes(axes, start=start, end=end)


class FngWeightedAverageStrategy(WeightedAverageStrategy_old):
    def __init__(self):
        super().__init__()

        # Indicators
        self.fng_indicator = FngIndicatorWrapper(ma_period=self.params.min_order_period)

        self.price = self.data.close

        # # Convert weighted_multipliers to list of floats if it's string (optimization case)
        # if (isinstance(self.params.weighted_multipliers, str)):
        #     self.params.weighted_multipliers = [
        #         float(e) for e in self.params.weighted_multipliers.split(' ')]

    def __str__(self):
        return 'Fear and Greed Weighted Av. DCA'

    def next(self):
        # An order is pending ... nothing can be done
        if self.order:
            self.debug(f"  ...skip: order in progress")
            return

        # Only buy every min_order_period days
        last_bar_executed_ago = self.get_last_bar_executed_ago()
        if last_bar_executed_ago is not None and (self.data.datetime.date() - self.data.datetime.date(last_bar_executed_ago) < timedelta(self.params.min_order_period)):
            self.debug(f"  ...skip: still to soon to buy")
            return

        fng_index = int(self.fng_indicator.fng_index[0])
        # fng_ma_index = int(self.fng_indicator.fng_ma_index[0])

        buy_dol_size = self.params.base_buy_amount * \
            self.params.weighted_multipliers[fng_index]
        buy_btc_size = buy_dol_size / self.price[0]
        self.log(
            f"{utils.Emojis.BUY} BUY {buy_btc_size:.6f} BTC = {buy_dol_size:.2f} USD, FnG: {fng_index + 1}, 1 BTC = {self.price[0]:.2f} USD", log_color=utils.LogColors.BOLDBUY)

        # Keep track of the created order to avoid a 2nd order
        self.order = self.buy(
            size=buy_btc_size, weighted_multiplier=self.params.weighted_multipliers[fng_index])

    def plot(self, show: bool = True):
        ticker_data = self.data._dataname

        gs_kw = dict(height_ratios=[2, 1, 1])
        fig, (ticker_axes, strategy_axes, indicator_axes) = plt.subplots(
            nrows=3, sharex=True, gridspec_kw=gs_kw, subplot_kw=dict(frameon=True))    # constrained_layout=True, figsize=(11, 7)
        fig.suptitle(str(self), fontsize='large')
        # fig.set_tight_layout(True)
        fig.subplots_adjust(hspace=0.1, wspace=0.1)

        plt.xticks(fontsize='small', rotation=45, ha='right')
        plt.yticks(fontsize='small')

        # Ticker chart ########
        ticker_axes.margins(x=0)
        ticker_axes.set_ylabel('Price', fontsize='medium')
        ticker_axes.plot(ticker_data.index, ticker_data['close'],
                         color='#333333', linewidth=1)
        
        # Plot Buy and sell scatters
        self.plot_axes(ticker_axes)

        # Strategy chart #########
        self.plot_axes(strategy_axes, show_params=True)

        # Fng indicator chart ########
        self.fng_indicator.plot_axes(indicator_axes, start = ticker_data.index.min(), end = ticker_data.index.max())
        
        # Calculate x ticks
        ticker_axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fng_data_length = len(ticker_data)
        xticks = ticker_data.iloc[::int(
            fng_data_length/20)].index.to_list()
        xticks[0] = ticker_data.index.min()
        xticks[-1] = ticker_data.index.max()

        # Calculate x limit
        xlim = [ticker_data.index.min(), ticker_data.index.max()]

        # Set x ticks and limits
        ticker_axes.set(xlim=xlim, xticks=xticks)
        strategy_axes.set(xlim=xlim, xticks=xticks)
        indicator_axes.set(xlim=xlim, xticks=xticks)

        # Show plot
        # plt.rcParams['figure.figsize'] = [12, 8]
        # plt.rcParams['figure.dpi'] = 200
        # plt.rcParams['savefig.dpi'] = 200
        if show:
            plt.show()

        return fig


class FngRebalanceStrategy(RebalanceStrategy_old):
    def __init__(self):
        super().__init__()

        # Indicators
        self.fng_indicator = FngIndicatorWrapper(ma_period=self.params.min_order_period)

        # Convert weighted_multipliers to list of floats if it's string (optimization case)
        # if (isinstance(self.params.rebalance_percents, str)):
        #     self.params.rebalance_percents = [
        #         float(e) for e in self.params.rebalance_percents.split(' ')]

    def __str__(self):
        return 'Fear and Greed Rebalance'

    def nextstart(self):
        # Do a initial rebalance with the first FnG value
        fng_index = int(self.fng_indicator.fng_index[0])

        self.log(
            f"R REBALANCE (FIRST). Current FnG: {fng_index + 1}, No previous FnG", log_color=utils.LogColors.BOLDSTRATEGY)
        self.rebalance(self.params.rebalance_percents[fng_index])

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
        if last_bar_executed_ago is not None and (self.data.datetime.date() - self.data.datetime.date(last_bar_executed_ago) < timedelta(self.params.min_order_period)):
            self.debug(f"  ...skip: still to soon to buy")
            return

        # Rebalance if fng index MA (in period min_order_period) is equals to current fng index and are different than previous rebalance
        fng_index = int(self.fng_indicator.fng_index[0])
        fng_ma_index = int(self.fng_indicator.fng_ma_index[0])
        last_bar_fng_index = int(
            self.fng_indicator.fng_index[last_bar_executed_ago])
        
        if fng_index == fng_ma_index and fng_index != last_bar_fng_index:
            self.log(
                f"R REBALANCE. Current FnG: {fng_index + 1}, Previous FnG: {last_bar_fng_index + 1}", log_color=utils.LogColors.BOLDSTRATEGY)
            self.rebalance(
                self.params.rebalance_percents[fng_index])
        else:
            self.debug(
                f"  ...skip: condition not fullfilled. Current FnG: {fng_index + 1}, MA FnG: {fng_ma_index + 1},  Previous FnG: {last_bar_fng_index + 1}")

    def plot(self, show: bool = True):
        ticker_data = self.data._dataname

        gs_kw = dict(height_ratios=[2, 1, 1])
        fig, (ticker_axes, strategy_axes, indicator_axes) = plt.subplots(
            nrows=3, sharex=True, gridspec_kw=gs_kw, subplot_kw=dict(frameon=True))  # constrained_layout=True, figsize=(11, 7)
        fig.suptitle(str(self), fontsize='large')
        # fig.set_tight_layout(True)
        fig.subplots_adjust(hspace=0.1, wspace=0.1)
        
        plt.xticks(fontsize='small', rotation=45, ha='right')
        plt.yticks(fontsize='small')

        # Ticker chart ########
        ticker_axes.margins(x=0)
        ticker_axes.set_ylabel('Price', fontsize='medium')
        ticker_axes.plot(ticker_data.index, ticker_data['close'],
                         color='#333333', linewidth=1)

        # Plot Buy and sell scatters
        self.plot_axes(ticker_axes)

        # Strategy chart #########
        self.plot_axes(strategy_axes, show_params=True)

        # Fng indicator chart ########
        self.fng_indicator.plot_axes(indicator_axes, start = ticker_data.index.min(), end = ticker_data.index.max())
        
        # Calculate x ticks
        ticker_axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fng_data_length = len(ticker_data)
        xticks = ticker_data.iloc[::int(
            fng_data_length/20)].index.to_list()
        xticks[0] = ticker_data.index.min()
        xticks[-1] = ticker_data.index.max()

        # Calculate x limit
        xlim = [ticker_data.index.min(), ticker_data.index.max()]

        # Set x ticks and limits
        ticker_axes.set(xlim=xlim, xticks=xticks)
        strategy_axes.set(xlim=xlim, xticks=xticks)
        indicator_axes.set(xlim=xlim, xticks=xticks)

        # Show plot
        # plt.rcParams['figure.figsize'] = [12, 8]
        # plt.rcParams['figure.dpi'] = 200
        # plt.rcParams['savefig.dpi'] = 200
        if show:
            plt.show()

        return fig
