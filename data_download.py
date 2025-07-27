# data_download.py

import yfinance as yf
import os
import pandas as pd
from config import TICKERS

def download_data(tickers, period="8d", interval="1m"):
    os.makedirs("data", exist_ok=True)
    for ticker in tickers:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            print(f"Warning: No data for {ticker}")
            continue
        df.to_csv(f"data/{ticker}.csv")
        print(f"Downloaded: {ticker}")

if __name__ == "__main__":
    download_data(TICKERS)
