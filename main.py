import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from config import TICKERS, SMA_PERIOD, PERCENTILES

def super_plot(ticker, df, sma, percentile_values):
    plt.figure(figsize=(14, 7))
    plt.title(f"Super Plot for {ticker}")

    close = df["Close"]
    plt.plot(close, alpha=0.5, label="Close")
    plt.plot(sma, alpha=0.5, label="SMA")

    plt.scatter(df.index, df["Buy"], color="green", label="Buy Signal", marker="^", alpha=1)
    plt.scatter(df.index, df["Sell"], color="red", label="Sell Signal", marker="v", alpha=1)

    upper_bound = sma * percentile_values[-1]
    middle_bound = sma * percentile_values[2]
    lower_bound = sma * percentile_values[0]

    plt.plot(upper_bound, c="red", linestyle="--", label="85th percentile (price)")
    plt.plot(middle_bound, c="yellow", linestyle="--", label="50th percentile (price)")
    plt.plot(lower_bound, c="green", linestyle="--", label="15th percentile (price)")

    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.legend()
    plt.show()


def backtest(df, initial_capital, percentiles):
    capital = initial_capital
    shares_held = 0
    equity_curve = []

    position_state = 0  # +1 = long, -1 = short, 0 = flat
    last_price = df["Close"].iloc[0]

    buy = percentiles[0]
    sell = percentiles[-1]
    mid_buy = percentiles[1]
    mid_sell = percentiles[3]

    for i in range(1, len(df)):
        current_price = df["Close"].iloc[i]
        current_ratio = df["Ratios"].iloc[i]
        signal = df["Positions"].iloc[i]

        # Close previous position
        if position_state == 1:
            capital += shares_held * (current_price - last_price)
        elif position_state == -1:
            capital += shares_held * (last_price - current_price)

        # Reset for new trade
        cash = capital
        shares_held = 0
        position_state = 0

        # New position sizing
        if signal == 1:
            pos_size_pct = 100 * min(2, 0.25 * ((buy - current_ratio) / (buy - mid_buy)))
            dollar_amt = cash * (pos_size_pct / 100.0)
            shares_held = int(dollar_amt // current_price)
            capital -= shares_held * current_price
            position_state = 1

        elif signal == -1:
            pos_size_pct = 100 * min(2, 0.25 * ((current_ratio - sell) / (mid_sell - sell)))
            dollar_amt = cash * (pos_size_pct / 100.0)
            shares_held = int(dollar_amt // current_price)
            capital -= shares_held * current_price
            position_state = -1

        # Equity = cash + market value of position
        if position_state == 1:
            equity = capital + shares_held * current_price
        elif position_state == -1:
            equity = capital + shares_held * (2 * last_price - current_price)
        else:
            equity = capital

        equity_curve.append(equity)
        last_price = current_price

    df["Equity"] = [initial_capital] + equity_curve
    return df["Equity"].iloc[-1]


def plot_backtest(df, initial_capital, percentiles):
    backtest(df, initial_capital, percentiles)
    prices = df["Close"]
    buy_and_hold = initial_capital * (prices / prices.iloc[0])

    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df["Equity"], label="Mean Reversion Strategy")
    plt.plot(df.index, buy_and_hold, label="Buy and Hold", linestyle='--')
    plt.title("Equity Curve vs Buy-and-Hold")
    plt.xlabel("Time")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def mass_backtest(dfs, initial_capital):
    profit_loss = 0
    num_outperformed = 0
    num_profitable = 0
    buy_and_hold_total = 0
    num_loops = 0

    for ticker, df in dfs.items():
        num_loops += 1
        temp = initial_capital
        strategy_final = backtest(df.copy(), initial_capital, np.percentile(df["Ratios"].dropna(), PERCENTILES))
        buy_and_hold_final = initial_capital * (df["Close"].iloc[-1] / df["Close"].iloc[0])

        num_profitable += strategy_final > temp
        num_outperformed += strategy_final > buy_and_hold_final
        profit_loss += (strategy_final - initial_capital)
        buy_and_hold_total += (buy_and_hold_final - initial_capital)

    final_strategy_capital = initial_capital + profit_loss
    final_buy_and_hold_capital = initial_capital + buy_and_hold_total

    print("============== BACKTEST RESULTS ==============")
    print(f"Starting Capital: {initial_capital}")
    print(f"Final Capital: {final_strategy_capital}")
    print(f"The Strategy Returned: {(final_strategy_capital - initial_capital)/initial_capital * 100:.2f}%")
    print("------------------------")
    print(f"The Strategy Outperformed Buy and Hold: {float(num_outperformed) / num_loops * 100:.2f}% of the time")
    print(f"The Strategy was Profitable: {float(num_profitable) / num_loops * 100:.2f}% of the time")
    print(f"In this time Buy and Hold: {(final_buy_and_hold_capital - initial_capital)/initial_capital * 100:.2f}%")
    print("===============================================")

    return final_strategy_capital, final_buy_and_hold_capital, num_outperformed, num_profitable


def mass_plot(dfs, initial_capital):
    aligned_equity_curves = []
    aligned_bh_curves = []

    common_index = set.intersection(*(set(df.index) for df in dfs.values()))
    common_index = sorted(common_index)

    for ticker, df in dfs.items():
        df = df.copy()
        backtest(df, initial_capital, np.percentile(df["Ratios"].dropna(), PERCENTILES))

        df = df[df.index.isin(common_index)]
        df = df.loc[common_index]

        equity = df["Equity"].values
        bh = initial_capital * (df["Close"] / df["Close"].iloc[0]).values

        aligned_equity_curves.append(equity)
        aligned_bh_curves.append(bh)

    equity_array = np.array(aligned_equity_curves)
    bh_array = np.array(aligned_bh_curves)

    avg_equity = equity_array.mean(axis=0)
    avg_bh = bh_array.mean(axis=0)

    plt.figure(figsize=(14, 6))
    plt.plot(common_index, avg_equity, label="Average Strategy Equity")
    plt.plot(common_index, avg_bh, label="Average Buy and Hold", linestyle="--")
    plt.title("Aggregate Equity Curve of All Strategies")
    plt.xlabel("Time")
    plt.ylabel("Equity")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    pass
