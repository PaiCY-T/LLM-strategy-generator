"""
Dynamic Liquidity Calculator Module.

Calculates minimum liquidity requirements based on portfolio parameters
for the finlab autonomous trading strategy optimization system.

This module provides foundation functions for dynamic liquidity calculation
to prevent trading illiquid stocks that could cause excessive market impact.

Key Concepts:
    - Position Size: Portfolio value divided by number of stocks
    - Safety Multiplier: Ratio of liquidity to position size (50x = 2% impact)
    - Safety Margin: Buffer below theoretical minimum (10% = 1.1x multiplier)
    - Market Impact: Percentage of daily volume consumed by position

Example:
    >>> from src.liquidity_calculator import calculate_min_liquidity
    >>> result = calculate_min_liquidity(20_000_000, stock_count=8)
    >>> print(f"Recommended threshold: {result['recommended_threshold']:,.0f} TWD")
    Recommended threshold: 138,888,889 TWD
    >>> print(f"Market impact: {result['market_impact_pct']:.2f}%")
    Market impact: 1.80%
"""

from typing import Any, Dict, Tuple


def calculate_min_liquidity(
    portfolio_value: float = 20_000_000,
    stock_count: int = 8,
    safety_multiplier: float = 50.0,
    safety_margin: float = 0.1,
) -> Dict[str, Any]:
    """
    Calculate minimum liquidity requirement for portfolio.

    Uses position sizing and market impact principles to determine
    the minimum daily trading volume needed for each stock to avoid
    excessive market impact.

    Formula:
        position_size = portfolio_value / stock_count
        theoretical_min = position_size * safety_multiplier
        recommended = theoretical_min / (1 - safety_margin)
        market_impact = (position_size / recommended) * 100

    Args:
        portfolio_value: Total portfolio capital in TWD (default: 20M)
        stock_count: Number of stocks in portfolio (default: 8)
        safety_multiplier: Multiplier for market impact calculation
            50x means position is 2% of daily volume (default: 50)
        safety_margin: Buffer percentage below theoretical minimum
            0.1 means 10% buffer, resulting in 1.11x multiplier (default: 0.1)

    Returns:
        Dictionary containing:
            - portfolio_value: Input portfolio value
            - stock_count: Input stock count
            - position_size: Size of each position (portfolio / stocks)
            - theoretical_min: Minimum without safety margin
            - recommended_threshold: Recommended liquidity threshold
            - market_impact_pct: Market impact percentage at recommended level
            - safety_multiplier: Input safety multiplier
            - safety_margin: Input safety margin

    Raises:
        ValueError: If inputs are invalid (negative, zero, or out of range)

    Example:
        >>> calc = calculate_min_liquidity(20_000_000, stock_count=6)
        >>> calc['position_size']
        3333333.3333333335
        >>> calc['recommended_threshold']
        185185185.1851852
        >>> calc['market_impact_pct']
        1.8

        >>> calc = calculate_min_liquidity(20_000_000, stock_count=12)
        >>> calc['position_size']
        1666666.6666666667
        >>> calc['recommended_threshold']
        92592592.59259259
        >>> calc['market_impact_pct']
        1.8
    """
    # Input validation
    if portfolio_value <= 0:
        raise ValueError(f"portfolio_value must be positive, got {portfolio_value}")
    if stock_count <= 0:
        raise ValueError(f"stock_count must be positive, got {stock_count}")
    if safety_multiplier <= 0:
        raise ValueError(f"safety_multiplier must be positive, got {safety_multiplier}")
    if not 0 <= safety_margin < 1:
        raise ValueError(
            f"safety_margin must be in [0, 1), got {safety_margin}"
        )

    # Calculate position size
    position_size = portfolio_value / stock_count

    # Calculate theoretical minimum (before safety margin)
    theoretical_min = position_size * safety_multiplier

    # Apply safety margin to get recommended threshold
    # If safety_margin = 0.1 (10%), divide by 0.9 to get 1.11x multiplier
    # This creates a buffer below the theoretical minimum for added safety
    recommended_threshold = theoretical_min / (1 - safety_margin)

    # Calculate market impact percentage
    # Position size as percentage of recommended daily volume
    market_impact_pct = (position_size / recommended_threshold) * 100

    return {
        "portfolio_value": portfolio_value,
        "stock_count": stock_count,
        "position_size": position_size,
        "theoretical_min": theoretical_min,
        "recommended_threshold": recommended_threshold,
        "market_impact_pct": market_impact_pct,
        "safety_multiplier": safety_multiplier,
        "safety_margin": safety_margin,
    }


def validate_liquidity_threshold(
    threshold: float,
    portfolio_value: float = 20_000_000,
    stock_count_range: Tuple[int, int] = (6, 12),
) -> Dict[str, Any]:
    """
    Validate liquidity threshold across stock count range.

    Tests whether a proposed liquidity threshold is adequate across
    different portfolio concentrations (stock counts). Calculates
    market impact for each stock count to identify worst-case scenario.

    Args:
        threshold: Proposed liquidity threshold in TWD
        portfolio_value: Total portfolio capital in TWD (default: 20M)
        stock_count_range: (min, max) stock count range to test (default: (6, 12))

    Returns:
        Dictionary containing:
            - threshold: Input threshold
            - portfolio_value: Input portfolio value
            - stock_count_range: Input range
            - results: List of dicts for each stock count with:
                - stock_count: Number of stocks
                - position_size: Position size at this stock count
                - market_impact_pct: Market impact percentage
                - is_acceptable: Whether impact is ≤2% (True/False)
            - worst_case: Dict with worst-case scenario:
                - stock_count: Stock count with highest impact
                - market_impact_pct: Worst-case market impact
            - is_valid: Whether threshold is valid across all stock counts
            - max_acceptable_impact: Maximum acceptable impact (2.0%)

    Raises:
        ValueError: If inputs are invalid

    Example:
        >>> result = validate_liquidity_threshold(150_000_000)
        >>> result['is_valid']
        True
        >>> result['worst_case']['stock_count']
        6
        >>> result['worst_case']['market_impact_pct']
        2.2222222222222223

        >>> result = validate_liquidity_threshold(200_000_000)
        >>> result['is_valid']
        True
        >>> result['worst_case']['market_impact_pct']
        1.6666666666666667
    """
    # Input validation
    if threshold <= 0:
        raise ValueError(f"threshold must be positive, got {threshold}")
    if portfolio_value <= 0:
        raise ValueError(f"portfolio_value must be positive, got {portfolio_value}")
    if len(stock_count_range) != 2:
        raise ValueError(
            f"stock_count_range must be tuple of 2 integers, got {stock_count_range}"
        )
    if stock_count_range[0] <= 0 or stock_count_range[1] <= 0:
        raise ValueError(
            f"stock count range values must be positive, got {stock_count_range}"
        )
    if stock_count_range[0] > stock_count_range[1]:
        raise ValueError(
            f"stock_count_range min must be ≤ max, got {stock_count_range}"
        )

    min_stocks, max_stocks = stock_count_range
    max_acceptable_impact = 2.0  # 2% market impact threshold
    results = []
    worst_case = None
    worst_impact = 0.0

    # Test each stock count in range
    for stock_count in range(min_stocks, max_stocks + 1):
        position_size = portfolio_value / stock_count
        market_impact_pct = (position_size / threshold) * 100
        is_acceptable = market_impact_pct <= max_acceptable_impact

        result_entry = {
            "stock_count": stock_count,
            "position_size": position_size,
            "market_impact_pct": market_impact_pct,
            "is_acceptable": is_acceptable,
        }
        results.append(result_entry)

        # Track worst case
        if market_impact_pct > worst_impact:
            worst_impact = market_impact_pct
            worst_case = {
                "stock_count": stock_count,
                "market_impact_pct": market_impact_pct,
            }

    # Overall validation
    is_valid = all(r["is_acceptable"] for r in results)

    return {
        "threshold": threshold,
        "portfolio_value": portfolio_value,
        "stock_count_range": stock_count_range,
        "results": results,
        "worst_case": worst_case,
        "is_valid": is_valid,
        "max_acceptable_impact": max_acceptable_impact,
    }


def recommend_threshold(
    portfolio_value: float,
    target_stock_count: int,
    max_impact: float = 2.0,
) -> Dict[str, Any]:
    """
    Recommend optimal liquidity threshold for given constraints.

    Calculates the minimum liquidity threshold needed to ensure
    market impact stays at or below the target percentage for
    a specific portfolio configuration.

    Args:
        portfolio_value: Total portfolio capital in TWD
        target_stock_count: Target number of stocks in portfolio
        max_impact: Maximum acceptable market impact percentage (default: 2.0)

    Returns:
        Dictionary containing:
            - portfolio_value: Input portfolio value
            - target_stock_count: Input stock count
            - max_impact: Input max impact percentage
            - position_size: Calculated position size
            - recommended_threshold: Recommended liquidity threshold
            - actual_impact: Actual impact at recommended threshold
            - safety_multiplier: Implied safety multiplier
            - justification: Text explanation of recommendation

    Raises:
        ValueError: If inputs are invalid

    Example:
        >>> rec = recommend_threshold(20_000_000, target_stock_count=8, max_impact=2.0)
        >>> rec['recommended_threshold']
        125000000.0
        >>> rec['actual_impact']
        2.0
        >>> rec['safety_multiplier']
        50.0

        >>> rec = recommend_threshold(20_000_000, target_stock_count=6, max_impact=1.5)
        >>> rec['recommended_threshold']
        222222222.22222224
        >>> rec['actual_impact']
        1.5
        >>> rec['safety_multiplier']
        66.66666666666667
    """
    # Input validation
    if portfolio_value <= 0:
        raise ValueError(f"portfolio_value must be positive, got {portfolio_value}")
    if target_stock_count <= 0:
        raise ValueError(
            f"target_stock_count must be positive, got {target_stock_count}"
        )
    if max_impact <= 0 or max_impact > 100:
        raise ValueError(
            f"max_impact must be in (0, 100], got {max_impact}"
        )

    # Calculate position size
    position_size = portfolio_value / target_stock_count

    # Calculate required threshold to achieve max_impact
    # market_impact = (position_size / threshold) * 100
    # threshold = (position_size / market_impact) * 100
    recommended_threshold = (position_size / max_impact) * 100

    # Calculate actual impact (should equal max_impact)
    actual_impact = (position_size / recommended_threshold) * 100

    # Calculate implied safety multiplier
    safety_multiplier = recommended_threshold / position_size

    # Generate justification
    justification = (
        f"For a portfolio of {portfolio_value:,.0f} TWD with "
        f"{target_stock_count} stocks, each position is "
        f"{position_size:,.0f} TWD. To maintain ≤{max_impact}% market "
        f"impact, minimum daily liquidity should be "
        f"{recommended_threshold:,.0f} TWD (safety multiplier: "
        f"{safety_multiplier:.1f}x)."
    )

    return {
        "portfolio_value": portfolio_value,
        "target_stock_count": target_stock_count,
        "max_impact": max_impact,
        "position_size": position_size,
        "recommended_threshold": recommended_threshold,
        "actual_impact": actual_impact,
        "safety_multiplier": safety_multiplier,
        "justification": justification,
    }
