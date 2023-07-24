
import pickle
import subprocess
import sys
import time
from itertools import zip_longest
import json,datetime,schedule

from aver6_trader import write_signal
from aver6_funcs import get_data,get_entrys_exits,get_entry_signals, validate_dfmpl
from disc_api import ALEXPING, ping,STATUS_PING2,SIGNALROLE,CRYPTO_SIGNALS2,ERROR_PING2
import threading
import numpy as np

TZOFFSET=5*60*60 

with open("9_0_subset_symbols_24hrchange.pkl","rb") as f:
    subset_symbols = pickle.load(f)
def get_time_before(minutes=10):
    return int((int(time.time())-minutes*60)*1000)
#start_time = get_time_before(24*60)
class signal_object:
    def __init__(self):
        self.interval="5m"
        self.last_ran = int(time.time())
        self.price_format = ".6g"
        self.offset=8*3600*1000
        self.tp=0.048
        self.sl=-0.02
        self.fetched_24hr_data=[[] for s in subset_symbols]
        self.fetched_fresh_all_data = [[] for s in subset_symbols]
        self.fetched_24hr_data_sync=[0 for s in subset_symbols]
        self.fetched_fresh_all_data_sync = [0 for s in subset_symbols]
        self.argsorted_data=None # [ordered ticker,time]
        self.subset_symbols=subset_symbols
        self.top10symbols_prev=None
        self.top10symbols_temp=None
        self.firstrun=False
    def fetch_24hr_data(self,idd): # do this every 1 to 4 th minute
        time.sleep(0.15*idd)
        if not self.firstrun:
            time.sleep(2*60) # TODO fix this :(
        start_time = get_time_before(15)#24*60)
        df0 = get_data(subset_symbols[idd]+"USDT","5m",limit=3,start_time=start_time-3600_000*24,offset=self.offset)
        self.fetched_24hr_data[idd]=df0.copy()
        self.fetched_24hr_data_sync[idd]+=1
        if idd in [0,len(subset_symbols)-1]:
            self.consolelog(f"0> fetch 24hr data{idd}")
    def fetch_new_data(self,idd): # do this every 4:10 th minute
        time.sleep(0.05*idd) 
        if not self.firstrun:
            time.sleep(20+4*60) # TODO fix this :(
        start_time = get_time_before(15)#24*60)
        df = get_data(subset_symbols[idd]+"USDT","5m",limit=3,start_time=start_time,offset=self.offset)
        self.fetched_fresh_all_data[idd]=df.copy()
        self.fetched_fresh_all_data_sync[idd]+=1
        if idd in [0,len(subset_symbols)-1]:
            self.consolelog(f"1> fetch temp data{idd}")
    def argsort_data(self):
        hr24change = [(df_aft.Close.values-df_bef.Close.values)/df_bef.Close.values for df_bef, df_aft in zip(self.fetched_24hr_data,self.fetched_fresh_all_data)]
        hr24change = np.asarray(hr24change)
        self.argsorted_data = np.argsort(-hr24change,axis=0) # the last row is the new incomplete data
        self.top10symbols_prev = self.argsorted_data[:10,1] # previous order
        self.top10symbols_temp = self.argsorted_data[:10,2] # current temp order 
    def checksync(self):
        avg = np.mean( self.fetched_24hr_data_sync )==np.mean(self.fetched_fresh_all_data_sync)
        constant = self.fetched_fresh_all_data_sync[0]==self.fetched_24hr_data_sync[0]
        if avg and constant:
            return True
        else:
            self.fetched_24hr_data_sync=[0 for s in subset_symbols]
            self.fetched_fresh_all_data_sync = [0 for s in subset_symbols]
            return False
    def get_signal(self):# execute this at 4:56 th minute
        self.last_ran = int(time.time())
        self.argsort_data()
        with open("trade_logs/data_logging_24_7_2023.log","a") as f:
            strr ="argsorted_data,"+self.ddtn_str()+"\n"
            strr+="_".join([ ",".join([ str(aa) for aa in a]) for a in self.argsorted_data]) + "\n"
            f.writelines( [strr] )
            self.consolelog("2> get_signal writelines")
        #print(self.fetched_24hr_data)
        #print(self.fetched_fresh_all_data)
        criteria_passed = False
        criteria_str = ""
        symbol = self.subset_symbols[self.top10symbols_temp[0]]
        self.top10current = [subset_symbols[iii] for iii in self.top10symbols_temp[:10]]
        if not self.top10symbols_prev[0]==self.top10symbols_temp[0]:
            # check for criteria, and then enter position
            argmax = self.top10symbols_temp[0]
            df=self.fetched_fresh_all_data[argmax]
            loc0=2
            gain=(df.iloc[loc0].Close-df.iloc[loc0].Open)/df.iloc[loc0].Open
            if gain>=0.03:
                pullback = (df.iloc[loc0].High - df.iloc[loc0].Close)/(df.iloc[loc0].High - df.iloc[loc0].Open)
                criteria_str =f",pb{pullback:.2%}."
                if pullback <=0.3:
                    criteria_passed=True
            if criteria_passed:
                  self.enter_position(symbol,df.iloc[loc0].Close,df.iloc[loc0].name)
                  self.entered=True
                  ping(CRYPTO_SIGNALS2,f"ENTER {symbol} {df.iloc[loc0].Close:{self.price_format}} {self.ddtn_str()}")
                  return
            else:
                criteria_str= f"gain{gain:.2%}"+criteria_str
            # did not pass criteria, wait for next iteration
            strr=f"prev {self.subset_symbols[self.top10symbols_prev[0]]},curr {symbol},failed criteria, {criteria_str}"
            ping(CRYPTO_SIGNALS2,strr)
        else:# no change in top position, wait for next iteration
            synced = self.checksync()
            top10current = ",".join(self.top10current)
            ping(STATUS_PING2,f"running {self.ddtn_str()}, sync{synced}, curr top symbols {top10current}")
        self.consolelog("fin signals")
    def enter_position(self,symbol,closeprice,dfname):
        xx = closeprice
        strr = f"`{symbol}` BUY `{xx}`" 
        strr += f" tp `{xx*(1+self.tp):{self.price_format}}` sl `{xx*(1+self.sl):{self.price_format}}`\n"
        strr += f"`{dfname}` (`{self.ddtn_str()}`) {SIGNALROLE}"
        write_signal(symbol,self.interval,signal="ENTER",closeprice=xx,dfname=dfname)
        # execute trading algo
        enterdftime = str(dfname).replace(" ","_")
        cmd = ["python","aver6_master_trades.py",symbol,"15",f"{enterdftime}","TEST",f"{xx:{self.price_format}}"]
        cmd = " ".join(cmd)
        subprocess.Popen( cmd , shell=True)
        ping(CRYPTO_SIGNALS2,strr)
    def consolelog(self,strr=""): 
        print(f"{self.ddtn_str()}, {strr}") 
    def ddtn_str(self):
        return str(datetime.datetime.now())[:-4]
    def get_signal_with_warnings(self):# execute this at :55 seconds
        # started at 1:50 seconds
        try:
            if not self.firstrun:
                self.consolelog(f"2> sleeping for signal,{3*60+5+60+60}secs")
                time.sleep(3*60+5+60+60) # this is more than 5mins to skip the first one, this works normally afterwards
            self.get_signal()
        except Exception as e:
            ping(ERROR_PING2,f"error {ALEXPING}"+str(e))
            raise

def run_threaded(job_func,data):
    job_thread = threading.Thread(target=job_func,args=(data,))
    job_thread.start()
def run_threaded_no_data(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()


# - every: 1 to 4th minute download previous data.
# - every 4th minute, download all new data and sort them
# - then at 4:40/4:55 second, download only the top 10 tickers
# - then if any other ticker becomes the first ticker, enter position
s = signal_object()
ddtn=datetime.datetime.now()
intvl = 5 #int(interval_choice.split("m")[0]); 
delay = (intvl-1-ddtn.minute%intvl)*60+(60-ddtn.second+35) # 0min 35 seconds after 0th min

if delay > 5*60:
    delay -= 5*60

##temp
# for idd in range(len( subset_symbols )):
#     s.fetch_24hr_data(idd)
#     s.fetch_new_data(idd)
# s.get_signal_with_warnings()
# assert False
## end temp
print(f"waiting for {delay} secs")
# if delay is more than ~120seconds, 
# set firstrun True
# run the 2 data functions then argsort
# then set firstrun False
# then wait to apply new schedule.
time.sleep(delay)
print(f"scheduling at {datetime.datetime.now()}")
for idd in range(len( subset_symbols )):
    schedule.every(intvl).minutes.at(":50").do(run_threaded,s.fetch_24hr_data,idd)
    schedule.every(intvl).minutes.at(":50").do(run_threaded,s.fetch_new_data,idd)
schedule.every(intvl).minutes.at(":50").do(run_threaded_no_data,s.get_signal_with_warnings)
print(f"scheduled algos {datetime.datetime.now()}")
while True:
    schedule.run_pending()
    time.sleep(1)






















