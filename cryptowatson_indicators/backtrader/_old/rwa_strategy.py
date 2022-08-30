from datetime import timedelta
import backtrader as bt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from cryptowatson_indicators.indicators import RwaIndicator
from cryptowatson_indicators import utils
from .base_strategy import RebalanceStrategy_old, WeightedAverageStrategy_old


class RwaIndicatorWrapper(bt.Indicator):
    lines = ('band_index', 'band_ma_index', )

    params = dict(
        ma_period=7,    # moving average period
    )

    def __init__(self):
        # self.addminperiod(self.params.ma_period)
        self.rainbow = RwaIndicator()     # self.data._dataname


    def next(self):
        bar_band_index = self.rainbow.get_rainbow_band_index(
            price=self.data.close[0], at_date=self.data.datetime.date())

        self.lines.band_index[0] = int(bar_band_index)
        self.lines.band_ma_index[0] = self.lines.band_index[0]

    def plot_axes(self, axes, start=None, end=None):
        return self.rainbow.plot_axes(axes, start=start, end=end)


class RwaWeightedAverageStrategy(WeightedAverageStrategy_old):
    def __init__(self):
        super().__init__()

        self.rwa_indicator = RwaIndicatorWrapper(ma_period=2 * self.params.min_order_period)

        self.price = self.data.close

    def __str__(self):
        return 'Rainbow Weighted Av. DCA'

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

        band_index = int(self.rwa_indicator.band_index[0])

        buy_dol_size = self.params.base_buy_amount * \
            self.params.weighted_multipliers[band_index]
        buy_btc_size = buy_dol_size / self.price[0]
        self.log(
            f"{utils.Emojis.BUY} BUY {buy_btc_size:.6f} BTC = {buy_dol_size:.2f} USD, Band: {band_index + 1}, 1 BTC = {self.price[0]:.4f} USD", log_color=utils.LogColors.BOLDBUY)

        # Keep track of the created order to avoid a 2nd order
        self.order = self.buy(
            size=buy_btc_size, weighted_multiplier=self.params.weighted_multipliers[band_index])

    def plot(self, show: bool = True):
        ticker_data = self.data._dataname

        gs_kw = dict(height_ratios=[2, 1, 1])
        fig, (ticker_axes, strategy_axes, indicator_axes) = plt.subplots(
            nrows=3, sharex=True, gridspec_kw=gs_kw, subplot_kw=dict(frameon=True))
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

        # Rainbow indicator chart ########
        self.rwa_indicator.plot_axes(indicator_axes, start = ticker_data.index.min(), end = ticker_data.index.max())
        
        # Calculate x ticks
        ticker_axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        rwa_data_length = len(ticker_data)
        xticks = ticker_data.iloc[::int(
            rwa_data_length/20)].index.to_list()
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


class RwaRebalanceStrategy(RebalanceStrategy_old):
    def __init__(self):
        super().__init__()

        # Indicators
        self.rwa_indicator = RwaIndicatorWrapper(ma_period=2 * self.params.min_order_period)
        # self.rwa_ma = bt.indicators.WeightedMovingAverage(
        #     self.rwa_indicator.l.band_index, period=self.params.min_order_period, subplot=False)

    def __str__(self):
        return 'Rainbow Rebalance'

    def nextstart(self):
        # Do a initial rebalance with the first FnG value
        band_index = int(self.rwa_indicator.band_index[0])

        self.log(
            f"R REBALANCE (FIRST). Current Band: {band_index + 1}, No previous Rainbow Band", log_color=utils.LogColors.BOLDSTRATEGY)
        self.rebalance(
            self.params.rebalance_percents[band_index])

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

        # Rebalance if the the MA (of period min_order_period) and current rwa is major than previous reblance rwa
        band_index = int(self.rwa_indicator.band_index[0])
        band_ma_index = int(self.rwa_indicator.band_ma_index[0])
        last_bar_band_index = int(
            self.rwa_indicator.band_index[last_bar_executed_ago])
        if band_index == band_ma_index and band_index != last_bar_band_index:
            self.log(
                f"R REBALANCE. Current Band: {band_index + 1} , Previous Band: {last_bar_band_index + 1}", log_color=utils.LogColors.BOLDSTRATEGY)
            self.rebalance(
                self.params.rebalance_percents[band_index])
        else:
            self.debug(
                f"  ...skip: condition not fullfilled. Current Band: {band_index + 1}, MA Band: {band_ma_index + 1},  Previous Band: {last_bar_band_index + 1}")

    def plot(self, show: bool = True):
        ticker_data = self.data._dataname

        gs_kw = dict(height_ratios=[2, 1, 1])
        fig, (ticker_axes, strategy_axes, indicator_axes) = plt.subplots(
            nrows=3, sharex=True, gridspec_kw=gs_kw, subplot_kw=dict(frameon=True))
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

        # Rainbow indicator chart ########
        self.rwa_indicator.plot_axes(indicator_axes, start = ticker_data.index.min(), end = ticker_data.index.max())
        
        # Calculate x ticks
        ticker_axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        rwa_data_length = len(ticker_data)
        xticks = ticker_data.iloc[::int(
            rwa_data_length/20)].index.to_list()
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
