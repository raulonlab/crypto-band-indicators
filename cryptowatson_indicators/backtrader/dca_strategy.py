from datetime import timedelta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from cryptowatson_indicators import utils
from .base_strategy import CryptoStrategy

class DCAStrategy(CryptoStrategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        buy_amount=100,      # amount to buy 
        min_order_period=7,  # number of days between buys
        multiplier=1,        # multiplier to apply depending on indicator index
    )

    def __init__(self):
        super().__init__()

        self.price = self.data.close

    def __str__(self):
        return  f"DCA {(self.params.buy_amount * self.params.multiplier):.2f}$"

    def describe(self, keys = None):
        self_dict = super().describe()
        self_dict['min_order_period'] = self.params.min_order_period
        self_dict['buy_amount'] = self.params.buy_amount
        self_dict['multiplier'] = self.params.multiplier
        self_dict['params'] = f"{self_dict['min_order_period']} days |{self_dict['buy_amount']}$ |x{self_dict['multiplier']}"

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

        buy_dol_size = self.params.buy_amount * \
            self.params.multiplier
        buy_btc_size = buy_dol_size / self.price[0]
        self.log(
            f"{utils.Emojis.BUY} BUY {buy_btc_size:.6f} BTC = {buy_dol_size:.2f} USD, 1 BTC = {self.price[0]:.2f} USD", log_color=utils.LogColors.BOLDBUY)

        # Keep track of the created order to avoid a 2nd order
        self.order = self.buy(
            size=buy_btc_size)

    def plot(self, show: bool = True, title_prefix: str = '', title_suffix: str = ''):
        ticker_data = self.data._dataname

        gs_kw = dict(height_ratios=[0.5])
        fig, (ticker_axes) = plt.subplots(
            nrows=1, sharex=True, gridspec_kw=gs_kw, subplot_kw=dict(frameon=True))    # constrained_layout=True, figsize=(11, 7)
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
        
        # Plot Buy and sell scatters
        self.plot_axes_orders(ticker_axes)

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

        # Show plot
        # plt.rcParams['figure.figsize'] = [12, 8]
        # plt.rcParams['figure.dpi'] = 200
        # plt.rcParams['savefig.dpi'] = 200
        if show:
            plt.show()

        return fig

