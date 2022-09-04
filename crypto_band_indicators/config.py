import os
from distutils.util import strtobool
from dotenv import load_dotenv
load_dotenv(verbose=True)

DISABLE_FETCH = 'disable_fetch'
ONLY_CACHE = 'only_cache'
ENABLE_BACKTRADER_LOG = 'enable_backtrader_log'
ENABLE_BACKTRADER_DEBUG = 'enable_backtrader_debug'

__conf = {
    DISABLE_FETCH: strtobool(os.environ.get('DISABLE_FETCH', '0')),
    ONLY_CACHE: strtobool(os.environ.get('ONLY_CACHE', '0')),
    ENABLE_BACKTRADER_LOG: strtobool(os.environ.get('ENABLE_BACKTRADER_LOG', '0')),
    ENABLE_BACKTRADER_DEBUG: strtobool(os.environ.get('ENABLE_BACKTRADER_DEBUG', '0')),
}

def get(name, default = None):
    global __confg
    return __conf[name] if name in __conf else default

def set(name, value):
    if name in __conf.keys():
        __conf[name] = value
    else:
        raise NameError(f"Parameter '{name}' not available in config")
