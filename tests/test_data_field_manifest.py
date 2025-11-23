"""
TDD Tests for DataFieldManifest Class (Layer 1: Enhanced Data Field Manifest)

This test module follows TDD RED-GREEN-REFACTOR methodology:
1. RED: Write failing tests first (this phase)
2. GREEN: Implement minimal code to pass
3. REFACTOR: Improve code quality while maintaining passing tests

Tests cover:
- Alias resolution (e.g., 'close' → 'price:收盤價')
- Canonical name lookup (direct field access)
- Field existence validation
- Alias retrieval (all aliases for a field)
- Performance benchmarks (<1ms lookups)

Layer 1 Architecture:
- O(1) alias resolution using pre-computed dict
- Bidirectional mapping: alias → canonical, canonical → aliases
- Integration with FieldMetadata and cache system
"""

import pytest
import time
from pathlib import Path
from typing import Optional

# Import the class to test (will fail initially - this is RED phase)
from src.config.data_fields import DataFieldManifest
from src.config.field_metadata import FieldMetadata


class TestAliasResolution:
    """Tests for alias → canonical name resolution (Task 4.1)."""

    @pytest.fixture
    def manifest(self):
        """Create DataFieldManifest from test cache."""
        cache_path = 'tests/fixtures/finlab_fields.json'
        return DataFieldManifest(cache_path=cache_path)

    def test_alias_resolution_close_to_canonical(self, manifest):
        """
        Test alias 'close' resolves to canonical name 'price:收盤價'.

        This is a critical alias mapping that LLM strategies commonly use.
        Verifies O(1) lookup from alias to canonical name.
        """
        field = manifest.get_field('close')
        assert field is not None, "Alias 'close' should resolve to a field"
        assert field.canonical_name == 'price:收盤價', \
            f"Alias 'close' should resolve to 'price:收盤價', got {field.canonical_name}"

    def test_alias_resolution_volume_to_canonical(self, manifest):
        """
        Test alias 'volume' resolves to 'price:成交金額' (trading value, NOT shares).

        CRITICAL: 'volume' is commonly mistaken to mean shares, but it maps to
        trading value (成交金額) in finlab API. This is a common LLM error.
        """
        field = manifest.get_field('volume')
        assert field is not None, "Alias 'volume' should resolve to a field"
        assert field.canonical_name == 'price:成交金額', \
            f"Alias 'volume' should resolve to 'price:成交金額' (trading value), got {field.canonical_name}"

    def test_alias_resolution_roe_lowercase(self, manifest):
        """Test alias 'roe' (lowercase) resolves to 'fundamental_features:ROE'."""
        field = manifest.get_field('roe')
        assert field is not None, "Alias 'roe' should resolve to a field"
        assert field.canonical_name == 'fundamental_features:ROE'

    def test_alias_resolution_roe_uppercase(self, manifest):
        """Test alias 'ROE' (uppercase) resolves to 'fundamental_features:ROE'."""
        field = manifest.get_field('ROE')
        assert field is not None, "Alias 'ROE' should resolve to a field"
        assert field.canonical_name == 'fundamental_features:ROE'

    def test_alias_resolution_pe_ratio(self, manifest):
        """Test alias 'pe' resolves to 'fundamental_features:本益比'."""
        field = manifest.get_field('pe')
        assert field is not None, "Alias 'pe' should resolve to a field"
        assert field.canonical_name == 'fundamental_features:本益比'

    def test_alias_resolution_invalid_alias(self, manifest):
        """Test that invalid alias returns None."""
        field = manifest.get_field('nonexistent_alias')
        assert field is None, "Invalid alias should return None"


class TestCanonicalNameLookup:
    """Tests for direct canonical name lookup (Task 4.1)."""

    @pytest.fixture
    def manifest(self):
        """Create DataFieldManifest from test cache."""
        cache_path = 'tests/fixtures/finlab_fields.json'
        return DataFieldManifest(cache_path=cache_path)

    def test_get_field_by_canonical_name_price(self, manifest):
        """Test direct canonical name lookup for price field."""
        field = manifest.get_field('price:收盤價')
        assert field is not None
        assert field.canonical_name == 'price:收盤價'
        assert field.category == 'price'

    def test_get_field_by_canonical_name_fundamental(self, manifest):
        """Test direct canonical name lookup for fundamental field."""
        field = manifest.get_field('fundamental_features:ROE')
        assert field is not None
        assert field.canonical_name == 'fundamental_features:ROE'
        assert field.category == 'fundamental'

    def test_get_field_by_invalid_canonical_name(self, manifest):
        """Test that invalid canonical name returns None."""
        field = manifest.get_field('invalid:field_name')
        assert field is None


class TestFieldExistenceValidation:
    """Tests for field existence validation (Task 4.1)."""

    @pytest.fixture
    def manifest(self):
        """Create DataFieldManifest from test cache."""
        cache_path = 'tests/fixtures/finlab_fields.json'
        return DataFieldManifest(cache_path=cache_path)

    def test_validate_field_exists_by_canonical_name(self, manifest):
        """Test field validation with canonical name."""
        assert manifest.validate_field('price:收盤價') is True
        assert manifest.validate_field('fundamental_features:ROE') is True

    def test_validate_field_exists_by_alias(self, manifest):
        """Test field validation with alias."""
        assert manifest.validate_field('close') is True
        assert manifest.validate_field('volume') is True
        assert manifest.validate_field('roe') is True

    def test_validate_field_not_exists(self, manifest):
        """Test that validation returns False for invalid fields."""
        assert manifest.validate_field('nonexistent_field') is False
        assert manifest.validate_field('invalid_alias') is False
        assert manifest.validate_field('') is False


class TestAliasRetrieval:
    """Tests for retrieving all aliases for a canonical field (Task 4.1)."""

    @pytest.fixture
    def manifest(self):
        """Create DataFieldManifest from test cache."""
        cache_path = 'tests/fixtures/finlab_fields.json'
        return DataFieldManifest(cache_path=cache_path)

    def test_get_all_aliases_for_close_price(self, manifest):
        """Test retrieving all aliases for closing price field."""
        aliases = manifest.get_aliases('price:收盤價')
        assert aliases is not None
        assert isinstance(aliases, list)
        assert 'close' in aliases
        assert '收盤價' in aliases
        assert 'closing_price' in aliases

    def test_get_all_aliases_for_volume(self, manifest):
        """Test retrieving all aliases for trading value field."""
        aliases = manifest.get_aliases('price:成交金額')
        assert aliases is not None
        assert 'volume' in aliases, "'volume' should be an alias for trading value"
        assert 'amount' in aliases
        assert 'value' in aliases

    def test_get_all_aliases_for_roe(self, manifest):
        """Test retrieving all aliases for ROE field."""
        aliases = manifest.get_aliases('fundamental_features:ROE')
        assert aliases is not None
        assert 'roe' in aliases
        assert 'ROE' in aliases
        assert 'return_on_equity' in aliases

    def test_get_aliases_for_invalid_field(self, manifest):
        """Test that get_aliases returns None/empty list for invalid field."""
        aliases = manifest.get_aliases('invalid:field')
        assert aliases is None or aliases == []

    def test_get_aliases_for_empty_string(self, manifest):
        """Test that get_aliases returns None for empty string."""
        aliases = manifest.get_aliases('')
        assert aliases is None

    def test_get_aliases_for_none(self, manifest):
        """Test that get_aliases handles None gracefully."""
        try:
            aliases = manifest.get_aliases(None)
            assert aliases is None
        except (TypeError, AttributeError):
            pass  # Acceptable to raise error for None


class TestCanonicalNameResolution:
    """Tests for alias → canonical name resolution (Task 4.1)."""

    @pytest.fixture
    def manifest(self):
        """Create DataFieldManifest from test cache."""
        cache_path = 'tests/fixtures/finlab_fields.json'
        return DataFieldManifest(cache_path=cache_path)

    def test_get_canonical_name_from_alias(self, manifest):
        """Test getting canonical name from alias."""
        assert manifest.get_canonical_name('close') == 'price:收盤價'
        assert manifest.get_canonical_name('volume') == 'price:成交金額'
        assert manifest.get_canonical_name('roe') == 'fundamental_features:ROE'

    def test_get_canonical_name_from_canonical(self, manifest):
        """Test that canonical names return themselves."""
        assert manifest.get_canonical_name('price:收盤價') == 'price:收盤價'
        assert manifest.get_canonical_name('fundamental_features:ROE') == 'fundamental_features:ROE'

    def test_get_canonical_name_invalid(self, manifest):
        """Test that invalid names return None."""
        assert manifest.get_canonical_name('invalid_alias') is None
        assert manifest.get_canonical_name('') is None


class TestPerformance:
    """Tests for lookup performance (Task 4.3 - Performance requirement)."""

    @pytest.fixture
    def manifest(self):
        """Create DataFieldManifest from test cache."""
        cache_path = 'tests/fixtures/finlab_fields.json'
        return DataFieldManifest(cache_path=cache_path)

    def test_alias_resolution_performance(self, manifest):
        """
        Test that alias resolution completes in <1ms.

        Performance requirement from Task 4.3:
        - Alias lookups must use O(1) dict access
        - Average lookup time should be <1ms
        """
        # Warm up
        manifest.get_field('close')

        # Benchmark 1000 lookups
        start_time = time.perf_counter()
        for _ in range(1000):
            manifest.get_field('close')
        end_time = time.perf_counter()

        avg_time_ms = (end_time - start_time) * 1000 / 1000
        assert avg_time_ms < 1.0, \
            f"Average alias resolution time {avg_time_ms:.3f}ms exceeds 1ms threshold"

    def test_canonical_lookup_performance(self, manifest):
        """
        Test that canonical name lookup completes in <1ms.

        Performance requirement from Task 4.3:
        - Canonical lookups must use O(1) dict access
        - Average lookup time should be <1ms
        """
        # Warm up
        manifest.get_field('price:收盤價')

        # Benchmark 1000 lookups
        start_time = time.perf_counter()
        for _ in range(1000):
            manifest.get_field('price:收盤價')
        end_time = time.perf_counter()

        avg_time_ms = (end_time - start_time) * 1000 / 1000
        assert avg_time_ms < 1.0, \
            f"Average canonical lookup time {avg_time_ms:.3f}ms exceeds 1ms threshold"

    def test_validation_performance(self, manifest):
        """
        Test that field validation completes in <1ms.

        Performance requirement from Task 4.3:
        - Validation should be O(1) using pre-computed structures
        """
        # Warm up
        manifest.validate_field('close')

        # Benchmark 1000 validations
        start_time = time.perf_counter()
        for _ in range(1000):
            manifest.validate_field('close')
        end_time = time.perf_counter()

        avg_time_ms = (end_time - start_time) * 1000 / 1000
        assert avg_time_ms < 1.0, \
            f"Average validation time {avg_time_ms:.3f}ms exceeds 1ms threshold"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def manifest(self):
        """Create DataFieldManifest from test cache."""
        cache_path = 'tests/fixtures/finlab_fields.json'
        return DataFieldManifest(cache_path=cache_path)

    def test_empty_string_field_name(self, manifest):
        """Test that empty string field name returns None/False."""
        assert manifest.get_field('') is None
        assert manifest.validate_field('') is False
        assert manifest.get_canonical_name('') is None

    def test_none_field_name(self, manifest):
        """Test that None field name is handled gracefully."""
        # Should not crash - either return None or raise TypeError
        try:
            result = manifest.get_field(None)
            assert result is None
        except TypeError:
            pass  # Acceptable to raise TypeError for None

    def test_case_sensitive_aliases(self, manifest):
        """Test that alias resolution respects case sensitivity."""
        # 'roe' and 'ROE' are both valid aliases
        assert manifest.get_field('roe') is not None
        assert manifest.get_field('ROE') is not None
        assert manifest.get_canonical_name('roe') == manifest.get_canonical_name('ROE')


class TestIntegration:
    """Integration tests for DataFieldManifest with cache system."""

    def test_manifest_loads_from_cache(self):
        """Test that DataFieldManifest successfully loads from cache file."""
        cache_path = 'tests/fixtures/finlab_fields.json'
        manifest = DataFieldManifest(cache_path=cache_path)

        # Verify manifest is properly initialized
        assert manifest is not None

        # Verify critical fields are accessible
        assert manifest.get_field('close') is not None
        assert manifest.get_field('price:收盤價') is not None
        assert manifest.validate_field('volume') is True

    def test_manifest_integrates_with_field_metadata(self):
        """Test that DataFieldManifest returns proper FieldMetadata objects."""
        cache_path = 'tests/fixtures/finlab_fields.json'
        manifest = DataFieldManifest(cache_path=cache_path)

        field = manifest.get_field('close')
        assert isinstance(field, FieldMetadata)
        assert field.canonical_name == 'price:收盤價'
        assert field.category == 'price'
        assert field.frequency == 'daily'
        assert field.dtype == 'float'
        assert len(field.aliases) > 0


class TestUtilityMethods:
    """Tests for utility methods (100% coverage)."""

    @pytest.fixture
    def manifest(self):
        """Create DataFieldManifest from test cache."""
        cache_path = 'tests/fixtures/finlab_fields.json'
        return DataFieldManifest(cache_path=cache_path)

    def test_get_field_count(self, manifest):
        """Test getting total field count."""
        count = manifest.get_field_count()
        assert count >= 14, f"Should have at least 14 fields, got {count}"
        assert isinstance(count, int)

    def test_get_all_canonical_names(self, manifest):
        """Test getting all canonical field names."""
        names = manifest.get_all_canonical_names()
        assert isinstance(names, list)
        assert len(names) >= 14
        assert 'price:收盤價' in names
        assert 'fundamental_features:ROE' in names
        # Verify sorted
        assert names == sorted(names)

    def test_get_fields_by_category_price(self, manifest):
        """Test getting all price fields."""
        price_fields = manifest.get_fields_by_category('price')
        assert isinstance(price_fields, list)
        assert len(price_fields) >= 7
        for field in price_fields:
            assert isinstance(field, FieldMetadata)
            assert field.category == 'price'

    def test_get_fields_by_category_fundamental(self, manifest):
        """Test getting all fundamental fields."""
        fundamental_fields = manifest.get_fields_by_category('fundamental')
        assert isinstance(fundamental_fields, list)
        assert len(fundamental_fields) >= 7
        for field in fundamental_fields:
            assert isinstance(field, FieldMetadata)
            assert field.category == 'fundamental'

    def test_get_fields_by_category_invalid(self, manifest):
        """Test getting fields for invalid category returns empty list."""
        fields = manifest.get_fields_by_category('invalid_category')
        assert fields == []

    def test_repr(self, manifest):
        """Test string representation."""
        repr_str = repr(manifest)
        assert 'DataFieldManifest' in repr_str
        assert 'fields=' in repr_str
        assert 'cache_path=' in repr_str
        assert '14' in repr_str or str(manifest.get_field_count()) in repr_str


class TestCommonMistakeCorrection:
    """Tests for common mistake mapping and auto-correction (Task 6.3)."""

    @pytest.fixture
    def manifest(self):
        """Create DataFieldManifest from test cache."""
        cache_path = 'tests/fixtures/finlab_fields.json'
        return DataFieldManifest(cache_path=cache_path)

    def test_validate_field_with_common_mistake_suggestion(self, manifest):
        """
        Test that common mistakes return suggestions.

        CRITICAL: 'price:成交量' is WRONG (should be 'price:成交金額').
        This tests the most common LLM field mistake.
        """
        is_valid, suggestion = manifest.validate_field_with_suggestion('price:成交量')
        assert is_valid is False, "price:成交量 should be invalid"
        assert suggestion is not None, "Should provide a correction suggestion"
        assert 'price:成交金額' in suggestion, \
            f"Suggestion should contain correct field 'price:成交金額', got: {suggestion}"

    def test_validate_field_with_turnover_mistake(self, manifest):
        """Test that 'turnover' suggests correct trading value field."""
        is_valid, suggestion = manifest.validate_field_with_suggestion('turnover')
        assert is_valid is False
        assert suggestion is not None
        assert 'price:成交金額' in suggestion

    def test_validate_field_with_closing_price_typo(self, manifest):
        """Test that 'closing_price' suggests correct field."""
        is_valid, suggestion = manifest.validate_field_with_suggestion('closing_price')
        # Note: 'closing_price' might be a valid alias, check cache
        # If invalid, should suggest 'price:收盤價'
        if not is_valid:
            assert suggestion is not None
            assert 'price:收盤價' in suggestion

    def test_validate_field_with_pe_ratio_typo(self, manifest):
        """Test that 'pe_ratio' suggests correct fundamental field."""
        is_valid, suggestion = manifest.validate_field_with_suggestion('pe_ratio')
        assert is_valid is False
        assert suggestion is not None
        assert 'fundamental_features:本益比' in suggestion

    def test_validate_field_with_roe_typo(self, manifest):
        """Test that 'return_on_equity' is handled (might be alias or needs suggestion)."""
        is_valid, suggestion = manifest.validate_field_with_suggestion('return_on_equity')
        # If not a valid alias, should suggest 'fundamental_features:ROE'
        if not is_valid:
            assert suggestion is not None
            assert 'fundamental_features:ROE' in suggestion

    def test_validate_field_with_no_suggestion(self, manifest):
        """Test that completely invalid fields return no suggestion."""
        is_valid, suggestion = manifest.validate_field_with_suggestion('completely_invalid_xyz_123')
        assert is_valid is False, "Should be invalid"
        assert suggestion is None, "Should not have a suggestion for unknown field"

    def test_validate_valid_field_returns_true_no_suggestion(self, manifest):
        """Test that valid fields return (True, None)."""
        is_valid, suggestion = manifest.validate_field_with_suggestion('close')
        assert is_valid is True, "'close' should be a valid alias"
        assert suggestion is None, "Valid fields should not have suggestions"

    def test_validate_valid_canonical_field_returns_true_no_suggestion(self, manifest):
        """Test that valid canonical fields return (True, None)."""
        is_valid, suggestion = manifest.validate_field_with_suggestion('price:收盤價')
        assert is_valid is True, "Canonical name should be valid"
        assert suggestion is None, "Valid fields should not have suggestions"

    def test_common_corrections_has_top_20_entries(self, manifest):
        """Test that COMMON_CORRECTIONS dict has at least 20 entries."""
        # Access the class constant
        assert hasattr(DataFieldManifest, 'COMMON_CORRECTIONS'), \
            "DataFieldManifest should have COMMON_CORRECTIONS class constant"

        corrections = DataFieldManifest.COMMON_CORRECTIONS
        assert isinstance(corrections, dict), "COMMON_CORRECTIONS should be a dict"
        assert len(corrections) >= 20, \
            f"COMMON_CORRECTIONS should have at least 20 entries, got {len(corrections)}"

    def test_common_corrections_includes_critical_mistake(self, manifest):
        """Test that COMMON_CORRECTIONS includes the critical 成交量 mistake."""
        corrections = DataFieldManifest.COMMON_CORRECTIONS
        assert 'price:成交量' in corrections, \
            "COMMON_CORRECTIONS must include critical 'price:成交量' → 'price:成交金額' mapping"
        assert corrections['price:成交量'] == 'price:成交金額', \
            "COMMON_CORRECTIONS['price:成交量'] should map to 'price:成交金額'"

    def test_empty_string_validation_with_suggestion(self, manifest):
        """Test that empty string returns (False, None)."""
        is_valid, suggestion = manifest.validate_field_with_suggestion('')
        assert is_valid is False
        assert suggestion is None

    def test_none_validation_with_suggestion(self, manifest):
        """Test that None is handled gracefully."""
        try:
            is_valid, suggestion = manifest.validate_field_with_suggestion(None)
            assert is_valid is False
            assert suggestion is None
        except (TypeError, AttributeError):
            pass  # Acceptable to raise error for None
