# 📈 Deep Backtest for Mean Reversion Strategy

This repository contains a **deep historical backtesting engine** for the [Mean Reversion Strategy](https://github.com/alexmueller07/Mean-Reversion-Strategy), a trading algorithm focused on capturing short-term inefficiencies in highly liquid, large-cap U.S. stocks.

> **Important:** This repo is **not the live trading engine**.  
> If you're looking for the live execution system that trades this strategy in real-time, go to:  
> 🔗 [github.com/alexmueller07/Mean-Reversion-Strategy](https://github.com/alexmueller07/Mean-Reversion-Strategy)

---

## 🧠 About This Project

This backtesting engine is purpose-built for analyzing the performance of a mean reversion strategy on a universe of 100 highly liquid U.S. stocks. It simulates the strategy over historical data and evaluates:

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

The strategy is typically applied on **daily** or **intraday** OHLCV data using standard statistical thresholds.

---

## Results

<img width="1919" height="1199" alt="image" src="https://github.com/user-attachments/assets/b7572f42-0c2b-4024-bfde-2d3a6b8df6fd" />

Note: This is the results for a one week period. Due to yfinance limits on free API I could only check week to week. I ended up checking every week and this result is from week #2 which is the closest to average. The other weeks went {Week 1: +%4.2

---

## 💡 Features

- ✅ Historical backtest across **100 top U.S. tickers**
- ✅ Slippage and commission simulation
- ✅ Dynamic portfolio sizing / capital constraints
- ✅ Configurable reversion signal (z-score, Bollinger, etc.)
- ✅ Performance reporting + trade logs
- ✅ Plug-and-play integration with live trading bot

---

## 📦 Ticker Universe

This strategy runs on a universe of **100 unique, highly liquid U.S. stocks**, drawn from the top of the S&P 500 and other mega/large-cap companies with strong liquidity profiles.

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
├── tickers.py            # List of top 100 tickers
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

