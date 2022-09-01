from datetime import date, timedelta
import backtrader as bt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from crypto_band_indicators import utils
from crypto_band_indicators.indicators import BandIndicatorBase
from .indicator_wrappers import BandIndicatorWrapper
from .base_strategy import CryptoStrategy


class RebalanceStrategy(CryptoStrategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        indicator_class=None,
        indicator_params={},
        min_order_period=7,        # Number of days between buys
        rebalance_percents=[100],  # rebalance percents to apply depending on indicator index
    )

    def __init__(self):
        super().__init__()

        if not issubclass(self.params.indicator_class, BandIndicatorBase):
            raise Exception('WeightedDCAStrategy.__init__: parameter indicator_class must be a subclass of BandIndicatorBase')

        # Create indicator dinamically with indicator_class and indicator_params
        if self.params.indicator_params is None: self.params.indicator_params = {}
        self.indicator = BandIndicatorWrapper(band_indicator=self.params.indicator_class(**self.params.indicator_params))
 
        # Add ma
        if self.params.ma_class is not None:
            self.ma = self.params.ma_class(period=self.params.min_order_period)    # self.params.min_order_period
        else:
            self.ma = None

    def __str__(self):
        return f"Rebalance {str(self.indicator)}"
    
    def describe(self, keys = None):
        self_dict = super().describe()
        self_dict['min_order_period'] = self.params.min_order_period
        self_dict['rebalance_percents'] = ','.join([str(rebalance) for rebalance in self.params.rebalance_percents])
        self_dict['ma_class'] = None if self.params.ma_class is None else ''.join([char for char in self.params.ma_class.__name__ if char.isupper()])
        self_dict['params'] = f"{self_dict['min_order_period']} days |{self_dict['rebalance_percents']}"

        if keys is not None:
            self_dict = {key: self_dict[key] for key in keys}
        
        return self_dict

    # def nextstart(self):
    #     # Do a initial rebalance with the first indicator index
    #     indicator_index = int(self.indicator[0])

    #     self.log(
    #         f"R REBALANCE (FIRST). Indicator index: {indicator_index}, rebalance percent: {self.params.rebalance_percents[indicator_index]}", log_color=utils.LogColors.BOLDSTRATEGY)
    #     self.rebalance(self.params.rebalance_percents[indicator_index])

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

        # Rebalance if fng index (in period min_order_period) is equals to current fng index and are different than previous rebalance
        indicator_index =int(self.indicator[0])
        last_executed_indicator_index = int(self.indicator[last_bar_executed_ago]) if last_bar_executed_ago is not None else None
        
        if indicator_index != last_executed_indicator_index:
            self.log(
                f"R REBALANCE. Current index: {indicator_index}, Previous: {last_executed_indicator_index}", log_color=utils.LogColors.BOLDSTRATEGY)
            self.rebalance(
                self.params.rebalance_percents[indicator_index])
        else:
            self.debug(
                f"  ...skip: condition not fullfilled. Current index: {indicator_index},  Previous: {last_executed_indicator_index}")


    def rebalance(self, percent: float):
        current_value = self.broker.getvalue()
        current_btc_price = self.data.close[0]

        if self.position:
            current_position_value = self.position.size * current_btc_price
        else:
            current_position_value = 0

        rebalance_position_value = current_value * \
            percent / 100    # desired position value / total value

        order_dol_size = abs(rebalance_position_value) - current_position_value
        order_btc_size = order_dol_size / current_btc_price

        self.debug(
            f"  - current_position_value: {current_position_value:.2f} USD")
        self.debug(
            f"  - rebalance_position_value: {rebalance_position_value:.2f} USD")
        self.debug(f"  - order_dol_size: {order_dol_size:.2f} USD")
        self.debug(f"  - order_btc_size: {order_btc_size:.6f} BTC")

        last_bar_executed_ago = self.get_last_bar_executed_ago()
        last_executed_btc_price = self.data.close[last_bar_executed_ago] if last_bar_executed_ago is not None else None
        current_price =  self.ma[0] if self.ma is not None else self.data.close[0]
        previous_price =  self.ma[-1] if self.ma is not None else self.data.close[-1]

        # Do nothing if rebalance value is the same than current value
        if int(rebalance_position_value) == int(current_position_value):
            self.log(
                f"  REBALANCE SKIPPED: already rebalanced at {percent}%", log_color=utils.LogColors.STRATEGY)
        # Buy, if ma goes up
        elif rebalance_position_value > current_position_value and current_price > previous_price:  # and (last_executed_btc_price is None or current_btc_price < last_executed_btc_price):  # and self.ma[0] > self.ma[-1]:
            self.log(
                f"{utils.Emojis.BUY} BUY {order_btc_size:.6f} BTC = {order_dol_size:.2f} USD, 1 BTC = {current_btc_price:.2f} USD", log_color=utils.LogColors.BOLDBUY)
            # Keep track of the created order to avoid a 2nd order
            self.order = self.buy(size=abs(order_btc_size),
                                  rebalance_percent=percent)
            # self.order.addinfo(rebalance_percent=percent)

        # Sell, if ma goes down
        elif rebalance_position_value < current_position_value and current_price < previous_price:  # (last_executed_btc_price is None or current_btc_price > last_executed_btc_price):    # self.ma[0] < self.ma[-1]:
            self.log(
                f"{utils.Emojis.SELL} SELL {order_btc_size:.6f} BTC = {order_dol_size:.2f} USD, 1 BTC = {current_btc_price:.2f} USD", log_color=utils.LogColors.BOLDSELL)
            # Keep track of the created order to avoid a 2nd order
            self.order = self.sell(size=order_btc_size,
                                   rebalance_percent=percent)


    def plot(self, show: bool = True, title_prefix: str = '', title_suffix: str = ''):
        ticker_data = self.data._dataname

        gs_kw = dict(height_ratios=[2, 1, 1])
        fig, (ticker_axes, strategy_axes, indicator_axes) = plt.subplots(
            nrows=3, sharex=True, gridspec_kw=gs_kw, subplot_kw=dict(frameon=True))  # constrained_layout=True, figsize=(11, 7)
        fig.suptitle(f"{title_prefix}{str(self)}{title_suffix}", fontsize='large', y=0.98)
        # fig.set_tight_layout(True)
        fig.subplots_adjust(hspace=0.1, wspace=0.1, top=0.83)
        
        plt.xticks(fontsize='x-small', rotation=45, ha='right')
        # plt.yticks(fontsize='x-small')

        # Ticker chart ########
        ticker_axes.margins(x=0)
        ticker_axes.set_ylabel('Price', fontsize='medium')
        ticker_axes.plot(ticker_data.index, ticker_data['close'],
                         color='#333333', linewidth=1)
        ticker_axes.tick_params(axis='y', labelsize='x-small')

        # Ticker ma
        if self.params.ma_class is not None:
            ma_data_array = self.ma.line0.array
            ticker_axes.plot(ticker_data.index, ma_data_array,
                            color='#333333', linewidth=1, alpha=0.5, linestyle='--', label='MA')
            ticker_axes.legend()

        # Ticker yticks: min to max on the left
        ticker_min = ticker_data['close'].min()
        ticker_max = ticker_data['close'].max()
        num_ticks = int((ticker_max - ticker_min) / 2000)
        ticker_axes.set(ylim=[ticker_min, ticker_max], yticks=np.linspace(ticker_min, ticker_max, num_ticks))

        # Ticker yticks: start and end on the right
        min_max_yaxis = ticker_axes.twinx()
        min_max_yaxis.tick_params(axis='y', labelsize='x-small')
        min_max_yaxis.set(ylim=ticker_axes.get_ylim(), yticks=[ticker_data.iloc[0]['close'], ticker_data.iloc[-1]['close']])
        # min_max_yaxis.grid(axis='y', linestyle='--')

        # Plot orders #########
        self.plot_axes_orders(ticker_axes)

        # Strategy chart #########
        self.plot_axes(strategy_axes, show_params=True)

        # Fng indicator chart ########
        self.indicator.plot_axes(indicator_axes, start = ticker_data.index.min(), end = ticker_data.index.max())
        self.plot_axes_order_vlines(indicator_axes)

        # Calculate x ticks
        ticker_axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fng_data_length = len(ticker_data)
        xticks = ticker_data.iloc[::int(
            fng_data_length/40)].index.to_list()
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


    def plot_axes(self, axes, show_legend=True, show_params=True):
        # axes.margins(y=1)
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
        axes.tick_params(axis='y', labelsize='x-small')

        if show_legend:
            axes.legend()

        if show_params:
            self_details = self.describe()
            params_str = f"min_order_period: {self_details.get('min_order_period')}, rebalance_percents: {self_details.get('rebalance_percents')}"
            axes.annotate(params_str,
                          xy=(1.0, 0.1),
                          xycoords='axes fraction',
                          ha='right',
                          va="center",
                          fontsize='small')

        return axes
