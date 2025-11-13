"""
Factor Category Enumeration

Defines categories for factor classification, mutation, and discovery in the Factor Graph System.
Categories enable:
- Category-aware mutation strategies (replace factor with same-category alternative)
- Factor library organization and discovery
- Validation logic (e.g., exit factors must follow entry factors)
- Performance tracking by factor type

Architecture: Phase 2.0+ Factor Graph System
"""

from enum import Enum


class FactorCategory(Enum):
    """
    Categories for factor classification and mutation.

    Each Factor belongs to exactly one category, enabling:
    - Intelligent mutation operations (replace with same-category alternative)
    - Factor library organization and discovery
    - Dependency validation (e.g., exit factors require entry factors)
    - Performance analysis by factor type

    Categories:
        MOMENTUM: Trend-following and momentum indicators
        VALUE: Value-based signals (fundamentals, ratios)
        QUALITY: Quality metrics (profitability, growth, stability)
        RISK: Risk management and position sizing
        EXIT: Exit logic and stop-loss mechanisms
        ENTRY: Entry signals and position initialization
        SIGNAL: Composite signals combining multiple factors

    Example:
        >>> from factor_category import FactorCategory
        >>> category = FactorCategory.MOMENTUM
        >>> category.value
        'momentum'
        >>> FactorCategory('exit')
        <FactorCategory.EXIT: 'exit'>
    """

    MOMENTUM = "momentum"
    """Trend-following and momentum indicators (RSI, MACD, moving averages)"""

    VALUE = "value"
    """Value-based signals (P/E, P/B, dividend yield, fundamental ratios)"""

    QUALITY = "quality"
    """Quality metrics (ROE, profit margins, growth stability, earnings quality)"""

    RISK = "risk"
    """Risk management (volatility, ATR, drawdown control, position sizing)"""

    EXIT = "exit"
    """Exit logic (stop-loss, take-profit, trailing stops, time-based exits)"""

    ENTRY = "entry"
    """Entry signals (breakout, pullback, reversal, pattern recognition)"""

    SIGNAL = "signal"
    """Composite signals (multi-factor combinations, ensemble methods)"""

    def __str__(self) -> str:
        """String representation for human-readable output."""
        return self.value

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"<FactorCategory.{self.name}: '{self.value}'>"
