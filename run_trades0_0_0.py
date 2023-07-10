
import sys 
from glob import glob
import time
from itertools import zip_longest
import json,requests,datetime,schedule

from trader import write_signal 
from funcs import get_data,get_entrys_exits,get_entry_signals,read_signal
from disc_api import ping,STATUS_PING2,SIGNALROLE,CRYPTO_SIGNALS2

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
#     klines = get_klines(tickerpair,interval,limit=100)
#     dfmpl = klines_to_dfmpl(klines).iloc[:-1]
#     xvals=np.arange(len(dfmpl.Close))
#     rolling_high_std_mean = dfmpl.High.rolling(14).std()/dfmpl.High.rolling(14).mean()
#     rolling_low_std_mean = dfmpl.Low.rolling(14).std()/dfmpl.Low.rolling(14).mean()
#     rolling_std_mean=rolling_low_std_mean*0.5+rolling_high_std_mean*0.5
#     r_std_mean_diff = rolling_std_mean.diff() 

#     mkoffset = 1.01
#     crossings = np.where(np.diff(r_std_mean_diff>thres_diff,1))[0]
#     scatter = [ dfmpl.Close.iloc[i]*mkoffset if i in crossings else np.nan for i in xvals]
#     crossup=np.where(np.diff((r_std_mean_diff>thres_diff)*1.,1)>0)[0]
#     scatterup = [ dfmpl.Close.iloc[i]*mkoffset if i in crossup else np.nan for i in xvals]
#     crossdn=np.where(np.diff((r_std_mean_diff>thres_diff)*1.,1)<0)[0]
#     scatterdn = [ dfmpl.Close.iloc[i]*mkoffset if i in crossdn else np.nan for i in xvals] 

#     entrys = np.where(~np.isnan(scatterup))[0]
#     exits = np.where(~np.isnan(scatterdn))[0]
    dfmpl = get_data(tickerpair,interval,limit=100,type="live")
    entrys,exits,sc_up,sc_dn,r_high_sm,r_low_sm,r_sm,r_sm_diff,thres_diff = get_entrys_exits(dfmpl,percentile,thres_diff)
    #get all entry signal
    entry_signals = get_entry_signals(entrys,dfmpl,onlybuy=True)
#     entry_signals = []
#     for entry in entrys:
#         if (entry-2)<0:
#             continue
#         s_1 = dfmpl.iloc[entry-2]
#         s = dfmpl.iloc[entry-1]
#         s1 = dfmpl.iloc[entry] 
#         values_ = [s_1.Close-s_1.Open,s.Close-s.Open] # need to check this
#         presignal = "".join([ "1"if x>0 else "0" for x in values_])
#         buy=mapped(presignal)
#         if buy==1:#if buy!=0:
#             entry_signals.append( (entry,buy) )
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
    if new_entry:
        assert buy==1
    if new_entry and entered:
        #print("hold")
        write_signal(tickerpair,interval,signal="HOLD",closeprice=dfmpl.iloc[-1].Close,dfname=dfmpl.iloc[-1].name) 
    elif not new_entry and entered:
        #print("exit trade now")
        entered=False
        strr = f"exit `{tickerpair}` `{interval}` `{dfmpl.iloc[-1].Close}`"
        strr+= f"`{dfmpl.iloc[-1].name}` (`{str(datetime.datetime.now())}`) {role}"
        write_signal(tickerpair,interval,signal="EXIT",closeprice=dfmpl.iloc[-1].Close,dfname=dfmpl.iloc[-1].name) 
        ping("CRYPTO_SIGNALS2",strr)#requests.post(config["crypto-signals2"],data={"content":strr})
    elif new_entry and not entered:
        entry_time_utc_ms = entry_df.name.value//1_000_000
        xx = entry_df.Close
        strr = f"`{tickerpair}` "+ ("BUY  " if buy==1 else "SELL ")+f"`{xx}`" 
        strr += f" tp `{xx*(1+0.01*buy):.4f}` sl `{xx*(1-0.005*buy):.4f}`\n"
        strr += f"`{entry_df.name}` (`{str(datetime.datetime.now())}`) {role}"
        write_signal(tickerpair,interval,signal="ENTER",closeprice=dfmpl.iloc[-1].Close,dfname=dfmpl.iloc[-1].name)
        # execute trading algo
        enterdftime = str(dfmpl.iloc[-1].name).replace(" ","_")
        cmd = ["python","master_trades.py",param_choice,"15",f"{enterdftime}","TEST"]
        subprocess.Popen( cmd , shell=True)
        ping("CRYPTO_SIGNALS2",strr)#requests.post(config["crypto-signals2"],data={"content":strr})
        entered=True
    else:
        strr = f"fetched `{tickerpair}` `{interval}` at `{dfmpl.iloc[-1].name}`"
        strr+= f"(`{str(datetime.datetime.now())}`)"
        ping("STATUS_PING2",strr)#requests.post(config["status-ping2"],data={"content":strr})
    ddtn=datetime.datetime.now()
    print(f"last ran:{ddtn}")
print("starting")
intvl = int(interval.split("m")[0]); ddtn=datetime.datetime.now()
delay = (intvl-1-ddtn.minute%intvl)*60+(60-ddtn.second+12) # 12 seconds after 
time.sleep(delay)
schedule.every(intvl).minutes.at(":02").do(get_signal) # run this at 22:30:04 
while True:
    schedule.run_pending()
    time.sleep(1)























