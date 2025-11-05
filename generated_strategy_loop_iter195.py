# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
roe = data.get('fundamental_features:ROE稅後')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
pe_ratio = data.get('price_earning_ratio:本益比')
rsi = data.indicator('RSI')
# 2. Calculate factors
# Factor 1: Medium-term Price Momentum (60-day returns)
momentum_factor = close.pct_change(60).shift(1)
# Factor 2: Quality & Growth (ROE smoothed + Monthly Revenue YoY)
# ROE: Use 4-quarter average for stability, then forward-fill and shift
quality_roe = roe.rolling(4).mean().ffill().shift(1)
# Revenue Growth: Forward-fill monthly data to daily, then shift
growth_revenue = revenue_yoy.ffill().shift(1)
# Combine quality and growth (simple average)
quality_growth_factor = (quality_roe + growth_revenue) / 2
# Factor 3: Institutional Buying Strength (Foreign Investor Net Buy over 20 days)
# Sum foreign net buy over 20 days, then shift
institutional_flow_factor = foreign_net_buy.rolling(20).sum().shift(1)
# Factor 4: Value (Inverse P/E Ratio)
# Handle potential division by zero or negative P/E by replacing inf/-inf with NaN, then shift
value_factor = (1 / pe_ratio).replace([float('inf'), -float('inf')], float('nan')).shift(1)
# 3. Combine factors (normalize first!)
# Normalize each factor to percentile ranks [0, 1]
momentum_rank = momentum_factor.rank(axis=1, pct=True)
quality_growth_rank = quality_growth_factor.rank(axis=1, pct=True)
institutional_flow_rank = institutional_flow_factor.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
# Combine with intelligent weights (sum to 1.0)
# Prioritize momentum and quality/growth, then institutional flow, then value
combined_factor = (momentum_rank * 0.35 +
                   quality_growth_rank * 0.30 +
                   institutional_flow_rank * 0.20 +
                   value_rank * 0.15)
# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000
# Price filter: Stock price > 15 TWD (avoid penny stocks)
price_filter = close.shift(1) > 15
# RSI filter: Avoid extreme overbought/oversold conditions (RSI between 30 and 70)
rsi_filter = (rsi.shift(1) > 30) & (rsi.shift(1) < 70)
# Apply all filters
filtered_factor = combined_factor[liquidity_filter & price_filter & rsi_filter]
# 5. Select top N stocks (e.g., top 10)
position = filtered_factor.is_largest(10)
# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)