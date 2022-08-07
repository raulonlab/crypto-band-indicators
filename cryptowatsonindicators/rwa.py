from typing import Union
from datetime import datetime, date
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from .helpers import data

RAINBOW_BANDS_NAMES = ["Maximum bubble!!", "Sell, seriouly sell!", "FOMO intensifies", "Is this a bubble?", "HODL", "Still cheap", "Accumulate", "Buy!", "Fire sale!!"]
RAINBOW_BANDS_COLORS = ['#ff1716', '#e76a5e', '#ff852a', '#fec68b', '#fff48b', '#b0e072', '#63ce9c', '#36b1c6', '#276feb']
RAINBOW_BANDS_FIBONACCI_MULTIPLIERS = [0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.3, 2.1, 3.4]
RAINBOW_BANDS_ORIGINAL_MULTIPLIERS = [0, 0.1, 0.2, 0.35, 0.5, 0.75, 1, 2.5, 3]

def _rwa_logarithmic_function(x,a,b,c):
    return a*np.log(b+x) + c

def plot_rainbow(start_date: Union[str, date, datetime, None] = None):
    historical_data = data.get_nasdaq_ticker_time_series(start_date)

    if (historical_data is None or historical_data.empty):
        print(f"[warn] plot_fng: No historical data available")
        return None

    # getting your x and y data from the dataframe
    xdata = np.array([x+1 for x in range(len(historical_data))])
    ydata = np.log(historical_data["Value"])

    # here we ar fitting the curve, you can use 2 data points however I wasn't able to get a graph that looked as good with just 2 points.
    popt, pcov = curve_fit(_rwa_logarithmic_function, xdata, ydata, p0 = [10,100,90]) # p0 is just a guess, doesn't matter as far as I know

    # This is our fitted data, remember we will need to get the ex of it to graph it
    fittedYData = _rwa_logarithmic_function(xdata, popt[0], popt[1], popt[2])

    # Dark background looks nice
    # plt.style.use("dark_background")
    # Plot in a with long Y axis
    plt.semilogy(historical_data["Date"], historical_data["Value"], 'k-', linewidth=1)
    plt.title('Bitcoin Rainbow Chart')
    plt.xlabel('Date')
    plt.ylabel('Bitcoin price in log scale')

    # Draw the rainbow bands
    for i in range(-2,6):
        historical_data[f"fitted_data{i}"] = np.exp(fittedYData + i*.455)
        plt.plot(historical_data["Date"], np.exp(fittedYData + i*.455), linewidth=1, markersize=0.5)
        # You can use the below plot fill between rather than the above line plot, I prefer the line graph
        # plt.fill_between(historical_data["Date"], np.exp(fittedYData + i*.45 -1), np.exp(fittedYData + i*.45), alpha=0.4, linewidth=1)
    
    # plt.scatter(monthly["Date"],monthly["Value"], c="red")

    # if (start_date_xlim):
    #     first_date = start_date_xlim
    # else:
    #     first_date = historical_data.iloc[0, 0]
    
    # last_date = historical_data.iloc[-1, 0]

    # x ticks
    data_length = len(historical_data)
    xticks = historical_data['Date'].iloc[lambda x: x.index % int(data_length/10) == 0].tolist()
    xticks[0] = historical_data['Date'].iloc[0]
    xticks[-1] = historical_data['Date'].iloc[-1]
    plt.xticks(xticks, fontsize = 10, rotation = 45, ha='right' )

    plt.axvline(x = date.today(), color = 'black', label = 'Today')
 
    # x limit (zoom)
    # plt.xlim(left=first_date)
    
    # Show plot
    plt.rcParams['figure.dpi'] = 600
    plt.rcParams['savefig.dpi'] = 600
    # plt.rcParams['figure.figsize'] = [20/2.54, 16/2.54]
    plt.show()

def _get_rainbow_band_info_by_index(index: int = -1) -> dict:
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

def get_current_rainbow_band(binance_api_key:str, binance_secret_key:str, ticker_symbol: str = 'BTCUSDT'):
    historical_data = data.get_nasdaq_ticker_time_series()

    # getting your x and y data from the dataframe
    xdata = np.array([x + 1 for x in range(len(historical_data))])
    ydata = np.log(historical_data["Value"])
    # here we ar fitting the curve, you can use 2 data points however I wasn't able to get a graph that looked as good with just 2 points.
    popt, pcov = curve_fit(_rwa_logarithmic_function, xdata, ydata, p0 = [10, 100, 90])  # p0 is justa guess, doesn't matter as far as I know
    # This is our fitted data, remember we will need to get the ex of it to graph it
    fittedYData = _rwa_logarithmic_function(xdata, popt[0], popt[1], popt[2])
    # Draw the rainbow bands
    for i in range(-2, 6):
        historical_data[f"fitted_data{i}"] = np.exp(fittedYData + i * .455)

    # Get current ticker price from Binance
    price_dict = data.get_binance_ticker_market_price(binance_api_key, binance_secret_key, ticker_symbol=ticker_symbol)
    current_price = float(price_dict["price"])

    current_index = -1
    # Fire sale!!, index 8
    if current_price < historical_data["fitted_data-2"].iloc[-1]:
        current_index = 8
    
    # Buy!, index 7
    elif current_price > historical_data["fitted_data-2"].iloc[-1] and current_price < historical_data["fitted_data-1"].iloc[-1]:
        current_index = 7
    
    # Accumulate, index 6
    elif current_price > historical_data["fitted_data-1"].iloc[-1] and current_price < historical_data["fitted_data0"].iloc[-1]:
        current_index = 6

    # Still cheap, index 5
    elif current_price > historical_data["fitted_data0"].iloc[-1] and current_price < historical_data["fitted_data1"].iloc[-1]:
        current_index = 5

    # HODL, index 4
    elif current_price > historical_data["fitted_data1"].iloc[-1] and current_price < historical_data["fitted_data2"].iloc[-1]:
        current_index = 4

    # Is this a bubble?, index 3
    elif current_price > historical_data["fitted_data2"].iloc[-1] and current_price < historical_data["fitted_data3"].iloc[-1]:
        current_index = 3

    # FOMO intensifies, index 2
    elif current_price > historical_data["fitted_data3"].iloc[-1] and current_price < historical_data["fitted_data4"].iloc[-1]:
        current_index = 2

    # Sell, seriouly sell!, index 1
    elif current_price> historical_data["fitted_data4"].iloc[-1] and current_price <  historical_data["fitted_data5"].iloc[-1]:
        current_index = 1

    # Maximum bubble!!, index 0
    else:
        current_index = 0

    query_info = {
        'ticker_symbol': ticker_symbol,
        'date': date.today(),
        'price': current_price,
    }
    band_info = _get_rainbow_band_info_by_index(current_index)
    return {**query_info, **band_info}
