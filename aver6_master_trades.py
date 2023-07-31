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
    pos_type = sys.argv[8]
    pos_number = int(sys.argv[9])
    cur_price = get_current_price(symbol,sell=False)
    price_format=".6g"
    sl=-0.02
    tp=0.02
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
        strr =f"`{symbol}`{emoji}, `{cur_price:{price_format}}` {pos_type} `Trd{pos_number}` {critStr}"
        buytimestr=str(datetime.datetime.now())[:-4]
        strr+=f"\n `{dfname}` (`{buytimestr}`)"
        if a1=="FILLED":# we have entered the trade
            ping(CRYPTO_SIGNALS2,f"👉Entered {strr}")
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
                    "hl_pairs":hl_pairs,"strat":"strat_tpsl3"}
        strat_data = {"cur_sl":sl,"cur_tp":tp,"slip":-0.002,"ent_sl":sl,"ent_tp":tp,
                      "strat":"strat_tpsl3","shiftSureProfit":False,"Highs":cur_price,"Lows":cur_price,"rolling_price":cur_price}

        stdmean_status="HOLD"
        stdmean_status_exited=False
        pas_status="HOLD"
        pas_strr=""
        
        while status=="HOLD": 
            cur_price = get_current_price(symbol)
            strat_data["Highs"] = max(strat_data["Highs"],cur_price)
            strat_data["Lows"] = min(strat_data["Lows"],cur_price)
            pas_status,strat_data,pas_strr = price_action_signal(enter_data,strat_data,cur_price) 
            if pas_strr[:2]=="Up": # shifting of SLTP
                timenow=str(datetime.datetime.now())[11:-4]
                strr_="🔄"+pas_status+f" `{symbol}{interval}` {emoji} {pos_type} `Trd{pos_number}`"
                strr_+=" CurPri`{cur_price:{price_format}}` "+pas_strr+f" ({timenow})"
                ping(CRYPTO_SIGNALS2,strr_)
            status ="HOLD" if ((stdmean_status=="HOLD") and (pas_status=="HOLD")) else "SELL"
            loopcounts+=1
            if status=="HOLD":
                time.sleep(5)

        # sell position
        a1,a2,a3 = market_trade(symbol,qty,buy=False,test=test)
        cur_price = get_current_price(symbol)# to simulate current sell price #TODO fix this for real sells
        exittime=str(datetime.datetime.now())[11:-4]
        if a1=="FILLED":# we have exited the trade
            change = (cur_price-enter_data['price'])/enter_data['price']
            sign = '⬆️' if change>0 else '⬇️'
            strr = f"{sign}Exited `{symbol}{interval}` {sign}{emoji},{pos_type} `Trd{pos_number}`\nCurPri`{cur_price:{price_format}}`,"
            strr+= f" entered at `{enter_data['price']:{price_format}}`, EntTime`{buytimestr}`,\n"
            strr+= f"(RESULT `{change:+.2%}`, `{qtyUSD*change:+.2f}$`) (ExitTime`{exittime}`)\n"
            highfrac=(strat_data['Highs']-enter_data['price'])/enter_data['price']
            lowfrac=(strat_data['Lows']-enter_data['price'])/enter_data['price']
            strr+= f"High `{strat_data['Highs']:{price_format}}` (`{highfrac:.2%}`), Low `{strat_data['Lows']:{price_format}}` (`{lowfrac:.2%}`)\n"
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
                            dfname,ent_time,exittime,reason,pos_type,critStr)
        else:
            ping(ERROR_PING2,f"EXIT ERROR {emoji} {symbol}{interval} {ALEXPING}")
            raise
    else:
        ping(CRYPTO_SIGNALS2,f"Entry price too high, skipping  trade. {symbol}{interval} curr`{cur_price:{price_format}}`")
except Exception as e:
    ping(ERROR_PING2,f"error  {symbol}{interval} {ALEXPING}"+str(e))
    raise