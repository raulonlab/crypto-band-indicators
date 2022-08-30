from __future__ import annotations
from binance.client import Client
from typing import List, Tuple, Union
from traceback import format_exc
import pandas as pd
import nasdaqdatalink
from datetime import datetime, date, timedelta
from .data_source_base import DataSourceBase
from cryptowatson_indicators.utils import parse_any_date
nasdaqdatalink.ApiConfig.verify_ssl = False
from functools import lru_cache

@lru_cache
def _fetch_data_cached(start: Union[str, date, datetime, None] = None) -> Union[pd.DataFrame, None]:
    start = parse_any_date(start, datetime(2010, 1, 1))

    if (start.date() >= date.today()):
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


class TickerDataSource(DataSourceBase):
    def __init__(self, *vargs, ** kvargs):
        self.cache_file_path = 'btcusdt_1d_nasdaq.csv'
        self.index_column = 'date'
        self.numeric_columns = ['close']
        self.text_columns = []
        super().__init__(*vargs, ** kvargs)

    
    def fetch_data(self, *args, **kwargs) -> Union[pd.DataFrame, None]:
        return _fetch_data_cached(*args, **kwargs)
        

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

        return (coindata.reindex(columns=['date', key]))
