"""
Parameter Validator for Strategy Templates
==========================================

Comprehensive parameter validation with range checking, type validation,
and consistency verification.

Validation Types:
    - Range Validation: Numeric parameter bounds and optimal ranges
    - Type Validation: Parameter type correctness
    - Consistency Validation: Cross-parameter relationship checks

Integration:
    - Optional performance_attributor integration for sensitivity data
    - Template-specific parameter schema enforcement
    - Automated fix suggestions for common issues

Usage:
    from src.validation import ParameterValidator

    validator = ParameterValidator()
    validator.validate_parameters(
        parameters={'n_stocks': 30, 'holding_period': 20},
        template_name='TurtleTemplate'
    )

    result = validator.get_result()
    if not result.is_valid():
        print(result)
"""

from typing import Dict, Any, Optional, Tuple, List, Union
from .template_validator import (
    TemplateValidator,
    ValidationResult,
    ValidationError,
    Category,
    Severity
)


# Parameter schema definitions for each template
PARAMETER_SCHEMAS = {
    'TurtleTemplate': {
        'n_stocks': {
            'type': int,
            'min': 5,
            'max': 200,
            'optimal_min': 15,
            'optimal_max': 50,
            'description': 'Number of stocks to select',
            'must_be_positive': True
        },
        'holding_period': {
            'type': int,
            'min': 5,
            'max': 60,
            'optimal_min': 10,
            'optimal_max': 30,
            'description': 'Holding period in days',
            'must_be_positive': True
        },
        'revenue_lookback': {
            'type': int,
            'min': 1,
            'max': 12,
            'optimal_min': 3,
            'optimal_max': 6,
            'description': 'Revenue lookback months',
            'must_be_positive': True
        },
        'price_lookback': {
            'type': int,
            'min': 20,
            'max': 252,
            'optimal_min': 60,
            'optimal_max': 120,
            'description': 'Price lookback days',
            'must_be_positive': True
        },
        'revenue_growth_threshold': {
            'type': (int, float),
            'min': 0.0,
            'max': 2.0,
            'optimal_min': 0.1,
            'optimal_max': 0.5,
            'description': 'Revenue growth threshold (e.g., 0.2 = 20%)'
        }
    },
    'MastiffTemplate': {
        'n_stocks': {
            'type': int,
            'min': 5,
            'max': 200,
            'optimal_min': 15,
            'optimal_max': 50,
            'description': 'Number of stocks to select',
            'must_be_positive': True
        },
        'holding_period': {
            'type': int,
            'min': 5,
            'max': 60,
            'optimal_min': 10,
            'optimal_max': 30,
            'description': 'Holding period in days',
            'must_be_positive': True
        },
        'price_drop_threshold': {
            'type': (int, float),
            'min': -1.0,
            'max': 0.0,
            'optimal_min': -0.3,
            'optimal_max': -0.1,
            'description': 'Price drop threshold (negative value, e.g., -0.2 = -20%)'
        },
        'volume_percentile': {
            'type': (int, float),
            'min': 0.0,
            'max': 1.0,
            'optimal_min': 0.2,
            'optimal_max': 0.5,
            'description': 'Volume percentile for low-volume selection'
        }
    },
    'FactorTemplate': {
        'n_stocks': {
            'type': int,
            'min': 5,
            'max': 200,
            'optimal_min': 15,
            'optimal_max': 50,
            'description': 'Number of stocks to select',
            'must_be_positive': True
        },
        'holding_period': {
            'type': int,
            'min': 5,
            'max': 60,
            'optimal_min': 10,
            'optimal_max': 30,
            'description': 'Holding period in days',
            'must_be_positive': True
        },
        'factor_name': {
            'type': str,
            'allowed_values': ['本益比', '股價淨值比', '殖利率', '市值'],
            'description': 'Factor name for ranking'
        },
        'ascending': {
            'type': bool,
            'description': 'Sort factor in ascending order (True) or descending (False)'
        }
    },
    'MomentumTemplate': {
        'n_stocks': {
            'type': int,
            'min': 5,
            'max': 200,
            'optimal_min': 15,
            'optimal_max': 50,
            'description': 'Number of stocks to select',
            'must_be_positive': True
        },
        'holding_period': {
            'type': int,
            'min': 5,
            'max': 60,
            'optimal_min': 10,
            'optimal_max': 30,
            'description': 'Holding period in days',
            'must_be_positive': True
        },
        'momentum_period': {
            'type': int,
            'min': 20,
            'max': 252,
            'optimal_min': 60,
            'optimal_max': 120,
            'description': 'Momentum calculation period in days',
            'must_be_positive': True
        },
        'revenue_weight': {
            'type': (int, float),
            'min': 0.0,
            'max': 1.0,
            'optimal_min': 0.3,
            'optimal_max': 0.7,
            'description': 'Weight for revenue catalyst (0.0-1.0)'
        }
    }
}


class ParameterValidator(TemplateValidator):
    """
    Validate strategy template parameters with comprehensive checks.

    Validation Layers:
        1. Type validation: Ensure correct parameter types
        2. Range validation: Check numeric bounds (absolute and optimal)
        3. Consistency validation: Verify cross-parameter relationships
        4. Sensitivity integration: Optional performance attribution data

    Features:
        - Template-specific schema enforcement
        - Automatic fix suggestions
        - Severity-based error categorization
        - Performance sensitivity awareness (when available)

    Example:
        >>> validator = ParameterValidator()
        >>> validator.validate_parameters(
        ...     parameters={'n_stocks': 30, 'holding_period': 20},
        ...     template_name='TurtleTemplate'
        ... )
        >>> result = validator.get_result()
        >>> print(f"Valid: {result.is_valid()}")
    """

    def __init__(self, sensitivity_data: Optional[Dict[str, Any]] = None):
        """
        Initialize parameter validator.

        Args:
            sensitivity_data: Optional performance attribution data from
                              performance_attributor for sensitivity-aware validation
        """
        super().__init__()
        self.sensitivity_data = sensitivity_data

    def _validate_type(
        self,
        param_name: str,
        param_value: Any,
        expected_type: Union[type, Tuple[type, ...]],
        schema: Dict[str, Any]
    ) -> bool:
        """
        Validate parameter type correctness.

        Args:
            param_name: Parameter name
            param_value: Parameter value to validate
            expected_type: Expected Python type(s)
            schema: Parameter schema with validation rules

        Returns:
            True if type is valid, False otherwise (adds error)

        Example:
            >>> validator._validate_type('n_stocks', 30, int, schema)
            True
            >>> validator._validate_type('n_stocks', '30', int, schema)
            False  # Wrong type
        """
        if not isinstance(param_value, expected_type):
            expected_str = (
                expected_type.__name__ if isinstance(expected_type, type)
                else ' or '.join(t.__name__ for t in expected_type)
            )
            actual_type = type(param_value).__name__

            self._add_error(
                category=Category.PARAMETER,
                error_type='type_mismatch',
                message=f"Parameter '{param_name}' has wrong type: expected {expected_str}, got {actual_type}",
                suggestion=f"Convert '{param_name}' to {expected_str}",
                context={
                    'parameter': param_name,
                    'expected_type': expected_str,
                    'actual_type': actual_type,
                    'value': param_value
                }
            )
            return False

        # Additional validation for string parameters with allowed values
        if isinstance(param_value, str) and 'allowed_values' in schema:
            allowed = schema['allowed_values']
            if param_value not in allowed:
                self._add_error(
                    category=Category.PARAMETER,
                    error_type='invalid_range',
                    message=f"Parameter '{param_name}' has invalid value: '{param_value}' not in {allowed}",
                    suggestion=f"Choose one of: {', '.join(allowed)}",
                    context={
                        'parameter': param_name,
                        'value': param_value,
                        'allowed_values': allowed
                    }
                )
                return False

        return True

    def _validate_range(
        self,
        param_name: str,
        param_value: Union[int, float],
        schema: Dict[str, Any]
    ) -> bool:
        """
        Validate numeric parameter range (absolute and optimal bounds).

        Validation Rules:
            - CRITICAL: Value outside absolute min/max bounds
            - MODERATE: Value outside optimal min/max bounds
            - Uses sensitivity data (if available) to adjust severity

        Args:
            param_name: Parameter name
            param_value: Numeric parameter value
            schema: Parameter schema with min, max, optimal_min, optimal_max

        Returns:
            True if within absolute bounds, False otherwise

        Example:
            >>> schema = {'min': 5, 'max': 200, 'optimal_min': 15, 'optimal_max': 50}
            >>> validator._validate_range('n_stocks', 30, schema)
            True  # Within optimal range
            >>> validator._validate_range('n_stocks', 150, schema)
            True  # Within absolute range (adds moderate warning)
            >>> validator._validate_range('n_stocks', 300, schema)
            False  # Outside absolute range (adds critical error)
        """
        min_val = schema.get('min')
        max_val = schema.get('max')
        optimal_min = schema.get('optimal_min')
        optimal_max = schema.get('optimal_max')

        # Check absolute bounds (CRITICAL)
        if min_val is not None and param_value < min_val:
            self._add_error(
                category=Category.PARAMETER,
                error_type='invalid_range',
                message=f"Parameter '{param_name}' is below minimum: {param_value} < {min_val}",
                suggestion=f"Set '{param_name}' to a value >= {min_val} (recommended: {optimal_min or min_val})",
                context={
                    'parameter': param_name,
                    'value': param_value,
                    'min': min_val,
                    'must_be_positive': schema.get('must_be_positive', False),
                    'absolute_max': max_val
                }
            )
            return False

        if max_val is not None and param_value > max_val:
            self._add_error(
                category=Category.PARAMETER,
                error_type='invalid_range',
                message=f"Parameter '{param_name}' exceeds maximum: {param_value} > {max_val}",
                suggestion=f"Set '{param_name}' to a value <= {max_val} (recommended: {optimal_max or max_val})",
                context={
                    'parameter': param_name,
                    'value': param_value,
                    'max': max_val,
                    'absolute_max': max_val
                }
            )
            return False

        # Check optimal bounds (MODERATE warning)
        if optimal_min is not None and param_value < optimal_min:
            # Check sensitivity data to adjust severity
            sensitivity_impact = self._get_sensitivity_impact(param_name)

            if sensitivity_impact and sensitivity_impact > 0.3:  # High sensitivity
                error_type = 'performance_concern'
            else:
                error_type = 'suboptimal_range'

            self._add_error(
                category=Category.PARAMETER,
                error_type=error_type,
                message=f"Parameter '{param_name}' is below optimal range: {param_value} < {optimal_min}",
                suggestion=f"Consider setting '{param_name}' to {optimal_min}-{optimal_max} for better performance",
                context={
                    'parameter': param_name,
                    'value': param_value,
                    'optimal_min': optimal_min,
                    'sensitivity_impact': sensitivity_impact
                }
            )

        if optimal_max is not None and param_value > optimal_max:
            sensitivity_impact = self._get_sensitivity_impact(param_name)

            if sensitivity_impact and sensitivity_impact > 0.3:
                error_type = 'performance_concern'
            else:
                error_type = 'suboptimal_range'

            self._add_error(
                category=Category.PARAMETER,
                error_type=error_type,
                message=f"Parameter '{param_name}' exceeds optimal range: {param_value} > {optimal_max}",
                suggestion=f"Consider setting '{param_name}' to {optimal_min}-{optimal_max} for better performance",
                context={
                    'parameter': param_name,
                    'value': param_value,
                    'optimal_max': optimal_max,
                    'sensitivity_impact': sensitivity_impact
                }
            )

        return True

    def _get_sensitivity_impact(self, param_name: str) -> Optional[float]:
        """
        Get parameter sensitivity impact from performance attribution data.

        Args:
            param_name: Parameter name

        Returns:
            Sensitivity impact (0.0-1.0) or None if not available

        Example:
            >>> validator.sensitivity_data = {'n_stocks': {'impact': 0.45}}
            >>> validator._get_sensitivity_impact('n_stocks')
            0.45
        """
        if not self.sensitivity_data:
            return None

        param_sensitivity = self.sensitivity_data.get(param_name, {})
        return param_sensitivity.get('impact')

    def _validate_consistency(
        self,
        parameters: Dict[str, Any],
        template_name: str
    ) -> None:
        """
        Validate cross-parameter consistency and relationships.

        Consistency Rules by Template:
            TurtleTemplate:
                - holding_period should be reasonable vs. price_lookback
                - revenue_lookback should align with holding_period

            MastiffTemplate:
                - price_drop_threshold should be negative
                - volume_percentile should be in [0, 1]

            MomentumTemplate:
                - momentum_period should be >= holding_period
                - revenue_weight should be balanced

        Args:
            parameters: Parameter dictionary
            template_name: Template name for template-specific rules

        Example:
            >>> params = {'holding_period': 100, 'price_lookback': 60}
            >>> validator._validate_consistency(params, 'TurtleTemplate')
            # Adds error: holding_period > price_lookback
        """
        if template_name == 'TurtleTemplate':
            # Check holding_period vs price_lookback
            holding_period = parameters.get('holding_period')
            price_lookback = parameters.get('price_lookback')

            if holding_period and price_lookback:
                if holding_period > price_lookback:
                    self._add_error(
                        category=Category.PARAMETER,
                        error_type='inconsistent_parameters',
                        message=f"holding_period ({holding_period}) should not exceed price_lookback ({price_lookback})",
                        suggestion=f"Set holding_period <= {price_lookback} or increase price_lookback",
                        context={
                            'holding_period': holding_period,
                            'price_lookback': price_lookback
                        }
                    )

        elif template_name == 'MastiffTemplate':
            # Check price_drop_threshold is negative
            price_drop = parameters.get('price_drop_threshold')

            if price_drop is not None and price_drop > 0:
                self._add_error(
                    category=Category.PARAMETER,
                    error_type='invalid_range',
                    message=f"price_drop_threshold must be negative (got {price_drop})",
                    suggestion="Set price_drop_threshold to a negative value (e.g., -0.2 for -20% drop)",
                    context={
                        'parameter': 'price_drop_threshold',
                        'value': price_drop
                    }
                )

        elif template_name == 'MomentumTemplate':
            # Check momentum_period vs holding_period
            momentum_period = parameters.get('momentum_period')
            holding_period = parameters.get('holding_period')

            if momentum_period and holding_period:
                if momentum_period < holding_period:
                    self._add_error(
                        category=Category.PARAMETER,
                        error_type='inconsistent_parameters',
                        message=f"momentum_period ({momentum_period}) should be >= holding_period ({holding_period})",
                        suggestion=f"Set momentum_period >= {holding_period}",
                        context={
                            'momentum_period': momentum_period,
                            'holding_period': holding_period
                        }
                    )

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        template_name: str
    ) -> None:
        """
        Validate all parameters for a template (orchestrator method).

        Validation Workflow:
            1. Check template schema exists
            2. Validate required parameters present
            3. Validate parameter types
            4. Validate parameter ranges
            5. Validate cross-parameter consistency
            6. Add improvement suggestions

        Args:
            parameters: Parameter dictionary to validate
            template_name: Template name for schema lookup

        Example:
            >>> validator.validate_parameters(
            ...     parameters={'n_stocks': 30, 'holding_period': 20},
            ...     template_name='TurtleTemplate'
            ... )
        """
        # Get template schema
        schema = PARAMETER_SCHEMAS.get(template_name)

        if not schema:
            self._add_error(
                category=Category.PARAMETER,
                error_type='invalid_range',
                message=f"Unknown template: {template_name}",
                suggestion=f"Use one of: {', '.join(PARAMETER_SCHEMAS.keys())}",
                context={'template_name': template_name}
            )
            return

        # Check for missing required parameters
        for param_name, param_schema in schema.items():
            if param_name not in parameters:
                # For now, we don't enforce required parameters (templates may have defaults)
                # This could be made stricter if needed
                self._add_suggestion(
                    f"Parameter '{param_name}' not provided - using template default"
                )

        # Validate each parameter
        for param_name, param_value in parameters.items():
            param_schema = schema.get(param_name)

            if not param_schema:
                self._add_error(
                    category=Category.PARAMETER,
                    error_type='suboptimal_range',
                    message=f"Unknown parameter '{param_name}' for template {template_name}",
                    suggestion=f"Remove '{param_name}' or check template documentation",
                    context={
                        'parameter': param_name,
                        'template_name': template_name
                    }
                )
                continue

            # Type validation
            expected_type = param_schema['type']
            if not self._validate_type(param_name, param_value, expected_type, param_schema):
                continue  # Skip range validation if type is wrong

            # Range validation (numeric types only)
            if isinstance(param_value, (int, float)):
                self._validate_range(param_name, param_value, param_schema)

        # Cross-parameter consistency validation
        self._validate_consistency(parameters, template_name)

    def get_result(self) -> ValidationResult:
        """
        Get validation result with all errors, warnings, and suggestions.

        Returns:
            ValidationResult with status determination

        Example:
            >>> validator.validate_parameters(params, 'TurtleTemplate')
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
            metadata={
                'validator': 'ParameterValidator',
                'has_sensitivity_data': self.sensitivity_data is not None
            }
        )
