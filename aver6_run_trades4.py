import asyncio
from binance import AsyncClient, BinanceSocketManager
from binance.enums import *
import time
import datetime
from collections import Counter
import pickle
import subprocess
from disc_api import ALEXPING, get_random_emoji, ping,STATUS_PING2,SIGNALROLE,CRYPTO_SIGNALS2,ERROR_PING2,CRYPTO_LOGS2
import traceback
import numpy as np

with open("9_0_subset_symbols_24hrchange.pkl","rb") as f:
    subset_symbols = pickle.load(f)
maxsymbols=-1
master_list=[[None] for _ in subset_symbols[:maxsymbols]]
master_list_gains=[[0,0] for _ in subset_symbols[:maxsymbols]]
master_list_status=["1111" for _ in subset_symbols[:maxsymbols]]
MOMENTUM_count=0
async def main(symbol='BNBBTC',idd=0):
    global master_list ,MOMENTUM_count,master_list_status
    await asyncio.sleep(idd*0.25)
    client = await AsyncClient.create()
    bm = BinanceSocketManager(client) 
    ts = bm.kline_socket(symbol, interval=KLINE_INTERVAL_1MINUTE) 
    print(f"sub{idd}",end=" ")
    prev="0000";prev_df=[None]
    last_updated="0001"
    async with ts as tscm:
        while True:
            try:
                res = await tscm.recv() 
                if res["e"]=="error":
                    print(str(datetime.datetime.now())[11:-4],res)
                    raise Exception(res) 
                if prev != str(res["k"]["T"])[6:-3]: # a new change, so append the prev_df into the master_list
                    prev = str(res["k"]["T"])[6:-3]
                    
                    ress=res["k"]
                    df = [ress["t"],float(ress["o"]),float(ress["c"]),float(ress["v"])] 
                    master_list[idd].append(prev_df.copy())
                    master_list_status[idd]=prev 
                    prev_df = df.copy()
                    if len(master_list[idd])>2:
                        master_list[idd].pop(0) 
                        if (master_list[idd][0][0] is not None) and (master_list[idd][1][0] is not None):
                            # work on master_list since it has the latest dataset
                            dfloc0 = master_list[idd][0];dfloc1=master_list[idd][1]
                            v0 = dfloc0[1]*dfloc0[3];v1 = dfloc1[1]*dfloc1[3];
                            g0 = (dfloc0[2]-dfloc0[1])/dfloc0[1]
                            g1 = (dfloc1[2]-dfloc1[1])/dfloc1[1]
                            master_list_gains[idd]=(g0,g1)
                            paramsWin = (-0.002,-0.002,1e6,1e6) # test params, should have 10 trades per day
                            if  g0<paramsWin[0] and g1<paramsWin[1] and v0>paramsWin[2] and v1>paramsWin[3]:
                                #BUY signal!
                                cmd = ["python","aver6_master_trades.py",symbol,"15",str(datetime.datetime.now())[:-4],
                                       "TEST",f"{dfloc1[2]:.6g}","-0.006","-0.006","MT_test",f"{MOMENTUM_count}"]
                                cmd = " ".join(cmd)
                                subprocess.Popen( cmd , shell=True)
                                MOMENTUM_count+=1 
                                signal_enter_position(symbol,dfloc1[2],dfname=str(datetime.datetime.now())[:-4])
                if (idd==0) and (last_updated!=prev) and (master_list[idd][0][0] is not None) and (master_list[idd][1][0] is not None): 
                    if len(Counter(master_list_status).keys())==1:
                        # everything is in sync, use this dataset
                        strr=f"MOMENT test {str(datetime.datetime.now())[:-4]},"
                        lowG="nothing"
                        try:
                            arrr = np.asarray(master_list_gains)
                            lowest_idd_prev = np.argmin(arrr[:,0])
                            lowest_idd_now = np.argmin(arrr[:,1])
                            lowG= f"prev g0{arrr[lowest_idd_prev,0]:.4%}g1{arrr[lowest_idd_prev,1]}({subset_symbols[lowest_idd_prev]}),"
                            lowG+=f"now g0{arrr[lowest_idd_now,0]:.4%}g1{arrr[lowest_idd_now,1]}({subset_symbols[lowest_idd_now]})."
                        except ValueError or IndexError as e:
                            lowG=f"error {str(e)}"
                        strr+=f"sync{Counter(master_list_status)}, opos={MOMENTUM_count},{lowG}"
                        ping(STATUS_PING2,strr)
                        last_updated=prev
            except Exception as e:
                strr=traceback.format_exc()
                print("ERROR",symbol,e,str(e))
                ping(ERROR_PING2,f"MOMENT test error {symbol} {ALEXPING} "+str(e)+"  "+strr+f" dfloc0{dfloc0} dfloc1{dfloc1}")
                break
    await client.close_connection()
    print(f"ended {symbol}") 
def ddtn_str():
    return str(datetime.datetime.now())[:-4]
def signal_enter_position(symbol,closeprice,dfname):
    xx = closeprice
    strr = f"`{symbol}` BUY `{xx}`" 
    #strr += f" tp `{xx*(1+self.tp):{self.price_format}}` sl `{xx*(1+self.sl):{self.price_format}}` {pos_type}\n"
    strr += f"`{dfname}` (`{ddtn_str()}`) {SIGNALROLE}"
    #write_signal(symbol,self.interval,signal="ENTER",closeprice=xx,dfname=dfname) 
    #enterdftime = str(dfname).replace(" ","_") 
    ping(CRYPTO_SIGNALS2,strr)

ddtn=datetime.datetime.now()
rand_emoji = f"{get_random_emoji()}{get_random_emoji()}{get_random_emoji()}"

ping(ERROR_PING2,f"new run {ddtn},{rand_emoji}")
ping(STATUS_PING2,f"new run {ddtn},{rand_emoji}")
ping(CRYPTO_SIGNALS2,f"new run {ddtn},{rand_emoji}")
ping(CRYPTO_LOGS2,f"new run {ddtn},{rand_emoji}")

loop = asyncio.get_event_loop() 
print("starting event loop")
for idd,s in enumerate(subset_symbols[:maxsymbols]):
    asyncio.run_coroutine_threadsafe(main(s+"USDT",idd), loop)
loop.run_forever()
print("ending loop")
