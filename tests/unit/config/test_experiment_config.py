"""
Unit tests for ExperimentConfig module - Test-First Approach

This test file is created BEFORE the implementation as part of test-driven development.
These tests are EXPECTED TO FAIL until Task 3.2 implements the ExperimentConfig module.

Test Coverage:
    - ExperimentConfig dataclass creation with required fields
    - from_dict() class method deserialization
    - to_dict() instance method serialization
    - Optional timestamp field defaults to None
    - Round-trip conversion (from_dict -> to_dict -> from_dict)

Bug Context:
    - Bug #3: ExperimentConfig module does not exist
    - Import fails every iteration, breaking config snapshot functionality
    - These tests will fail with ImportError until module is implemented

Expected Module Design:
    @dataclass
    class ExperimentConfig:
        iteration: int
        config_snapshot: Dict[str, Any]
        timestamp: Optional[str] = None
"""

import pytest
from typing import Dict, Any


class TestExperimentConfig:
    """Test suite for ExperimentConfig dataclass."""

    def test_experiment_config_creation(self):
        """Test creating ExperimentConfig instance with required fields.

        Verifies that:
        - ExperimentConfig can be instantiated with iteration and config_snapshot
        - Fields are accessible as instance attributes
        - Field types match expected types

        Expected behavior:
            config = ExperimentConfig(
                iteration=5,
                config_snapshot={"param1": "value1", "param2": 42}
            )
            assert config.iteration == 5
            assert config.config_snapshot == {"param1": "value1", "param2": 42}
            assert config.timestamp is None  # default value
        """
        from src.config.experiment_config import ExperimentConfig

        # Create instance with required fields
        config = ExperimentConfig(
            iteration=5,
            config_snapshot={"param1": "value1", "param2": 42}
        )

        # Verify fields are set correctly
        assert config.iteration == 5
        assert config.config_snapshot == {"param1": "value1", "param2": 42}
        assert config.timestamp is None  # default value

    def test_experiment_config_with_timestamp(self):
        """Test creating ExperimentConfig instance with optional timestamp field.

        Verifies that:
        - timestamp field can be explicitly set
        - timestamp field accepts string values
        - All fields are accessible

        Expected behavior:
            config = ExperimentConfig(
                iteration=10,
                config_snapshot={"key": "value"},
                timestamp="2024-11-02T09:00:00"
            )
            assert config.timestamp == "2024-11-02T09:00:00"
        """
        from src.config.experiment_config import ExperimentConfig

        # Create instance with timestamp
        config = ExperimentConfig(
            iteration=10,
            config_snapshot={"key": "value"},
            timestamp="2024-11-02T09:00:00"
        )

        # Verify all fields including timestamp
        assert config.iteration == 10
        assert config.config_snapshot == {"key": "value"}
        assert config.timestamp == "2024-11-02T09:00:00"

    def test_experiment_config_from_dict(self):
        """Test from_dict() class method creates instance from dictionary.

        Verifies that:
        - from_dict() class method exists
        - Method accepts a dictionary with matching field names
        - Returns ExperimentConfig instance
        - All fields are correctly populated from dictionary

        Expected behavior:
            config_dict = {
                "iteration": 3,
                "config_snapshot": {"a": 1, "b": 2},
                "timestamp": "2024-11-02"
            }
            config = ExperimentConfig.from_dict(config_dict)
            assert isinstance(config, ExperimentConfig)
            assert config.iteration == 3
        """
        from src.config.experiment_config import ExperimentConfig

        # Create config from dictionary
        config_dict = {
            "iteration": 3,
            "config_snapshot": {"a": 1, "b": 2},
            "timestamp": "2024-11-02T10:30:00"
        }

        config = ExperimentConfig.from_dict(config_dict)

        # Verify instance is created correctly
        assert isinstance(config, ExperimentConfig)
        assert config.iteration == 3
        assert config.config_snapshot == {"a": 1, "b": 2}
        assert config.timestamp == "2024-11-02T10:30:00"

    def test_experiment_config_to_dict(self):
        """Test to_dict() instance method returns correct dictionary.

        Verifies that:
        - to_dict() instance method exists
        - Method returns a dictionary
        - Dictionary contains all fields as keys
        - Dictionary values match instance attribute values

        Expected behavior:
            config = ExperimentConfig(iteration=7, config_snapshot={"x": 10})
            result = config.to_dict()
            assert result == {
                "iteration": 7,
                "config_snapshot": {"x": 10},
                "timestamp": None
            }
        """
        from src.config.experiment_config import ExperimentConfig

        # Create instance
        config = ExperimentConfig(
            iteration=7,
            config_snapshot={"x": 10, "y": 20},
            timestamp="2024-11-02"
        )

        # Convert to dictionary
        result = config.to_dict()

        # Verify dictionary structure and values
        assert isinstance(result, dict)
        assert result["iteration"] == 7
        assert result["config_snapshot"] == {"x": 10, "y": 20}
        assert result["timestamp"] == "2024-11-02"

    def test_experiment_config_roundtrip(self):
        """Test from_dict(config.to_dict()) round-trip conversion works.

        Verifies that:
        - Converting to dict and back preserves all data
        - No data loss during serialization/deserialization
        - Result equals original instance

        Expected behavior:
            original = ExperimentConfig(
                iteration=15,
                config_snapshot={"test": "data"},
                timestamp="2024-11-02"
            )
            restored = ExperimentConfig.from_dict(original.to_dict())
            assert restored.iteration == original.iteration
            assert restored.config_snapshot == original.config_snapshot
            assert restored.timestamp == original.timestamp
        """
        from src.config.experiment_config import ExperimentConfig

        # Create original instance
        original = ExperimentConfig(
            iteration=15,
            config_snapshot={"test": "data", "nested": {"key": "value"}},
            timestamp="2024-11-02T12:00:00"
        )

        # Round-trip: to_dict() -> from_dict()
        config_dict = original.to_dict()
        restored = ExperimentConfig.from_dict(config_dict)

        # Verify data is preserved
        assert restored.iteration == original.iteration
        assert restored.config_snapshot == original.config_snapshot
        assert restored.timestamp == original.timestamp

    def test_experiment_config_optional_timestamp(self):
        """Test optional timestamp field defaults to None.

        Verifies that:
        - timestamp field is optional (has default value)
        - Default value is None
        - Can create instance without providing timestamp
        - to_dict() includes timestamp=None in result

        Expected behavior:
            config = ExperimentConfig(iteration=1, config_snapshot={})
            assert config.timestamp is None

            result = config.to_dict()
            assert "timestamp" in result
            assert result["timestamp"] is None
        """
        from src.config.experiment_config import ExperimentConfig

        # Create instance without timestamp
        config = ExperimentConfig(
            iteration=1,
            config_snapshot={"minimal": "config"}
        )

        # Verify timestamp defaults to None
        assert config.timestamp is None

        # Verify to_dict() includes timestamp field
        result = config.to_dict()
        assert "timestamp" in result
        assert result["timestamp"] is None

    def test_experiment_config_complex_snapshot(self):
        """Test ExperimentConfig handles complex nested config_snapshot.

        Verifies that:
        - config_snapshot can contain nested dictionaries
        - config_snapshot can contain lists
        - config_snapshot can contain mixed types
        - Complex data structures are preserved in round-trip

        Expected behavior:
            complex_snapshot = {
                "nested": {"level1": {"level2": "value"}},
                "list": [1, 2, 3],
                "mixed": {"a": [1, 2], "b": {"c": 3}}
            }
            config = ExperimentConfig(iteration=99, config_snapshot=complex_snapshot)
            assert config.config_snapshot["nested"]["level1"]["level2"] == "value"
        """
        from src.config.experiment_config import ExperimentConfig

        # Create complex config snapshot
        complex_snapshot = {
            "nested": {"level1": {"level2": "value"}},
            "list": [1, 2, 3],
            "mixed": {"a": [1, 2], "b": {"c": 3}},
            "string": "test",
            "number": 42,
            "float": 3.14
        }

        # Create instance with complex snapshot
        config = ExperimentConfig(
            iteration=99,
            config_snapshot=complex_snapshot
        )

        # Verify complex data is accessible
        assert config.config_snapshot["nested"]["level1"]["level2"] == "value"
        assert config.config_snapshot["list"] == [1, 2, 3]
        assert config.config_snapshot["mixed"]["b"]["c"] == 3

        # Verify round-trip preserves complex data
        restored = ExperimentConfig.from_dict(config.to_dict())
        assert restored.config_snapshot == complex_snapshot
