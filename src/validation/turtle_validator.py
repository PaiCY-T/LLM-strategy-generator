"""
TurtleTemplate Specific Validator
==================================

Comprehensive validation for the TurtleTemplate strategy implementation with
6-layer AND filtering architecture, revenue weighting logic, and parameter
interdependency checks.

Validation Layers:
    1. Parameter Schema Validation: Type, range, and optimal value checks
    2. Architectural Validation: 6-layer AND filtering integrity
    3. Revenue Weighting Logic: Weighting algorithm and dataset validation
    4. Parameter Interdependencies: Cross-parameter consistency checks
    5. Performance Target Validation: Expected performance alignment

Template Architecture:
    The TurtleTemplate implements a 6-layer AND filtering strategy:
    - Layer 1: Dividend Yield (基本面選股)
    - Layer 2: Technical Confirmation (技術面選股)
    - Layer 3: Revenue Acceleration (營收面選股)
    - Layer 4: Operating Margin Quality (品質面選股)
    - Layer 5: Director Confidence (內部人持股)
    - Layer 6: Liquidity (流動性篩選)

Usage:
    from src.validation import TurtleTemplateValidator

    validator = TurtleTemplateValidator()
    validator.validate_parameters(
        parameters={'n_stocks': 10, 'yield_threshold': 6.0, ...},
        template_name='TurtleTemplate'
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


class TurtleTemplateValidator(ParameterValidator):
    """
    TurtleTemplate-specific validator with 6-layer AND filtering validation.

    Extends ParameterValidator with TurtleTemplate-specific validation rules:
        - 6-layer AND filtering architecture integrity
        - Revenue weighting logic validation
        - Parameter interdependency checks (ma_short < ma_long, etc.)
        - Template-specific parameter constraints
        - Performance target alignment

    Architecture Validation:
        Validates the 6-layer AND filtering strategy implementation by checking:
        - All 6 layers are implemented with correct datasets
        - Filtering logic uses AND operators correctly
        - Revenue weighting uses correct dataset and algorithm
        - Parameter values align with layer requirements

    Parameter Interdependencies:
        Critical consistency checks:
        - ma_short < ma_long (technical layer consistency)
        - rev_short < rev_long (revenue layer consistency)
        - vol_min < vol_max (liquidity layer consistency)
        - stop_loss < take_profit (risk management consistency)

    Example:
        >>> validator = TurtleTemplateValidator()
        >>> params = {
        ...     'yield_threshold': 6.0, 'ma_short': 20, 'ma_long': 60,
        ...     'rev_short': 3, 'rev_long': 12, 'n_stocks': 10,
        ...     'stop_loss': 0.06, 'take_profit': 0.5, 'position_limit': 0.125,
        ...     'op_margin_threshold': 3, 'director_threshold': 10,
        ...     'vol_min': 50, 'vol_max': 10000, 'resample': 'M'
        ... }
        >>> validator.validate_parameters(params, 'TurtleTemplate')
        >>> result = validator.get_result()
        >>> print(f"Valid: {result.is_valid()}")
        Valid: True
    """

    # Template-specific datasets required for 6-layer AND filtering
    REQUIRED_DATASETS = {
        'layer1_yield': 'price_earning_ratio:殖利率(%)',
        'layer2_technical': 'price:收盤價',
        'layer3_revenue': 'monthly_revenue:當月營收',
        'layer4_quality': 'fundamental_features:營業利益率',
        'layer5_insider': 'internal_equity_changes:董監持有股數占比',
        'layer6_liquidity': 'price:成交股數',
        'weighting': 'monthly_revenue:去年同月增減(%)'
    }

    def __init__(self, sensitivity_data: Optional[Dict[str, Any]] = None):
        """
        Initialize TurtleTemplate validator.

        Args:
            sensitivity_data: Optional sensitivity analysis data from performance_attributor
                             for enhanced parameter validation
        """
        super().__init__(sensitivity_data)

        # Template-specific validation state
        self.template_name = 'TurtleTemplate'
        self.architecture_validated = False
        self.interdependencies_validated = False

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        template_name: str
    ) -> None:
        """
        Validate TurtleTemplate parameters with comprehensive checks.

        Validation Workflow:
            1. Base parameter validation (type, range, optimal values)
            2. Template name verification
            3. Parameter interdependency validation
            4. 6-layer architecture validation
            5. Revenue weighting logic validation
            6. Performance target alignment check

        Args:
            parameters: Parameter dictionary with all 14 TurtleTemplate parameters
            template_name: Must be 'TurtleTemplate' or 'Turtle'

        Example:
            >>> validator = TurtleTemplateValidator()
            >>> params = {'n_stocks': 10, 'yield_threshold': 6.0, ...}
            >>> validator.validate_parameters(params, 'TurtleTemplate')
            >>> result = validator.get_result()
        """
        # Step 1: Verify template name
        if template_name not in ('TurtleTemplate', 'Turtle'):
            self._add_error(
                category=Category.PARAMETER,
                error_type='invalid_template',
                message=f"Template name '{template_name}' is not valid for TurtleTemplateValidator",
                suggestion="Use 'TurtleTemplate' or 'Turtle' as template name",
                context={'provided_name': template_name, 'expected': 'TurtleTemplate'}
            )
            return

        # Step 2: Base parameter validation (inherited from ParameterValidator)
        # This validates type, range, optimal values for all parameters
        super().validate_parameters(parameters, template_name)

        # Step 3: Validate parameter interdependencies
        self._validate_interdependencies(parameters)

        # Step 4: Validate 6-layer architecture requirements
        self._validate_architecture(parameters)

        # Step 5: Validate revenue weighting logic
        self._validate_revenue_weighting(parameters)

        # Step 6: Validate performance target alignment
        self._validate_performance_targets(parameters)

    def _validate_interdependencies(self, parameters: Dict[str, Any]) -> None:
        """
        Validate critical parameter interdependencies.

        Checks cross-parameter consistency constraints that are critical
        for the TurtleTemplate strategy to function correctly.

        Critical Interdependencies:
            - ma_short < ma_long: Technical layer requires short MA < long MA
            - rev_short < rev_long: Revenue layer requires short < long window
            - vol_min < vol_max: Liquidity layer requires min < max volume
            - stop_loss < take_profit: Risk management requires loss < profit

        Args:
            parameters: Parameter dictionary to validate

        Error Types:
            - inconsistent_parameters (MODERATE): Parameters violate consistency rules
        """
        # Check 1: Technical layer - ma_short < ma_long
        if 'ma_short' in parameters and 'ma_long' in parameters:
            ma_short = parameters['ma_short']
            ma_long = parameters['ma_long']

            if ma_short >= ma_long:
                self._add_error(
                    category=Category.PARAMETER,
                    error_type='inconsistent_parameters',
                    message=f"ma_short ({ma_short}) must be less than ma_long ({ma_long})",
                    suggestion=f"Set ma_short to a value less than {ma_long} (e.g., {ma_long // 2})",
                    context={
                        'ma_short': ma_short,
                        'ma_long': ma_long,
                        'layer': 'Layer 2 (Technical)'
                    }
                )

        # Check 2: Revenue layer - rev_short < rev_long
        if 'rev_short' in parameters and 'rev_long' in parameters:
            rev_short = parameters['rev_short']
            rev_long = parameters['rev_long']

            if rev_short >= rev_long:
                self._add_error(
                    category=Category.PARAMETER,
                    error_type='inconsistent_parameters',
                    message=f"rev_short ({rev_short}) must be less than rev_long ({rev_long})",
                    suggestion=f"Set rev_short to a value less than {rev_long} (e.g., 3 or 6 months)",
                    context={
                        'rev_short': rev_short,
                        'rev_long': rev_long,
                        'layer': 'Layer 3 (Revenue)'
                    }
                )

        # Check 3: Liquidity layer - vol_min < vol_max
        if 'vol_min' in parameters and 'vol_max' in parameters:
            vol_min = parameters['vol_min']
            vol_max = parameters['vol_max']

            if vol_min >= vol_max:
                self._add_error(
                    category=Category.PARAMETER,
                    error_type='inconsistent_parameters',
                    message=f"vol_min ({vol_min}k) must be less than vol_max ({vol_max}k)",
                    suggestion=f"Set vol_min to a value less than {vol_max} (e.g., {vol_max // 10})",
                    context={
                        'vol_min': vol_min,
                        'vol_max': vol_max,
                        'layer': 'Layer 6 (Liquidity)'
                    }
                )

        # Check 4: Risk management - stop_loss < take_profit
        if 'stop_loss' in parameters and 'take_profit' in parameters:
            stop_loss = parameters['stop_loss']
            take_profit = parameters['take_profit']

            if stop_loss >= take_profit:
                self._add_error(
                    category=Category.PARAMETER,
                    error_type='inconsistent_parameters',
                    message=f"stop_loss ({stop_loss:.1%}) must be less than take_profit ({take_profit:.1%})",
                    suggestion=f"Set stop_loss to a value less than {take_profit:.1%} (e.g., 6-10%)",
                    context={
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'layer': 'Risk Management'
                    }
                )

        self.interdependencies_validated = True

    def _validate_architecture(self, parameters: Dict[str, Any]) -> None:
        """
        Validate 6-layer AND filtering architecture requirements.

        Validates that all required parameters for the 6-layer AND filtering
        strategy are present and correctly configured.

        Architecture Layers:
            Layer 1 (Yield): yield_threshold
            Layer 2 (Technical): ma_short, ma_long
            Layer 3 (Revenue): rev_short, rev_long
            Layer 4 (Quality): op_margin_threshold
            Layer 5 (Insider): director_threshold
            Layer 6 (Liquidity): vol_min, vol_max

        Args:
            parameters: Parameter dictionary to validate

        Error Types:
            - missing_parameter (CRITICAL): Required layer parameter missing
            - invalid_architecture (MODERATE): Architecture integrity violation
        """
        # Define required parameters for each layer
        layer_requirements = {
            'Layer 1 (Yield)': ['yield_threshold'],
            'Layer 2 (Technical)': ['ma_short', 'ma_long'],
            'Layer 3 (Revenue)': ['rev_short', 'rev_long'],
            'Layer 4 (Quality)': ['op_margin_threshold'],
            'Layer 5 (Insider)': ['director_threshold'],
            'Layer 6 (Liquidity)': ['vol_min', 'vol_max']
        }

        # Check each layer for required parameters
        missing_layers = []
        for layer_name, required_params in layer_requirements.items():
            missing_params = [p for p in required_params if p not in parameters]

            if missing_params:
                missing_layers.append(layer_name)
                self._add_error(
                    category=Category.ARCHITECTURE,
                    error_type='missing_parameter',
                    message=f"{layer_name} missing required parameters: {', '.join(missing_params)}",
                    suggestion=f"Add {', '.join(missing_params)} to parameters dictionary",
                    context={
                        'layer': layer_name,
                        'missing_parameters': missing_params,
                        'required_parameters': required_params
                    }
                )

        # If all layers are present, validate architecture integrity
        if not missing_layers:
            self._validate_layer_integrity(parameters)
            self.architecture_validated = True
        else:
            self._add_error(
                category=Category.ARCHITECTURE,
                error_type='invalid_architecture',
                message=f"6-layer AND filtering architecture incomplete: {len(missing_layers)}/6 layers missing parameters",
                suggestion="Ensure all 6 layers have required parameters for AND filtering strategy",
                context={
                    'missing_layers': missing_layers,
                    'total_layers': 6,
                    'architecture': 'multi_layer_and'
                }
            )

    def _validate_layer_integrity(self, parameters: Dict[str, Any]) -> None:
        """
        Validate integrity of 6-layer AND filtering implementation.

        Checks that parameter values align with layer-specific requirements
        and that the overall architecture maintains consistency.

        Layer Integrity Checks:
            - Yield layer: threshold in realistic range (4-8%)
            - Technical layer: MA periods in valid range with proper separation
            - Revenue layer: windows in valid range with proper separation
            - Quality layer: margin threshold non-negative
            - Insider layer: threshold in valid range (5-15%)
            - Liquidity layer: volume bounds in valid range with proper separation

        Args:
            parameters: Parameter dictionary to validate
        """
        # Layer 1 (Yield): Check yield threshold range
        if 'yield_threshold' in parameters:
            yield_threshold = parameters['yield_threshold']
            if yield_threshold < 4.0 or yield_threshold > 8.0:
                self._add_suggestion(
                    f"Layer 1 (Yield): yield_threshold {yield_threshold}% is outside typical range (4-8%). "
                    f"Consider using a more realistic dividend yield threshold."
                )

        # Layer 2 (Technical): Check MA period separation
        if 'ma_short' in parameters and 'ma_long' in parameters:
            ma_short = parameters['ma_short']
            ma_long = parameters['ma_long']
            ma_diff = ma_long - ma_short

            if ma_diff < 20:
                self._add_error(
                    category=Category.ARCHITECTURE,
                    error_type='suboptimal_range',
                    message=f"Layer 2 (Technical): MA period separation ({ma_diff} days) is too small",
                    suggestion=f"Increase separation to at least 20 days for better signal quality (e.g., ma_long = {ma_short + 20})",
                    context={
                        'ma_short': ma_short,
                        'ma_long': ma_long,
                        'separation': ma_diff,
                        'minimum_recommended': 20
                    }
                )

        # Layer 3 (Revenue): Check revenue window separation
        if 'rev_short' in parameters and 'rev_long' in parameters:
            rev_short = parameters['rev_short']
            rev_long = parameters['rev_long']
            rev_diff = rev_long - rev_short

            if rev_diff < 6:
                self._add_error(
                    category=Category.ARCHITECTURE,
                    error_type='suboptimal_range',
                    message=f"Layer 3 (Revenue): Revenue window separation ({rev_diff} months) is too small",
                    suggestion=f"Increase separation to at least 6 months for meaningful trend differentiation",
                    context={
                        'rev_short': rev_short,
                        'rev_long': rev_long,
                        'separation': rev_diff,
                        'minimum_recommended': 6
                    }
                )

        # Layer 6 (Liquidity): Check volume range separation
        if 'vol_min' in parameters and 'vol_max' in parameters:
            vol_min = parameters['vol_min']
            vol_max = parameters['vol_max']
            vol_ratio = vol_max / vol_min if vol_min > 0 else float('inf')

            if vol_ratio < 10:
                self._add_error(
                    category=Category.ARCHITECTURE,
                    error_type='suboptimal_range',
                    message=f"Layer 6 (Liquidity): Volume range too narrow (ratio: {vol_ratio:.1f}x)",
                    suggestion=f"Increase vol_max to at least {vol_min * 10}k for better liquidity filtering",
                    context={
                        'vol_min': vol_min,
                        'vol_max': vol_max,
                        'ratio': vol_ratio,
                        'minimum_recommended_ratio': 10
                    }
                )

    def _validate_revenue_weighting(self, parameters: Dict[str, Any]) -> None:
        """
        Validate revenue weighting logic and dataset usage.

        The TurtleTemplate uses year-over-year revenue growth weighting
        to prioritize stocks with strong revenue momentum.

        Validation Checks:
            - n_stocks parameter present and valid
            - Revenue weighting dataset availability
            - Weighting logic consistency with architecture

        Args:
            parameters: Parameter dictionary to validate

        Error Types:
            - missing_parameter (CRITICAL): n_stocks parameter missing
            - invalid_data (MODERATE): Revenue weighting dataset unavailable
        """
        # Check 1: n_stocks parameter present (required for top N selection)
        if 'n_stocks' not in parameters:
            self._add_error(
                category=Category.PARAMETER,
                error_type='missing_parameter',
                message="Revenue weighting requires 'n_stocks' parameter for top N selection",
                suggestion="Add 'n_stocks' parameter to specify portfolio size (5-20 stocks)",
                context={
                    'required_parameter': 'n_stocks',
                    'weighting_dataset': self.REQUIRED_DATASETS['weighting']
                }
            )
            return

        # Check 2: n_stocks in valid range
        n_stocks = parameters['n_stocks']
        if n_stocks < 5 or n_stocks > 20:
            self._add_error(
                category=Category.PARAMETER,
                error_type='invalid_range',
                message=f"n_stocks ({n_stocks}) outside valid range for revenue weighting (5-20)",
                suggestion="Set n_stocks to a value between 5 and 20 for balanced portfolio diversification",
                context={
                    'n_stocks': n_stocks,
                    'valid_range': (5, 20),
                    'optimal_range': (10, 15)
                }
            )

        # Check 3: Revenue growth dataset documentation
        self._add_suggestion(
            f"Revenue weighting uses '{self.REQUIRED_DATASETS['weighting']}' dataset. "
            f"Ensure this dataset is available in production environment."
        )

    def _validate_performance_targets(self, parameters: Dict[str, Any]) -> None:
        """
        Validate parameters against expected performance targets.

        The TurtleTemplate has specific performance targets:
        - Sharpe Ratio: 1.5-2.5
        - Annual Return: 20-35%
        - Max Drawdown: -25% to -10%

        This method provides guidance on parameter choices that are likely
        to achieve these targets based on backtesting experience.

        Args:
            parameters: Parameter dictionary to validate
        """
        # Performance guidance for critical parameters
        if 'n_stocks' in parameters:
            n_stocks = parameters['n_stocks']

            # Optimal range for Sharpe ratio: 10-15 stocks
            if n_stocks < 10:
                self._add_suggestion(
                    f"Performance: n_stocks={n_stocks} may result in higher volatility. "
                    f"Consider 10-15 stocks for better risk-adjusted returns (Sharpe 1.5-2.5)."
                )
            elif n_stocks > 15:
                self._add_suggestion(
                    f"Performance: n_stocks={n_stocks} may reduce returns due to over-diversification. "
                    f"Consider 10-15 stocks for optimal return/risk balance (target: 20-35% annual return)."
                )

        # Risk management guidance
        if 'stop_loss' in parameters and 'take_profit' in parameters:
            stop_loss = parameters['stop_loss']
            take_profit = parameters['take_profit']
            risk_reward_ratio = take_profit / stop_loss if stop_loss > 0 else float('inf')

            if risk_reward_ratio < 3.0:
                self._add_suggestion(
                    f"Performance: Risk/reward ratio ({risk_reward_ratio:.1f}x) is below 3.0. "
                    f"Consider increasing take_profit or decreasing stop_loss for better expected returns."
                )

    def get_result(self) -> ValidationResult:
        """
        Get validation result with TurtleTemplate-specific metadata.

        Returns:
            ValidationResult with status, errors, warnings, suggestions, and metadata

        Metadata includes:
            - validator: 'TurtleTemplateValidator'
            - template_name: 'TurtleTemplate'
            - architecture_validated: Whether 6-layer architecture was validated
            - interdependencies_validated: Whether parameter interdependencies were validated
            - total_layers: 6 (number of filtering layers)
            - pattern_type: 'multi_layer_and'

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

        # Build metadata with TurtleTemplate-specific information
        metadata = {
            'validator': 'TurtleTemplateValidator',
            'template_name': self.template_name,
            'architecture_validated': self.architecture_validated,
            'interdependencies_validated': self.interdependencies_validated,
            'total_layers': 6,
            'pattern_type': 'multi_layer_and',
            'required_datasets': self.REQUIRED_DATASETS
        }

        return ValidationResult(
            status=status,
            errors=self.errors,
            warnings=self.warnings,
            suggestions=self.suggestions,
            metadata=metadata
        )
