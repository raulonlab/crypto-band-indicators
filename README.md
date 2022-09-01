# crypto-band-indicators

Implementation of crypto indicators and strategies based on indexes that can be divided or grouped in bands. Any index with a known range of values is suitable to be divided in bands by taking the range of the data (largest minus smallest) and divide it by the number of desired bands.

The library contains the implementation of the indicators: 
- `Fear and Greed`,
- `Rainbow Index`,

And the strategies:
- `Rebalance`,
- `Weighted DCA`

There are also 2 simulators written in Jupyter notebooks to backtest the performance of the indicators / strategies:

- Compare strategies: Run a simulation of the indicators / strategies for a given set of parameters and dates [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/raulonlab/crypto-band-indicators/blob/main/simulators/compare_strategies.ipynb)

- Optimise strategies: Run a simulation of the indicators / strategies in order to get the best parameters [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/raulonlab/crypto-band-indicators/blob/main/simulators/optimise_strategies.ipynb)

## Indicators

### Fear and Greed

The Fear and Greed Index is a tool that helps investors and traders analyze the Bitcoin and Crypto market from a sentiment perspective. It identifies the extent to which the market is becoming overly fearful or overly greedy. Hence why it is called the Fear and Greed Index.

- See the live version for Bitcoin in [lookintobitcoin](https://www.lookintobitcoin.com/charts/bitcoin-fear-and-greed-index/)

The Fear and Greed index has a value in the range (0, 100) and is divided in 5 bands ordered from best (Fear) to worst (Greed):

1. ( 0-25):  Extreme Fear
2. (26-46):  Fear
3. (47-54):  Neutral
4. (55-75):  Greed
5. (76-100): Extreme Greed

### Rainbow Chart

The Rainbow Chart is a long-term valuation tool for Bitcoin. It uses a logarithmic growth curve to forecast the potential future price direction of Bitcoin.

It overlays rainbow color bands on top of the logarithmic growth curve channel in an attempt to highlight market sentiment at each rainbow color stage as price moves through it. Therefore highlighting potential opportunities to buy or sell.

See a live version for Bitcoin in [lookintobitcoin](https://www.lookintobitcoin.com/charts/bitcoin-rainbow-chart/) or [blockchaincenter](https://www.blockchaincenter.net/en/bitcoin-rainbow-chart/)

And for Ethereum in [blockchaincenter](https://www.blockchaincenter.net/ethereum-rainbow-chart/)

The Rainbow Chart is divided in 9 bands ordered from worst (expensive) to best (cheap):

1. Maximum bubble!!
2. Sell, seriouly sell!
3. FOMO intensifies
4. Is this a bubble?
5. HODL
6. Still cheap
7. Accumulate
8. Buy!
9. Fire sale!!

## Strategies

### Rebalance 

Applies a rebalance percentage of the position between BTC and USDT depending on the indicator band. The better band index, the more percentage of BTC against USDT is kept in the wallet over the total value in USDT.

#### Parameters
- **rebalance_percents**: Rebalance percentages of BTC over USDT for each band. Ex: [85, 65, 50, 15, 10]
- **min_order_period**: Minimum interval of days between consecutive orders. Ex: 5

### Weighted Averaging DCA

Variation of the traditional Dollar Cost Average (DCA) method of investing that takes into account the current indicator index. The better index, the bigger the amount of BTC purchased.

The idea of applying this strategy with the Rainbow index comes from [this post in Reddit by the user u/pseudoHappyHippy](https://www.reddit.com/r/CryptoCurrency/comments/qg9s6v/introducing_rainbowweighted_averaging_a_more/). The author claims that RWA (Rainbow Weighted Averaging) outperforms DCA 96.8% of the time by an average of 35.3% greater returns when applied to historical BTC price data.

#### Parameters

- **base_buy_amount**: Amount base to buy, as in standard DCA
- **weighted_multipliers**: Buy amount multipliers (weight) for each band. Ex: [1.5, 1.25, 1, 0.75, 0.5]
- **min_order_period**: Interval of days between periodical orders. Ex: 5

## Simulators

Jupyter notebooks to backtest the performance of the different combinations of indicators and strategies with its respective parameters:  

- `simulators/compare_strategies.ipynb`: Run a backtest to compare the performance of all the indicators / strategies for a given set of parameters and dates.  
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/raulonlab/crypto-band-indicators/blob/main/simulators/compare_strategies.ipynb)

- `simulators/optimise_strategies.ipynb`: Run a backtest to optimise the performance of all the indicators / strategies by using different set of parameters.  
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/raulonlab/crypto-band-indicators/blob/main/simulators/optimise_strategies.ipynb)

The notebooks provide a `Variables` section to change the parameters of the simulation:

```
# Common variables
# ticker_symbol       = "BTCUSDT"   # currently only works with BTCUSDT
start               = '01/01/2021'  # start date of the simulation. Ex: '01/08/2020' or None
end                 = '31/12/2021'  # end date of the simulation. Ex: '01/08/2020' or None
initial_cash        = 10000.0       # initial broker cash. Default 10000 usd
min_order_period    = 5             # Minimum period in days to place orders
base_buy_amount     = 100           # Amount purchased in standard DCA

# Specific for Fear and greed indicator
fng_weighted_multipliers    = [1.5, 1.25, 1, 0.75, 0.5]  # buy amount multipliers (weighted) for each band
fng_rebalance_percents      = [85, 65, 50, 15, 10]       # rebalance percentages of BTC / total for each band
fng_indicator_params        = {}                         # specific parameters for FnG indicator

# Specific for Rainbow indicator
rainbow_weighted_multipliers    = [0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.3, 2.1, 3.4]
rainbow_rebalance_percents      = [10, 20, 30, 40, 50, 60, 70, 80, 90]
rainbow_indicator_params        = {}

# Other options
log_progress         = False
plot_results         = False
```
