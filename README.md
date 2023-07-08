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
conda install -y -c conda-forge ta-lib
python testimports.py


## todos

- a script to start/restart all runs
- find tickerpairs present on trading platform.
- optimise parameters for tickerpairs.
- run multiple signals at the same time.
- try binance apis for trading