from logging import exception
from typing import Union
from datetime import datetime, date
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from cryptowatsonindicators import datas, utils

# 0-25: Extreme Fear
# 26-46: Fear
# 47-54: Neutral
# 55-75: Greed
# 76-100: Extreme Greed
FNG_THRESHOLDS =  [25,             46,        54,        75,        100]
FNG_NAMES =       ["Extreme Fear", "Fear",    "Neutral", "Greed",   "Extreme Greed"]
FNG_COLORS =      ["#C05840",      "#FC9A24", "#E5C769", "#B4E168", "#5CBC3C"]
FNG_MULTIPLIERS = [1.5,            1.25,      1,         0.75,      0.5]

class Fng:
    indicator_data = None

    def __init__(self, indicator_start_date: Union[str, date, datetime, None] = None, ticker_symbol:str = 'BTCUSDT', binance_api_key:str = '', binance_secret_key:str = ''):
        self.indicator_start_date = indicator_start_date
        self.ticker_symbol = ticker_symbol
        self.binance_api_key = binance_api_key
        self.binance_secret_key = binance_secret_key

        # load indicator data
        self.indicator_data = datas.get_fng_time_series(start_date=indicator_start_date)

        if (self.indicator_data is None or self.indicator_data.empty):
            error_message = f"Fng.constructor: No indicator data available"
            print(f"[error] {error_message}")
            raise exception(error_message) 


    def get_current_fng_value(self) -> Union[int, None]:
        return self.get_fng_value(at_date = None)

    def get_fng_value(self, at_date: Union[str, date, datetime, None] = None) -> Union[int, None]:
        if (self.indicator_data is None or self.indicator_data.empty):
            print(f"[warn] Fng.get_fng_value: No indicator data available")
            return None
        
        at_date_index = -1
        at_date_value = date.today()
        if at_date:
            at_date_value = utils.parse_any_date(at_date, datetime.now()).date()
            at_date_pd = pd.Timestamp(at_date_value)

            # find fitted_data index at date
            at_date_index_list = list(self.indicator_data[self.indicator_data['Date'] == at_date_pd].index)
            if (len(at_date_index_list) == 0):
                print(f"[warn] Fng.get_fng_value: Data not found at date {at_date_value}")
                return None

            at_date_index = int(at_date_index_list[0])

        fng_data = self.indicator_data.iloc[at_date_index].to_dict()

        return int(fng_data.get('Value'))

    @classmethod
    def _get_fng_value_details(cls, value: int = -1) -> dict:
        if (value < 0 or value > 100):
            return dict()
        
        # Get index
        index = 0
        if (0 <= value < FNG_THRESHOLDS[0]):
            index = 0
        elif (FNG_THRESHOLDS[0] <= value < FNG_THRESHOLDS[1]):
            index = 1
        elif (FNG_THRESHOLDS[1] <= value <= FNG_THRESHOLDS[2]):
            index = 2
        elif (FNG_THRESHOLDS[2] < value <= FNG_THRESHOLDS[3]):
            index = 3
        elif (FNG_THRESHOLDS[3] < value <= FNG_THRESHOLDS[4]):
            index = 4

        return {
            'fng_index': index,
            'fng_ordinal': f"{index + 1}/5",
            'name': FNG_NAMES[index],
            'color': FNG_COLORS[index],
            'multiplier': FNG_MULTIPLIERS[index],
        }

    def plot_fng(self):
        if (self.indicator_data is None or self.indicator_data.empty):
            print(f"[warn] Fng.plot_fng: No indicator data available")
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
        range1 = self.indicator_data[self.indicator_data['Value'].between(0, 25, inclusive='left')]
        range2 = self.indicator_data[self.indicator_data['Value'].between(25, 46, inclusive='left')]
        range3 = self.indicator_data[self.indicator_data['Value'].between(46, 54, inclusive='both')]
        range4 = self.indicator_data[self.indicator_data['Value'].between(54, 75, inclusive='right')]
        range5 = self.indicator_data[self.indicator_data['Value'].between(75, 100, inclusive='right')]

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
        data_length = len(self.indicator_data)
        xticks = self.indicator_data['Date'].iloc[lambda x: x.index % int(data_length/20) == 0].tolist()
        xticks[0] = self.indicator_data['Date'].iloc[0]
        xticks[-1] = self.indicator_data['Date'].iloc[-1]
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
        if (self.indicator_data is None or self.indicator_data.empty):
            print(f"[warn] Fng.plot_fng_and_ticker_price: No indicator data available")
            return None
        
        ticker_start_date = self.indicator_data['Date'][0]
        ticker_data = datas.get_nasdaq_ticker_time_series(start_date = ticker_start_date)
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
        range1 = self.indicator_data[self.indicator_data['Value'].between(0, 25, inclusive='left')]
        range2 = self.indicator_data[self.indicator_data['Value'].between(25, 46, inclusive='left')]
        range3 = self.indicator_data[self.indicator_data['Value'].between(46, 54, inclusive='both')]
        range4 = self.indicator_data[self.indicator_data['Value'].between(54, 75, inclusive='right')]
        range5 = self.indicator_data[self.indicator_data['Value'].between(75, 100, inclusive='right')]

        axes.bar(range1['Date'], range1['Value'], color='#C05840') # , width, yerr=menStd
        axes.bar(range2['Date'], range2['Value'], color='#FC9A24') # , width, yerr=menStd
        axes.bar(range3['Date'], range3['Value'], color='#E5C769') # , width, yerr=menStd
        axes.bar(range4['Date'], range4['Value'], color='#B4E168') # , width, yerr=menStd
        axes.bar(range5['Date'], range5['Value'], color='#5CBC3C') # , width, yerr=menStd

        # fng ticks
        axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fng_data_length = len(self.indicator_data)
        fng_xticks = self.indicator_data['Date'].iloc[lambda x: x.index % int(fng_data_length/20) == 0].tolist()
        fng_xticks[0] = self.indicator_data['Date'].iloc[0]
        fng_xticks[-1] = self.indicator_data['Date'].iloc[-1]
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
        if (self.indicator_data is None or self.indicator_data.empty):
            print(f"[warn] Fng.plot_fng_and_ticker_price_2: No indicator data available")
            return None
        
        ticker_start_date = self.indicator_data['Date'][0]
        ticker_data = datas.get_nasdaq_ticker_time_series(start_date = ticker_start_date)
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
        merged_data = pd.merge(self.indicator_data, ticker_data, how='inner', on='Date', suffixes=('Fng', 'Ticker'))

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
        fng_data_length = len(self.indicator_data)
        fng_xticks = self.indicator_data['Date'].iloc[lambda x: x.index % int(fng_data_length/20) == 0].tolist()
        fng_xticks[0] = self.indicator_data['Date'].iloc[0]
        fng_xticks[-1] = self.indicator_data['Date'].iloc[-1]
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


