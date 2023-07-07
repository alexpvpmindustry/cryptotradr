import numpy as np
import pandas as pd
import mplfinance as mpf
import os
import sys
from glob import glob
#import matplotlib.pyplot as plt
from trader import get_klines
from trader import klines_to_dfmpl
#%matplotlib inline
from collections import Counter
import talib as ta # conda activate cryt310
from matplotlib.ticker import AutoMinorLocator
import time
from itertools import zip_longest
#from IPython.display import Javascript
import datetime
import schedule
import json,requests
#config = json.load(open("secrets.config","r")) 
role="<@&1126499478342475807>"

tickerpair="ETCUSDT" #GBPUSDT #LTCUSDT #ETHUSDT #BTCUSDT
#tickerpair="BNBUSDT" #BNBUSDT #AUDUSDT #XMRUSDT
intervals=['1m','3m','5m','15m','30m','1h','2h','3h','4h','6h','8h','12h','1d','3d','1w','1Month']

def mapped(i):
    if i[:2]=="00":
        return -1
    if i[:2]=="11":
        return 1
    return 0
def now_ms():
    return int(time.time()*1_000)
print("imported everything!")