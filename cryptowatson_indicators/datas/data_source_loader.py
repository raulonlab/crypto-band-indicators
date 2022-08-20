from __future__ import annotations
from typing import List, Tuple, Union
import pandas as pd
import backtrader as bt
from datetime import datetime, date
from cryptowatson_indicators.utils import parse_any_date


class DataSourceLoader:
    data_sources = dict()
    last_data_source_loaded = None
    last_source_loaded = None
    only_cache = False

    def add_data_source(self, data_source_class, source: str, **kvargs) -> DataSourceLoader:
        data_source = data_source_class(kvargs)

        # Register data and source
        self.last_data_source_loaded = data_source
        self.last_source_loaded = source
        self.data_sources[source] = data_source

        return self

    def to_dataframe(self, source: str = None, start: Union[str, date, datetime, None] = None, end: Union[str, date, datetime, None] = None) -> pd.DataFrame:
        if not source and self.last_data_source_loaded:
            return self.last_data_source_loaded.to_dataframe(start, end)
        elif source:
            return self.data_sources[source].to_dataframe(start, end)

        return None

    def to_dataframes(self, start: Union[str, date, datetime, None] = None, end: Union[str, date, datetime, None] = None) -> List(pd.DataFrame):
        local_data_sources = []
        for data_source in list(self.data_sources.values()):
            # Append filtered by dates
            local_data_sources.append(data_source.to_dataframe(start, end))

        return local_data_sources

    def to_backtrade_feed(self, label: str = None, start: Union[str, date, datetime, None] = None, end: Union[str, date, datetime, None] = None) -> bt.feeds.PandasData:
        df = self.to_dataframe(label, start, end)

        return bt.feeds.PandasData(
            dataname=df,
            # datetime=list(ticker_data.columns).index("Date"),
            high=None,
            low=None,
            # uses the column 1 ('Value') as open price
            open=list(df.columns).index("close"),
            # uses the column 1 ('Value') as close price
            close=list(df.columns).index("close"),
            volume=None,
            openinterest=None,
        )

    def to_backtrade_feeds(self, start: Union[str, date, datetime, None] = None, end: Union[str, date, datetime, None] = None) -> List(bt.feeds.PandasData):
        df_list = self.to_dataframes(start, end)

        backtrade_feeds = list()
        for df in df_list:
            backtrade_feeds.append(bt.feeds.PandasData(
                dataname=df,
                # datetime=list(ticker_data.columns).index("Date"),
                high=None,
                low=None,
                # uses the column 1 ('Value') as open price
                open=list(df.columns).index("close"),
                # uses the column 1 ('Value') as close price
                close=list(df.columns).index("close"),
                volume=None,
                openinterest=None,
            ))

        return backtrade_feeds

    def get_value_start_end(self, label: str = None, start: Union[str, date, datetime, None] = None, end: Union[str, date, datetime, None] = None, column_name: str = 'close') -> Tuple(float):
        if not label:
            dataframe = self.last_data_source_loaded
        else:
            dataframe = self.data_sources[label].dataframe

        # Get start index
        start_index = parse_any_date(start)
        if not start_index:
            start_index = dataframe.index.min()

        # Get end index
        end_index = parse_any_date(end)
        if not end_index:
            end_index = dataframe.index.max()

        rwa_serie_start = dataframe[dataframe.index ==
                                    pd.to_datetime(start_index)]
        rwa_serie_end = dataframe[dataframe.index == pd.to_datetime(end_index)]
        return (float(rwa_serie_start[column_name]), float(rwa_serie_end[column_name]))
