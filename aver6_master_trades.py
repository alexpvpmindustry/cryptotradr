import datetime,time,sys
import traceback
from aver6_trader import get_current_price,market_trade,price_action_signal, read_signal,log_trade_results
from aver6_trader import client as cc
from disc_api import ALEXPING, ERROR_PING2, ping,SIGNALROLE,CRYPTO_SIGNALS2,get_random_emoji,CRYPTO_LOGS2
import time
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
    # get precision from exchange
    info = cc.get_exchange_info()
    pricePrecision=8
    for idxx,symbol_ in enumerate(info["symbols"]):
        if symbol == info["symbols"][idxx]["symbol"]:
            pricePrecision = info['symbols'][idxx]['quotePrecision']
    
    #
    sl=-0.005
    tp=0.015
    hl_pairs=None
    interval="1m"
    passed_criteria = (criteria_gain>0.025) and (criteria_pullback<0.3)
    passed="critPASS" if passed_criteria else "critFAIL(2.5%&30%)"
    critStr = "_" #no use for this f"{passed} critGain=`{criteria_gain:.2%}`, critPlBk=`{criteria_pullback:.2%}`"
    buytimestr=""

    if (cur_price-closeprice)/closeprice<0.009: 
        qty = qtyUSD/cur_price
        qty = "{:0.0{}f}".format(qty, pricePrecision)
        print("qty",qty,"test",test)
        a1,a2,a3 = market_trade(symbol,qty,buy=True,test=test)
        if not test and a1=="FILLED":
            cur_price=float(a2[0]["price"])
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
        enter_time_time = time.time()
        # continous loop until exit or sell signal is recieved
        status="HOLD"
        loopcounts=1

        ent_time=str(datetime.datetime.now())[:-4].replace(" ","_")
        enter_data = {"price":cur_price,"sl":sl,"tp":tp,"dfname":dfname,"ent_time":ent_time,
                    "hl_pairs":hl_pairs,"strat":"strat_tpsl3"}
        strat_data = {"cur_sl":sl,"cur_tp":tp,"slip":-0.002,"ent_sl":sl,"ent_tp":tp,
                      "strat":"strat_tpsl3","shiftSureProfit":False,"Highs":cur_price,"Lows":cur_price,"rolling_price":cur_price}

        nextcandle_status="HOLD"
        nextcandle_status_exited=False
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
                strr_+=f" CurPri`{cur_price:{price_format}}` "+pas_strr+f" ({timenow})"
                ping(CRYPTO_SIGNALS2,strr_)
            if (time.time() - enter_time_time)/60 >1:# more than 1minute has passed!
                nextcandle_status="SELL"
            status ="HOLD" if ((nextcandle_status=="HOLD") and (pas_status=="HOLD")) else "SELL"
            loopcounts+=1
            if status=="HOLD":
                time.sleep(5)

        # sell position
        qty = qty*0.9985 # sell off the remaining 99.85% ... 
        # 0.1% is for transaction fee 0.05% is for safety
        a1,a2,a3 = market_trade(symbol,qty,buy=False,test=test)
        if test:
            cur_price = get_current_price(symbol)
        else:
            cur_price = float(a2[0]["price"]) # but this should actually be the weighted average
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
            if nextcandle_status!="HOLD":
                strr+= "Reason: Exit signal from next candle\n"
                reason+="Reason: Exit signal from next candle"
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
    strr=traceback.format_exc()
    ping(ERROR_PING2,f"error 108 {symbol}{interval} {ALEXPING} str{str(e)} tb: {strr}")
    raise