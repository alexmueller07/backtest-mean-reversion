# tests/test_metrics.py
"""Unit tests for the performance metrics module.

Each metric is checked against a hand-computed expected value so a regression in
the math fails loudly. Run with `pytest` from the repository root.
"""
import math

import numpy as np
import pytest

from metrics import (
    annualized_return,
    equity_to_returns,
    max_drawdown,
    sharpe_ratio,
    total_return,
    win_rate,
)


def test_equity_to_returns_basic():
    returns = equity_to_returns([100, 110, 121])
    assert np.allclose(returns, [0.10, 0.10])


def test_equity_to_returns_too_short():
    assert equity_to_returns([100]).size == 0


def test_total_return():
    assert total_return([100, 150]) == pytest.approx(0.50)
    assert total_return([200, 100]) == pytest.approx(-0.50)


def test_total_return_degenerate():
    assert total_return([100]) == 0.0
    assert total_return([0, 100]) == 0.0


def test_max_drawdown():
    # Peak 120 -> trough 90 is the worst decline: (90 - 120) / 120 = -0.25.
    assert max_drawdown([100, 120, 90, 130]) == pytest.approx(-0.25)


def test_max_drawdown_monotonic_up_is_zero():
    assert max_drawdown([100, 110, 120]) == pytest.approx(0.0)


def test_win_rate():
    assert win_rate([1, -1, 2, 0]) == pytest.approx(0.5)
    assert win_rate([]) == 0.0


def test_sharpe_zero_volatility():
    # Constant returns have no dispersion, so Sharpe is defined here as 0.
    assert sharpe_ratio([0.01, 0.01, 0.01]) == 0.0


def test_sharpe_positive_for_positive_drift():
    rng = np.random.default_rng(0)
    returns = rng.normal(0.001, 0.01, size=1000)
    assert sharpe_ratio(returns, periods_per_year=252) > 0


def test_sharpe_matches_manual_formula():
    returns = np.array([0.01, -0.005, 0.02, 0.0, 0.015])
    expected = math.sqrt(252) * returns.mean() / returns.std(ddof=1)
    assert sharpe_ratio(returns, periods_per_year=252) == pytest.approx(expected)


def test_annualized_return_compounds():
    # Doubling over exactly one year of daily bars implies ~100% annualized.
    equity = [100.0] + [100.0 * (2 ** (i / 252)) for i in range(1, 253)]
    assert annualized_return(equity, periods_per_year=252) == pytest.approx(1.0, rel=1e-6)
