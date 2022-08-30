# <AUTOGEN_INIT>
from .base_strategy import (CheatOnOpenCryptoStrategy, CryptoStrategy,)
from .dca_strategy import (DCAStrategy,)
from .hodl_strategy import (HodlStrategy,)
from .indicator_wrappers import (BandIndicatorWrapper, BandIndicatorWrapperOld,
                                 FngBandIndicatorWrapper,
                                 RainbowBandIndicatorWrapper,)
from .rebalance_strategy import (RebalanceStrategy,)
from .weighted_dca_strategy import (WeightedDCAStrategy,)

__all__ = ['BandIndicatorWrapper', 'BandIndicatorWrapperOld',
           'CheatOnOpenCryptoStrategy', 'CryptoStrategy', 'DCAStrategy',
           'FngBandIndicatorWrapper', 'HodlStrategy',
           'RainbowBandIndicatorWrapper', 'RebalanceStrategy',
           'WeightedDCAStrategy']
# </AUTOGEN_INIT>
