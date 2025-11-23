"""Validation result data structures for Layer 2 field validator.

This module provides structured error reporting for the AST-based field validator.
It includes FieldError and FieldWarning for individual issues, and ValidationResult
for aggregating validation outcomes.

Key Features:
- Line/column tracking for precise error location
- Error type classification for targeted fixes
- Suggestion system for auto-correction hints
- Separation of errors (blocking) vs warnings (non-blocking)
- ValidationMetadata for tracking multi-layer validation (Task 7.1)

Usage:
    >>> result = ValidationResult()
    >>> result.add_error(
    ...     line=10, column=15, field_name='price:成交量',
    ...     error_type='invalid_field', message='Invalid field name',
    ...     suggestion='Did you mean "price:成交金額"?'
    ... )
    >>> print(result.is_valid)  # False
    >>> print(result)
    Errors (1):
      - Line 10:15 - invalid_field: Invalid field name (Did you mean "price:成交金額"?)
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class ValidationMetadata:
    """Metadata from multi-layer validation pipeline.

    Tracks execution details across all validation layers including latency,
    error counts, and layer results. Used for monitoring, debugging, and
    optimization of the validation system.

    Attributes:
        layers_executed: List of layer names that were executed (e.g., ["Layer1", "Layer2"])
        layer_results: Dict mapping layer name to pass/fail boolean
        layer_latencies: Dict mapping layer name to latency in milliseconds
        total_latency_ms: Total validation time across all layers in milliseconds
        error_counts: Dict mapping layer name to number of errors found
        timestamp: ISO format timestamp when validation occurred

    Example:
        >>> metadata = ValidationMetadata(
        ...     layers_executed=["Layer1", "Layer2"],
        ...     layer_results={"Layer1": True, "Layer2": False},
        ...     layer_latencies={"Layer1": 0.5, "Layer2": 1.2},
        ...     total_latency_ms=1.7,
        ...     error_counts={"Layer1": 0, "Layer2": 2},
        ...     timestamp="2025-11-19T10:00:00"
        ... )
        >>> print(metadata.total_latency_ms)
        1.7
    """
    layers_executed: List[str] = field(default_factory=list)
    layer_results: Dict[str, bool] = field(default_factory=dict)
    layer_latencies: Dict[str, float] = field(default_factory=dict)
    total_latency_ms: float = 0.0
    error_counts: Dict[str, int] = field(default_factory=dict)
    timestamp: str = ""


@dataclass
class FieldError:
    """
    Represents a field validation error with location and suggestion.

    Errors are blocking issues that prevent code execution or produce incorrect results.
    Each error includes precise location information (line/column) and optional suggestions
    for auto-correction.

    Attributes:
        line: Line number where error occurred (1-indexed)
        column: Column number where error occurred (0-indexed)
        field_name: Invalid field name that caused the error
        error_type: Type of error ('invalid_field', 'syntax_error', 'type_mismatch', etc.)
        message: Human-readable error message
        suggestion: Optional suggestion for correction (e.g., "Did you mean 'price:成交金額'?")

    Example:
        >>> error = FieldError(
        ...     line=10, column=15, field_name='price:成交量',
        ...     error_type='invalid_field', message='Invalid field name',
        ...     suggestion='Did you mean "price:成交金額"?'
        ... )
        >>> print(error)
        Line 10:15 - invalid_field: Invalid field name (Did you mean "price:成交金額"?)
    """
    line: int
    column: int
    field_name: str
    error_type: str
    message: str
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """Format error as string for display.

        Returns:
            Formatted string: "Line {line}:{column} - {error_type}: {message} ({suggestion})"
        """
        base = f"Line {self.line}:{self.column} - {self.error_type}: {self.message}"
        if self.suggestion:
            base += f" ({self.suggestion})"
        return base


@dataclass
class FieldWarning:
    """
    Represents a field validation warning (non-critical issue).

    Warnings are non-blocking issues that indicate potential problems or improvements.
    They don't prevent execution but suggest better practices (e.g., deprecated aliases,
    performance concerns, style violations).

    Attributes:
        line: Line number where warning occurred (1-indexed)
        column: Column number where warning occurred (0-indexed)
        field_name: Field name that triggered warning
        warning_type: Type of warning ('deprecated_alias', 'performance', 'style', etc.)
        message: Human-readable warning message
        suggestion: Optional suggestion for improvement

    Example:
        >>> warning = FieldWarning(
        ...     line=5, column=10, field_name='turnover',
        ...     warning_type='deprecated_alias',
        ...     message='Alias "turnover" is deprecated',
        ...     suggestion='Use "price:成交金額" instead'
        ... )
        >>> print(warning)
        Line 5:10 - deprecated_alias: Alias "turnover" is deprecated (Use "price:成交金額" instead)
    """
    line: int
    column: int
    field_name: str
    warning_type: str
    message: str
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """Format warning as string for display.

        Returns:
            Formatted string: "Line {line}:{column} - {warning_type}: {message} ({suggestion})"
        """
        base = f"Line {self.line}:{self.column} - {self.warning_type}: {self.message}"
        if self.suggestion:
            base += f" ({self.suggestion})"
        return base


@dataclass
class ValidationResult:
    """
    Container for validation results with errors and warnings.

    Aggregates all validation issues found during code analysis. Provides a clean
    interface for checking validity (no errors) and accessing errors/warnings.

    Attributes:
        errors: List of FieldError objects (blocking issues)
        warnings: List of FieldWarning objects (non-blocking issues)
        metadata: Optional ValidationMetadata tracking multi-layer validation (Task 7.1)
        is_valid: True if no errors exist (computed property, warnings don't affect validity)

    Example:
        >>> result = ValidationResult()
        >>> result.add_error(
        ...     line=10, column=15, field_name='bad',
        ...     error_type='invalid', message='Invalid field'
        ... )
        >>> result.add_warning(
        ...     line=5, column=10, field_name='old',
        ...     warning_type='deprecated', message='Deprecated alias'
        ... )
        >>> print(result.is_valid)  # False (has errors)
        >>> print(len(result.errors))  # 1
        >>> print(len(result.warnings))  # 1
    """
    errors: List[FieldError] = field(default_factory=list)
    warnings: List[FieldWarning] = field(default_factory=list)
    metadata: Optional[ValidationMetadata] = None

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors).

        Warnings do not affect validity - only errors cause validation to fail.

        Returns:
            True if no errors exist, False otherwise
        """
        return len(self.errors) == 0

    def add_error(
        self,
        line: int,
        column: int,
        field_name: str,
        error_type: str,
        message: str,
        suggestion: Optional[str] = None
    ) -> None:
        """Add an error to the validation result.

        Args:
            line: Line number where error occurred (1-indexed)
            column: Column number where error occurred (0-indexed)
            field_name: Invalid field name that caused the error
            error_type: Type of error (e.g., 'invalid_field', 'syntax_error')
            message: Human-readable error message
            suggestion: Optional suggestion for correction

        Example:
            >>> result = ValidationResult()
            >>> result.add_error(
            ...     line=10, column=15, field_name='xyz',
            ...     error_type='invalid', message='Bad field',
            ...     suggestion='Did you mean "abc"?'
            ... )
        """
        error = FieldError(
            line=line, column=column, field_name=field_name,
            error_type=error_type, message=message, suggestion=suggestion
        )
        self.errors.append(error)

    def add_warning(
        self,
        line: int,
        column: int,
        field_name: str,
        warning_type: str,
        message: str,
        suggestion: Optional[str] = None
    ) -> None:
        """Add a warning to the validation result.

        Args:
            line: Line number where warning occurred (1-indexed)
            column: Column number where warning occurred (0-indexed)
            field_name: Field name that triggered warning
            warning_type: Type of warning (e.g., 'deprecated_alias', 'performance')
            message: Human-readable warning message
            suggestion: Optional suggestion for improvement

        Example:
            >>> result = ValidationResult()
            >>> result.add_warning(
            ...     line=5, column=10, field_name='old',
            ...     warning_type='deprecated', message='Old alias',
            ...     suggestion='Use new alias instead'
            ... )
        """
        warning = FieldWarning(
            line=line, column=column, field_name=field_name,
            warning_type=warning_type, message=message, suggestion=suggestion
        )
        self.warnings.append(warning)

    def __str__(self) -> str:
        """Format validation result as string for display.

        Returns:
            Multi-line string with errors, warnings, or success message

        Example output:
            Errors (2):
              - Line 10:15 - invalid_field: Invalid field (suggestion)
              - Line 20:25 - syntax_error: Syntax error
            Warnings (1):
              - Line 5:10 - deprecated: Deprecated alias (suggestion)
        """
        lines = []
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  - {error}")
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        if not self.errors and not self.warnings:
            lines.append("✅ Validation passed")
        return "\n".join(lines)
