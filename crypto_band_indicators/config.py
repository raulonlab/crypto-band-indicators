import os
from distutils.util import strtobool
from dotenv import load_dotenv
load_dotenv(verbose=True)

__conf = {
    "disable_fetch": strtobool(os.environ.get('DISABLE_FETCH', '0')),
    "only_cache": strtobool(os.environ.get('ONLY_CACHE', '0')),
}

def get(name, default = None):
    global __confg
    return __conf[name] if name in __conf else default

def set(name, value):
    if name in __conf.keys():
        __conf[name] = value
    else:
        raise NameError(f"Parameter '{name}' not available in config")
