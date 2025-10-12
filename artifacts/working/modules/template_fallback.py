"""
Template Fallback System for AI-Generated Strategy Code

This module provides a known-good fallback strategy template when AI-generated code
fails AST validation or other critical checks. The fallback strategy is based on
the champion strategy (Iteration 6) with a Sharpe ratio of 2.4751.

Design Philosophy:
- Use proven high-performing strategy (validated in production)
- Robust parameter selection (60-day momentum, fundamental factors)
- Defensive coding (proper fillna, shift operations)
- Simple but effective (multi-factor combination)

Author: Autonomous Iteration Engine
Created: 2025-10-09
Champion Strategy: Iteration 6 (Sharpe: 2.4751)
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Champion strategy metrics for validation reference
CHAMPION_METRICS = {
    'iteration': 6,
    'sharpe_ratio': 2.4751,
    'total_return': 0.4823,  # Example - adjust based on actual data
    'max_drawdown': -0.0854,  # Example - adjust based on actual data
    'strategy_type': 'Multi-Factor (Momentum + Fundamentals + Technical)',
    'validation_date': '2025-10-09',
}


def get_fallback_strategy() -> str:
    """
    Return a known-good template strategy as fallback.

    This strategy is based on the champion from Iteration 6 (Sharpe: 2.4751).
    It uses a balanced multi-factor approach combining:
    - Momentum (60-day percentage change) - 35%
    - Revenue YoY growth - 30%
    - EPS growth - 25%
    - Inverse RSI (oversold signal) - 10%

    Filters:
    - Liquidity: 20-day avg trading value > 50M TWD
    - Price: 20-day avg close > 10 TWD (avoid penny stocks)

    Returns:
        str: Python code string for the fallback strategy

    Example:
        >>> code = get_fallback_strategy()
        >>> len(code) > 100
        True
        >>> 'position' in code and 'sim(' in code
        True
    """
    logger.info(f"Using fallback strategy (Champion: Iteration {CHAMPION_METRICS['iteration']}, "
                f"Sharpe: {CHAMPION_METRICS['sharpe_ratio']:.4f})")

    fallback_code = '''# FALLBACK STRATEGY - Champion Template (Iteration 6)
# Sharpe Ratio: 2.4751 (validated in production)
# Strategy: Multi-Factor (Momentum + Fundamentals + Technical)

# 1. Load data
close = data.get('price:收盤價')
trading_value = data.get('price:成交金額')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
eps = data.get('financial_statement:每股盈餘')
rsi = data.indicator('RSI')

# 2. Calculate factors
# Factor 1: Medium-term Momentum (60-day percentage change)
momentum = close.pct_change(60)
momentum = momentum.shift(1)

# Factor 2: Monthly Revenue YoY Growth
# This dataset already provides YoY growth, so we use it directly.
revenue_growth_factor = revenue_yoy.shift(1)

# Factor 3: EPS Growth (Year-over-Year, assuming quarterly EPS)
# Compares current EPS with EPS from 4 quarters ago.
eps_growth = eps.pct_change(4)
eps_growth = eps_growth.shift(1)

# Factor 4: Inverse RSI (Lower RSI values indicate oversold, which can be a buy signal)
# We want to rank stocks with lower RSI higher, so we use 100 - RSI.
inverse_rsi = 100 - rsi
inverse_rsi = inverse_rsi.shift(1)

# 3. Combine factors
# We combine the factors with weights. Higher weights for fundamental growth and momentum.
# Fill NaN values with 0 for combination, as they represent missing data for the factor.
combined_factor = (
    momentum.fillna(0) * 0.35 +
    revenue_growth_factor.fillna(0) * 0.30 +
    eps_growth.fillna(0) * 0.25 +
    inverse_rsi.fillna(0) * 0.10
)

# 4. Apply filters
# Liquidity filter: Average daily trading value over 20 days must be greater than 50 million TWD.
liquidity_filter = trading_value.rolling(20).mean() > 50_000_000
liquidity_filter = liquidity_filter.shift(1)

# Price filter: Average close price over 20 days must be greater than 10 TWD to avoid penny stocks.
price_filter = close.rolling(20).mean() > 10
price_filter = price_filter.shift(1)

# Combine all filters
all_filters = liquidity_filter & price_filter

# 5. Select stocks
# Apply the combined filters to the combined factor.
# Then, select the top 10 stocks based on the filtered factor.
filtered_factor = combined_factor[all_filters]
position = filtered_factor.is_largest(10)

# 6. Run backtest
report = sim(position, resample="Q", upload=False, stop_loss=0.08)
'''

    return fallback_code


def get_champion_metadata() -> Dict[str, Any]:
    """
    Get metadata about the champion strategy used for fallback.

    Returns:
        dict: Champion strategy metrics and metadata

    Example:
        >>> metadata = get_champion_metadata()
        >>> metadata['iteration']
        6
        >>> metadata['sharpe_ratio']
        2.4751
    """
    return CHAMPION_METRICS.copy()


def log_fallback_usage(reason: str, iteration: int) -> None:
    """
    Log when fallback strategy is used and why.

    Args:
        reason: Why the fallback was triggered (e.g., "AST validation failed")
        iteration: Current iteration number

    Example:
        >>> log_fallback_usage("AST validation failed", 15)
    """
    logger.warning(f"[Iteration {iteration}] Fallback strategy triggered")
    logger.warning(f"  Reason: {reason}")
    logger.info(f"  Using champion template (Iteration {CHAMPION_METRICS['iteration']}, "
                f"Sharpe: {CHAMPION_METRICS['sharpe_ratio']:.4f})")


if __name__ == "__main__":
    # Self-test
    print("Template Fallback System - Self Test\n" + "="*60)

    # Test 1: Get fallback strategy
    code = get_fallback_strategy()
    print(f"\n✅ Test 1: Fallback strategy generated ({len(code)} chars)")
    assert len(code) > 100, "Code too short"
    assert 'position' in code, "Missing position variable"
    assert 'sim(' in code, "Missing sim() call"
    print(f"   Preview: {code[:100]}...")

    # Test 2: Get champion metadata
    metadata = get_champion_metadata()
    print(f"\n✅ Test 2: Champion metadata retrieved")
    print(f"   Iteration: {metadata['iteration']}")
    print(f"   Sharpe: {metadata['sharpe_ratio']:.4f}")
    print(f"   Strategy Type: {metadata['strategy_type']}")

    # Test 3: Log fallback usage
    print(f"\n✅ Test 3: Logging fallback usage")
    log_fallback_usage("AST validation failed", 15)

    print("\n" + "="*60)
    print("All tests passed! Fallback system ready.")
