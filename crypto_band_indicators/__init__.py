# The following `__init__.py` variables modify autogeneration behavior:

#             `__submodules__` (List[str] | Dict[str, List[str])) -
#                 Indicates the list of submodules to be introspected, if
#                 unspecified all submodules are introspected. Can be a list
#                 of submodule names, or a dictionary mapping each submodule name
#                 to a list of attribute names to expose. If the value is None,
#                 then all attributes are exposed (or __all__) is respected).

#             `__external__` - Specify external modules to expose the attributes of.

#             `__explicit__` - Add custom explicitly defined names to this, and
#                 they will be automatically added to the __all__ variable.

#             `__protected__` -  Protected modules are exposed, but their attributes are not.

#             `__private__` - Private modules and their attributes are not exposed.

#             `__ignore__` - Tells mkinit to ignore particular attributes

__protected__ = ['utils', 'config']

# <AUTOGEN_INIT>
from crypto_band_indicators import backtrader
from crypto_band_indicators import config
from crypto_band_indicators import datas
from crypto_band_indicators import indicators
from crypto_band_indicators import utils

from crypto_band_indicators.backtrader import (BandIndicatorWrapper,
                                               CheatOnOpenCryptoStrategy,
                                               CryptoStrategy, DCAStrategy,
                                               HodlStrategy, RebalanceStrategy,
                                               WeightedDCAStrategy,)
from crypto_band_indicators.datas import (DataSourceBase, FngDataSource,
                                          PandasDataFactory, TickerDataSource,)
from crypto_band_indicators.indicators import (BandDetails, BandIndicatorBase,
                                               FngBandIndicator,
                                               RainbowBandIndicator,)

__all__ = ['BandDetails', 'BandIndicatorBase', 'BandIndicatorWrapper',
           'CheatOnOpenCryptoStrategy', 'CryptoStrategy', 'DCAStrategy',
           'DataSourceBase', 'FngBandIndicator', 'FngDataSource',
           'HodlStrategy', 'PandasDataFactory', 'RainbowBandIndicator',
           'RebalanceStrategy', 'TickerDataSource', 'WeightedDCAStrategy',
           'backtrader', 'config', 'datas', 'indicators', 'utils']
# </AUTOGEN_INIT>
