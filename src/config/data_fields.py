"""
Layer 1: Enhanced Data Field Manifest with Alias Resolution and Auto-Correction

This module implements the DataFieldManifest class, which provides:
- O(1) alias resolution (e.g., 'close' → 'price:收盤價')
- O(1) canonical name lookup
- O(1) field existence validation
- Bidirectional mapping: alias ↔ canonical name
- Auto-correction for top 20 common LLM field mistakes

Architecture:
- Pre-computed _alias_map for O(1) alias → canonical resolution
- Pre-computed _fields_by_canonical for O(1) canonical → FieldMetadata lookup
- COMMON_CORRECTIONS dict for auto-correcting frequent LLM mistakes (29.4% error rate)
- Integration with FieldMetadata dataclass and JSON cache system

Usage:
    from src.config.data_fields import DataFieldManifest

    # Initialize manifest from cache
    manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')

    # Resolve alias to field
    field = manifest.get_field('close')
    assert field.canonical_name == 'price:收盤價'

    # Validate field existence
    assert manifest.validate_field('volume') is True

    # Validate with auto-correction suggestions
    is_valid, suggestion = manifest.validate_field_with_suggestion('price:成交量')
    assert is_valid is False
    assert "price:成交金額" in suggestion  # Auto-suggests correct field

    # Get all aliases for a field
    aliases = manifest.get_aliases('price:收盤價')
    assert 'close' in aliases

    # Get canonical name from alias
    canonical = manifest.get_canonical_name('close')
    assert canonical == 'price:收盤價'

Performance:
- All lookups use O(1) dict access
- Average lookup time <1ms (tested with 1000 iterations)
- Pre-computation at initialization for zero runtime overhead

See Also:
    - src.config.field_metadata: FieldMetadata dataclass
    - scripts.discover_finlab_fields: Field discovery and cache management
    - tests.test_data_field_manifest: TDD test suite
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Import cache loading function and FieldMetadata
from scripts.discover_finlab_fields import load_field_cache
from src.config.field_metadata import FieldMetadata


class DataFieldManifest:
    """
    Layer 1: Enhanced Data Field Manifest with O(1) alias resolution.

    This class provides fast field lookups using pre-computed data structures:
    - _fields_by_canonical: Dict[canonical_name, FieldMetadata] for O(1) canonical lookup
    - _alias_map: Dict[alias, canonical_name] for O(1) alias resolution

    All lookups are O(1) using dict access, ensuring <1ms performance.

    Attributes:
        _fields_by_canonical: Mapping from canonical field names to FieldMetadata objects
        _alias_map: Mapping from aliases to canonical field names
        _cache_path: Path to JSON cache file used for initialization

    Example:
        >>> # Initialize from cache
        >>> manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
        >>>
        >>> # Resolve alias to canonical name
        >>> field = manifest.get_field('close')
        >>> assert field.canonical_name == 'price:收盤價'
        >>>
        >>> # Direct canonical name lookup
        >>> field = manifest.get_field('price:收盤價')
        >>> assert field is not None
        >>>
        >>> # Validate field existence
        >>> assert manifest.validate_field('volume') is True
        >>> assert manifest.validate_field('invalid_field') is False
        >>>
        >>> # Get all aliases for a field
        >>> aliases = manifest.get_aliases('price:收盤價')
        >>> assert 'close' in aliases
        >>>
        >>> # Get canonical name from alias
        >>> canonical = manifest.get_canonical_name('close')
        >>> assert canonical == 'price:收盤價'
    """

    # Top 20 common field mistakes (based on LLM error analysis - 29.4% error rate)
    # These corrections handle the most frequent LLM field naming errors
    COMMON_CORRECTIONS: Dict[str, str] = {
        # CRITICAL: Trading value vs shares confusion (most common mistake)
        'price:成交量': 'price:成交金額',  # 成交量 is ambiguous, should be 成交金額 (trading VALUE)
        '成交量': 'price:成交金額',  # CRITICAL: Ambiguous term - LLM often uses this incorrectly
        'trading_volume': 'price:成交金額',  # Trading VALUE (not shares)
        'turnover': 'price:成交金額',  # Common English term for trading value
        'volume_amount': 'price:成交金額',  # Explicitly means trading value

        # Common price field typos and variations
        'close_value': 'price:收盤價',
        'closing': 'price:收盤價',
        '收盤': 'price:收盤價',
        'opening': 'price:開盤價',
        '開盤': 'price:開盤價',
        'highest': 'price:最高價',
        'lowest': 'price:最低價',

        # Common fundamental ratio typos
        'pe_ratio': 'fundamental_features:本益比',
        'pb_ratio': 'fundamental_features:股價淨值比',
        'roe_ratio': 'fundamental_features:ROE',
        'roa_ratio': 'fundamental_features:ROA',

        # Chinese variations and common typos
        '股東權益報酬率': 'fundamental_features:ROE',
        '資產報酬率': 'fundamental_features:ROA',
        '現金殖利率': 'fundamental_features:殖利率',

        # Shares field confusion
        'volume_shares': 'price:成交股數',  # Explicitly means shares count
        'share_volume': 'price:成交股數',
    }

    def __init__(self, cache_path: str = 'tests/fixtures/finlab_fields.json'):
        """
        Initialize DataFieldManifest by loading fields from cache and building O(1) lookup structures.

        Args:
            cache_path: Path to JSON cache file containing field metadata.
                       Defaults to 'tests/fixtures/finlab_fields.json' for testing.

        Raises:
            FileNotFoundError: If cache file doesn't exist at specified path
            json.JSONDecodeError: If cache file contains invalid JSON
            ValueError: If cache contains invalid field metadata

        Note:
            - Loads all fields from cache using load_field_cache()
            - Pre-computes _alias_map for O(1) alias → canonical resolution
            - Pre-computes _fields_by_canonical for O(1) canonical → FieldMetadata lookup
            - Initialization time is O(n) where n = number of fields, but all subsequent
              lookups are O(1)

        Example:
            >>> # Initialize with default cache path
            >>> manifest = DataFieldManifest()
            >>> assert len(manifest._fields_by_canonical) >= 14
            >>>
            >>> # Initialize with custom cache path
            >>> manifest = DataFieldManifest('path/to/custom_cache.json')
        """
        self._cache_path = cache_path

        # Load fields from cache (raises FileNotFoundError if not found)
        fields_dict = load_field_cache(cache_path)

        # Store fields by canonical name for O(1) lookup
        self._fields_by_canonical: Dict[str, FieldMetadata] = fields_dict

        # Build alias → canonical name mapping for O(1) alias resolution
        self._alias_map: Dict[str, str] = {}
        for canonical_name, field_metadata in fields_dict.items():
            # Map each alias to its canonical name
            for alias in field_metadata.aliases:
                self._alias_map[alias] = canonical_name

            # Also map canonical name to itself for unified lookup
            self._alias_map[canonical_name] = canonical_name

    def get_field(self, name: str) -> Optional[FieldMetadata]:
        """
        Get field by canonical name or alias (O(1) lookup).

        This method provides unified field lookup - it works with both
        canonical names and aliases, automatically resolving to the
        correct FieldMetadata object.

        Args:
            name: Field name (canonical or alias).
                 Examples: 'close', 'price:收盤價', 'volume', 'ROE'

        Returns:
            FieldMetadata object if field exists, None otherwise.

        Performance:
            O(1) dict lookup. Average time <1ms.

        Example:
            >>> manifest = DataFieldManifest()
            >>>
            >>> # Get field by alias
            >>> field = manifest.get_field('close')
            >>> assert field.canonical_name == 'price:收盤價'
            >>>
            >>> # Get field by canonical name
            >>> field = manifest.get_field('price:收盤價')
            >>> assert field is not None
            >>>
            >>> # Invalid field returns None
            >>> field = manifest.get_field('invalid_alias')
            >>> assert field is None
        """
        if not name or not isinstance(name, str):
            return None

        # Resolve alias to canonical name (O(1) dict lookup)
        canonical_name = self._alias_map.get(name)
        if canonical_name is None:
            return None

        # Get field metadata by canonical name (O(1) dict lookup)
        return self._fields_by_canonical.get(canonical_name)

    def validate_field(self, name: str) -> bool:
        """
        Check if field exists (canonical or alias) using O(1) lookup.

        Args:
            name: Field name (canonical or alias) to validate.

        Returns:
            True if field exists, False otherwise.

        Performance:
            O(1) dict lookup. Average time <1ms.

        Example:
            >>> manifest = DataFieldManifest()
            >>>
            >>> # Validate by alias
            >>> assert manifest.validate_field('close') is True
            >>> assert manifest.validate_field('volume') is True
            >>>
            >>> # Validate by canonical name
            >>> assert manifest.validate_field('price:收盤價') is True
            >>>
            >>> # Invalid field
            >>> assert manifest.validate_field('invalid_field') is False
            >>> assert manifest.validate_field('') is False
        """
        if not name or not isinstance(name, str):
            return False

        # Check if name exists in alias map (O(1) dict lookup)
        return name in self._alias_map

    def validate_field_with_suggestion(self, name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate field and provide correction suggestion if available.

        This method extends validate_field() by providing helpful suggestions for
        common LLM field naming mistakes. Based on error analysis showing 29.4%
        field error rate, this helps auto-correct frequent mistakes.

        Args:
            name: Field name (canonical or alias) to validate.

        Returns:
            Tuple of (is_valid, suggestion):
            - (True, None) if field is valid
            - (False, "Did you mean '...'?") if common mistake detected
            - (False, None) if invalid with no known correction

        Performance:
            O(1) dict lookups. Average time <1ms.

        Example:
            >>> manifest = DataFieldManifest()
            >>>
            >>> # Valid field returns (True, None)
            >>> is_valid, suggestion = manifest.validate_field_with_suggestion('close')
            >>> assert is_valid is True
            >>> assert suggestion is None
            >>>
            >>> # Common mistake returns suggestion
            >>> is_valid, suggestion = manifest.validate_field_with_suggestion('price:成交量')
            >>> assert is_valid is False
            >>> assert "price:成交金額" in suggestion
            >>>
            >>> # Unknown invalid field returns (False, None)
            >>> is_valid, suggestion = manifest.validate_field_with_suggestion('invalid_xyz')
            >>> assert is_valid is False
            >>> assert suggestion is None
        """
        # Handle edge cases
        if not name or not isinstance(name, str):
            return (False, None)

        # Check if field is valid (O(1) lookup)
        if self.validate_field(name):
            return (True, None)

        # Check for common corrections (O(1) lookup)
        if name in self.COMMON_CORRECTIONS:
            correct_name = self.COMMON_CORRECTIONS[name]
            return (False, f"Did you mean '{correct_name}'?")

        # Invalid field with no known correction
        return (False, None)

    def get_aliases(self, canonical_name: str) -> Optional[List[str]]:
        """
        Get all aliases for a canonical field name.

        Args:
            canonical_name: Canonical field name (e.g., 'price:收盤價').

        Returns:
            List of aliases if field exists, None otherwise.

        Performance:
            O(1) dict lookup + O(k) list copy where k = number of aliases.
            Average time <1ms.

        Example:
            >>> manifest = DataFieldManifest()
            >>>
            >>> # Get aliases for closing price
            >>> aliases = manifest.get_aliases('price:收盤價')
            >>> assert 'close' in aliases
            >>> assert '收盤價' in aliases
            >>>
            >>> # Get aliases for trading value
            >>> aliases = manifest.get_aliases('price:成交金額')
            >>> assert 'volume' in aliases
            >>>
            >>> # Invalid field returns None
            >>> aliases = manifest.get_aliases('invalid:field')
            >>> assert aliases is None
        """
        if not canonical_name or not isinstance(canonical_name, str):
            return None

        # Get field metadata (O(1) dict lookup)
        field = self._fields_by_canonical.get(canonical_name)
        if field is None:
            return None

        # Return copy of aliases list to prevent external modification
        return field.aliases.copy()

    def get_canonical_name(self, name: str) -> Optional[str]:
        """
        Resolve alias or canonical name to canonical name (O(1) lookup).

        This method provides bidirectional resolution:
        - If name is an alias, returns canonical name
        - If name is already canonical, returns itself
        - If name is invalid, returns None

        Args:
            name: Field name (alias or canonical).

        Returns:
            Canonical field name if valid, None otherwise.

        Performance:
            O(1) dict lookup. Average time <1ms.

        Example:
            >>> manifest = DataFieldManifest()
            >>>
            >>> # Resolve alias to canonical
            >>> assert manifest.get_canonical_name('close') == 'price:收盤價'
            >>> assert manifest.get_canonical_name('volume') == 'price:成交金額'
            >>>
            >>> # Canonical name returns itself
            >>> assert manifest.get_canonical_name('price:收盤價') == 'price:收盤價'
            >>>
            >>> # Invalid name returns None
            >>> assert manifest.get_canonical_name('invalid_alias') is None
        """
        if not name or not isinstance(name, str):
            return None

        # Resolve using alias map (O(1) dict lookup)
        # This works for both aliases and canonical names since we map
        # canonical names to themselves in __init__
        return self._alias_map.get(name)

    def get_field_count(self) -> int:
        """
        Get total number of unique fields in manifest.

        Returns:
            Number of canonical fields.

        Example:
            >>> manifest = DataFieldManifest()
            >>> assert manifest.get_field_count() >= 14
        """
        return len(self._fields_by_canonical)

    def get_all_canonical_names(self) -> List[str]:
        """
        Get list of all canonical field names.

        Returns:
            Sorted list of canonical field names.

        Example:
            >>> manifest = DataFieldManifest()
            >>> names = manifest.get_all_canonical_names()
            >>> assert 'price:收盤價' in names
            >>> assert 'fundamental_features:ROE' in names
        """
        return sorted(self._fields_by_canonical.keys())

    def get_fields_by_category(self, category: str) -> List[FieldMetadata]:
        """
        Get all fields in a specific category.

        Args:
            category: Category name ('price', 'fundamental', 'technical').

        Returns:
            List of FieldMetadata objects in the specified category.

        Example:
            >>> manifest = DataFieldManifest()
            >>>
            >>> # Get all price fields
            >>> price_fields = manifest.get_fields_by_category('price')
            >>> assert len(price_fields) >= 7
            >>>
            >>> # Get all fundamental fields
            >>> fundamental_fields = manifest.get_fields_by_category('fundamental')
            >>> assert len(fundamental_fields) >= 7
        """
        return [
            field for field in self._fields_by_canonical.values()
            if field.category == category
        ]

    def __repr__(self) -> str:
        """
        String representation of DataFieldManifest.

        Returns:
            String showing field count and cache path.

        Example:
            >>> manifest = DataFieldManifest()
            >>> repr(manifest)
            'DataFieldManifest(fields=14, cache_path=tests/fixtures/finlab_fields.json)'
        """
        return f"DataFieldManifest(fields={self.get_field_count()}, cache_path={self._cache_path})"
