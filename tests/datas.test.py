import backtrader as bt
from cryptowatsonindicators import datas
import pprint
pprint = pprint.PrettyPrinter(
    indent=2, sort_dicts=False, compact=False).pprint   # pprint with defaults

def test():
    # dataframe = datas.DataLoader(start = '01/08/2022', end = '16/08/2022').load_data('ticker_nasdaq').to_dataframe()
    # print('ticker_nasdaq data:')
    # print(dataframe.to_string())

    # dataframe = datas.DataLoader(start = '01/08/2022', end = '16/08/2022').load_data('fng').to_dataframe()
    # print('fng data:')
    # print(dataframe.to_string())

    dataframes = datas.DataLoader(start = '01/08/2022', end = '16/08/2022') \
        .load_data('ticker_nasdaq') \
        .load_data('fng') \
        .to_dataframes()

    for dataframe in dataframes:
        print(dataframe.to_string())
        print('------------------------')

if __name__ == '__main__':
    test()
