# backtest.py

import json
import os

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # render to file; no display needed for headless/CI runs
import matplotlib.pyplot as plt  # noqa: E402

from config import TICKERS, CAPITAL
from strategy import generate_signals
from metrics import (
    MINUTE_BARS_PER_YEAR,
    annualized_return,
    equity_to_returns,
    max_drawdown,
    sharpe_ratio,
    total_return,
    win_rate,
)

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
        # Imported lazily so a backtest on already-downloaded data needs no
        # network access (and no yfinance install).
        from data_download import download_data

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

    if not equity_curves:
        print("No tickers produced an equity curve; nothing to evaluate.")
        return None

    # Build the aggregate portfolio equity curve (mean across all tickers),
    # anchored at the starting capital so metrics read on a real-dollar basis.
    min_len = min(len(c) for c in equity_curves)
    trimmed = [np.array(c[:min_len]) for c in equity_curves]
    avg_curve = np.concatenate([[starting_capital], np.mean(trimmed, axis=0)])

    # Per-ticker PnL drives the trade-level win rate.
    per_ticker_pnl = np.array(final_capitals) - starting_capital

    bh_finals = []
    for ticker in TICKERS:
        try:
            bh_finals.append(buy_and_hold(load_clean_csv(ticker), starting_capital))
        except Exception:
            pass
    bh_total_pct = (np.mean(bh_finals) - starting_capital) / starting_capital * 100 if bh_finals else 0.0

    returns = equity_to_returns(avg_curve)
    metrics = {
        "tickers_tested": len(final_capitals),
        "bar_frequency": "1min",
        "periods_per_year": MINUTE_BARS_PER_YEAR,
        "total_return_pct": round(total_return(avg_curve) * 100, 2),
        "annualized_return_pct": round(annualized_return(avg_curve) * 100, 2),
        "sharpe_ratio": round(sharpe_ratio(returns), 2),
        "max_drawdown_pct": round(max_drawdown(avg_curve) * 100, 2),
        "win_rate_pct": round(win_rate(per_ticker_pnl) * 100, 2),
        "beat_buy_and_hold_pct": round(100 * beat_benchmark / len(final_capitals), 2),
        "profitable_pct": round(100 * profitable / len(final_capitals), 2),
        "buy_and_hold_total_return_pct": round(float(bh_total_pct), 2),
    }

    print("\n============== BACKTEST RESULTS ==============")
    print(f"Tickers tested:        {metrics['tickers_tested']}")
    print(f"Total return:          {metrics['total_return_pct']:.2f}%")
    print(f"Annualized return:     {metrics['annualized_return_pct']:.2f}%")
    print(f"Sharpe ratio:          {metrics['sharpe_ratio']:.2f}")
    print(f"Max drawdown:          {metrics['max_drawdown_pct']:.2f}%")
    print(f"Win rate (by ticker):  {metrics['win_rate_pct']:.2f}%")
    print(f"Beat buy-and-hold:     {metrics['beat_buy_and_hold_pct']:.2f}% of tickers")
    print(f"Profitable:            {metrics['profitable_pct']:.2f}% of tickers")
    print(f"Buy-and-hold return:   {metrics['buy_and_hold_total_return_pct']:.2f}%")
    print("===============================================")

    os.makedirs("results", exist_ok=True)
    with open(os.path.join("results", "metrics.json"), "w") as handle:
        json.dump(metrics, handle, indent=2)

    plt.plot(avg_curve, label="Strategy")
    plt.axhline(starting_capital, color="gray", linestyle="--", label="Start")
    plt.title("Average Equity Curve Across All Tickers")
    plt.xlabel("Time")
    plt.ylabel("Equity ($)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join("results", "equity_curve.png"), dpi=120)

    return metrics

if __name__ == "__main__":
    main()
