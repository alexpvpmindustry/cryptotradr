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
config = json.load(open("secrets.config","r")) 
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

# define constants
tickerpair="ETCUSDT"
interval="5m"
## input arguments
if len(sys.argv)>1:
    tickerpair= sys.argv[1]
    interval = sys.argv[2]
percentile=98
#thres_diff=0.004225 #ETCUSDT 30m 98%
#thres_diff=0.002227 #ETCUSDT 15m 98%
thres_diff=0.0009295 *0.95 #ETCUSDT 5m 98%
thres_diff=None
if tickerpair=="ETCUSDT":
    if interval=="30m":
        thres_diff=0.004225
    if interval=="15m":
        thres_diff=0.002227
    if interval=="5m":
        thres_diff=0.0009295*0.95
        
entered=False

def get_signal():
    global new_entry, entered,thres_diff,percentile,interval,tickerpair
    klines = get_klines(tickerpair,interval,limit=300)
    dfmpl = klines_to_dfmpl(klines).iloc[:-1]
    #fulllen=len(dfmpl)
    #print(fulllen)

    xvals=np.arange(len(dfmpl.Close))
    rolling_high_std_mean = dfmpl.High.rolling(14).std()/dfmpl.High.rolling(14).mean()
    rolling_low_std_mean = dfmpl.Low.rolling(14).std()/dfmpl.Low.rolling(14).mean()
    rolling_std_mean=rolling_low_std_mean*0.5+rolling_high_std_mean*0.5
    r_std_mean_diff = rolling_std_mean.diff()

    if not thres_diff:
        thres_diff = np.percentile(r_std_mean_diff.values[np.where(~np.isnan(r_std_mean_diff.values))],percentile)

    mkoffset = 1.01
    crossings = np.where(np.diff(r_std_mean_diff>thres_diff,1))[0]
    scatter = [ dfmpl.Close.iloc[i]*mkoffset if i in crossings else np.nan for i in xvals]
    crossup=np.where(np.diff((r_std_mean_diff>thres_diff)*1.,1)>0)[0]
    scatterup = [ dfmpl.Close.iloc[i]*mkoffset if i in crossup else np.nan for i in xvals]
    crossdn=np.where(np.diff((r_std_mean_diff>thres_diff)*1.,1)<0)[0]
    scatterdn = [ dfmpl.Close.iloc[i]*mkoffset if i in crossdn else np.nan for i in xvals] 

    entrys = np.where(~np.isnan(scatterup))[0]
    exits = np.where(~np.isnan(scatterdn))[0]
    #get all entry signal
    entry_signals = []
    for entry in entrys:
        if (entry-2)<0:
            continue
        s_1 = dfmpl.iloc[entry-2]
        s = dfmpl.iloc[entry-1]
        s1 = dfmpl.iloc[entry] 
        values_ = [s_1.Close-s_1.Open,s.Close-s.Open]
        presignal = "".join([ "1"if x>0 else "0" for x in values_])
        buy=mapped(presignal)
        if buy!=0:
            entry_signals.append( (entry,buy) )
    # check if its new entry
    new_entry=False
    entry_df= None;entry_time_utc_ms=None;buy=None
    for entry,exit in zip_longest(entrys,exits,fillvalue=None):
        if exit is None: # missing exit signal, so its a new enter signal
            buy_list = [ buy for entry_, buy in entry_signals if entry_==entry]
            if len(buy_list)==1: 
                new_entry=True
                entry_df=dfmpl.iloc[entry]
                buy=buy_list[0]

    if new_entry and entered:
        #print(dfmpl.iloc[-1])
        #print("hold")
        pass
    elif not new_entry and entered:
        #print(dfmpl.iloc[exits[-1]])
        #print("exit trade now")
        entered=False
        requests.post(config["crypto-signals2"],data={"content":f"exit {tickerpair} {interval} {dfmpl.iloc[-1].Close} {dfmpl.iloc[-1].name}"})
    elif new_entry and not entered:
        entry_time_utc_ms = entry_df.name.value//1_000_000
        xx = entry_df.Close
        strr = tickerpair+" "+ ("BUY  " if buy==1 else "SELL ")+f"{xx}" 
        strr += f" tp {xx*(1+0.01*buy):.4f} sl {xx*(1-0.005*buy):.4f}\n"
        strr += f"{entry_df.name} {role} at {str(datetime.datetime.now())}"
        #print(strr)
        requests.post(config["crypto-signals2"],data={"content":strr})
        #print(entry_df)
        entered=True
        #print("*"*8,"new entry",entry_time_utc_ms) #klinetime= entry_time_utc_ms-3*3600*1_000
    else:
        strr = f"fetched {tickerpair} {interval} at {dfmpl.iloc[-1].name} at {str(datetime.datetime.now())}"
        requests.post(config["status-ping2"],data={"content":strr})
    ddtn=datetime.datetime.now()
    print(f"last ran:{ddtn}")
print("starting")
intvl = int(interval.split("m")[0]); ddtn=datetime.datetime.now()
delay = (intvl-1-ddtn.minute%intvl)*60+(60-ddtn.second+12) # 12 seconds after 
time.sleep(delay)
schedule.every(intvl).minutes.at(":03").do(get_signal) # run this at 22:30:04 
while True:
    schedule.run_pending()
    time.sleep(1)























