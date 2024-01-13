# CryptoTrader
speaks for itself


## current analysis

[here](html_results/2_3_0_try_dd.html)

## installation

conda install with `conda create --name cryt310 --file requirements2.txt`

install with `pip3 install -r requirements2.txt`

uses python 3.10

install ta lib with `conda install -c conda-forge ta-lib`

pip install requests schedule pandas mplfinance numpy

## commands

#### install these

```bash
conda create -n cryt310 python=3.10
conda activate cryt310
pip install -q numpy requests schedule pandas mplfinance notebook
pip install python-binance
conda install -y -c conda-forge ta-lib
```

#### test these

```bash
python testimports.py
python test_trades.py
```
## todos



- fix entry for times when entry was before initialisation ( need to check )
- look for tickers at 5m interval with more than 9% (to 6%) change. next ticks might be high.
    - see STMXUSDT at 2023/7/23 12:30
- restructure the code so that its more modular. the followings should be kept seperate
    - download/get data, identify signals, act on signals
    - this way, (2) and (3) can be backtested


- ✅ rewrite `run_trades_ver2.py` to scale up to ~750 ticker/interval pairs per 5 minutes
- ✅ fix run_trades_ver2, dont Upslow on initial run?
- ✅ reduce status calls to discord ping.
- ✅ limit number of positions? using binanceexceptions
- ✅ some code to validate the timing of prev candlestick
- ✅ a script to start/restart all runs
- ✅ run multiple signals at the same time.
- ✅ try binance apis for trading
- ✅ update historical data to recent months
- ✅ report reason for exit, either TP,SL,Exitsignal

## idea todos
- from 9_0_5
- do predictions for top 10 tickers at 5m resolution
- then use hourly/30m-ly 24hr change to find datasets to validate this analysis/prediction

## non-urgent todos

- get_data to return more live data then just 1000
- find tickerpairs present on MT4 trading platform.
- optimise parameters for tickerpairs.

## commands

conda activate cryt310
cd Documents\Github\cryptotradr
python aver6_run_trades.py


python aver5_run_trades.py 0 40 5m
python aver5_run_trades.py 80 120 30m