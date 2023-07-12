# CryptoTrader
speaks for itself

## installation

conda install with `conda create --name cryt310 --file requirements2.txt`

install with `pip3 install -r requirements2.txt`
1
uses python 3.10

install ta lib with `conda install -c conda-forge ta-lib`

pip install requests schedule pandas mplfinance numpy

## commands

conda create -n cryt310 python=3.10
conda activate cryt310
pip install -q numpy requests schedule pandas mplfinance notebook
pip install python-binance
conda install -y -c conda-forge ta-lib
python testimports.py


## todos

- ✅ a script to start/restart all runs

- ✅ run multiple signals at the same time.
- ✅ try binance apis for trading
- rewrite `run_trades_ver2.py` to scale up to ~750 ticker/interval pairs per 5 minutes
- update historical data to recent months
- fix run_trades_ver2, dont Upslow on initial run?
- report reason for exit, either TP,SL,Exitsignal
## non-urgent todos

- find tickerpairs present on MT4 trading platform.
- optimise parameters for tickerpairs.