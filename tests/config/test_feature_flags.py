"""
Tests for Task 2.2: Layer 1 Feature Flag System

TDD approach:
- RED: Write failing tests first
- GREEN: Implement minimal code to pass tests
- REFACTOR: Improve code quality while keeping tests green

Requirements:
- AC1.4: ENABLE_VALIDATION_LAYER1 environment variable support
- NFR-R2: Fail-safe flags (default to false, graceful degradation)
"""

import os
import pytest
from unittest.mock import patch
import importlib
import sys


@pytest.fixture(autouse=True)
def reset_feature_flags():
    """Reset FeatureFlagManager singleton before each test."""
    # Reset singleton instance before test
    if 'src.config.feature_flags' in sys.modules:
        from src.config.feature_flags import FeatureFlagManager
        FeatureFlagManager._instance = None
        # Force reload to pick up new env vars
        importlib.reload(sys.modules['src.config.feature_flags'])

    yield

    # Clean up after test
    if 'src.config.feature_flags' in sys.modules:
        from src.config.feature_flags import FeatureFlagManager
        FeatureFlagManager._instance = None


class TestFeatureFlagManager:
    """Test centralized feature flag management."""

    def test_layer1_flag_disabled_by_default(self):
        """
        Test that Layer 1 is disabled when ENABLE_VALIDATION_LAYER1 is not set.

        REQUIREMENT: NFR-R2 - Fail-safe flags default to false
        """
        # Clear environment variable if it exists
        with patch.dict(os.environ, {}, clear=True):
            # Reload module to pick up env changes
            if 'src.config.feature_flags' in sys.modules:
                importlib.reload(sys.modules['src.config.feature_flags'])

            from src.config.feature_flags import FeatureFlagManager

            manager = FeatureFlagManager()

            # Should be disabled by default
            assert manager.is_layer1_enabled is False, \
                "Layer 1 should be disabled when env var not set"

    def test_layer1_flag_enabled_when_true(self):
        """
        Test that Layer 1 is enabled when ENABLE_VALIDATION_LAYER1=true.

        REQUIREMENT: AC1.4 - Environment variable support
        """
        # Set environment variable to "true"
        with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": "true"}):
            # Reload module to pick up env changes
            if 'src.config.feature_flags' in sys.modules:
                importlib.reload(sys.modules['src.config.feature_flags'])

            from src.config.feature_flags import FeatureFlagManager

            manager = FeatureFlagManager()

            # Should be enabled
            assert manager.is_layer1_enabled is True, \
                "Layer 1 should be enabled when ENABLE_VALIDATION_LAYER1=true"

    def test_layer1_flag_case_insensitive(self):
        """
        Test that Layer 1 flag accepts True/TRUE/true as enabled.

        REQUIREMENT: AC1.4 - Robust environment variable parsing
        """
        test_cases = ["true", "True", "TRUE", "TrUe"]

        for value in test_cases:
            with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": value}):
                # Reload module to pick up env changes
                if 'src.config.feature_flags' in sys.modules:
                    importlib.reload(sys.modules['src.config.feature_flags'])

                from src.config.feature_flags import FeatureFlagManager

                manager = FeatureFlagManager()

                # Should be enabled for all case variations
                assert manager.is_layer1_enabled is True, \
                    f"Layer 1 should be enabled for value: {value}"

    def test_layer2_layer3_flags_independent(self):
        """
        Test that Layer 2 and Layer 3 flags work independently.

        REQUIREMENT: AC1.4 - Multiple independent feature flags
        """
        # Test with only Layer 2 enabled
        with patch.dict(os.environ, {
            "ENABLE_VALIDATION_LAYER1": "false",
            "ENABLE_VALIDATION_LAYER2": "true",
            "ENABLE_VALIDATION_LAYER3": "false",
        }):
            # Reload module to pick up env changes
            if 'src.config.feature_flags' in sys.modules:
                importlib.reload(sys.modules['src.config.feature_flags'])

            from src.config.feature_flags import FeatureFlagManager

            manager = FeatureFlagManager()

            # Only Layer 2 should be enabled
            assert manager.is_layer1_enabled is False, "Layer 1 should be disabled"
            assert manager.is_layer2_enabled is True, "Layer 2 should be enabled"
            assert manager.is_layer3_enabled is False, "Layer 3 should be disabled"

        # Test with all layers enabled
        with patch.dict(os.environ, {
            "ENABLE_VALIDATION_LAYER1": "true",
            "ENABLE_VALIDATION_LAYER2": "true",
            "ENABLE_VALIDATION_LAYER3": "true",
        }):
            # Reload module to pick up env changes
            if 'src.config.feature_flags' in sys.modules:
                importlib.reload(sys.modules['src.config.feature_flags'])

            from src.config.feature_flags import FeatureFlagManager

            manager = FeatureFlagManager()

            # All layers should be enabled
            assert manager.is_layer1_enabled is True, "Layer 1 should be enabled"
            assert manager.is_layer2_enabled is True, "Layer 2 should be enabled"
            assert manager.is_layer3_enabled is True, "Layer 3 should be enabled"

    def test_invalid_flag_values_treated_as_false(self):
        """
        Test that invalid flag values are treated as false (fail-safe).

        REQUIREMENT: NFR-R2 - Fail-safe flags with graceful degradation
        """
        invalid_values = ["1", "yes", "on", "enabled", "True1", "random", ""]

        for value in invalid_values:
            with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": value}):
                # Reload module to pick up env changes
                if 'src.config.feature_flags' in sys.modules:
                    importlib.reload(sys.modules['src.config.feature_flags'])

                from src.config.feature_flags import FeatureFlagManager

                manager = FeatureFlagManager()

                # Should be disabled for invalid values (fail-safe)
                assert manager.is_layer1_enabled is False, \
                    f"Layer 1 should be disabled for invalid value: '{value}'"

    def test_flag_manager_singleton_behavior(self):
        """
        Test that FeatureFlagManager implements singleton pattern.

        REQUIREMENT: Single instance across application
        """
        with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": "true"}):
            # Reload module to pick up env changes
            if 'src.config.feature_flags' in sys.modules:
                importlib.reload(sys.modules['src.config.feature_flags'])

            from src.config.feature_flags import FeatureFlagManager

            # Create two instances
            manager1 = FeatureFlagManager()
            manager2 = FeatureFlagManager()

            # Should be the same instance
            assert manager1 is manager2, \
                "FeatureFlagManager should return the same instance (singleton)"

            # Should have same flag values
            assert manager1.is_layer1_enabled == manager2.is_layer1_enabled, \
                "Singleton instances should have identical flag values"

    def test_false_string_value_treated_as_disabled(self):
        """
        Test that explicit "false" value disables the flag.

        REQUIREMENT: NFR-R2 - Explicit disable capability
        """
        with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": "false"}):
            # Reload module to pick up env changes
            if 'src.config.feature_flags' in sys.modules:
                importlib.reload(sys.modules['src.config.feature_flags'])

            from src.config.feature_flags import FeatureFlagManager

            manager = FeatureFlagManager()

            # Should be disabled
            assert manager.is_layer1_enabled is False, \
                "Layer 1 should be disabled when ENABLE_VALIDATION_LAYER1=false"

    def test_flag_properties_are_read_only(self):
        """
        Test that flag properties cannot be modified after initialization.

        REQUIREMENT: Immutable configuration for safety
        """
        with patch.dict(os.environ, {"ENABLE_VALIDATION_LAYER1": "true"}):
            # Reload module to pick up env changes
            if 'src.config.feature_flags' in sys.modules:
                importlib.reload(sys.modules['src.config.feature_flags'])

            from src.config.feature_flags import FeatureFlagManager

            manager = FeatureFlagManager()

            # Attempt to modify property should raise AttributeError
            with pytest.raises(AttributeError):
                manager.is_layer1_enabled = False
