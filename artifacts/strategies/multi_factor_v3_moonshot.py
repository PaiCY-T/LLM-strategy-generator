# Multi-Factor Strategy V3 - Moonshot (Catalyst-Driven Hyper-Concentrated Momentum)
# Philosophy Shift: Abandon balanced multi-factor, embrace concentrated trend-following
# Optimized by: Gemini 2.5 Pro + Claude
# Date: 2025-10-10
#
# Key Changes from V2:
#   1. Event-Driven Filter: Only stocks with 12-month high revenue
#   2. Hyper-Concentration: 5 stocks only (vs 15)
#   3. Weekly Rebalancing: Fast reaction (vs Monthly)
#   4. Pure Momentum: 100% momentum factor (no value/quality dilution)
#   5. Wider Stop Loss: 10% to avoid noise whipsaws
#
# Risk Warning: This is an EXTREMELY aggressive strategy
#   - Expected high volatility
#   - Potential for >40% drawdowns
#   - May hold significant cash during low-signal periods

from finlab import data, backtest
import pandas as pd

# --- 1. Data Loading ---
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
revenue = data.get('monthly_revenue:去年同月增減(%)')  # YoY growth rate

# --- 2. Base Universe Filtering ---
turnover = close * volume
avg_turnover_20d = turnover.average(20)
universe = (avg_turnover_20d > 150_000_000) & (close > 10)

# --- 3. V3 CORE: Event-Driven Catalyst Filter ---
# Only select stocks hitting 12-month revenue growth HIGH
# This filters to <5% of universe - the true growth champions
revenue_12m_high = revenue.rolling(12).max()
is_revenue_breakout = (revenue >= revenue_12m_high) & (revenue > 0)

# Combine filters
tradeable_universe = universe & is_revenue_breakout

# --- 4. Pure Momentum Ranking ---
# No quality, value, or volatility factors
# 100% focus on price momentum
momentum_score = close.pct_change(40)
final_score = momentum_score[tradeable_universe]

# --- 5. Hyper-Concentrated Portfolio: Top 5 Only ---
n_stocks = 5
position = final_score.is_largest(n_stocks)

# --- 6. Weekly Rebalancing: Fast & Aggressive ---
report = backtest.sim(
    position,
    resample="W-FRI",  # Weekly on Fridays
    fee_ratio=1.425/1000/3,
    stop_loss=0.10,    # Wider stop to avoid noise
    position_limit=1/n_stocks,  # 20% per stock
    name="Catalyst_Momentum_V3"
)

# --- 7. Results ---
print("=" * 60)
print("V3: 催化劑驅動超集中動量策略 (MOONSHOT)")
print("=" * 60)
print(f"年化報酬率: {report.metrics.annual_return():.2%}")
print(f"夏普比率: {report.metrics.sharpe_ratio():.2f}")
print(f"最大回撤: {report.metrics.max_drawdown():.2%}")
print("\n歷代對比:")
print(f"  單因子最佳 (Iter 14): 年化 2.56% | Sharpe 0.15 | MDD -54.50%")
print(f"  V1 多因子基準線:      年化 5.38% | Sharpe 0.35 | MDD -26.35%")
print(f"  V2 激進優化:          年化 7.12% | Sharpe 0.43 | MDD -32.92%")
print(f"  V3 超集中Moonshot:    年化 {report.metrics.annual_return():.2%} | Sharpe {report.metrics.sharpe_ratio():.2f} | MDD {report.metrics.max_drawdown():.2%}")
print("\n目標達成狀況:")
print(f"  Sharpe Ratio: > 2.0  [當前: {report.metrics.sharpe_ratio():.2f}] [達成率: {report.metrics.sharpe_ratio()/2.0*100:.1f}%] {'✅' if report.metrics.sharpe_ratio() >= 2.0 else '❌'}")
print(f"  年化報酬率: > 30%   [當前: {report.metrics.annual_return():.2%}] [達成率: {report.metrics.annual_return()/0.30*100:.1f}%] {'✅' if report.metrics.annual_return() >= 0.30 else '❌'}")
print(f"  最大回撤: < -20%    [當前: {report.metrics.max_drawdown():.2%}] [達成率: {abs(report.metrics.max_drawdown())/0.20*100:.1f}%] {'✅' if report.metrics.max_drawdown() >= -0.20 else '❌'}")
print("=" * 60)
