# 1. Load data
close = data.get('etl:adj_close')
trading_value = data.get('price:成交金額')
market_value = data.get('etl:market_value')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
roe = data.get('fundamental_features:ROE稅後')
revenue_mom = data.get('monthly_revenue:上月比較增減(%)')
inv_trust_strength = data.get('institutional_investors_trading_summary:投信買賣超股數')
mfi = data.indicator('MFI')
# 2. Calculate factors
# Factor 1: Value (Inverse Price-to-Book Ratio) - Prioritized underused factor
# Use ffill for fundamental data, then shift to avoid look-ahead
value_factor = (1 / pb_ratio).ffill().shift(1)
# Factor 2: Quality (Smoothed Return on Equity)
# Use 4-