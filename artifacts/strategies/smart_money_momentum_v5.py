# V5 Strategy: Smart Money Momentum (籌碼面主導策略)
# Philosophy: Follow institutional money, avoid retail traps
# Optimized by: Gemini 2.5 Pro (Max Thinking Mode)
# Date: 2025-10-10
#
# Core Innovation:
#   1. Smart Money Factors: Foreign + Trust institutional strength
#   2. Retail Contrarian: Low margin ratio = safer
#   3. Quality Filter: ROE > 5%, Operating Margin > 0%
#   4. Trend Filter: Price > 60-day MA
#   5. Smart Exit: MA break OR foreign net selling
#
# Target Performance:
#   - Sharpe: 1.5 - 2.0
#   - Annual Return: 20-30%
#   - MDD: <-30%

from finlab import data, backtest
import pandas as pd

# --- 1. Data Loading ---
close = data.get('price:收盤價')
volume = data.get('price:成交股數')

# Smart Money Factors (NEW!)
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')
trust_strength = data.get('etl:investment_trust_buy_sell_summary:strength')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')

# Retail Sentiment (Contrarian)
margin_ratio = data.get('etl:margin_trading_short_sales:margin_ratio')

# Quality Factors (Enhanced)
roe = data.get('fundamental_features:ROE稅後')
op_margin = data.get('fundamental_features:營業利益率')

# --- 2. Strategy Parameters ---
N_STOCKS = 10
SMART_MONEY_LOOKBACK = 20
MOMENTUM_MA_PERIOD = 60
EXIT_MA_PERIOD = 40
EXIT_SELLING_LOOKBACK = 5

# --- 3. Factor Construction & Universe Filtering ---

# A. Smart Money Composite Score (90% weight)
# Rank each factor independently, then combine
smart_money_score = (
    foreign_strength.average(SMART_MONEY_LOOKBACK).rank(axis=1, pct=True) +
    trust_strength.average(SMART_MONEY_LOOKBACK).rank(axis=1, pct=True)
)

# B. Retail Contrarian Score (10% weight)
# Lower margin ratio = better (avoid retail speculation)
retail_contrarian_score = margin_ratio.rank(axis=1, pct=True, ascending=False)

# C. Final Score
final_score = smart_money_score * 0.9 + retail_contrarian_score * 0.1

# D. Multi-Layered Entry Filters
# Filter 1: Liquidity
turnover = close * volume
base_universe = (turnover.average(20) > 100_000_000) & (close > 10)

# Filter 2: Quality (NEW!)
quality_filter = (roe > 5) & (op_margin > 0)

# Filter 3: Trend
momentum_filter = close > close.average(MOMENTUM_MA_PERIOD)

# Combine all filters
tradeable_universe = base_universe & quality_filter & momentum_filter

# Apply universe filter
final_score = final_score[tradeable_universe]

# --- 4. Dynamic Exit Rules ---
# Exit 1: Technical breakdown
exit_ma_break = close < close.average(EXIT_MA_PERIOD)

# Exit 2: Smart Money distribution (NEW!)
exit_foreign_selling = foreign_net_buy.rolling(EXIT_SELLING_LOOKBACK).sum() < 0

# Combine exit signals
daily_exit_signals = exit_ma_break | exit_foreign_selling

# --- 5. Position Construction ---
weekly_entries = final_score.is_largest(N_STOCKS)
positions_hold = weekly_entries.reindex(close.index, method='ffill').fillna(False)
final_positions = positions_hold & (~daily_exit_signals)

# --- 6. Backtesting ---
report = backtest.sim(
    final_positions,
    resample="W-FRI",
    fee_ratio=1.425/1000/3,
    position_limit=1/N_STOCKS,
    name="V5_Smart_Money_Momentum"
)

# --- 7. Results ---
print("=" * 80)
print("V5: Smart Money Momentum Strategy (籌碼面主導策略)")
print("=" * 80)
print(f"\n📊 核心績效:")
print(f"  年化報酬率: {report.metrics.annual_return():.2%}")
print(f"  夏普比率: {report.metrics.sharpe_ratio():.2f}")
print(f"  最大回撤: {report.metrics.max_drawdown():.2%}")

print(f"\n📈 策略演進對比:")
print(f"  單因子最佳:    2.56% | Sharpe 0.15 | MDD -54.50%")
print(f"  V1 多因子:     5.38% | Sharpe 0.35 | MDD -26.35%")
print(f"  V2 激進:       7.12% | Sharpe 0.43 | MDD -32.92%")
print(f"  V3 Moonshot:  16.76% | Sharpe 0.57 | MDD -85.91%")
print(f"  V4 風控失敗:   4.20% | Sharpe 0.21 | MDD -49.25%")
print(f"  V5 籌碼主導:  {report.metrics.annual_return():.2%} | Sharpe {report.metrics.sharpe_ratio():.2f} | MDD {report.metrics.max_drawdown():.2%}")

print(f"\n🎯 目標達成狀況:")
sharpe_target = 1.5
return_target = 0.20
mdd_target = -0.30

sharpe_status = "✅ 達標!" if report.metrics.sharpe_ratio() >= sharpe_target else f"❌ 未達標 (需 {sharpe_target:.1f})"
return_status = "✅ 達標!" if report.metrics.annual_return() >= return_target else f"❌ 未達標 (需 {return_target:.0%})"
mdd_status = "✅ 達標!" if report.metrics.max_drawdown() >= mdd_target else f"❌ 未達標 (需 < {mdd_target:.0%})"

print(f"  Sharpe > 1.5:  [{report.metrics.sharpe_ratio():.2f}] {sharpe_status}")
print(f"  報酬 > 20%:    [{report.metrics.annual_return():.2%}] {return_status}")
print(f"  MDD < -30%:    [{report.metrics.max_drawdown():.2%}] {mdd_status}")

print(f"\n💡 V5 核心創新:")
print(f"  ✓ 籌碼面因子: 外資力道 + 投信力道 (90%權重)")
print(f"  ✓ 散戶逆向: 低融資比例 (10%權重)")
print(f"  ✓ 質量篩選: ROE>5% + 營業利益率>0%")
print(f"  ✓ 趨勢確認: 股價>60日均線")
print(f"  ✓ 智能退出: MA破位 OR 外資連續賣超")

print("=" * 80)
