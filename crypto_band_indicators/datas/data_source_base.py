from __future__ import annotations
import os
from typing import Dict, List, Tuple, Union
import pandas as pd
import numpy as np
import pandas_ta as ta
import backtrader as bt
from datetime import datetime, date, timedelta
from .. import utils, config
from wrapt import synchronized

class PandasDataFactory():
    @classmethod
    def create_feed(cls, lines, **kvargs):
        class_extensions = dict(
            lines=tuple(lines),
            params=tuple([(line, None) for line in lines]),
            # datafields=datafields,
        )

        extended_class = type('custom_pandas_data', (bt.feeds.PandasData,), class_extensions)
        return extended_class(**kvargs)

def _get_ta_ma_strategy(configs):
    return ta.Strategy(
        name="ta_ma_strategy",
        ta=configs
)

class DataSourceBase():
    cache_file_path = None
    index_column = 'date'
    numeric_columns = []
    text_columns = []
    
    def __init__(self, ticker_symbol: str = 'BTCUSDT'):
        self.ticker_symbol = ticker_symbol
        self.dataframe = None
        self.ta_columns = []

    @synchronized
    def load(self) -> DataSourceBase:
        cached_data = None
        missing_data = None
        missing_start_date = None
        errors = list()

        # Load cached csv data
        try:
            cached_data = self.read_cache()

            last_date_cached = cached_data.index.max() if isinstance(
                cached_data, pd.DataFrame) else None
            if last_date_cached:
                missing_start_date = last_date_cached.date() + timedelta(days=1)
        except Exception as e:
            errors.append(f"Error reading cache: {str(e)}")
            cached_data = None

        # Fetch API data
        if not config.get('disable_fetch') and not (config.get('only_cache') and isinstance(cached_data, pd.DataFrame)):
            # print(f"{type(self).__name__}: Fetching... ")
            try:
                missing_data = self.fetch_data(start=missing_start_date)
            except Exception as e:
                errors.append(f"Error fetching data: {str(e)}")
                missing_data = None

        # Validate data
        if not isinstance(cached_data, pd.DataFrame) and not isinstance(missing_data, pd.DataFrame):
            self.dataframe = None
            if len(errors) > 0:
                raise Exception(f"{type(self).__name__}: {', '.join(errors)}")
            else:
                raise Exception(f"{type(self).__name__}: Something went wrong loading the data...")

        # Concatenate data
        all_data = pd.concat([cached_data, missing_data])

        if (all_data.empty):
            raise Exception(f"{type(self).__name__}: No data available...")

        # Register data
        self.dataframe = all_data

        # Fill missing time series
        self.fill_the_gaps()

        # Write cache if there is something to write
        if not isinstance(cached_data, pd.DataFrame) or all_data.index.max() > cached_data.index.max():
            # print(f"{type(self).__name__}: Writing cache... ")
            self.write_cache()

        return self

    def fetch_data(self):
        pass

    def write_cache(self) -> None:
        self._validate_dataframe()

        local_cache_file_path = self.__class__.cache_file_path if self.__class__.cache_file_path else f"{type(self).__name__}.csv"
        local_index_column = self.__class__.index_column if self.__class__.index_column else 'date'
        self.dataframe.to_csv(local_cache_file_path, sep=';',
                              date_format='%Y-%m-%d', index=True, index_label=local_index_column)

    def read_cache(self) -> Union[pd.DataFrame, None]:
        local_cache_file_path = self.__class__.cache_file_path if self.__class__.cache_file_path else f"{type(self).__name__}.csv"
        cached_data = pd.read_csv(local_cache_file_path, sep=';')
        
        if not isinstance(cached_data, pd.DataFrame) or cached_data.empty:
            return None

        local_index_column = self.__class__.index_column if self.__class__.index_column else 'date'
        local_numeric_columns = self.__class__.numeric_columns if isinstance(
            self.__class__.numeric_columns, list) else list()

        # Convert column types and discard invalid data
        cached_data[local_index_column] = pd.to_datetime(
            cached_data[local_index_column], format='%Y-%m-%d')

        for local_numeric_column in local_numeric_columns:
            cached_data[local_numeric_column] = pd.to_numeric(
                cached_data[local_numeric_column], errors='coerce')
            # Drop 0, np values
            # cached_data = cached_data[cached_data[numeric_column] > 0]

        # Set index
        cached_data.set_index(
            local_index_column, drop=True, inplace=True)

        return cached_data

    def to_dataframe(self, start: Union[str, date, datetime, None] = None, end: Union[str, date, datetime, None] = None) -> pd.DataFrame:
        self._validate_dataframe()

        # Filter by dates
        start = utils.parse_any_date(start)
        end = utils.parse_any_date(end)
        return self.get_filtered_by_dates(start, end)

    def to_backtrade_feed(self, start: Union[str, date, datetime, None] = None, end: Union[str, date, datetime, None] = None) -> bt.feeds.PandasData:
        local_dataframe = self.to_dataframe(start, end)

        close_column_index = list(local_dataframe.columns).index("close")
                
        feed_parameters = {
            'dataname': local_dataframe,
            # datetime=list(ticker_data.columns).index("Date"),
            'high': None,
            'low': None,
            'open': close_column_index,
            'close': close_column_index,
            'volume': None,
            'openinterest': None,
        }

        # Check MA columns
        if self.ta_columns is not None and len(self.ta_columns) > 0:
            # params = dict()
            for ta_column in self.ta_columns:
                ta_column_index = list(local_dataframe.columns).index(ta_column)
                feed_parameters[ta_column] = ta_column_index
            
            return PandasDataFactory.create_feed(lines=self.ta_columns, **feed_parameters)

        return bt.feeds.PandasData(**feed_parameters)

    @synchronized
    def append_ta_columns(self, ta_configs: Union[List(Dict), Dict, None] = None, **kwargs) -> DataSourceBase:
        self._validate_dataframe()

        if ta_configs is None:
            return self

        if not isinstance(ta_configs, list):
            ta_configs = [ta_configs]
        
        self.dataframe.ta.cores = 0     # Disable multiprocessing (conflicts with backtrader)
        self.dataframe.ta.strategy(_get_ta_ma_strategy(ta_configs), **kwargs)

        # Save columns to be retrieve in get_ta_columns
        self.ta_columns.extend(self.dataframe.columns[-len(ta_configs):])
        
        return self
    
    # @synchronized
    def get_ta_columns(self) -> List(str):
        return self.ta_columns

    def fill_the_gaps(self, start: datetime = None, end: datetime = None) -> DataSourceBase:
        self._validate_dataframe()

        min = self.dataframe.index.min()
        max = self.dataframe.index.max()

        # Filter index range
        if start is not None:
            min = start if start > min else min
        if end is not None:
            max = end if end < max else max

        # start=min, end=max, freq="D"
        all_dates_range = pd.date_range(min, max)
        # print('missing_dates in self.dataframe: ', all_dates_range.difference(self.dataframe.index))

        self.dataframe = self.dataframe.reindex(
            all_dates_range, fill_value=np.nan).interpolate()

        return self

    def get_filtered_by_dates(self, start: datetime = None, end: datetime = None) -> pd.DataFrame:
        self._validate_dataframe()

        min = start if start is not None else self.dataframe.index.min()
        max = end if end is not None else self.dataframe.index.max()

        return self.dataframe[(self.dataframe.index >= min) & (self.dataframe.index <= max)]

    def get_value_start_end(self, start: Union[str, date, datetime, None] = None, end: Union[str, date, datetime, None] = None, column_name: str = 'close') -> Tuple(float):
        self._validate_dataframe()

        # Get start index
        start_index = utils.parse_any_date(start)
        if not start_index:
            start_index = self.dataframe.index.min()

        # Get end index
        end_index = utils.parse_any_date(end)
        if not end_index:
            end_index = self.dataframe.index.max()

        rwa_serie_start = self.dataframe[self.dataframe.index ==
                                         pd.to_datetime(start_index)]
        rwa_serie_end = self.dataframe[self.dataframe.index == pd.to_datetime(
            end_index)]
        return (float(rwa_serie_start[column_name]), float(rwa_serie_end[column_name]))

    def _validate_dataframe(self):
        if not isinstance(self.dataframe, pd.DataFrame):
            raise Exception('Data source not loaded or invalid. Did you forget to call load()?')

    @classmethod
    def _reindex_dataframes(cls, data1: pd.DataFrame, data2: pd.DataFrame, date_column_name: str = 'Date', start_date: Union[str, date, datetime, None] = None, end_date: Union[str, date, datetime, None] = None) -> pd.DataFrame:
        # df = df.set_index('timestamp').resample('S').ffill().reset_index()

        # https://stackoverflow.com/a/69052477
        dt1 = data1.set_index(date_column_name, drop=True)
        dt2 = data2.set_index(date_column_name, drop=True)

        # Get min and max across the 2 dataframes
        min1 = dt1.index.min()
        max1 = dt1.index.max()
        min2 = dt2.index.min()
        max2 = dt2.index.max()

        min = min1 if min1 < min2 else min2
        max = max1 if max1 > max2 else max2

        # Cut range between start_date and end_date:
        start_date = utils.parse_any_date(start_date, None)
        end_date = utils.parse_any_date(end_date, None)
        if start_date is not None:
            min = start_date if start_date > min else min
        if end_date is not None:
            max = end_date if end_date < max else max

        # start=min, end=max, freq="D"
        all_dates_range = pd.date_range(min, max)
        # print('missing_dates in dt1: ', all_dates_range.difference(dt1.index))
        # print('missing_dates in dt2: ', all_dates_range.difference(dt2.index))
        # print('\n')
        # print('all_dates_range: ', all_dates_range)

        dt1 = dt1.reindex(all_dates_range, fill_value=np.nan).interpolate()
        dt2 = dt2.reindex(all_dates_range, fill_value=np.nan).interpolate()

        dt1[date_column_name] = dt1.index
        dt2[date_column_name] = dt2.index
        dt1.reset_index(drop=True, inplace=True)
        dt2.reset_index(drop=True, inplace=True)

        return dt1, dt2

    # fill missing dates in dataframe and return dataframe object
    # tested on only YYYY-MM-DD format
    # ds=fill_in_missing_dates(ds,date_col_name='Date')
    # ds= dataframe object
    # date_col_name= col name in your dataframe, has datevalue
    # Source: https://github.com/n-idhisharma/mywork/blob/09942f15f6859e94e5dbb9fcb1af05ac7f627b06/Py_filling_missing_dates
    @classmethod
    def _fillin_dataframe(cls, data: pd.DataFrame, date_col_name='Date', fill_val=np.nan, date_format='%Y-%m-%d'):
        df = data.set_index(date_col_name, drop=True)
        df.index = pd.to_datetime(df.index, format=date_format)
        idx = pd.date_range(df.index.min(), df.index.max())
        # print('missing_dates are', idx.difference(df.index))
        df = df.reindex(idx, fill_value=fill_val)
        # print('missing_dates after fill',idx.difference(df.index))
        df[date_col_name] = df.index
        df.reset_index(drop=True, inplace=True)
        return df
