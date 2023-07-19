
import subprocess
import sys
import time
from itertools import zip_longest
import json,datetime,schedule

from aver5_trader import write_signal
from aver5_funcs import get_data,get_entrys_exits,get_entry_signals, validate_dfmpl
from disc_api import ALEXPING, ping,STATUS_PING2,SIGNALROLE,CRYPTO_SIGNALS2,ERROR_PING2
import threading

TZOFFSET=5*60*60 

## input arguments # min and max of param choice
param_choice_min = 0
param_choice_max = 1
if len(sys.argv)>1:
    param_choice_min = int(sys.argv[1])
    param_choice_max = int(sys.argv[2])
    interval_choice = sys.argv[3]
class signal_object:
    def __init__(self,param_choice):
        self.param_choice=param_choice
        self.interval=None
        self.load_params()
    def load_params(self):
        with open("trade_params.json","r") as f:
            self.trade_params = json.load(f)
        self.trade_param = self.trade_params["ver5"]["params"][self.param_choice]
        self.thres_diff = float(self.trade_param["thres_diff"])
        self.tickerpair = self.trade_param["tickerpair"]
        self.interval = self.trade_param["interval"]
        self.sl = float(self.trade_param["sl"])
        self.tp = float(self.trade_param["tp"])
        self.percentile = float(self.trade_param["percentile"])*0.8
        self.hl_pairs = None
        self.entered=False
        self.new_entry=False
        self.price_format = ".6g"

    def get_signal(self,firstRun=False):
        #global new_entry, entered,thres_diff,percentile,interval,tickerpair
        correct=False;trys=0
        while not correct:
            dfmpl = get_data(self.tickerpair,self.interval,limit=100,type="live")
            # check that dfmpl contains the last candlestick
            correct,dfmpl = validate_dfmpl(dfmpl)
            if not correct:
                time.sleep(1)
                print(f"waiting 1 sec for retrypc{self.param_choice},{self.tickerpair}{self.interval}")
            if trys>60:#something might be wrong here,
                raise Exception(f"pc{self.param_choice}{self.tickerpair}{self.interval} too many tries without getting last candlestick {datetime.datetime.now()}")
            trys+=1
        entrys,exits,_,_,_,_,_,_,_ = get_entrys_exits(dfmpl,self.percentile,self.thres_diff)
        #get all entry signal
        entry_signals = get_entry_signals(entrys,dfmpl,onlybuy=True) 
        self.new_entry=False
        entry_df= None;buy=None
        # todo , this will still report pervious entries as new entry on start
        # todo redo run trades (possibly fixed)
        for entry,exit in zip_longest(entrys,exits,fillvalue=None):
            if exit is None: # missing exit signal, so its a new enter signal
                buy_list = [ buy for ( entry_, buy, _ ) in entry_signals if entry_==entry]
                if len(buy_list)==1: 
                    self.new_entry=True
                    entry_df=dfmpl.iloc[entry]
                    buy=buy_list[0]
        if self.new_entry:
            assert buy==1
            if not self.entered:
                # ensure that the candlestick is the latest candlestick
                timediff_minutes = ((datetime.datetime.now() - entry_df.name).seconds - TZOFFSET)/60
                intvl = int(self.interval.split("m")[0])
                strr = f"new entry pc{self.param_choice}{self.tickerpair}{self.interval}, entrydf.close{entry_df.Close:{self.price_format}} but checking\n"
                strr+= f"timediff{timediff_minutes:.2f} intvl {intvl}, current time{datetime.datetime.now()}\n"
                strr+= f"entrydf{entry_df.name}, last few df \n{dfmpl.iloc[-2:]}"
                ping(STATUS_PING2,strr)
                assert timediff_minutes>intvl # candle should open more than "interval" minutes ago
                if timediff_minutes>intvl*1.5: # next candle should be at least in the first half of the interval
                    self.new_entry=False
                    self.consolelog()
                    return
        # at this point, entry_df should be the latest completed candle. at most half self.interval towards the next candle.
        if self.new_entry and self.entered:
            #print("hold")
            write_signal(self.tickerpair,self.interval,signal="HOLD",closeprice=dfmpl.iloc[-1].Close,dfname=dfmpl.iloc[-1].name) 
        elif not self.new_entry and self.entered:
            #print("exit trade now")
            self.entered=False
            strr = f"EXIT signal pc{self.param_choice} `{self.tickerpair}` `{self.interval}` `{dfmpl.iloc[-1].Close:{self.price_format}}` "
            strr+= f"`{dfmpl.iloc[-1].name}` (`{str(datetime.datetime.now())[:-4]}`) {SIGNALROLE}"
            write_signal(self.tickerpair,self.interval,signal="EXIT",closeprice=dfmpl.iloc[-1].Close,dfname=dfmpl.iloc[-1].name) 
            ping(CRYPTO_SIGNALS2,strr)
        elif self.new_entry and not self.entered:
            xx = entry_df.Close
            strr = f"pc{self.param_choice} `{self.tickerpair}` `{self.interval}` "+ ("BUY  " if buy==1 else "SELL ")+f"`{xx}`" 
            strr += f" tp `{xx*(1+self.tp):{self.price_format}}` sl `{xx*(1+self.sl):{self.price_format}}`\n"
            strr += f"`{entry_df.name}` (`{str(datetime.datetime.now())[:-4]}`) {SIGNALROLE}"
            write_signal(self.tickerpair,self.interval,signal="ENTER",closeprice=dfmpl.iloc[-1].Close,dfname=dfmpl.iloc[-1].name)
            # execute trading algo
            enterdftime = str(dfmpl.iloc[-1].name).replace(" ","_")
            cmd = ["python","aver5_master_trades.py",f"{self.param_choice}","15",f"{enterdftime}","TEST",f"{xx:{self.price_format}}"]
            cmd = " ".join(cmd)
            subprocess.Popen( cmd , shell=True)
            ping(CRYPTO_SIGNALS2,strr)
            self.entered=True
        else:
            strr = f"pc{self.param_choice} `{self.tickerpair}` `{self.interval}` at `{dfmpl.iloc[-1].name}`"
            strr+= f"(`{str(datetime.datetime.now())[:-4]}`) ftch"
            time.sleep(1*self.param_choice )
            ping(STATUS_PING2,strr)
        self.consolelog()
    def consolelog(self):
        ddtn=str(datetime.datetime.now())[:-4]
        print(f"last ran:{ddtn},new_e{self.new_entry},entrd{self.entered},pc{self.param_choice}{self.tickerpair}{self.interval}")
    def get_signal_with_warnings(self,firstRun=False):
        try:
            print(f"within get_signal_with_warnings, pc{self.param_choice} {self.tickerpair}{self.interval}")
            time.sleep( 0.1*self.param_choice ) # delay subsequent calls by 0.1sec
            self.get_signal(firstRun)
        except Exception as e:
            ping(ERROR_PING2,f"error pc{self.param_choice} {self.tickerpair}{self.interval} {ALEXPING}"+str(e))
            raise

print("starting param choice",param_choice_min,param_choice_max)
list_of_signal_objects=[]
for param_choice in range(param_choice_min,param_choice_max+1):
    s= signal_object(param_choice)
    print("params",interval_choice,s.interval,s.tickerpair)
    if s.interval == interval_choice:
        list_of_signal_objects.append(s)

def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()

#def add_to_schedule(self): # this needs to be fixed
ddtn=datetime.datetime.now()
if "m" in interval_choice:
    intvl = int(interval_choice.split("m")[0]); 
    delay = (intvl-1-ddtn.minute%intvl)*60+(60-ddtn.second+22) # 22 seconds after 0th min
    time.sleep(delay)
    print(f"scheduling for {len(list_of_signal_objects)} tickers")
    for s in list_of_signal_objects:
        schedule.every(intvl).minutes.at(":03").do(run_threaded,s.get_signal_with_warnings)
if len(list_of_signal_objects)>0:
    print(f"while loop for {len(list_of_signal_objects)} tickers")
    while True:
        schedule.run_pending()
        time.sleep(1)
else:
    print(f"no valid symbols for this interval {interval_choice}, ending")






















