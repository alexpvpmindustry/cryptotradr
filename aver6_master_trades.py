import datetime,time,sys
from aver6_trader import get_current_price,market_trade,price_action_signal, read_signal,log_trade_results 
from disc_api import ALEXPING, ERROR_PING2, ping,SIGNALROLE,CRYPTO_SIGNALS2,get_random_emoji,CRYPTO_LOGS2

symbol=""
interval=""
        
try:
    symbol = sys.argv[1]+"USDT"
    qtyUSD = float(sys.argv[2])
    dfname = sys.argv[3]
    test   = sys.argv[4]=="TEST"
    closeprice=float(sys.argv[5])
    criteria_gain=float(sys.argv[6])
    criteria_pullback=float(sys.argv[7])

    cur_price = get_current_price(symbol,sell=False)
    price_format=".6g"
    sl=-0.02
    tp=0.048
    hl_pairs=None
    interval="5m"
    passed_criteria = (criteria_gain>0.025) and (criteria_pullback<0.3)
    passed="critPASS" if passed_criteria else "critFAIL(2.5%&30%)"
    critStr = f"{passed} critGain=`{criteria_gain:.2%}`, critPlBk=`{criteria_pullback:.2%}`"
    buytimestr=""

    if (cur_price-closeprice)/closeprice<0.009: 
        qty = qtyUSD/cur_price
        a1,a2,a3 = market_trade(symbol,qty,buy=True,test=test)
        emoji=get_random_emoji()
        strr =f"`{symbol}{emoji}`, `{cur_price:{price_format}}` {critStr}"
        buytimestr=str(datetime.datetime.now())[:-4]
        strr+=f"\n `{dfname}` (`{buytimestr}`)"
        if a1=="FILLED":# we have entered the trade
            ping(CRYPTO_SIGNALS2,f"Entered {strr}")
        elif a1=="INSUFFICIENTBALANCE":
            ping(CRYPTO_SIGNALS2,f"INSUFFICIENTBALANCE for entering {strr}")
            assert False
        else:
            ping(CRYPTO_SIGNALS2,f"ENTER ERROR {symbol}{emoji} {SIGNALROLE}")
            assert False
        # continous loop until exit or sell signal is recieved
        status="HOLD"
        loopcounts=1

        ent_time=str(datetime.datetime.now())[:-4].replace(" ","_")
        enter_data = {"price":cur_price,"sl":sl,"tp":tp,"dfname":dfname,"ent_time":ent_time,
                    "hl_pairs":hl_pairs,"strat":"strat_tpsl1"}
        strat_data = {"cur_sl":sl,"cur_tp":tp,"slip":-0.002,"ent_sl":sl,"ent_tp":tp,
                      "strat":"strat_tpsl2","shiftSureProfit":False}

        stdmean_status="HOLD"
        stdmean_status_exited=False
        pas_status="HOLD"
        pas_strr=""
        while status=="HOLD": 
            cur_price = get_current_price(symbol) 
            pas_status,strat_data,pas_strr = price_action_signal(enter_data,strat_data,cur_price)
            ## start of update routine
            # updated=False;update_list=[] 
            # update_list.append(pas_strr[:6])
            # while (pas_strr[:2]=="Up"):
            #     # repeat until its not up anymore, then take the prev sl and tp
            #     prev_strat_data = strat_data.copy()
            #     prev_pas_status = pas_status
            #     prev_pas_strr = pas_strr
            #     pas_status,strat_data,pas_strr = price_action_signal(enter_data,strat_data,cur_price)
            #     if pas_strr[:2]=="Up":
            #         updated=True
            #         update_list.append(pas_strr[:6]) 
            # if updated:
            #     pas_status,strat_data,pas_strr = prev_pas_status,prev_strat_data.copy(),prev_pas_strr
            #     pas_strr = " ".join(update_list[:-1])+" "+pas_strr
            ## end of update routine
            if pas_strr[:2]=="Up": # shifting of SLTP
                ping(CRYPTO_SIGNALS2,pas_status+f" `{symbol}{interval}` {emoji} `{cur_price:{price_format}}` "+pas_strr)
            if False and loopcounts%6==0 and not stdmean_status_exited:# read exit status (remove the False and for effect)
                stdmean_status=read_signal(symbol,interval)
                #if stdmean_status != "EXIT":
                #    stdmean_status = "HOLD"
                if stdmean_status == "EXIT": #checks if we are exiting becos of signal
                    log_trade_results(symbol,interval,enter_data['price'],cur_price, dfname,ent_time,str(datetime.datetime.now())[:-4],reason="exit_from_read_signal")
                    change = (cur_price-enter_data['price'])/enter_data['price']
                    sign = '⬆️' if change>0 else '⬇️'
                    strr = f"Exit🪃Signal {symbol}{interval} {sign}{emoji} `{cur_price:{price_format}}` "
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
        cur_price = get_current_price(symbol)# to simulate current sell price #TODO fix this for real sells
        exittime=str(datetime.datetime.now())[:-4]
        if a1=="FILLED":# we have exited the trade
            change = (cur_price-enter_data['price'])/enter_data['price']
            sign = '⬆️' if change>0 else '⬇️'
            strr = f"Exited `{symbol}{interval}` {sign}{emoji}, `{cur_price:{price_format}}`,"
            strr+= f" entered at `{enter_data['price']:{price_format}}`, `{buytimestr}`,\n"
            strr+= f"(`{exittime}`) "
            strr+= f"size=`${qtyUSD}` (RESULT `{change:+.2%}`, `{qtyUSD*change:+.2f}$`)\n"
            strr+= f"{critStr}\n"
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
            ping(ERROR_PING2,f"EXIT ERROR {emoji} {symbol}{interval} {ALEXPING}")
            raise
    else:
        ping(CRYPTO_SIGNALS2,f"Entry price too high, skipping  trade. {symbol}{interval} curr`{cur_price:{price_format}}`")
except Exception as e:
    ping(ERROR_PING2,f"error  {symbol}{interval} {ALEXPING}"+str(e))
    raise