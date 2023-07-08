import numpy as np
from trader import *
from collections import Counter
import datetime
import json,requests

# loading config and constants
config = json.load(open("secrets.config","r")) 
role="<@&1126499478342475807>"


# for data analysis
def mapped(i):
    if i[:2]=="00":
        return -1
    if i[:2]=="11":
        return 1
    return 0
def now_ms():
    return int(time.time()*1_000)

def get_data(tickerpair,interval,limit=1000,type="live"):
    """limit==0 for no limit
    type: live,sampledata,data
    """
    if type=="live":
        klines = get_klines_live(tickerpair,interval,limit=limit)  
        dfmpl = df_to_dfmpl(pd.DataFrame(klines)).iloc[:-1]# skips the last tick which is incomplete
    elif type=="sampledata":
        df = get_historical_df(tickerpair,interval,folder="kline_data_sample").iloc[-limit:]
        dfmpl = df_to_dfmpl(df)
    elif type=="data":
        df = get_historical_df(tickerpair,interval,folder="kline_data").iloc[-limit:]
        dfmpl = df_to_dfmpl(df)
    else:
        assert False
    return dfmpl
def get_entrys_exits(dfmpl,percentile,thres_diff):
    xvals=np.arange(len(dfmpl.Close))
    r_high_sm = dfmpl.High.rolling(14).std()/dfmpl.High.rolling(14).mean()
    r_low_sm = dfmpl.Low.rolling(14).std()/dfmpl.Low.rolling(14).mean()
    r_sm=r_low_sm*0.5+r_high_sm*0.5
    r_sm_diff = r_sm.diff()

    if not thres_diff:
        thres_diff = np.percentile(r_sm_diff.values[np.where(~np.isnan(r_sm_diff.values))],percentile)

    mkoffset = 1.01
    crossings = np.where(np.diff(r_sm_diff>thres_diff,1))[0]
    scatter = [ dfmpl.Close.iloc[i]*mkoffset if i in crossings else np.nan for i in xvals]
    crossup=np.where(np.diff((r_sm_diff>thres_diff)*1.,1)>0)[0]
    scatterup = [ dfmpl.Close.iloc[i]*mkoffset if i in crossup else np.nan for i in xvals]
    crossdn=np.where(np.diff((r_sm_diff>thres_diff)*1.,1)<0)[0]
    scatterdn = [ dfmpl.Close.iloc[i]*mkoffset if i in crossdn else np.nan for i in xvals] 

    entrys = np.where(~np.isnan(scatterup))[0]
    exits = np.where(~np.isnan(scatterdn))[0]
    return entrys,exits,dfmpl,scatterup,scatterdn,r_high_sm,r_low_sm,r_sm,r_sm_diff,thres_diff
def get_entry_signals(entrys,dfmpl):    #get all entry signal
    entry_signals = []
    for entry in entrys:
        if (entry-2)<0:
            continue
        s_1 = dfmpl.iloc[entry-2]
        s = dfmpl.iloc[entry-1]
        s1 = dfmpl.iloc[entry] 
        #values_ = [s_1.Close-s_1.Open,s.Close-s.Open]
        values_ = [s.Close-s.Open,s1.Close-s1.Open,]
        presignal = "".join([ "1"if x>0 else "0" for x in values_])
        buy=mapped(presignal)
        if buy!=0:
            entry_signals.append( (entry,buy,dfmpl.iloc[entry].name) )
    return entry_signals
def parse_signals_and_send_msg(entrys,exits,dfmpl,entry_signals,tickerpair,interval):

    # check if its new entry
    new_entry=False
    entered=False
    entry_df= None;entry_time_utc_ms=None;buy=None
    for entry,exit in zip_longest(entrys,exits,fillvalue=None):
        if exit is None: # missing exit signal, so its a new enter signal
            buy_list = [ buy for entry_, buy,_ in entry_signals if entry_==entry]
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
        strr = f"exit {tickerpair} {interval} {dfmpl.iloc[-1].Close}"
        requests.post(config["crypto-signals2"],data={"content":strr})
    elif new_entry and not entered:
        entry_time_utc_ms = entry_df.name.value//1_000_000
        xx = entry_df.Close
        strr = tickerpair+" "+ ("BUY  " if buy==1 else "SELL ")+f"{xx}" 
        strr += f" tp {xx*(1+0.01*buy):.4f} sl {xx*(1-0.005*buy):.4f}\n"
        strr += f"{entry_df.name} {role} at {str(datetime.datetime.now())}"
        requests.post(config["crypto-signals2"],data={"content":strr}) 
        entered=True  #print("*"*8,"new entry",entry_time_utc_ms) #klinetime= entry_time_utc_ms-3*3600*1_000
    else:
        strr = f"fetched {tickerpair} {interval} at {dfmpl.iloc[-1].name} at {str(datetime.datetime.now())}"
        requests.post(config["status-ping2"],data={"content":strr})
        
def get_predictions(entrys,exits,dfmpl): # need to rename this
    predict = [] # capture data
    result= [] 
    entry_exit_pairs=(entrys,exits)
    for entry,exit in zip(*entry_exit_pairs):
        if (entry-2)<0:
            continue
        s_1 = dfmpl.iloc[entry-2]
        s = dfmpl.iloc[entry-1]
        s1 = dfmpl.iloc[entry]
        s2 = dfmpl.iloc[exit]
        predict.append( (s.Close-s.Open,s1.Close-s1.Open) )
        result.append( s2.Close-s1.Close )
    pred_sign = np.sign(predict,out=np.ones_like(np.asarray(predict))*-1.,where=np.asarray(predict)!=0)
    true_sign = np.sign(result,out=np.ones_like(np.asarray(result))*-1.,where=np.asarray(result)!=0)
    input_labels = [ "".join([ "1"if x>0 else "0" for x in [*i,z]]) for i,z in zip(pred_sign,true_sign) ] 
    predict_seq = sorted(Counter(input_labels).items()) 
    predicted_result = np.asarray([ mapped(i) for i in input_labels])
    return predict,result,predict_seq,predicted_result

def get_profit_highlows_of_predictions(entrys,exits,predicted_result,dfmpl):
    entry_exit_pairs=(entrys,exits)
    profit=[] # implement backtesting for this strat
    trade_durations = []
    concated_df0=[]
    concated_df0_signal=[]
    high_low_pair = []
    for entry,exit,buy in zip(*entry_exit_pairs,predicted_result): 
        s_1 = dfmpl.iloc[entry-2]
        s = dfmpl.iloc[entry-1]
        s1 = dfmpl.iloc[entry]
        s2 = dfmpl.iloc[exit]
        if buy==0:continue #if buy==-1:continue
        gains= buy*(s2.Close-s1.Close)/(s1.Close)
        profit.append(gains)
        # collecting trade stats
        indd=dfmpl.iloc[[entry,exit]].index
        diff = indd[1].to_datetime64()-indd[0].to_datetime64()
        trade_hr = int(diff)*1e-9/3600
        trade_durations.append( trade_hr )
        concated_df0.append( dfmpl.iloc[entry-1:exit+1] )
        concated_df0_signal.append(buy)
        high_low_pair.append( (s1.Close,s2.Close,buy,
                               dfmpl.iloc[entry:exit+1].High.max(),
                               dfmpl.iloc[entry:exit+1].Low.min()) ) 
    return profit,trade_durations,concated_df0,concated_df0_signal,high_low_pair

def get_stats(dfmpl,scatterup,profit,trade_dur,lastNsamples=0): 
    
    profit1=profit[-lastNsamples:]
    ind=dfmpl.iloc[np.where(~np.isnan(scatterup))[0][np.r_[-lastNsamples,-1]]].index
    equity=[1]
    
    final_profit = 1
    for p in profit1:
        final_profit *= (1+p)
        equity.append(final_profit)
    
    wins=sum(p>0 for p in profit1)
    diff = ind[1].to_datetime64()-ind[0].to_datetime64()
    trading_days = max(int(diff)*1e-9/3600/24,1)
    gains_=final_profit*100-100
    #print(final_profit,trading_days)
    gains_per_day = np.exp(np.log(final_profit)/trading_days)*100-100
    gains_per_trade = np.exp(np.log(final_profit)/len(profit1))*100-100
    str1=f"gain% = {gains_:.2f}%"+f", avg%= {np.mean(profit1)*100:.2f}%"+"\n"+\
          f"trades={len(profit1)}, wins={wins}, win%={wins/len(profit1)*100:.2f}%"+"\n"+\
          f"days={trading_days:.3g}d, trdDur={np.mean(trade_dur[-lastNsamples:]):.3g}hr,"+\
    f" trd/d={len(profit1)/trading_days:.3g}"+"\n"+\
    f"g%/day={gains_per_day:.2f}%/d, g%/trade={gains_per_trade:.2f}%/trd"
    return str1,gains_,trading_days
def get_all_equity(profit):
    final_profit = 1
    profit1=profit
    equity=[1]
    for p in profit1:
        final_profit *= (1+p)
        equity.append(final_profit)
    return final_profit,equity

def get_hl_data(hl_pair):
    hl_data=[]
    for buy_ in [1,-1]:
        highs=[(high-ent)/ent*100 for ent,exi,buy,high,low in hl_pair if buy==buy_]
        lows=[(low-ent)/ent*100 for ent,exi,buy,high,low in hl_pair if buy==buy_]
        profit_=[buy*(exi-ent)/ent*100 for ent,exi,buy,high,low in hl_pair if buy==buy_]  
        hl_data.append((np.mean(highs),np.std(highs),
                       np.mean(lows),np.std(lows),
                        np.mean(profit_),np.std(profit_)
                       ))
    return hl_data


# for plotting


def plot_hl_ax(ax,hl_pair,hl_data,bres=0.1): #bres=0.1 # bin resolution, 0.1%    
    vals=[]
    for buy_ in [1,-1]:
        highs=[(high-ent)/ent*100 for ent,exi,buy,high,low in hl_pair if buy==buy_]
        lows=[(low-ent)/ent*100 for ent,exi,buy,high,low in hl_pair if buy==buy_]
        profit_=[buy*(exi-ent)/ent*100 for ent,exi,buy,high,low in hl_pair if buy==buy_]
        vals.append(np.asarray([highs,lows,profit_]).reshape(-1))
    vals = [v for vv in vals for v in vv]
    binminmax=max(np.abs(int(np.min(vals)/bres)*bres),np.abs(int(np.max(vals)/bres)*bres))
    bins=np.arange(-binminmax-bres/2,binminmax+bres/2,bres)

    for buy_,offset in zip([1,-1],[0,3]):
        highs=[(high-ent)/ent*100 for ent,exi,buy,high,low in hl_pair if buy==buy_]
        lows=[(low-ent)/ent*100 for ent,exi,buy,high,low in hl_pair if buy==buy_]
        profit_=[buy*(exi-ent)/ent*100 for ent,exi,buy,high,low in hl_pair if buy==buy_]
        for i,stats in enumerate([highs,lows,profit_]):
            hist ,_ = np.histogram(stats,bins=bins)
            hist=hist/max(hist)
            ax.bar(bins[1:]*0.5+bins[:-1]*0.5,hist,bottom=5-(offset+i),width=bres)
            ax.axhline(offset+i,ls="--",alpha=0.4)
    for buy_,hlp,offset in zip([1,-1],hl_data,[0,3]):
        mh,sh,ml,sl,mp,sp = hlp
        for i,(mean,std,name) in enumerate([(mh,sh,"hi"),(ml,sl,"lo"),(mp,sp,"pf")]):
            add = (f"{buy_}") if name=="pf" else ""
            strr = f"{add}{name} {mean:.2f}% $\pm${std:.2f}\n{mean-std:.2f},{mean+std:.2f}" 
            ax.text(-binminmax-bres/2,5-(offset+i)+1,strr,ha="left",va="top",alpha=0.7)
            ax.scatter( [mean-std,mean,mean+std] ,[5-(offset+i)+0.5]*3,marker="x") 
    ax.set_yticks([])
    ax.axhline(offset+i+1,ls="--",alpha=0.4)
    ax.set_ylim(0,offset+i+1)
    ax.axvline(0,ls="--",alpha=0.4)
    ax.grid(which='major', axis = 'x',alpha=0.6)
    ax.grid(which='minor', axis = 'x',alpha=0.3)
    ax.tick_params(axis="x",direction ="in")