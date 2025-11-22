# 1. Load data
close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
trading_value = data.get('price:成交金額')  # OK for liquidity filter
market_cap = data.get('etl:market_value') # Underused factor, used for filter
# Underused factors for core strategy
pb_ratio = data.get