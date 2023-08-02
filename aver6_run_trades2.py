import asyncio
from binance import AsyncClient, BinanceSocketManager
from binance.enums import *
import time
import datetime
from collections import Counter
import pickle
import subprocess
from disc_api import ALEXPING, get_random_emoji, ping,STATUS_PING2,SIGNALROLE,CRYPTO_SIGNALS2,ERROR_PING2,CRYPTO_LOGS2

with open("9_0_subset_symbols_24hrchange.pkl","rb") as f:
    subset_symbols = pickle.load(f)
master_list=[[None] for _ in subset_symbols[:]]
master_list_status=["1111" for _ in subset_symbols[:]]
MOMENTUM_count=0
async def main(symbol='BNBBTC',idd=0):
    global master_list ,MOMENTUM_count,master_list_status
    await asyncio.sleep(idd*0.25)
    client = await AsyncClient.create()
    bm = BinanceSocketManager(client) 
    ts = bm.kline_socket(symbol, interval=KLINE_INTERVAL_1MINUTE) 
    print(f"sub{idd}",end=" ")
    prev="0000";prev_df=[None]
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
                        if master_list[idd][0] is not None:
                            # work on master_list since it has the latest dataset
                            dfloc0 = master_list[idd][0];dfloc1=master_list[idd][1]
                            v0 = dfloc0[1]*dfloc0[3];v1 = dfloc1[1]*dfloc1[3];
                            g0 = (dfloc0[2]-dfloc0[1])/dfloc0[1]
                            g1 = (dfloc1[2]-dfloc1[1])/dfloc1[1]
                            if v0>3e6 and v1>3e6 and g0<-0.008 and g1<-0.008:
                                #BUY signal!
                                cmd = ["python","aver6_master_trades.py",symbol,"15",str(datetime.datetime.now())[:-4],
                                       "TEST",f"{dfloc1[2]:.6g}","-0.008","-0.008","MOMENTUM",f"{MOMENTUM_count}"]
                                cmd = " ".join(cmd)
                                subprocess.Popen( cmd , shell=True)
                                MOMENTUM_count+=1
                            if idd==0:
                                strr=f"MOMENTUM {str(datetime.datetime.now())[:-4]},"
                                strr+=f"sync{Counter(master_list_status)}, opos={MOMENTUM_count}"
                                ping(STATUS_PING2,strr)
            except Exception as e:
                print(symbol,e,str(e))
                ping(ERROR_PING2,f"MOMENT error {symbol} {ALEXPING} "+str(e))
                break
    await client.close_connection()
    print(f"ended {symbol}")

ddtn=datetime.datetime.now()
rand_emoji = f"{get_random_emoji()}{get_random_emoji()}{get_random_emoji()}"

ping(ERROR_PING2,f"new run {ddtn},{rand_emoji}")
loop = asyncio.get_event_loop() 
print("starting event loop")
for idd,s in enumerate(subset_symbols[:]):
    asyncio.run_coroutine_threadsafe(main(s+"USDT",idd), loop)
loop.run_forever()
print("ending loop")
