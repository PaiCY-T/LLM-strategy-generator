# 1. Load data
close = data.get('price:收盤價')
rsi = data.indicator('RSI')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_strength = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
trading_value = data.get('price:成交金額')

# 2. Calculate factors
# Factor 1: RSI Reversal - higher value means more oversold (potential bounce)
# We want to buy stocks that are relatively oversold, so (100 - RSI) will be higher for oversold stocks.
rsi_reversal_factor = (100 - rsi).shift(1)

# Factor 2: Monthly Revenue YoY Growth - higher growth is better
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 3: Foreign Investor Buying Strength - higher strength indicates institutional interest
foreign_buying_factor = foreign_strength.shift(1)

# 3. Combine factors
# Combine factors with equal weighting. All factors are designed such that higher values are desirable.
combined_factor = rsi_reversal_factor + revenue_growth_factor + foreign_buying_factor

# 4. Apply filters
# Liquidity filter: Ensure sufficient trading volume for tradability
# Average daily trading value over the past 20 days must be greater than 10 million TWD
avg_trading_value = trading_value.rolling(20).mean()
liquidity_filter = (avg_trading_value.shift(1) > 10_000_000)

# 5. Select stocks
# Apply the liquidity filter and then select the top 8 stocks based on the combined factor
position = combined_factor[liquidity_filter].is_largest(8)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)