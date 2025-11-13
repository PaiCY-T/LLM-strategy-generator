"""
Semantic Validator - Validates trading behavior patterns for realistic constraints.

This module implements Story 5 (Semantic Validation) from the Learning System Stability Fixes spec.
It validates behavioral aspects like position concentration, turnover rates, and portfolio size
to ensure strategies exhibit realistic trading patterns.

Design Reference: design.md v1.1 lines 149-274 (ValidationHook Protocol)
Interface Contract: design.md v1.1 lines 149-198 (ValidationHook Protocol)

Key Differences from MetricValidator:
- SemanticValidator focuses on behavioral checks (position concentration, turnover, portfolio size)
- Works with position DataFrames from execution results
- Validates trading behavior patterns rather than metric calculations
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd


# ==============================================================================
# SemanticValidator - Story 5: Semantic Validation
# ==============================================================================

class SemanticValidator:
    """
    Validates strategy behavior patterns for realistic trading constraints.

    Implements ValidationHook protocol from design.md v1.1 lines 170-193.

    Key Responsibilities:
    1. Validate position concentration (no single-stock concentration >50%)
    2. Validate monthly turnover rates (should be <100% for realistic strategies)
    3. Validate average portfolio size (should be >3 stocks for diversification)
    4. Generate audit trail with position analysis

    Error Handling (Failure Mode Matrix, design.md v1.1 lines 966-968):
    - Logical Failure: Returns Tuple[bool, List[str]] with passed=False
    - System Error: Raises ValidationSystemError
    - Non-critical Failure: Logs warning, continues with validation

    Design Note:
    This validator focuses on behavioral validation using position DataFrames
    from execution results, complementing MetricValidator's mathematical checks.
    """

    def __init__(self):
        """
        Initialize SemanticValidator with no parameters.

        Establishes foundation for behavioral validation following
        the ValidationHook protocol pattern.
        """
        pass

    def check_position_concentration(
        self,
        position_df: pd.DataFrame
    ) -> Tuple[bool, str]:
        """
        Check if any single stock exceeds 20% position concentration.

        Implements Task 5.2 requirement: max position weight per stock <= 20%.
        This ensures portfolio diversification by preventing over-concentration
        in any single stock.

        Args:
            position_df: Position DataFrame with dates as index and stock tickers as columns.
                        Values represent position sizes (shares or portfolio value allocated).

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if all stocks <= 20% concentration
            - error_message: Empty string if valid, violation details if invalid

        Example:
            >>> validator = SemanticValidator()
            >>> # Concentrated portfolio (35% in stock '2330')
            >>> is_valid, error = validator.check_position_concentration(position_df)
            >>> # Returns: (False, "Position concentration violation: stock 2330 max weight 35.0% exceeds limit 20.0%")

        Design Reference:
            - tasks.md lines 165-173 (Task 5.2 specification)
            - requirements.md F5.1 (position concentration <= 20%)
        """
        # Handle empty or invalid position DataFrame
        if position_df is None or position_df.empty:
            return True, ""

        # Calculate position weights for each date
        # position_weights[date][stock] = weight of stock on that date
        position_weights = position_df.div(position_df.sum(axis=1), axis=0)

        # For each stock (column), find max weight across all dates
        max_weights = position_weights.max(axis=0)

        # Check if any stock exceeds 20% threshold
        concentration_limit = 0.20
        violations = max_weights[max_weights > concentration_limit]

        if len(violations) > 0:
            # Get the first violating stock for error message
            violating_stock = violations.index[0]
            max_weight_pct = violations.iloc[0] * 100
            is_valid = False
            error_message = (
                f"Position concentration violation: stock {violating_stock} "
                f"max weight {max_weight_pct:.1f}% exceeds limit {concentration_limit * 100:.1f}%"
            )
        else:
            is_valid = True
            error_message = ""

        return is_valid, error_message

    def check_portfolio_turnover(
        self,
        position_df: pd.DataFrame,
        rebalance_freq: str
    ) -> Tuple[bool, str]:
        """
        Check if portfolio turnover exceeds 500% annual limit.

        Implements Task 5.3 requirement: annual turnover <= 500%.
        This ensures reasonable trading costs by preventing excessive
        portfolio churn.

        Portfolio turnover measures how frequently positions change:
        - Turnover = sum(abs(position changes)) / avg_portfolio_value
        - Annual turnover = turnover * rebalances_per_year

        Args:
            position_df: Position DataFrame with dates as index and stock tickers as columns.
                        Values represent position sizes (shares or portfolio value).
            rebalance_freq: Rebalancing frequency code:
                           - 'M': Monthly (12 rebalances/year)
                           - 'Q': Quarterly (4 rebalances/year)
                           - Default: Assumes monthly if unrecognized

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if annual turnover <= 500%
            - error_message: Empty string if valid, violation details if invalid

        Example:
            >>> validator = SemanticValidator()
            >>> # High turnover portfolio (800% annual)
            >>> is_valid, error = validator.check_portfolio_turnover(position_df, 'M')
            >>> # Returns: (False, "Portfolio turnover violation: annual turnover 800.0% exceeds limit 500.0%")

        Design Reference:
            - tasks.md lines 175-182 (Task 5.3 specification)
            - requirements.md F5.2 (annual turnover <= 500%)
        """
        # Handle empty or invalid position DataFrame
        if position_df is None or position_df.empty:
            return True, ""

        # Handle single-period DataFrames (no turnover possible)
        if len(position_df) < 2:
            return True, ""

        # Step 1: Calculate position changes between rebalance dates
        # position_df.diff() gives change in position for each stock between periods
        # abs() to get total position changes regardless of direction
        # sum(axis=1) to get total change across all stocks for each date
        position_changes = position_df.diff().abs().sum(axis=1)

        # Step 2: Sum total position changes over backtest period
        # Skip first row (NaN from diff())
        total_changes = position_changes.iloc[1:].sum()

        # Step 3: Calculate average portfolio value
        # Sum across stocks (axis=1) to get total portfolio value each date
        portfolio_values = position_df.sum(axis=1)
        avg_portfolio_value = portfolio_values.mean()

        # Handle edge case: empty portfolio
        if avg_portfolio_value == 0:
            return True, ""

        # Step 4: Compute turnover
        turnover = total_changes / avg_portfolio_value

        # Step 5: Annualize based on rebalance frequency
        # Map rebalance frequency to rebalances per year
        rebalances_per_year = {
            'M': 12,  # Monthly
            'Q': 4,   # Quarterly
        }.get(rebalance_freq, 12)  # Default to monthly if unrecognized

        annual_turnover = turnover * rebalances_per_year

        # Step 6: Check if annual turnover exceeds 500% (5.0)
        turnover_limit = 5.0
        if annual_turnover > turnover_limit:
            is_valid = False
            error_message = (
                f"Portfolio turnover violation: annual turnover {annual_turnover * 100:.1f}% "
                f"exceeds limit {turnover_limit * 100:.1f}%"
            )
        else:
            is_valid = True
            error_message = ""

        # Step 7: Return validation result
        return is_valid, error_message

    def check_portfolio_size(
        self,
        position_df: pd.DataFrame
    ) -> Tuple[bool, str]:
        """
        Check if average portfolio size is within diversification range [5, 50].

        Implements Task 5.4 requirement: 5 <= avg_positions <= 50.
        This ensures effective diversification - not too concentrated (>5 stocks)
        and not over-diversified (<50 stocks).

        Portfolio size rationale:
        - Minimum 5 stocks: Ensures basic diversification (avoid concentrated risk)
        - Maximum 50 stocks: Prevents over-diversification (difficult to manage, diluted returns)

        Args:
            position_df: Position DataFrame with dates as index and stock tickers as columns.
                        Values represent position sizes (shares or portfolio value).

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if 5 <= avg_positions <= 50
            - error_message: Empty string if valid, violation details if invalid

        Example:
            >>> validator = SemanticValidator()
            >>> # Under-diversified portfolio (avg 2.5 positions)
            >>> is_valid, error = validator.check_portfolio_size(position_df)
            >>> # Returns: (False, "Portfolio size violation: average 2.5 positions below minimum 5")

            >>> # Over-diversified portfolio (avg 75 positions)
            >>> is_valid, error = validator.check_portfolio_size(position_df)
            >>> # Returns: (False, "Portfolio size violation: average 75.0 positions exceeds maximum 50")

        Design Reference:
            - tasks.md lines 184-192 (Task 5.4 specification)
            - requirements.md F5.3 (5 <= portfolio_size <= 50)
        """
        # Handle empty or invalid position DataFrame
        if position_df is None or position_df.empty:
            return True, ""

        # Step 1: Count non-zero positions per date
        # (position_df != 0) creates boolean DataFrame (True for non-zero positions)
        # .sum(axis=1) counts True values across columns for each date
        position_counts = (position_df != 0).sum(axis=1)

        # Step 2: Calculate average number of positions across dates
        avg_positions = position_counts.mean()

        # Step 3: Define portfolio size limits
        min_positions = 5
        max_positions = 50

        # Step 4: Check if avg_positions is within range [5, 50]
        if avg_positions < min_positions:
            # Too few positions - under-diversified
            is_valid = False
            error_message = (
                f"Portfolio size violation: average {avg_positions:.1f} positions "
                f"below minimum {min_positions}"
            )
        elif avg_positions > max_positions:
            # Too many positions - over-diversified
            is_valid = False
            error_message = (
                f"Portfolio size violation: average {avg_positions:.1f} positions "
                f"exceeds maximum {max_positions}"
            )
        else:
            # Within acceptable range
            is_valid = True
            error_message = ""

        # Step 5: Return validation result
        return is_valid, error_message

    def check_always_empty_or_full(
        self,
        position_df: pd.DataFrame
    ) -> Tuple[bool, str]:
        """
        Check if portfolio is always empty (never enters) or always full (never exits).

        Implements Task 5.5 requirement: detect non-trading or never-exiting strategies.
        This identifies strategies with broken logic that either:
        - Never enter positions (always empty)
        - Hold all stocks without changes (always full)

        Strategy Pattern Detection:
        - Always Empty: Strategy generates no positions (likely broken entry logic)
        - Always Full: Strategy holds all available stocks with no changes (no actual trading)

        Args:
            position_df: Position DataFrame with dates as index and stock tickers as columns.
                        Values represent position sizes (shares or portfolio value).

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if portfolio trades normally (neither always empty nor always full)
            - error_message: Empty string if valid, pattern description if invalid

        Example:
            >>> validator = SemanticValidator()
            >>> # Always empty portfolio (0 positions on all dates)
            >>> is_valid, error = validator.check_always_empty_or_full(position_df)
            >>> # Returns: (False, "Always empty portfolio: strategy never enters positions (0 positions on all 252 dates)")

            >>> # Always full portfolio (50 positions on all dates, never changes)
            >>> is_valid, error = validator.check_always_empty_or_full(position_df)
            >>> # Returns: (False, "Always full portfolio: strategy never exits positions (50 positions on all 252 dates)")

        Design Reference:
            - tasks.md lines 194-202 (Task 5.5 specification)
            - requirements.md F5.4 (detect always-empty or always-full portfolios)
        """
        # Handle empty or invalid position DataFrame
        if position_df is None or position_df.empty:
            return True, ""

        # Step 1: Count non-zero positions per date
        # (position_df != 0) creates boolean DataFrame (True for non-zero positions)
        # .sum(axis=1) counts True values across columns for each date
        position_counts = (position_df != 0).sum(axis=1)

        # Step 2: Check if always empty (0 positions on all dates)
        if position_counts.eq(0).all():
            is_valid = False
            num_dates = len(position_counts)
            error_message = (
                f"Always empty portfolio: strategy never enters positions "
                f"(0 positions on all {num_dates} dates)"
            )
            return is_valid, error_message

        # Step 3: Check if always full (same position count on all dates = universe size)
        # This detects strategies that hold all stocks without any changes
        if position_counts.nunique() == 1:
            # Portfolio has same number of positions on all dates
            total_universe_size = len(position_df.columns)
            constant_position_count = position_counts.iloc[0]

            # Check if this constant count equals the universe size (holding all stocks)
            if constant_position_count == total_universe_size:
                is_valid = False
                num_dates = len(position_counts)
                error_message = (
                    f"Always full portfolio: strategy never exits positions "
                    f"({constant_position_count} positions on all {num_dates} dates)"
                )
                return is_valid, error_message

        # Step 4: Neither always empty nor always full - portfolio trades normally
        is_valid = True
        error_message = ""
        return is_valid, error_message

    def validate_strategy(
        self,
        code: str,
        execution_result: Optional[Any] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate strategy behavioral patterns.

        Args:
            code: Generated strategy code (for context)
            execution_result: FinlabReport object with position DataFrame

        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
            - is_valid: True if all behavioral checks pass
            - error_messages: List of validation failure descriptions

        Example:
            validator = SemanticValidator()
            is_valid, errors = validator.validate_strategy(code, report)
            if not is_valid:
                for error in errors:
                    print(f"Behavioral issue: {error}")

        Note:
            Specific check methods (position concentration, turnover, portfolio size)
            will be implemented in subsequent tasks (5.2-5.5).
        """
        errors = []

        # Placeholder for behavioral checks (Tasks 5.2-5.5)
        # TODO Task 5.2: Implement position concentration check
        # TODO Task 5.3: Implement monthly turnover check
        # TODO Task 5.4: Implement portfolio size check
        # TODO Task 5.5: Integrate all checks into validate_strategy

        # Return validation result
        is_valid = len(errors) == 0
        return is_valid, errors
