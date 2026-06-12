# 📈 Deep Backtest for Mean Reversion Strategy

This repository contains a **deep historical backtesting engine** for the [Mean Reversion Strategy](https://github.com/alexmueller07/Mean-Reversion-Strategy), a trading algorithm focused on capturing short-term inefficiencies in highly liquid, large-cap U.S. stocks.

> **Important:** This repo is **not the live trading engine**.  
> If you're looking for the live execution system that trades this strategy in real-time, go to:  
> 🔗 [github.com/alexmueller07/Mean-Reversion-Strategy](https://github.com/alexmueller07/Mean-Reversion-Strategy)

---

## 🧠 About This Project

This backtesting engine is purpose-built for analyzing the performance of a mean reversion strategy on a universe of a bunch of highly liquid U.S. stocks. It simulates the strategy over historical data and evaluates:

- Entry and exit performance
- Trade-level statistics (win rate, expectancy, holding time)
- Portfolio equity curves
- Exposure, drawdowns, and volatility
- Parameter sensitivity (via walk-forward optimization)

The goal is to rigorously evaluate the **robustness, profitability, and risk profile** of the strategy across market regimes before deploying it in production.

---

## 🧪 Strategy Overview

The core idea of the strategy:

> **Buy weakness, sell strength** — exploiting short-term reversions in large-cap stocks using mean-reversion signals (e.g., z-score of returns, RSI oversold conditions, Bollinger Band touches, etc.)

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

The metric functions (Sharpe, max drawdown, win rate, returns) are pure and unit
tested:

```bash
pip install -r requirements.txt
pytest
```

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

