# See buy and hold example: https://www.backtrader.com/blog/2019-06-13-buy-and-hold/buy-and-hold/

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from cryptowatson_indicators import utils
from .base_strategy import CryptoStrategy


class HodlStrategy(CryptoStrategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        percent=100,  # percent of the portfolio value to buy and hodl
    )

    def __init__(self):
        super().__init__()

    def __str__(self):
        return  f"HODL {self.params.percent}%"
    
    def describe(self, keys = None):
        self_dict = super().describe()
        self_dict['percent'] = self.params.percent
        self_dict['params'] = f"{self_dict['percent']}%"

        if keys is not None:
            self_dict = {key: self_dict[key] for key in keys}
        
        return self_dict

    def nextstart(self):
        self.log(
            f"H HODL, percent: {self.params.percent}", log_color=utils.LogColors.BOLDSTRATEGY)
        self.hodl(self.params.percent)


    def next(self):
        pass


    def hodl(self, percent: float):
        current_value = self.broker.getvalue()
        current_btc_price = self.data0.close[0]  # = self.data

        rebalance_value = current_value * percent / 100    # desired position value in USDT

        order_btc_size = rebalance_value / current_btc_price

        self.debug(
            f"  - rebalance_value: {rebalance_value:.2f} USD")
        self.debug(f"  - order_btc_size: {order_btc_size:.6f} BTC")

        self.log(
                f"{utils.Emojis.BUY} BUY {order_btc_size:.6f} BTC = {rebalance_value:.2f} USD, 1 BTC = {current_btc_price:.2f} USD", log_color=utils.LogColors.BOLDBUY)
        # Keep track of the created order to avoid a 2nd order
        self.order = self.buy(size=abs(order_btc_size), rebalance_percent=percent)

    def plot(self, show: bool = True, title_prefix: str = '', title_suffix: str = ''):
        ticker_data = self.data._dataname

        gs_kw = dict(height_ratios=[0.5])
        fig, (ticker_axes) = plt.subplots(
            nrows=1, sharex=True, gridspec_kw=gs_kw, subplot_kw=dict(frameon=True))  # constrained_layout=True, figsize=(11, 7)
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


