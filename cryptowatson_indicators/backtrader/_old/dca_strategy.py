from datetime import timedelta
from cryptowatson_indicators import utils
from .base_strategy import WeightedAverageStrategy_old


class DCAStrategy(WeightedAverageStrategy_old):
    params = dict(
        weighted_multipliers=[1],  # Override with a weight multiplier of 1
    )

    def __init__(self):
        super().__init__()

        self.price = self.data.close

    def __str__(self):
        return 'DCA'

    def next(self):
        # An order is pending ... nothing can be done
        if self.order:
            self.debug(f"  ...skip: order in progress")
            return

        # Only buy every min_order_period days
        last_bar_executed_ago = self.get_last_bar_executed_ago()
        if last_bar_executed_ago is not None and (self.data.datetime.date() - self.data.datetime.date(last_bar_executed_ago) < timedelta(self.params.min_order_period)):
            self.debug(f"  ...skip: still to soon to buy")
            return

        buy_dol_size = self.params.base_buy_amount
        buy_btc_size = buy_dol_size / self.price[0]
        self.log(
            f"{utils.Emojis.BUY} BUY {buy_btc_size:.6f} BTC = {buy_dol_size:.2f} USD, 1 BTC = {self.price[0]:.2f} USD", log_color=utils.LogColors.BOLDBUY)

        # Keep track of the created order to avoid a 2nd order
        self.order = self.buy(size=buy_btc_size)

    def plot(self):
        pass
