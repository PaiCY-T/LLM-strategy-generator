"""
Constants module for the finlab trading system.

This module centralizes all system-wide constants including:
- Performance metric keys for standardized backtesting results
- File path constants for data persistence
- Parameter criticality levels for attribution analysis

Usage:
    from constants import METRIC_SHARPE, CHAMPION_FILE, CRITICAL_PARAMS
"""

# =============================================================================
# Performance Metric Keys
# =============================================================================
"""
Standardized keys for accessing performance metrics in backtest results.
These keys are used consistently across:
- Champion strategy tracking
- Performance comparison and attribution
- Historical analysis and reporting
"""

METRIC_SHARPE = 'sharpe_ratio'
"""str: Sharpe ratio metric key - measures risk-adjusted returns"""

METRIC_RETURN = 'annual_return'
"""str: Annual return metric key - measures absolute performance"""

METRIC_DRAWDOWN = 'max_drawdown'
"""str: Maximum drawdown metric key - measures downside risk"""

METRIC_WIN_RATE = 'win_rate'
"""str: Win rate metric key - percentage of profitable trades"""


# =============================================================================
# File Path Constants
# =============================================================================
"""
Standardized file paths for data persistence and historical tracking.
All paths are relative to the project root directory.
"""

CHAMPION_FILE = 'artifacts/data/champion_strategy.json'
"""str: Path to champion strategy persistence file - stores best-performing strategy"""

FAILURE_PATTERNS_FILE = 'artifacts/data/failure_patterns.json'
"""str: Path to failure patterns file - stores anti-patterns and failed configurations"""

HISTORY_FILE = 'artifacts/data/mvp_final_clean_history.json'
"""str: Path to historical strategy file - stores all evaluated strategies"""


# =============================================================================
# Parameter Criticality Levels
# =============================================================================
"""
Parameter classification by criticality level for performance attribution.
Used to identify which parameter changes have the most impact on strategy performance.

Classification criteria:
- CRITICAL_PARAMS: Core strategy parameters that fundamentally change behavior
- MODERATE_PARAMS: Important parameters that affect strategy tuning
- LOW_PARAMS: Minor parameters with limited impact on overall performance
"""

CRITICAL_PARAMS = ['roe_type', 'roe_smoothing_window', 'liquidity_threshold']
"""list[str]: Critical parameters - fundamental changes that significantly impact strategy behavior"""

MODERATE_PARAMS = ['revenue_handling', 'value_factor']
"""list[str]: Moderate parameters - important tuning parameters that affect strategy performance"""

LOW_PARAMS = ['price_filter', 'volume_filter']
"""list[str]: Low-impact parameters - minor filters with limited performance impact"""
