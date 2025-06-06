
#import csv
import json,datetime,requests,time
import pandas as pd
from glob import glob
from binance.client import Client
from binance.exceptions import BinanceAPIException

with open("secrets.config","r") as f:
    config = json.load(f)
bin_api_key=config["bin_api_key"]
bin_api_secr=config["bin_api_secr"]


base_url = 'https://api.binance.com' 
price_format=".6g"
# getting data
def get_klines_live(symbol, interval='1h', start_time=None, end_time=None, limit=500):
    endpoint = '/api/v3/klines'
    url = base_url + endpoint
    params = {'symbol': symbol,'interval': interval,'limit': limit}
    if start_time:
        params['startTime'] = start_time
    if end_time:
        params['endTime'] = end_time
    response = requests.get(url, params=params)
    counts=0
    while (response.status_code !=200):
        time.sleep(5)
        response = requests.get(url, params=params)
        counts+=1
        if counts>10:
            break
    if response.status_code == 200:
        klines_data = response.json()
        klines = []
        for kline in klines_data:
            klines.append({
                'open_time': kline[0],
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[5]),
                'close_time': kline[6],
                'quote_asset_volume': float(kline[7]),
                'number_of_trades': kline[8],
                'taker_buy_base_asset_volume': float(kline[9]),
                'taker_buy_quote_asset_volume': float(kline[10]),
                'ignore': kline[11]
            })

        return klines
    else:
        print(f'Error: {response.status_code}',end="")
        raise ValueError(f'line 52 Error: {response.status_code}, counts={counts}')
def df_to_dfmpl(df,offset=3600*3*1e3):
    try:
        dfmpl = df[["open_time","open","high","low","close","volume"]]
    except KeyError:
        raise KeyError(f"keyerror here, df is {str(df)}")
    dfmpl = dfmpl.rename(columns={"open_time":"Date","open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"})
    dfmpl=dfmpl.set_index("Date")
    dfmpl.index = pd.to_datetime(dfmpl.index+offset,unit="ms")
    return dfmpl
def get_historical_df(tickerpair,interval,folder="kline_data_sample"):
    df = [pd.read_csv(g) for g in sorted(glob(f"{folder}\\{tickerpair}/*")) if f"_{interval}.csv" in g]
    df = pd.concat(df, ignore_index=True).drop_duplicates().reset_index(drop=True)
    return df

# doing actual trades
client = Client(bin_api_key, bin_api_secr)

def get_current_price(symbol,sell=True):
    data = client.get_order_book(symbol=symbol,limit=1)
    # current_price=float(data["bids"][0][0])*0.5+float(data["asks"][0][0])*0.5
    if sell:
        current_price=float(data["bids"][0][0]) # price for selling right now
    else:
        current_price=float(data["asks"][0][0]) # price for selling right now
    return current_price
def market_trade(symbol,quantity,buy=True,test=True):
    if test: #todo: just get the current price
        return ("FILLED",[{'price': '97.89000000','qty': '0.15000000',
                          'commission': '0.01468350','commissionAsset': 'TUSD',
                          'tradeId': 1141128}],"")
    else:
        try:
            if buy:
                c=client.order_market_buy(symbol=symbol,quantity=quantity)
                return c["status"],c["fills"],c
            else:
                c=client.order_market_sell(symbol=symbol,quantity=quantity)
                return c["status"],c["fills"],c
        except BinanceAPIException as e:
            if "Account has insufficient balance for requested action." in str(e):
                return "INSUFFICIENTBALANCE",None,None
            else:
                raise Exception("nani?") from e

# trading strats

def strat_tpsl2(enter_data,strat_data,cur_price):# only HOLD or SELL
    # strat_data = {"cur_sl":sl,"cur_tp":tp,"slip":-0.002,"ent_sl":sl,"ent_tp":tp,"strat":"strat_tpsl1"}
    enter_price = enter_data["price"]
    if cur_price < ((1+strat_data["cur_sl"])*enter_price ): 
        return "SELL",strat_data,f"StopLoss{strat_data['cur_sl']:.2%}"
    elif cur_price > ((1+strat_data["cur_tp"])*enter_price ): 
        return "SELL",strat_data,f"TakeProf{strat_data['cur_tp']:.2%}"
    # strats to shrink tp and sl
    width=enter_data["tp"]-enter_data["sl"] # 4%, +-2%
    #print("width",width)
    strat_status="In SLTP"

    if (not strat_data["shiftSureProfit"]) and (cur_price > ( 1.01*enter_price )): # if more than 1% gain from enterprice, move sltp
        strat_status = "Up1%StopLoss"
        strat_data["cur_sl"] = 0.005
        strat_data["cur_tp"] = 0.045
        strat_data["shiftSureProfit"]=True
    elif cur_price > ( (1+strat_data["cur_sl"]+width*0.55)*enter_price ): # shifts up by 0.55*4%-2% =0.2% from center point
        strat_data["cur_sl"] = strat_data["cur_sl"]+width*0.06 # increases 0.24% = 4%*0.06
        strat_data["cur_tp"] = strat_data["cur_tp"]+width*0.06 # increases 0.24% = 4%*0.06
        strat_status = "UpSlow"
    str1=f"SL`{enter_price*(1+strat_data['cur_sl']):{price_format}}`,"
    str1+=f"TP`{enter_price*(1+strat_data['cur_tp']):{price_format}}`"
    str2=f"(`{strat_data['cur_sl']:+.2%}`,`{(cur_price-enter_price)/enter_price:+.2%}`,`{strat_data['cur_tp']:+.2%}`)"
    str3=f"\nNxtlvl: `{(1+strat_data['cur_sl']+width*0.55)*enter_price:{price_format}}`,"
    str4=f"(`{(strat_data['cur_sl']+width*0.55):+.2%}`)" 
    str5=f"width={width:.2%}"
    return "HOLD",strat_data,f"{strat_status} {str1} {str2}{str3}{str4}, {str5}"
def strat_tpsl3(enter_data,strat_data,cur_price):# only HOLD or SELL
    # strat_data = {"cur_sl":sl,"cur_tp":tp,"slip":-0.002,"ent_sl":sl,"ent_tp":tp,"strat":"strat_tpsl3","rolling_price":rolling_price}
    enter_price = enter_data["price"]
    if cur_price < ((1+strat_data["cur_sl"])*enter_price ): 
        return "SELL",strat_data,f"StopLoss{strat_data['cur_sl']:.2%}"
    elif cur_price > ((1+strat_data["cur_tp"])*enter_price ): 
        return "SELL",strat_data,f"TakeProf{strat_data['cur_tp']:.2%}"
    # strats to shrink tp and sl
    # width=enter_data["tp"]-enter_data["sl"] # +1.5% -0.5%
    # print("width",width)
    strat_status="In SLTP"
    nextlvlincrease=0.005 # 0.5%
    if (not strat_data["shiftSureProfit"]) and (cur_price > ( 1.01*enter_price )): # if more than 1% gain from enterprice, move sltp
        strat_status = "Up1%StopLoss"
        strat_data["cur_sl"] = 0.008
        strat_data["cur_tp"] = 0.028
        strat_data["shiftSureProfit"]=True
        strat_data["rolling_price"]=cur_price
    elif cur_price > (strat_data["rolling_price"]*(1+nextlvlincrease)):
        #( (1+strat_data["cur_sl"]+width*0.55)*enter_price ): # shifts up by 0.55*4%-2% =0.2% from center point
        strat_data["cur_sl"] =  (cur_price-enter_price)/enter_price-0.005
        strat_data["cur_tp"] =  (cur_price-enter_price)/enter_price+0.015
        strat_status = "UpSlow"
        strat_data["rolling_price"]=cur_price
    str1=f"SL`{enter_price*(1+strat_data['cur_sl']):{price_format}}`,"
    str1+=f"TP`{enter_price*(1+strat_data['cur_tp']):{price_format}}`"
    str2=f"(`{strat_data['cur_sl']:+.2%}`,`{(cur_price-enter_price)/enter_price:+.2%}`,`{strat_data['cur_tp']:+.2%}`)"
    str3=f"\nNxtlvl: `{strat_data['rolling_price']*(1+nextlvlincrease):{price_format}}`,"
    str4=f"(`{nextlvlincrease:+.2%}`)" 
    str5=f"width={strat_data['cur_tp']-strat_data['cur_sl']:.2%}"
    
    return "HOLD",strat_data,f"{strat_status} {str1} {str2}{str3}{str4}, {str5}"
def price_action_signal(enter_data,strat_data,cur_price):
    # enter_data = {"price":cur_price,"sl":sl,"tp":tp,"dfname":dfname,"ent_time":ent_time,
    #          "hl_pairs":hl_pairs,"strat":"strat_tpsl1"}
    if enter_data["strat"]=="strat_tpsl2":
        return strat_tpsl2(enter_data,strat_data,cur_price)
    elif enter_data["strat"]=="strat_tpsl3":
        return strat_tpsl3(enter_data,strat_data,cur_price)
    else:
        raise NotImplementedError("#todo strat :(")
def write_signal(ticker,interval,signal,closeprice,dfname):
    strr = f"{signal},{closeprice:{price_format}},{str(dfname).replace(' ','_')},"
    strr+= f"{str(datetime.datetime.now()).replace(' ','_')}\n"
    with open(f"trade_signals/{ticker}{interval}.status","a") as f:
        f.writelines(strr)
def read_signal(ticker,interval):
    signal_raw=""
    with open(f"trade_signals/{ticker}{interval}.status","r") as f:
        signal_raw = f.readlines()
    signal=signal_raw[-1].split(",")[0]
    return signal
def log_trade_results(ticker,interval,openprice,closeprice,dfname,starttime,exittime,reason="",pos_type="",critStr=""):
    strr = f"{ticker},{interval},open{openprice:{price_format}},closeprice{closeprice:{price_format}},"
    strr+= f"dfname{dfname},starttime{starttime},exittime{exittime},exitreason{reason},postype{pos_type},critStr{critStr}\n"
    with open("trade_logs/results_trades18_13_09_2023.log","a") as f:
        f.writelines(strr)