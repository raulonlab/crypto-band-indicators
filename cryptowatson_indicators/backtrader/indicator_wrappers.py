from datetime import timedelta
from logging import exception
import backtrader as bt
import pandas as pd
from cryptowatson_indicators.datas.fng_data_source import FngDataSource
from cryptowatson_indicators.datas.ticker_data_source import TickerDataSource
from cryptowatson_indicators.indicators import FngBandIndicator, RainbowBandIndicator
from cryptowatson_indicators.indicators.band_indicator_base import BandIndicatorBase


def _get_ta_ma_config(kind, length): return {
    "kind": kind, "length": length, "col_numbers": (0,), "col_names": ("close_ma",)}

class BandIndicatorWrapper(bt.Indicator):
    lines = ('band_index', )

    params = dict(
        band_indicator=None,    # band indicator instance
    )

    def __init__(self):
        if not isinstance(self.params.band_indicator, BandIndicatorBase):
            raise exception('band_indicator parameter must be an instance of BandIndicatorBase')
            
        self.band_indicator = self.params.band_indicator
    
    def next(self):
        self.lines.band_index[0] = self.band_indicator.get_band_at(price=self.data.close[0], at_date=self.data.datetime.date())

    def __str__(self):
        return str(self.band_indicator)

    def plot_axes(self, axes, start=None, end=None):
        return self.band_indicator.plot_axes(axes, start=start, end=end)

# class BandIndicatorWrapperOld(bt.Indicator):
#     lines = ('band_index', )

#     params = dict(
#         ma_kind=None,    # pandas_ta ma indicator to use instead of raw value
#         ma_period=7,     # pandas_ta ma indicator period
#     )

#     def __str__(self):
#         return '(No indicator)'

#     def plot_axes(self, *args, **kwargs):
#         pass


# class FngBandIndicatorWrapper(BandIndicatorWrapperOld):
#     def __init__(self):
#         indicator_data_source = FngDataSource()
#         indicator_data_source.load()
#         data_column = 'close'

#         if self.params.ma_kind is not None:
#             self.addminperiod(self.params.ma_period)

#             ta_ma_config = _get_ta_ma_config(
#                 self.params.ma_kind, self.params.ma_period)
#             indicator_data_source = indicator_data_source.append_ta_column(
#                 ta_config=ta_ma_config)
#             data_column = "close_ma"

#         self.fng = FngBandIndicator(
#             data=indicator_data_source.to_dataframe(), data_column=data_column)

#     def next(self):
#         self.lines.band_index[0] = self.fng.get_band_at(self.data.datetime.date())
    
#     # def once(self, start, end):
#     #     print('FngBandIndicatorWrapper.once()')
#     #     band_index_array = self.lines.band_index.array

#     #     for i in pd.date_range(start, end - timedelta(days=1), freq='d'):
#     #         bar_fng_value = self.fng.get_value_at(i)
#     #         bar_fng_info = FngBandIndicator._get_fng_value_details(bar_fng_value)

#     #         band_index_array[i] = int(bar_fng_info.get('fng_index'))

#     def __str__(self):
#         return 'Fear and Greed'

#     def plot_axes(self, axes, start=None, end=None):
#         return self.fng.plot_axes(axes, start=start, end=end)


# class RainbowBandIndicatorWrapper(BandIndicatorWrapperOld):
#     def __init__(self):
#         indicator_data_source = TickerDataSource()
#         indicator_data_source.load()
#         data_column = 'close'

#         self.rainbow = RainbowBandIndicator(
#             data=indicator_data_source.to_dataframe(), data_column=data_column)

#     def next(self):
#         self.lines.band_index[0] = self.rainbow.get_band_at(price=self.data.close[0], at_date=self.data.datetime.date())

#     # def once(self, start, end):
#     #    band_index_array = self.lines.band_index.array

#     #    for i in pd.date_range(start, end - timedelta(days=1), freq='d'):
#     #        band_index = self.rainbow.get_rainbow_band_index(
#     #            price=self.data.close[0], at_date=self.data.datetime.date())

#     #        band_index_array[i] = int(band_index)

#     def __str__(self):
#         return 'Rainbow band'

#     def plot_axes(self, axes, start=None, end=None):
#         return self.rainbow.plot_axes(axes, start=start, end=end)
