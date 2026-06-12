# tests/test_statarb.py
"""Unit tests for the statistical-arbitrage building blocks."""
import numpy as np
import pandas as pd
import pytest

from statarb import (
    hedge_ratio,
    half_life,
    zscore,
    trade_positions,
    pair_pnl,
    select_pairs,
)


def test_hedge_ratio_exact_line():
    b = np.linspace(1, 10, 50)
    a = 2.0 * b + 3.0
    assert hedge_ratio(a, b) == pytest.approx(2.0, rel=1e-9)


def test_half_life_mean_reverting_is_finite():
    # Synthetic Ornstein-Uhlenbeck path mean-reverts, so half-life is finite.
    rng = np.random.default_rng(1)
    x = np.zeros(2000)
    for t in range(1, len(x)):
        x[t] = x[t - 1] - 0.05 * x[t - 1] + rng.normal(0, 0.1)
    hl = half_life(pd.Series(x))
    assert np.isfinite(hl) and hl > 0


def test_half_life_random_walk_reverts_far_slower_than_ou():
    # A random walk has no (or only spurious, very slow) mean reversion, so its
    # estimated half-life must dwarf a genuinely mean-reverting OU series.
    rng = np.random.default_rng(2)
    ou = np.zeros(3000)
    for t in range(1, len(ou)):
        ou[t] = ou[t - 1] - 0.1 * ou[t - 1] + rng.normal(0, 0.1)
    walk = np.cumsum(rng.normal(0, 1, 3000))
    assert half_life(pd.Series(ou)) < half_life(pd.Series(walk))


def test_zscore_centered():
    s = pd.Series(np.arange(100, dtype=float))
    z = zscore(s, window=10).dropna()
    # A rolling window on a linear ramp sits above its trailing mean.
    assert (z > 0).all()


def test_trade_positions_hysteresis():
    z = pd.Series([0, 2.5, 1.0, 0.2, -2.5, -1.0, 0.0])
    pos = trade_positions(z, entry=2.0, exit=0.5).tolist()
    # Enter short at 2.5, hold through 1.0, exit at 0.2; enter long at -2.5, exit at 0.0.
    assert pos == [0, -1, -1, 0, 1, 1, 0]


def test_pair_pnl_runs_and_is_finite():
    rng = np.random.default_rng(3)
    idx = pd.date_range("2020-01-01", periods=300, freq="B")
    base = np.cumsum(rng.normal(0, 1, 300)) + 100
    prices = pd.DataFrame({"A": base + rng.normal(0, 0.5, 300), "B": base}, index=idx)
    logp = np.log(prices)
    rets = prices.pct_change().fillna(0.0)
    pnl = pair_pnl(logp, rets, "A", "B", beta=1.0, window=20)
    assert len(pnl) == 300 and np.isfinite(pnl.to_numpy()).all()


def test_select_pairs_finds_cointegrated_pair():
    rng = np.random.default_rng(4)
    idx = pd.date_range("2019-01-01", periods=500, freq="B")
    base = np.cumsum(rng.normal(0, 1, 500)) + 100
    # A and B share a common trend (cointegrated); C is independent.
    prices = pd.DataFrame(
        {
            "A": base + rng.normal(0, 0.5, 500),
            "B": base + rng.normal(0, 0.5, 500),
            "C": np.cumsum(rng.normal(0, 1, 500)) + 100,
        },
        index=idx,
    )
    rets = prices.pct_change().fillna(0.0)
    # Wide half-life band so the test checks the selection logic (correlation +
    # cointegration + positive hedge), not a specific reversion speed.
    pairs = select_pairs(rets, np.log(prices), corr_threshold=0.5, half_life_bounds=(0.5, 300.0))
    assert any({a, b} == {"A", "B"} for a, b, _ in pairs)
