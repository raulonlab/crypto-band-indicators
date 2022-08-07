from typing import Union
from datetime import datetime, date
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from .helpers import data

def plot_fng(start_date: Union[str, date, datetime, None] = None):
    historical_data = data.get_fng_time_series(start_date)

    if (historical_data is None or historical_data.empty):
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
    range1 = historical_data[historical_data['Value'].between(0, 25, inclusive='left')]
    range2 = historical_data[historical_data['Value'].between(25, 46, inclusive='left')]
    range3 = historical_data[historical_data['Value'].between(46, 54, inclusive='both')]
    range4 = historical_data[historical_data['Value'].between(54, 75, inclusive='right')]
    range5 = historical_data[historical_data['Value'].between(75, 100, inclusive='right')]

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
    data_length = len(historical_data)
    xticks = historical_data['Date'].iloc[lambda x: x.index % int(data_length/20) == 0].tolist()
    xticks[0] = historical_data['Date'].iloc[0]
    xticks[-1] = historical_data['Date'].iloc[-1]
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


def get_current_fng():
    historical_data = data.get_fng_time_series()

    if (historical_data.empty):
        return None

    current_data = historical_data.iloc[-1].to_dict()

    return {
        'date': current_data.get('Date'),
        'fng_value': current_data.get('Value'),
        'fng_name': current_data.get('ValueName'),
    }
