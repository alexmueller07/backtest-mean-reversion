# backtest.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from config import TICKERS, CAPITAL
from data_download import download_data
from strategy import generate_signals
import os

def load_clean_csv(ticker):
    df = pd.read_csv(f"data/{ticker}.csv")

    if "Datetime" in df.columns:
        df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce")
        df.set_index("Datetime", inplace=True)
    elif "timestamp" in df.columns:
        df["Datetime"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df.set_index("Datetime", inplace=True)
    else:
        df.index = pd.to_datetime(df.index, errors="coerce")

    # Convert OHLCV to floats, coerce any bad values
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df.dropna(subset=["Open", "High", "Low", "Close", "Volume"], inplace=True)

    return df

def backtest(df, initial_capital):
    capital = initial_capital
    position = 0
    equity_curve = []
    
    for i in range(1, len(df)):
        signal = df["Signal"].iloc[i]
        price = df["Close"].iloc[i]

        if signal == 1 and position == 0:
            shares = capital // price
            position = shares
            capital -= shares * price

        elif signal == -1 and position > 0:
            capital += position * price
            position = 0

        equity = capital + position * price
        equity_curve.append(equity)

    final = capital + position * df["Close"].iloc[-1]
    return final, equity_curve

def buy_and_hold(df, initial_capital):
    price_start = df["Close"].iloc[0]
    price_end = df["Close"].iloc[-1]
    return initial_capital * (price_end / price_start)

def main():
    if not os.path.exists("data"):
        download_data(TICKERS)

    starting_capital = CAPITAL
    final_capitals = []
    equity_curves = []
    beat_benchmark = 0
    profitable = 0

    for ticker in TICKERS:
        try:
            df = load_clean_csv(ticker)
            df = generate_signals(df)

            final, equity_curve = backtest(df, starting_capital)
            final_capitals.append(final)
            equity_curves.append(equity_curve)

            buy_hold = buy_and_hold(df, starting_capital)
            if final > buy_hold:
                beat_benchmark += 1
            if final > starting_capital:
                profitable += 1

            print(f"{ticker}: Final = {final:.2f}, Buy & Hold = {buy_hold:.2f}")

        except Exception as e:
            print(f"Failed on {ticker}: {e}")

    avg_final = np.mean(final_capitals)
    total_return = (avg_final - starting_capital) / starting_capital * 100

    print("\n============== BACKTEST RESULTS ==============")
    print(f"Starting Capital: {starting_capital}")
    print(f"Final Capital: {avg_final}")
    print(f"The Strategy Returned: {total_return:.2f}%")
    print("------------------------")
    print(f"The Strategy Outperformed Buy and Hold: {100 * beat_benchmark / len(TICKERS):.2f}% of the time")
    print(f"The Strategy was Profitable: {100 * profitable / len(TICKERS):.2f}% of the time")
    
    bh_returns = []
    for ticker in TICKERS:
        try:
            df = load_clean_csv(ticker)
            bh = buy_and_hold(df, starting_capital)
            bh_returns.append(bh)
        except:
            pass

    bh_avg = np.mean(bh_returns)
    bh_total = (bh_avg - starting_capital) / starting_capital * 100
    print(f"In this time Buy and Hold: {bh_total:.2f}%")

    # Plot average equity curve
    min_len = min(len(c) for c in equity_curves)
    trimmed = [np.array(c[:min_len]) for c in equity_curves]
    avg_curve = np.mean(trimmed, axis=0)

    plt.plot(avg_curve, label="Strategy")
    plt.axhline(starting_capital, color='gray', linestyle='--', label="Start")
    plt.title("Average Equity Curve Across All Tickers")
    plt.xlabel("Time")
    plt.ylabel("Equity ($)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
