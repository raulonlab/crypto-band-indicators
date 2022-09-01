import backtrader as bt
from crypto_band_indicators.indicators import BandIndicatorBase


def _get_ta_ma_config(kind, length): return {
    "kind": kind, "length": length, "col_numbers": (0,), "col_names": ("close_ma",)}

class BandIndicatorWrapper(bt.Indicator):
    lines = ('band_index', )

    params = dict(
        band_indicator=None,    # band indicator instance
    )

    def __init__(self):
        if not isinstance(self.params.band_indicator, BandIndicatorBase):
            raise Exception('band_indicator parameter must be an instance of BandIndicatorBase')
            
        self.band_indicator = self.params.band_indicator
    
    def next(self):
        self.lines.band_index[0] = self.band_indicator.get_band_at(price=self.data.close[0], at_date=self.data.datetime.date())

    def __str__(self):
        return str(self.band_indicator)

    def plot_axes(self, axes, start=None, end=None):
        return self.band_indicator.plot_axes(axes, start=start, end=end)
