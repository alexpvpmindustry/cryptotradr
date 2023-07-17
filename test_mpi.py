from multiprocessing import Pool

#import numpy as np
#import pandas as pd
#import mplfinance as mpf
import os
#from glob import glob
import matplotlib.pyplot as plt 

#import talib as ta # conda activate cryt310
from matplotlib.ticker import AutoMinorLocator
#import time
#from itertools import zip_longest 
#import datetime
#import schedule
#import json,requests
from aver4_funcs import *
import pickle
import warnings

warnings.simplefilter("error")


tickerpair="ETCUSDT" #GBPUSDT #LTCUSDT #ETHUSDT #BTCUSDT
#tickerpair="BNBUSDT" #BNBUSDT #AUDUSDT #XMRUSDT
tickerpairs=["ETCUSDT","GBPUSDT","LTCUSDT","ETHUSDT","BTCUSDT","BNBUSDT","AUDUSDT","XMRUSDT"] 

intervals=['1m','3m','5m','15m','30m','1h','2h','3h','4h','6h','8h','12h','1d','3d','1w','1Month']

# define constants
tickerpair="ETCUSDT"
interval="5m"
percentile=98
thres_diff=None 
entered=False
 
percentiles = [99]#[90,93,95,98,99]#[:1]
intervals=['5m','15m','30m']#[-1:]
tickerpairs=['ARBUSDT', 'AVAXUSDT', 'BCHUSDT', 'BNBUSDT', 'BTCUSDT',
             'ETCUSDT', 'ETHUSDT', 'LTCUSDT', 'MATICUSDT','SHIBUSDT', 
             'SOLUSDT','WAVESUSDT','XRPUSDT']
tickerpairs=os.listdir("kline_data/")

with open("trading_pairs.pkl","rb") as f:
    trading_pairs = pickle.load(f)
tickerpairs = [t["symbol"] for t in trading_pairs[:200]]

tp_i_list = [(tickerpair,interval) for tickerpair in tickerpairs for interval in intervals]

def f(x):
    tickerpair,interval=x
    return tickerpair+interval

if __name__ == '__main__':
    with Pool(5) as p:
        print(p.map(f, tp_i_list))