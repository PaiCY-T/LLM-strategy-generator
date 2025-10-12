# V5 Strategy: Smart Money Momentum (Simplified - Using Only Available Data)
# Philosophy: Foreign institutional flow + Quality + Momentum
# Date: 2025-10-10
#
# Key Changes:
#   1. Use ONLY verified available datasets
#   2. Foreign net buy as primary signal (proven to work)
#   3. Quality filters: ROE + Operating Margin + Revenue Growth
#   4. Multiple exit signals for better risk control
#   5. Moderate concentration (10 stocks) for balance

from finlab import data, backtest
import pandas as pd

# --- Data Loading (Only Verified Datasets) ---
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
high = data.get('price:最高價')
low = data.get('price:最低價')

# Smart Money: Foreign Institutional Flow (VERIFIED)
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')

# Quality Factors
roe = data.get('fundamental_features:ROE稅後')
op_margin = data.get('fundamental_features:營業利益率')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
pe_ratio = data.get('price_earning_ratio:本益比')

# --- Parameters ---
N_STOCKS = 10
FOREIGN_FLOW_DAYS = 20      # 20-day cumulative foreign flow
MOMENTUM_PERIOD = 40        # 40-day momentum
EXIT_MA_PERIOD = 30         # Exit if below 30-day MA
MIN_ROE = 8                 # Minimum ROE
MIN_OP_MARGIN = 3           # Minimum operating margin %
MAX_PE = 25                 # Maximum P/E ratio
EXIT_FOREIGN_SELLING_DAYS = 5  # Exit if foreign selling for 5 days

# --- Factor Construction ---

# 1. Smart Money Factor (40% weight)
# Cumulative foreign net buying over 20 days
foreign_flow_20d = foreign_net_buy.rolling(FOREIGN_FLOW_DAYS).sum()
foreign_flow_rank = foreign_flow_20d.rank(axis=1, pct=True)

# 2. Momentum Factor (30% weight)
momentum = close.pct_change(MOMENTUM_PERIOD)
momentum_rank = momentum.rank(axis=1, pct=True)

# 3. Quality Factor (20% weight)
# Combine ROE and Operating Margin
quality_score = roe * (op_margin / 100)  # op_margin is in percentage
quality_rank = quality_score.rank(axis=1, pct=True)

# 4. Value Factor (10% weight)
# Lower P/E is better
value_rank = pe_ratio.rank(axis=1, pct=True, ascending=False)

# Combined Score
final_score = (
    foreign_flow_rank * 0.40 +
    momentum_rank * 0.30 +
    quality_rank * 0.20 +
    value_rank * 0.10
)

# --- Multi-Layer Entry Filters ---

# Filter 1: Liquidity
turnover = close * volume
liquidity_filter = (turnover.average(20) > 100_000_000) & (close > 10)

# Filter 2: Quality (Strict!)
quality_filter = (roe > MIN_ROE) & (op_margin > MIN_OP_MARGIN) & (revenue_yoy > 0)

# Filter 3: Valuation (Avoid overvalued stocks)
valuation_filter = (pe_ratio > 0) & (pe_ratio < MAX_PE)

# Filter 4: Trend (Price above MA)
trend_filter = close > close.average(EXIT_MA_PERIOD)

# Filter 5: Foreign Flow (Must be positive!)
foreign_filter = foreign_flow_20d > 0

# Combine ALL filters
tradeable_universe = (
    liquidity_filter &
    quality_filter &
    valuation_filter &
    trend_filter &
    foreign_filter
)

# Apply filters
final_score = final_score[tradeable_universe]

# --- Dynamic Exit Rules ---

# Exit 1: MA Breakdown
exit_ma_break = close < close.average(EXIT_MA_PERIOD)

# Exit 2: Foreign Institutional Selling
# If foreign investors are net sellers for N consecutive days, exit
foreign_selling_streak = foreign_net_buy.rolling(EXIT_FOREIGN_SELLING_DAYS).sum() < 0
exit_foreign_selling = foreign_selling_streak

# Exit 3: ATR-based Stop Loss
# Calculate True Range and ATR manually
tr1 = high - low
tr2 = abs(high - close.shift(1))
tr3 = abs(low - close.shift(1))
true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
atr = true_range.rolling(20).mean()

# Chandelier Exit: Price < (20-day high - 2.5 * ATR)
chandelier_level = close.rolling(20).max() - (atr * 2.5)
exit_chandelier = close < chandelier_level

# Combine ALL exit signals (any trigger = exit)
daily_exit_signals = exit_ma_break | exit_foreign_selling | exit_chandelier

# --- Position Construction ---
weekly_entries = final_score.is_largest(N_STOCKS)
positions_hold = weekly_entries.reindex(close.index, method='ffill').fillna(False)
final_positions = positions_hold & (~daily_exit_signals)

# --- Backtesting ---
report = backtest.sim(
    final_positions,
    resample="W-FRI",
    fee_ratio=1.425/1000/3,
    position_limit=1/N_STOCKS,
    name="V5_Smart_Money_Simplified"
)

# --- Results ---
print("=" * 90)
print("V5: Smart Money Momentum - Simplified (使用實際可用數據)")
print("=" * 90)
print(f"\n📊 績效指標:")
print(f"  年化報酬率: {report.metrics.annual_return():.2%}")
print(f"  夏普比率: {report.metrics.sharpe_ratio():.2f}")
print(f"  最大回撤: {report.metrics.max_drawdown():.2%}")

print(f"\n📈 歷代對比:")
versions = [
    ("單因子最佳", 2.56, 0.15, -54.50),
    ("V1 多因子", 5.38, 0.35, -26.35),
    ("V2 激進", 7.12, 0.43, -32.92),
    ("V3 Moonshot", 16.76, 0.57, -85.91),
    ("V4 風控失敗", 4.20, 0.21, -49.25),
]

for name, ret, sharpe, mdd in versions:
    print(f"  {name:15s} {ret:6.2f}% | Sharpe {sharpe:4.2f} | MDD {mdd:7.2f}%")

print(f"  {'V5 籌碼主導':15s} {report.metrics.annual_return():.2%} | Sharpe {report.metrics.sharpe_ratio():4.2f} | MDD {report.metrics.max_drawdown():.2%}")

# Calculate improvements
if report.metrics.sharpe_ratio() >= 1.5:
    sharpe_emoji = "🎉 突破目標!"
elif report.metrics.sharpe_ratio() >= 1.0:
    sharpe_emoji = "✅ 大幅改善"
elif report.metrics.sharpe_ratio() >= 0.7:
    sharpe_emoji = "⚠️ 略有改善"
else:
    sharpe_emoji = "❌ 仍需優化"

print(f"\n🎯 目標達成:")
print(f"  Sharpe > 1.5:  [{report.metrics.sharpe_ratio():.2f}] {sharpe_emoji}")
print(f"  報酬 > 20%:    [{report.metrics.annual_return():.2%}] {'✅' if report.metrics.annual_return() >= 0.20 else '❌'}")
print(f"  MDD < -30%:    [{report.metrics.max_drawdown():.2%}] {'✅' if report.metrics.max_drawdown() >= -0.30 else '❌'}")

print(f"\n💡 V5 核心特色:")
print(f"  • 外資流向 (40%): 20日累積買超排名")
print(f"  • 價格動量 (30%): 40日價格變化")
print(f"  • 企業質量 (20%): ROE × 營業利益率")
print(f"  • 估值安全 (10%): P/E < 25")
print(f"  • 嚴格篩選: ROE>8% + 營業利益率>3% + 營收成長>0% + 外資買超")
print(f"  • 三重退出: MA破位 OR 外資賣超 OR Chandelier停損")

print("=" * 90)
