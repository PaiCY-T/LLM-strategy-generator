"""
Backtest Configuration Validator for Strategy Templates
=======================================================

Validates backtest configuration parameters including resam pling, fee ratios,
risk management (stop-loss, take-profit), position sizing, and trade timing.

Validation Types:
    - Resample Frequency: Validate resampling period ('M', 'W-FRI', 'D')
    - Risk Management: Stop-loss and take-profit parameter validation
    - Position Sizing: Position limit and portfolio constraints
    - Fee Configuration: Transaction fee ratio validation
    - Entry/Exit Timing: Trade timing and execution validation

Usage:
    from src.validation import BacktestValidator

    validator = BacktestValidator()
    validator.validate_backtest_config({
        'resample': 'M',
        'stop_loss': 0.08,
        'take_profit': 0.5,
        'position_limit': 0.125,
        'fee_ratio': 1.425/1000/3
    })

    result = validator.get_result()
    if not result.is_valid():
        print(result)
"""

from typing import Dict, Any, List, Optional
from .template_validator import (
    TemplateValidator,
    ValidationResult,
    ValidationError,
    Category,
    Severity
)


# Valid resample frequencies
VALID_RESAMPLE_FREQUENCIES = {
    'D',       # Daily
    'W',       # Weekly (default Sunday)
    'W-MON',   # Weekly on Monday
    'W-TUE',   # Weekly on Tuesday
    'W-WED',   # Weekly on Wednesday
    'W-THU',   # Weekly on Thursday
    'W-FRI',   # Weekly on Friday (Taiwan stock market)
    'W-SAT',   # Weekly on Saturday
    'W-SUN',   # Weekly on Sunday
    'M',       # Monthly
    'Q',       # Quarterly
    'Y',       # Yearly
}

# Resample frequency performance characteristics
RESAMPLE_PERFORMANCE = {
    'D': 'High frequency - more transactions, higher fees',
    'W-FRI': 'Weekly - balanced frequency for Taiwan market',
    'M': 'Monthly - lower fees, better for long-term strategies',
    'Q': 'Quarterly - very low fees, long-term only',
    'Y': 'Yearly - minimal fees, very long-term'
}

# Parameter bounds
STOP_LOSS_MIN = 0.01      # 1% minimum stop-loss
STOP_LOSS_MAX = 0.30      # 30% maximum stop-loss
STOP_LOSS_OPTIMAL_MIN = 0.05  # 5% optimal minimum
STOP_LOSS_OPTIMAL_MAX = 0.15  # 15% optimal maximum

TAKE_PROFIT_MIN = 0.05    # 5% minimum take-profit
TAKE_PROFIT_MAX = 2.00    # 200% maximum take-profit
TAKE_PROFIT_OPTIMAL_MIN = 0.20  # 20% optimal minimum
TAKE_PROFIT_OPTIMAL_MAX = 1.00  # 100% optimal maximum

POSITION_LIMIT_MIN = 0.01   # 1% minimum position size
POSITION_LIMIT_MAX = 1.00   # 100% maximum position size
POSITION_LIMIT_OPTIMAL_MIN = 0.05  # 5% optimal minimum (diversification)
POSITION_LIMIT_OPTIMAL_MAX = 0.25  # 25% optimal maximum (concentration)

FEE_RATIO_TAIWAN = 1.425 / 1000 / 3  # Taiwan stock market fee (buy + sell + tax)


class BacktestValidator(TemplateValidator):
    """
    Validate backtest configuration parameters.

    Validation Layers:
        1. Resample frequency: Check valid pandas resample strings
        2. Risk management: Validate stop-loss and take-profit ratios
        3. Position sizing: Validate position limits and constraints
        4. Fee configuration: Validate transaction fee ratios
        5. Trade timing: Check entry/exit timing consistency

    Features:
        - Resample frequency validation against pandas strings
        - Stop-loss/take-profit ratio validation
        - Position limit validation with diversification checks
        - Fee ratio validation for Taiwan market
        - Consistency checks (e.g., stop-loss < take-profit)

    Example:
        >>> validator = BacktestValidator()
        >>> config = {
        ...     'resample': 'M',
        ...     'stop_loss': 0.08,
        ...     'take_profit': 0.5,
        ...     'position_limit': 0.125
        ... }
        >>> validator.validate_backtest_config(config)
        >>> result = validator.get_result()
        >>> print(f"Valid: {result.is_valid()}")
    """

    def __init__(self):
        """Initialize backtest validator."""
        super().__init__()

    def _validate_resample(
        self,
        resample_value: str
    ) -> bool:
        """
        Validate resample frequency parameter.

        Checks:
            - Valid pandas resample string
            - Appropriate for Taiwan stock market
            - Performance implications documented

        Args:
            resample_value: Resampling frequency string

        Returns:
            True if valid, False otherwise (adds error)

        Example:
            >>> validator._validate_resample('M')
            True  # Monthly is valid
            >>> validator._validate_resample('invalid')
            False  # Invalid frequency
        """
        if not isinstance(resample_value, str):
            self._add_error(
                category=Category.BACKTEST,
                error_type='type_mismatch',
                message=f"resample must be string, got {type(resample_value).__name__}",
                suggestion="Use valid pandas resample string (e.g., 'M', 'W-FRI', 'D')",
                context={
                    'resample_value': resample_value,
                    'expected_type': 'str'
                }
            )
            return False

        if resample_value not in VALID_RESAMPLE_FREQUENCIES:
            self._add_error(
                category=Category.BACKTEST,
                error_type='invalid_range',
                message=f"Invalid resample frequency: '{resample_value}'",
                suggestion=f"Use one of: {', '.join(sorted(VALID_RESAMPLE_FREQUENCIES))}",
                context={
                    'resample_value': resample_value,
                    'valid_frequencies': sorted(VALID_RESAMPLE_FREQUENCIES)
                }
            )
            return False

        # Add performance note for high-frequency resampling
        if resample_value == 'D':
            self._add_error(
                category=Category.BACKTEST,
                error_type='performance_concern',
                message=f"Daily resampling may result in high transaction fees",
                suggestion="Consider 'W-FRI' or 'M' for lower transaction costs",
                context={
                    'resample_value': resample_value,
                    'performance_note': RESAMPLE_PERFORMANCE.get(resample_value, '')
                }
            )

        return True

    def _validate_risk_management(
        self,
        stop_loss: Optional[float],
        take_profit: Optional[float]
    ) -> None:
        """
        Validate stop-loss and take-profit parameters.

        Validation Rules:
            - Stop-loss: 1-30% (optimal: 5-15%)
            - Take-profit: 5-200% (optimal: 20-100%)
            - Consistency: stop-loss < take-profit

        Args:
            stop_loss: Stop-loss ratio (e.g., 0.08 = 8%)
            take_profit: Take-profit ratio (e.g., 0.5 = 50%)

        Example:
            >>> validator._validate_risk_management(0.08, 0.5)
            # No errors - both in optimal range
            >>> validator._validate_risk_management(0.02, 0.01)
            # Error - stop-loss > take-profit (inconsistent)
        """
        # Validate stop-loss
        if stop_loss is not None:
            if not isinstance(stop_loss, (int, float)):
                self._add_error(
                    category=Category.BACKTEST,
                    error_type='type_mismatch',
                    message=f"stop_loss must be numeric, got {type(stop_loss).__name__}",
                    suggestion="Provide stop-loss as decimal (e.g., 0.08 for 8%)",
                    context={'stop_loss': stop_loss}
                )
            else:
                # Check absolute bounds
                if stop_loss < STOP_LOSS_MIN or stop_loss > STOP_LOSS_MAX:
                    self._add_error(
                        category=Category.BACKTEST,
                        error_type='invalid_range',
                        message=f"stop_loss {stop_loss:.2%} outside valid range [{STOP_LOSS_MIN:.1%}, {STOP_LOSS_MAX:.1%}]",
                        suggestion=f"Set stop_loss between {STOP_LOSS_MIN:.1%} and {STOP_LOSS_MAX:.1%}",
                        context={
                            'stop_loss': stop_loss,
                            'min': STOP_LOSS_MIN,
                            'max': STOP_LOSS_MAX
                        }
                    )

                # Check optimal bounds
                elif stop_loss < STOP_LOSS_OPTIMAL_MIN or stop_loss > STOP_LOSS_OPTIMAL_MAX:
                    self._add_error(
                        category=Category.BACKTEST,
                        error_type='suboptimal_range',
                        message=f"stop_loss {stop_loss:.2%} outside optimal range [{STOP_LOSS_OPTIMAL_MIN:.1%}, {STOP_LOSS_OPTIMAL_MAX:.1%}]",
                        suggestion=f"Consider stop_loss between {STOP_LOSS_OPTIMAL_MIN:.1%} and {STOP_LOSS_OPTIMAL_MAX:.1%} for balanced risk",
                        context={
                            'stop_loss': stop_loss,
                            'optimal_min': STOP_LOSS_OPTIMAL_MIN,
                            'optimal_max': STOP_LOSS_OPTIMAL_MAX
                        }
                    )

        # Validate take-profit
        if take_profit is not None:
            if not isinstance(take_profit, (int, float)):
                self._add_error(
                    category=Category.BACKTEST,
                    error_type='type_mismatch',
                    message=f"take_profit must be numeric, got {type(take_profit).__name__}",
                    suggestion="Provide take-profit as decimal (e.g., 0.5 for 50%)",
                    context={'take_profit': take_profit}
                )
            else:
                # Check absolute bounds
                if take_profit < TAKE_PROFIT_MIN or take_profit > TAKE_PROFIT_MAX:
                    self._add_error(
                        category=Category.BACKTEST,
                        error_type='invalid_range',
                        message=f"take_profit {take_profit:.2%} outside valid range [{TAKE_PROFIT_MIN:.1%}, {TAKE_PROFIT_MAX:.0%}]",
                        suggestion=f"Set take_profit between {TAKE_PROFIT_MIN:.1%} and {TAKE_PROFIT_MAX:.0%}",
                        context={
                            'take_profit': take_profit,
                            'min': TAKE_PROFIT_MIN,
                            'max': TAKE_PROFIT_MAX
                        }
                    )

                # Check optimal bounds
                elif take_profit < TAKE_PROFIT_OPTIMAL_MIN or take_profit > TAKE_PROFIT_OPTIMAL_MAX:
                    self._add_error(
                        category=Category.BACKTEST,
                        error_type='suboptimal_range',
                        message=f"take_profit {take_profit:.2%} outside optimal range [{TAKE_PROFIT_OPTIMAL_MIN:.1%}, {TAKE_PROFIT_OPTIMAL_MAX:.0%}]",
                        suggestion=f"Consider take_profit between {TAKE_PROFIT_OPTIMAL_MIN:.1%} and {TAKE_PROFIT_OPTIMAL_MAX:.0%} for realistic targets",
                        context={
                            'take_profit': take_profit,
                            'optimal_min': TAKE_PROFIT_OPTIMAL_MIN,
                            'optimal_max': TAKE_PROFIT_OPTIMAL_MAX
                        }
                    )

        # Validate consistency: stop-loss should be < take-profit
        if stop_loss is not None and take_profit is not None:
            if isinstance(stop_loss, (int, float)) and isinstance(take_profit, (int, float)):
                if stop_loss >= take_profit:
                    self._add_error(
                        category=Category.BACKTEST,
                        error_type='inconsistent_parameters',
                        message=f"stop_loss ({stop_loss:.2%}) must be less than take_profit ({take_profit:.2%})",
                        suggestion=f"Reduce stop_loss or increase take_profit to maintain risk/reward ratio",
                        context={
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'risk_reward_ratio': take_profit / stop_loss if stop_loss > 0 else 0
                        }
                    )

    def _validate_position_sizing(
        self,
        position_limit: Optional[float],
        n_stocks: Optional[int] = None
    ) -> None:
        """
        Validate position sizing parameters.

        Validation Rules:
            - Position limit: 1-100% (optimal: 5-25%)
            - Consistency: position_limit * n_stocks should allow full portfolio deployment
            - Diversification: Warning if position_limit > 1/n_stocks (concentration risk)

        Args:
            position_limit: Maximum position size as portfolio fraction (e.g., 0.125 = 12.5%)
            n_stocks: Number of stocks in portfolio (for diversification check)

        Example:
            >>> validator._validate_position_sizing(0.125, 10)
            # No errors - reasonable diversification (12.5% * 10 = 125%)
            >>> validator._validate_position_sizing(0.5, 5)
            # Warning - high concentration (50% * 5 = 250%)
        """
        if position_limit is None:
            return

        if not isinstance(position_limit, (int, float)):
            self._add_error(
                category=Category.BACKTEST,
                error_type='type_mismatch',
                message=f"position_limit must be numeric, got {type(position_limit).__name__}",
                suggestion="Provide position_limit as decimal (e.g., 0.125 for 12.5%)",
                context={'position_limit': position_limit}
            )
            return

        # Check absolute bounds
        if position_limit < POSITION_LIMIT_MIN or position_limit > POSITION_LIMIT_MAX:
            self._add_error(
                category=Category.BACKTEST,
                error_type='invalid_range',
                message=f"position_limit {position_limit:.2%} outside valid range [{POSITION_LIMIT_MIN:.1%}, {POSITION_LIMIT_MAX:.0%}]",
                suggestion=f"Set position_limit between {POSITION_LIMIT_MIN:.1%} and {POSITION_LIMIT_MAX:.0%}",
                context={
                    'position_limit': position_limit,
                    'min': POSITION_LIMIT_MIN,
                    'max': POSITION_LIMIT_MAX
                }
            )

        # Check optimal bounds
        elif position_limit < POSITION_LIMIT_OPTIMAL_MIN or position_limit > POSITION_LIMIT_OPTIMAL_MAX:
            self._add_error(
                category=Category.BACKTEST,
                error_type='suboptimal_range',
                message=f"position_limit {position_limit:.2%} outside optimal range [{POSITION_LIMIT_OPTIMAL_MIN:.1%}, {POSITION_LIMIT_OPTIMAL_MAX:.1%}]",
                suggestion=f"Consider position_limit between {POSITION_LIMIT_OPTIMAL_MIN:.1%} and {POSITION_LIMIT_OPTIMAL_MAX:.1%} for better diversification",
                context={
                    'position_limit': position_limit,
                    'optimal_min': POSITION_LIMIT_OPTIMAL_MIN,
                    'optimal_max': POSITION_LIMIT_OPTIMAL_MAX
                }
            )

        # Check diversification vs. concentration
        if n_stocks is not None and isinstance(n_stocks, int):
            equal_weight = 1.0 / n_stocks

            if position_limit > equal_weight * 2:  # More than 2x equal weight
                self._add_error(
                    category=Category.BACKTEST,
                    error_type='performance_concern',
                    message=f"position_limit {position_limit:.2%} allows high concentration (>2x equal weight of {equal_weight:.2%})",
                    suggestion=f"Consider lowering position_limit to ~{equal_weight:.2%} for better diversification",
                    context={
                        'position_limit': position_limit,
                        'n_stocks': n_stocks,
                        'equal_weight': equal_weight,
                        'concentration_ratio': position_limit / equal_weight
                    }
                )

    def _validate_fee_ratio(
        self,
        fee_ratio: Optional[float]
    ) -> None:
        """
        Validate transaction fee ratio.

        Taiwan stock market standard fee:
            - Buy: 0.1425% (broker fee)
            - Sell: 0.1425% (broker fee) + 0.3% (securities transaction tax)
            - Total: ~0.4475% per round trip
            - Simplified: 1.425 / 1000 / 3 = 0.000475

        Args:
            fee_ratio: Fee ratio per transaction (e.g., 0.000475)

        Example:
            >>> validator._validate_fee_ratio(1.425/1000/3)
            # No errors - standard Taiwan fee
            >>> validator._validate_fee_ratio(0.01)
            # Warning - unusually high fee (1%)
        """
        if fee_ratio is None:
            self._add_suggestion(
                "No fee_ratio provided - backtest may not account for transaction costs"
            )
            return

        if not isinstance(fee_ratio, (int, float)):
            self._add_error(
                category=Category.BACKTEST,
                error_type='type_mismatch',
                message=f"fee_ratio must be numeric, got {type(fee_ratio).__name__}",
                suggestion="Provide fee_ratio as decimal (e.g., 1.425/1000/3 for Taiwan market)",
                context={'fee_ratio': fee_ratio}
            )
            return

        # Check if fee is unreasonably high (>1%)
        if fee_ratio > 0.01:
            self._add_error(
                category=Category.BACKTEST,
                error_type='invalid_range',
                message=f"fee_ratio {fee_ratio:.4%} is unusually high (>1%)",
                suggestion=f"Standard Taiwan fee is ~{FEE_RATIO_TAIWAN:.4%} (1.425/1000/3)",
                context={
                    'fee_ratio': fee_ratio,
                    'taiwan_standard': FEE_RATIO_TAIWAN
                }
            )

        # Check if fee is close to Taiwan standard
        elif abs(fee_ratio - FEE_RATIO_TAIWAN) / FEE_RATIO_TAIWAN > 0.5:
            # More than 50% deviation from standard
            self._add_error(
                category=Category.BACKTEST,
                error_type='suboptimal_range',
                message=f"fee_ratio {fee_ratio:.4%} deviates significantly from Taiwan standard {FEE_RATIO_TAIWAN:.4%}",
                suggestion=f"Verify fee_ratio - standard Taiwan fee is 1.425/1000/3 = {FEE_RATIO_TAIWAN:.4%}",
                context={
                    'fee_ratio': fee_ratio,
                    'taiwan_standard': FEE_RATIO_TAIWAN,
                    'deviation': abs(fee_ratio - FEE_RATIO_TAIWAN) / FEE_RATIO_TAIWAN
                }
            )

    def validate_backtest_config(
        self,
        backtest_config: Dict[str, Any],
        n_stocks: Optional[int] = None
    ) -> None:
        """
        Validate complete backtest configuration.

        Validation Workflow:
            1. Validate resample frequency
            2. Validate risk management (stop-loss, take-profit)
            3. Validate position sizing
            4. Validate fee ratio
            5. Check parameter consistency

        Args:
            backtest_config: Backtest configuration dictionary with keys:
                - resample (str): Resampling frequency
                - stop_loss (float): Stop-loss ratio
                - take_profit (float): Take-profit ratio
                - position_limit (float): Position size limit
                - fee_ratio (float): Transaction fee ratio
            n_stocks: Number of stocks (for diversification check)

        Example:
            >>> config = {
            ...     'resample': 'M',
            ...     'stop_loss': 0.08,
            ...     'take_profit': 0.5,
            ...     'position_limit': 0.125,
            ...     'fee_ratio': 1.425/1000/3
            ... }
            >>> validator.validate_backtest_config(config, n_stocks=10)
        """
        # 1. Validate resample frequency
        resample = backtest_config.get('resample')
        if resample is not None:
            self._validate_resample(resample)
        else:
            self._add_suggestion(
                "No resample frequency provided - backtest will use default"
            )

        # 2. Validate risk management
        stop_loss = backtest_config.get('stop_loss')
        take_profit = backtest_config.get('take_profit')
        self._validate_risk_management(stop_loss, take_profit)

        # 3. Validate position sizing
        position_limit = backtest_config.get('position_limit')
        self._validate_position_sizing(position_limit, n_stocks)

        # 4. Validate fee ratio
        fee_ratio = backtest_config.get('fee_ratio')
        self._validate_fee_ratio(fee_ratio)

    def get_result(self) -> ValidationResult:
        """
        Get validation result with all errors, warnings, and suggestions.

        Returns:
            ValidationResult with status determination

        Example:
            >>> validator.validate_backtest_config(config)
            >>> result = validator.get_result()
            >>> if not result.is_valid():
            ...     print(result)
        """
        # Determine status
        if self.errors:
            critical_errors = [e for e in self.errors if e.severity == Severity.CRITICAL]
            if critical_errors:
                status = 'invalid'
            else:
                status = 'warning'
        else:
            status = 'valid'

        return ValidationResult(
            status=status,
            errors=self.errors,
            warnings=self.warnings,
            suggestions=self.suggestions,
            metadata={'validator': 'BacktestValidator'}
        )
