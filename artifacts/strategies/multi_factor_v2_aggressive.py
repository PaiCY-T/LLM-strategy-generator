# Multi-Factor Strategy V2 - Aggressive Optimization
# Optimized by: Gemini 2.5 Pro + Claude
# Date: 2025-10-10
# Key Changes from V1:
#   1. Fixed .rank() lookahead issue (axis=1)
#   2. Multi-timeframe momentum (20d + 40d + 60d breakout)
#   3. Revenue acceleration (2nd derivative)
#   4. Value trap filtering (PE<30 pre-screen)
#   5. Removed take_profit to let winners run
#   6. Increased to 15 stocks for diversification
#   7. Rebalanced weights: Momentum 50% (was 40%)

from finlab import data, backtest
import pandas as pd

# --- 1. Data Loading ---
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
pe_ratio = data.get('price_earning_ratio:本益比')
roe = data.get('fundamental_features:ROE稅後')
revenue = data.get('monthly_revenue:去年同月增減(%)')

# --- 2. Universe Filtering (Liquidity & Basic Health) ---
turnover = close * volume
avg_turnover_20d = turnover.average(20)

# Basic liquidity and price filters
universe = (avg_turnover_20d > 150_000_000) & (close > 10)

# V2 Enhancement: Pre-filter to avoid value traps
# Screen out negative earnings and extreme valuations
healthy_value_universe = (pe_ratio > 0) & (pe_ratio < 30)
universe = universe & healthy_value_universe

# --- 3. Factor Calculation (V2 Aggressive Enhancements) ---

# A. Momentum Factor (Weight: 50%)
# Multi-timeframe momentum + breakout confirmation
mom_20d = close.pct_change(20)
mom_40d = close.pct_change(40)
breakout_60d = close / close.rolling(60).max().fillna(1)

# Combine momentum signals
momentum_score = (mom_20d * 0.4 + mom_40d * 0.4 + breakout_60d * 0.2)
momentum_rank = momentum_score.rank(axis=1, pct=True)

# B. Quality Factor (Weight: 25%)
# Revenue acceleration (2nd derivative) instead of simple growth
# Note: revenue is already YoY%, so we calculate its rate of change
revenue_acceleration = revenue.pct_change(3)  # 3-month change in YoY growth

# Combine ROE and revenue acceleration
quality_score = roe.fillna(0) * revenue_acceleration.fillna(0)
quality_rank = quality_score.rank(axis=1, pct=True, ascending=True)

# C. Value Factor (Weight: 15%)
# After pre-filtering, use PE ranking (lower is better)
value_rank = pe_ratio.rank(axis=1, pct=True, ascending=False)  # Lower PE = higher rank

# D. Low Volatility Factor (Weight: 10%)
volatility_40d = close.pct_change().rolling(40).std()
low_vol_rank = volatility_40d.rank(axis=1, pct=True, ascending=False)

# --- 4. Factor Combination ---
weights = {
    'momentum': 0.50,
    'quality': 0.25,
    'value': 0.15,
    'low_vol': 0.10,
}

final_score = (
    momentum_rank * weights['momentum'] +
    quality_rank * weights['quality'] +
    value_rank * weights['value'] +
    low_vol_rank * weights['low_vol']
)

# Apply universe filter
final_score = final_score[universe]

# --- 5. Portfolio Construction ---
n_stocks = 15  # Increased from 10 for better diversification
position = final_score.is_largest(n_stocks)

# --- 6. Backtesting ---
report = backtest.sim(
    position,
    resample="M",
    fee_ratio=1.425/1000/3,
    stop_loss=0.04,      # Tightened from 0.05
    # take_profit removed to let momentum winners run
    position_limit=1/n_stocks,  # Dynamic: ~6.67% per stock
    name="Aggressive_MultiFactor_V2"
)

# --- 7. Results ---
print("=== 多因子策略 V2 激進優化結果 ===")
print(f"年化報酬率: {report.metrics.annual_return():.2%}")
print(f"夏普比率: {report.metrics.sharpe_ratio():.2f}")
print(f"最大回撤: {report.metrics.max_drawdown():.2%}")
print("\n與 V1 對比:")
print("  V1: 年化 5.38% | Sharpe 0.35 | MDD -26.35%")
print(f"  V2: 年化 {report.metrics.annual_return():.2%} | Sharpe {report.metrics.sharpe_ratio():.2f} | MDD {report.metrics.max_drawdown():.2%}")
print("\n目標指標:")
print(f"  Sharpe Ratio: > 2.0  [當前: {report.metrics.sharpe_ratio():.2f}] {'✅' if report.metrics.sharpe_ratio() >= 2.0 else '❌'}")
print(f"  年化報酬率: > 30%   [當前: {report.metrics.annual_return():.2%}] {'✅' if report.metrics.annual_return() >= 0.30 else '❌'}")
print(f"  最大回撤: < -20%    [當前: {report.metrics.max_drawdown():.2%}] {'✅' if report.metrics.max_drawdown() >= -0.20 else '❌'}")
