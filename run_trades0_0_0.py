
import subprocess
import sys 
from glob import glob
import time
from itertools import zip_longest
import json,datetime,schedule

from trader import write_signal 
from funcs import get_data,get_entrys_exits,get_entry_signals,read_signal
from disc_api import ping,STATUS_PING2,SIGNALROLE,CRYPTO_SIGNALS2,ERROR_PING2

## input arguments
param_choice = 0 
if len(sys.argv)>1:
    param_choice = int(sys.argv[1])

trade_params = json.load(open("trade_params.json","r"))
trade_param = trade_params["ver1"]["params"][param_choice]
thres_diff = float(trade_param["thres_diff"])
tickerpair = trade_param["tickerpair"]
interval = trade_param["interval"]
sl = float(trade_param["sl"])
tp = float(trade_param["tp"])
percentile = float(trade_param["percentile"])
hl_pairs = None

entered=False
new_entry=False

def get_signal():
    global new_entry, entered,thres_diff,percentile,interval,tickerpair 
    dfmpl = get_data(tickerpair,interval,limit=100,type="live")
    entrys,exits,sc_up,sc_dn,r_high_sm,r_low_sm,r_sm,r_sm_diff,thres_diff = get_entrys_exits(dfmpl,percentile,thres_diff)
    #get all entry signal
    entry_signals = get_entry_signals(entrys,dfmpl,onlybuy=True) 
    new_entry=False
    entry_df= None;buy=None
    for entry,exit in zip_longest(entrys,exits,fillvalue=None):
        if exit is None: # missing exit signal, so its a new enter signal
            buy_list = [ buy for entry_, buy in entry_signals if entry_==entry]
            if len(buy_list)==1: 
                new_entry=True
                entry_df=dfmpl.iloc[entry]
                buy=buy_list[0]
    if new_entry:
        assert buy==1
    if new_entry and entered:
        #print("hold")
        write_signal(tickerpair,interval,signal="HOLD",closeprice=dfmpl.iloc[-1].Close,dfname=dfmpl.iloc[-1].name) 
    elif not new_entry and entered:
        #print("exit trade now")
        entered=False
        strr = f"EXIT pc{param_choice} `{tickerpair}` `{interval}` `{dfmpl.iloc[-1].Close}`"
        strr+= f"`{dfmpl.iloc[-1].name}` (`{str(datetime.datetime.now())}`) {SIGNALROLE}"
        write_signal(tickerpair,interval,signal="EXIT",closeprice=dfmpl.iloc[-1].Close,dfname=dfmpl.iloc[-1].name) 
        ping(CRYPTO_SIGNALS2,strr)#requests.post(config["crypto-signals2"],data={"content":strr})
    elif new_entry and not entered:
        xx = entry_df.Close
        strr = f"pc{param_choice} `{tickerpair}` `{interval}` "+ ("BUY  " if buy==1 else "SELL ")+f"`{xx}`" 
        strr += f" tp `{xx*(1+0.01*buy):.4f}` sl `{xx*(1-0.005*buy):.4f}`\n"
        strr += f"`{entry_df.name}` (`{str(datetime.datetime.now())}`) {SIGNALROLE}"
        write_signal(tickerpair,interval,signal="ENTER",closeprice=dfmpl.iloc[-1].Close,dfname=dfmpl.iloc[-1].name)
        # execute trading algo
        enterdftime = str(dfmpl.iloc[-1].name).replace(" ","_")
        cmd = ["python","master_trades.py",param_choice,"15",f"{enterdftime}","TEST"]
        subprocess.Popen( cmd , shell=True)
        ping(CRYPTO_SIGNALS2,strr)#requests.post(config["crypto-signals2"],data={"content":strr})
        entered=True
    else:
        strr = f"fetched pc{param_choice} `{tickerpair}` `{interval}` at `{dfmpl.iloc[-1].name}`"
        strr+= f"(`{str(datetime.datetime.now())}`)"
        ping(STATUS_PING2,strr)#requests.post(config["status-ping2"],data={"content":strr})
    ddtn=datetime.datetime.now()
    print(f"last ran:{ddtn}")
def get_signal_with_warnings():
    try:
        get_signal()
    except Exception as e:
        ping(ERROR_PING2,f"error pc{param_choice} "+str(e))
        raise
print("starting")
intvl = int(interval.split("m")[0]); ddtn=datetime.datetime.now()
delay = (intvl-1-ddtn.minute%intvl)*60+(60-ddtn.second+12) # 12 seconds after 
time.sleep(delay)
schedule.every(intvl).minutes.at(":02").do(get_signal) # run this at 22:30:04 
while True:
    schedule.run_pending()
    time.sleep(1)























