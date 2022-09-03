from typing import Union
import pandas as pd

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
    _default_column = 'close' 
    data = None
    data_column = 'close'  # select data column: ie: moving average data column
    ticker_symbol = 'BTCUSDT'
    def __init__(self, data: Union[pd.DataFrame, None] = None, data_column: str = None, ticker_symbol: str = 'BTCUSDT', **kvargs):
        self.ticker_symbol = ticker_symbol
        self.data = None
        self.data_column = 'close'  # select data column: ie: moving average data column
        
        if isinstance(data, pd.DataFrame):
            self.data = data
        
            if self.data.empty:
                error_message = f"BandIndicatorBase.__init__: data is empty"
                print(f"[error] {error_message}")
                raise Exception(error_message)
            
            if data_column is not None:
                self.data_column = data_column
            
            if not self.data_column in self.data.columns:
                error_message = f"BandIndicatorBase.__init__: data_column doesn't exist in data"
                print(f"[error] {error_message}")
                raise Exception(error_message)

    def get_band_at(self) -> Union[int, None]:
        pass

    def get_band_details_at(self) -> Union[BandDetails, None]:
        pass

    def plot_axes(self):
        pass

