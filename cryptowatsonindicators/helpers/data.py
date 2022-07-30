from binance.client import Client
# from binance.exceptions import BinanceAPIException, BinanceOrderException
import pandas as pd
import nasdaqdatalink
from datetime import datetime, date, timedelta

NASDAQ_CSV_CACHE_PATH = 'btcusdt_1d_nasdaq.csv'

def get_binance_ticker_market_price(binance_api_key:str, binance_secret_key:str, ticker_symbol: str = 'BTCUSDT'):
    client = Client(binance_api_key, binance_secret_key)

    if not binance_api_key or not binance_secret_key:
        client.API_URL = 'https://testnet.binance.vision/api'
    
    return client.get_symbol_ticker(symbol=ticker_symbol)

def get_binance_ticker_time_series(binance_api_key:str, binance_secret_key:str, ticker_symbol: str = 'BTCUSDT', days: int = 365, granularity:str = '1d'):
    """
    Gets ticker price of a specific coin pair
    """
    client = Client(binance_api_key, binance_secret_key)

    if not binance_api_key or not binance_secret_key:
        client.API_URL = 'https://testnet.binance.vision/api'

    target_date = (datetime.now() - timedelta(days = days)).strftime("%d %b %Y %H:%M:%S")
    key = f"{ticker_symbol}"
    end_date = datetime.now() 
    end_date = end_date.strftime("%d %b %Y %H:%M:%S")
    
    coindata = pd.DataFrame(columns = [key])

    prices = []
    dates = []
    for result in client.get_historical_klines(
        ticker_symbol, granularity, target_date, end_date, limit=1000
        ):
        date = datetime.utcfromtimestamp(result[0] / 1000).strftime("%d %b %Y %H:%M:%S")
        price = float(result[1])
        dates.append(date)
        prices.append(price)

    coindata[key] = prices
    coindata['date'] = dates

    return(coindata.reindex(columns =['date', key]))


def get_nasdaq_ticker_time_series():
    # Load cached csv data
    csv_data = None
    missing_start_date = None
    try:
        csv_data = pd.read_csv(NASDAQ_CSV_CACHE_PATH, sep = ';')
        if isinstance(csv_data, pd.DataFrame):
            csv_data['Date'] = pd.to_datetime(csv_data['Date'], format='%Y-%m-%d')
            # last_date = datetime.strptime(csv_data.iloc[-1,0], '%Y-%m-%d').date()
            last_date = pd.to_datetime(csv_data.iloc[-1]['Date'], format='%Y-%m-%d').date()
            # print('type(last_date): ', type(last_date))
            # print('last_date: ', last_date)
            # print('date.today(): ', date.today())

            if (last_date == date.today()):
                return csv_data

            missing_start_date = last_date + timedelta(days=1)
            # print('missing_start_date: ', missing_start_date)
    except Exception as e:
        print(f"Error reading csv file {NASDAQ_CSV_CACHE_PATH}: {e}")
        csv_data = None

    # Fech data from https://data.nasdaq.com/. 50 free API calls per day without keys and unlimited with keys (free with a signed up account).
    if (missing_start_date):
        nasdaq_response = nasdaqdatalink.get("BCHAIN/MKPRU", start_date=missing_start_date)
    else:
        nasdaq_response = nasdaqdatalink.get("BCHAIN/MKPRU")
    
    missing_data =  pd.DataFrame(nasdaq_response).reset_index()
    missing_data['Date'] = pd.to_datetime(missing_data['Date']) # Ensure that the date is in datetime or graphs might look funny
    missing_data = missing_data[missing_data["Value"] > 0] # Drop all 0 values as they will fuck up the regression bands

    all_data = pd.concat([csv_data, missing_data])
    all_data.to_csv(NASDAQ_CSV_CACHE_PATH, sep = ';', index=False)
    return all_data
