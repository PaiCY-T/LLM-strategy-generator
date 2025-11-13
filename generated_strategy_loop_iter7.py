# 1. Load data
import numpy as np
close = data.get('etl:adj_close')  # ✅ Use adjusted data for price filter and P/E, P/B calculation
trading_value = data.get('price:成交金額')  # OK for liquidity filter
market_cap = data.get('etl:market_value')  # Underused factor, used for market cap filter
# Underused/rare factors prioritized for diversity
pe_ratio = data.get('price_earning_ratio:本益比')
pb_ratio = data.get('price_earning_ratio:股價淨值比')
revenue_mom = data.