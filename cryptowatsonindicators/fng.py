from logging import exception
from typing import Union
from datetime import datetime, date
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from .helpers import data, utils

class Fng:
    def __init__(self, start_date: Union[str, date, datetime, None] = None, ticker_symbol:str = 'BTCUSDT', binance_api_key:str = '', binance_secret_key:str = ''):
        self.start_date = start_date
        self.ticker_symbol = ticker_symbol
        self.binance_api_key = binance_api_key
        self.binance_secret_key = binance_secret_key

        # load data
        self.data = data.get_fng_time_series(start_date)

        if (self.data is None or self.data.empty):
            e = f"Fng constructor: No historical data available"
            print(e)
            raise exception(e) 


    def get_current_fng(self):
        return self.get_fng()

    def get_fng(self, at_date: Union[str, date, datetime, None] = None):
        if (self.data is None or self.data.empty):
            print(f"[warn] get_current_fng: No data available")
            return None
        
        at_date_index = -1
        at_date_value = date.today()
        if at_date:
            at_date_value = utils.parse_any_date(at_date, datetime.now()).date()
            at_date_pd = pd.Timestamp(at_date_value)

            # find fitted_data index at date
            at_date_index_list = list(self.data[self.data['Date'] == at_date_pd].index)
            if (len(at_date_index_list) == 0):
                print(f"[warn] get_fng: Data not found at date {at_date_value}")
                return None

            at_date_index = int(at_date_index_list[0])

        fng_data = self.data.iloc[at_date_index].to_dict()

        return {
            'date': at_date_value,
            'fng_value': fng_data.get('Value'),
            'fng_name': fng_data.get('ValueName'),
        }

    def plot_fng(self):
        if (self.data is None or self.data.empty):
            print(f"[warn] plot_fng: No historical data available")
            return None

        fig, axes = plt.subplots()

        # Select rows between values: https://stackoverflow.com/questions/38884466/how-to-select-a-range-of-values-in-a-pandas-dataframe-column
        # 0-25: Extreme Fear
        # 26-46: Fear
        # 47-54: Neutral
        # 55-75: Greed
        # 76-100: Extreme Greed

        # Color gradient: https://colordesigner.io/gradient-generator/?mode=rgb#DE2121-21DE21
        #de2121 #af5021 #808021 #50af21 #21de21
        # Option 2: Looking at alternative.md chart palette
        # #C05840 #FC9A24 #E5C769 #B4E168 #5CBC3C
        # matplotlib colors: https://matplotlib.org/stable/tutorials/colors/colors.html#sphx-glr-tutorials-colors-colors-py
        # Consider using pivot(): https://pandas.pydata.org/pandas-docs/dev/getting_started/intro_tutorials/09_timeseries.html#datetime-as-index
        range1 = self.data[self.data['Value'].between(0, 25, inclusive='left')]
        range2 = self.data[self.data['Value'].between(25, 46, inclusive='left')]
        range3 = self.data[self.data['Value'].between(46, 54, inclusive='both')]
        range4 = self.data[self.data['Value'].between(54, 75, inclusive='right')]
        range5 = self.data[self.data['Value'].between(75, 100, inclusive='right')]

        axes.bar(range1['Date'], range1['Value'], color='#C05840') # , width, yerr=menStd
        axes.bar(range2['Date'], range2['Value'], color='#FC9A24') # , width, yerr=menStd
        axes.bar(range3['Date'], range3['Value'], color='#E5C769') # , width, yerr=menStd
        axes.bar(range4['Date'], range4['Value'], color='#B4E168') # , width, yerr=menStd
        axes.bar(range5['Date'], range5['Value'], color='#5CBC3C') # , width, yerr=menStd

        # ax.axhline(0, color='grey', linewidth=0.8)
        # axes.set_xlabel('Date')
        axes.set_ylabel('FnG')
        axes.set_title('Fear and Greed history')

        axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        data_length = len(self.data)
        xticks = self.data['Date'].iloc[lambda x: x.index % int(data_length/20) == 0].tolist()
        xticks[0] = self.data['Date'].iloc[0]
        xticks[-1] = self.data['Date'].iloc[-1]
        axes.set_xticks(xticks)
        plt.xticks(fontsize=8, rotation=45, ha='right')

        # Label with label_type 'center' instead of the default 'edge'
        # ax.bar_label(p1, label_type='center')
        # ax.bar_label(p2, label_type='center')
        # ax.bar_label(p2)

        # Show plot
        plt.rcParams['figure.dpi'] = 600
        plt.rcParams['savefig.dpi'] = 600
        # plt.rcParams['figure.figsize'] = [20/2.54, 16/2.54]
        plt.show()


    def plot_fng_and_ticker_price(self):
        if (self.data is None or self.data.empty):
            print(f"[warn] plot_fng_and_ticker_price: No data available")
            return None
        
        ticker_start_date = self.data['Date'][0]
        ticker_data = data.get_nasdaq_ticker_time_series(start_date = ticker_start_date)
        if (ticker_data is None or ticker_data.empty):
            print(f"[warn] plot_fng_and_ticker_price: No ticker data available")
            return None

        fig, axes = plt.subplots()
        fig.suptitle('Fear and Greed Index / BTCUSDT Price', fontsize='large')
        # fig.set_tight_layout(True)
        axes.set_ylabel('FnG Index', fontsize='medium')
        plt.xticks(fontsize='small', rotation=45, ha='right')
        plt.yticks(fontsize='small')

        # fng chart ########
        range1 = self.data[self.data['Value'].between(0, 25, inclusive='left')]
        range2 = self.data[self.data['Value'].between(25, 46, inclusive='left')]
        range3 = self.data[self.data['Value'].between(46, 54, inclusive='both')]
        range4 = self.data[self.data['Value'].between(54, 75, inclusive='right')]
        range5 = self.data[self.data['Value'].between(75, 100, inclusive='right')]

        axes.bar(range1['Date'], range1['Value'], color='#C05840') # , width, yerr=menStd
        axes.bar(range2['Date'], range2['Value'], color='#FC9A24') # , width, yerr=menStd
        axes.bar(range3['Date'], range3['Value'], color='#E5C769') # , width, yerr=menStd
        axes.bar(range4['Date'], range4['Value'], color='#B4E168') # , width, yerr=menStd
        axes.bar(range5['Date'], range5['Value'], color='#5CBC3C') # , width, yerr=menStd

        # fng ticks
        axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fng_data_length = len(self.data)
        fng_xticks = self.data['Date'].iloc[lambda x: x.index % int(fng_data_length/20) == 0].tolist()
        fng_xticks[0] = self.data['Date'].iloc[0]
        fng_xticks[-1] = self.data['Date'].iloc[-1]
        axes.set_xticks(fng_xticks)
        axes.set_yticks([0, 25, 46, 54, 75, 100])

        # ticker chart ##########
        axes2 = axes.twinx()
        axes2.set_ylabel('Price', fontsize='medium')
        axes2.plot(ticker_data['Date'], ticker_data['Value'], color='#333333', linewidth=0.75)
        
        # ticker ticks
        ticker_max_value = ticker_data['Value'].max()
        ticker_yticks = np.arange(0, int(ticker_max_value), int(ticker_max_value / 10))
        ticker_yticks[0] = 0
        ticker_yticks[-1] = ticker_max_value 
        axes2.set_yticks(ticker_yticks)

        # horizontal line with latest ticker value
        # ticker_latest_value = ticker_data.iloc[-1, 1]
        # axes2.axhline(y=ticker_latest_value, color='#dedede', linewidth=0.5, linestyle='--', zorder=-1)

        # Show plot
        plt.rcParams['figure.dpi'] = 600
        plt.rcParams['savefig.dpi'] = 600
        # plt.rcParams["figure.autolayout"] = True
        # plt.rcParams['figure.figsize'] = [20/2.54, 16/2.54]
        # fig.subplots_adjust(hspace=0.2)
        plt.tight_layout()
        plt.show()


    def plot_fng_and_ticker_price_2(self):
        if (self.data is None or self.data.empty):
            print(f"[warn] plot_fng_and_ticker_price_2: No data available")
            return None
        
        ticker_start_date = self.data['Date'][0]
        ticker_data = data.get_nasdaq_ticker_time_series(start_date = ticker_start_date)
        if (ticker_data is None or ticker_data.empty):
            print(f"[warn] plot_fng_and_ticker_price: No ticker data available")
            return None

        # fig, axes = plt.subplots()
        fig, (fng_axes, ticker_axes) = plt.subplots(nrows=2, sharex=True, subplot_kw=dict(frameon=True))
        ticker_axes2 = ticker_axes.secondary_yaxis('right')
        fig.suptitle('Fear and Greed Index / BTCUSDT Price', fontsize='large')
        # fig.set_tight_layout(True)
        fng_axes.set_ylabel('FnG Index', fontsize='medium')
        ticker_axes.set_ylabel('Price', fontsize='medium')
        plt.xticks(fontsize='small', rotation=45, ha='right')
        plt.yticks(fontsize='small')

        # fng chart ########
        merged_data = pd.merge(self.data, ticker_data, how='inner', on='Date', suffixes=('Fng', 'Ticker'))

        range1 = merged_data[merged_data['ValueFng'].between(0, 25, inclusive='left')]
        range2 = merged_data[merged_data['ValueFng'].between(25, 46, inclusive='left')]
        range3 = merged_data[merged_data['ValueFng'].between(46, 54, inclusive='both')]
        range4 = merged_data[merged_data['ValueFng'].between(54, 75, inclusive='right')]
        range5 = merged_data[merged_data['ValueFng'].between(75, 100, inclusive='right')]

        fng_axes.bar(range1['Date'], range1['ValueFng'], color='#C05840') # , width, yerr=menStd
        fng_axes.bar(range2['Date'], range2['ValueFng'], color='#FC9A24') # , width, yerr=menStd
        fng_axes.bar(range3['Date'], range3['ValueFng'], color='#E5C769') # , width, yerr=menStd
        fng_axes.bar(range4['Date'], range4['ValueFng'], color='#B4E168') # , width, yerr=menStd
        fng_axes.bar(range5['Date'], range5['ValueFng'], color='#5CBC3C') # , width, yerr=menStd

        # fng ticks
        fng_axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fng_data_length = len(self.data)
        fng_xticks = self.data['Date'].iloc[lambda x: x.index % int(fng_data_length/20) == 0].tolist()
        fng_xticks[0] = self.data['Date'].iloc[0]
        fng_xticks[-1] = self.data['Date'].iloc[-1]
        fng_axes.set_xticks(fng_xticks)
        fng_axes.set_yticks([0, 25, 46, 54, 75, 100])

        # ticker chart ##########
        ticker_axes.bar(range1['Date'], range1['ValueTicker'], color='#C05840') # , width, yerr=menStd
        ticker_axes.bar(range2['Date'], range2['ValueTicker'], color='#FC9A24') # , width, yerr=menStd
        ticker_axes.bar(range3['Date'], range3['ValueTicker'], color='#E5C769') # , width, yerr=menStd
        ticker_axes.bar(range4['Date'], range4['ValueTicker'], color='#B4E168') # , width, yerr=menStd
        ticker_axes.bar(range5['Date'], range5['ValueTicker'], color='#5CBC3C') # , width, yerr=menStd

        # ticker ticks
        ticker_max_value = ticker_data['Value'].max()
        ticker_yticks = np.arange(0, int(ticker_max_value), int(ticker_max_value / 10))
        ticker_yticks[0] = 0
        ticker_yticks[-1] = ticker_max_value 
        ticker_axes.set_yticks(ticker_yticks)

        # ticker ticks 2
        ticker_latest_value = ticker_data.iloc[-1, 1]
        ticker_axes2.set_yticks(
            [ticker_latest_value, ticker_max_value],
            [f"today:\n{ticker_latest_value}", f"max:\n{ticker_max_value}"],
            fontsize='small'
            )
        
        # horizontal lines in today and max
        ticker_axes.axhline(y=ticker_latest_value, color='#dedede', linewidth=0.5, linestyle='--', zorder=-1)
        ticker_axes.axhline(y=ticker_max_value, color='#dedede', linewidth=0.5, linestyle='--', zorder=-1)
        
        # Show plot
        plt.rcParams['figure.dpi'] = 600
        plt.rcParams['savefig.dpi'] = 600
        # plt.rcParams["figure.autolayout"] = True
        # plt.rcParams['figure.figsize'] = [20/2.54, 16/2.54]
        # fig.subplots_adjust(hspace=0.2)
        plt.tight_layout()
        plt.show()


