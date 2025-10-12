"""
Data Access Validator for Strategy Templates
============================================

Validates data.get() calls in generated strategy code with dataset existence checking,
caching pattern analysis, and performance optimization suggestions.

Validation Types:
    - Dataset Key Validation: Verify dataset keys exist in Finlab
    - Caching Usage: Check for efficient data access patterns
    - Performance Analysis: Detect excessive data.get() calls
    - Data Access Patterns: Identify anti-patterns and inefficiencies

Usage:
    from src.validation import DataValidator

    validator = DataValidator()
    validator.validate_data_access(generated_code)

    result = validator.get_result()
    if not result.is_valid():
        print(result)
"""

import re
from typing import Dict, Any, List, Tuple, Set
from .template_validator import (
    TemplateValidator,
    ValidationResult,
    ValidationError,
    Category,
    Severity
)


# Known Finlab datasets registry
# Source: Combined from DataCache.COMMON_DATASETS and NoveltyScorer dataset registry
KNOWN_DATASETS = {
    # Price data (OHLCV)
    'price:收盤價',           # Close price
    'price:開盤價',           # Open price
    'price:最高價',           # High price
    'price:最低價',           # Low price
    'price:成交股數',         # Volume
    'price:成交金額',         # Trading value

    # Revenue data
    'monthly_revenue:當月營收',          # Monthly revenue
    'monthly_revenue:去年同期營收',      # Last year same month revenue
    'monthly_revenue:上月營收',          # Last month revenue
    'monthly_revenue:去年當月營收',      # Last year current month revenue
    'monthly_revenue:去年同月增減(%)',   # YoY revenue growth

    # Fundamental features
    'fundamental_features:本益比',       # P/E ratio
    'fundamental_features:股價淨值比',   # P/B ratio
    'fundamental_features:殖利率',       # Dividend yield
    'fundamental_features:市值',         # Market cap
    'fundamental_features:營業利益率',   # Operating margin

    # Financial ratios
    'price_earning_ratio:本益比',        # P/E ratio (alternative)
    'price_earning_ratio:殖利率(%)',     # Dividend yield (%)

    # ETL financial data
    'etl:股東權益報酬率',               # ROE
    'etl:總資產報酬率',                 # ROA
    'etl:營業毛利率',                   # Gross margin

    # Insider trading
    'tejdata_shareholding_director:持股增減',           # Director shareholding changes
    'internal_equity_changes:董監持有股數占比',         # Director shareholding ratio
}


# Performance thresholds for data.get() call frequency
MAX_DATA_CALLS_OPTIMAL = 5      # Optimal: ≤5 data.get() calls
MAX_DATA_CALLS_ACCEPTABLE = 10  # Acceptable: ≤10 data.get() calls
MAX_DATA_CALLS_CRITICAL = 20    # Critical: >20 data.get() calls


class DataValidator(TemplateValidator):
    """
    Validate data access patterns in generated strategy code.

    Validation Layers:
        1. Dataset key existence: Verify all data.get() keys are valid
        2. Caching patterns: Check for efficient data access
        3. Performance analysis: Detect excessive data loading
        4. Anti-pattern detection: Identify inefficient patterns

    Features:
        - Regex-based data.get() call extraction
        - Known dataset registry validation
        - Performance optimization suggestions
        - Caching pattern analysis

    Example:
        >>> validator = DataValidator()
        >>> code = "close = data.get('price:收盤價')\\nvolume = data.get('price:成交股數')"
        >>> validator.validate_data_access(code)
        >>> result = validator.get_result()
        >>> print(f"Valid: {result.is_valid()}")
    """

    def __init__(self):
        """Initialize data validator with dataset registry and regex patterns."""
        super().__init__()

        # Use known datasets registry
        self.known_datasets = KNOWN_DATASETS

        # Pre-compile regex pattern for performance (same as NoveltyScorer)
        self._dataset_pattern = re.compile(r"data\.get\(['\"]([^'\"]+)['\"]\)")

        # Track extracted data calls for analysis
        self.data_calls: List[Tuple[str, int]] = []  # (dataset_key, line_number)

    def _extract_data_calls(self, code: str) -> List[Tuple[str, int]]:
        """
        Extract all data.get() calls from strategy code with line numbers.

        Uses regex pattern matching to find all data.get('key') calls and
        track their line numbers for error reporting.

        Args:
            code: Generated strategy Python code

        Returns:
            List of (dataset_key, line_number) tuples

        Example:
            >>> code = '''
            ... close = data.get('price:收盤價')
            ... volume = data.get('price:成交股數')
            ... '''
            >>> calls = validator._extract_data_calls(code)
            >>> len(calls)
            2
            >>> calls[0]
            ('price:收盤價', 2)
        """
        data_calls = []
        lines = code.split('\n')

        for line_num, line in enumerate(lines, start=1):
            # Find all data.get() calls in this line
            matches = self._dataset_pattern.findall(line)

            for dataset_key in matches:
                data_calls.append((dataset_key, line_num))

        return data_calls

    def _validate_dataset_key(
        self,
        dataset_key: str,
        line_number: int
    ) -> bool:
        """
        Validate that dataset key exists in known datasets.

        Checks if the dataset key is present in KNOWN_DATASETS registry.
        If not found, adds CRITICAL error suggesting valid alternatives.

        Args:
            dataset_key: Dataset key from data.get() call
            line_number: Line number where data.get() appears

        Returns:
            True if dataset exists, False otherwise (adds error)

        Example:
            >>> validator._validate_dataset_key('price:收盤價', 10)
            True  # Known dataset
            >>> validator._validate_dataset_key('price:unknown', 15)
            False  # Unknown dataset (adds error)
        """
        if dataset_key not in self.known_datasets:
            # Try to suggest similar dataset keys
            suggestions = self._suggest_similar_datasets(dataset_key)
            suggestion_text = f"Did you mean: {', '.join(suggestions)}" if suggestions else "Check Finlab documentation for valid dataset keys"

            self._add_error(
                category=Category.DATA,
                error_type='invalid_dataset',
                message=f"Unknown dataset key: '{dataset_key}'",
                line_number=line_number,
                suggestion=suggestion_text,
                context={
                    'dataset_key': dataset_key,
                    'line_number': line_number,
                    'similar_datasets': suggestions
                }
            )
            return False

        return True

    def _suggest_similar_datasets(self, dataset_key: str, max_suggestions: int = 3) -> List[str]:
        """
        Suggest similar dataset keys using simple string matching.

        Uses substring matching to find datasets with similar prefixes
        (e.g., 'price:' prefix for price-related datasets).

        Args:
            dataset_key: Unknown dataset key
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of similar dataset keys

        Example:
            >>> validator._suggest_similar_datasets('price:unknown')
            ['price:收盤價', 'price:開盤價', 'price:最高價']
        """
        # Extract prefix (e.g., 'price:', 'monthly_revenue:')
        if ':' in dataset_key:
            prefix = dataset_key.split(':')[0] + ':'

            # Find all datasets with same prefix
            similar = [
                ds for ds in self.known_datasets
                if ds.startswith(prefix)
            ]

            return sorted(similar)[:max_suggestions]

        # No prefix - return most common datasets
        return sorted(list(self.known_datasets))[:max_suggestions]

    def _check_caching_usage(self, code: str, data_calls: List[Tuple[str, int]]) -> None:
        """
        Check for efficient caching patterns in data access.

        Analyzes code to detect:
            - Duplicate data.get() calls (should be cached in variable)
            - Missing DataCache usage (should use get_cached_data)
            - Inefficient repeated data loading

        Args:
            code: Generated strategy code
            data_calls: List of (dataset_key, line_number) extracted data calls

        Example:
            >>> code = '''
            ... close1 = data.get('price:收盤價')
            ... close2 = data.get('price:收盤價')  # Duplicate!
            ... '''
            >>> validator._check_caching_usage(code, data_calls)
            # Adds warning about duplicate data.get() call
        """
        # Check for duplicate data.get() calls
        dataset_counts = {}
        for dataset_key, line_number in data_calls:
            if dataset_key not in dataset_counts:
                dataset_counts[dataset_key] = []
            dataset_counts[dataset_key].append(line_number)

        for dataset_key, line_numbers in dataset_counts.items():
            if len(line_numbers) > 1:
                self._add_error(
                    category=Category.DATA,
                    error_type='performance_concern',
                    message=f"Duplicate data.get() call for '{dataset_key}' at lines {line_numbers}",
                    line_number=line_numbers[0],
                    suggestion=f"Store '{dataset_key}' in a variable and reuse it instead of loading multiple times",
                    context={
                        'dataset_key': dataset_key,
                        'duplicate_lines': line_numbers,
                        'duplicate_count': len(line_numbers)
                    }
                )

        # Check if DataCache is being used (performance optimization suggestion)
        if 'DataCache' not in code and 'get_cached_data' not in code:
            if len(data_calls) >= MAX_DATA_CALLS_OPTIMAL:
                self._add_suggestion(
                    f"Consider using DataCache for {len(data_calls)} data.get() calls to improve performance"
                )

    def _analyze_performance(self, data_calls: List[Tuple[str, int]]) -> None:
        """
        Analyze data access performance and suggest optimizations.

        Performance Rules:
            - Optimal: ≤5 data.get() calls (no warning)
            - Acceptable: 6-10 calls (LOW severity suggestion)
            - Concerning: 11-20 calls (MODERATE severity warning)
            - Critical: >20 calls (CRITICAL severity error)

        Args:
            data_calls: List of (dataset_key, line_number) extracted data calls

        Example:
            >>> data_calls = [('price:收盤價', 1), ('price:成交股數', 2), ...]
            >>> validator._analyze_performance(data_calls)
            # Adds warnings/errors based on call count
        """
        total_calls = len(data_calls)

        if total_calls == 0:
            # No data.get() calls - might be a problem
            self._add_error(
                category=Category.DATA,
                error_type='invalid_range',
                message="No data.get() calls found in strategy code",
                suggestion="Strategies should load at least one dataset (e.g., data.get('price:收盤價'))",
                context={'total_calls': 0}
            )
            return

        # Optimal range (≤5 calls)
        if total_calls <= MAX_DATA_CALLS_OPTIMAL:
            # Good performance - no warning
            return

        # Acceptable range (6-10 calls)
        if total_calls <= MAX_DATA_CALLS_ACCEPTABLE:
            self._add_error(
                category=Category.DATA,
                error_type='suboptimal_range',
                message=f"Strategy has {total_calls} data.get() calls (optimal: ≤{MAX_DATA_CALLS_OPTIMAL})",
                suggestion="Consider consolidating datasets or using fewer data sources for better performance",
                context={
                    'total_calls': total_calls,
                    'optimal_max': MAX_DATA_CALLS_OPTIMAL
                }
            )
            return

        # Concerning range (11-20 calls)
        if total_calls <= MAX_DATA_CALLS_CRITICAL:
            self._add_error(
                category=Category.DATA,
                error_type='performance_concern',
                message=f"Strategy has excessive data.get() calls: {total_calls} (acceptable: ≤{MAX_DATA_CALLS_ACCEPTABLE})",
                suggestion="Significantly reduce data.get() calls - use DataCache and consolidate datasets",
                context={
                    'total_calls': total_calls,
                    'acceptable_max': MAX_DATA_CALLS_ACCEPTABLE
                }
            )
            return

        # Critical range (>20 calls)
        self._add_error(
            category=Category.DATA,
            error_type='excessive_complexity',
            message=f"Strategy has critically excessive data.get() calls: {total_calls} (critical threshold: {MAX_DATA_CALLS_CRITICAL})",
            suggestion="Redesign strategy to use significantly fewer datasets - current approach will have severe performance issues",
            context={
                'total_calls': total_calls,
                'critical_threshold': MAX_DATA_CALLS_CRITICAL
            }
        )

    def validate_data_access(self, generated_code: str) -> None:
        """
        Validate all data access patterns in generated strategy code.

        Validation Workflow:
            1. Extract all data.get() calls with line numbers
            2. Validate each dataset key exists
            3. Check for caching anti-patterns
            4. Analyze performance implications
            5. Generate optimization suggestions

        Args:
            generated_code: Generated strategy Python code

        Example:
            >>> code = "close = data.get('price:收盤價')"
            >>> validator.validate_data_access(code)
            >>> result = validator.get_result()
            >>> if result.is_valid():
            ...     print("Data access validated successfully")
        """
        # 1. Extract all data.get() calls
        self.data_calls = self._extract_data_calls(generated_code)

        # 2. Validate each dataset key
        for dataset_key, line_number in self.data_calls:
            self._validate_dataset_key(dataset_key, line_number)

        # 3. Check caching usage patterns
        self._check_caching_usage(generated_code, self.data_calls)

        # 4. Analyze performance
        self._analyze_performance(self.data_calls)

        # 5. Add summary statistics to metadata
        unique_datasets = set(key for key, _ in self.data_calls)
        self.metadata = {
            'total_data_calls': len(self.data_calls),
            'unique_datasets': len(unique_datasets),
            'datasets_used': sorted(unique_datasets)
        }

    def get_result(self) -> ValidationResult:
        """
        Get validation result with all errors, warnings, and suggestions.

        Returns:
            ValidationResult with status determination and metadata

        Example:
            >>> validator.validate_data_access(code)
            >>> result = validator.get_result()
            >>> print(f"Total data.get() calls: {result.metadata['total_data_calls']}")
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

        # Build metadata
        metadata = {
            'validator': 'DataValidator',
            'total_data_calls': getattr(self, 'metadata', {}).get('total_data_calls', 0),
            'unique_datasets': getattr(self, 'metadata', {}).get('unique_datasets', 0),
            'datasets_used': getattr(self, 'metadata', {}).get('datasets_used', [])
        }

        return ValidationResult(
            status=status,
            errors=self.errors,
            warnings=self.warnings,
            suggestions=self.suggestions,
            metadata=metadata
        )
