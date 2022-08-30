# cryptowatson-indicators

Implementation of crypto trading indicators and strategies based on the indexes `Fear and Greed` and `Rainbow Price`.

Also includes simulators (backtests) of the strategies in Jupyter notebooks (using [backtrader](https://www.backtrader.com/)):

- Fear and Greed simulator [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/raultruco/cryptowatson-indicators/blob/main/simulators/fng_simulator.ipynb)

- Rainbow simulator [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/raultruco/cryptowatson-indicators/blob/main/simulators/rwa_simulator.ipynb)

## Indicators

### Rainbow Chart

The Rainbow Chart is a long-term valuation tool for Bitcoin. It uses a logarithmic growth curve to forecast the potential future price direction of Bitcoin.

It overlays rainbow color bands on top of the logarithmic growth curve channel in an attempt to highlight market sentiment at each rainbow color stage as price moves through it. Therefore highlighting potential opportunities to buy or sell.

See a live version for Bitcoin in [lookintobitcoin](https://www.lookintobitcoin.com/charts/bitcoin-rainbow-chart/) or [blockchaincenter](https://www.blockchaincenter.net/en/bitcoin-rainbow-chart/)

And for Ethereum in [blockchaincenter](https://www.blockchaincenter.net/ethereum-rainbow-chart/)

The Rainbow Chart is divided in 9 bands. being the 1st the worst to buy (expensive), and the 9th the best (cheap):

1. Maximum bubble!!
2. Sell, seriouly sell!
3. FOMO intensifies
4. Is this a bubble?
5. HODL
6. Still cheap
7. Accumulate
8. Buy!
9. Fire sale!!

### Fear and Greed

The Fear and Greed Index is a tool that helps investors and traders analyze the Bitcoin and Crypto market from a sentiment perspective. It identifies the extent to which the market is becoming overly fearful or overly greedy. Hence why it is called the Fear and Greed Index.

- See the live version for Bitcoin in [lookintobitcoin](https://www.lookintobitcoin.com/charts/bitcoin-fear-and-greed-index/)

The Fear and Greed index has a value in the range (0, 100) and is divided in 5 bands, being the 1st the best to buy (Fear), and the 5th the worst (Greed):

1. ( 0-25):  Extreme Fear
2. (26-46):  Fear
3. (47-54):  Neutral
4. (55-75):  Greed
5. (76-100): Extreme Greed

## Strategies

### Weighted Averaging DCA

Variation of the traditional Dollar Cost Average (DCA) method of investing that takes into account the current indicator index. The better index, the bigger the amount of BTC purchased.

The idea of applying this strategy with the Rainbow index comes from [this post in Reddit by the user u/pseudoHappyHippy](https://www.reddit.com/r/CryptoCurrency/comments/qg9s6v/introducing_rainbowweighted_averaging_a_more/). The author claims that RWA (Rainbow Weighted Averaging) outperforms DCA 96.8% of the time by an average of 35.3% greater returns when applied to historical BTC price data.

#### Parameters

- **base_buy_amount**: Amount base to buy, as in standard DCA
- **weighted_multipliers**: Amount multipliers (weighted) for each band. Ex: [1.5, 1.25, 1, 0.75, 0.5]
- **min_order_period**: Interval of days between periodical orders. Ex: 5

### Rebalance 

Applies a rebalance percentage of the position between BTC and USDT depending on the indicator index. The better index, the more percentage of BTC against USDT is kept in the wallet over the total value in USDT.

#### Parameters
- **rebalance_percents**: Rebalance percentages of BTC over USDT for each band. Ex: [85, 65, 50, 15, 10]
- **min_order_period**: Minimum interval of days between consecutive orders. Ex: 5

## Simulators

The simulators are available as Jupyter notebooks in Google Collab:

- [Open Fear and Greed simulator in Colab](https://colab.research.google.com/github/raultruco/cryptowatson-indicators/blob/main/simulators/fng_simulator.ipynb)

- [Open Rainbow simulator in Colab](https://colab.research.google.com/github/raultruco/cryptowatson-indicators/blob/main/simulators/rwa_simulator.ipynb)

Change the value of these variables, at the top of the notebook, to customize the simulation. 

```
strategy             = "weighted_dca"    # Select strategy between "weighted_dca" and "rebalance"
ticker_symbol        = "BTCUSDT"      # currently only works with BTCUSDT
start                = '01/03/2022'   # start date of the simulation. Ex: '01/08/2020' or None
end                  = None           # end date of the simulation. Ex: '01/08/2020' or None
initial_cash         = 10000.0        # initial broker cash. Default 10000 usd
min_order_period     = 7              # Used in weighted_dca and rebalance strategies
base_buy_amount      = 100            # Used in weighted_dca strategy
weighted_multipliers = [1.5, 1.25, 1, 0.75, 0.5]    # Used in weighted_dca strategy
rebalance_percents   = [85, 65, 50, 15, 10]         # Used in rebalance strategy
```
