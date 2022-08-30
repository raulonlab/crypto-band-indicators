from logging import exception
from typing import Dict, Tuple, Union
from datetime import datetime, date
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from cryptowatson_indicators.datas import FngDataSource
from cryptowatson_indicators import utils

# 0-25: Extreme Fear
# 26-46: Fear
# 47-54: Neutral
# 55-75: Greed
# 76-100: Extreme Greed
_FNG_THRESHOLDS = [25,             46,        54,        75,        100]
_FNG_NAMES = ["Extreme Fear", "Fear",    "Neutral", "Greed",   "Extreme Greed"]
# https://colordesigner.io/gradient-generator/?mode=rgb#DE2121-21DE21
_FNG_COLORS = ["#C05840",      "#FC9A24", "#E5C769", "#B4E168", "#5CBC3C"]
_FNG_MULTIPLIERS = [1.5,            1.25,      1,         0.75,      0.5]

class BandDetails:
    band_index=0
    band_ordinal=''
    name=''
    color=''
    multiplier=1
        

class BandIndicatorBase:
    _band_thresholds=[]
    _band_names=[]
    _band_colors=[]
    # def __init__(self, data: Union[pd.DataFrame, None] = None, data_column: str = 'close', indicator_start_date: Union[str, date, datetime, None] = None, ticker_symbol: str = 'BTCUSDT', binance_api_key: str = '', binance_secret_key: str = ''):
    #     self.ticker_symbol = ticker_symbol
    #     self.binance_api_key = binance_api_key
    #     self.binance_secret_key = binance_secret_key
    #     self.data_column = data_column

    #     # load indicator data
    #     if isinstance(data, pd.DataFrame):
    #         self.indicator_data = data
    #     else:
    #         self.indicator_data = FngDataSource().to_dataframe(start=indicator_start_date)

    #     if not isinstance(self.indicator_data, pd.DataFrame) or self.indicator_data.empty:
    #         error_message = f"FngBandIndicator.constructor: No indicator data available"
    #         print(f"[error] {error_message}")
    #         raise exception(error_message)

    # def get_current_band(self) -> Union[int, None]:
    #     return self.get_band_at(at_date=None)
    
    def get_band_at(self, at_date) -> Union[int, None]:
        pass

    def get_band_details_at(self, at_date) -> Union[BandDetails, None]:
        pass

    def plot_axes(self, axes, start=None, end=None):
        pass

