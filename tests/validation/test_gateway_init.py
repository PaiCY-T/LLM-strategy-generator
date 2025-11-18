"""Tests for ValidationGateway initialization and Layer 1 integration.

This module tests the ValidationGateway class initialization behavior:
- Feature flag-based conditional initialization
- Layer dependency management (Layer 2 requires Layer 1)
- Field suggestions injection for LLM prompts

Test Structure:
- Test gateway initialization with different feature flag combinations
- Test inject_field_suggestions() method with enabled/disabled Layer 1
- Test singleton behavior (or lack thereof)

Requirements:
- AC3.1: Gateway initializes components based on feature flags
- AC3.2: Layer 2 requires Layer 1 to be enabled
- AC3.3: inject_field_suggestions() returns formatted field reference
"""

import os
import sys
import importlib
import pytest
from typing import Optional

from src.validation.gateway import ValidationGateway
from src.config.data_fields import DataFieldManifest


@pytest.fixture(autouse=True)
def reset_feature_flags():
    """Reset FeatureFlagManager singleton before each test.

    This ensures each test starts with a clean feature flag state
    by clearing the singleton instance and reloading the module.
    """
    # Save original environment
    original_env = {}
    for key in ['ENABLE_VALIDATION_LAYER1', 'ENABLE_VALIDATION_LAYER2', 'ENABLE_VALIDATION_LAYER3']:
        original_env[key] = os.environ.get(key)

    # Clear singleton instance before test
    if 'src.config.feature_flags' in sys.modules:
        from src.config.feature_flags import FeatureFlagManager
        FeatureFlagManager._instance = None

    yield

    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    # Clean up after test
    if 'src.config.feature_flags' in sys.modules:
        from src.config.feature_flags import FeatureFlagManager
        FeatureFlagManager._instance = None


class TestValidationGatewayInitialization:
    """Test ValidationGateway initialization based on feature flags."""

    def test_gateway_initializes_with_all_layers_disabled(self):
        """Test gateway initialization when all validation layers are disabled.

        Environment:
            ENABLE_VALIDATION_LAYER1=false (default)
            ENABLE_VALIDATION_LAYER2=false (default)
            ENABLE_VALIDATION_LAYER3=false (default)

        Expected:
            All validation components (manifest, field_validator, schema_validator)
            should be None, allowing graceful degradation when validation disabled.
        """
        # Set all flags to false (default state)
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'false'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'false'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'false'

        # Initialize gateway
        gateway = ValidationGateway()

        # Assert all components are None
        assert gateway.manifest is None, "Manifest should be None when Layer 1 disabled"
        assert gateway.field_validator is None, "FieldValidator should be None when Layer 2 disabled"
        assert gateway.schema_validator is None, "SchemaValidator should be None when Layer 3 disabled"

    def test_gateway_initializes_layer1_only(self):
        """Test gateway initialization with only Layer 1 enabled.

        Environment:
            ENABLE_VALIDATION_LAYER1=true
            ENABLE_VALIDATION_LAYER2=false (default)
            ENABLE_VALIDATION_LAYER3=false (default)

        Expected:
            - manifest should be DataFieldManifest instance
            - field_validator should be None (Layer 2 disabled)
            - schema_validator should be None (Layer 3 disabled)
        """
        # Enable only Layer 1
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'false'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'false'

        # Initialize gateway
        gateway = ValidationGateway()

        # Assert Layer 1 initialized, others None
        assert gateway.manifest is not None, "Manifest should be initialized when Layer 1 enabled"
        assert isinstance(gateway.manifest, DataFieldManifest), "Manifest should be DataFieldManifest instance"
        assert gateway.field_validator is None, "FieldValidator should be None when Layer 2 disabled"
        assert gateway.schema_validator is None, "SchemaValidator should be None when Layer 3 disabled"

    def test_gateway_initializes_layer2_requires_layer1(self):
        """Test that Layer 2 initialization requires Layer 1 to be enabled.

        Environment:
            ENABLE_VALIDATION_LAYER1=true
            ENABLE_VALIDATION_LAYER2=true
            ENABLE_VALIDATION_LAYER3=false (default)

        Expected:
            - manifest should be DataFieldManifest instance
            - field_validator should be FieldValidator instance (requires manifest)
            - schema_validator should be None (Layer 3 disabled)
        """
        # Enable Layer 1 and Layer 2
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'false'

        # Initialize gateway
        gateway = ValidationGateway()

        # Assert both Layer 1 and Layer 2 initialized
        assert gateway.manifest is not None, "Manifest should be initialized when Layer 1 enabled"
        assert gateway.field_validator is not None, "FieldValidator should be initialized when Layer 2 enabled"
        assert gateway.schema_validator is None, "SchemaValidator should be None when Layer 3 disabled"

        # Verify field_validator has reference to manifest
        assert hasattr(gateway.field_validator, 'manifest'), "FieldValidator should have manifest attribute"
        assert gateway.field_validator.manifest is gateway.manifest, "FieldValidator should use same manifest instance"

    def test_gateway_initializes_layer3_independently(self):
        """Test that Layer 3 can be initialized independently of Layer 1/2.

        Environment:
            ENABLE_VALIDATION_LAYER1=false (default)
            ENABLE_VALIDATION_LAYER2=false (default)
            ENABLE_VALIDATION_LAYER3=true

        Expected:
            - manifest should be None (Layer 1 disabled)
            - field_validator should be None (Layer 2 disabled)
            - schema_validator should be SchemaValidator instance
        """
        # Enable only Layer 3
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'false'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'false'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        # Initialize gateway
        gateway = ValidationGateway()

        # Assert only Layer 3 initialized
        assert gateway.manifest is None, "Manifest should be None when Layer 1 disabled"
        assert gateway.field_validator is None, "FieldValidator should be None when Layer 2 disabled"
        assert gateway.schema_validator is not None, "SchemaValidator should be initialized when Layer 3 enabled"

    def test_gateway_initializes_all_layers_enabled(self):
        """Test gateway initialization with all layers enabled.

        Environment:
            ENABLE_VALIDATION_LAYER1=true
            ENABLE_VALIDATION_LAYER2=true
            ENABLE_VALIDATION_LAYER3=true

        Expected:
            All components (manifest, field_validator, schema_validator) initialized
        """
        # Enable all layers
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        # Initialize gateway
        gateway = ValidationGateway()

        # Assert all components initialized
        assert gateway.manifest is not None, "Manifest should be initialized"
        assert gateway.field_validator is not None, "FieldValidator should be initialized"
        assert gateway.schema_validator is not None, "SchemaValidator should be initialized"


class TestValidationGatewayFieldSuggestions:
    """Test inject_field_suggestions() method for LLM prompt injection."""

    def test_inject_field_suggestions_when_disabled(self):
        """Test inject_field_suggestions() returns empty string when Layer 1 disabled.

        Environment:
            ENABLE_VALIDATION_LAYER1=false (default)

        Expected:
            inject_field_suggestions() returns empty string "", allowing
            LLM to operate without field validation guidance.
        """
        # Disable Layer 1
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'false'

        # Initialize gateway
        gateway = ValidationGateway()

        # Get field suggestions
        suggestions = gateway.inject_field_suggestions()

        # Assert empty string when disabled
        assert suggestions == "", "Should return empty string when Layer 1 disabled"
        assert isinstance(suggestions, str), "Should return string type"

    def test_inject_field_suggestions_when_enabled(self):
        """Test inject_field_suggestions() returns formatted field reference when enabled.

        Environment:
            ENABLE_VALIDATION_LAYER1=true

        Expected:
            inject_field_suggestions() returns formatted string containing:
            - "Valid Data Fields Reference" header
            - Common field corrections (21 entries)
            - Available fields by category (price, fundamental)
        """
        # Enable Layer 1
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'

        # Initialize gateway
        gateway = ValidationGateway()

        # Get field suggestions
        suggestions = gateway.inject_field_suggestions()

        # Assert non-empty formatted string
        assert suggestions != "", "Should return non-empty string when Layer 1 enabled"
        assert isinstance(suggestions, str), "Should return string type"

        # Verify header is present
        assert "Valid Data Fields Reference" in suggestions, "Should contain header"

        # Verify common corrections section is present
        assert "Common Field Corrections:" in suggestions, "Should contain common corrections section"

        # Verify at least some corrections are present (sample check)
        # Based on DataFieldManifest.COMMON_CORRECTIONS
        assert "price:成交量" in suggestions, "Should contain common correction example"
        assert "price:成交金額" in suggestions, "Should contain correction target example"

        # Verify field categories are present
        assert "Price Fields:" in suggestions or "price" in suggestions.lower(), "Should contain price fields"
        assert "Fundamental Fields:" in suggestions or "fundamental" in suggestions.lower(), "Should contain fundamental fields"


class TestValidationGatewaySingletonBehavior:
    """Test ValidationGateway singleton behavior (or lack thereof)."""

    def test_gateway_not_singleton(self):
        """Test that ValidationGateway is NOT a singleton.

        Environment:
            ENABLE_VALIDATION_LAYER1=true

        Expected:
            Multiple gateway instances should be different objects,
            allowing flexible instantiation in different contexts.
        """
        # Enable Layer 1 for testing
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'

        # Create two gateway instances
        gateway1 = ValidationGateway()
        gateway2 = ValidationGateway()

        # Assert they are different instances
        assert gateway1 is not gateway2, "Gateway should NOT be singleton"

        # But they should have same configuration (both have manifest)
        assert gateway1.manifest is not None
        assert gateway2.manifest is not None
