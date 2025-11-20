#!/usr/bin/env python3
"""
Test suite for FinLab field catalog completeness.

This test suite validates the comprehensive field discovery for LLM prompt improvement.
Tests ensure that ALL FinLab fields are cataloged, not just a subset, to address the
root cause of 50% LLM failure rate (Phase 1.1 requirements).

Requirements:
- Total fields >100 (CRITICAL: Show ALL fields, not just first 20)
- fundamental_features >50
- financial_statement >100
- Proper Python dict format with categories

Phase: RED (Write Failing Tests First)
Expected: ALL tests should FAIL with current 14-field catalog
"""

import json
import pytest
from pathlib import Path


class TestFinLabFieldCatalogCompleteness:
    """Test suite for comprehensive FinLab field catalog."""

    @pytest.fixture
    def field_catalog_path(self) -> Path:
        """Return path to field catalog fixture."""
        return Path(__file__).parent / 'fixtures' / 'finlab_fields.json'

    @pytest.fixture
    def field_catalog(self, field_catalog_path: Path) -> dict:
        """Load field catalog from JSON fixture."""
        with open(field_catalog_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_field_catalog_exists(self, field_catalog_path: Path):
        """Test that field catalog file exists."""
        assert field_catalog_path.exists(), \
            f"Field catalog not found at {field_catalog_path}"

    def test_field_catalog_is_dict(self, field_catalog: dict):
        """Test that field catalog is a Python dictionary."""
        assert isinstance(field_catalog, dict), \
            "Field catalog must be a dictionary"

    def test_field_catalog_completeness(self, field_catalog: dict):
        """
        Test that field catalog has >100 total fields.

        CRITICAL: This test validates the core requirement from tasks.md:
        "CRITICAL: Show ALL fields, not just first 20"

        Expected: FAIL with current 14-field catalog
        Required: >100 total fields
        """
        total_fields = len(field_catalog)
        assert total_fields > 100, \
            f"Field catalog must have >100 fields. Found: {total_fields}. " \
            f"CRITICAL: Show ALL fields, not just first 20 (tasks.md line 11)"

    def test_fundamental_features_coverage(self, field_catalog: dict):
        """
        Test that field catalog has >50 fundamental_features fields.

        Expected: FAIL with current 7 fundamental fields
        Required: >50 fundamental_features fields
        """
        fundamental_fields = [
            name for name, metadata in field_catalog.items()
            if name.startswith('fundamental_features:')
        ]
        count = len(fundamental_fields)
        assert count > 50, \
            f"Field catalog must have >50 fundamental_features fields. " \
            f"Found: {count}. Current fields: {fundamental_fields[:10]}..."

    def test_financial_statement_coverage(self, field_catalog: dict):
        """
        Test that field catalog has >100 financial_statement fields.

        Expected: FAIL with current 0 financial_statement fields
        Required: >100 financial_statement fields
        """
        financial_fields = [
            name for name, metadata in field_catalog.items()
            if name.startswith('financial_statement:')
        ]
        count = len(financial_fields)
        assert count > 100, \
            f"Field catalog must have >100 financial_statement fields. " \
            f"Found: {count}. This category is missing from current catalog."

    def test_price_fields_present(self, field_catalog: dict):
        """Test that price fields are present (baseline validation)."""
        price_fields = [
            name for name, metadata in field_catalog.items()
            if name.startswith('price:')
        ]
        count = len(price_fields)
        assert count >= 7, \
            f"Field catalog must have >=7 price fields. Found: {count}"

    def test_field_catalog_format(self, field_catalog: dict):
        """
        Test that field catalog uses proper format with categories.

        Each field must have:
        - canonical_name: str
        - category: str
        - frequency: str
        - dtype: str
        - description_zh: str
        - description_en: str
        - aliases: list
        """
        for field_name, metadata in field_catalog.items():
            assert isinstance(metadata, dict), \
                f"Field {field_name} metadata must be a dict"

            # Required fields
            required_keys = [
                'canonical_name', 'category', 'frequency', 'dtype',
                'description_zh', 'description_en', 'aliases'
            ]
            for key in required_keys:
                assert key in metadata, \
                    f"Field {field_name} missing required key: {key}"

            # Type validation
            assert isinstance(metadata['canonical_name'], str)
            assert isinstance(metadata['category'], str)
            assert isinstance(metadata['frequency'], str)
            assert isinstance(metadata['dtype'], str)
            assert isinstance(metadata['description_zh'], str)
            assert isinstance(metadata['description_en'], str)
            assert isinstance(metadata['aliases'], list)

    def test_field_categories_present(self, field_catalog: dict):
        """Test that all major field categories are present."""
        categories = set()
        for metadata in field_catalog.values():
            categories.add(metadata['category'])

        required_categories = {'price', 'fundamental'}
        missing = required_categories - categories
        assert not missing, \
            f"Field catalog missing required categories: {missing}"

    def test_field_canonical_names_unique(self, field_catalog: dict):
        """Test that canonical field names are unique."""
        canonical_names = [
            metadata['canonical_name']
            for metadata in field_catalog.values()
        ]
        duplicates = [
            name for name in canonical_names
            if canonical_names.count(name) > 1
        ]
        assert not duplicates, \
            f"Duplicate canonical names found: {set(duplicates)}"

    def test_field_aliases_non_empty(self, field_catalog: dict):
        """Test that all fields have at least one alias."""
        fields_without_aliases = [
            name for name, metadata in field_catalog.items()
            if not metadata['aliases']
        ]
        assert not fields_without_aliases, \
            f"Fields without aliases: {fields_without_aliases}"


class TestFieldDiscoveryIntegration:
    """Integration tests for field discovery script."""

    def test_discovery_script_exists(self):
        """Test that field discovery script exists."""
        script_path = Path(__file__).parent.parent / 'scripts' / 'discover_finlab_fields.py'
        assert script_path.exists(), \
            f"Field discovery script not found at {script_path}"

    def test_discovery_script_has_main(self):
        """Test that discovery script has main() function."""
        script_path = Path(__file__).parent.parent / 'scripts' / 'discover_finlab_fields.py'
        content = script_path.read_text(encoding='utf-8')
        assert 'def main()' in content, \
            "Discovery script must have main() function"
        assert "if __name__ == '__main__':" in content, \
            "Discovery script must have main entry point"

    def test_discovery_script_imports_finlab(self):
        """Test that discovery script imports finlab module."""
        script_path = Path(__file__).parent.parent / 'scripts' / 'discover_finlab_fields.py'
        content = script_path.read_text(encoding='utf-8')
        assert 'import finlab' in content or 'from finlab' in content, \
            "Discovery script must import finlab module"
