import pandas as pd

def strategy(data):
    # 1. Load necessary data with appropriate shifts to prevent look-ahead bias
    close = data.get('etl:adj_close').shift(1) # Adjusted close for price calculations
    trading_value = data.get('price:成交金額').shift(1) # For liquidity filter
    net_profit_margin = data.get('fundamental_features:稅後淨利率').shift(1) # Profitability
    pe_ratio = data.get('price_earning_ratio:本益比').shift(1) # Valuation
    revenue_mom = data.get('monthly_revenue:上月比較增減(%)').shift(1) # Revenue momentum

    # 2. Liquidity Filter: Ensure average daily trading value is above 150M TWD
    # Calculate 20-day simple moving average of trading value
    avg_trading_value = trading_value.rolling(window=20, min_periods=10).mean()
    liquid_stocks = avg_trading_value > 150_000_000

    # 3. Price Momentum: Calculate 20-day price momentum
    # Use adjusted close price to calculate momentum
    momentum_20d = (close / close.rolling(window=20, min_periods=10).mean()) - 1
    # Select top 30% stocks by momentum
    top_momentum = momentum_20d.rank(axis=1, pct=True) > 0.7

    # 4. Profitability & Valuation Filter: Combine Net Profit Margin and PE Ratio
    # High net profit margin (above median) implies good profitability
    high_profitability = net_profit_margin.rank(axis=1, pct=True) > 0.5

    # Low PE ratio (below 25th percentile, but not negative/too low indicating distress)
    # Ensure PE is positive and not excessively high
    low_pe = (pe_ratio < pe_ratio.quantile(0.25, axis=1)) & (pe_ratio > 5)

    # 5. Revenue Momentum Filter: Look for companies with increasing revenue month-over-month
    # Revenue momentum above 0 implies growth
    positive_revenue_mom = revenue_mom > 0

    # 6. Combine all filters
    # The champion strategy relied on strong momentum and low drawdowns.
    # We enhance it by adding profitability, valuation, and revenue growth.
    # The liquidity filter is crucial for tradability.
    combined_signal = (
        liquid_stocks
        & top_momentum
        & high_profitability
        & low_pe
        & positive_revenue_mom
    )

    # Handle NaN values by filling with False
    position = combined_signal.fillna(False)

    return position