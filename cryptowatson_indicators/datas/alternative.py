"""
Alternative.me API wrapper
"""
import requests
import time
import datetime
import typing
from typing import Union, Optional, List, Dict
Timestamp = Union[datetime.datetime, datetime.date, int, float]
requests.packages.urllib3.disable_warnings()

# API:
_URL_ALTERNATIVE_FNG = 'https://api.alternative.me/fng/?limit={}'


def _query_alternative(url: str, errorCheck: bool = True) -> Optional[Dict]:
    """
    Query the url and return the result or None on failure.
    :param url: the url
    :param errorCheck: run extra error checks (default: True)
    :returns: response, or nothing if errorCheck=True and the response contains errors
    """
    try:
        response = requests.get(url, verify=False).json()
    except Exception as e:
        print(f"[ERROR] Unexpected error calling Alternative API. {str(e)}")
        time.sleep(2)
        return None

    if errorCheck and (response.get('metadata', {}).get('error')):
        print(
            f"[ERROR] Call to Alternative API returned error: {str(response.get('metadata', {}).get('error'))}")
        return None

    return response


def _format_parameter(parameter: object) -> str:
    """
    Format the parameter depending on its type and return
    the string representation accepted by the API.
    :param parameter: parameter to format
    """
    if isinstance(parameter, list):
        return ','.join(parameter)

    else:
        return str(parameter)


def _format_timestamp(timestamp: Timestamp) -> int:
    """
    Format the timestamp depending on its type and return
    the integer representation accepted by the API.
    :param timestamp: timestamp to format
    """
    if isinstance(timestamp, datetime.datetime) or isinstance(timestamp, datetime.date):
        return int(time.mktime(timestamp.timetuple()))
    return int(timestamp)


###############################################################################
def get_fng_history(limit: int = 10) -> Union[List, None]:
    """
    Get last {limit} fear and greed indexes
    :returns: list of indexes
    """
    alternative_response = _query_alternative(
        _URL_ALTERNATIVE_FNG.format(_format_parameter(limit)))
    if alternative_response:
        fng_list = typing.cast(List, alternative_response['data'])
        fng_list.reverse()

        # for fng in fng_list:
        #     fng['datetime'] = datetime.datetime.utcfromtimestamp(int(fng['timestamp']))
        return fng_list

    return None


def get_fng_latest() -> Union[Dict, None]:
    """
    Get latest fear and greed indexes
    :returns: list of indexes
    """
    alternative_response = _query_alternative(
        _URL_ALTERNATIVE_FNG.format(_format_parameter(1)))
    if alternative_response:
        fng_list = typing.cast(List, alternative_response['data'])
        if (len(fng_list) > 0):
            return fng_list[0]

    return None
