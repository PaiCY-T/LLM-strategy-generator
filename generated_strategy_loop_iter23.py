# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('foreign_main_force_buy_sell_summary')
pe_ratio = data.get('price_earning_ratio:本益比')

# 2. Calculate factors
# Momentum factor (60-day returns)
momentum_factor = close.pct_change(60).shift(1)

# Revenue growth factor (YoY)
# Higher YoY growth is better
revenue_growth_factor = revenue_yoy.shift(1)

# Foreign investor net buying strength
# Higher net buy volume is better
foreign_buy_factor = foreign_net_buy.shift(1)

# Value factor (inverse of P/E ratio)
# Lower P/E is better, so take inverse. Handle potential division by zero or negative P/E.
pe_ratio_shifted = pe_ratio.shift(1)
# Replace infinite values (from 1/0) with NaN and mask out non-positive P/E ratios
value_factor = (1 / pe_ratio_shifted).replace([float('inf'), -float('inf')], float('nan'))
value_factor = value_factor.mask(pe_ratio_shifted <= 0)

# Normalize factors using rank for robustness and comparability
momentum_factor_ranked = momentum_factor.rank(axis=1, pct=True)
revenue_growth_factor_ranked = revenue_growth_factor.rank(axis=1, pct=True)
foreign_buy_factor_ranked = foreign_buy_factor.rank(axis=1, pct=True)
value_factor_ranked = value_factor.rank(axis=1, pct=True)

# 3. Combine factors
# Assign weights to the ranked factors
combined_factor = (
    momentum_factor_ranked * 0.35 +
    revenue_growth_factor_ranked * 0.25 +
    foreign_buy_factor_ranked * 0.25 +
    value_factor_ranked * 0.15
)

# 4. Apply filters
# Liquidity filter: Average trading value over 20 days > 50 million TWD
avg_trading_value = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_trading_value > 50_000_000

# Price filter: Stock price > 10 TWD to avoid very low-priced stocks
price_filter = close.shift(1) > 10

# Combine all filters
final_filter = liquidity_filter & price_filter

# 5. Select stocks
# Apply filters to the combined factor and select the top 10 stocks
position = combined_factor[final_filter].is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)