# metrics.py
"""Performance metrics for backtest equity curves.

Every function here is pure and operates on plain sequences or numpy arrays,
which keeps them trivial to unit test. "Returns" means simple period-over-period
returns of an equity curve unless stated otherwise.

The default annualization assumes 1-minute bars during US equity regular hours
(390 minutes/day * 252 trading days). Pass `periods_per_year` explicitly when the
equity curve is sampled at a different frequency.
"""
from __future__ import annotations

import numpy as np

TRADING_DAYS_PER_YEAR = 252
MINUTES_PER_TRADING_DAY = 390
MINUTE_BARS_PER_YEAR = TRADING_DAYS_PER_YEAR * MINUTES_PER_TRADING_DAY


def equity_to_returns(equity) -> np.ndarray:
    """Convert an equity curve to simple period returns."""
    equity = np.asarray(equity, dtype=float)
    if equity.size < 2:
        return np.array([])
    prev = equity[:-1]
    # Guard against divide-by-zero on a wiped-out account.
    with np.errstate(divide="ignore", invalid="ignore"):
        returns = np.where(prev != 0, np.diff(equity) / prev, 0.0)
    return returns


def total_return(equity) -> float:
    """Total return over the whole curve, e.g. 0.05 == +5%."""
    equity = np.asarray(equity, dtype=float)
    if equity.size < 2 or equity[0] == 0:
        return 0.0
    return float(equity[-1] / equity[0] - 1.0)


def sharpe_ratio(
    returns,
    periods_per_year: int = MINUTE_BARS_PER_YEAR,
    risk_free_rate: float = 0.0,
) -> float:
    """Annualized Sharpe ratio of a return series.

    `risk_free_rate` is an annual rate; it is de-annualized to the bar frequency
    before subtraction. Returns 0.0 when volatility is zero or the series is too
    short to have a sample standard deviation.
    """
    returns = np.asarray(returns, dtype=float)
    if returns.size < 2:
        return 0.0
    excess = returns - risk_free_rate / periods_per_year
    sd = excess.std(ddof=1)
    if sd == 0:
        return 0.0
    return float(np.sqrt(periods_per_year) * excess.mean() / sd)


def max_drawdown(equity) -> float:
    """Largest peak-to-trough decline, as a negative fraction (e.g. -0.12)."""
    equity = np.asarray(equity, dtype=float)
    if equity.size == 0:
        return 0.0
    running_max = np.maximum.accumulate(equity)
    with np.errstate(divide="ignore", invalid="ignore"):
        drawdowns = np.where(running_max != 0, (equity - running_max) / running_max, 0.0)
    return float(drawdowns.min())


def annualized_return(equity, periods_per_year: int = MINUTE_BARS_PER_YEAR) -> float:
    """Compound annual growth rate implied by the curve and its bar frequency."""
    equity = np.asarray(equity, dtype=float)
    n = equity.size - 1
    if n < 1 or equity[0] <= 0:
        return 0.0
    growth = equity[-1] / equity[0]
    if growth <= 0:
        return -1.0
    return float(growth ** (periods_per_year / n) - 1.0)


def win_rate(pnls) -> float:
    """Fraction of entries with positive PnL (e.g. 0.62 == 62%)."""
    pnls = np.asarray(pnls, dtype=float)
    if pnls.size == 0:
        return 0.0
    return float((pnls > 0).mean())
