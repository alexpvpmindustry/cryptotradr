import datetime,time,sys
from trader import get_current_price,market_trade,price_action_signal, read_signal,log_trade_results
import json
from disc_api import ALEXPING, ERROR_PING2, ping,SIGNALROLE,CRYPTO_SIGNALS2,get_random_emoji,CRYPTO_LOGS2

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
try:
    if (cur_price-closeprice)/closeprice<0.009: 
        qty = qtyUSD/cur_price
        a1,a2,a3 = market_trade(symbol,qty,buy=True,test=test)
        emoji=get_random_emoji()
        strr=f"{symbol}{interval} pc{param_choice}{emoji}, `{cur_price:.4f}`,\n `{dfname}` (`{datetime.datetime.now()}`)"
        if a1=="FILLED":# we have entered the trade
            ping(CRYPTO_SIGNALS2,f"Entered {strr}")
        elif a1=="INSUFFICIENTBALANCE":
            ping(CRYPTO_SIGNALS2,f"INSUFFICIENTBALANCE for entering {strr}")
            assert False
        else:
            ping(CRYPTO_SIGNALS2,f"ENTER ERROR pc{param_choice}{emoji} {SIGNALROLE}")
            assert False
        # continous loop until exit or sell signal is recieved
        status="HOLD"
        loopcounts=1

        ent_time=str(datetime.datetime.now())[:-4].replace(" ","_")
        enter_data = {"price":cur_price,"sl":sl,"tp":tp,"dfname":dfname,"ent_time":ent_time,
                    "hl_pairs":hl_pairs,"strat":"strat_tpsl1"}
        strat_data = {"cur_sl":sl,"cur_tp":tp,"slip":-0.002,"ent_sl":sl,"ent_tp":tp,"strat":"strat_tpsl1"}

        stdmean_status="HOLD"
        stdmean_status_exited=False
        pas_status="HOLD"
        pas_strr=""
        while status=="HOLD":
            # get current price
            cur_price = get_current_price(symbol)
            # get price_action_signal
            pas_status,strat_data,pas_strr = price_action_signal(enter_data,strat_data,cur_price)
            ## start of update routine
            updated=False;update_list=[] 
            update_list.append(pas_strr[:6])
            while (pas_strr[:2]=="Up"):
                # repeat until its not up anymore, then take the prev sl and tp
                prev_strat_data = strat_data.copy()
                prev_pas_status = pas_status
                prev_pas_strr = pas_strr
                pas_status,strat_data,pas_strr = price_action_signal(enter_data,strat_data,cur_price)
                if pas_strr[:2]=="Up":
                    updated=True
                    update_list.append(pas_strr[:6]) 
            if updated:
                pas_status,strat_data,pas_strr = prev_pas_status,prev_strat_data.copy(),prev_pas_strr
                pas_strr = " ".join(update_list[:-1])+" "+pas_strr
            ## end of update routine
            if pas_strr[:2]=="Up": # shifting of SLTP
                ping(CRYPTO_SIGNALS2,pas_status+f" {symbol}{interval} pc{param_choice}{emoji} `{cur_price:.4f}` "+pas_strr)
            if loopcounts%6==0 and not stdmean_status_exited:# read exit status (remove the False and for effect)
                stdmean_status=read_signal(symbol,interval)
                #if stdmean_status != "EXIT":
                #    stdmean_status = "HOLD"
                if stdmean_status == "EXIT": #checks if we are exiting becos of signal
                    log_trade_results(symbol,interval,enter_data['price'],cur_price, dfname,ent_time,str(datetime.datetime.now())[:-4],reason="exit_from_read_signal")
                    change = (cur_price-enter_data['price'])/enter_data['price']
                    sign = '⬆️' if change>0 else '⬇️'
                    strr = f"ExitSignal🪃 {symbol}{interval} {sign}pc{param_choice}{emoji} `{cur_price:.4f}` "
                    strr+= f"size=`${qtyUSD}` (`{change*100:.2f}%`, `{qtyUSD*change:.2f}$`)\n"
                    ping(CRYPTO_LOGS2,strr)
                    stdmean_status_exited=True
                stdmean_status = "HOLD" # reset this signal since we are not using it.
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
            ping(CRYPTO_LOGS2,strr)
            log_trade_results(symbol,interval,enter_data['price'],cur_price,
                            dfname,ent_time,exittime,reason)
        else:
            ping(ERROR_PING2,f"EXIT ERROR pc{param_choice}{emoji} {tickerpair}{interval} {ALEXPING}")
            raise
    else:
        ping(CRYPTO_SIGNALS2,f"Entry price too high, skipping pc{param_choice} trade. {symbol}{interval} curr`{cur_price:.4f}`")
except Exception as e:
    ping(ERROR_PING2,f"error pc{param_choice} {tickerpair}{interval} {ALEXPING}"+str(e))
    raise