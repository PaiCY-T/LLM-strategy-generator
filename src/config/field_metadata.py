"""
Field Metadata Data Structure

Defines the FieldMetadata dataclass for finlab API field information.
This module provides the core data structure for Layer 1: Enhanced Data Field Manifest.

Usage:
    from src.config.field_metadata import FieldMetadata

    field = FieldMetadata(
        canonical_name='price:收盤價',
        category='price',
        frequency='daily',
        dtype='float',
        description_zh='每日收盤價格',
        description_en='Daily closing price',
        aliases=['close', '收盤價', 'closing_price'],
        valid_range=(0.0, 10000.0)
    )
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple


@dataclass
class FieldMetadata:
    """
    Metadata for a finlab API field.

    This dataclass encapsulates all information needed for Layer 1 field validation:
    - Canonical field naming (e.g., 'price:收盤價')
    - Alias resolution (e.g., 'close' → 'price:收盤價')
    - Field categorization and frequency
    - Data type validation
    - Bilingual descriptions
    - Valid ranges for numeric fields

    Attributes:
        canonical_name: Canonical finlab API field name (e.g., 'price:收盤價', 'fundamental_features:ROE')
        category: Field category for classification
            - 'price': Price-related fields (OHLCV data)
            - 'fundamental': Fundamental analysis fields (financial ratios, metrics)
            - 'technical': Technical indicator fields (derived calculations)
        frequency: Data frequency/update interval
            - 'daily': Updated every trading day
            - 'weekly': Weekly data
            - 'monthly': Monthly data
            - 'quarterly': Quarterly financial data
            - 'annual': Annual financial data
        dtype: Python data type for validation
            - 'float': Floating-point numbers (prices, ratios)
            - 'int': Integers (counts, volumes)
            - 'str': String values (categorical data)
            - 'datetime': Date/time values
        description_zh: Chinese description for human readability
        description_en: English description for human readability
        aliases: List of common aliases that map to this canonical name
            Examples:
            - 'close' → 'price:收盤價'
            - 'volume' → 'price:成交金額' (⚠️ Common mistake: volume ≠ shares)
            - 'ROE' → 'fundamental_features:ROE'
        example_values: Optional list of example values for documentation/testing
        valid_range: Optional (min, max) tuple for numeric validation
            - Price fields: (0.0, 10000.0) TWD
            - Ratio fields: (-100.0, 200.0) percentage
            - Volume fields: (0.0, 1e12) large numbers

    Example:
        >>> # Create metadata for closing price field
        >>> close_field = FieldMetadata(
        ...     canonical_name='price:收盤價',
        ...     category='price',
        ...     frequency='daily',
        ...     dtype='float',
        ...     description_zh='每日收盤價格',
        ...     description_en='Daily closing price',
        ...     aliases=['close', '收盤價', 'closing_price', 'close_price'],
        ...     valid_range=(0.0, 10000.0)
        ... )
        >>>
        >>> # Verify aliases
        >>> assert 'close' in close_field.aliases
        >>> assert close_field.category == 'price'
        >>>
        >>> # Check valid range
        >>> assert close_field.valid_range == (0.0, 10000.0)

    See Also:
        - scripts/discover_finlab_fields.py: Field discovery script using this dataclass
        - src/config/data_fields.py: DataFieldManifest using this dataclass (Layer 1)
        - src/validation/field_validator.py: Field validation using this dataclass (Layer 2)
    """

    # Required fields
    canonical_name: str
    category: str
    frequency: str
    dtype: str
    description_zh: str
    description_en: str
    aliases: List[str]

    # Optional fields with defaults
    example_values: Optional[List[Any]] = None
    valid_range: Optional[Tuple[float, float]] = None

    def __post_init__(self):
        """
        Validate FieldMetadata after initialization.

        Raises:
            ValueError: If any required field is empty or invalid
        """
        # Validate canonical name
        if not self.canonical_name or not isinstance(self.canonical_name, str):
            raise ValueError(f"canonical_name must be a non-empty string, got: {self.canonical_name}")

        # Validate category
        valid_categories = {'price', 'fundamental', 'technical'}
        if self.category not in valid_categories:
            raise ValueError(f"category must be one of {valid_categories}, got: {self.category}")

        # Validate frequency
        valid_frequencies = {'daily', 'weekly', 'monthly', 'quarterly', 'annual'}
        if self.frequency not in valid_frequencies:
            raise ValueError(f"frequency must be one of {valid_frequencies}, got: {self.frequency}")

        # Validate dtype
        valid_dtypes = {'float', 'int', 'str', 'datetime'}
        if self.dtype not in valid_dtypes:
            raise ValueError(f"dtype must be one of {valid_dtypes}, got: {self.dtype}")

        # Validate descriptions
        if not self.description_zh or not isinstance(self.description_zh, str):
            raise ValueError(f"description_zh must be a non-empty string")

        if not self.description_en or not isinstance(self.description_en, str):
            raise ValueError(f"description_en must be a non-empty string")

        # Validate aliases
        if not self.aliases or not isinstance(self.aliases, list):
            raise ValueError(f"aliases must be a non-empty list")

        if not all(isinstance(alias, str) for alias in self.aliases):
            raise ValueError(f"all aliases must be strings")

        # Validate valid_range if provided
        if self.valid_range is not None:
            if not isinstance(self.valid_range, tuple) or len(self.valid_range) != 2:
                raise ValueError(f"valid_range must be a tuple of (min, max), got: {self.valid_range}")

            min_val, max_val = self.valid_range
            if not isinstance(min_val, (int, float)) or not isinstance(max_val, (int, float)):
                raise ValueError(f"valid_range values must be numeric, got: {self.valid_range}")

            if min_val >= max_val:
                raise ValueError(f"valid_range min must be less than max, got: {self.valid_range}")

    def is_alias(self, name: str) -> bool:
        """
        Check if a given name is an alias for this field.

        Args:
            name: Name to check (e.g., 'close', 'volume', 'ROE')

        Returns:
            True if name is an alias for this field, False otherwise

        Example:
            >>> field = FieldMetadata(
            ...     canonical_name='price:收盤價',
            ...     category='price',
            ...     frequency='daily',
            ...     dtype='float',
            ...     description_zh='每日收盤價格',
            ...     description_en='Daily closing price',
            ...     aliases=['close', '收盤價', 'closing_price']
            ... )
            >>> field.is_alias('close')
            True
            >>> field.is_alias('volume')
            False
        """
        return name in self.aliases

    def matches_canonical_or_alias(self, name: str) -> bool:
        """
        Check if a given name matches canonical name or any alias.

        Args:
            name: Name to check

        Returns:
            True if name matches canonical name or any alias

        Example:
            >>> field = FieldMetadata(
            ...     canonical_name='price:收盤價',
            ...     category='price',
            ...     frequency='daily',
            ...     dtype='float',
            ...     description_zh='每日收盤價格',
            ...     description_en='Daily closing price',
            ...     aliases=['close', '收盤價']
            ... )
            >>> field.matches_canonical_or_alias('price:收盤價')
            True
            >>> field.matches_canonical_or_alias('close')
            True
            >>> field.matches_canonical_or_alias('invalid_field')
            False
        """
        return name == self.canonical_name or self.is_alias(name)

    def validate_value(self, value: Any) -> bool:
        """
        Validate if a value is within valid_range (if specified).

        Args:
            value: Value to validate

        Returns:
            True if value is valid (within range or no range specified)

        Example:
            >>> field = FieldMetadata(
            ...     canonical_name='price:收盤價',
            ...     category='price',
            ...     frequency='daily',
            ...     dtype='float',
            ...     description_zh='每日收盤價格',
            ...     description_en='Daily closing price',
            ...     aliases=['close'],
            ...     valid_range=(0.0, 10000.0)
            ... )
            >>> field.validate_value(100.0)
            True
            >>> field.validate_value(-10.0)
            False
            >>> field.validate_value(15000.0)
            False
        """
        if self.valid_range is None:
            return True

        min_val, max_val = self.valid_range
        try:
            numeric_value = float(value)
            return min_val <= numeric_value <= max_val
        except (ValueError, TypeError):
            return False


# Module-level constants for common field categories
CATEGORY_PRICE = 'price'
CATEGORY_FUNDAMENTAL = 'fundamental'
CATEGORY_TECHNICAL = 'technical'

# Module-level constants for common frequencies
FREQUENCY_DAILY = 'daily'
FREQUENCY_WEEKLY = 'weekly'
FREQUENCY_MONTHLY = 'monthly'
FREQUENCY_QUARTERLY = 'quarterly'
FREQUENCY_ANNUAL = 'annual'

# Module-level constants for common dtypes
DTYPE_FLOAT = 'float'
DTYPE_INT = 'int'
DTYPE_STR = 'str'
DTYPE_DATETIME = 'datetime'
