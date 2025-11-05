"""
Strategy Validator for Template Mode
======================================

Validates generated strategy parameters for template-guided mode with focus on:
- Risk management compliance (stop_loss, n_stocks, rebalancing frequency)
- Logical consistency between parameters (momentum-MA alignment, rebalancing-momentum)
- Warning-based validation (no hard failures to maintain flexibility)

Usage:
    from src.validation import StrategyValidator

    validator = StrategyValidator()
    is_valid, warnings = validator.validate_parameters({
        'n_stocks': 15,
        'stop_loss': 0.08,
        'resample': 'W',
        'momentum_lookback': 20,
        'ma_short': 20
    })

    if warnings:
        for warning in warnings:
            print(f"Warning: {warning}")

Task Context: Phase 0 - Template Mode (Tasks 1.9-1.12)
"""

from typing import Dict, Any, List, Tuple


class StrategyValidator:
    """
    Validates strategy parameters for template mode with risk management and consistency checks.

    Validation Philosophy:
        - All validations return warnings (not errors) to maintain flexibility
        - Risk management: Prevents extreme parameter choices
        - Logical consistency: Catches suspicious parameter combinations
        - Taiwan market-specific: Considers T+2, retail participation, concentration

    Validation Layers:
        1. Risk Management: stop_loss, n_stocks, resample frequency
        2. Logical Consistency: Parameter relationships (momentum-MA, resampling-momentum)

    Example:
        >>> validator = StrategyValidator()
        >>> is_valid, warnings = validator.validate_parameters({
        ...     'n_stocks': 3,  # Too concentrated
        ...     'stop_loss': 0.03,  # Too tight
        ...     'resample': 'D'  # Daily rebalancing
        ... })
        >>> print(warnings)
        ['Portfolio too concentrated: 3 stocks < 5 (increases volatility)',
         'Stop loss too tight: 3.0% < 5.0% (frequent exits)',
         'Daily rebalancing discouraged: high transaction costs in Taiwan market']
    """

    def __init__(self, strict_mode: bool = False):
        """
        Initialize strategy validator.

        Args:
            strict_mode: If True, convert all warnings to hard failures
                         (default: False for template mode flexibility)

        Note:
            strict_mode is reserved for future use. Currently all validations
            return warnings to maintain maximum flexibility in template mode.
        """
        self.strict_mode = strict_mode

    def _validate_risk_management(
        self,
        params: Dict[str, Any]
    ) -> List[str]:
        """
        Validate risk management parameters with Taiwan market-specific rules.

        Checks:
            1. Stop Loss: 0.05 ≤ stop_loss ≤ 0.20
               - Too tight (<5%): Frequent exits due to noise
               - Too loose (>20%): Excessive risk exposure

            2. Portfolio Size: 5 ≤ n_stocks ≤ 30
               - Too concentrated (<5): High volatility, idiosyncratic risk
               - Too large (>30): Diluted performance, over-diversification

            3. Rebalancing Frequency: Avoid 'D' (daily)
               - Taiwan T+2 settlement + high transaction costs
               - Daily rebalancing = excessive costs

        Taiwan Market Context:
            - T+2 settlement cycle (buy today, settle in 2 days)
            - High retail participation (~70% of volume)
            - Concentration in tech/financial sectors
            - Transaction costs: ~0.3% per trade (brokerage + tax)

        Args:
            params: Parameter dictionary with optional keys:
                - stop_loss: float (0.0-1.0 range, e.g., 0.08 = 8%)
                - n_stocks: int (portfolio size)
                - resample: str ('D', 'W', 'M')

        Returns:
            List of warning messages (empty if all checks pass)

        Example:
            >>> warnings = validator._validate_risk_management({
            ...     'stop_loss': 0.03,
            ...     'n_stocks': 3,
            ...     'resample': 'D'
            ... })
            >>> assert len(warnings) == 3
        """
        warnings = []

        # Check 1: Stop Loss Range (5-20%)
        if 'stop_loss' in params:
            stop_loss = params['stop_loss']

            if stop_loss < 0.05:
                warnings.append(
                    f"Stop loss too tight: {stop_loss*100:.1f}% < 5.0% "
                    f"(frequent exits due to market noise)"
                )
            elif stop_loss > 0.20:
                warnings.append(
                    f"Stop loss too loose: {stop_loss*100:.1f}% > 20.0% "
                    f"(excessive risk exposure)"
                )

        # Check 2: Portfolio Size (5-30 stocks)
        if 'n_stocks' in params:
            n_stocks = params['n_stocks']

            if n_stocks < 5:
                warnings.append(
                    f"Portfolio too concentrated: {n_stocks} stocks < 5 "
                    f"(increases volatility and idiosyncratic risk)"
                )
            elif n_stocks > 30:
                warnings.append(
                    f"Portfolio over-diversified: {n_stocks} stocks > 30 "
                    f"(diluted performance, over-diversification)"
                )

        # Check 3: Rebalancing Frequency (avoid daily)
        if 'resample' in params:
            resample = params['resample']

            if resample == 'D':
                warnings.append(
                    "Daily rebalancing discouraged: high transaction costs "
                    "(~0.3% per trade) and T+2 settlement in Taiwan market"
                )

        return warnings

    def _validate_logical_consistency(
        self,
        params: Dict[str, Any]
    ) -> List[str]:
        """
        Validate logical consistency of parameter combinations.

        Consistency Rules:
            1. Short momentum (≤10d) + Long MA (≥90d)
               - Misalignment: Fast momentum with slow trend filter
               - Suggestion: Use medium MA (20-60d) with short momentum

            2. Long momentum (≥20d) + Short MA (≤20d)
               - Misalignment: Slow momentum with fast trend filter
               - Suggestion: Use longer MA (60-90d) with long momentum

            3. Weekly rebalancing + Long momentum (≥20d)
               - Inefficient: Slow signal with frequent rebalancing
               - Suggestion: Use monthly rebalancing or shorter momentum

            4. Monthly rebalancing + Short momentum (≤10d)
               - Inefficient: Fast signal with infrequent rebalancing
               - Suggestion: Use weekly rebalancing or longer momentum

        Parameter Relationship Guidance:
            Momentum Period → MA Period → Rebalancing Frequency

            Short (5-10d) → Short-Med (20-60d) → Weekly
            Medium (10-20d) → Medium (60-90d) → Weekly-Monthly
            Long (20-60d) → Long (90-120d) → Monthly

        Args:
            params: Parameter dictionary with optional keys:
                - momentum_lookback: int (days for momentum calculation)
                - ma_short: int (days for moving average)
                - ma_long: int (days for long-term MA)
                - resample: str ('D', 'W', 'M')

        Returns:
            List of warning messages (empty if all checks pass)

        Example:
            >>> warnings = validator._validate_logical_consistency({
            ...     'momentum_lookback': 5,
            ...     'ma_short': 120,
            ...     'resample': 'W'
            ... })
            >>> assert 'Short momentum (5d) + Long MA (120d)' in warnings[0]
        """
        warnings = []

        momentum = params.get('momentum_lookback')
        ma_short = params.get('ma_short')
        ma_long = params.get('ma_long')
        resample = params.get('resample')

        # Check 1: Short momentum + Long MA misalignment
        if momentum is not None and ma_short is not None:
            if momentum <= 10 and ma_short >= 90:
                warnings.append(
                    f"Short momentum ({momentum}d) + Long MA ({ma_short}d) misalignment: "
                    f"Fast momentum signal conflicts with slow trend filter. "
                    f"Consider using medium MA (20-60d) with short momentum."
                )

        # Check 2: Long momentum + Short MA misalignment
        if momentum is not None and ma_short is not None:
            if momentum >= 20 and ma_short <= 20:
                warnings.append(
                    f"Long momentum ({momentum}d) + Short MA ({ma_short}d) misalignment: "
                    f"Slow momentum signal conflicts with fast trend filter. "
                    f"Consider using longer MA (60-90d) with long momentum."
                )

        # Check 3: Weekly rebalancing + Long momentum inefficiency
        if resample == 'W' and momentum is not None and momentum >= 20:
            warnings.append(
                f"Weekly rebalancing + Long momentum ({momentum}d) inefficiency: "
                f"Slow signal changes don't benefit from frequent rebalancing. "
                f"Consider monthly rebalancing or shorter momentum (10-15d)."
            )

        # Check 4: Monthly rebalancing + Short momentum inefficiency
        if resample == 'M' and momentum is not None and momentum <= 10:
            warnings.append(
                f"Monthly rebalancing + Short momentum ({momentum}d) inefficiency: "
                f"Fast signal changes missed by infrequent rebalancing. "
                f"Consider weekly rebalancing or longer momentum (20-30d)."
            )

        return warnings

    def validate_parameters(
        self,
        params: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate strategy parameters (main orchestrator method).

        Validation Workflow:
            1. Risk Management Validation
               - Stop loss bounds (5-20%)
               - Portfolio size (5-30 stocks)
               - Rebalancing frequency (avoid daily)

            2. Logical Consistency Validation
               - Momentum-MA alignment
               - Rebalancing-momentum efficiency
               - Parameter relationship coherence

            3. Warning Aggregation
               - All checks return warnings (not errors)
               - Maintains flexibility for template mode
               - Allows LLM to learn from validation feedback

        Args:
            params: Parameter dictionary with template parameters
                Common keys:
                    - n_stocks: int
                    - stop_loss: float (0.0-1.0)
                    - resample: str ('D', 'W', 'M')
                    - momentum_lookback: int
                    - ma_short: int
                    - ma_long: int

        Returns:
            Tuple of (is_valid: bool, warnings: List[str])
                - is_valid: Always True (warnings don't block execution)
                - warnings: List of warning messages (may be empty)

        Design Philosophy:
            Template mode prioritizes flexibility over strict validation.
            All validation issues return as warnings to allow:
            1. LLM learning from validation feedback
            2. Exploration of parameter space
            3. Discovery of unconventional strategies

            Future: strict_mode could convert warnings to errors if needed.

        Example:
            >>> validator = StrategyValidator()
            >>> is_valid, warnings = validator.validate_parameters({
            ...     'n_stocks': 15,
            ...     'stop_loss': 0.08,
            ...     'resample': 'W',
            ...     'momentum_lookback': 20,
            ...     'ma_short': 60
            ... })
            >>> assert is_valid is True
            >>> assert len(warnings) == 0  # All parameters within optimal ranges
        """
        # Step 1: Risk Management Validation
        risk_warnings = self._validate_risk_management(params)

        # Step 2: Logical Consistency Validation
        consistency_warnings = self._validate_logical_consistency(params)

        # Step 3: Aggregate Warnings
        all_warnings = risk_warnings + consistency_warnings

        # Template mode: Always valid (warnings don't block)
        # This maintains flexibility for LLM learning and exploration
        is_valid = True

        return (is_valid, all_warnings)
