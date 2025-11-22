import pandas as pd
import numpy as np

def strategy(data):
    # 1. Load data - ALWAYS use adjusted data for price!
    # Ensure to use the VALID_FIELDS list provided in the prompt.
    close = data.get('etl:adj_close')  # ✅ Adjusted for dividends/splits
    trading_value = data.get('price:成交金額')  # OK for liquidity filter
    pe_ratio = data.get('price_earning_ratio:本益比')
    pb_ratio = data.get('price_earning_ratio:股價淨值比')
    market_cap = data.get('etl:market_value') # Use 'etl:market_value' as per VALID_FIELDS
    
    # MFI is an indicator, assuming it's available via data.indicator()
    # If not, it needs to be calculated from raw price/volume data using FinLab's internal functions.
    # For now, let's assume `data.indicator('MFI')` works as in the champion strategy.
    mfi = data.indicator('MFI')

    # 2. Calculate factors with .shift(1) to prevent look-ahead bias
    # Price momentum: 20-day rate of change
    roc_20d = close.pct_change(20).shift(1)

    # Moving Averages for trend following and smoothing
    ma_5 = close.rolling(5).mean().shift(1)
    ma_20 = close.rolling(20).mean().shift(1)
    ma_60 = close.rolling(60).mean().shift(1)

    # 3. Liquidity filter: Average daily trading value > 150M TWD
    # Calculate 20-day average trading value
    avg_trading_value = trading_value.rolling(20).mean().shift(1)
    liquidity_filter = avg_trading_value > 150_000_000

    # 4. Value filter: Low PE and PB ratios
    # Shift PE and PB ratios to prevent look-ahead bias
    pe_filter = pe_ratio.shift(1) < 20  # Example threshold, adjust as needed
    pb_filter = pb_ratio.shift(1) < 2   # Example threshold, adjust as needed

    # 5. Momentum filter: Price above short and medium-term moving averages
    # Also, positive 20-day rate of change
    momentum_filter = (close.shift(1) > ma_5) & \
                      (close.shift(1) > ma_20) & \
                      (roc_20d > 0)
    
    # 6. MFI filter: Money Flow Index to confirm buying pressure
    # Assuming MFI values range from 0-100, MFI > 50 indicates buying pressure
    mfi_filter = mfi.shift(1) > 50

    # 7. Combine all filters to generate entry signals
    # Preserve successful patterns: momentum, moving averages, low drawdown, high win rate
    # Targeted improvements: Add value filters (PE, PB) and MFI to enhance Sharpe.
    # The combination of momentum, value, and money flow should provide a more robust signal.
    
    # We want stocks that are liquid, show positive momentum (price above MAs, positive ROC),
    # are not excessively overvalued (low PE/PB), and have positive money flow.
    entry_signal = liquidity_filter & momentum_filter & pe_filter & pb_filter & mfi_filter

    # 8. Position sizing (equal weighting for all selected stocks)
    # The strategy can return a boolean series, and FinLab will handle equal weighting.
    position = entry_signal.astype(float).fillna(0)

    # Ensure no look-ahead bias: all factors are shifted by 1 day.
    # Handle NaN values: fillna(0) for position series.
    # Maintain FinLab API constraints.

    return position

# Assume 'data' object is provided by the FinLab backtesting environment
# and 'sim' function is available.
# For demonstration, these lines would be outside the function in a FinLab environment.

# Example usage (mock objects for local testing, will be replaced by FinLab's actual objects)
# import pandas as pd
# if 'data' not in globals():
#     # Mock data for local testing if finlab isn't available
#     dates = pd.to_datetime(pd.date_range(start='2020-01-01', periods=200, freq='D'))
#     stocks = ['2330', '2454', '2303']
#     mock_data = {
#         'etl:adj_close': pd.DataFrame(np.random.rand(200, 3) * 100 + 100, index=dates, columns=stocks),
#         'price:成交金額': pd.DataFrame(np.random.rand(200, 3) * 500_000_000, index=dates, columns=stocks),
#         'price_earning_ratio:本益比': pd.DataFrame(np.random.rand(200, 3) * 30 + 5, index=dates, columns=stocks),
#         'price_earning_ratio:股價淨值比': pd.DataFrame(np.random.rand(200, 3) * 3 + 0.5, index=dates, columns=stocks),
#         'etl:market_value': pd.DataFrame(np.random.rand(200, 3) * 100_000_000_000, index=dates, columns=stocks),
#     }
#     class MockData:
#         def get(self, field):
#             return mock_data.get(field, pd.DataFrame(0, index=dates, columns=stocks))
#         def indicator(self, ind_name):
#             if ind_name == 'MFI':
#                 return pd.DataFrame(np.random.rand(200, 3) * 100, index=dates, columns=stocks) # Mock MFI
#             return pd.DataFrame(0, index=dates, columns=stocks)
#     data = MockData()
#
# def sim(position, fee_ratio, tax_ratio, resample):
#     print("Simulating backtest...")
#     # This is a mock simulation function for local testing
#     # In FinLab, this would run the actual backtest and return a report object
#     mock_report = {
#         'sharpe_ratio': 5.15,
#         'max_drawdown': -15.0,
#         'win_rate': 0.60,
#         'calmar_ratio': 0.34
#     }
#     return type('obj', (object,), mock_report)() # Simple object to mimic report attributes

# Define fee and tax ratios as per FinLab environment
# fee_ratio = 1.425 / 1000 * 2 # Buy and Sell
# tax_ratio = 3 / 1000 # Sell tax

# Execute backtest (REQUIRED)
# These variables would be defined by the FinLab environment during backtesting.
# For submission, they are typically assumed to exist or are part of the platform's setup.
# Let's define them here for completeness if running outside FinLab's direct environment.
# Assuming 'start_date', 'end_date', 'fee_ratio', 'tax_ratio' are globally available
# or passed to the script by the FinLab platform.
# For local testing, you might define them:
# start_date = '2021-01-01'
# end_date = '2023-12-31'
# fee_ratio = 0.001425
# tax_ratio = 0.003
# resample = "M"

# The following lines are part of the FinLab backtesting execution block
# and should be present exactly as requested in the output format.
position = strategy(data)
position = position.loc[start_date:end_date]
report = sim(
    position,
    fee_ratio=fee_ratio,
    tax_ratio=tax_ratio,
    resample="M"
)