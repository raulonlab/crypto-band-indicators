# cryptowatson-indicators

Python package to calculate crypto indicators and run trading simulations

### Cryptocurrency indicators

### Rainbow Weighted Average

Rainbow-Weighted Averagin (RWA) is a variation of the traditional Dollar Cost Average (DCA) method of investing that takes into account the current Rainbox Index. The idea comes from [this post in Reddit by the user u/pseudoHappyHippy](https://www.reddit.com/r/CryptoCurrency/comments/qg9s6v/introducing_rainbowweighted_averaging_a_more/). The author claims that RWA outperforms DCA 96.8% of the time by an average of 35.3% greater returns when applied to historical BTC price data

- BTC Rainbow chart: 
    - [lookintobitcoin](https://www.lookintobitcoin.com/charts/bitcoin-rainbow-chart/)
    - [Bitcoin Rainbow Chart (Live) - Blockchaincenter](https://www.blockchaincenter.net/en/bitcoin-rainbow-chart/)

- [Bitcoin Logarithmic Growth Curves @ lookintobitcoin](https://www.lookintobitcoin.com/charts/bitcoin-logarithmic-growth-curve/)
  
- ETH Rainbow chart: [Ethereum Rainbow Chart - Blockchaincenter](https://www.blockchaincenter.net/ethereum-rainbow-chart/)


### Fear and Greed Index

The Fear and Greed Index is a tool that helps investors and traders analyze the Bitcoin and Crypto market from a sentiment perspective. It identifies the extent to which the market is becoming overly fearful or overly greedy. Hence why it is called the Fear and Greed Index.

- Fear And Greed Index, by lookintobitcoin: https://www.lookintobitcoin.com/charts/bitcoin-fear-and-greed-index/

### Backtrading for backtesting
- [Backtrader for backtesting @ algotrading101](https://algotrading101.com/learn/backtrader-for-backtesting/)
- 

### Resources

- [Part 1 - Using Python to Analyze Rainbow-Weighted Averaging — A More Profitable Frequency Investment Strategy](https://medium.com/coinmonks/using-python-to-analyze-rainbow-weighted-averaging-a-more-profitable-frequency-investment-12009a8c3617)
- [Part 2 - Creating a Rainbow Weighted Average Trading bot with Python](https://blog.devgenius.io/creating-a-rainbow-weighted-average-trading-bot-with-python-99f13642a2c9)
    - Source code: https://github.com/Totesthegoats/rwa_bot
    - RWA strategy revisited: https://medium.com/@chris_42047/the-rainbow-weighted-average-strategy-revisited-afb02b45aead
    - Logarithmic (non-linear) regression - Bitcoin estimated value @ bitcointalk.org: https://bitcointalk.org/index.php?topic=831547
- [Logarithmic Regression in Python (Step-by-Step)](https://www.statology.org/logarithmic-regression-python/) and [Logarithmic regression calculator](https://www.statology.org/logarithmic-regression-calculator/)

- Fear and Greed Index API: https://alternative.me/crypto/fear-and-greed-index/#api

- 
- [What is a Walk-Forward Optimization and How to Run It?](https://algotrading101.com/learn/walk-forward-optimization/)
- using GitHub (or other providers) as a PyPy Server: https://www.freecodecamp.org/news/how-to-use-github-as-a-pypi-server-1c3b0d07db2

- Run Jupyter notebooks online:
    - https://mybinder.org/
        - Python package with setup.py: https://mybinder.readthedocs.io/en/latest/examples/sample_repos.html?highlight=requirements#python-package-with-setup-py
    - https://colab.research.google.com/
    - http://cocalc.com/
    - https://github.com/features/codespaces

# Notes

- Alternative API misses these dates:
merged = pd.merge(fng_data, ticker_data, how='outer', on='Date')
print('merged:\n', merged)
1646 2018-04-14      NaN           NaN   8036.511051
1647 2018-04-15      NaN           NaN   8340.748333
1648 2018-04-16      NaN           NaN   8368.100000


