
import subprocess
import sys
import time
from itertools import zip_longest
import json,datetime,schedule

from trader import write_signal
from funcs import get_data,get_entrys_exits,get_entry_signals, validate_dfmpl
from disc_api import ALEXPING, ping,STATUS_PING2,SIGNALROLE,CRYPTO_SIGNALS2,ERROR_PING2

TZOFFSET=5*60*60 

## input arguments
param_choice = 0 
if len(sys.argv)>1:
    param_choice = int(sys.argv[1])

trade_params = json.load(open("trade_params.json","r"))
trade_param = trade_params["ver2"]["params"][param_choice]
thres_diff = float(trade_param["thres_diff"])
tickerpair = trade_param["tickerpair"]
interval = trade_param["interval"]
sl = float(trade_param["sl"])
tp = float(trade_param["tp"])
percentile = float(trade_param["percentile"])
hl_pairs = None

entered=False
new_entry=False

def get_signal(firstRun=False):
    global new_entry, entered,thres_diff,percentile,interval,tickerpair
    correct=False;trys=0
    while not correct:
        dfmpl = get_data(tickerpair,interval,limit=100,type="live")
        # check that dfmpl contains the last candlestick
        correct,dfmpl = validate_dfmpl(dfmpl)
        if not correct:
            time.sleep(1)
        if trys>60:#something might be wrong here,
            raise Exception(f"pc{param_choice}{tickerpair}{interval} too many tries without getting last candlestick {datetime.datetime.now()}")
        trys+=1
    entrys,exits,_,_,_,_,_,_,thres_diff = get_entrys_exits(dfmpl,percentile,thres_diff)
    #get all entry signal
    entry_signals = get_entry_signals(entrys,dfmpl,onlybuy=True) 
    new_entry=False
    entry_df= None;buy=None
    # todo , this will still report pervious entries as new entry on start
    # todo redo run trades (possibly fixed)
    for entry,exit in zip_longest(entrys,exits,fillvalue=None):
        if exit is None: # missing exit signal, so its a new enter signal
            buy_list = [ buy for ( entry_, buy, _ ) in entry_signals if entry_==entry]
            if len(buy_list)==1: 
                new_entry=True
                entry_df=dfmpl.iloc[entry]
                buy=buy_list[0]
    if new_entry:
        assert buy==1
        if not entered:
            # ensure that the candlestick is the latest candlestick
            timediff_minutes = ((datetime.datetime.now() - entry_df.name).seconds - TZOFFSET)/60
            intvl = int(interval.split("m")[0])
            strr = f"new entry, but checking timediff{timediff_minutes:.2f} intvl {intvl}, current time{datetime.datetime.now()}\n"
            strr+= f"entrydf{entry_df.name}, last few df {dfmpl.iloc[-2:]}"
            ping(STATUS_PING2,strr)
            assert timediff_minutes>intvl # candle should open more than "interval" minutes ago
            if timediff_minutes>intvl*1.5: # next candle should be at least in the first half of the interval
                new_entry=False
                consolelog()
                return
    # at this point, entry_df should be the latest completed candle. at most half interval towards the next candle.
    if new_entry and entered:
        #print("hold")
        write_signal(tickerpair,interval,signal="HOLD",closeprice=dfmpl.iloc[-1].Close,dfname=dfmpl.iloc[-1].name) 
    elif not new_entry and entered:
        #print("exit trade now")
        entered=False
        strr = f"EXIT signal pc{param_choice} `{tickerpair}` `{interval}` `{dfmpl.iloc[-1].Close}` "
        strr+= f"`{dfmpl.iloc[-1].name}` (`{str(datetime.datetime.now())[:-4]}`) {SIGNALROLE}"
        write_signal(tickerpair,interval,signal="EXIT",closeprice=dfmpl.iloc[-1].Close,dfname=dfmpl.iloc[-1].name) 
        ping(CRYPTO_SIGNALS2,strr)
    elif new_entry and not entered:
        xx = entry_df.Close
        strr = f"pc{param_choice} `{tickerpair}` `{interval}` "+ ("BUY  " if buy==1 else "SELL ")+f"`{xx}`" 
        strr += f" tp `{xx*(1+tp):.4f}` sl `{xx*(1+sl):.4f}`\n"
        strr += f"`{entry_df.name}` (`{str(datetime.datetime.now())[:-4]}`) {SIGNALROLE}"
        write_signal(tickerpair,interval,signal="ENTER",closeprice=dfmpl.iloc[-1].Close,dfname=dfmpl.iloc[-1].name)
        # execute trading algo
        enterdftime = str(dfmpl.iloc[-1].name).replace(" ","_")
        cmd = ["python","master_trades_ver2.py",f"{param_choice}","15",f"{enterdftime}","TEST",f"{xx:.6f}"]
        cmd = " ".join(cmd)
        subprocess.Popen( cmd , shell=True)
        ping(CRYPTO_SIGNALS2,strr)
        entered=True
    else:
        strr = f"pc{param_choice} `{tickerpair}` `{interval}` at `{dfmpl.iloc[-1].name}`"
        strr+= f"(`{str(datetime.datetime.now())[:-4]}`) ftch"
        time.sleep(1*param_choice )
        ping(STATUS_PING2,strr)
    consolelog()
def consolelog():
    ddtn=datetime.datetime.now()
    print(f"last ran:{ddtn}, new_entry{new_entry}, entered{entered},{tickerpair},{interval}")
def get_signal_with_warnings(firstRun=False):
    try:
        time.sleep( 0.1*param_choice ) # delay subsequent calls by 0.1sec
        get_signal(firstRun)
    except Exception as e:
        ping(ERROR_PING2,f"error pc{param_choice} {tickerpair}{interval} {ALEXPING}"+str(e))
        raise
print("starting")
ddtn=datetime.datetime.now()
if "m" in interval:
    intvl = int(interval.split("m")[0]); 
    delay = (intvl-1-ddtn.minute%intvl)*60+(60-ddtn.second+22) # 22 seconds after 0th min
    time.sleep(delay)
    schedule.every(intvl).minutes.at(":06").do(get_signal_with_warnings)
else:
    intvl = int(interval.split("h")[0])
    get_signal_with_warnings(True)
    delay = 1 # TODO
    schedule.every(intvl).hours.at(":00:02").do(get_signal_with_warnings)
while True:
    schedule.run_pending()
    time.sleep(1)























