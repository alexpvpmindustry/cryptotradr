import datetime,time,sys
from trader import get_current_price,price_action_signal, read_signal
import json
from disc_api import ping,STATUS_PING2,SIGNALROLE,CRYPTO_SIGNALS2
from trader import market_trade, write_signal 

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

#enter trade:
symbol = tickerpair
qtyUSD = float(sys.argv[2])
dfname = sys.argv[3]
test=(sys.argv[4]=="TEST")

cur_price = get_current_price(symbol,sell=False)
qty = qtyUSD/cur_price
a1,a2,a3 = market_trade(symbol,qty,buy=True,test=test)

if a1=="FILLED":# we have entered the trade
    ping(CRYPTO_SIGNALS2,f"We have entered the trade pc{param_choice}, {cur_price:.4f}")
else:
    ping(CRYPTO_SIGNALS2,f"ENTER ERROR pc{param_choice} {SIGNALROLE}")
    assert False
# continous loop until exit or sell signal is recieved
status="HOLD"
loopcounts=0

ent_time=str(datetime.datetime.now()).replace(" ","_")
enter_data = {"price":cur_price,"sl":sl,"tp":tp,"dfname":dfname,"ent_time":ent_time,
              "hl_pairs":hl_pairs,"strat":"strat_tpsl1"}
strat_data = {"cur_sl":sl,"cur_tp":tp,"slip":-0.002,"ent_sl":sl,"ent_tp":tp,"strat":"strat_tpsl1"}

stdmean_status="HOLD"
while status=="HOLD":
    # get current price
    cur_price = get_current_price(symbol)
    # get price_action_signal
    pas_status,strat_data,strr = price_action_signal(enter_data,strat_data,cur_price)
    if strr[:2]=="Up": # shifting of SLTP
        ping(CRYPTO_SIGNALS2,pas_status+f" pc{param_choice} "+strr)
    if loopcounts%10==0:# read exit status
        #TODO read exit status
        stdmean_status=read_signal(symbol,interval)
        if stdmean_status != "EXIT":
            stdmean_status = "HOLD"
    status ="HOLD" if ((stdmean_status=="HOLD") and (pas_status=="HOLD")) else "SELL"
    loopcounts+=1
    if status=="HOLD":
        time.sleep(3)

# sell position
a1,a2,a3 = market_trade(symbol,qty,buy=False,test=test)
if a1=="FILLED":# we have exited the trade
    change = (cur_price-enter_data['price'])/enter_data['price']
    strr = f"We have exited the trade pc{param_choice}, {cur_price:.4f},"
    strr+= f" entered at {enter_data['price']:.4f},\nsize=${qtyUSD} ({change*100:.2f}%, {qtyUSD*change:.2f}$)"
    ping(CRYPTO_SIGNALS2,strr)
else:
    ping(CRYPTO_SIGNALS2,f"EXIT ERROR pc{param_choice} {SIGNALROLE}")
    assert False