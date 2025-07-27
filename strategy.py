# strategy.py

import pandas as pd
import numpy as np
from config import SMA_WINDOW, LOW_PERCENTILE, HIGH_PERCENTILE

def generate_signals(df):
    df["SMA"] = df["Close"].rolling(window=SMA_WINDOW).mean()
    df["Ratio"] = df["Close"] / df["SMA"]
    
    low = np.percentile(df["Ratio"].dropna(), LOW_PERCENTILE)
    high = np.percentile(df["Ratio"].dropna(), HIGH_PERCENTILE)

    df["Signal"] = 0
    df.loc[df["Ratio"] < low, "Signal"] = 1   # Buy
    df.loc[df["Ratio"] > high, "Signal"] = -1  # Sell

    return df
