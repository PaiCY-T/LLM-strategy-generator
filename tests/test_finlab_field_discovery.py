"""
TDD Tests for finlab Field Discovery Module

This test module follows TDD RED-GREEN-REFACTOR methodology:
1. RED: Write failing tests first
2. GREEN: Implement minimal code to pass
3. REFACTOR: Improve code quality while maintaining passing tests

Tests cover:
- Field discovery from finlab API
- Field metadata completeness and validation
- JSON cache save/load functionality
- Cache file format verification
"""

import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict

# Import the functions and classes to test
from scripts.discover_finlab_fields import (
    discover_finlab_fields,
    save_field_cache,
    load_field_cache,
    FieldMetadata,
)


class TestFieldDiscovery:
    """Tests for discover_finlab_fields() function."""

    def test_finlab_api_field_availability(self):
        """
        Test that all discovered fields exist in finlab API.

        Verifies:
        - Minimum field count (≥14 fields)
        - Critical fields exist (price, fundamental)
        - Field metadata completeness
        - Metadata validation (category, frequency, etc.)
        """
        fields = discover_finlab_fields()

        # Verify minimum field count
        assert len(fields) >= 14, f"Should discover at least 14 fields, got {len(fields)}"

        # Verify critical fields exist
        assert 'price:收盤價' in fields, "Missing critical field: price:收盤價"
        assert 'price:成交金額' in fields, "Missing critical field: price:成交金額"
        assert 'fundamental_features:ROE' in fields, "Missing critical field: fundamental_features:ROE"

        # Verify field metadata completeness for all fields
        for field_name, metadata in fields.items():
            # Verify canonical name matches key
            assert metadata.canonical_name == field_name, \
                f"Canonical name mismatch: {metadata.canonical_name} != {field_name}"

            # Verify category is valid
            assert metadata.category in ['price', 'fundamental', 'technical'], \
                f"Invalid category '{metadata.category}' for field {field_name}"

            # Verify frequency is valid
            assert metadata.frequency in ['daily', 'weekly', 'monthly', 'quarterly'], \
                f"Invalid frequency '{metadata.frequency}' for field {field_name}"

            # Verify aliases exist and are not empty
            assert len(metadata.aliases) > 0, \
                f"No aliases found for field {field_name}"

            assert isinstance(metadata.aliases, list), \
                f"Aliases must be a list for {field_name}"

    def test_field_metadata_completeness(self):
        """
        Test that field metadata is complete and properly structured.

        Verifies:
        - All required attributes are present
        - Data types are correct
        - String fields are non-empty
        - Collections are properly structured
        """
        fields = discover_finlab_fields()

        required_attributes = [
            'canonical_name',
            'category',
            'frequency',
            'dtype',
            'description_zh',
            'description_en',
            'aliases',
        ]

        for field_name, metadata in fields.items():
            # Verify all required attributes exist
            for attr in required_attributes:
                assert hasattr(metadata, attr), \
                    f"Missing attribute '{attr}' in metadata for {field_name}"

            # Verify string fields are non-empty
            assert metadata.canonical_name.strip(), \
                f"Empty canonical_name for {field_name}"
            assert metadata.category.strip(), \
                f"Empty category for {field_name}"
            assert metadata.frequency.strip(), \
                f"Empty frequency for {field_name}"
            assert metadata.dtype.strip(), \
                f"Empty dtype for {field_name}"
            assert metadata.description_zh.strip(), \
                f"Empty description_zh for {field_name}"
            assert metadata.description_en.strip(), \
                f"Empty description_en for {field_name}"

            # Verify dtype is valid
            assert metadata.dtype in ['float', 'int', 'str'], \
                f"Invalid dtype '{metadata.dtype}' for {field_name}"

            # Verify aliases structure
            assert isinstance(metadata.aliases, list), \
                f"Aliases must be a list for {field_name}"
            for alias in metadata.aliases:
                assert isinstance(alias, str), \
                    f"All aliases must be strings for {field_name}"
                assert alias.strip(), \
                    f"Empty alias found for {field_name}"


class TestCacheSaveAndLoad:
    """Tests for save_field_cache() and load_field_cache() functions."""

    def test_cache_save_and_load_roundtrip(self):
        """
        Test that fields can be saved and loaded without data loss.

        Verifies:
        - Save creates file in correct location
        - File is valid JSON
        - Load retrieves all fields
        - Metadata is preserved exactly (round-trip serialization)
        """
        fields = discover_finlab_fields()

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"

            # Save fields to temporary cache
            save_field_cache(fields, str(cache_path))

            # Verify file exists
            assert cache_path.exists(), f"Cache file not created at {cache_path}"

            # Load fields from cache
            loaded_fields = load_field_cache(str(cache_path))

            # Verify same number of fields
            assert len(loaded_fields) == len(fields), \
                f"Field count mismatch: {len(loaded_fields)} != {len(fields)}"

            # Verify all field names are present
            assert set(loaded_fields.keys()) == set(fields.keys()), \
                "Field names don't match after round-trip"

            # Verify metadata is identical for each field
            for field_name in fields:
                original = fields[field_name]
                loaded = loaded_fields[field_name]

                assert loaded.canonical_name == original.canonical_name
                assert loaded.category == original.category
                assert loaded.frequency == original.frequency
                assert loaded.dtype == original.dtype
                assert loaded.description_zh == original.description_zh
                assert loaded.description_en == original.description_en
                assert loaded.aliases == original.aliases
                assert loaded.valid_range == original.valid_range

    def test_cache_file_format(self):
        """
        Test that cache file is valid JSON with expected structure.

        Verifies:
        - File is valid JSON
        - Top-level is object (dict) with field names as keys
        - Each field object has required properties
        - Data types in JSON are correct (valid_range is array, not tuple)
        """
        fields = discover_finlab_fields()

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            save_field_cache(fields, str(cache_path))

            # Read raw JSON to verify format
            with open(cache_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            # Verify top-level is dict
            assert isinstance(json_data, dict), "JSON root must be an object"

            # Verify each field in JSON has required properties
            for field_name, field_obj in json_data.items():
                assert isinstance(field_obj, dict), \
                    f"Field {field_name} must be an object in JSON"

                # Verify required properties
                assert 'canonical_name' in field_obj
                assert 'category' in field_obj
                assert 'frequency' in field_obj
                assert 'dtype' in field_obj
                assert 'description_zh' in field_obj
                assert 'description_en' in field_obj
                assert 'aliases' in field_obj

                # Verify aliases is array in JSON
                assert isinstance(field_obj['aliases'], list), \
                    f"Aliases in JSON must be array for {field_name}"

                # Verify valid_range is array (not tuple) if present
                if field_obj['valid_range'] is not None:
                    assert isinstance(field_obj['valid_range'], list), \
                        f"valid_range in JSON must be array for {field_name}"

    def test_cache_load_from_missing_file(self):
        """
        Test that load_field_cache raises FileNotFoundError for missing file.

        Verifies:
        - Proper error handling for non-existent cache files
        - Error message is informative
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "nonexistent" / "cache.json"

            with pytest.raises(FileNotFoundError) as exc_info:
                load_field_cache(str(missing_path))

            assert "not found" in str(exc_info.value).lower()

    def test_cache_load_from_invalid_json(self):
        """
        Test that load_field_cache raises JSONDecodeError for invalid JSON.

        Verifies:
        - Proper error handling for corrupted/invalid cache files
        - Error message indicates JSON parsing issue
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "invalid.json"

            # Write invalid JSON
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write("{ invalid json }")

            with pytest.raises(json.JSONDecodeError):
                load_field_cache(str(cache_path))


class TestCriticalFields:
    """Tests for presence and validity of critical fields."""

    def test_price_category_fields(self):
        """Test that all critical price fields are present and valid."""
        fields = discover_finlab_fields()

        critical_price_fields = [
            'price:收盤價',
            'price:開盤價',
            'price:最高價',
            'price:最低價',
            'price:成交股數',
            'price:成交金額',
        ]

        for field_name in critical_price_fields:
            assert field_name in fields, f"Missing critical price field: {field_name}"
            metadata = fields[field_name]
            assert metadata.category == 'price', \
                f"Field {field_name} should have category 'price'"
            assert metadata.frequency == 'daily', \
                f"Price field {field_name} should have daily frequency"

    def test_fundamental_category_fields(self):
        """Test that fundamental features fields are present and valid."""
        fields = discover_finlab_fields()

        # At least ROE should exist
        assert 'fundamental_features:ROE' in fields, \
            "Missing critical fundamental field: fundamental_features:ROE"

        roe_metadata = fields['fundamental_features:ROE']
        assert roe_metadata.category == 'fundamental', \
            "ROE field should have category 'fundamental'"


class TestFieldMetadataValidation:
    """Tests for FieldMetadata class validation."""

    def test_field_metadata_instantiation(self):
        """Test that FieldMetadata can be properly instantiated and used."""
        metadata = FieldMetadata(
            canonical_name='price:測試',
            category='price',
            frequency='daily',
            dtype='float',
            description_zh='測試描述',
            description_en='Test description',
            aliases=['test', '測試'],
            valid_range=(0.0, 1000.0)
        )

        assert metadata.canonical_name == 'price:測試'
        assert metadata.category == 'price'
        assert metadata.frequency == 'daily'
        assert metadata.dtype == 'float'
        assert metadata.aliases == ['test', '測試']
        assert metadata.valid_range == (0.0, 1000.0)

    def test_field_metadata_optional_fields(self):
        """Test that optional fields can be omitted."""
        metadata = FieldMetadata(
            canonical_name='test:field',
            category='technical',
            frequency='daily',
            dtype='int',
            description_zh='描述',
            description_en='Description',
            aliases=['test'],
        )

        assert metadata.example_values is None
        assert metadata.valid_range is None


class TestCacheIntegration:
    """Integration tests for complete cache workflow."""

    def test_complete_workflow(self):
        """
        Test complete workflow: discover -> save -> load -> verify.

        This integration test ensures the entire cache pipeline works correctly.
        """
        # Step 1: Discover fields
        discovered_fields = discover_finlab_fields()
        assert len(discovered_fields) >= 14

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "complete_test.json"

            # Step 2: Save to cache
            save_field_cache(discovered_fields, str(cache_path))
            assert cache_path.exists()

            # Step 3: Load from cache
            loaded_fields = load_field_cache(str(cache_path))

            # Step 4: Verify completeness
            assert len(loaded_fields) == len(discovered_fields)
            assert 'price:收盤價' in loaded_fields
            assert 'price:成交金額' in loaded_fields
            assert 'fundamental_features:ROE' in loaded_fields

            # Step 5: Verify metadata accuracy
            for field_name in discovered_fields:
                original = discovered_fields[field_name]
                loaded = loaded_fields[field_name]

                assert loaded.canonical_name == original.canonical_name
                assert loaded.category == original.category
                assert loaded.frequency == original.frequency
                assert loaded.dtype == original.dtype
                assert loaded.aliases == original.aliases
