# daily_backtest.py
"""Multi-year daily backtest of the mean-reversion strategy.

The minute-bar backtest in `backtest.py` can only cover ~1 week (yfinance free
tier limit), which makes any annualized Sharpe meaningless. This script runs the
same SMA-ratio mean-reversion idea on years of daily bars so the risk-adjusted
numbers are actually interpretable.

Two things make this version honest:
  * Signal bands are computed on a *trailing* window and shifted one bar, so a
    decision never peeks at the current or future price (no lookahead bias).
  * Positions earn the *next* bar's return, matching how a live order would fill.

Data is cached under `data_daily/` so re-runs are deterministic and offline.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from config import TICKERS, CAPITAL, SMA_WINDOW
from metrics import (
    TRADING_DAYS_PER_YEAR,
    annualized_return,
    equity_to_returns,
    max_drawdown,
    sharpe_ratio,
    total_return,
    win_rate,
)

DATA_DIR = "data_daily"
LOOKBACK = 252           # trailing window (~1 year) for the percentile bands
MIN_LOOKBACK = 60        # need this much history before trading a name
LOW_PCT, HIGH_PCT = 25, 75


def download_daily(tickers, period: str = "3y") -> None:
    """Cache adjusted daily closes for each ticker as a clean Date,Close CSV."""
    import yfinance as yf

    os.makedirs(DATA_DIR, exist_ok=True)
    for ticker in tickers:
        path = os.path.join(DATA_DIR, f"{ticker}.csv")
        if os.path.exists(path):
            continue
        df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
        if df.empty:
            print(f"Warning: no daily data for {ticker}")
            continue
        df["Close"].to_csv(path, header=["Close"])
        print(f"Downloaded daily: {ticker}")


def load_daily(ticker: str) -> pd.Series:
    """Load a cached Date-indexed close series."""
    df = pd.read_csv(os.path.join(DATA_DIR, f"{ticker}.csv"))
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).set_index(date_col)
    close = pd.to_numeric(df["Close"], errors="coerce").dropna()
    close.name = ticker
    return close


def strategy_equity(close: pd.Series, capital: float) -> pd.Series:
    """Causal long-only mean-reversion equity curve for one ticker."""
    sma = close.rolling(SMA_WINDOW).mean()
    ratio = close / sma

    # Bands from prior bars only (shift(1)) -> no lookahead.
    prior = ratio.shift(1)
    low = prior.rolling(LOOKBACK, min_periods=MIN_LOOKBACK).quantile(LOW_PCT / 100)
    high = prior.rolling(LOOKBACK, min_periods=MIN_LOOKBACK).quantile(HIGH_PCT / 100)

    enter = ratio < low      # oversold -> go long
    exit_ = ratio > high     # reverted -> flatten

    position = np.zeros(len(close))
    state = 0
    for i in range(len(close)):
        if state == 0 and bool(enter.iloc[i]):
            state = 1
        elif state == 1 and bool(exit_.iloc[i]):
            state = 0
        position[i] = state

    asset_returns = close.pct_change().fillna(0.0).to_numpy()
    # Yesterday's position earns today's return.
    held = np.concatenate([[0.0], position[:-1]])
    strat_returns = held * asset_returns
    equity = capital * np.cumprod(1.0 + strat_returns)
    return pd.Series(equity, index=close.index)


def run(period: str = "3y") -> dict:
    download_daily(TICKERS, period=period)

    curves: dict[str, pd.Series] = {}
    per_ticker_pnl = []
    beat = 0
    profitable = 0
    bh_finals = []

    for ticker in TICKERS:
        path = os.path.join(DATA_DIR, f"{ticker}.csv")
        if not os.path.exists(path):
            continue
        close = load_daily(ticker)
        if len(close) < MIN_LOOKBACK + SMA_WINDOW:
            continue

        equity = strategy_equity(close, CAPITAL)
        curves[ticker] = equity

        final = float(equity.iloc[-1])
        bh_final = CAPITAL * float(close.iloc[-1] / close.iloc[0])
        per_ticker_pnl.append(final - CAPITAL)
        bh_finals.append(bh_final)
        profitable += final > CAPITAL
        beat += final > bh_final

    if not curves:
        raise SystemExit("No daily data available to evaluate.")

    # Equal-weight portfolio on the shared trading calendar.
    portfolio = pd.concat(curves.values(), axis=1).dropna().mean(axis=1)
    returns = equity_to_returns(portfolio.to_numpy())

    n = len(per_ticker_pnl)
    metrics = {
        "tickers_tested": n,
        "bar_frequency": "1day",
        "period_requested": period,
        "trading_days": int(len(portfolio)),
        "periods_per_year": TRADING_DAYS_PER_YEAR,
        "total_return_pct": round(total_return(portfolio.to_numpy()) * 100, 2),
        "annualized_return_pct": round(annualized_return(portfolio.to_numpy(), TRADING_DAYS_PER_YEAR) * 100, 2),
        "sharpe_ratio": round(sharpe_ratio(returns, TRADING_DAYS_PER_YEAR), 2),
        "max_drawdown_pct": round(max_drawdown(portfolio.to_numpy()) * 100, 2),
        "win_rate_pct": round(win_rate(np.array(per_ticker_pnl)) * 100, 2),
        "beat_buy_and_hold_pct": round(100 * beat / n, 2),
        "profitable_pct": round(100 * profitable / n, 2),
        "buy_and_hold_total_return_pct": round((np.mean(bh_finals) - CAPITAL) / CAPITAL * 100, 2),
    }

    print("\n========== DAILY BACKTEST RESULTS ==========")
    for key, value in metrics.items():
        print(f"{key:>28}: {value}")
    print("============================================")

    os.makedirs("results", exist_ok=True)
    with open(os.path.join("results", "daily_metrics.json"), "w") as handle:
        json.dump(metrics, handle, indent=2)

    plt.figure(figsize=(12, 6))
    plt.plot(portfolio.index, portfolio.to_numpy(), label="Strategy (equal-weight)")
    plt.axhline(CAPITAL, color="gray", linestyle="--", label="Start")
    plt.title("Daily Mean-Reversion Portfolio Equity")
    plt.xlabel("Date")
    plt.ylabel("Equity ($)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join("results", "daily_equity_curve.png"), dpi=120)

    return metrics


if __name__ == "__main__":
    run()
