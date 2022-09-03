from datetime import date, timedelta
import backtrader as bt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from ..utils import LogColors, Emojis, PlotColors
from ..indicators import BandIndicatorBase
from .indicator_wrappers import BandIndicatorWrapper
from .base_strategy import CryptoStrategy

class WeightedDCAStrategy(CryptoStrategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        indicator_class=None,
        indicator_params={},
        base_buy_amount=100,   # amount base to buy, to be multiplied by weighted multiplier
        min_order_period=7,        # number of days between buys
        weighted_multipliers=[1],  # multiplier to apply depending on indicator index
    )

    def __init__(self):
        super().__init__()

        if not issubclass(self.params.indicator_class, BandIndicatorBase):
            raise Exception('WeightedDCAStrategy.__init__: parameter indicator_class must be a subclass of BandIndicatorBase')

        # Create indicator dinamically with indicator_class and indicator_params
        if self.params.indicator_params is None: self.params.indicator_params = {}
        self.indicator = BandIndicatorWrapper(band_indicator=self.params.indicator_class(**self.params.indicator_params))

        self.price = self.data.close

    def __str__(self):
        return f"Weighted DCA {str(self.indicator)}"
    
    def describe(self, keys=None):
        self_dict = super().describe()
        self_dict['min_order_period'] = self.params.min_order_period
        self_dict['base_buy_amount'] = self.params.base_buy_amount
        self_dict['weighted_multipliers'] = ','.join([str(multiplier) for multiplier in self.params.weighted_multipliers])
        self_dict['ma_class'] = None if self.params.ma_class is None else ''.join([char for char in self.params.ma_class.__name__ if char.isupper()])
        self_dict['params'] = f"{self_dict['min_order_period']} days |{self_dict['base_buy_amount']}$ |{self_dict['weighted_multipliers']}"

        if keys is not None:
            self_dict = {key: self_dict[key] for key in keys}
        
        return self_dict

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

        indicator_index =int(self.indicator[0])

        buy_dol_size = self.params.base_buy_amount * \
            self.params.weighted_multipliers[indicator_index]
        buy_btc_size = buy_dol_size / self.price[0]
        self.log(
            f"{Emojis.BUY} BUY {buy_btc_size:.6f} BTC = {buy_dol_size:.2f} USD, Current index: {indicator_index}, 1 BTC = {self.price[0]:.2f} USD", log_color=LogColors.BOLDBUY)
        
        # Keep track of the created order to avoid a 2nd order
        self.order = self.buy(
            size=buy_btc_size, weighted_multiplier=self.params.weighted_multipliers[indicator_index])

    def plot(self, show: bool = True, title_prefix: str = '', title_suffix: str = ''):
        ticker_data = self.data._dataname

        gs_kw = dict(height_ratios=[2, 1, 1])
        fig, (ticker_axes, strategy_axes, indicator_axes) = plt.subplots(
            nrows=3, sharex=True, gridspec_kw=gs_kw, subplot_kw=dict(frameon=True))    # constrained_layout=True, figsize=(11, 7)
        fig.suptitle(f"{title_prefix}{str(self)}{title_suffix}", fontsize='large')
        # fig.set_tight_layout(True)
        fig.subplots_adjust(hspace=0.1, wspace=0.1)

        plt.xticks(fontsize='x-small', rotation=45, ha='right')
        # plt.yticks(fontsize='x-small')

        # Ticker chart ########
        ticker_axes.margins(x=0)
        ticker_axes.set_ylabel('Price', fontsize='medium')
        ticker_axes.plot(ticker_data.index, ticker_data['close'],
                         color='#333333', linewidth=1)
        ticker_axes.tick_params(axis='y', labelsize='x-small')
        
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
        # self.plot_axes_orders(ticker_axes)

        # Strategy chart #########
        self.plot_axes(strategy_axes, show_params=True)

        # Fng indicator chart ########
        self.indicator.plot_axes(indicator_axes, start = ticker_data.index.min(), end = ticker_data.index.max())
        # self.plot_axes_order_vlines(indicator_axes)

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
                          color=PlotColors.GOLD, step="post", alpha=0.4, label='Weighted multiplier')
        axes.step(steps_data_x, steps_data_y,
                  color=PlotColors.GOLD, where='post')

        axes.set(ylim=(0, max(steps_data_y)),
                 yticks=self.params.weighted_multipliers)
        axes.tick_params(axis='y', labelsize='x-small')

        if show_legend:
            axes.legend()

        if show_params:
            params_str = f"min_order_period: {self.params.min_order_period}, base_buy_amount: {self.params.base_buy_amount}, weighted_multipliers: {self.params.weighted_multipliers}"
            axes.annotate(params_str,
                          xy=(1.0, -0.2),
                          xycoords='axes fraction',
                          ha='right',
                          va="center",
                          fontsize='small')

        return axes
