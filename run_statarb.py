# run_statarb.py
"""Run the statistical-arbitrage study and write its results.

Produces two things:
  1. The honest, walk-forward pairs result (every bar out-of-sample).
  2. A selection-bias demonstration: a one-shot pairs backtest looks strong on the
     window it was selected on, then decays out-of-sample. This is the core
     research finding and the reason the walk-forward number is the credible one.
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from metrics import sharpe_ratio, max_drawdown
from statarb import select_pairs, pair_pnl, walk_forward, vol_target

UNIVERSE_DIR = "data_universe"


def load_universe(path: str = UNIVERSE_DIR) -> pd.DataFrame:
    series = {}
    for file in glob.glob(os.path.join(path, "*.csv")):
        ticker = os.path.basename(file)[:-4]
        df = pd.read_csv(file)
        date_col = df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col]).set_index(date_col)
        series[ticker] = pd.to_numeric(df["Close"], errors="coerce")
    prices = pd.DataFrame(series).dropna(how="all").ffill().dropna(axis=1)
    return prices


def annualized_return(curve: np.ndarray) -> float:
    if len(curve) < 2 or curve[0] <= 0:
        return 0.0
    return float(curve[-1] ** (252 / len(curve)) - 1.0)


def static_selection_decay(prices: pd.DataFrame, train_frac: float = 0.7) -> dict:
    """Select pairs ONCE on the train window, then read Sharpe in- vs out-of-sample."""
    log_prices = np.log(prices)
    returns = prices.pct_change().fillna(0.0)
    split = int(len(prices) * train_frac)

    pairs = select_pairs(returns.iloc[:split], log_prices.iloc[:split])
    if not pairs:
        return {"pairs": 0, "in_sample_sharpe": 0.0, "out_sample_sharpe": 0.0}

    portfolio = pd.concat(
        [pair_pnl(log_prices, returns, a, b, beta) for a, b, beta in pairs], axis=1
    ).mean(axis=1)
    scaled = vol_target(portfolio)
    return {
        "pairs": len(pairs),
        "in_sample_sharpe": round(sharpe_ratio(scaled[:split], 252), 2),
        "out_sample_sharpe": round(sharpe_ratio(scaled[split:], 252), 2),
    }


def main() -> dict:
    prices = load_universe()
    print(f"Universe: {prices.shape[1]} names, {len(prices)} days "
          f"({prices.index[0].date()} to {prices.index[-1].date()})")

    # 1. Honest walk-forward result.
    pnl, diag = walk_forward(prices)
    curve = np.cumprod(1.0 + vol_target(pnl))
    scaled = vol_target(pnl)
    half = len(scaled) // 2

    walk = {
        "sharpe": round(sharpe_ratio(scaled, 252), 2),
        "sharpe_first_half": round(sharpe_ratio(scaled[:half], 252), 2),
        "sharpe_second_half": round(sharpe_ratio(scaled[half:], 252), 2),
        "annualized_return_pct": round(annualized_return(curve) * 100, 2),
        "max_drawdown_pct": round(max_drawdown(curve) * 100, 2),
        "avg_pairs_per_quarter": round(diag["avg_pairs_per_block"], 0),
        "quarters": diag["blocks"],
    }

    # 2. Selection-bias / decay demonstration.
    decay = static_selection_decay(prices)

    results = {"walk_forward": walk, "static_selection_decay": decay}

    print("\n===== WALK-FORWARD PAIRS (every bar out-of-sample) =====")
    for key, value in walk.items():
        print(f"{key:>22}: {value}")
    print("\n===== SELECTION-BIAS DEMONSTRATION (select once on train) =====")
    print(f"   in-sample Sharpe:  {decay['in_sample_sharpe']}  (looks great)")
    print(f"   out-sample Sharpe: {decay['out_sample_sharpe']}  (the edge decays)")
    print(f"   -> walk-forward's {walk['sharpe']} is the credible, tradable number")
    print("================================================================")

    os.makedirs("results", exist_ok=True)
    with open(os.path.join("results", "statarb_metrics.json"), "w") as handle:
        json.dump(results, handle, indent=2)

    plt.figure(figsize=(12, 6))
    plt.plot(prices.index[-len(curve):], curve, label="Walk-forward stat-arb")
    plt.axhline(1.0, color="gray", linestyle="--")
    plt.title("Walk-Forward Statistical Arbitrage (vol-targeted, net of costs)")
    plt.xlabel("Date")
    plt.ylabel("Growth of $1")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join("results", "statarb_equity.png"), dpi=120)

    return results


if __name__ == "__main__":
    main()
