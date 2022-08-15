from binance.client import Client
from typing import Union
from traceback import format_exc
import pandas as pd
import numpy as np
import nasdaqdatalink
from datetime import datetime, date, timedelta
from .alternative import get_fng_history
from cryptowatsonindicators.utils import parse_any_date

NASDAQ_CSV_CACHE_PATH = 'btcusdt_1d_nasdaq.csv'
FNG_CSV_CACHE_PATH = 'fng_1d_alternative.csv'


def get_binance_ticker_market_price(binance_api_key: str, binance_secret_key: str, ticker_symbol: str = 'BTCUSDT'):
    client = Client(binance_api_key, binance_secret_key)

    if not binance_api_key or not binance_secret_key:
        client.API_URL = 'https://testnet.binance.vision/api'

    return client.get_symbol_ticker(symbol=ticker_symbol)


def get_binance_ticker_time_series(binance_api_key: str, binance_secret_key: str, ticker_symbol: str = 'BTCUSDT', days: int = 365, granularity: str = '1d') -> pd.DataFrame:
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


def get_nasdaq_ticker_time_series(start_date: Union[str, date, datetime, None] = None) -> Union[pd.DataFrame, None]:
    start_date = parse_any_date(start_date, datetime(2010, 1, 1))

    cached_data = None
    missing_data = None

    # Load cached csv data
    try:
        cached_data = pd.read_csv(NASDAQ_CSV_CACHE_PATH, sep=';')
        if isinstance(cached_data, pd.DataFrame):
            # Convert column types and discard invalid data
            cached_data['Date'] = pd.to_datetime(
                cached_data['Date'], format='%Y-%m-%d')
            cached_data['Value'] = pd.to_numeric(
                cached_data['Value'], errors='coerce')
            # Drop 0 or np values
            cached_data = cached_data[cached_data["Value"] > 0]

            try:
                last_date_cached = cached_data.iloc[-1]['Date'].date()
            except:
                # In case we want a day before start_date: start_date - timedelta(days=1)
                last_date_cached = None
    except Exception as e:
        print(f"Error reading csv file {NASDAQ_CSV_CACHE_PATH}: {repr(e)}")
        cached_data = None
        last_date_cached = None

    # Load missing data if needed (from Nasdaq. 50 free daily calls without keys)
    if (not last_date_cached or last_date_cached != date.today()):
        try:
            if (last_date_cached):
                query_start_date = last_date_cached + timedelta(days=1)
                nasdaq_response = nasdaqdatalink.get(
                    "BCHAIN/MKPRU", start_date=query_start_date)
            else:
                nasdaq_response = nasdaqdatalink.get("BCHAIN/MKPRU")
                
            # reset index to the default rather than DateIndex
            missing_data = pd.DataFrame(nasdaq_response).reset_index()

            # Convert column types and discard invalid data
            missing_data['Value'] = pd.to_numeric(
                missing_data['Value'], errors='raise')
            # Drop 0 or np values
            missing_data = missing_data[missing_data["Value"] > 0]

            if (len(missing_data) == 0):
                missing_data = None
        except Exception as e:
            print(f"Error fetching and parsing nasdaq data... {format_exc()}")
            missing_data = None

    if not isinstance(cached_data, pd.DataFrame) and not isinstance(missing_data, pd.DataFrame):
        return None

    # concatenate cached and missing data, save to csv and return filtered
    # .reset_index(drop=True)
    all_data = pd.concat([cached_data, missing_data])
    all_data.to_csv(NASDAQ_CSV_CACHE_PATH, sep=';',
                    date_format='%Y-%m-%d', index=False)

    return all_data[all_data['Date'] >= start_date].reset_index(drop=True)


def get_fng_time_series(start_date: Union[str, date, datetime, None] = None) -> Union[pd.DataFrame, None]:
    start_date = parse_any_date(start_date, datetime(2010, 1, 1))

    cached_data = None
    missing_data = None

    # Load cached data
    try:
        cached_data = pd.read_csv(FNG_CSV_CACHE_PATH, sep=';')
        if isinstance(cached_data, pd.DataFrame):
            # Convert column types and discard invalid data
            cached_data['Date'] = pd.to_datetime(
                cached_data['Date'], format='%Y-%m-%d')
            cached_data['Value'] = pd.to_numeric(
                cached_data['Value'], errors='coerce')
            # Drop 0 or np values
            cached_data = cached_data[cached_data["Value"] > 0]

            try:
                last_date_cached = cached_data.iloc[-1]['Date'].date()
            except:
                # In case we want a day before start_date: start_date - timedelta(days=1)
                last_date_cached = None
    except Exception as e:
        print(f"Error reading csv file {FNG_CSV_CACHE_PATH}: {repr(e)}")
        cached_data = None
        last_date_cached = None

    # Load missing data if needed
    if (not last_date_cached or last_date_cached != date.today()):
        try:
            if (last_date_cached):
                limit = abs(date.today() - last_date_cached).days
                fng_response = get_fng_history(limit=limit)
            else:
                fng_response = get_fng_history(limit=0)
                
            missing_data = pd.DataFrame(fng_response, columns=[
                                        'timestamp', 'value', 'value_classification'])  # .reset_index(drop=True)
            missing_data = missing_data.rename(
                columns={'timestamp': 'Date', 'value': 'Value', 'value_classification': 'ValueName'})

            # Convert column types and discard invalid data
            missing_data['Date'] = pd.to_datetime(missing_data['Date'].apply(lambda x: datetime.fromtimestamp(int(x)).date()))

            missing_data['Value'] = pd.to_numeric(
                missing_data['Value'], errors='raise')
            # Drop 0 or np values
            missing_data = missing_data[missing_data["Value"] > 0]
            # Remove rows already cached (duplicates)
            if (last_date_cached):
                missing_data = missing_data[~(missing_data["Date"] == pd.to_datetime(last_date_cached))]
            
            if (len(missing_data) == 0):
                missing_data = None
        except Exception as e:
            print(f"Error fetching and parsing fng data... {format_exc()}")
            missing_data = None

    if not isinstance(cached_data, pd.DataFrame) and not isinstance(missing_data, pd.DataFrame):
        return None

    # concatenate cached and missing data, save to csv and return filtered
    all_data = pd.concat([cached_data, missing_data]
                         )   # .reset_index(drop=True)
    all_data.to_csv(FNG_CSV_CACHE_PATH, sep=';',
                    date_format='%Y-%m-%d', index=False)

    return all_data[all_data['Date'] >= start_date].reset_index(drop=True)


def resample_time_series(dt1: pd.DataFrame, dt2: pd.DataFrame, date_column_name: str = 'Date', start_date: Union[str, date, datetime, None] = None, end_date: Union[str, date, datetime, None] = None) -> pd.DataFrame:
    # df = df.set_index('timestamp').resample('S').ffill().reset_index()

    # https://stackoverflow.com/a/69052477
    dt1.set_index(date_column_name, drop=True, inplace=True)
    dt2.set_index(date_column_name, drop=True, inplace=True)
    
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
def fill_in_missing_dates(df, date_col_name = 'Date', fill_val = np.nan, date_format='%Y-%m-%d'):
    df.set_index(date_col_name, drop=True, inplace=True)
    df.index = pd.to_datetime(df.index, format = date_format)
    idx = pd.date_range(df.index.min(), df.index.max())
    # print('missing_dates are', idx.difference(df.index))
    df = df.reindex(idx, fill_value = fill_val)
    # print('missing_dates after fill',idx.difference(df.index))
    df[date_col_name] = df.index
    df.reset_index(drop=True, inplace=True)
    return df
