from __future__ import annotations
from typing import List, Tuple, Union
from traceback import format_exc
import pandas as pd
from datetime import datetime, date
from .alternative import get_fng_history
from .data_source_base import DataSourceBase
from ..utils import parse_any_date


class FngDataSource(DataSourceBase):
    cache_file_path = 'fng_1d_alternative.csv'
    index_column = 'date'
    numeric_columns = ['close']

    def fetch_data(self, start: Union[str, date, datetime, None] = None) -> Union[pd.DataFrame, None]:
        start = parse_any_date(start, datetime(2010, 1, 1))

        if (start.date() >= date.today()):
            return None

        data = None

        try:
            if (start):
                limit = (date.today() - start.date()).days + 1
                fng_response = get_fng_history(limit=limit)
            else:
                fng_response = get_fng_history(limit=0)

            data = pd.DataFrame(fng_response, columns=[
                'timestamp', 'value', 'value_classification'])

            if not isinstance(data, pd.DataFrame) or data.empty:
                return None

            data = data.rename(
                columns={'timestamp': 'date', 'value': 'close', 'value_classification': 'close_name'})

            # Convert column types and discard invalid data
            data['date'] = pd.to_datetime(data['date'].apply(
                lambda x: datetime.fromtimestamp(int(x)).date()))
            data['close'] = pd.to_numeric(
                data['close'], errors='raise')
            # Drop invalid rows
            data = data[data["close"] > 0]

            # Set index
            data = data.set_index('date', drop=True)

            # Remove non requested dates
            if (start):
                data = data[~(data.index < pd.to_datetime(start))]

            return data

        except Exception as e:
            print(f"Error fetching and parsing fng data... {format_exc()}")
            return None


