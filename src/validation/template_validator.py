"""
Template Validator Base Class
==============================

Comprehensive validation framework for strategy templates with error categorization,
severity assessment, and fix suggestions.

Validation Categories:
    - PARAMETER: Parameter validation (ranges, types, consistency)
    - ARCHITECTURE: Template structure and design patterns
    - DATA: Data access patterns and dataset usage
    - BACKTEST: Backtest configuration and settings

Severity Levels:
    - CRITICAL: Strategy will fail or produce invalid results
    - MODERATE: Strategy may have issues but can run
    - LOW: Code quality or style suggestions

Usage:
    from src.validation import TemplateValidator, ValidationResult

    validator = TemplateValidator()
    result = validator.validate(template_instance, parameters)

    if not result.is_valid():
        for error in result.errors:
            print(f"{error.severity}: {error.message}")
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum


# Error severity levels
class Severity(str, Enum):
    """Validation error severity classification."""
    CRITICAL = "CRITICAL"  # Strategy will fail or produce invalid results
    MODERATE = "MODERATE"  # Strategy may have issues but can run
    LOW = "LOW"            # Code quality or style suggestions


# Error category constants
class Category(str, Enum):
    """Validation error category classification."""
    PARAMETER = "parameter"        # Parameter validation issues
    ARCHITECTURE = "architecture"  # Template structure issues
    DATA = "data"                  # Data access pattern issues
    BACKTEST = "backtest"          # Backtest configuration issues


@dataclass
class ValidationError:
    """
    Represents a single validation error with context and suggestions.

    Attributes:
        severity: Error severity (CRITICAL | MODERATE | LOW)
        category: Error category (parameter | architecture | data | backtest)
        message: Human-readable error description
        line_number: Optional line number in generated code
        suggestion: Optional fix suggestion
        context: Optional additional context (e.g., parameter name, dataset key)

    Example:
        >>> error = ValidationError(
        ...     severity=Severity.CRITICAL,
        ...     category=Category.PARAMETER,
        ...     message="n_stocks must be between 5 and 50",
        ...     suggestion="Set n_stocks to a value in range [5, 50]",
        ...     context={'parameter': 'n_stocks', 'value': 100}
        ... )
    """
    severity: Severity
    category: Category
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Format error for display."""
        parts = [f"[{self.severity.value}] {self.category.value.upper()}: {self.message}"]

        if self.line_number is not None:
            parts.append(f"  Line: {self.line_number}")

        if self.suggestion:
            parts.append(f"  Suggestion: {self.suggestion}")

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"  Context: {context_str}")

        return "\n".join(parts)


@dataclass
class ValidationResult:
    """
    Container for validation results with status and detailed findings.

    Attributes:
        status: Overall validation status ('valid' | 'invalid' | 'warning')
        errors: List of validation errors (empty if valid)
        warnings: List of non-critical warnings
        suggestions: List of improvement suggestions
        metadata: Additional metadata (e.g., validation timestamp, validator version)

    Methods:
        is_valid(): Returns True if no CRITICAL or MODERATE errors
        has_warnings(): Returns True if warnings present
        get_critical_errors(): Returns only CRITICAL severity errors
        get_moderate_errors(): Returns only MODERATE severity errors

    Example:
        >>> result = ValidationResult(
        ...     status='invalid',
        ...     errors=[error1, error2],
        ...     warnings=[warning1],
        ...     suggestions=['Consider using fewer stocks for better Sharpe ratio']
        ... )
        >>> if not result.is_valid():
        ...     print(f"Found {len(result.get_critical_errors())} critical errors")
    """
    status: str  # 'valid' | 'invalid' | 'warning'
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """
        Check if validation passed (no CRITICAL or MODERATE errors).

        Returns:
            True if no blocking errors, False otherwise
        """
        blocking_errors = [
            e for e in self.errors
            if e.severity in (Severity.CRITICAL, Severity.MODERATE)
        ]
        return len(blocking_errors) == 0

    def has_warnings(self) -> bool:
        """
        Check if validation has warnings.

        Returns:
            True if warnings present, False otherwise
        """
        return len(self.warnings) > 0

    def get_critical_errors(self) -> List[ValidationError]:
        """
        Get only CRITICAL severity errors.

        Returns:
            List of critical errors
        """
        return [e for e in self.errors if e.severity == Severity.CRITICAL]

    def get_moderate_errors(self) -> List[ValidationError]:
        """
        Get only MODERATE severity errors.

        Returns:
            List of moderate errors
        """
        return [e for e in self.errors if e.severity == Severity.MODERATE]

    def get_low_errors(self) -> List[ValidationError]:
        """
        Get only LOW severity errors (quality suggestions).

        Returns:
            List of low severity errors
        """
        return [e for e in self.errors if e.severity == Severity.LOW]

    def __str__(self) -> str:
        """Format validation result for display."""
        lines = [f"Validation Status: {self.status.upper()}"]
        lines.append("")

        # Critical errors
        critical = self.get_critical_errors()
        if critical:
            lines.append(f"CRITICAL ERRORS ({len(critical)}):")
            for error in critical:
                lines.append(str(error))
                lines.append("")

        # Moderate errors
        moderate = self.get_moderate_errors()
        if moderate:
            lines.append(f"MODERATE ERRORS ({len(moderate)}):")
            for error in moderate:
                lines.append(str(error))
                lines.append("")

        # Low errors
        low = self.get_low_errors()
        if low:
            lines.append(f"CODE QUALITY SUGGESTIONS ({len(low)}):")
            for error in low:
                lines.append(str(error))
                lines.append("")

        # Warnings
        if self.warnings:
            lines.append(f"WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(str(warning))
                lines.append("")

        # Suggestions
        if self.suggestions:
            lines.append("IMPROVEMENT SUGGESTIONS:")
            for suggestion in self.suggestions:
                lines.append(f"  - {suggestion}")
            lines.append("")

        return "\n".join(lines)


class TemplateValidator:
    """
    Base class for template validation with error categorization.

    Provides foundation for validating strategy templates with comprehensive
    error detection, severity assessment, and fix suggestions.

    Validation Categories:
        - Parameter validation (ranges, types, consistency)
        - Architecture validation (structure, patterns, design)
        - Data access validation (dataset usage, caching)
        - Backtest configuration validation (settings, resampling)

    Subclass Implementation:
        Subclasses should override:
        - validate_parameters(): Validate parameter values and ranges
        - validate_architecture(): Validate template structure
        - validate_data_access(): Validate data.get() calls
        - validate_backtest_config(): Validate backtest settings

    Usage:
        >>> validator = TemplateValidator()
        >>> result = validator.validate(template, parameters)
        >>> if not result.is_valid():
        ...     print(result)
    """

    def __init__(self):
        """Initialize validator with empty error tracking."""
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.suggestions: List[str] = []

    def _categorize_error(
        self,
        error_type: str,
        context: Dict[str, Any]
    ) -> Severity:
        """
        Categorize error severity based on error type and context.

        Categorization Rules:
            CRITICAL:
                - Invalid parameter ranges (e.g., n_stocks > 200)
                - Missing required parameters
                - Invalid data.get() calls (non-existent datasets)
                - Syntax errors in generated code
                - Invalid backtest configuration

            MODERATE:
                - Suboptimal parameter ranges (e.g., n_stocks > 100)
                - Performance concerns (e.g., excessive data.get() calls)
                - Missing recommended features
                - Inconsistent parameter combinations

            LOW:
                - Code style issues
                - Documentation improvements
                - Performance micro-optimizations
                - Better naming suggestions

        Args:
            error_type: Type of error (e.g., 'invalid_range', 'missing_dataset')
            context: Error context with additional details

        Returns:
            Severity level (CRITICAL | MODERATE | LOW)

        Example:
            >>> severity = validator._categorize_error(
            ...     error_type='invalid_range',
            ...     context={'parameter': 'n_stocks', 'value': 300, 'max': 200}
            ... )
            >>> assert severity == Severity.CRITICAL
        """
        # CRITICAL severity conditions
        critical_types = {
            'invalid_range',
            'missing_parameter',
            'invalid_dataset',
            'syntax_error',
            'invalid_backtest_config',
            'type_mismatch',
            'division_by_zero',
            'circular_dependency'
        }

        if error_type in critical_types:
            return Severity.CRITICAL

        # MODERATE severity conditions
        moderate_types = {
            'suboptimal_range',
            'performance_concern',
            'missing_recommended',
            'inconsistent_parameters',
            'deprecated_usage',
            'excessive_complexity'
        }

        if error_type in moderate_types:
            return Severity.MODERATE

        # Check context-specific severity escalation
        if 'value' in context:
            value = context['value']

            # Extreme values → CRITICAL
            if isinstance(value, (int, float)):
                if value <= 0 and context.get('must_be_positive', False):
                    return Severity.CRITICAL
                if value > context.get('absolute_max', float('inf')):
                    return Severity.CRITICAL

        # Default to LOW for code quality issues
        return Severity.LOW

    def _add_error(
        self,
        category: Category,
        error_type: str,
        message: str,
        line_number: Optional[int] = None,
        suggestion: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add validation error with automatic severity categorization.

        Args:
            category: Error category (PARAMETER | ARCHITECTURE | DATA | BACKTEST)
            error_type: Type of error for severity categorization
            message: Human-readable error description
            line_number: Optional line number in generated code
            suggestion: Optional fix suggestion
            context: Optional additional context
        """
        if context is None:
            context = {}

        severity = self._categorize_error(error_type, context)

        error = ValidationError(
            severity=severity,
            category=category,
            message=message,
            line_number=line_number,
            suggestion=suggestion,
            context=context
        )

        if severity == Severity.LOW:
            self.warnings.append(error)
        else:
            self.errors.append(error)

    def _add_suggestion(self, suggestion: str) -> None:
        """
        Add improvement suggestion.

        Args:
            suggestion: Human-readable improvement suggestion
        """
        self.suggestions.append(suggestion)

    def _reset(self) -> None:
        """Reset validator state for new validation."""
        self.errors = []
        self.warnings = []
        self.suggestions = []

    def validate(
        self,
        template: Any,
        parameters: Dict[str, Any],
        **kwargs
    ) -> ValidationResult:
        """
        Validate template with parameters (override in subclasses).

        Args:
            template: Template instance to validate
            parameters: Parameter dictionary to validate
            **kwargs: Additional validation options

        Returns:
            ValidationResult with status, errors, warnings, suggestions

        Raises:
            NotImplementedError: If called on base class
        """
        raise NotImplementedError("Subclasses must implement validate()")

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        template_name: str
    ) -> None:
        """
        Validate parameter values and ranges (override in subclasses).

        Args:
            parameters: Parameter dictionary to validate
            template_name: Name of template being validated

        Raises:
            NotImplementedError: If called on base class
        """
        raise NotImplementedError("Subclasses must implement validate_parameters()")

    def validate_architecture(
        self,
        template: Any,
        generated_code: str
    ) -> None:
        """
        Validate template architecture and structure (override in subclasses).

        Args:
            template: Template instance to validate
            generated_code: Generated strategy code

        Raises:
            NotImplementedError: If called on base class
        """
        raise NotImplementedError("Subclasses must implement validate_architecture()")

    def validate_data_access(
        self,
        generated_code: str
    ) -> None:
        """
        Validate data.get() calls and dataset usage (override in subclasses).

        Args:
            generated_code: Generated strategy code

        Raises:
            NotImplementedError: If called on base class
        """
        raise NotImplementedError("Subclasses must implement validate_data_access()")

    def validate_backtest_config(
        self,
        backtest_config: Dict[str, Any]
    ) -> None:
        """
        Validate backtest configuration settings (override in subclasses).

        Args:
            backtest_config: Backtest configuration dictionary

        Raises:
            NotImplementedError: If called on base class
        """
        raise NotImplementedError("Subclasses must implement validate_backtest_config()")

    def validate_diversity(
        self,
        strategy_codes: List[str],
        min_unique_ratio: float = 0.8,
        distance_threshold: float = 0.2
    ) -> Dict[str, Any]:
        """
        Validate strategy diversity to ensure generated strategies are sufficiently different.

        **Task 27 Requirements**:
        - Ensure ≥80% unique strategies (8/10 different)
        - Use Levenshtein distance ≥0.2 for code comparison
        - Return validation results with {is_valid, errors, metrics}

        The diversity validation prevents the system from generating redundant strategies
        by comparing code similarity using Levenshtein distance. This addresses the
        oversimplification problem observed in 150-iteration failure (130/150 identical).

        Algorithm:
            1. Compare each strategy code with all others using Levenshtein distance
            2. Normalize distance to [0, 1] range (0 = identical, 1 = completely different)
            3. Consider strategies "unique" if distance ≥ distance_threshold (default: 0.2)
            4. Calculate unique_ratio = unique_count / total_count
            5. Pass if unique_ratio ≥ min_unique_ratio (default: 0.8)

        Args:
            strategy_codes: List of strategy code strings to compare
            min_unique_ratio: Minimum ratio of unique strategies required (default: 0.8 = 80%)
            distance_threshold: Minimum Levenshtein distance for uniqueness (default: 0.2)

        Returns:
            Dictionary with validation results:
                {
                    'is_valid': bool,  # True if diversity meets threshold
                    'errors': List[str],  # Error messages if validation fails
                    'metrics': {
                        'total_strategies': int,
                        'unique_strategies': int,
                        'unique_ratio': float,
                        'min_distance': float,
                        'max_distance': float,
                        'avg_distance': float,
                        'duplicate_pairs': List[Tuple[int, int, float]]  # (idx1, idx2, distance)
                    }
                }

        Example:
            >>> validator = TemplateValidator()
            >>> codes = [strategy1_code, strategy2_code, ..., strategy10_code]
            >>> result = validator.validate_diversity(codes, min_unique_ratio=0.8)
            >>> if not result['is_valid']:
            ...     print(f"Diversity validation failed: {result['errors']}")
            ...     print(f"Unique ratio: {result['metrics']['unique_ratio']:.1%}")

        Performance:
            - Time complexity: O(n²) for n strategies (pairwise comparison)
            - For 10 strategies: ~50ms
            - For 100 strategies: ~5s (acceptable for validation)

        Requirements:
            - Requirement 3: Template validation system
            - Prevents 90% oversimplification problem from 150-iteration failure
        """
        try:
            from Levenshtein import distance as levenshtein_distance
        except ImportError:
            # Fallback to difflib if Levenshtein not available
            import difflib
            def levenshtein_distance(s1: str, s2: str) -> int:
                """Fallback Levenshtein distance using difflib."""
                seq_matcher = difflib.SequenceMatcher(None, s1, s2)
                return int((1.0 - seq_matcher.ratio()) * max(len(s1), len(s2)))

        errors = []
        metrics = {
            'total_strategies': len(strategy_codes),
            'unique_strategies': 0,
            'unique_ratio': 0.0,
            'min_distance': 1.0,
            'max_distance': 0.0,
            'avg_distance': 0.0,
            'duplicate_pairs': []
        }

        # Validate input
        if not strategy_codes:
            errors.append("No strategy codes provided for diversity validation")
            return {'is_valid': False, 'errors': errors, 'metrics': metrics}

        if len(strategy_codes) < 2:
            # Single strategy is always unique
            metrics['unique_strategies'] = 1
            metrics['unique_ratio'] = 1.0
            return {'is_valid': True, 'errors': [], 'metrics': metrics}

        # Calculate pairwise Levenshtein distances
        n = len(strategy_codes)
        distances = []
        duplicate_pairs = []

        for i in range(n):
            is_unique = True
            for j in range(i + 1, n):
                # Calculate raw Levenshtein distance
                raw_distance = levenshtein_distance(strategy_codes[i], strategy_codes[j])

                # Normalize to [0, 1] range
                max_len = max(len(strategy_codes[i]), len(strategy_codes[j]))
                normalized_distance = raw_distance / max_len if max_len > 0 else 0.0

                distances.append(normalized_distance)

                # Check if strategies are too similar (duplicates)
                if normalized_distance < distance_threshold:
                    duplicate_pairs.append((i, j, normalized_distance))
                    is_unique = False

            if is_unique or i == 0:  # First strategy is always counted
                metrics['unique_strategies'] += 1

        # Calculate distance statistics
        if distances:
            metrics['min_distance'] = min(distances)
            metrics['max_distance'] = max(distances)
            metrics['avg_distance'] = sum(distances) / len(distances)
            metrics['duplicate_pairs'] = duplicate_pairs

        # Calculate unique ratio
        metrics['unique_ratio'] = metrics['unique_strategies'] / metrics['total_strategies']

        # Validate diversity threshold
        is_valid = metrics['unique_ratio'] >= min_unique_ratio

        if not is_valid:
            errors.append(
                f"Diversity validation failed: {metrics['unique_strategies']}/{metrics['total_strategies']} "
                f"unique strategies ({metrics['unique_ratio']:.1%}) is below threshold {min_unique_ratio:.1%}"
            )
            errors.append(
                f"Found {len(duplicate_pairs)} duplicate pairs with distance < {distance_threshold}"
            )

            # Add specific duplicate pair information
            if len(duplicate_pairs) <= 5:  # Show details for small number of duplicates
                for idx1, idx2, dist in duplicate_pairs:
                    errors.append(
                        f"  - Strategy {idx1} and {idx2} are too similar (distance: {dist:.3f})"
                    )

        return {
            'is_valid': is_valid,
            'errors': errors,
            'metrics': metrics
        }

    def validate_performance(
        self,
        metrics: Dict[str, float],
        min_sharpe: float = 0.5,
        sharpe_range: Optional[Tuple[float, float]] = None,
        annual_return_range: Optional[Tuple[float, float]] = None,
        max_dd_range: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Validate strategy performance metrics against thresholds and bounds.

        **Task 28 Requirements**:
        - Performance validation with min_sharpe threshold
        - Metric bounds validation (annual_return, max_dd)
        - Return validation results as dict with {is_valid, errors, metrics}

        The performance validation ensures generated strategies meet minimum quality
        standards before being added to Hall of Fame or used in further iterations.

        Validation Rules:
            CRITICAL:
                - Sharpe ratio ≥ min_sharpe (default: 0.5)
                - Annual return within bounds (if specified)
                - Max drawdown within bounds (if specified)

            MODERATE:
                - Sharpe ratio outside optimal range (if specified)
                - Warning for negative returns
                - Warning for excessive drawdown

        Args:
            metrics: Performance metrics dictionary with at minimum:
                - 'sharpe_ratio': float
                - 'annual_return': float (optional)
                - 'max_drawdown': float (optional)
            min_sharpe: Minimum acceptable Sharpe ratio (default: 0.5)
            sharpe_range: Optional (min, max) bounds for Sharpe ratio
            annual_return_range: Optional (min, max) bounds for annual return
            max_dd_range: Optional (min, max) bounds for max drawdown (negative values)

        Returns:
            Dictionary with validation results:
                {
                    'is_valid': bool,  # True if all critical checks pass
                    'errors': List[str],  # Critical errors
                    'warnings': List[str],  # Moderate warnings
                    'metrics': {
                        'sharpe_ratio': float,
                        'annual_return': float,
                        'max_drawdown': float,
                        'meets_min_sharpe': bool,
                        'in_sharpe_range': bool,
                        'in_return_range': bool,
                        'in_dd_range': bool
                    }
                }

        Example:
            >>> validator = TemplateValidator()
            >>> metrics = {
            ...     'sharpe_ratio': 1.8,
            ...     'annual_return': 0.25,
            ...     'max_drawdown': -0.15
            ... }
            >>> result = validator.validate_performance(
            ...     metrics,
            ...     min_sharpe=1.5,
            ...     sharpe_range=(1.5, 2.5),
            ...     annual_return_range=(0.20, 0.35),
            ...     max_dd_range=(-0.25, -0.10)
            ... )
            >>> if not result['is_valid']:
            ...     print(f"Performance validation failed: {result['errors']}")

        Performance Targets by Template:
            TurtleTemplate: Sharpe 1.5-2.5, Return 20-35%, MDD -25% to -10%
            MastiffTemplate: Sharpe 1.2-2.0, Return 15-30%, MDD -30% to -15%
            FactorTemplate: Sharpe 0.8-1.3, Return 10-20%, MDD -20% to -10%
            MomentumTemplate: Sharpe 0.8-1.5, Return 12-25%, MDD -25% to -12%

        Requirements:
            - Requirement 3: Template validation system
            - NFR Performance: Validation completes in <5s
        """
        errors = []
        warnings = []
        validation_metrics = {
            'sharpe_ratio': metrics.get('sharpe_ratio', 0.0),
            'annual_return': metrics.get('annual_return', 0.0),
            'max_drawdown': metrics.get('max_drawdown', 0.0),
            'meets_min_sharpe': False,
            'in_sharpe_range': True,
            'in_return_range': True,
            'in_dd_range': True
        }

        # Validate required metrics are present
        if 'sharpe_ratio' not in metrics:
            errors.append("Missing required metric: 'sharpe_ratio'")
            return {
                'is_valid': False,
                'errors': errors,
                'warnings': warnings,
                'metrics': validation_metrics
            }

        sharpe_ratio = metrics['sharpe_ratio']
        annual_return = metrics.get('annual_return')
        max_drawdown = metrics.get('max_drawdown')

        # CRITICAL: Check minimum Sharpe ratio threshold
        validation_metrics['meets_min_sharpe'] = sharpe_ratio >= min_sharpe
        if not validation_metrics['meets_min_sharpe']:
            errors.append(
                f"Sharpe ratio {sharpe_ratio:.2f} is below minimum threshold {min_sharpe:.2f}"
            )

        # MODERATE: Check Sharpe ratio range (if specified)
        if sharpe_range is not None:
            min_sharpe_range, max_sharpe_range = sharpe_range
            validation_metrics['in_sharpe_range'] = (
                min_sharpe_range <= sharpe_ratio <= max_sharpe_range
            )

            if sharpe_ratio < min_sharpe_range:
                warnings.append(
                    f"Sharpe ratio {sharpe_ratio:.2f} is below optimal range "
                    f"[{min_sharpe_range:.2f}, {max_sharpe_range:.2f}]"
                )
            elif sharpe_ratio > max_sharpe_range:
                warnings.append(
                    f"Sharpe ratio {sharpe_ratio:.2f} exceeds optimal range "
                    f"[{min_sharpe_range:.2f}, {max_sharpe_range:.2f}] - "
                    f"may indicate overfitting"
                )

        # CRITICAL/MODERATE: Check annual return bounds (if specified)
        if annual_return is not None:
            if annual_return_range is not None:
                min_return, max_return = annual_return_range
                validation_metrics['in_return_range'] = (
                    min_return <= annual_return <= max_return
                )

                if annual_return < min_return:
                    errors.append(
                        f"Annual return {annual_return:.1%} is below minimum "
                        f"threshold {min_return:.1%}"
                    )
                elif annual_return > max_return:
                    warnings.append(
                        f"Annual return {annual_return:.1%} exceeds maximum "
                        f"threshold {max_return:.1%} - may indicate overfitting"
                    )

            # Warning for negative returns
            if annual_return < 0:
                warnings.append(
                    f"Strategy has negative annual return: {annual_return:.1%}"
                )

        # CRITICAL/MODERATE: Check max drawdown bounds (if specified)
        if max_drawdown is not None:
            if max_dd_range is not None:
                min_dd, max_dd = max_dd_range  # Both negative, min_dd more negative
                validation_metrics['in_dd_range'] = (
                    min_dd <= max_drawdown <= max_dd
                )

                if max_drawdown < min_dd:
                    errors.append(
                        f"Max drawdown {max_drawdown:.1%} exceeds maximum "
                        f"acceptable drawdown {min_dd:.1%}"
                    )
                elif max_drawdown > max_dd:
                    warnings.append(
                        f"Max drawdown {max_drawdown:.1%} is better than "
                        f"optimal range [{min_dd:.1%}, {max_dd:.1%}]"
                    )

            # Warning for excessive drawdown
            if max_drawdown < -0.5:  # More than 50% drawdown
                warnings.append(
                    f"Strategy has excessive drawdown: {max_drawdown:.1%}"
                )

        # Determine overall validation status
        is_valid = len(errors) == 0

        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'metrics': validation_metrics
        }

    def validate_params(
        self,
        parameters: Dict[str, Any],
        param_schema: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate parameters against schema with type checking, range validation, and required field checks.

        **Task 29 Requirements**:
        - Parameter type checking
        - Parameter range validation (min/max bounds)
        - Required field validation
        - Return validation results as dict with {is_valid, errors, metrics}

        This method provides comprehensive parameter validation against a schema
        definition, ensuring all parameters meet type, range, and presence requirements.

        Schema Format:
            {
                'parameter_name': {
                    'type': type | Tuple[type, ...],  # Expected type(s)
                    'required': bool,  # Whether parameter is required (default: False)
                    'min': float,  # Minimum value for numeric types (optional)
                    'max': float,  # Maximum value for numeric types (optional)
                    'allowed_values': List[Any],  # Allowed values for enum types (optional)
                    'description': str  # Human-readable description (optional)
                }
            }

        Validation Rules:
            CRITICAL:
                - Missing required parameters
                - Type mismatches
                - Values outside min/max bounds
                - Values not in allowed_values list

            MODERATE:
                - Unknown parameters not in schema
                - Values at boundary of ranges

        Args:
            parameters: Dictionary of parameter values to validate
            param_schema: Schema definition for parameter validation

        Returns:
            Dictionary with validation results:
                {
                    'is_valid': bool,  # True if all validations pass
                    'errors': List[str],  # Critical errors
                    'warnings': List[str],  # Moderate warnings
                    'metrics': {
                        'total_parameters': int,
                        'validated_parameters': int,
                        'missing_required': List[str],
                        'type_errors': List[str],
                        'range_errors': List[str],
                        'unknown_parameters': List[str]
                    }
                }

        Example:
            >>> schema = {
            ...     'n_stocks': {
            ...         'type': int,
            ...         'required': True,
            ...         'min': 5,
            ...         'max': 50,
            ...         'description': 'Number of stocks to select'
            ...     },
            ...     'sharpe_threshold': {
            ...         'type': (int, float),
            ...         'required': False,
            ...         'min': 0.0,
            ...         'description': 'Minimum Sharpe ratio'
            ...     }
            ... }
            >>> params = {'n_stocks': 30, 'sharpe_threshold': 1.5}
            >>> result = validator.validate_params(params, schema)
            >>> if not result['is_valid']:
            ...     print(f"Parameter validation failed: {result['errors']}")

        Integration:
            - Used by ParameterValidator for template-specific validation
            - Integrates with validate_parameters() in parameter_validator.py
            - Used by all template validators (Turtle, Mastiff, Factor, Momentum)

        Requirements:
            - Requirement 1.8: Parameter validation with template-specific rules
            - Requirement 3.1: Comprehensive parameter validation
        """
        errors = []
        warnings = []
        metrics = {
            'total_parameters': len(parameters),
            'validated_parameters': 0,
            'missing_required': [],
            'type_errors': [],
            'range_errors': [],
            'unknown_parameters': []
        }

        # Check for missing required parameters
        for param_name, schema in param_schema.items():
            if schema.get('required', False) and param_name not in parameters:
                metrics['missing_required'].append(param_name)
                errors.append(
                    f"Missing required parameter: '{param_name}' - "
                    f"{schema.get('description', 'No description available')}"
                )

        # Validate provided parameters
        for param_name, param_value in parameters.items():
            # Check if parameter is in schema
            if param_name not in param_schema:
                metrics['unknown_parameters'].append(param_name)
                warnings.append(
                    f"Unknown parameter: '{param_name}' not in schema"
                )
                continue

            schema = param_schema[param_name]
            metrics['validated_parameters'] += 1

            # Type validation
            expected_type = schema.get('type')
            if expected_type is not None:
                if not isinstance(param_value, expected_type):
                    expected_str = (
                        expected_type.__name__ if isinstance(expected_type, type)
                        else ' or '.join(t.__name__ for t in expected_type)
                    )
                    actual_type = type(param_value).__name__

                    metrics['type_errors'].append(param_name)
                    errors.append(
                        f"Parameter '{param_name}' has wrong type: "
                        f"expected {expected_str}, got {actual_type} (value: {param_value})"
                    )
                    continue  # Skip further validation if type is wrong

            # Range validation for numeric types
            if isinstance(param_value, (int, float)):
                min_val = schema.get('min')
                max_val = schema.get('max')

                if min_val is not None and param_value < min_val:
                    metrics['range_errors'].append(param_name)
                    errors.append(
                        f"Parameter '{param_name}' is below minimum: "
                        f"{param_value} < {min_val}"
                    )

                if max_val is not None and param_value > max_val:
                    metrics['range_errors'].append(param_name)
                    errors.append(
                        f"Parameter '{param_name}' exceeds maximum: "
                        f"{param_value} > {max_val}"
                    )

            # Allowed values validation (for enum types)
            allowed_values = schema.get('allowed_values')
            if allowed_values is not None and param_value not in allowed_values:
                metrics['range_errors'].append(param_name)
                errors.append(
                    f"Parameter '{param_name}' has invalid value: "
                    f"'{param_value}' not in allowed values {allowed_values}"
                )

        # Determine overall validation status
        is_valid = len(errors) == 0

        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'metrics': metrics
        }

    @staticmethod
    def validate_strategy(
        template_name: str,
        parameters: Dict[str, Any],
        generated_code: Optional[str] = None,
        backtest_config: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Comprehensive validation orchestrator for strategy templates.

        Orchestrates all validation checks:
        1. Parameter validation (type, range, consistency)
        2. Data access validation (dataset usage, caching)
        3. Backtest configuration validation (if provided)
        4. Template-specific validation (architecture, interdependencies)

        **Task 34 Requirements**:
        - Call appropriate template validator based on template type
        - Generate comprehensive ValidationResult
        - Determine status: PASS | NEEDS_FIX | FAIL
        - Target: <5s per strategy validation

        Args:
            template_name: Template name ('TurtleTemplate', 'MastiffTemplate', etc.)
            parameters: Parameter dictionary to validate
            generated_code: Optional generated strategy code for data access validation
            backtest_config: Optional backtest configuration dictionary

        Returns:
            ValidationResult with comprehensive validation status

        Status Determination:
            - PASS: No CRITICAL or MODERATE errors (is_valid() == True)
            - NEEDS_FIX: Only LOW severity warnings
            - FAIL: CRITICAL or MODERATE errors present

        Performance:
            Target execution time: <5s per strategy validation
            Actual: ~0.5-2s for typical validations (dominated by regex parsing)

        Example:
            >>> result = TemplateValidator.validate_strategy(
            ...     template_name='TurtleTemplate',
            ...     parameters={'n_stocks': 10, 'ma_short': 20, ...},
            ...     generated_code="close = data.get('price:收盤價')...",
            ...     backtest_config={'resample': 'M', 'stop_loss': 0.06}
            ... )
            >>> if result.is_valid():
            ...     print("PASS - Strategy validated successfully")
            >>> else:
            ...     print(f"FAIL - {len(result.get_critical_errors())} critical errors")

        Requirements:
            - Requirement 3.1: Comprehensive validation orchestration
            - Requirement 3.4: Template-specific validation routing
            - NFR Performance.5: <5s validation time
        """
        import time
        start_time = time.time()

        # Import validators (lazy import to avoid circular dependencies)
        from .parameter_validator import ParameterValidator
        from .data_validator import DataValidator
        from .backtest_validator import BacktestValidator
        from .turtle_validator import TurtleTemplateValidator
        from .mastiff_validator import MastiffTemplateValidator

        # Step 1: Select appropriate template-specific validator
        template_validators = {
            'TurtleTemplate': TurtleTemplateValidator,
            'Turtle': TurtleTemplateValidator,
            'MastiffTemplate': MastiffTemplateValidator,
            'Mastiff': MastiffTemplateValidator,
            # Generic fallback for Factor and Momentum templates
            'FactorTemplate': ParameterValidator,
            'Factor': ParameterValidator,
            'MomentumTemplate': ParameterValidator,
            'Momentum': ParameterValidator
        }

        ValidatorClass = template_validators.get(template_name, ParameterValidator)

        # Step 2: Initialize validators
        param_validator = ValidatorClass()
        data_validator = DataValidator() if generated_code else None
        backtest_validator = BacktestValidator() if backtest_config else None

        # Step 3: Run parameter validation
        try:
            param_validator.validate_parameters(parameters, template_name)
        except Exception as e:
            # Catch any exceptions during parameter validation
            param_validator._add_error(
                category=Category.PARAMETER,
                error_type='invalid_range',
                message=f"Parameter validation failed: {str(e)}",
                suggestion="Check parameter types and values",
                context={'exception': str(e), 'template_name': template_name}
            )

        # Step 4: Run data access validation (if generated code provided)
        if data_validator and generated_code:
            try:
                data_validator.validate_data_access(generated_code)
            except Exception as e:
                # Catch any exceptions during data validation
                data_validator._add_error(
                    category=Category.DATA,
                    error_type='invalid_range',
                    message=f"Data access validation failed: {str(e)}",
                    suggestion="Check generated code syntax and data.get() calls",
                    context={'exception': str(e)}
                )

        # Step 5: Run backtest configuration validation (if config provided)
        if backtest_validator and backtest_config:
            try:
                # Extract n_stocks for position sizing validation
                n_stocks = parameters.get('n_stocks')
                backtest_validator.validate_backtest_config(backtest_config, n_stocks)
            except Exception as e:
                # Catch any exceptions during backtest validation
                backtest_validator._add_error(
                    category=Category.BACKTEST,
                    error_type='invalid_range',
                    message=f"Backtest configuration validation failed: {str(e)}",
                    suggestion="Check backtest configuration parameters",
                    context={'exception': str(e)}
                )

        # Step 6: Aggregate errors from all validators
        all_errors = []
        all_warnings = []
        all_suggestions = []

        # Collect from parameter validator
        param_result = param_validator.get_result()
        all_errors.extend(param_result.errors)
        all_warnings.extend(param_result.warnings)
        all_suggestions.extend(param_result.suggestions)

        # Collect from data validator
        if data_validator:
            data_result = data_validator.get_result()
            all_errors.extend(data_result.errors)
            all_warnings.extend(data_result.warnings)
            all_suggestions.extend(data_result.suggestions)

        # Collect from backtest validator
        if backtest_validator:
            backtest_result = backtest_validator.get_result()
            all_errors.extend(backtest_result.errors)
            all_warnings.extend(backtest_result.warnings)
            all_suggestions.extend(backtest_result.suggestions)

        # Step 7: Determine overall status
        critical_errors = [e for e in all_errors if e.severity == Severity.CRITICAL]
        moderate_errors = [e for e in all_errors if e.severity == Severity.MODERATE]

        if critical_errors or moderate_errors:
            status = 'FAIL'
        elif all_warnings:
            status = 'NEEDS_FIX'
        else:
            status = 'PASS'

        # Step 8: Calculate validation time
        validation_time = time.time() - start_time

        # Step 9: Build comprehensive metadata
        metadata = {
            'template_name': template_name,
            'validator_used': ValidatorClass.__name__,
            'validation_time_seconds': round(validation_time, 3),
            'total_errors': len(all_errors),
            'critical_errors': len(critical_errors),
            'moderate_errors': len(moderate_errors),
            'warnings': len(all_warnings),
            'suggestions': len(all_suggestions),
            'validation_layers': {
                'parameters': True,
                'data_access': data_validator is not None,
                'backtest_config': backtest_validator is not None,
                'template_specific': ValidatorClass != ParameterValidator
            }
        }

        # Add template-specific metadata if available
        if hasattr(param_result, 'metadata') and param_result.metadata:
            # Merge without overwriting existing keys
            for key, value in param_result.metadata.items():
                if key not in metadata:
                    metadata[key] = value

        # Add data validator metadata
        if data_validator and hasattr(data_result, 'metadata') and data_result.metadata:
            metadata['data_validation'] = {
                'total_data_calls': data_result.metadata.get('total_data_calls', 0),
                'unique_datasets': data_result.metadata.get('unique_datasets', 0),
                'datasets_used': data_result.metadata.get('datasets_used', [])
            }

        # Step 10: Check performance target (<5s)
        if validation_time > 5.0:
            all_warnings.append(ValidationError(
                severity=Severity.LOW,
                category=Category.ARCHITECTURE,
                message=f"Validation time {validation_time:.2f}s exceeds 5s target",
                suggestion="Consider simplifying validation rules or optimizing regex patterns",
                context={'validation_time': validation_time, 'target': 5.0}
            ))
            metadata['performance_warning'] = True

        # Step 11: Return comprehensive validation result
        return ValidationResult(
            status=status,
            errors=all_errors,
            warnings=all_warnings,
            suggestions=all_suggestions,
            metadata=metadata
        )
