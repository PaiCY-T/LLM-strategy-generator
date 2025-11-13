# 1. Load data
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
trading_value = data.get('price:成交金額')  # OK for liquidity filter
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')
foreign_net_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
rsi = data.indicator('RSI')
market_cap = data.get('etl:market_value')

# 2. Calculate factors
# Factor 1: Price Momentum (60-day returns)
momentum = close.pct_change(60).shift(1)

# Factor 2: Revenue Growth (monthly data aligned to daily)
revenue_growth = revenue_yoy.ffill().shift(1)

# Factor 3: Quality (ROE with 4-quarter smoothing)
quality = roe.rolling(4).mean().ffill().shift(1)

# Factor 4: Institutional Flow (10-day sum of foreign net buy)
institutional_flow = foreign_net_buy.rolling(10).sum().ffill().shift(1)

# Factor 5: RSI (momentum/reversal indicator)
rsi_level = rsi.shift(1)

# 3. Combine factors (normalize first!)
momentum_rank = momentum.rank(axis=1, pct=True)
revenue_rank = revenue_growth.rank(axis=1, pct=True)
quality_rank = quality.rank(axis=1, pct=True)
flow_rank = institutional_flow.rank(axis=1, pct=True)
rsi_rank = rsi_level.rank(axis=1, pct=True)

combined_factor = (momentum_rank * 0.30 +
                   revenue_rank * 0.25 +
                   quality_rank * 0.20 +
                   flow_rank * 0.15 +
                   rsi_rank * 0.10)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days > 50M TWD
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 50_000_000

# Price filter: Adjusted close price > 10 TWD
price_filter = close.shift(1) > 10

# Market Cap filter: Market cap > 5B TWD
market_cap_filter = market_cap.shift(1) > 5_000_000_000

# RSI filter: RSI between 30 and 70 (avoiding extreme overbought/oversold)
rsi_filter = (rsi_level > 30) & (rsi_level < 70)

filtered_factor = combined_factor[liquidity_filter & price_filter & market_cap_filter & rsi_filter]

# 5. Select stocks
# Select top 10 stocks based on combined factor score
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)