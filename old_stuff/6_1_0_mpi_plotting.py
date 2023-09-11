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

def plotresults(pickled_data2,dfmpl):
    fee=0.0015
    (entrys,exits,sc_up,sc_dn,r_high_sm,r_low_sm,r_sm,r_sm_diff,thres_diff,
    predict,result,predict_seq,predicted_result,profit,trade_dur,df0,
    df0_signal,hl_pair,final_profit,equity)=pickled_data2
    lastNsamples = int(len(result)*0.1)
    fig,(ax1,ax2)=plt.subplots(2,1,figsize=(8,5),sharex=True,dpi=100)
    ax1.plot(equity,"-x")
    ax1.set_ylabel("equity (start with $1)")
    ax1.set_title(f"{tickerpair} {interval} {percentile}% fee{fee} buy only")
    str1,gains_,trading_days,gains_per_day,gains_per_trade,avg_prof,wr= get_stats(dfmpl,sc_up,profit,trade_dur,0,fee=0)
    gs = get_stats(dfmpl,sc_up,profit,trade_dur,lastNsamples,fee=0)[0]
    ax1.text(0.02,0.99, "overall\n"+str1,transform=ax1.transAxes,va="top",ha="left")
    ax1.text(0.02,0.56, f"last {lastNsamples} trades\n"+gs,transform=ax1.transAxes,va="top",ha="left")
    ax1.text(0.87,0.0, "seq,n\n"+"\n".join([p[0]+","+str(p[1]) for p in predict_seq]),transform=ax1.transAxes,va="bottom",ha="left")
    ax1.axvline(len(profit)-lastNsamples,c="r",ls="--")
    ax2.plot(profit,"x")
    ax2.axhline(0,c="r",alpha=0.3)
    ax2.set_ylabel("profit per trade")
    ax2.text(0.02,0.99,f"full len={len(dfmpl)}, thres_diff={thres_diff:.4g}",transform=ax2.transAxes,va="top",ha="left") 
    for ax in (ax1,ax2):
        ax.set_xlabel("trades")
        ax.tick_params("both",direction="in")
    ax2.yaxis.set_minor_locator(AutoMinorLocator())
    ax2.tick_params("y",which='minor',color="r")
    ax2.grid(which='minor',axis="y",alpha=0.5)
    ax2.grid(which='major',axis="y",color="r",alpha=0.5) 
    ax3 = ax2.inset_axes((1.05,0.1,0.3,0.3)) 
    ax3.text(0,1,"pfHist,g/trd",transform=ax3.transAxes,va="top",ha="left")
    ax3.hist(profit,bins=100)
    ax3.axvline(0,c="r",alpha=0.3)
    ax3.tick_params("both",direction="in",rotation=25,color="r") 
    ax3.set_yticks([])
    ax3.set_facecolor(f'#00{intpl(gains_per_trade*10,0,20):02X}0f60')
    ax4 = ax2.inset_axes((1.05,0.65,0.3,0.3))
    ax4.hist(r_sm_diff,bins=100)
    ax4.text(0,1,"thresDiff,g/day",transform=ax4.transAxes,va="top",ha="left") 
    ax4.axvline(thres_diff,c="r")
    ax4.tick_params("both",direction="in",rotation=25,color="r")
    ax4.set_yticks([])
    ax4.set_facecolor(f'#00{intpl(gains_per_day*10,0,20):02X}0f60')

    ax5 = ax1.inset_axes((1.05,0.0,0.4,0.99))
    hl_data = get_hl_data(hl_pair,buyonly=True) 
    plot_hl_ax(ax5,hl_pair,hl_data,bres=0.1,buyonly=True) 
    plt.tight_layout(h_pad=-1.08)
    plt.savefig(f"6_1_0_figures/FeeBO_{tickerpair}_{interval}_pcent{int(percentile):05d}.png")
    plt.close("all")
tp_i_list = [(tickerpair,interval) for tickerpair in tickerpairs for interval in intervals]


from multiprocessing import Pool

def f(tp_i_list_i):
    tickerpair,interval = tp_i_list_i
    try:
        dfmpl = get_data(tickerpair,interval,limit=55000,type="data")
    except ValueError:
        return "error"
    for percentile in percentiles:
        #if count%10==0:print(count,end=" ")#,tickerpair,interval,percentile)
        #count+=1
        with open(f"6_1_0_analysisdata/plotdata_{tickerpair}_{interval}_{percentile}.pkl","rb") as f:
            pickled_data2 = pickle.load(f)
        # (entrys,exits,sc_up,sc_dn,r_high_sm,r_low_sm,r_sm,r_sm_diff,thres_diff,
        # predict,result,predict_seq,predicted_result,profit,trade_dur,df0,
        # df0_signal,hl_pair,final_profit,equity)=pickled_data2

        plotresults(pickled_data2,dfmpl)
    return "done" 

if __name__ == '__main__':
    print("starting")
    with Pool(4) as p:
        print(p.map(f, tp_i_list[80:]))
    print("done")