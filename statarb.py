# statarb.py
"""Statistical-arbitrage (pairs) mean reversion.

This module trades the *spread* between two cointegrated stocks rather than a
single stock's price. The spread is the mean-reverting object: when it strays
from its mean we bet on its return, long one leg and short the other, so the
position is market-neutral by construction.

The functions are deliberately small and pure so each piece (hedge ratio,
half-life, z-score, pair PnL) is unit tested. The headline result this module
produces is a *walk-forward* backtest: pairs are re-selected every quarter using
only trailing data, which makes the entire track record out-of-sample and avoids
the selection bias that makes a one-shot pairs backtest look far better than it is.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# --- pure building blocks ------------------------------------------------------


def hedge_ratio(log_a: np.ndarray, log_b: np.ndarray) -> float:
    """OLS slope of log price A on log price B (the dollar-neutral hedge)."""
    log_a = np.asarray(log_a, dtype=float)
    log_b = np.asarray(log_b, dtype=float)
    return float(np.polyfit(log_b, log_a, 1)[0])


def half_life(spread) -> float:
    """Ornstein-Uhlenbeck half-life of mean reversion, in bars.

    Fits the AR(1) relationship d(spread) = kappa * spread_lag + c. A negative
    kappa means the spread pulls back toward its mean; the half-life is the time
    to close half the gap. Returns +inf when the series does not mean-revert.
    """
    spread = pd.Series(spread, dtype=float)
    delta = spread.diff().dropna()
    lag = spread.shift(1).dropna().loc[delta.index]
    if len(delta) < 3:
        return float("inf")
    kappa = float(np.polyfit(lag.values, delta.values, 1)[0])
    if kappa >= 0:
        return float("inf")
    return float(-np.log(2) / kappa)


def zscore(spread: pd.Series, window: int) -> pd.Series:
    """Rolling z-score of the spread (how many std devs from its recent mean)."""
    mean = spread.rolling(window).mean()
    std = spread.rolling(window).std()
    return (spread - mean) / std


def trade_positions(z: pd.Series, entry: float, exit: float) -> pd.Series:
    """Convert a z-score series into spread positions with entry/exit hysteresis.

    Short the spread (-1) when it is stretched high, long it (+1) when stretched
    low, and flatten once it reverts inside the exit band. State is held between
    bars, so the rule has memory rather than flipping every bar.
    """
    values = np.asarray(z, dtype=float)
    out = np.zeros(len(values))
    state = 0
    for i, zi in enumerate(values):
        if not np.isnan(zi):
            if state == 0:
                if zi > entry:
                    state = -1
                elif zi < -entry:
                    state = 1
            elif state == 1 and zi > -exit:
                state = 0
            elif state == -1 and zi < exit:
                state = 0
        out[i] = state
    return pd.Series(out, index=z.index)


def pair_pnl(
    log_prices: pd.DataFrame,
    returns: pd.DataFrame,
    a: str,
    b: str,
    beta: float,
    window: int = 40,
    entry: float = 2.0,
    exit: float = 0.5,
    cost_bps: float = 5.0,
) -> pd.Series:
    """Net daily return contribution of one pair, after transaction costs."""
    spread = log_prices[a] - beta * log_prices[b]
    z = zscore(spread, window)
    position = trade_positions(z, entry, exit)
    # Dollar-neutral leg return, normalized by gross exposure (1 + |beta|).
    leg_return = (returns[a] - beta * returns[b]) / (1.0 + abs(beta))
    turnover = position.diff().abs().fillna(0.0) / (1.0 + abs(beta))
    return position.shift(1).fillna(0.0) * leg_return - (cost_bps / 1e4) * turnover


# --- pair selection ------------------------------------------------------------


def select_pairs(
    returns: pd.DataFrame,
    log_prices: pd.DataFrame,
    corr_threshold: float = 0.6,
    half_life_bounds: tuple[float, float] = (5.0, 120.0),
    max_candidates: int = 400,
) -> list[tuple[str, str, float]]:
    """Pick mean-reverting pairs from a formation window.

    Candidates are the most correlated pairs; each is kept only if its spread is
    statistically mean-reverting (negative AR(1) coefficient) with a half-life in
    a tradable range. Returns (a, b, beta) tuples.
    """
    names = list(returns.columns)
    corr = returns.corr()
    candidates: list[tuple[str, str, float]] = []
    for i in range(len(names)):
        row = corr.iloc[i]
        for j in range(i + 1, len(names)):
            c = row.iloc[j]
            if c > corr_threshold:
                candidates.append((names[i], names[j], float(c)))
    candidates.sort(key=lambda item: -item[2])
    candidates = candidates[:max_candidates]

    lo, hi = half_life_bounds
    selected: list[tuple[str, str, float]] = []
    for a, b, _ in candidates:
        beta = hedge_ratio(log_prices[a].values, log_prices[b].values)
        if beta <= 0:
            continue
        spread = log_prices[a] - beta * log_prices[b]
        hl = half_life(spread)
        if lo < hl < hi:
            selected.append((a, b, beta))
    return selected


# --- backtests -----------------------------------------------------------------


def walk_forward(
    prices: pd.DataFrame,
    formation: int = 252,
    step: int = 63,
    window: int = 40,
    entry: float = 2.0,
    exit: float = 0.5,
    cost_bps: float = 5.0,
    **select_kwargs,
) -> tuple[pd.Series, dict]:
    """Walk-forward pairs backtest. Every traded bar is out-of-sample.

    For each `step`-day block the pairs are re-selected on the prior `formation`
    days, then traded over the next block. Concatenating the blocks gives a track
    record with no lookahead in either selection or signals.
    """
    log_prices = np.log(prices)
    returns = prices.pct_change().fillna(0.0)
    index = prices.index
    n = len(index)

    pnl = pd.Series(0.0, index=index)
    pairs_per_block: list[int] = []

    start = formation
    while start + 1 < n:
        end = min(start + step, n)
        form_returns = returns.iloc[start - formation : start]
        form_logs = log_prices.iloc[start - formation : start]
        pairs = select_pairs(form_returns, form_logs, **select_kwargs)
        pairs_per_block.append(len(pairs))

        if pairs:
            # Compute each pair over a warmup+block slice, keep only the block.
            warm = max(0, start - window - 5)
            sliced_logs = log_prices.iloc[warm:end]
            sliced_returns = returns.iloc[warm:end]
            block = pd.concat(
                [
                    pair_pnl(sliced_logs, sliced_returns, a, b, beta, window, entry, exit, cost_bps)
                    for a, b, beta in pairs
                ],
                axis=1,
            ).mean(axis=1)
            block = block.reindex(index[start:end])
            pnl.loc[block.index] = block.values
        start = end

    diagnostics = {
        "avg_pairs_per_block": float(np.mean(pairs_per_block)) if pairs_per_block else 0.0,
        "blocks": len(pairs_per_block),
        "formation": formation,
        "step": step,
    }
    return pnl.iloc[formation:], diagnostics


def vol_target(pnl: pd.Series, target_vol: float = 0.10, lookback: int = 20) -> np.ndarray:
    """Scale a PnL stream to a constant annualized volatility (causal)."""
    realized = pnl.rolling(lookback).std().shift(1)
    daily_target = target_vol / np.sqrt(252)
    scale = (daily_target / realized.replace(0, np.nan)).clip(upper=4).fillna(0.0)
    return (pnl * scale).to_numpy()
