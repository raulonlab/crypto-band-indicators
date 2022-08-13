from logging import exception
from typing import Union
from datetime import datetime, date
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from cryptowatsonindicators import datas, utils

RAINBOW_BANDS_NAMES = ["Maximum bubble!!", "Sell, seriouly sell!", "FOMO intensifies", "Is this a bubble?", "HODL", "Still cheap", "Accumulate", "Buy!", "Fire sale!!"]
RAINBOW_BANDS_COLORS = ['#ff1716', '#e76a5e', '#ff852a', '#fec68b', '#fff48b', '#b0e072', '#63ce9c', '#36b1c6', '#276feb']
RAINBOW_BANDS_FIBONACCI_MULTIPLIERS = [0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.3, 2.1, 3.4]
RAINBOW_BANDS_ORIGINAL_MULTIPLIERS = [0, 0.1, 0.2, 0.35, 0.5, 0.75, 1, 2.5, 3]

class Rwa:
    def __init__(self, start_date: Union[str, date, datetime, None] = None, ticker_symbol:str = 'BTCUSDT', binance_api_key:str = '', binance_secret_key:str = ''):
        self.start_date = start_date
        self.ticker_symbol = ticker_symbol
        self.binance_api_key = binance_api_key
        self.binance_secret_key = binance_secret_key

        # load data
        self.data = datas.get_nasdaq_ticker_time_series(start_date)

        if (self.data is None or self.data.empty):
            e = f"Rwa constructor: No historical data available"
            print(e)
            raise exception(e) 

        # calculate fitted data columns
        # getting your x and y data from the dataframe
        xdata = np.array([x + 1 for x in range(len(self.data))])
        ydata = np.log(self.data["Value"])
        # here we ar fitting the curve, you can use 2 data points however I wasn't able to get a graph that looked as good with just 2 points.
        popt, pcov = curve_fit(Rwa._rwa_logarithmic_function, xdata, ydata, p0 = [10, 100, 90])  # p0 is justa guess, doesn't matter as far as I know
        # This is our fitted data, remember we will need to get the ex of it to graph it
        self.fittedYData = Rwa._rwa_logarithmic_function(xdata, popt[0], popt[1], popt[2])
        # Add columns with rainbow coordenates
        for i in range(-2, 6):
            self.data[f"fitted_data{i}"] = np.exp(self.fittedYData + i * .455)


    def plot_rainbow(self):
        if (self.data is None or self.data.empty):
            print(f"[warn] plot_rainbow: No historical data available")
            return None

        # Dark background looks nice
        # plt.style.use("dark_background")
        # Plot in a with long Y axis
        plt.semilogy(self.data["Date"], self.data["Value"], 'k-', linewidth=1)
        plt.title('Bitcoin Rainbow Chart')
        plt.xlabel('Date')
        plt.ylabel('Bitcoin price in log scale')

        # Draw the rainbow bands
        for i in range(-2,6):
            self.data[f"fitted_data{i}"] = np.exp(self.fittedYData + i*.455)
            plt.plot(self.data["Date"], np.exp(self.fittedYData + i*.455), linewidth=1, markersize=0.5)
            # You can use the below plot fill between rather than the above line plot, I prefer the line graph
            # plt.fill_between(self.data["Date"], np.exp(self.fittedYData + i*.45 -1), np.exp(self.fittedYData + i*.45), alpha=0.4, linewidth=1)

        # x ticks
        data_length = len(self.data)
        xticks = self.data['Date'].iloc[lambda x: x.index % int(data_length/10) == 0].tolist()
        xticks[0] = self.data['Date'].iloc[0]
        xticks[-1] = self.data['Date'].iloc[-1]
        plt.xticks(xticks, fontsize = 10, rotation = 45, ha='right' )

        plt.axvline(x = date.today(), color = 'black', label = 'Today')

        # Show plot
        plt.rcParams['figure.dpi'] = 600
        plt.rcParams['savefig.dpi'] = 600
        plt.show()


    def get_current_rainbow_band(self):
        # Get current ticker price from Binance
        price_dict = data.get_binance_ticker_market_price(self.binance_api_key, self.binance_secret_key, ticker_symbol=self.ticker_symbol)
        current_price = float(price_dict["price"])

        # Get rainbow band (at the most recent time of the time series)
        return self.get_rainbow_band(current_price)


    def get_rainbow_band(self, price: float, at_date: Union[str, date, datetime, None] = None ):
        if (self.data is None or self.data.empty):
            print(f"[warn] get_rainbow_band: No historical data available")
            return None
        
        at_date_index = -1
        at_date_value = date.today()
        if at_date:
            at_date_value = utils.parse_any_date(at_date, datetime.now()).date()
            at_date_pd = pd.Timestamp(at_date_value)

            # find fitted_data index at date
            at_date_index_list = list(self.data[self.data['Date'] == at_date_pd].index)
            if (len(at_date_index_list) == 0):
                print(f"[warn] get_rainbow_band: Data not found at date {at_date_value}")
                return None

            at_date_index = int(at_date_index_list[0])

        # Search for the band index 
        band_index = -1
        # Fire sale!!, index 8
        if price < self.data["fitted_data-2"].iloc[at_date_index]:
            band_index = 8
        
        # Buy!, index 7
        elif price > self.data["fitted_data-2"].iloc[at_date_index] and price < self.data["fitted_data-1"].iloc[at_date_index]:
            band_index = 7
        
        # Accumulate, index 6
        elif price > self.data["fitted_data-1"].iloc[at_date_index] and price < self.data["fitted_data0"].iloc[at_date_index]:
            band_index = 6

        # Still cheap, index 5
        elif price > self.data["fitted_data0"].iloc[at_date_index] and price < self.data["fitted_data1"].iloc[at_date_index]:
            band_index = 5

        # HODL, index 4
        elif price > self.data["fitted_data1"].iloc[at_date_index] and price < self.data["fitted_data2"].iloc[at_date_index]:
            band_index = 4

        # Is this a bubble?, index 3
        elif price > self.data["fitted_data2"].iloc[at_date_index] and price < self.data["fitted_data3"].iloc[at_date_index]:
            band_index = 3

        # FOMO intensifies, index 2
        elif price > self.data["fitted_data3"].iloc[at_date_index] and price < self.data["fitted_data4"].iloc[at_date_index]:
            band_index = 2

        # Sell, seriouly sell!, index 1
        elif price> self.data["fitted_data4"].iloc[at_date_index] and price <  self.data["fitted_data5"].iloc[at_date_index]:
            band_index = 1

        # Maximum bubble!!, index 0
        else:
            band_index = 0

        query_info = {
            'ticker_symbol': self.ticker_symbol,
            'date': at_date_value,
            'price': price,
        }
        rwa_info = Rwa._get_rainbow_info_by_index(band_index)
        return {**query_info, **rwa_info}


    @classmethod
    def _rwa_logarithmic_function(cls, x,a,b,c):
        return a*np.log(b+x) + c


    @classmethod
    def _get_rainbow_info_by_index(cls, index: int = -1) -> dict:
        if (index < 0 or index > len(RAINBOW_BANDS_NAMES)):
            return dict()
        
        return {
            'band_index': index,
            'band_ordinal': f"{index + 1}/9",
            'band_name': RAINBOW_BANDS_NAMES[index],
            'band_color': RAINBOW_BANDS_COLORS[index],
            'band_fib_multiplier': RAINBOW_BANDS_FIBONACCI_MULTIPLIERS[index],
            'band_original_multiplier': RAINBOW_BANDS_ORIGINAL_MULTIPLIERS[index],
        }
