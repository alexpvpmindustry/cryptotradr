import datetime,time,sys
from trader import get_current_price,price_action_signal, read_signal,log_trade_results
import json
from disc_api import ping,SIGNALROLE,CRYPTO_SIGNALS2,get_random_emoji
from trader import market_trade 

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

#enter trade:
symbol = tickerpair
qtyUSD = float(sys.argv[2])
dfname = sys.argv[3]
test   = (sys.argv[4]=="TEST")
closeprice=float(sys.argv[5])
cur_price = get_current_price(symbol,sell=False)
if (cur_price-closeprice)/closeprice<0.009: 
    qty = qtyUSD/cur_price
    a1,a2,a3 = market_trade(symbol,qty,buy=True,test=test)
    emoji=get_random_emoji()
    if a1=="FILLED":# we have entered the trade
        ping(CRYPTO_SIGNALS2,f"Entered {symbol}{interval} pc{param_choice}{emoji}, `{cur_price:.4f}`,\n `{dfname}` (`{datetime.datetime.now()}`)")
    else:
        ping(CRYPTO_SIGNALS2,f"ENTER ERROR pc{param_choice}{emoji} {SIGNALROLE}")
        assert False
    # continous loop until exit or sell signal is recieved
    status="HOLD"
    loopcounts=0

    ent_time=str(datetime.datetime.now())[:-4].replace(" ","_")
    enter_data = {"price":cur_price,"sl":sl,"tp":tp,"dfname":dfname,"ent_time":ent_time,
                "hl_pairs":hl_pairs,"strat":"strat_tpsl1"}
    strat_data = {"cur_sl":sl,"cur_tp":tp,"slip":-0.002,"ent_sl":sl,"ent_tp":tp,"strat":"strat_tpsl1"}

    stdmean_status="HOLD"
    pas_status="HOLD"
    pas_strr=""
    while status=="HOLD":
        # get current price
        cur_price = get_current_price(symbol)
        # get price_action_signal
        pas_status,strat_data,pas_strr = price_action_signal(enter_data,strat_data,cur_price)
        if pas_strr[:2]=="Up": # shifting of SLTP
            ping(CRYPTO_SIGNALS2,pas_status+f" {symbol}{interval} pc{param_choice}{emoji} `{cur_price:.4f}` "+pas_strr)
        if False and loopcounts%10==0:# read exit status (remove the False and for effect)
            stdmean_status=read_signal(symbol,interval)
            if stdmean_status != "EXIT":
                stdmean_status = "HOLD"
        status ="HOLD" if ((stdmean_status=="HOLD") and (pas_status=="HOLD")) else "SELL"
        loopcounts+=1
        if status=="HOLD":
            time.sleep(5)

    # sell position
    a1,a2,a3 = market_trade(symbol,qty,buy=False,test=test)
    exittime=str(datetime.datetime.now())[:-4]
    if a1=="FILLED":# we have exited the trade
        change = (cur_price-enter_data['price'])/enter_data['price']
        sign = '⬆️' if change>0 else '⬇️'
        strr = f"Exited {symbol}{interval} {sign}pc{param_choice}{emoji}, `{cur_price:.4f}`,"
        strr+= f" entered at `{enter_data['price']:.4f}`,\n"
        strr+= f"(`{exittime}`) "
        strr+= f"size=`${qtyUSD}` (`{change*100:.2f}%`, `{qtyUSD*change:.2f}$`)\n"
        reason=""
        if pas_status=="SELL":
            strr+= f"Reason: {pas_strr}\n"
            reason+=f"Reason: {pas_strr}"
        if stdmean_status!="HOLD":
            strr+= "Reason: Exit signal from PAS\n"
            reason+="Reason: Exit signal from PAS"
        ping(CRYPTO_SIGNALS2,strr)
        log_trade_results(symbol,interval,enter_data['price'],cur_price,
                        dfname,ent_time,exittime,reason)
    else:
        ping(CRYPTO_SIGNALS2,f"EXIT ERROR pc{param_choice}{emoji} {SIGNALROLE}")
        assert False
else:
    ping(CRYPTO_SIGNALS2,f"Entry price too high, skipping pc{param_choice} trade. {symbol}{interval} curr`{cur_price:.4f}`")