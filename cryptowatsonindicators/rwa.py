from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import nasdaqdatalink
from .helpers import data

def _rwa_logarithmic_function(x,a,b,c):
    return a*np.log(b+x) + c

def plot_rainbow():
    raw_data = data.get_nasdaq_ticker_time_series()

    # Set high resolution
    plt.rcParams['figure.dpi'] = 1200

    # getting your x and y data from the dataframe
    xdata = np.array([x+1 for x in range(len(raw_data))])
    ydata = np.log(raw_data["Value"])

    # here we ar fitting the curve, you can use 2 data points however I wasn't able to get a graph that looked as good with just 2 points.
    popt, pcov = curve_fit(_rwa_logarithmic_function, xdata, ydata, p0 = [10,100,90]) # p0 is justa guess, doesn't matter as far as I know

    # This is our fitted data, remember we will need to get the ex of it to graph it
    fittedYData = _rwa_logarithmic_function(xdata, popt[0], popt[1], popt[2])

    # Dark background looks nice
    plt.style.use("dark_background")
    # Plot in a with long Y axis
    plt.semilogy(raw_data["Date"], raw_data["Value"])
    plt.title('Bitcoin Rainbow Chart')
    plt.xlabel('Time')
    plt.ylabel('Bitcoin price in log scale')

    # Draw the rainbow bands
    for i in range(-2,6):
        raw_data[f"fitted_data{i}"] = np.exp(fittedYData + i*.455)
        plt.plot(raw_data["Date"], np.exp(fittedYData + i*.455), linewidth=1, markersize=0.5)
        # You can use the below plot fill between rather than the above line plot, I prefer the line graph
        # plt.fill_between(raw_data["Date"], np.exp(fittedYData + i*.45 -1), np.exp(fittedYData + i*.45), alpha=0.4, linewidth=1)
    
    # plt.scatter(monthly["Date"],monthly["Value"], c="red")
    
    plt.show()


def rwa_calculations(binance_api_key:str, binance_secret_key:str, ticker_symbol: str = 'BTCUSDT', weight_type: str = "fibs"):
    raw_data = data.get_nasdaq_ticker_time_series()

    # getting your x and y data from the dataframe
    xdata = np.array([x + 1 for x in range(len(raw_data))])
    ydata = np.log(raw_data["Value"])
    # here we ar fitting the curve, you can use 2 data points however I wasn't able to get a graph that looked as good with just 2 points.
    popt, pcov = curve_fit(_rwa_logarithmic_function, xdata, ydata, p0 = [10, 100, 90])  # p0 is justa guess, doesn't matter as far as I know
    # This is our fitted data, remember we will need to get the ex of it to graph it
    fittedYData = _rwa_logarithmic_function(xdata, popt[0], popt[1], popt[2])
    # Draw the rainbow bands
    for i in range(-2, 6):
        raw_data[f"fitted_data{i}"] = np.exp(fittedYData + i * .455)

    historical_data = raw_data

    fibs = {"bubble": 0, "sell": 0.1, "FOMO": 0.2, "Bubble?": 0.3, "Hodl": 0.5, "cheap": 0.8, "accumulate": 1.3,
            "Buy": 2.1, "fire_sale": 3.4}
    originalRCA = {"bubble": 0, "sell": 0.1, "FOMO": 0.2, "Bubble?": 0.35, "Hodl": 0.5, "cheap": 0.75, "accumulate": 1,"Buy": 2.5, "fire_sale": 3}
    # Choose what type of weightings you want to RCA with

    if weight_type == "fibs":
        weighted = fibs
    else:
        weighted = originalRCA

    price_dict = data.get_binance_ticker_market_price(binance_api_key, binance_secret_key, ticker_symbol=ticker_symbol)
    current_price = float(price_dict["price"])
    print(type(current_price))
    print(historical_data["fitted_data-1"].iloc[-1])

    if current_price < historical_data["fitted_data-2"].iloc[-1]:
        print("Bitcoin is below $", historical_data["fitted_data-1"].iloc[-1], " therefore our multiplier is ", weighted["fire_sale"])
        # tweet("Bitcoin is below $", historical_data["fitted_data-1"].iloc[-1], " therefore our multiplier is ", weighted["fire_sale"])
        # dcaBot(ticker_symbol, dcaamount*weighted["fire_sale"])

    elif current_price > historical_data["fitted_data-2"].iloc[-1] and current_price < historical_data["fitted_data-1"].iloc[-1]:
        print("Bitcoin is below $", historical_data["fitted_data-1"].iloc[-1], " therefore our multiplier is ", weighted["Buy"])
        # tweet()
        # dcaBot(ticker_symbol, dcaamount*weighted["Buy"])

    elif current_price > historical_data["fitted_data-1"].iloc[-1] and current_price < historical_data["fitted_data0"].iloc[-1]:
        print("Bitcoins price falls between $", historical_data["fitted_data-1"].iloc[-1], "and $", historical_data["fitted_data0"].iloc[-1], " therefore our multiplier is ", weighted["accumulate"])
        # tweet()
        # dcaBot(ticker_symbol, dcaamount * weighted["accumulate"])

    elif current_price > historical_data["fitted_data0"].iloc[-1] and current_price < historical_data["fitted_data1"].iloc[-1]:
        print("Bitcoins price falls between $", historical_data["fitted_data0"].iloc[-1], "and $", historical_data["fitted_data1"].iloc[-1], " therefore our multiplier is ", weighted["cheap"])
        # tweet()
        # dcaBot(ticker_symbol, dcaamount * weighted["cheap"])

    elif current_price > historical_data["fitted_data1"].iloc[-1] and current_price < historical_data["fitted_data2"].iloc[-1]:
        print("Bitcoins price falls between $", historical_data["fitted_data1"].iloc[-1], "and $", historical_data["fitted_data2"].iloc[-1], " therefore our multiplier is ", weighted["Hodl"])
        # tweet()
        # dcaBot(ticker_symbol, dcaamount * weighted["Hodl"])

    elif current_price > historical_data["fitted_data2"].iloc[-1] and current_price < historical_data["fitted_data3"].iloc[-1]:
        print("Bitcoins price falls between $", historical_data["fitted_data2"].iloc[-1], "and $", historical_data["fitted_data3"].iloc[-1], " therefore our multiplier is ", weighted["Bubble?"])
        # tweet()
        # dcaBot(ticker_symbol, dcaamount * weighted["Bubble"])

    elif current_price > historical_data["fitted_data3"].iloc[-1] and current_price < historical_data["fitted_data4"].iloc[-1]:
        print("Bitcoins price falls between $", historical_data["fitted_data3"].iloc[-1], "and $", historical_data["fitted_data4"].iloc[-1], " therefore our multiplier is ", weighted["FOMO"])
        # tweet()
        # dcaBot(ticker_symbol, dcaamount * weighted["FOMO"])

    elif current_price> historical_data["fitted_data4"].iloc[-1] and current_price <  historical_data["fitted_data5"].iloc[-1]:
        print("Bitcoins price falls between $", historical_data["fitted_data4"].iloc[-1], "and $", historical_data["fitted_data5"].iloc[-1], " therefore our multiplier is ", weighted["sell"])
        # tweet()
        # dcaBot(ticker_symbol, dcaamount * weighted["sell"])

    else:
        print("Don't buy bitcoin")
