"""
Validation Failure Logging and Reporting Framework
===================================================

Comprehensive logging and reporting system for strategy template validation failures.
Tracks validation history, generates human-readable reports, and provides statistics.

Features:
    - Validation failure logging with timestamp and iteration tracking
    - Human-readable report generation with error summary and fix suggestions
    - Statistics tracking (total validations, pass rate by template)
    - Code snippet extraction with line numbers for error context
    - Integration with FixSuggestor for automated fix recommendations
    - JSON and text report formats

Usage:
    from src.validation import ValidationLogger, ValidationResult

    logger = ValidationLogger(log_dir='logs/validation')

    # Log validation failure
    logger.log_failure(
        result=validation_result,
        iteration=5,
        template_name='TurtleTemplate',
        generated_code=code_string
    )

    # Generate human-readable report
    report = logger.generate_report(
        result=validation_result,
        template_name='TurtleTemplate',
        generated_code=code_string
    )
    print(report)

    # Get statistics
    stats = logger.get_statistics()
    print(f"Pass rate: {stats['overall_pass_rate']:.1%}")

Requirements:
    - Requirement 3.5: Validation failure logging and reporting
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import json
import logging
import re

from .template_validator import ValidationResult, ValidationError, Severity, Category
from .fix_suggestor import FixSuggestor


@dataclass
class ValidationLog:
    """
    Single validation log entry.

    Attributes:
        timestamp: ISO format timestamp of validation
        iteration: Iteration number (for iterative generation)
        template_name: Template type being validated
        status: Validation status (PASS/NEEDS_FIX/FAIL)
        errors: List of validation errors
        warnings: List of validation warnings
        suggestions: List of improvement suggestions
        metadata: Additional validation metadata
    """
    timestamp: str
    iteration: int
    template_name: str
    status: str
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_validation_result(
        cls,
        result: ValidationResult,
        iteration: int,
        template_name: str
    ) -> 'ValidationLog':
        """
        Create ValidationLog from ValidationResult.

        Args:
            result: ValidationResult object
            iteration: Iteration number
            template_name: Template name

        Returns:
            ValidationLog instance
        """
        return cls(
            timestamp=datetime.now().isoformat(),
            iteration=iteration,
            template_name=template_name,
            status=result.status,
            errors=[
                {
                    'category': error.category.value,
                    'error_type': error.error_type,
                    'severity': error.severity.value,
                    'message': error.message,
                    'location': error.location
                }
                for error in result.errors
            ],
            warnings=[
                {
                    'category': warning.category.value,
                    'error_type': warning.error_type,
                    'severity': warning.severity.value,
                    'message': warning.message,
                    'location': warning.location
                }
                for warning in result.warnings
            ],
            suggestions=result.suggestions,
            metadata=result.metadata
        )


class ValidationLogger:
    """
    Validation failure logging and reporting system.

    Provides comprehensive logging of validation failures with human-readable
    reports, statistics tracking, and integration with fix suggestion system.

    Features:
        - JSON log file for machine-readable validation history
        - Text report generation with error summaries and fix suggestions
        - Code snippet extraction with line numbers for error context
        - Statistics tracking by template type and overall
        - Configurable log rotation and retention

    Attributes:
        log_dir: Directory for validation logs
        log_file: Path to JSON log file
        fix_suggestor: FixSuggestor instance for fix recommendations
        logger: Python logger for internal logging

    Example:
        >>> logger = ValidationLogger(log_dir='logs/validation')
        >>> logger.log_failure(result, iteration=5, template_name='TurtleTemplate')
        >>> report = logger.generate_report(result, 'TurtleTemplate', code_string)
        >>> print(report)
    """

    # Default log file name
    DEFAULT_LOG_FILE = 'validation_failures.jsonl'

    # Code snippet context lines (before and after error)
    CONTEXT_LINES = 3

    def __init__(
        self,
        log_dir: str = 'logs/validation',
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize validation logger.

        Args:
            log_dir: Directory for validation logs (created if not exists)
            logger: Optional logger for internal logging
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.log_dir / self.DEFAULT_LOG_FILE
        self.fix_suggestor = FixSuggestor()
        self.logger = logger or logging.getLogger(__name__)

        self.logger.info(f"ValidationLogger initialized with log_dir: {self.log_dir}")

    def log_failure(
        self,
        result: ValidationResult,
        iteration: int,
        template_name: str,
        generated_code: Optional[str] = None
    ) -> None:
        """
        Log validation failure to JSON log file.

        Appends validation failure to JSONL log file with timestamp,
        iteration, template type, and all validation errors/warnings.

        Args:
            result: ValidationResult object
            iteration: Iteration number (for iterative generation)
            template_name: Template type being validated
            generated_code: Optional generated code for context

        Example:
            >>> logger.log_failure(
            ...     result=validation_result,
            ...     iteration=5,
            ...     template_name='TurtleTemplate',
            ...     generated_code=code_string
            ... )
        """
        # Create log entry
        log_entry = ValidationLog.from_validation_result(
            result=result,
            iteration=iteration,
            template_name=template_name
        )

        # Add code statistics if provided
        if generated_code:
            log_entry.metadata['code_stats'] = {
                'lines': len(generated_code.splitlines()),
                'chars': len(generated_code)
            }

        # Write to JSONL log file (append mode)
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry.to_dict(), ensure_ascii=False) + '\n')

            self.logger.info(
                f"Logged validation failure: iteration={iteration}, "
                f"template={template_name}, status={result.status}, "
                f"errors={len(result.errors)}"
            )
        except Exception as e:
            self.logger.error(f"Failed to write validation log: {e}")

    def generate_report(
        self,
        result: ValidationResult,
        template_name: str,
        generated_code: Optional[str] = None,
        include_code_snippets: bool = True,
        include_fix_suggestions: bool = True
    ) -> str:
        """
        Generate human-readable validation report.

        Creates comprehensive text report with:
        - Error summary with severity counts
        - Detailed error descriptions with locations
        - Code snippets with line numbers (if code provided)
        - Fix suggestions from FixSuggestor (if enabled)
        - Validation statistics

        Args:
            result: ValidationResult object
            template_name: Template name for context
            generated_code: Optional code for snippet extraction
            include_code_snippets: Include code context around errors
            include_fix_suggestions: Include automated fix suggestions

        Returns:
            Formatted validation report string

        Example:
            >>> report = logger.generate_report(
            ...     result=validation_result,
            ...     template_name='TurtleTemplate',
            ...     generated_code=code_string
            ... )
            >>> print(report)
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Template: {template_name}")
        lines.append(f"Status: {result.status}")
        lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Error summary
        critical_errors = [e for e in result.errors if e.severity == Severity.CRITICAL]
        moderate_errors = [e for e in result.errors if e.severity == Severity.MODERATE]
        low_errors = [e for e in result.errors if e.severity == Severity.LOW]

        lines.append("ERROR SUMMARY:")
        lines.append(f"  🚨 Critical Errors: {len(critical_errors)}")
        lines.append(f"  ⚠️  Moderate Errors: {len(moderate_errors)}")
        lines.append(f"  ℹ️  Low Severity: {len(low_errors)}")
        lines.append(f"  ⚡ Warnings: {len(result.warnings)}")
        lines.append(f"  💡 Suggestions: {len(result.suggestions)}")
        lines.append("")

        # Critical errors (most important)
        if critical_errors:
            lines.append("🚨 CRITICAL ERRORS (Require Immediate Fix):")
            lines.append("=" * 80)
            for i, error in enumerate(critical_errors, 1):
                lines.extend(self._format_error(
                    error=error,
                    index=i,
                    generated_code=generated_code if include_code_snippets else None
                ))

                # Add fix suggestion
                if include_fix_suggestions:
                    fix = self.fix_suggestor.generate_fix_suggestion(error, template_name)
                    if fix:
                        lines.append("  💊 FIX SUGGESTION:")
                        for fix_line in fix.splitlines():
                            lines.append(f"     {fix_line}")
                        lines.append("")
            lines.append("")

        # Moderate errors
        if moderate_errors:
            lines.append("⚠️  MODERATE ERRORS (Should Be Fixed):")
            lines.append("=" * 80)
            for i, error in enumerate(moderate_errors, 1):
                lines.extend(self._format_error(
                    error=error,
                    index=i,
                    generated_code=generated_code if include_code_snippets else None
                ))

                # Add fix suggestion
                if include_fix_suggestions:
                    fix = self.fix_suggestor.generate_fix_suggestion(error, template_name)
                    if fix:
                        lines.append("  💊 FIX SUGGESTION:")
                        for fix_line in fix.splitlines():
                            lines.append(f"     {fix_line}")
                        lines.append("")
            lines.append("")

        # Low severity errors
        if low_errors:
            lines.append("ℹ️  LOW SEVERITY ISSUES (Optional Improvements):")
            lines.append("=" * 80)
            for i, error in enumerate(low_errors, 1):
                lines.extend(self._format_error(
                    error=error,
                    index=i,
                    generated_code=generated_code if include_code_snippets else None
                ))
            lines.append("")

        # Warnings
        if result.warnings:
            lines.append("⚡ WARNINGS:")
            lines.append("=" * 80)
            for i, warning in enumerate(result.warnings, 1):
                lines.extend(self._format_error(
                    error=warning,
                    index=i,
                    generated_code=generated_code if include_code_snippets else None
                ))
            lines.append("")

        # Suggestions
        if result.suggestions:
            lines.append("💡 SUGGESTIONS FOR IMPROVEMENT:")
            lines.append("=" * 80)
            for i, suggestion in enumerate(result.suggestions, 1):
                lines.append(f"{i}. {suggestion}")
            lines.append("")

        # Metadata
        if result.metadata:
            lines.append("VALIDATION METADATA:")
            lines.append("=" * 80)
            for key, value in result.metadata.items():
                if isinstance(value, dict):
                    lines.append(f"{key}:")
                    for sub_key, sub_value in value.items():
                        lines.append(f"  {sub_key}: {sub_value}")
                else:
                    lines.append(f"{key}: {value}")
            lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append("END OF VALIDATION REPORT")
        lines.append("=" * 80)

        return '\n'.join(lines)

    def _format_error(
        self,
        error: ValidationError,
        index: int,
        generated_code: Optional[str] = None
    ) -> List[str]:
        """
        Format single error with optional code snippet.

        Args:
            error: ValidationError object
            index: Error index number
            generated_code: Optional code for snippet extraction

        Returns:
            List of formatted lines
        """
        lines = []

        # Error header
        lines.append(f"{index}. [{error.category.value.upper()}] {error.error_type}")
        lines.append(f"   Severity: {error.severity.value.upper()}")
        lines.append(f"   Message: {error.message}")

        if error.location:
            lines.append(f"   Location: {error.location}")

            # Extract code snippet if code provided
            if generated_code:
                snippet = self._extract_code_snippet(generated_code, error.location)
                if snippet:
                    lines.append("   Code Context:")
                    for snippet_line in snippet:
                        lines.append(f"     {snippet_line}")

        lines.append("")
        return lines

    def _extract_code_snippet(
        self,
        code: str,
        location: str
    ) -> Optional[List[str]]:
        """
        Extract code snippet around error location.

        Extracts CONTEXT_LINES before and after the error line,
        with line numbers for reference.

        Args:
            code: Full generated code
            location: Error location (e.g., "line 45" or "line 45-50")

        Returns:
            List of formatted code lines with line numbers, or None if extraction fails

        Example:
            >>> snippet = logger._extract_code_snippet(code, "line 45")
            >>> print('\\n'.join(snippet))
            42:     def calculate():
            43:         # Some code
            44:         x = data.get('price:收盤價')
            45: >>> y = data.get('price:收盤價')  # DUPLICATE CALL
            46:         return x + y
            47:
            48:     result = calculate()
        """
        # Parse location (e.g., "line 45" or "line 45-50")
        match = re.search(r'line[s]?\s+(\d+)(?:-(\d+))?', location, re.IGNORECASE)
        if not match:
            return None

        start_line = int(match.group(1))
        end_line = int(match.group(2)) if match.group(2) else start_line

        # Split code into lines
        code_lines = code.splitlines()
        total_lines = len(code_lines)

        # Calculate snippet range (with context)
        snippet_start = max(0, start_line - self.CONTEXT_LINES - 1)  # -1 for 0-based index
        snippet_end = min(total_lines, end_line + self.CONTEXT_LINES)

        # Extract snippet with line numbers
        snippet_lines = []
        for i in range(snippet_start, snippet_end):
            line_num = i + 1  # 1-based line number
            line_content = code_lines[i]

            # Mark error lines with ">>>"
            if start_line <= line_num <= end_line:
                snippet_lines.append(f"{line_num:4d}: >>> {line_content}")
            else:
                snippet_lines.append(f"{line_num:4d}:     {line_content}")

        return snippet_lines if snippet_lines else None

    def get_statistics(
        self,
        template_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get validation statistics from log file.

        Calculates statistics including:
        - Total validations
        - Pass rate (overall and by template)
        - Average errors per validation
        - Most common error types
        - Validation trend over time

        Args:
            template_filter: Optional template name to filter statistics

        Returns:
            Dictionary with validation statistics

        Example:
            >>> stats = logger.get_statistics()
            >>> print(f"Overall pass rate: {stats['overall_pass_rate']:.1%}")
            Overall pass rate: 65.2%

            >>> turtle_stats = logger.get_statistics(template_filter='TurtleTemplate')
            >>> print(f"Turtle pass rate: {turtle_stats['pass_rate']:.1%}")
            Turtle pass rate: 72.3%
        """
        if not self.log_file.exists():
            return {
                'total_validations': 0,
                'overall_pass_rate': 0.0,
                'message': 'No validation logs found'
            }

        # Read all log entries
        logs = []
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        except Exception as e:
            self.logger.error(f"Failed to read validation logs: {e}")
            return {'error': str(e)}

        # Filter by template if specified
        if template_filter:
            logs = [log for log in logs if log['template_name'] == template_filter]

        if not logs:
            return {
                'total_validations': 0,
                'overall_pass_rate': 0.0,
                'message': f'No logs found for template: {template_filter}' if template_filter else 'No logs found'
            }

        # Calculate statistics
        total_validations = len(logs)
        passed = sum(1 for log in logs if log['status'] == 'PASS')
        failed = sum(1 for log in logs if log['status'] == 'FAIL')
        needs_fix = sum(1 for log in logs if log['status'] == 'NEEDS_FIX')

        # Overall statistics
        stats = {
            'total_validations': total_validations,
            'passed': passed,
            'failed': failed,
            'needs_fix': needs_fix,
            'overall_pass_rate': passed / total_validations if total_validations > 0 else 0.0,
            'fail_rate': failed / total_validations if total_validations > 0 else 0.0,
        }

        # Statistics by template (if not filtered)
        if not template_filter:
            template_stats = {}
            for log in logs:
                template = log['template_name']
                if template not in template_stats:
                    template_stats[template] = {
                        'total': 0,
                        'passed': 0,
                        'failed': 0,
                        'needs_fix': 0
                    }
                template_stats[template]['total'] += 1
                if log['status'] == 'PASS':
                    template_stats[template]['passed'] += 1
                elif log['status'] == 'FAIL':
                    template_stats[template]['failed'] += 1
                else:
                    template_stats[template]['needs_fix'] += 1

            # Calculate pass rate for each template
            for template, t_stats in template_stats.items():
                t_stats['pass_rate'] = t_stats['passed'] / t_stats['total'] if t_stats['total'] > 0 else 0.0

            stats['by_template'] = template_stats

        # Error type statistics
        error_types = {}
        for log in logs:
            for error in log['errors']:
                error_type = error['error_type']
                if error_type not in error_types:
                    error_types[error_type] = 0
                error_types[error_type] += 1

        # Sort by frequency
        stats['most_common_errors'] = sorted(
            error_types.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  # Top 10 most common errors

        # Average errors per validation
        total_errors = sum(len(log['errors']) for log in logs)
        stats['avg_errors_per_validation'] = total_errors / total_validations if total_validations > 0 else 0.0

        return stats

    def clear_logs(self, confirm: bool = False) -> None:
        """
        Clear all validation logs.

        WARNING: This permanently deletes all validation history.

        Args:
            confirm: Must be True to actually clear logs (safety check)
        """
        if not confirm:
            self.logger.warning("clear_logs() called without confirmation - no action taken")
            return

        if self.log_file.exists():
            try:
                self.log_file.unlink()
                self.logger.info("Validation logs cleared")
            except Exception as e:
                self.logger.error(f"Failed to clear logs: {e}")
