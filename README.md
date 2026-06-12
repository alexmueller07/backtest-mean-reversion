# 📈 Deep Backtest for Mean Reversion Strategy

This repository contains a **deep historical backtesting engine** for the [Mean Reversion Strategy](https://github.com/alexmueller07/Mean-Reversion-Strategy), a trading algorithm focused on capturing short-term inefficiencies in highly liquid, large-cap U.S. stocks.

> **Important:** This repo is **not the live trading engine**.  
> If you're looking for the live execution system that trades this strategy in real-time, go to:  
> 🔗 [github.com/alexmueller07/Mean-Reversion-Strategy](https://github.com/alexmueller07/Mean-Reversion-Strategy)

---

## 🧠 About This Project

This repo has two parts:

1. **A trading strategy** — a single-name mean-reversion backtest ("buy weakness,
   sell strength") with a tested metrics engine (Sharpe, drawdown, win rate) and a
   causal, lookahead-free multi-year daily backtest.
2. **A research study** — a walk-forward **statistical-arbitrage** (cointegrated
   pairs) backtest that trades the *mean reversion of a spread* rather than a
   single price, plus an honest investigation of where mean-reversion alpha does
   and does not survive out-of-sample on liquid US equities.

The guiding principle throughout is that a backtest is only worth the validation
behind it: every result here is causal, net of transaction costs, and reported
out-of-sample.

---

## 🧪 Strategies

**Single-name mean reversion** — *buy weakness, sell strength*: trade a stock's
deviation from its own moving average (z-score of the price/SMA ratio).

**Statistical-arbitrage pairs** — the spread between two cointegrated stocks is
the mean-reverting object. When it strays from its mean, go long one leg and short
the other (market-neutral), and bet on the spread reverting. Pairs are chosen by
correlation plus a cointegration/half-life filter, and **re-selected every quarter
on trailing data** so the track record is entirely out-of-sample.

### 🔬 Research finding

Naive mean reversion looks far better in-sample than it trades. Selecting pairs
once and backtesting on the same window gives an inflated Sharpe that collapses
out-of-sample as cointegration decays:

| Approach | Sharpe |
|---|---|
| Pairs, select once (in-sample) | ~1.3 |
| Same pairs, out-of-sample | ~0 |
| **Walk-forward (re-selected, fully OOS)** | **~0.33** |

The walk-forward number is the credible one. The takeaway: classical mean-reversion
edge in liquid large-caps has largely decayed, and only continuous re-selection
keeps a small, stable, positive risk-adjusted return (low ~13% drawdown, net of
5 bps costs). Regenerate with `python run_statarb.py` → `results/statarb_metrics.json`.

---

## Backtests

Two backtests are included, for two different jobs:

- **`backtest.py`** — minute-bar backtest over the most recent ~1 week (the most
  yfinance's free tier allows at 1-minute resolution). Good for a quick smoke
  test, but far too short to annualize. **Do not read its Sharpe as meaningful**:
  annualizing a week of minute returns inflates it into nonsense.
- **`daily_backtest.py`** — a multi-year **daily** backtest, which is the right
  tool for risk-adjusted metrics. Signal bands are computed on a trailing,
  one-bar-lagged window (no lookahead), and each position earns the *next* bar's
  return, matching a realistic fill.

### Latest 3-year daily run (50 large-cap U.S. equities)

| Metric | Value |
|---|---|
| Sharpe ratio | 0.85 |
| Annualized return | 7.7% |
| Total return (3y) | 24.8% |
| Max drawdown | -13.7% |
| Win rate (by ticker) | 78% |
| Buy-and-hold (3y) | 62.7% |

Read honestly: the strategy earns a positive risk-adjusted return with a shallow
drawdown, but over this window it **underperforms buy-and-hold on absolute
return** because it holds cash whenever a name is not oversold. That trade-off —
lower return, lower drawdown — is the point of measuring it properly rather than
quoting a cherry-picked short window. Numbers regenerate with
`python daily_backtest.py` and are written to `results/daily_metrics.json`.

## Tests

The metric functions and the stat-arb building blocks (hedge ratio, half-life,
z-score, entry/exit logic, pair selection) are pure and unit tested — 18 tests:

```bash
pip install -r requirements.txt
pytest
```

## Layout

| File | Purpose |
|---|---|
| `metrics.py` | Pure performance metrics (Sharpe, drawdown, win rate, returns) |
| `strategy.py` / `backtest.py` | Single-name mean-reversion signal + daily/minute backtest |
| `daily_backtest.py` | Causal multi-year daily backtest of the single-name strategy |
| `statarb.py` | Cointegration pair selection, spread z-score, walk-forward engine |
| `run_statarb.py` | Runs the walk-forward study + selection-bias demonstration |
| `tests/` | Pytest suite for metrics and stat-arb |
| `data_universe/` | Cached 10y daily closes (~112 large-caps) for the stat-arb study |

---

## 💡 Features

- ✅ Historical backtest across **a bunch of top U.S. tickers**
- ✅ Slippage and commission simulation
- ✅ Dynamic portfolio sizing / capital constraints
- ✅ Configurable reversion signal (z-score, Bollinger, etc.)
- ✅ Performance reporting + trade logs
- ✅ Plug-and-play integration with live trading bot

---

## 📦 Ticker Universe

This strategy runs on a universe of **a bunch of unique, highly liquid U.S. stocks**, drawn from the top of the S&P 500 and other mega/large-cap companies with strong liquidity profiles.

Examples include AAPL, MSFT, GOOGL, AMZN, META, TSLA, NVDA, JPM, V, JNJ, and many others.

Full list in `tickers.py`.

---

## 🚀 Live Trading Bot

This repository is complementary to the live version of the strategy found here:

👉 Mean-Reversion-Strategy (Live Bot)  
That project executes this strategy on real markets using broker APIs, manages orders, and performs live PnL tracking.

---

## 📁 Project Structure

```bash
/deep-backtest/
│
├── backtest.py           # Main backtest engine
├── strategy.py           # Entry/exit logic
├── tickers.py            # List of top a bunch of tickers
├── data/                 # Historical OHLCV data
├── results/              # Performance outputs, plots, trade logs
├── utils.py              # Helper functions
└── README.md
```

## 🛠️ Setup & Usage

Download recent data:

```bash
pip install -r requirements.txt
```

Run the backtest:

```bash
python backtest.py
```

Note: Only the past week of trading data is able to be backtested using yfinance free API. Feel free to sign up for their premium service and link your paid API keys for further backtesting.


## License

MIT License

## Disclaimer

This software is for educational purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.

## Author

Alexander Mueller

- GitHub: [alexmueller07](https://github.com/alexmueller07)
- LinkedIn: [Alexander Mueller](https://www.linkedin.com/in/alexander-mueller-021658307/)
- Email: amueller.code@gmail.com

