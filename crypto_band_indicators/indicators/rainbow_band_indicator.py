from typing import Union
from datetime import datetime, date
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.optimize import curve_fit
from ..datas import TickerDataSource
from .. import utils
from .band_indicator_base import BandIndicatorBase, BandDetails

_FITTED_BAND_LOG_MULTIPLIER = .455

def _rainbow_logarithmic_function(x, a, b, c):
        return a*np.log(b+x) + c

class RainbowBandIndicator(BandIndicatorBase):
    _band_thresholds= []
    _band_names=      ["Maximum bubble!!", "Sell, seriouly sell!", "FOMO intensifies",
                        "Is this a bubble?", "HODL", "Still cheap", "Accumulate", "Buy!", "Fire sale!!"]
    _band_colors=     ['#6b8ed0', '#78acb2', '#84ca95',
                         '#c0de9a', '#feed94', '#f8c37d', '#f1975e', '#df6a4d', '#cf463f']
    _band_multipliers=[0, 0.1, 0.2, 0.35, 0.5, 0.75, 1, 2.5, 3]
    _band_multipliers_fibonacci=[0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.3, 2.1, 3.4]
    def __init__(self, indicator_start_date: Union[str, date, datetime, None] = None, binance_api_key: str = '', binance_secret_key: str = '', fitted_multiplier: float = _FITTED_BAND_LOG_MULTIPLIER, **kvargs):
        super().__init__(**kvargs)
        self.binance_api_key = binance_api_key
        self.binance_secret_key = binance_secret_key

        # load indicator data if not passed
        if not isinstance(self.data, pd.DataFrame):
            data_source = TickerDataSource().load()
            self.data = data_source.to_dataframe(start=indicator_start_date)

        if not isinstance(self.data, pd.DataFrame) or self.data.empty:
            error_message = f"RainbowBandIndicator.__init__: No indicator data available"
            print(f"[error] {error_message}")
            raise Exception(error_message)


        # calculate fitted data columns
        # getting your x and y data from the dataframe
        xdata = np.array([x + 1 for x in range(len(self.data))])
        ydata = np.log(self.data[self.data_column])
        # here we ar fitting the curve, you can use 2 data points however I wasn't able to get a graph that looked as good with just 2 points.
        # p0=[10, 100, 90], p0 is justa guess, doesn't matter as far as I know
        popt, pcov = curve_fit(
            _rainbow_logarithmic_function, xdata, ydata)
        
        # This is our fitted data, remember we will need to get the ex of it to graph it
        self.fittedYData = _rainbow_logarithmic_function(
            xdata, popt[0], popt[1], popt[2])
        # Add columns with rainbow coordenates
        for i in range(-3, 7):
            self.data[f"fitted_data{i}"] = np.exp(
                self.fittedYData + i * fitted_multiplier)


    def _get_current_ticker_market_price(self) -> Union[float, None]:
        # Get current ticker price from Binance
        price_dict = TickerDataSource.get_binance_ticker_market_price(self.ticker_symbol,
                                                                      self.binance_api_key, self.binance_secret_key)
        return float(price_dict['price']) if price_dict['price'] is not None else None


    def get_band_at(self, price: float = None, at_date: Union[str, date, datetime, None] = None) -> Union[int, None]:
        if not isinstance(self.data, pd.DataFrame) or self.data.empty:
            print(
                f"[warn] RainbowBandIndicator.get_band_at: No historical data available")
            return None
        
        if price is None:
            price = self._get_current_ticker_market_price()

        at_date = utils.parse_any_date(at_date)
        if not at_date:
            at_date = self.data.index.max().date()

        rainbow_serie_at = self.data[self.data.index == pd.to_datetime(
            at_date)]
        if (rainbow_serie_at.empty):
            print(
                f"[warn] RainbowBandIndicator.get_band_at: Data not found at date {at_date}")
            return None

        # Search for the band index
        band_index_at = -1
        # Fire sale!!
        if price < float(rainbow_serie_at["fitted_data-2"]):
            band_index_at = 8

        # Buy!
        elif price > float(rainbow_serie_at["fitted_data-2"]) and price <= float(rainbow_serie_at["fitted_data-1"]):
            band_index_at = 7

        # Accumulate
        elif price > float(rainbow_serie_at["fitted_data-1"]) and price <= float(rainbow_serie_at["fitted_data0"]):
            band_index_at = 6

        # Still cheap
        elif price > float(rainbow_serie_at["fitted_data0"]) and price <= float(rainbow_serie_at["fitted_data1"]):
            band_index_at = 5

        # HODL
        elif price > float(rainbow_serie_at["fitted_data1"]) and price <= float(rainbow_serie_at["fitted_data2"]):
            band_index_at = 4

        # Is this a bubble?
        elif price > float(rainbow_serie_at["fitted_data2"]) and price <= float(rainbow_serie_at["fitted_data3"]):
            band_index_at = 3

        # FOMO intensifies
        elif price > float(rainbow_serie_at["fitted_data3"]) and price <= float(rainbow_serie_at["fitted_data4"]):
            band_index_at = 2

        # Sell, seriouly sell!
        elif price > float(rainbow_serie_at["fitted_data4"]) and price <= float(rainbow_serie_at["fitted_data5"]):
            band_index_at = 1

        # Maximum bubble!!
        else:
            band_index_at = 0

        return band_index_at
    
    def get_band_details_at(self, price: float = None, at_date: Union[str, date, datetime, None] = None) -> Union[BandDetails, None]:
        band_index = self.get_band_at(price=price, at_date=at_date) 
        
        if (band_index is None or band_index < 0 or band_index > len(self._band_names) -1):
            return None
        
        band_details_at = BandDetails()
        band_details_at.band_index=band_index
        band_details_at.band_ordinal=f"{band_index + 1}/{len(self._band_names)}",
        band_details_at.name=self._band_names[band_index]
        band_details_at.color=self._band_colors[band_index]
        band_details_at.multiplier=self._band_multipliers[band_index]

        return band_details_at

    
    def plot_axes(self, axes, start=None, end=None):
        plot_data = self.data
        plot_data_column = self._default_column

        if start is not None:
            plot_data = plot_data[plot_data.index >= start]
        if end is not None:
            plot_data = plot_data[plot_data.index <= end]

        latest_serie = plot_data.iloc[-1]

        # Draw bitcoin price
        axes.semilogy(
            plot_data.index, plot_data[plot_data_column], color='#333333', linewidth=1)

        # Draw the rainbow bands
        for i in range(-2, 7):
            # You can use the below plot fill between rather than the above line plot, I prefer the line graph
            axes.fill_between(plot_data.index, plot_data[f"fitted_data{i-1}"],
                              plot_data[f"fitted_data{i}"], alpha=0.8, linewidth=1, color=self._band_colors[i+2])
            axes.plot(plot_data.index,
                      plot_data[f"fitted_data{i}"], linewidth=1, color=self._band_colors[i+2])

        # yticks
        axes.tick_params(axis='y', labelsize='x-small')

        # Add yticks on the right
        band_axis = axes.secondary_yaxis("right")

        rainbow_band_yticks = list()
        for i in range(-3, 7):
            # print(f"fitted_data{i}: ", latest_serie[f"fitted_data{i}"])
            rainbow_band_yticks.append(latest_serie[f"fitted_data{i}"])
        band_axis.set_yticks(rainbow_band_yticks)
        band_axis.set_yticklabels(
            [f"{rainbow_band_ytick:.2f}" for rainbow_band_ytick in rainbow_band_yticks])
        band_axis.tick_params(axis='y', labelsize='x-small')
        
        # Grid
        band_axis.grid(axis = 'y', linestyle = '--', linewidth = 0.5)

        return axes
    
    def __str__(self):
        return 'Rainbow'

    def plot_rainbow(self):
        if not isinstance(self.data, pd.DataFrame) or self.data.empty:
            print(f"[warn] plot_rainbow: No historical data available")
            return None

        latest_serie = self.data.iloc[-1]

        fig, axes = plt.subplots()
        fig.suptitle('Bitcoin Rainbow Chart', fontsize='large')
        plt.xlabel('Date')
        plt.ylabel('Bitcoin price in log scale')
        # axes.margins(x=0)

        # Draw bitcoin price
        axes.semilogy(
            self.data.index, self.data[self.data_column], color='#333333', linewidth=0.75)

        # Draw the rainbow bands
        for i in range(-2, 7):
            # You can use the below plot fill between rather than the above line plot, I prefer the line graph
            axes.fill_between(self.data.index, self.data[f"fitted_data{i-1}"],
                              self.data[f"fitted_data{i}"], alpha=0.8, linewidth=1, color=self._band_colors[i+2])
            axes.plot(self.data.index,
                      self.data[f"fitted_data{i}"], linewidth=1.5, markersize=0.5, color=self._band_colors[i+2])

        axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

        # Set xticks
        rwa_data_length = len(self.data)
        rwa_xticks = self.data.iloc[::int(
            rwa_data_length/20)].index.to_list()
        rwa_xticks[0] = self.data.index.min()
        rwa_xticks[-1] = self.data.index.max()
        axes.set_xticks(rwa_xticks)
        plt.xticks(fontsize=8, rotation=45, ha='right')

        # Add yticks on the right
        band_axis = axes.secondary_yaxis("right")

        rainbow_band_yticks = list()
        for i in range(-3, 7):
            # print(f"fitted_data{i}: ", latest_serie[f"fitted_data{i}"])
            rainbow_band_yticks.append(latest_serie[f"fitted_data{i}"])
        band_axis.set_yticks(rainbow_band_yticks)
        band_axis.set_yticklabels(
            [f"{rainbow_band_ytick:.2f}" for rainbow_band_ytick in rainbow_band_yticks])

        plt.show()
