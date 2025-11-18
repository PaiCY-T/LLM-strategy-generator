"""
Feature Flag Management for Validation Layers

Centralized feature flag system for managing validation layer rollout.

Requirements:
- AC1.4: ENABLE_VALIDATION_LAYER1 environment variable support
- NFR-R2: Fail-safe flags (default to false, graceful degradation)

Usage:
    from src.config.feature_flags import FeatureFlagManager

    manager = FeatureFlagManager()
    if manager.is_layer1_enabled:
        # Execute Layer 1 validation logic
        pass
"""

import os
from typing import Optional


class FeatureFlagManager:
    """Centralized feature flag management for validation layers.

    Implements fail-safe defaults (all flags default to False).
    Supports environment variable configuration for deployment flexibility.
    Uses singleton pattern to ensure consistent state across application.

    Environment Variables:
        ENABLE_VALIDATION_LAYER1: Enable DataFieldManifest validation (default: false)
        ENABLE_VALIDATION_LAYER2: Enable FieldValidator validation (default: false)
        ENABLE_VALIDATION_LAYER3: Enable SchemaValidator validation (default: false)

    Example:
        >>> manager = FeatureFlagManager()
        >>> if manager.is_layer1_enabled:
        ...     # Use Layer 1 validation
        ...     pass
    """

    _instance: Optional['FeatureFlagManager'] = None

    def __new__(cls):
        """Singleton pattern - ensure single instance.

        Returns:
            FeatureFlagManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize feature flags from environment variables.

        Flags are only initialized once (on first instantiation) to ensure
        consistent configuration throughout application lifecycle.
        """
        if not hasattr(self, '_initialized'):
            self._layer1_enabled = self._parse_bool_flag("ENABLE_VALIDATION_LAYER1")
            self._layer2_enabled = self._parse_bool_flag("ENABLE_VALIDATION_LAYER2")
            self._layer3_enabled = self._parse_bool_flag("ENABLE_VALIDATION_LAYER3")
            self._initialized = True

    @staticmethod
    def _parse_bool_flag(env_var_name: str) -> bool:
        """Parse boolean environment variable with fail-safe default.

        Only accepts "true" (case-insensitive) as enabled. All other values,
        including missing variables, are treated as disabled (fail-safe).

        Args:
            env_var_name: Name of environment variable to parse

        Returns:
            True if env var is "true" (case-insensitive), False otherwise

        Examples:
            >>> # ENABLE_VALIDATION_LAYER1=true
            >>> FeatureFlagManager._parse_bool_flag("ENABLE_VALIDATION_LAYER1")
            True

            >>> # ENABLE_VALIDATION_LAYER1=false
            >>> FeatureFlagManager._parse_bool_flag("ENABLE_VALIDATION_LAYER1")
            False

            >>> # ENABLE_VALIDATION_LAYER1 not set
            >>> FeatureFlagManager._parse_bool_flag("ENABLE_VALIDATION_LAYER1")
            False
        """
        value = os.getenv(env_var_name, "false")
        return value.lower() == "true"

    @property
    def is_layer1_enabled(self) -> bool:
        """Check if Layer 1 (DataFieldManifest) validation is enabled.

        Returns:
            True if ENABLE_VALIDATION_LAYER1=true, False otherwise
        """
        return self._layer1_enabled

    @property
    def is_layer2_enabled(self) -> bool:
        """Check if Layer 2 (FieldValidator) validation is enabled.

        Returns:
            True if ENABLE_VALIDATION_LAYER2=true, False otherwise
        """
        return self._layer2_enabled

    @property
    def is_layer3_enabled(self) -> bool:
        """Check if Layer 3 (SchemaValidator) validation is enabled.

        Returns:
            True if ENABLE_VALIDATION_LAYER3=true, False otherwise
        """
        return self._layer3_enabled
