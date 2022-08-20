from logging import exception
from typing import Union
from datetime import datetime, date
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.optimize import curve_fit
from cryptowatsonindicators import datas, utils

RAINBOW_BANDS_NAMES = ["Maximum bubble!!", "Sell, seriouly sell!", "FOMO intensifies",
                       "Is this a bubble?", "HODL", "Still cheap", "Accumulate", "Buy!", "Fire sale!!"]
RAINBOW_BANDS_COLORS = ['#6b8ed0', '#78acb2', '#84ca95',
                        '#c0de9a', '#feed94', '#f8c37d', '#f1975e', '#df6a4d', '#cf463f']
RAINBOW_BANDS_FIBONACCI_MULTIPLIERS = [
    0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.3, 2.1, 3.4]
RAINBOW_BANDS_ORIGINAL_MULTIPLIERS = [0, 0.1, 0.2, 0.35, 0.5, 0.75, 1, 2.5, 3]
FITTED_BAND_LOG_MULTIPLIER = .455


class RwaIndicator:
    def __init__(self, data: Union[pd.DataFrame, None] = None, indicator_start_date: Union[str, date, datetime, None] = None, ticker_symbol: str = 'BTCUSDT', binance_api_key: str = '', binance_secret_key: str = '', fitted_multiplier: float = FITTED_BAND_LOG_MULTIPLIER):
        self.ticker_symbol = ticker_symbol
        self.binance_api_key = binance_api_key
        self.binance_secret_key = binance_secret_key

        # load indicator data
        if isinstance(data, pd.DataFrame):
            self.indicator_data = data
        else:
            self.indicator_data = datas.TickerDataSource().to_dataframe(start=indicator_start_date)

        if not isinstance(self.indicator_data, pd.DataFrame) or self.indicator_data.empty:
            error_message = f"FngIndicator.constructor: No indicator data available"
            print(f"[error] {error_message}")
            raise exception(error_message)

        # calculate fitted data columns
        # getting your x and y data from the dataframe
        xdata = np.array([x + 1 for x in range(len(self.indicator_data))])
        ydata = np.log(self.indicator_data["close"])
        # here we ar fitting the curve, you can use 2 data points however I wasn't able to get a graph that looked as good with just 2 points.
        # p0=[10, 100, 90], p0 is justa guess, doesn't matter as far as I know
        popt, pcov = curve_fit(
            RwaIndicator._rwa_logarithmic_function, xdata, ydata)
        # This is our fitted data, remember we will need to get the ex of it to graph it

        # print('popt: ', popt)

        self.fittedYData = RwaIndicator._rwa_logarithmic_function(
            xdata, popt[0], popt[1], popt[2])
        # Add columns with rainbow coordenates
        for i in range(-3, 7):
            self.indicator_data[f"fitted_data{i}"] = np.exp(
                self.fittedYData + i * fitted_multiplier)

    def get_current_rainbow_band_index(self):
        # Get current ticker price from Binance
        price_dict = datas.TickerDataSource.get_binance_ticker_market_price(self.ticker_symbol,
                                                                      self.binance_api_key, self.binance_secret_key)
        current_price = float(price_dict["price"])

        # Get rainbow band index (at the most recent time of the time series)
        return self.get_rainbow_band_index(current_price)

    def get_rainbow_band_index(self, price: float, at_date: Union[str, date, datetime, None] = None):
        if not isinstance(self.indicator_data, pd.DataFrame) or self.indicator_data.empty:
            print(
                f"[warn] RwaIndicator.get_rainbow_band_index: No historical data available")
            return None

        at_date = utils.parse_any_date(at_date)
        if not at_date:
            at_date = self.indicator_data.index.max().date()

        rwa_serie_at_date = self.indicator_data[self.indicator_data.index == pd.to_datetime(
            at_date)]
        if (rwa_serie_at_date.empty):
            print(
                f"[warn] RwaIndicator.get_rainbow_band_index: Data not found at date {at_date}")
            return None

        # Search for the band index
        band_index = -1
        # Fire sale!!
        if price < float(rwa_serie_at_date["fitted_data-2"]):
            band_index = 8

        # Buy!
        elif price > float(rwa_serie_at_date["fitted_data-2"]) and price < float(rwa_serie_at_date["fitted_data-1"]):
            band_index = 7

        # Accumulate
        elif price > float(rwa_serie_at_date["fitted_data-1"]) and price < float(rwa_serie_at_date["fitted_data0"]):
            band_index = 6

        # Still cheap
        elif price > float(rwa_serie_at_date["fitted_data0"]) and float(rwa_serie_at_date["fitted_data1"]):
            band_index = 5

        # HODL
        elif price > float(rwa_serie_at_date["fitted_data1"]) and price < float(rwa_serie_at_date["fitted_data2"]):
            band_index = 4

        # Is this a bubble?
        elif price > float(rwa_serie_at_date["fitted_data2"]) and float(rwa_serie_at_date["fitted_data3"]):
            band_index = 3

        # FOMO intensifies
        elif price > float(rwa_serie_at_date["fitted_data3"]) and price < float(rwa_serie_at_date["fitted_data4"]):
            band_index = 2

        # Sell, seriouly sell!
        elif price > float(rwa_serie_at_date["fitted_data4"]) and price < float(rwa_serie_at_date["fitted_data5"]):
            band_index = 1

        # Maximum bubble!!
        else:
            band_index = 0

        return band_index

    @classmethod
    def _rwa_logarithmic_function(cls, x, a, b, c):
        return a*np.log(b+x) + c

    @classmethod
    def _get_rainbow_info_by_index(cls, index: int = -1) -> dict:
        if (index < 0 or index > len(RAINBOW_BANDS_NAMES)):
            return dict()

        return {
            'band_index': index,
            'band_ordinal': f"{index + 1}/9",
            'name': RAINBOW_BANDS_NAMES[index],
            'color': RAINBOW_BANDS_COLORS[index],
            'fibs_multiplier': RAINBOW_BANDS_FIBONACCI_MULTIPLIERS[index],
            'original_multiplier': RAINBOW_BANDS_ORIGINAL_MULTIPLIERS[index],
        }

    def plot_rainbow(self):
        if not isinstance(self.indicator_data, pd.DataFrame) or self.indicator_data.empty:
            print(f"[warn] plot_rainbow: No historical data available")
            return None

        latest_serie = self.indicator_data.iloc[-1]

        fig, axes = plt.subplots()
        fig.suptitle('Bitcoin Rainbow Chart', fontsize='large')
        plt.xlabel('Date')
        plt.ylabel('Bitcoin price in log scale')
        axes.margins(x=0)

        # Draw bitcoin price
        axes.semilogy(
            self.indicator_data.index, self.indicator_data["close"], color='#333333', linewidth=0.75)

        # Draw the rainbow bands
        for i in range(-2, 7):
            # You can use the below plot fill between rather than the above line plot, I prefer the line graph
            axes.fill_between(self.indicator_data.index, self.indicator_data[f"fitted_data{i-1}"],
                              self.indicator_data[f"fitted_data{i}"], alpha=0.8, linewidth=1, color=RAINBOW_BANDS_COLORS[i+2])
            axes.plot(self.indicator_data.index,
                      self.indicator_data[f"fitted_data{i}"], linewidth=1.5, markersize=0.5, color=RAINBOW_BANDS_COLORS[i+2])

        axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

        # Set xticks
        rwa_data_length = len(self.indicator_data)
        rwa_xticks = self.indicator_data.iloc[::int(
            rwa_data_length/20)].index.to_list()
        rwa_xticks[0] = self.indicator_data.index.min()
        rwa_xticks[-1] = self.indicator_data.index.max()
        axes.set_xticks(rwa_xticks)
        plt.xticks(fontsize=8, rotation=45, ha='right')

        # Add yticks on the right
        band_axis = axes.secondary_yaxis("right")

        rainbow_band_yticks = list()
        for i in range(-3, 7):
            print(f"fitted_data{i}: ", latest_serie[f"fitted_data{i}"])
            rainbow_band_yticks.append(latest_serie[f"fitted_data{i}"])
        band_axis.set_yticks(rainbow_band_yticks)
        band_axis.set_yticklabels(
            [f"{rainbow_band_ytick:.2f}" for rainbow_band_ytick in rainbow_band_yticks])

        # axes2.axvline(x=self.indicator_data.index.max(), color='#333333', linewidth=1)  # label='Today'

        # Show plot
        plt.rcParams['figure.dpi'] = 1200
        plt.rcParams['savefig.dpi'] = 1200
        plt.show()
