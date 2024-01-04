

import yfinance as yf
import matplotlib.pyplot as plt
# %matplotlib inline
import pandas_ta as ta
from multiprocessing.pool import Pool
from sklearn.manifold import TSNE
import pandas as pd
import pickle
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn import svm
from sklearn import metrics
from collections import Counter
from sklearn.neural_network import MLPClassifier

# %%time
with open("hist_data_2018-1-1_2023-7-12.pkl","rb") as f:
    data = pickle.load(f)
columns = list(data["Open"].columns)
coli_with_na = np.where(np.sum(pd.isna(data["Close"]))>0)[0]
#for coli in coli_with_na:
#    print(columns[coli])

opens= data["Open"].drop(columns=[columns[coli] for coli in coli_with_na])
closes = data["Close"].drop(columns=[columns[coli] for coli in coli_with_na])
# Open	High	Low	Close	Volume
highs = data["High"].drop(columns=[columns[coli] for coli in coli_with_na])
lows = data["Low"].drop(columns=[columns[coli] for coli in coli_with_na])
volumes = data["Volume"].drop(columns=[columns[coli] for coli in coli_with_na])

def funcc_symbol(x):
    ticker=x
    training_X=[]
    training_Y=[]
    correlation_Y = []
    temp_df_full = pd.DataFrame(data={"Open":opens[ticker],
                             "High":highs[ticker],
                             "Low":lows[ticker],
                             "Close":closes[ticker],
                             "Volume":volumes[ticker],
                            })
    t=0
    window_size = 34
    def clamp(df,w_min,w_max):
        return (df-w_min)/(w_max-w_min)
    while True:
        try:
            temp_df_full.iloc[window_size+t+1] # checks if y (unseen data) is available
        except IndexError :
            break
            
        training_X.append(2)
        training_Y.append(2)
        correlation_Y.append( ticker)
        t+=10
    return [training_X,training_Y,correlation_Y]