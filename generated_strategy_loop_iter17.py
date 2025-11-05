# 1. Load data
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits, used for price filter
trading_value = data.get('price:成交金額')  # OK for liquidity filter
net_profit_margin = data.get('fundamental_features:稅後淨利率')  # Underused: Profitability
pe_ratio = data.get('price_earning_ratio:本益比')  # Underused: Valuation
revenue_mom = data.get('monthly_revenue:上月比較增減(%)')  # Underused: Short-term Growth
market_cap = data.get('etl:market_value')  # Underused: Size (as price:總市值)
# 2. Calculate factors
# Factor 1: Profitability (Net Profit Margin)
# Higher net profit margin is better
factor_profitability = net_profit_margin.ffill().shift(1)
# Factor 2: Value (Inverse P/E Ratio)
# Lower P/E is better, so we invert it for ranking
# Filter out non-positive P/E ratios before inversion to avoid infinity/NaN
factor_value = (1 / pe_ratio).ffill().shift(1)
# Factor 3: Short-term Revenue Momentum (Monthly Revenue MoM)
# Higher MoM growth is better
factor_growth = revenue_mom.ffill().shift(1)
# Factor 4: Size (Inverse Market Cap for Small-Cap Bias)
# Smaller market cap is better, so we invert it for ranking
factor_size = (1 / market_cap).shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks
profitability_rank = factor_profitability.rank(axis=1, pct=True)
value_rank = factor_value.rank(axis=1, pct=True)
growth_rank = factor_growth.rank(axis=1, pct=True)
size_rank = factor_size.rank(axis=1, pct=True)
# Combine with diverse weights
# Emphasize profitability and value, with strong growth and a small-cap bias
combined_factor = (profitability_rank * 0.35 +
                   value_rank * 0.30 +
                   growth_rank * 0.25 +
                   size_rank * 0.10)
# 4. Apply filters
# Liquidity filter: Target higher liquidity to avoid illiquid stocks
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000
# Price filter: Avoid very low-priced stocks
price_filter = close.shift(1) > 25
# P/E Ratio filter: Exclude extreme or negative P/E values for robustness
pe_ratio_valid_filter = (pe_ratio.ffill().shift(1) > 5) & (pe_ratio.ffill().shift(1) < 40)
# Net Profit Margin filter: Ensure positive profitability
profitability_positive_filter = net_profit_margin.ffill().shift(1) > 0
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & pe_ratio_valid_filter & profitability_positive_filter]
# 5. Select stocks
# Select top 10 stocks based on the combined factor score
position = filtered_factor.is_largest(10)
# 6. Run backtest
# Use quarterly rebalancing and a standard stop loss
report = sim(position, resample="Q", upload=False, stop_loss=0.08)