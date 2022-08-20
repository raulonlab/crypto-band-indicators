from __future__ import annotations
from binance.client import Client
from typing import List, Tuple, Union
import pandas as pd
import numpy as np
import backtrader as bt
from datetime import datetime, date, timedelta
from cryptowatson_indicators.utils import parse_any_date


class DataSourceBase:
    dataframe = None
    only_cache = False

    def __init__(self, ticker_symbol: str = 'BTCUSDT', binance_api_key: str = None, binance_secret_key: str = None):
        self.ticker_symbol = ticker_symbol
        self.binance_api_key = binance_api_key
        self.binance_secret_key = binance_secret_key

        self.load_data()

    def load_data(self) -> DataSourceBase:
        cached_data = None
        missing_data = None
        missing_start_date = None

        # Load cached csv data
        try:
            cached_data = self.read_cache()
            last_date_cached = cached_data.index.max() if isinstance(
                cached_data, pd.DataFrame) else None
            if last_date_cached:
                missing_start_date = last_date_cached.date() + timedelta(days=1)
        except Exception as e:
            print(
                f"[warn] Error reading cache in: {self.__class__}: {str(e)}")
            cached_data = None

        # Fetch API data
        if not self.only_cache:
            missing_data = self.fetch_data(start=missing_start_date)

        # Validate data
        if not isinstance(cached_data, pd.DataFrame) and not isinstance(missing_data, pd.DataFrame):
            self.dataframe = None
            return

        # Concatenate data
        all_data = pd.concat([cached_data, missing_data])

        if (all_data is None or all_data.empty):
            error_message = f"{type(self).__name__}: No data available"
            print(f"WARNING: {error_message}")
            return

        # Register data
        self.dataframe = all_data

        # Fill missing time series
        self.fill_the_gaps()

        # Write cache
        self.write_cache()

        return self

    def fetch_data(self):
        pass

    def write_cache(self) -> None:
        local_cache_file_path = self.cache_file_path if self.cache_file_path else f"{type(self).__name__}.csv"
        local_index_column = self.index_column if self.index_column else 'date'
        self.dataframe.to_csv(local_cache_file_path, sep=';',
                              date_format='%Y-%m-%d', index=True, index_label=local_index_column)

    def read_cache(self) -> Union[pd.DataFrame, None]:
        local_cache_file_path = self.cache_file_path if self.cache_file_path else f"{type(self).__name__}.csv"
        cached_data = pd.read_csv(local_cache_file_path, sep=';')

        if not isinstance(cached_data, pd.DataFrame) or cached_data.empty:
            return None

        local_index_column = self.index_column if self.index_column else 'date'
        local_numeric_columns = self.numeric_columns if isinstance(
            self.numeric_columns, list) else list()

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
        # Filter by dates
        start = parse_any_date(start)
        end = parse_any_date(end)
        return self.get_filtered_by_dates(start, end)

    def to_backtrade_feed(self, start: Union[str, date, datetime, None] = None, end: Union[str, date, datetime, None] = None) -> bt.feeds.PandasData:
        local_dataframe = self.to_dataframe(start, end)

        return bt.feeds.PandasData(
            dataname=local_dataframe,
            # datetime=list(ticker_data.columns).index("Date"),
            high=None,
            low=None,
            open=list(local_dataframe.columns).index("close"),
            close=list(local_dataframe.columns).index("close"),
            volume=None,
            openinterest=None,
        )

    def fill_the_gaps(self, start: datetime = None, end: datetime = None) -> DataSourceBase:
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
        min = start if start is not None else self.dataframe.index.min()
        max = end if end is not None else self.dataframe.index.max()

        return self.dataframe[(self.dataframe.index >= min) & (self.dataframe.index <= max)]

    def get_value_start_end(self, start: Union[str, date, datetime, None] = None, end: Union[str, date, datetime, None] = None, column_name: str = 'close') -> Tuple(float):
        # Get start index
        start_index = parse_any_date(start)
        if not start_index:
            start_index = self.dataframe.index.min()

        # Get end index
        end_index = parse_any_date(end)
        if not end_index:
            end_index = self.dataframe.index.max()

        rwa_serie_start = self.dataframe[self.dataframe.index ==
                                         pd.to_datetime(start_index)]
        rwa_serie_end = self.dataframe[self.dataframe.index == pd.to_datetime(
            end_index)]
        return (float(rwa_serie_start[column_name]), float(rwa_serie_end[column_name]))

    @classmethod
    def reindex_dataframes(cls, data1: pd.DataFrame, data2: pd.DataFrame, date_column_name: str = 'Date', start_date: Union[str, date, datetime, None] = None, end_date: Union[str, date, datetime, None] = None) -> pd.DataFrame:
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
        start_date = parse_any_date(start_date, None)
        end_date = parse_any_date(end_date, None)
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

        # print('dt1: \n', dt1.tail(50))
        # print('dt2: \n', dt2.tail(50))
        # return

        return dt1, dt2

    # fill missing dates in dataframe and return dataframe object
    # tested on only YYYY-MM-DD format
    # ds=fill_in_missing_dates(ds,date_col_name='Date')
    # ds= dataframe object
    # date_col_name= col name in your dataframe, has datevalue
    # Source: https://github.com/n-idhisharma/mywork/blob/09942f15f6859e94e5dbb9fcb1af05ac7f627b06/Py_filling_missing_dates

    @classmethod
    def fillin_dataframe(cls, data: pd.DataFrame, date_col_name='Date', fill_val=np.nan, date_format='%Y-%m-%d'):
        df = data.set_index(date_col_name, drop=True)
        df.index = pd.to_datetime(df.index, format=date_format)
        idx = pd.date_range(df.index.min(), df.index.max())
        # print('missing_dates are', idx.difference(df.index))
        df = df.reindex(idx, fill_value=fill_val)
        # print('missing_dates after fill',idx.difference(df.index))
        df[date_col_name] = df.index
        df.reset_index(drop=True, inplace=True)
        return df
