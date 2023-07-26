
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
        self.pos_number=0
    def fetch_24hr_data(self,idd): # do this every 1 to 4 th minute
        
        if not self.firstrun:
            time.sleep(0.15*idd)
            time.sleep(2*60)
        else:
            time.sleep(0.05*idd)
        start_time = get_time_before(15)#24*60)
        df0 = get_data(subset_symbols[idd]+"USDT","5m",limit=3,start_time=start_time-3600_000*24,offset=self.offset)
        self.fetched_24hr_data[idd]=df0.copy()
        self.fetched_24hr_data_sync[idd]+=1
        if idd in [0,len(subset_symbols)-1]:
            if not self.firstrun:
                self.consolelog(f"0> fetch 24hr data{idd}")
            else:
                self.consolelog(f"0>0 fetch 24hr data{idd}")
    def fetch_new_data(self,idd): # do this every 4:10 th minute
        time.sleep(0.05*idd) 
        if not self.firstrun:
            time.sleep( 4*60+43)
        else:
            time.sleep(27) # will end at 4:45 seconds
        start_time = get_time_before(15)#24*60)
        df = get_data(subset_symbols[idd]+"USDT","5m",limit=3,start_time=start_time,offset=self.offset)
        self.fetched_fresh_all_data[idd]=df.copy()
        self.fetched_fresh_all_data_sync[idd]+=1
        if idd in [0,len(subset_symbols)-1]:
            if not self.firstrun:
                self.consolelog(f"1> fetch temp data{idd}")
            else:
                self.consolelog(f"1>0 fetch temp data{idd}")
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

        self.top10current = [subset_symbols[iii] for iii in self.top10symbols_temp[:10]] 
        opened_pos = False
        symbol_id = self.top10symbols_temp[0]
        if not self.top10symbols_prev[0]==self.top10symbols_temp[0]:
            # check for criteria, and then enter position
            pos_change=10
            if symbol_id in self.top10symbols_prev:
                pos_change = np.where(self.top10symbols_prev==symbol_id)[0][0]-currpos
            opened_pos = self.checkCriteria_then_openPos(symbol_id,pos_type=f"TopPos_Jump{pos_change}")
        # check for other possible opening for positions
        for currpos,currsymbol in enumerate(self.top10symbols_temp): # ignore the first one
            if currpos==0: continue 
            pos_change=10
            if currsymbol in self.top10symbols_prev:
                pos_change = np.where(self.top10symbols_prev==currsymbol)[0][0]-currpos
            if pos_change>1: # jumps by at least 2 positions
                opened_pos = opened_pos or self.checkCriteria_then_openPos(currsymbol,pos_type=f"JUMP{pos_change}POS")
        #if not opened_pos:# no change in top position, wait for next iteration
        synced = self.checksync()
        top10current = ",".join(self.top10current)
        ping(STATUS_PING2,f"{self.ddtn_str()},sync{synced},TOPsym {top10current} ,opos={opened_pos}")
        self.consolelog("fin signals")

    def checkCriteria_then_openPos(self, symbol_id,pos_type):
        criteria_passed = False
        criteria_str = ""
        symbol = self.subset_symbols[symbol_id]
        df=self.fetched_fresh_all_data[symbol_id]
        opened_pos=False
        loc0=2
        gain=(df.iloc[loc0].Close-df.iloc[loc0].Open)/df.iloc[loc0].Open
        if gain>=0.005: # was 0.03
            pullback = (df.iloc[loc0].High - df.iloc[loc0].Close)/(df.iloc[loc0].High - df.iloc[loc0].Open)
            criteria_str =f",pb{pullback:.2%}."
            if pullback <=0.5: # was 0.3
                criteria_passed=True
        if criteria_passed: 
            self.enter_position(symbol,df.iloc[loc0].Close,df.iloc[loc0].name,gain,pullback,pos_type)
            ping(CRYPTO_SIGNALS2,f"ENTERSIGNAL({pos_type}) `{symbol}` `{df.iloc[loc0].Close:{self.price_format}}` `{self.ddtn_str()}`")
            opened_pos=True
        else: # did not pass criteria
            criteria_str= f"gain{gain:.2%}"+criteria_str
            strr=""
            if pos_type[:4]=="TopP":
                strr=f"Signal failed: {pos_type} prev `{self.subset_symbols[self.top10symbols_prev[0]]}`, curr `{symbol}`,critFail,{criteria_str}"
            if pos_type[:4]=="JUMP":
                strr=f"Signal failed: {pos_type} ,critFail,{criteria_str}"
            ping(CRYPTO_SIGNALS2,strr)
        return opened_pos
    def enter_position(self,symbol,closeprice,dfname,criteria_gain,criteria_pullback,pos_type):
        xx = closeprice
        strr = f"`{symbol}` BUY `{xx}`" 
        strr += f" tp `{xx*(1+self.tp):{self.price_format}}` sl `{xx*(1+self.sl):{self.price_format}}`\n"
        strr += f"`{dfname}` (`{self.ddtn_str()}`) {SIGNALROLE}"
        write_signal(symbol,self.interval,signal="ENTER",closeprice=xx,dfname=dfname)
        # execute trading algo
        enterdftime = str(dfname).replace(" ","_")
        cmd = ["python","aver6_master_trades.py",symbol,"15",f"{enterdftime}","TEST",f"{xx:{self.price_format}}",f"{criteria_gain:.4f}",
               f"{criteria_pullback:.4f}",f"{pos_type}",f"{self.pos_number}"]
        cmd = " ".join(cmd)
        subprocess.Popen( cmd , shell=True)
        self.pos_number+=1
        ping(CRYPTO_SIGNALS2,strr)
    def consolelog(self,strr=""): 
        print(f"{self.ddtn_str()}, {strr}") 
    def ddtn_str(self):
        return str(datetime.datetime.now())[:-4]
    def get_signal_with_warnings(self):# execute this at :55 seconds
        # started at 1:50 seconds
        try:
            if not self.firstrun:
                self.consolelog(f"2> sleeping for signal,{ 5+5*60}secs")
                time.sleep(5+5*60) # this is more than 5mins to skip the first one, this works normally afterwards
            else:
                self.consolelog(f"2>0 firstrun sleeping for signal,{ 53}secs")
                time.sleep(53)
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
def first_run(): #TODO make the logic for firstrun
    print(f"this is a first run at {datetime.datetime.now()}")
    for idd in range(len( subset_symbols )):
        run_threaded(s.fetch_24hr_data,idd)
        run_threaded(s.fetch_new_data,idd)
    run_threaded_no_data(s.get_signal_with_warnings) 
min_delay = 60+35
if delay>min_delay:
    print(f"first delay is very long, so do a run first, waiting for {delay-min_delay} secs , {datetime.datetime.now()}")
    # delay is very long, so do a run first.......
    time.sleep(delay-min_delay)
    # time now should be at 4:00
    print(f"time now should be 4:00, {datetime.datetime.now()}")
    s.firstrun=True
    first_run()
    print(f"done threaded first run, {datetime.datetime.now()}")
    delay=min_delay
print(f"waiting for {delay} secs, {datetime.datetime.now()}")
time.sleep(delay)
# now we are at X:35 minutes where X is a multiple of 5
s.firstrun=False

print(f"scheduling at {datetime.datetime.now()}")
for idd in range(len( subset_symbols )):
    schedule.every(intvl).minutes.at(":50").do(run_threaded,s.fetch_24hr_data,idd)
    schedule.every(intvl).minutes.at(":50").do(run_threaded,s.fetch_new_data,idd)
schedule.every(intvl).minutes.at(":50").do(run_threaded_no_data,s.get_signal_with_warnings)
print(f"scheduled algos {datetime.datetime.now()}")
# sleep for 3min and 24 seconds to make another data run......
# but need to use data arguments for custom delays # TODO 
while True:
    schedule.run_pending()
    time.sleep(1)






















