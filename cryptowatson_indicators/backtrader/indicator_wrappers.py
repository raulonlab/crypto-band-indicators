from datetime import timedelta
import backtrader as bt
import pandas as pd
from cryptowatson_indicators.datas.fng_data_source import FngDataSource
from cryptowatson_indicators.datas.ticker_data_source import TickerDataSource
from cryptowatson_indicators.indicators import FngIndicator, RainbowIndicator


def _get_ta_ma_config(kind, length): return {
    "kind": kind, "length": length, "col_numbers": (0,), "col_names": ("close_ma",)}


class BandIndicatorWrapper(bt.Indicator):
    lines = ('band_index', )

    params = dict(
        ma_kind=None,    # pandas_ta ma indicator to use instead of raw value
        ma_period=7,     # pandas_ta ma indicator period
    )

    def __str__(self):
        return '(No indicator)'

    def plot_axes(self, *args, **kwargs):
        pass


class FngBandIndicatorWrapper(BandIndicatorWrapper):
    def __init__(self):
        indicator_data_source = FngDataSource()
        indicator_data_source.load()
        data_column = 'close'

        if self.params.ma_kind is not None:
            self.addminperiod(self.params.ma_period)

            ta_ma_config = _get_ta_ma_config(
                self.params.ma_kind, self.params.ma_period)
            indicator_data_source = indicator_data_source.append_ta_column(
                ta_config=ta_ma_config)
            data_column = "close_ma"

        self.fng = FngIndicator(
            data=indicator_data_source.to_dataframe(), data_column=data_column)

    def next(self):
        bar_fng_value = self.fng.get_fng_value(self.data.datetime.date())
        bar_fng_info = FngIndicator._get_fng_value_details(bar_fng_value)
        self.lines.band_index[0] = int(bar_fng_info.get('fng_index'))
    
    # def once(self, start, end):
    #     print('FngBandIndicatorWrapper.once()')
    #     band_index_array = self.lines.band_index.array

    #     for i in pd.date_range(start, end - timedelta(days=1), freq='d'):
    #         bar_fng_value = self.fng.get_fng_value(i)
    #         bar_fng_info = FngIndicator._get_fng_value_details(bar_fng_value)

    #         band_index_array[i] = int(bar_fng_info.get('fng_index'))

    def __str__(self):
        return 'Fear and Greed'

    def plot_axes(self, axes, start=None, end=None):
        return self.fng.plot_axes(axes, start=start, end=end)


class RainbowBandIndicatorWrapper(BandIndicatorWrapper):
    def __init__(self):
        indicator_data_source = TickerDataSource()
        indicator_data_source.load()
        data_column = 'close'

        self.rainbow = RainbowIndicator(
            data=indicator_data_source.to_dataframe(), data_column=data_column)

    def next(self):
        band_index = self.rainbow.get_rainbow_band_index(
            price=self.data.close[0], at_date=self.data.datetime.date())
        
        # print('price: ', self.data.close[0])
        # print('at_date: ', self.data.datetime.date())
        # print('band_index: ', band_index)

        self.lines.band_index[0] = int(band_index)

    # def once(self, start, end):
    #    band_index_array = self.lines.band_index.array

    #    for i in pd.date_range(start, end - timedelta(days=1), freq='d'):
    #        band_index = self.rainbow.get_rainbow_band_index(
    #            price=self.data.close[0], at_date=self.data.datetime.date())

    #        band_index_array[i] = int(band_index)

    def __str__(self):
        return 'Rainbow band'

    def plot_axes(self, axes, start=None, end=None):
        return self.rainbow.plot_axes(axes, start=start, end=end)
