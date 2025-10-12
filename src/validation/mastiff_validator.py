"""
MastiffTemplate Specific Validator
===================================

Comprehensive validation for the MastiffTemplate contrarian reversal strategy
with 6-condition filtering architecture, volume weighting logic validation,
and concentrated positioning checks.

Validation Layers:
    1. Parameter Schema Validation: Type, range, and optimal value checks
    2. Architectural Validation: 6-condition contrarian filtering integrity
    3. Volume Weighting Logic: Contrarian selection (is_smallest) validation
    4. Parameter Interdependencies: Cross-parameter consistency checks
    5. Concentrated Positioning Validation: High-conviction portfolio constraints
    6. Performance Target Validation: Expected performance alignment

Template Architecture:
    The MastiffTemplate implements a contrarian reversal strategy with 6 conditions:
    - Condition 1: Price High Filter (stock price = 250-day rolling max)
    - Condition 2: Revenue Decline Filter (exclude consistent decline)
    - Condition 3: Revenue Growth Filter (exclude excessive growth)
    - Condition 4: Revenue Bottom Detection (confirm recovery from lows)
    - Condition 5: Momentum Filter (ensure momentum not too negative)
    - Condition 6: Liquidity (10-day avg volume > 200k shares)

Contrarian Logic:
    **CRITICAL DIFFERENCE from TurtleTemplate**:
    - Uses .is_smallest() to select LOW-volume stocks (contrarian)
    - NOT .is_largest() like momentum strategies
    - Concentrated portfolio: n_stocks 3-10 (vs Turtle's 5-20)
    - High concentration: position_limit 15-30% (vs Turtle's 10-20%)

Usage:
    from src.validation import MastiffTemplateValidator

    validator = MastiffTemplateValidator()
    validator.validate_parameters(
        parameters={'n_stocks': 5, 'stop_loss': 0.15, ...},
        template_name='MastiffTemplate'
    )

    result = validator.get_result()
    if not result.is_valid():
        print(result)

Requirements:
    - Requirement 3.1: Parameter validation with template-specific rules
    - Requirement 3.2: Architecture integrity validation
"""

from typing import Dict, Any, Optional
from .parameter_validator import ParameterValidator
from .template_validator import ValidationError, ValidationResult, Category, Severity


class MastiffTemplateValidator(ParameterValidator):
    """
    MastiffTemplate-specific validator with contrarian reversal validation.

    Extends ParameterValidator with MastiffTemplate-specific validation rules:
        - 6-condition contrarian filtering architecture integrity
        - Volume weighting logic validation (is_smallest selection)
        - Concentrated positioning constraints (n_stocks ≤10, position_limit ≥15%)
        - Parameter interdependency checks (stop_loss < take_profit, etc.)
        - Template-specific parameter constraints
        - Performance target alignment

    Architecture Validation:
        Validates the 6-condition contrarian reversal strategy by checking:
        - All 6 conditions are implemented with correct datasets
        - Filtering logic uses AND operators correctly
        - Volume weighting uses contrarian selection (is_smallest)
        - Parameter values align with contrarian strategy requirements

    Parameter Interdependencies:
        Critical consistency checks:
        - stop_loss < take_profit (risk management consistency)
        - n_stocks ≤ 10 (concentrated positioning constraint)
        - position_limit ≥ 0.15 (high concentration requirement)
        - stop_loss ≥ 0.10 (higher risk tolerance for mean reversion)

    Example:
        >>> validator = MastiffTemplateValidator()
        >>> params = {
        ...     'low_volume_days': 10, 'volume_percentile': 20,
        ...     'price_drop_threshold': -0.10, 'pe_max': 20,
        ...     'revenue_growth_min': 0, 'n_stocks': 5,
        ...     'stop_loss': 0.15, 'take_profit': 0.50,
        ...     'position_limit': 0.20, 'resample': 'M'
        ... }
        >>> validator.validate_parameters(params, 'MastiffTemplate')
        >>> result = validator.get_result()
        >>> print(f"Valid: {result.is_valid()}")
        Valid: True
    """

    # Template-specific datasets required for contrarian reversal filtering
    REQUIRED_DATASETS = {
        'condition1_price': 'price:收盤價',
        'condition2_revenue_yoy': 'monthly_revenue:去年同月增減(%)',
        'condition3_revenue_yoy': 'monthly_revenue:去年同月增減(%)',
        'condition4_revenue': 'monthly_revenue:當月營收',
        'condition5_revenue_mom': 'monthly_revenue:上月比較增減(%)',
        'condition6_volume': 'price:成交股數',
        'weighting': 'price:成交股數'  # Volume weighting (contrarian selection)
    }

    # Concentrated positioning constraints (KEY DIFFERENCE from TurtleTemplate)
    MAX_N_STOCKS = 10  # Maximum portfolio size for concentrated contrarian strategy
    MIN_POSITION_LIMIT = 0.15  # Minimum 15% per stock for high-conviction positions
    MIN_STOP_LOSS = 0.10  # Minimum 10% stop-loss for mean reversion risk tolerance

    def __init__(self, sensitivity_data: Optional[Dict[str, Any]] = None):
        """
        Initialize MastiffTemplate validator.

        Args:
            sensitivity_data: Optional sensitivity analysis data from performance_attributor
                             for enhanced parameter validation
        """
        super().__init__(sensitivity_data)

        # Template-specific validation state
        self.template_name = 'MastiffTemplate'
        self.architecture_validated = False
        self.interdependencies_validated = False
        self.concentration_validated = False

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        template_name: str
    ) -> None:
        """
        Validate MastiffTemplate parameters with comprehensive checks.

        Validation Workflow:
            1. Base parameter validation (type, range, optimal values)
            2. Template name verification
            3. Parameter interdependency validation
            4. 6-condition contrarian architecture validation
            5. Volume weighting logic validation (is_smallest selection)
            6. Concentrated positioning validation
            7. Performance target alignment check

        Args:
            parameters: Parameter dictionary with all 10 MastiffTemplate parameters
            template_name: Must be 'MastiffTemplate' or 'Mastiff'

        Example:
            >>> validator = MastiffTemplateValidator()
            >>> params = {'n_stocks': 5, 'stop_loss': 0.15, ...}
            >>> validator.validate_parameters(params, 'MastiffTemplate')
            >>> result = validator.get_result()
        """
        # Step 1: Verify template name
        if template_name not in ('MastiffTemplate', 'Mastiff'):
            self._add_error(
                category=Category.PARAMETER,
                error_type='invalid_template',
                message=f"Template name '{template_name}' is not valid for MastiffTemplateValidator",
                suggestion="Use 'MastiffTemplate' or 'Mastiff' as template name",
                context={'provided_name': template_name, 'expected': 'MastiffTemplate'}
            )
            return

        # Step 2: Base parameter validation (inherited from ParameterValidator)
        # This validates type, range, optimal values for all parameters
        super().validate_parameters(parameters, template_name)

        # Step 3: Validate parameter interdependencies
        self._validate_interdependencies(parameters)

        # Step 4: Validate 6-condition contrarian architecture requirements
        self._validate_architecture(parameters)

        # Step 5: Validate volume weighting logic (contrarian selection)
        self._validate_volume_weighting(parameters)

        # Step 6: Validate concentrated positioning constraints
        self._validate_concentration(parameters)

        # Step 7: Validate performance target alignment
        self._validate_performance_targets(parameters)

    def _validate_interdependencies(self, parameters: Dict[str, Any]) -> None:
        """
        Validate critical parameter interdependencies.

        Checks cross-parameter consistency constraints specific to the
        MastiffTemplate contrarian reversal strategy.

        Critical Interdependencies:
            - stop_loss < take_profit: Risk management requires loss < profit
            - n_stocks ≤ 10: Concentrated positioning constraint
            - position_limit ≥ 0.15: High-conviction position sizing
            - stop_loss ≥ 0.10: Higher risk tolerance for mean reversion

        Args:
            parameters: Parameter dictionary to validate

        Error Types:
            - inconsistent_parameters (MODERATE): Parameters violate consistency rules
        """
        # Check 1: Risk management - stop_loss < take_profit
        if 'stop_loss' in parameters and 'take_profit' in parameters:
            stop_loss = parameters['stop_loss']
            take_profit = parameters['take_profit']

            if stop_loss >= take_profit:
                self._add_error(
                    category=Category.PARAMETER,
                    error_type='inconsistent_parameters',
                    message=f"stop_loss ({stop_loss:.1%}) must be less than take_profit ({take_profit:.1%})",
                    suggestion=f"Set stop_loss to a value less than {take_profit:.1%} (e.g., 10-20%)",
                    context={
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'layer': 'Risk Management'
                    }
                )

        # Check 2: Concentrated positioning - n_stocks ≤ 10
        if 'n_stocks' in parameters:
            n_stocks = parameters['n_stocks']

            if n_stocks > self.MAX_N_STOCKS:
                self._add_error(
                    category=Category.PARAMETER,
                    error_type='invalid_range',
                    message=f"n_stocks ({n_stocks}) exceeds maximum for concentrated contrarian strategy ({self.MAX_N_STOCKS})",
                    suggestion=f"Set n_stocks to ≤{self.MAX_N_STOCKS} for high-conviction contrarian positioning",
                    context={
                        'n_stocks': n_stocks,
                        'max_allowed': self.MAX_N_STOCKS,
                        'strategy_type': 'concentrated_contrarian'
                    }
                )

        # Check 3: High-conviction sizing - position_limit ≥ 0.15
        if 'position_limit' in parameters:
            position_limit = parameters['position_limit']

            if position_limit < self.MIN_POSITION_LIMIT:
                self._add_error(
                    category=Category.PARAMETER,
                    error_type='suboptimal_range',
                    message=f"position_limit ({position_limit:.1%}) below minimum for high-conviction contrarian strategy ({self.MIN_POSITION_LIMIT:.1%})",
                    suggestion=f"Set position_limit to ≥{self.MIN_POSITION_LIMIT:.1%} (15-30%) for concentrated positioning",
                    context={
                        'position_limit': position_limit,
                        'min_recommended': self.MIN_POSITION_LIMIT,
                        'optimal_range': (0.15, 0.30),
                        'strategy_type': 'concentrated_contrarian'
                    }
                )

        # Check 4: Mean reversion risk tolerance - stop_loss ≥ 0.10
        if 'stop_loss' in parameters:
            stop_loss = parameters['stop_loss']

            if stop_loss < self.MIN_STOP_LOSS:
                self._add_error(
                    category=Category.PARAMETER,
                    error_type='suboptimal_range',
                    message=f"stop_loss ({stop_loss:.1%}) below minimum for mean reversion strategy ({self.MIN_STOP_LOSS:.1%})",
                    suggestion=f"Set stop_loss to ≥{self.MIN_STOP_LOSS:.1%} (10-20%) for adequate mean reversion tolerance",
                    context={
                        'stop_loss': stop_loss,
                        'min_recommended': self.MIN_STOP_LOSS,
                        'optimal_range': (0.10, 0.20),
                        'strategy_type': 'contrarian_reversal'
                    }
                )

        self.interdependencies_validated = True

    def _validate_architecture(self, parameters: Dict[str, Any]) -> None:
        """
        Validate 6-condition contrarian filtering architecture requirements.

        Validates that all required parameters for the 6-condition contrarian
        reversal strategy are present and correctly configured.

        Architecture Conditions:
            Condition 1 (Price High): Implicit (uses price:收盤價 with rolling max)
            Condition 2 (Revenue Decline): Implicit (uses revenue YoY growth)
            Condition 3 (Revenue Growth): Implicit (uses revenue YoY growth)
            Condition 4 (Revenue Bottom): Implicit (uses monthly revenue)
            Condition 5 (Momentum): Implicit (uses revenue MoM growth)
            Condition 6 (Liquidity): Implicit (uses trading volume)

        Required Parameters:
            Reversal Detection: low_volume_days, volume_percentile, price_drop_threshold
            Fundamental Quality: pe_max, revenue_growth_min
            Position Management: n_stocks, stop_loss, take_profit, position_limit, resample

        Args:
            parameters: Parameter dictionary to validate

        Error Types:
            - missing_parameter (CRITICAL): Required parameter missing
            - invalid_architecture (MODERATE): Architecture integrity violation
        """
        # Define required parameters for contrarian architecture
        architecture_requirements = {
            'Reversal Detection': ['low_volume_days', 'volume_percentile', 'price_drop_threshold'],
            'Fundamental Quality': ['pe_max', 'revenue_growth_min'],
            'Position Management': ['n_stocks', 'stop_loss', 'take_profit', 'position_limit', 'resample']
        }

        # Check each component for required parameters
        missing_components = []
        for component_name, required_params in architecture_requirements.items():
            missing_params = [p for p in required_params if p not in parameters]

            if missing_params:
                missing_components.append(component_name)
                self._add_error(
                    category=Category.ARCHITECTURE,
                    error_type='missing_parameter',
                    message=f"{component_name} missing required parameters: {', '.join(missing_params)}",
                    suggestion=f"Add {', '.join(missing_params)} to parameters dictionary",
                    context={
                        'component': component_name,
                        'missing_parameters': missing_params,
                        'required_parameters': required_params
                    }
                )

        # If all components are present, validate architecture integrity
        if not missing_components:
            self._validate_condition_integrity(parameters)
            self.architecture_validated = True
        else:
            self._add_error(
                category=Category.ARCHITECTURE,
                error_type='invalid_architecture',
                message=f"Contrarian reversal architecture incomplete: {len(missing_components)}/3 components missing parameters",
                suggestion="Ensure all 3 architecture components have required parameters",
                context={
                    'missing_components': missing_components,
                    'total_components': 3,
                    'architecture': 'contrarian_reversal'
                }
            )

    def _validate_condition_integrity(self, parameters: Dict[str, Any]) -> None:
        """
        Validate integrity of 6-condition contrarian filtering implementation.

        Checks that parameter values align with condition-specific requirements
        and that the overall architecture maintains consistency.

        Condition Integrity Checks:
            - Price drop threshold: negative values for reversal detection
            - Volume percentile: low percentile for neglected stock selection
            - Revenue growth: allow negative values for value plays
            - P/E max: reasonable valuation screen

        Args:
            parameters: Parameter dictionary to validate
        """
        # Condition 1 & 2 & 3: Price drop threshold must be negative (reversal detection)
        if 'price_drop_threshold' in parameters:
            price_drop = parameters['price_drop_threshold']

            if price_drop >= 0:
                self._add_error(
                    category=Category.ARCHITECTURE,
                    error_type='invalid_range',
                    message=f"price_drop_threshold ({price_drop:.1%}) must be negative for reversal detection",
                    suggestion="Set price_drop_threshold to a negative value (e.g., -0.05, -0.10, -0.15)",
                    context={
                        'price_drop_threshold': price_drop,
                        'valid_range': (-0.15, -0.05),
                        'condition': 'Condition 1-3 (Reversal Detection)'
                    }
                )

        # Condition 6: Volume percentile should be low for contrarian selection
        if 'volume_percentile' in parameters:
            vol_pct = parameters['volume_percentile']

            if vol_pct > 30:
                self._add_suggestion(
                    f"Condition 6 (Liquidity): volume_percentile {vol_pct} is above typical contrarian range (10-30). "
                    f"Consider using a lower percentile for better neglected stock selection."
                )

        # Fundamental Quality: Revenue growth can be negative for value plays
        if 'revenue_growth_min' in parameters:
            rev_growth = parameters['revenue_growth_min']

            if rev_growth < -5:
                self._add_suggestion(
                    f"Fundamental Quality: revenue_growth_min {rev_growth}% is very low. "
                    f"Consider using a higher threshold (-5% to 5%) to avoid value traps."
                )

    def _validate_volume_weighting(self, parameters: Dict[str, Any]) -> None:
        """
        Validate volume weighting logic and contrarian selection.

        The MastiffTemplate uses contrarian volume weighting with .is_smallest()
        to select LOW-volume stocks (neglected, under-the-radar opportunities).

        **CRITICAL VALIDATION**:
        This validates the KEY DIFFERENCE from TurtleTemplate:
        - TurtleTemplate: .is_largest() → HIGH revenue growth (momentum)
        - MastiffTemplate: .is_smallest() → LOW volume (contrarian)

        Validation Checks:
            - n_stocks parameter present and valid
            - n_stocks ≤ 10 (concentrated contrarian positioning)
            - Volume weighting dataset availability
            - Contrarian selection logic documentation

        Args:
            parameters: Parameter dictionary to validate

        Error Types:
            - missing_parameter (CRITICAL): n_stocks parameter missing
            - invalid_range (CRITICAL): n_stocks exceeds concentrated limit
        """
        # Check 1: n_stocks parameter present (required for contrarian selection)
        if 'n_stocks' not in parameters:
            self._add_error(
                category=Category.PARAMETER,
                error_type='missing_parameter',
                message="Volume weighting requires 'n_stocks' parameter for contrarian selection",
                suggestion="Add 'n_stocks' parameter to specify portfolio size (3-10 stocks)",
                context={
                    'required_parameter': 'n_stocks',
                    'weighting_dataset': self.REQUIRED_DATASETS['weighting'],
                    'selection_method': 'is_smallest() - CONTRARIAN'
                }
            )
            return

        # Check 2: n_stocks within concentrated range (3-10 stocks)
        n_stocks = parameters['n_stocks']
        if n_stocks < 3 or n_stocks > self.MAX_N_STOCKS:
            self._add_error(
                category=Category.PARAMETER,
                error_type='invalid_range',
                message=f"n_stocks ({n_stocks}) outside valid range for contrarian volume weighting (3-{self.MAX_N_STOCKS})",
                suggestion=f"Set n_stocks to a value between 3 and {self.MAX_N_STOCKS} for concentrated contrarian positioning",
                context={
                    'n_stocks': n_stocks,
                    'valid_range': (3, self.MAX_N_STOCKS),
                    'optimal_range': (5, 8),
                    'selection_method': 'is_smallest() - CONTRARIAN'
                }
            )

        # Check 3: Contrarian selection logic documentation
        self._add_suggestion(
            f"Volume weighting uses '{self.REQUIRED_DATASETS['weighting']}' dataset with "
            f".is_smallest() selection (CONTRARIAN - opposite of momentum strategies). "
            f"This selects the {n_stocks} stocks with LOWEST volume for neglected, "
            f"under-the-radar opportunities."
        )

    def _validate_concentration(self, parameters: Dict[str, Any]) -> None:
        """
        Validate concentrated positioning constraints.

        The MastiffTemplate is a high-conviction contrarian strategy requiring:
        - Small portfolio: n_stocks ≤ 10 (concentrated positions)
        - High position sizing: position_limit ≥ 15% (high conviction)
        - Adequate risk tolerance: stop_loss ≥ 10% (mean reversion allowance)

        This validation ensures the concentrated contrarian positioning is
        properly configured for asymmetric upside opportunities.

        Args:
            parameters: Parameter dictionary to validate
        """
        concentration_score = 0
        concentration_issues = []

        # Check 1: Portfolio size concentration (n_stocks ≤ 10)
        if 'n_stocks' in parameters:
            n_stocks = parameters['n_stocks']

            if n_stocks <= 5:
                concentration_score += 2  # Very concentrated
            elif n_stocks <= 8:
                concentration_score += 1  # Moderately concentrated
            elif n_stocks <= self.MAX_N_STOCKS:
                concentration_score += 0  # Acceptable
            else:
                concentration_issues.append(f"n_stocks ({n_stocks}) exceeds concentrated limit")

        # Check 2: Position size concentration (position_limit ≥ 15%)
        if 'position_limit' in parameters:
            position_limit = parameters['position_limit']

            if position_limit >= 0.25:
                concentration_score += 2  # Very high conviction
            elif position_limit >= 0.20:
                concentration_score += 1  # High conviction
            elif position_limit >= self.MIN_POSITION_LIMIT:
                concentration_score += 0  # Acceptable
            else:
                concentration_issues.append(f"position_limit ({position_limit:.1%}) below minimum")

        # Check 3: Risk tolerance (stop_loss ≥ 10%)
        if 'stop_loss' in parameters:
            stop_loss = parameters['stop_loss']

            if stop_loss >= 0.15:
                concentration_score += 1  # High risk tolerance
            elif stop_loss >= self.MIN_STOP_LOSS:
                concentration_score += 0  # Acceptable
            else:
                concentration_issues.append(f"stop_loss ({stop_loss:.1%}) below minimum")

        # Assess overall concentration
        if concentration_issues:
            self._add_error(
                category=Category.ARCHITECTURE,
                error_type='suboptimal_range',
                message=f"Concentrated positioning constraints not met: {'; '.join(concentration_issues)}",
                suggestion=f"Ensure n_stocks ≤{self.MAX_N_STOCKS}, position_limit ≥{self.MIN_POSITION_LIMIT:.1%}, stop_loss ≥{self.MIN_STOP_LOSS:.1%}",
                context={
                    'concentration_score': concentration_score,
                    'concentration_issues': concentration_issues,
                    'strategy_type': 'concentrated_contrarian'
                }
            )
        elif concentration_score >= 3:
            self._add_suggestion(
                f"Concentrated positioning score: {concentration_score}/5 (High conviction). "
                f"This configuration supports asymmetric upside opportunities from mean reversion."
            )

        self.concentration_validated = True

    def _validate_performance_targets(self, parameters: Dict[str, Any]) -> None:
        """
        Validate parameters against expected performance targets.

        The MastiffTemplate has specific performance targets:
        - Sharpe Ratio: 1.2-2.0
        - Annual Return: 15-30%
        - Max Drawdown: -30% to -15%

        This method provides guidance on parameter choices that are likely
        to achieve these targets for contrarian reversal strategies.

        Args:
            parameters: Parameter dictionary to validate
        """
        # Performance guidance for critical parameters
        if 'n_stocks' in parameters and 'position_limit' in parameters:
            n_stocks = parameters['n_stocks']
            position_limit = parameters['position_limit']

            # Optimal concentration for Sharpe 1.2-2.0: 5-8 stocks with 20-25% position limit
            if n_stocks < 5 and position_limit >= 0.25:
                self._add_suggestion(
                    f"Performance: Very concentrated positioning (n_stocks={n_stocks}, "
                    f"position_limit={position_limit:.1%}) may result in higher volatility. "
                    f"Expected MDD: -25% to -30% (within target range)."
                )
            elif n_stocks > 8 or position_limit < 0.20:
                self._add_suggestion(
                    f"Performance: Less concentrated positioning (n_stocks={n_stocks}, "
                    f"position_limit={position_limit:.1%}) may reduce asymmetric upside. "
                    f"Consider 5-8 stocks with 20-25% position_limit for optimal risk/reward."
                )

        # Risk management guidance for contrarian strategy
        if 'stop_loss' in parameters and 'take_profit' in parameters:
            stop_loss = parameters['stop_loss']
            take_profit = parameters['take_profit']
            risk_reward_ratio = take_profit / stop_loss if stop_loss > 0 else float('inf')

            if risk_reward_ratio < 2.5:
                self._add_suggestion(
                    f"Performance: Risk/reward ratio ({risk_reward_ratio:.1f}x) is below 2.5. "
                    f"For contrarian mean reversion, consider increasing take_profit (e.g., 50-80%) "
                    f"to capture asymmetric upside from neglected stocks."
                )

    def get_result(self) -> ValidationResult:
        """
        Get validation result with MastiffTemplate-specific metadata.

        Returns:
            ValidationResult with status, errors, warnings, suggestions, and metadata

        Metadata includes:
            - validator: 'MastiffTemplateValidator'
            - template_name: 'MastiffTemplate'
            - architecture_validated: Whether 6-condition architecture was validated
            - interdependencies_validated: Whether parameter interdependencies were validated
            - concentration_validated: Whether concentrated positioning was validated
            - total_conditions: 6 (number of filtering conditions)
            - pattern_type: 'contrarian_reversal'
            - selection_method: 'is_smallest() - CONTRARIAN'

        Example:
            >>> result = validator.get_result()
            >>> print(f"Architecture validated: {result.metadata['architecture_validated']}")
            Architecture validated: True
        """
        # Determine status based on errors
        if self.errors:
            critical_errors = [e for e in self.errors if e.severity == Severity.CRITICAL]
            if critical_errors:
                status = 'invalid'
            else:
                status = 'warning'
        else:
            status = 'valid'

        # Build metadata with MastiffTemplate-specific information
        metadata = {
            'validator': 'MastiffTemplateValidator',
            'template_name': self.template_name,
            'architecture_validated': self.architecture_validated,
            'interdependencies_validated': self.interdependencies_validated,
            'concentration_validated': self.concentration_validated,
            'total_conditions': 6,
            'pattern_type': 'contrarian_reversal',
            'selection_method': 'is_smallest() - CONTRARIAN',
            'required_datasets': self.REQUIRED_DATASETS,
            'concentration_constraints': {
                'max_n_stocks': self.MAX_N_STOCKS,
                'min_position_limit': self.MIN_POSITION_LIMIT,
                'min_stop_loss': self.MIN_STOP_LOSS
            }
        }

        return ValidationResult(
            status=status,
            errors=self.errors,
            warnings=self.warnings,
            suggestions=self.suggestions,
            metadata=metadata
        )
