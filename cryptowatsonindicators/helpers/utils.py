from typing import Union
from datetime import datetime, date, time

def parse_any_date(date_any: Union[str, date, None] = None, default_date: any = None) -> Union[datetime, any]:
    # parse and return date_any
    if date_any is None:
        return default_date
    elif isinstance(date_any, str):
        try:
            return datetime.strptime(date_any, '%d/%m/%Y')
        except:
            print(f"[warn] parse_date: invalid date {date_any} doesn't look like '%d/%m/%Y'")
    elif isinstance(date_any, date):
        return datetime.combine(date_any, time(0, 0, 0))
    
    # parse and return default_date
    if isinstance(default_date, str):
        try:
            return datetime.strptime(default_date, '%d/%m/%Y')
        except:
            print(f"[warn] parse_date: invalid default_date {default_date} doesn't look like '%d/%m/%Y'")
    elif isinstance(default_date, date):
        return datetime.combine(default_date, time(0, 0, 0))

    return default_date
