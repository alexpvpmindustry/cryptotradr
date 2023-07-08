import requests
import csv
from datetime import datetime
from pathlib import Path
from os.path import exists
import time
import pandas as pd
from glob import glob

base_url = 'https://api.binance.com' 

def get_klines_live(symbol, interval='1h', start_time=None, end_time=None, limit=500):
    endpoint = '/api/v3/klines'
    url = base_url + endpoint
    params = {'symbol': symbol,'interval': interval,'limit': limit}
    if start_time:
        params['startTime'] = start_time
    if end_time:
        params['endTime'] = end_time
    response = requests.get(url, params=params)
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
        return None
def df_to_dfmpl(df): 
    dfmpl = df[["open_time","open","high","low","close","volume"]]
    dfmpl = dfmpl.rename(columns={"open_time":"Date","open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"})
    dfmpl=dfmpl.set_index("Date")
    dfmpl.index = pd.to_datetime(dfmpl.index+3600*3*1e3,unit="ms")
    return dfmpl
def get_historical_df(tickerpair,interval,folder="kline_data_sample"):
    df = [pd.read_csv(g) for g in sorted(glob(f"{folder}\\{tickerpair}/*")) if f"_{interval}.csv" in g]
    df = pd.concat(df, ignore_index=True).drop_duplicates().reset_index(drop=True)
    return df