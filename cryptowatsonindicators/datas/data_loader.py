from __future__ import annotations
from binance.client import Client
from typing import List, Tuple, Union
from traceback import format_exc
import pandas as pd
import numpy as np
import nasdaqdatalink
import backtrader as bt
from datetime import datetime, date, timedelta
from .alternative import get_fng_history
from cryptowatsonindicators.utils import parse_any_date

nasdaqdatalink.ApiConfig.verify_ssl = False

NASDAQ_CSV_CACHE_PATH = 'btcusdt_1d_nasdaq.csv'
FNG_CSV_CACHE_PATH = 'fng_1d_alternative.csv'
RAINBOW_CSV_CACHE_PATH = 'rainbow_1d_nasdaq.csv'
DEFAULT_CSV_CACHE_PATH = 'default_1d.csv'

# DATA_SOURCES = ['ticker_nasdaq', 'fng', 'rainbow']

SOURCE_INFO = {
    'ticker_nasdaq': {'cache_path': 'btcusdt_1d_nasdaq.csv', 'index_column': 'date', 'numeric_columns': ['close'], 'text_columns': []},
    'fng': {'cache_path': 'fng_1d_alternative.csv', 'index_column': 'date', 'numeric_columns': ['close'], 'text_columns': ['close_name']},
}

class DataFrameWrapper:
    def __init__(self, source: str, dataframe: pd.DataFrame):
        self.source = source
        self.dataframe = dataframe

class DataLoader:
    dataframes = dict()
    last_dataframe_loaded = None
    last_source_loaded = None
    start = None
    end = None
    ticker_symbol = 'BTCUSDT'
    binance_api_key = None
    binance_secret_key = None
    only_cache = False

    def __init__(self, start: Union[str, date, datetime, None] = None, end: Union[str, date, datetime, None] = None, ticker_symbol: str = 'BTCUSDT', binance_api_key: str = None, binance_secret_key: str = None):
        self.ticker_symbol = ticker_symbol
        self.start = parse_any_date(start, datetime(2010, 1, 1))
        self.end = parse_any_date(end, None)
        self.binance_api_key = binance_api_key
        self.binance_secret_key = binance_secret_key

    
    def load_data(self, source: str, label: str = None) -> DataLoader:
        # source_info = SOURCE_INFO[source]

        if not label:
            label = source

        # Load cache
        cached_data = None
        missing_data = None
        missing_start_date = None

        # Load cached csv data
        # try:
        cached_data = DataLoader.read_cache(source)
        last_date_cached = cached_data.index.max() if isinstance(cached_data, pd.DataFrame) else None
        if last_date_cached:
            missing_start_date = last_date_cached.date() + timedelta(days=1)
    
        # except Exception as e:
            # print(f"[warn] Error loading csv cache file: {NASDAQ_CSV_CACHE_PATH}: {repr(e)}")
            # cached_data = None

        # Fetch API data
        if not self.only_cache:
            if (source == 'ticker_nasdaq'):
                missing_data = DataLoader.get_nasdaq_ticker_time_series(start = missing_start_date)
            # elif (source == 'ticker/binance'):
            #     self.dataframe = DataLoader.get_binance_ticker_time_series()
            elif (source == 'fng'):
                missing_data = DataLoader.get_fng_time_series(start = missing_start_date)
            elif (source == 'rainbow'):
                missing_data = DataLoader.get_nasdaq_ticker_time_series(start = missing_start_date)
        
        # Validate data
        if not isinstance(cached_data, pd.DataFrame) and not isinstance(missing_data, pd.DataFrame):
            self.dataframe = None
            return
        
        # Concatenate data
        all_data = pd.concat([cached_data, missing_data])
        DataLoader.write_cache(all_data, source)

        if (all_data is None or all_data.empty):
            error_message = f"DataLoader: No data available in source {source}"
            print(f"WARNING: {error_message}")
            return
        
        # Filter data
        all_data = all_data[all_data.index >= self.start]

        # Reindex data
        all_data = DataLoader.reindex(all_data, self.start, self.end)
        
        # Register data and source
        self.last_dataframe_loaded = all_data
        self.last_dataframe_loaded.name = source
        self.last_source_loaded = source
        self.dataframes[label] = DataFrameWrapper(source=source, dataframe=all_data)
        
        return self


    def to_dataframe(self, label: str = None) -> pd.DataFrame:
        if not label:
            return self.last_dataframe_loaded
        else:
            return self.dataframes[label].dataframe
    
    def to_dataframes(self) -> List(pd.DataFrame):
        dataframes = []
        for dataframe_wrapper in list(self.dataframes.values()):
            dataframes.append(dataframe_wrapper.dataframe)
        
        return dataframes

    def to_backtrade_feed(self, label: str = None) -> bt.feeds.PandasData:
        if not label:
            dataframe = self.last_dataframe_loaded
        else:
            dataframe = self.dataframes[label].dataframe
    
        return bt.feeds.PandasData(
            dataname=dataframe,
            # datetime=list(ticker_data.columns).index("Date"),
            high=None,
            low=None,
            open=list(dataframe.columns).index("close"),     # uses the column 1 ('Value') as open price
            close=list(dataframe.columns).index("close"),    # uses the column 1 ('Value') as close price
            volume=None,
            openinterest=None,
        )

    def to_backtrade_feeds(self) -> List(bt.feeds.PandasData):
        backtrade_feeds = list()
        for dataframe_wrapper in list(self.dataframes.values()):
            backtrade_feeds.append(bt.feeds.PandasData(
                dataname=dataframe_wrapper.dataframe,
                # datetime=list(ticker_data.columns).index("Date"),
                high=None,
                low=None,
                open=list(dataframe_wrapper.dataframe.columns).index("close"),     # uses the column 1 ('Value') as open price
                close=list(dataframe_wrapper.dataframe.columns).index("close"),    # uses the column 1 ('Value') as close price
                volume=None,
                openinterest=None,
            ))
        
        return backtrade_feeds


    def get_value_start_end(self, label: str = None, column_name: str = 'close') -> Tuple(float):
        if not label:
            dataframe = self.last_dataframe_loaded
        else:
            dataframe = self.dataframes[label].dataframe
        
        return (float(dataframe.iloc[0][column_name]), float(dataframe.iloc[-1][column_name]))


    @classmethod
    def reindex(cls, dataframe: pd.DataFrame, start: datetime, end: datetime) -> pd.DataFrame:
        # Git min and max index
        min = dataframe.index.min()
        max = dataframe.index.max()

        # Filter index range
        if start is not None:
            min = start if start > min else min
        if end is not None:
            max = end if end < max else max
        
        all_dates_range = pd.date_range(min, max)   # start=min, end=max, freq="D"
        # print('missing_dates in dataframe: ', all_dates_range.difference(dataframe.index))

        return dataframe.reindex(all_dates_range, fill_value = np.nan).interpolate()


    @classmethod
    def get_binance_ticker_market_price(cls, ticker_symbol: str = 'BTCUSDT', binance_api_key: str = None, binance_secret_key: str = None):
        client = Client(binance_api_key, binance_secret_key)

        if not binance_api_key or not binance_secret_key:
            client.API_URL = 'https://testnet.binance.vision/api'

        return client.get_symbol_ticker(symbol=ticker_symbol)


    @classmethod
    def get_binance_ticker_time_series(csl, ticker_symbol: str = 'BTCUSDT', binance_api_key: str = None, binance_secret_key: str = None, days: int = 365, granularity: str = '1d') -> pd.DataFrame:
        """
        Gets ticker price of a specific coin pair
        """
        client = Client(binance_api_key, binance_secret_key)

        if not binance_api_key or not binance_secret_key:
            client.API_URL = 'https://testnet.binance.vision/api'

        target_date = (datetime.now() - timedelta(days=days)
                    ).strftime("%d %b %Y %H:%M:%S")
        key = f"{ticker_symbol}"
        end_date = datetime.now()
        end_date = end_date.strftime("%d %b %Y %H:%M:%S")

        coindata = pd.DataFrame(columns=[key])

        prices = []
        dates = []
        for result in client.get_historical_klines(
            ticker_symbol, granularity, target_date, end_date, limit=1000
        ):
            date = datetime.utcfromtimestamp(
                result[0] / 1000).strftime("%d %b %Y %H:%M:%S")
            price = float(result[1])
            dates.append(date)
            prices.append(price)

        coindata[key] = prices
        coindata['date'] = dates

        return(coindata.reindex(columns=['date', key]))


    @classmethod
    def get_nasdaq_ticker_time_series(cls, start: Union[str, date, datetime, None] = None) -> Union[pd.DataFrame, None]:
        start = parse_any_date(start, datetime(2010, 1, 1))

        if (start.date() > date.today()):
            return None

        data = None

        try:
            if (start):
                nasdaq_response = nasdaqdatalink.get(
                    "BCHAIN/MKPRU", start_date=start)
            else:
                nasdaq_response = nasdaqdatalink.get("BCHAIN/MKPRU")
                
            data = pd.DataFrame(nasdaq_response)

            if not isinstance(data, pd.DataFrame) or data.empty:
                return None
 
            data = data.rename(columns={'Value': 'close'})
            data.index.name = 'date'
            # data['date'] = pd.to_datetime(data['date'], format='%Y-%m-%d')

            # Convert column types and discard invalid data
            data['close'] = pd.to_numeric(
                data['close'], errors='coerce')
            # Drop 0 or np values
            data = data[data["close"] > 0]

            # Remove rows already cached (duplicates)
            if (start):
                data = data[~(data.index < pd.to_datetime(start))]
            
            return data

        except Exception as e:
            print(f"Error fetching and parsing nasdaq data... {format_exc()}")
            return


    @classmethod
    def get_fng_time_series(cls, start: Union[str, date, datetime, None] = None) -> Union[pd.DataFrame, None]:
        start = parse_any_date(start, datetime(2010, 1, 1))

        if (start.date() > date.today()):
            return None

        data = None

        try:
            if (start):
                limit = (date.today() - start.date()).days + 1
                fng_response = get_fng_history(limit=limit)
            else:
                fng_response = get_fng_history(limit=0)
                
            data = pd.DataFrame(fng_response, columns=[
                                        'timestamp', 'value', 'value_classification'])  # .reset_index(drop=True)
            
            if not isinstance(data, pd.DataFrame) or data.empty:
                return None

            data = data.rename(
                columns={'timestamp': 'date', 'value': 'close', 'value_classification': 'close_name'})

            # Convert column types and discard invalid data
            data['date'] = pd.to_datetime(data['date'].apply(lambda x: datetime.fromtimestamp(int(x)).date()))
            data['close'] = pd.to_numeric(
                data['close'], errors='raise')
            # Drop 0 or np values
            data = data[data["close"] > 0]

            # Set index
            data = data.set_index('date', drop=True)

            # Remove rows already cached (duplicates)
            if (start):
                data = data[~(data.index < pd.to_datetime(start))]
            
            return data

        except Exception as e:
            print(f"Error fetching and parsing fng data... {format_exc()}")
            return None


    @classmethod
    def write_cache(self, df: pd.DataFrame, source: str) -> None:
        df.to_csv(SOURCE_INFO[source]['cache_path'], sep=';', date_format='%Y-%m-%d', index=True, index_label='date')


    @classmethod
    def read_cache(self, source: str) -> Union[pd.DataFrame, None]:
        source_info = SOURCE_INFO[source]
        cached_data = pd.read_csv(source_info['cache_path'], sep=';')

        if not isinstance(cached_data, pd.DataFrame) or cached_data.empty:
            return None

        # Convert column types and discard invalid data
        cached_data[source_info['index_column']] = pd.to_datetime(
            cached_data[source_info['index_column']], format='%Y-%m-%d')

        for numeric_column in source_info['numeric_columns']:
            cached_data[numeric_column] = pd.to_numeric(cached_data[numeric_column], errors='coerce')
            # Drop 0, np values
            # cached_data = cached_data[cached_data[numeric_column] > 0]
        
        # Set index
        cached_data.set_index(source_info['index_column'], drop=True, inplace=True)
        
        return cached_data


    @classmethod
    def reindex_dataframes(cls, data1: pd.DataFrame, data2: pd.DataFrame, date_column_name: str = 'Date', start_date: Union[str, date, datetime, None] = None, end_date: Union[str, date, datetime, None] = None) -> pd.DataFrame:
        # df = df.set_index('timestamp').resample('S').ffill().reset_index()

        # https://stackoverflow.com/a/69052477
        dt1 = data1.set_index(date_column_name, drop=True)
        dt2 = data2.set_index(date_column_name, drop=True)
        
        # Git min and max across the 2 dataframes
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
        
        all_dates_range = pd.date_range(min, max)   # start=min, end=max, freq="D"
        # print('missing_dates in dt1: ', all_dates_range.difference(dt1.index))
        # print('missing_dates in dt2: ', all_dates_range.difference(dt2.index))
        # print('\n')
        # print('all_dates_range: ', all_dates_range)

        dt1 = dt1.reindex(all_dates_range, fill_value = np.nan).interpolate()
        dt2 = dt2.reindex(all_dates_range, fill_value = np.nan).interpolate()

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
    def fillin_dataframe(cls, data: pd.DataFrame, date_col_name = 'Date', fill_val = np.nan, date_format='%Y-%m-%d'):
        df = data.set_index(date_col_name, drop=True)
        df.index = pd.to_datetime(df.index, format = date_format)
        idx = pd.date_range(df.index.min(), df.index.max())
        # print('missing_dates are', idx.difference(df.index))
        df = df.reindex(idx, fill_value = fill_val)
        # print('missing_dates after fill',idx.difference(df.index))
        df[date_col_name] = df.index
        df.reset_index(drop=True, inplace=True)
        return df
