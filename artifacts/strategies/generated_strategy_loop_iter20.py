# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
pe_ratio = data.get('price_earning_ratio:本益比')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')

# 2. Calculate factors

# Factor 1: Momentum (20-day returns)
returns_20d = close.pct_change(20)
momentum_factor = returns_20d.rank(axis=1, pct=True).shift(1)

# Factor 2: Value (P/E ratio)
# Filter out non-positive P/E ratios as they are not indicative of value
pe_ratio_filtered = pe_ratio.copy()
pe_ratio_filtered[pe_ratio_filtered <= 0] = float('nan')
# Rank P/E ratios, lower P/E is better (higher rank)
value_factor = pe_ratio_filtered.rank(axis=1, ascending=False, pct=True).shift(1)

# Factor 3: Growth (Monthly Revenue YoY)
# Rank revenue YoY, higher growth is better
growth_factor = revenue_yoy.rank(axis=1, pct=True).shift(1)

# Factor 4: Institutional Flow (Foreign Investor Net Buy)
# Sum foreign net buy over 5 days
foreign_flow_sum = foreign_net_buy.rolling(5).sum()
# Rank foreign flow, higher net buy is better
foreign_flow_factor = foreign_flow_sum.rank(axis=1, pct=True).shift(1)

# 3. Combine factors
# Equal weighting for simplicity
combined_factor = (
    momentum_factor * 0.25 +
    value_factor * 0.25 +
    growth_factor * 0.25 +
    foreign_flow_factor * 0.25
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50 million TWD
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 50_000_000

# 5. Select stocks
# Apply the liquidity filter and select the top 8 stocks based on the combined factor
position = combined_factor[liquidity_filter].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)