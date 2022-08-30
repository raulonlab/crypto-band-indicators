from cryptowatson_indicators import utils
from .base_strategy import RebalanceStrategy_old


class HodlStrategy(RebalanceStrategy_old):

    def __str__(self):
        return 'HODL'

    def nextstart(self):
        self.log(
            f"R REBALANCE to 100% and HODL!", log_color=utils.LogColors.BOLDSTRATEGY)
        self.rebalance(100)

    def plot(self):
        pass
