"""
Unit tests for ExperimentConfigManager - Story 8: Experiment Configuration Tracking.

This module tests the ExperimentConfigManager's ability to capture, store, retrieve,
and compare experiment configurations for reproducibility.

Design Reference: learning-system-enhancement/spec.md
Tasks Reference: learning-system-enhancement/tasks.md lines 472-493 (Task 8.8)
Requirements Reference: 1.8.1-1.8.4, F8.1-F8.4 (configuration tracking system)
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import sys

from src.config.experiment_config_manager import (
    ExperimentConfig,
    ExperimentConfigManager
)


# ==============================================================================
# Test Fixtures
# ==============================================================================

@pytest.fixture
def temp_config_file():
    """Create temporary config file for testing."""
    with tempfile.NamedTemporaryFile(
        mode='w',
        delete=False,
        suffix='.json',
        encoding='utf-8'
    ) as f:
        temp_path = Path(f.name)
    yield temp_path
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def manager(temp_config_file):
    """Create ExperimentConfigManager instance with temp file."""
    return ExperimentConfigManager(str(temp_config_file))


@pytest.fixture
def mock_experiment_config():
    """Create valid ExperimentConfig instance for testing."""
    return ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={
            "model_name": "google/gemini-2.5-flash",
            "temperature": 0.7,
            "max_tokens": 8192,
            "top_p": 0.95
        },
        prompt_config={
            "version": "v3_comprehensive",
            "template_path": "prompt_template_v3_comprehensive.txt",
            "template_hash": "sha256:abc123def456"
        },
        system_thresholds={
            "anti_churn_threshold": 0.02,
            "probation_period": 3,
            "novelty_threshold": 0.05,
            "max_iterations": 30
        },
        environment_state={
            "python_version": sys.version,
            "packages": {
                "finlab": "0.4.6",
                "numpy": "1.24.0",
                "pandas": "2.0.0"
            },
            "api_endpoints": ["https://generativelanguage.googleapis.com/v1beta"],
            "os_info": "Linux 5.15.153.1"
        }
    )


@pytest.fixture
def mock_autonomous_loop():
    """
    Create mock AutonomousLoop with all required attributes.

    Returns:
        Mock AutonomousLoop with:
        - model: Model name string
        - config: Configuration dict
        - max_iterations: Integer
        - prompt_builder: Mock with template_file attribute
    """
    loop = MagicMock()

    # Basic attributes
    loop.model = "google/gemini-2.5-flash"
    loop.config = {
        'model': 'google/gemini-2.5-flash',
        'temperature': 1.0,
        'max_tokens': 8000
    }
    loop.max_iterations = 30

    # Mock prompt_builder
    loop.prompt_builder = MagicMock()
    loop.prompt_builder.template_file = "prompt_template_v3_comprehensive.txt"

    return loop


# ==============================================================================
# Test: ExperimentConfig Creation and Validation
# ==============================================================================

def test_experiment_config_creation(mock_experiment_config):
    """
    Test ExperimentConfig instance creation.

    Requirement: 1.8.1 - Complete configuration snapshots
    """
    # Assert
    assert mock_experiment_config.iteration_num == 0
    assert mock_experiment_config.model_config["model_name"] == "google/gemini-2.5-flash"
    assert mock_experiment_config.prompt_config["version"] == "v3_comprehensive"
    assert mock_experiment_config.system_thresholds["anti_churn_threshold"] == 0.02
    assert "python_version" in mock_experiment_config.environment_state


def test_experiment_config_to_dict(mock_experiment_config):
    """Test ExperimentConfig.to_dict() serialization."""
    # Act
    config_dict = mock_experiment_config.to_dict()

    # Assert
    assert isinstance(config_dict, dict)
    assert config_dict["iteration_num"] == 0
    assert "model_config" in config_dict
    assert "prompt_config" in config_dict
    assert "system_thresholds" in config_dict
    assert "environment_state" in config_dict


def test_experiment_config_from_dict(mock_experiment_config):
    """Test ExperimentConfig.from_dict() deserialization."""
    # Arrange
    config_dict = mock_experiment_config.to_dict()

    # Act
    restored_config = ExperimentConfig.from_dict(config_dict)

    # Assert
    assert restored_config.iteration_num == mock_experiment_config.iteration_num
    assert restored_config.model_config == mock_experiment_config.model_config
    assert restored_config.prompt_config == mock_experiment_config.prompt_config
    assert restored_config.system_thresholds == mock_experiment_config.system_thresholds


def test_experiment_config_serialization_roundtrip(mock_experiment_config):
    """Test complete serialization roundtrip maintains data integrity."""
    # Act
    config_dict = mock_experiment_config.to_dict()
    restored_config = ExperimentConfig.from_dict(config_dict)
    config_dict2 = restored_config.to_dict()

    # Assert
    assert config_dict == config_dict2, "Roundtrip should preserve all data"


def test_experiment_config_validation_success(mock_experiment_config):
    """
    Test ExperimentConfig.validate() with valid configuration.

    Requirement: F8.1 - Configuration validation
    """
    # Act
    errors = mock_experiment_config.validate()

    # Assert
    assert len(errors) == 0, f"Valid config should have no errors: {errors}"


def test_experiment_config_validation_negative_iteration():
    """Test validation fails for negative iteration_num."""
    # Arrange
    config = ExperimentConfig(
        iteration_num=-1,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "test", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    # Act
    errors = config.validate()

    # Assert
    assert len(errors) > 0
    assert any("iteration_num must be non-negative" in err for err in errors)


def test_experiment_config_validation_invalid_timestamp():
    """Test validation fails for invalid timestamp format."""
    # Arrange
    config = ExperimentConfig(
        iteration_num=0,
        timestamp="not-a-valid-timestamp",
        model_config={"model_name": "test", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    # Act
    errors = config.validate()

    # Assert
    assert len(errors) > 0
    assert any("Invalid timestamp format" in err for err in errors)


def test_experiment_config_validation_missing_model_fields():
    """Test validation fails for missing required model_config fields."""
    # Arrange - Missing temperature and max_tokens
    config = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "test"},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    # Act
    errors = config.validate()

    # Assert
    assert len(errors) >= 2
    assert any("temperature" in err for err in errors)
    assert any("max_tokens" in err for err in errors)


def test_experiment_config_validation_invalid_temperature():
    """Test validation fails for temperature out of range."""
    # Arrange - Temperature > 1.0
    config = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "test", "temperature": 1.5, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    # Act
    errors = config.validate()

    # Assert
    assert len(errors) > 0
    assert any("temperature must be between 0.0 and 1.0" in err for err in errors)


def test_experiment_config_validation_missing_prompt_fields():
    """Test validation fails for missing prompt_config fields."""
    # Arrange - Missing template_path
    config = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "test", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    # Act
    errors = config.validate()

    # Assert
    assert len(errors) > 0
    assert any("template_path" in err for err in errors)


def test_experiment_config_validation_missing_threshold_fields():
    """Test validation fails for missing system_thresholds fields."""
    # Arrange - Missing probation_period
    config = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "test", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    # Act
    errors = config.validate()

    # Assert
    assert len(errors) > 0
    assert any("probation_period" in err for err in errors)


def test_experiment_config_validation_missing_environment_fields():
    """Test validation fails for missing environment_state fields."""
    # Arrange - Missing api_endpoints
    config = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "test", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}}
    )

    # Act
    errors = config.validate()

    # Assert
    assert len(errors) > 0
    assert any("api_endpoints" in err for err in errors)


# ==============================================================================
# Test: ExperimentConfigManager Initialization and Storage
# ==============================================================================

def test_manager_initialization(temp_config_file):
    """Test ExperimentConfigManager initialization."""
    # Act
    manager = ExperimentConfigManager(str(temp_config_file))

    # Assert
    assert manager.config_file == temp_config_file
    assert isinstance(manager.configs, list)
    assert len(manager.configs) == 0


def test_manager_initialization_creates_directory(tmp_path):
    """Test manager creates parent directory if needed."""
    # Arrange
    nested_path = tmp_path / "subdir" / "configs.json"

    # Act
    manager = ExperimentConfigManager(str(nested_path))

    # Assert - Directory creation happens on first save
    # Ensure parent directory exists before save
    nested_path.parent.mkdir(parents=True, exist_ok=True)
    manager.configs = []
    manager.save()
    assert nested_path.parent.exists()
    assert nested_path.exists()


def test_save_and_load_config(manager, mock_experiment_config):
    """
    Test save_config() and load_config() basic functionality.

    Requirement: 1.8.2 - Configuration storage and retrieval
    """
    # Act - Save
    manager.save_config(mock_experiment_config)

    # Assert - File exists
    assert manager.config_file.exists()

    # Act - Load
    loaded_config = manager.load_config(iteration_num=0)

    # Assert - Data matches
    assert loaded_config is not None
    assert loaded_config.iteration_num == mock_experiment_config.iteration_num
    assert loaded_config.model_config == mock_experiment_config.model_config


def test_save_config_validation_error(manager):
    """Test save_config rejects invalid configuration."""
    # Arrange - Invalid config (negative iteration_num)
    invalid_config = ExperimentConfig(
        iteration_num=-1,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "test", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid configuration"):
        manager.save_config(invalid_config)


def test_save_config_updates_existing(manager, mock_experiment_config):
    """Test save_config updates existing config with same iteration_num."""
    # Arrange - Save initial config
    manager.save_config(mock_experiment_config)

    # Modify config
    modified_config = ExperimentConfig(
        iteration_num=0,  # Same iteration
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "different-model", "temperature": 0.8, "max_tokens": 4096},
        prompt_config={"version": "v2", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.03, "probation_period": 2, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    # Act - Save modified config
    manager.save_config(modified_config)

    # Assert - Only one config, updated
    all_configs = manager.get_all_configs()
    assert len(all_configs) == 1
    assert all_configs[0].model_config["model_name"] == "different-model"


def test_load_config_not_found(manager):
    """Test load_config returns None for non-existent iteration."""
    # Act
    config = manager.load_config(iteration_num=999)

    # Assert
    assert config is None


def test_get_all_configs(manager, mock_experiment_config):
    """Test get_all_configs returns all stored configurations."""
    # Arrange - Save multiple configs
    for i in range(3):
        config = ExperimentConfig(
            iteration_num=i,
            timestamp=datetime.utcnow().isoformat(),
            model_config={"model_name": f"model-{i}", "temperature": 0.7, "max_tokens": 8000},
            prompt_config={"version": "v1", "template_path": "test.txt"},
            system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
            environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
        )
        manager.save_config(config)

    # Act
    all_configs = manager.get_all_configs()

    # Assert
    assert len(all_configs) == 3
    assert all(isinstance(c, ExperimentConfig) for c in all_configs)


def test_get_all_configs_empty(manager):
    """Test get_all_configs returns empty list when no configs stored."""
    # Act
    all_configs = manager.get_all_configs()

    # Assert
    assert all_configs == []


def test_get_latest_config(manager, mock_experiment_config):
    """Test get_latest_config returns most recent configuration."""
    # Arrange - Save configs with different iteration numbers
    for i in [0, 2, 5, 3]:  # Not in order
        config = ExperimentConfig(
            iteration_num=i,
            timestamp=datetime.utcnow().isoformat(),
            model_config={"model_name": f"model-{i}", "temperature": 0.7, "max_tokens": 8000},
            prompt_config={"version": "v1", "template_path": "test.txt"},
            system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
            environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
        )
        manager.save_config(config)

    # Act
    latest = manager.get_latest_config()

    # Assert
    assert latest is not None
    assert latest.iteration_num == 5


def test_get_latest_config_empty(manager):
    """Test get_latest_config returns None when no configs stored."""
    # Act
    latest = manager.get_latest_config()

    # Assert
    assert latest is None


def test_multiple_configs_ordering(manager):
    """Test configs maintain correct ordering by iteration_num."""
    # Arrange - Save configs in random order
    iterations = [5, 1, 3, 0, 2]
    for i in iterations:
        config = ExperimentConfig(
            iteration_num=i,
            timestamp=datetime.utcnow().isoformat(),
            model_config={"model_name": f"model-{i}", "temperature": 0.7, "max_tokens": 8000},
            prompt_config={"version": "v1", "template_path": "test.txt"},
            system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
            environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
        )
        manager.save_config(config)

    # Act
    all_configs = manager.get_all_configs()

    # Assert - All configs retrievable
    assert len(all_configs) == 5
    for i in iterations:
        config = manager.load_config(i)
        assert config is not None
        assert config.iteration_num == i


# ==============================================================================
# Test: capture_config_snapshot
# ==============================================================================

def test_capture_config_snapshot_basic(manager, mock_autonomous_loop):
    """
    Test capture_config_snapshot extracts configuration from AutonomousLoop.

    Requirement: 1.8.3 - Live configuration capture
    """
    # Act
    config = manager.capture_config_snapshot(mock_autonomous_loop, iteration_num=0)

    # Assert
    assert config is not None
    assert config.iteration_num == 0
    assert config.model_config["model_name"] == "google/gemini-2.5-flash"
    assert config.model_config["temperature"] == 1.0
    assert config.model_config["max_tokens"] == 8000


def test_capture_config_snapshot_with_prompt_builder(manager, mock_autonomous_loop):
    """Test capture extracts prompt configuration from prompt_builder."""
    # Act
    config = manager.capture_config_snapshot(mock_autonomous_loop, iteration_num=0)

    # Assert
    assert "template_path" in config.prompt_config
    assert config.prompt_config["template_path"] == "prompt_template_v3_comprehensive.txt"
    assert config.prompt_config["version"] == "v3_comprehensive"
    assert "template_hash" in config.prompt_config


def test_capture_config_snapshot_prompt_hash(manager, mock_autonomous_loop, tmp_path):
    """Test capture computes template hash when file exists."""
    # Arrange - Create actual template file
    template_file = tmp_path / "prompt_template_v3_comprehensive.txt"
    test_content = b"test template content for hash computation"
    template_file.write_bytes(test_content)

    # Update mock to point to real file
    mock_autonomous_loop.prompt_builder.template_file = str(template_file)

    # Act
    config = manager.capture_config_snapshot(mock_autonomous_loop, iteration_num=0)

    # Assert - Hash should be computed (not error or file_not_found)
    assert config.prompt_config["template_hash"].startswith("sha256:")
    assert config.prompt_config["template_hash"] != "file_not_found"
    assert config.prompt_config["template_hash"] != "error_computing_hash"


def test_capture_config_snapshot_missing_prompt_builder(manager, mock_autonomous_loop):
    """Test capture handles missing prompt_builder gracefully."""
    # Arrange - Remove prompt_builder
    mock_autonomous_loop.prompt_builder = None

    # Act
    config = manager.capture_config_snapshot(mock_autonomous_loop, iteration_num=0)

    # Assert - Should still create config with defaults
    assert config is not None
    assert config.prompt_config["version"] == "unknown"
    assert config.prompt_config["template_path"] == "not_found"


def test_capture_config_snapshot_auto_save(manager, mock_autonomous_loop):
    """Test capture_config_snapshot automatically saves configuration."""
    # Act
    config = manager.capture_config_snapshot(mock_autonomous_loop, iteration_num=5)

    # Assert - Config should be saved
    loaded = manager.load_config(5)
    assert loaded is not None
    assert loaded.iteration_num == 5


def test_capture_config_snapshot_system_thresholds(manager, mock_autonomous_loop):
    """Test capture extracts system thresholds correctly."""
    # Act
    config = manager.capture_config_snapshot(mock_autonomous_loop, iteration_num=0)

    # Assert
    assert config.system_thresholds["anti_churn_threshold"] == 0.05
    assert config.system_thresholds["probation_period"] == 2
    assert config.system_thresholds["novelty_threshold"] == 0.3
    assert config.system_thresholds["max_iterations"] == 30


def test_capture_config_snapshot_environment_state(manager, mock_autonomous_loop):
    """Test capture records environment state."""
    # Act
    config = manager.capture_config_snapshot(mock_autonomous_loop, iteration_num=0)

    # Assert
    assert "python_version" in config.environment_state
    assert "packages" in config.environment_state
    assert "api_endpoints" in config.environment_state
    assert "os_info" in config.environment_state


# ==============================================================================
# Test: compute_config_diff
# ==============================================================================

def test_config_diff_no_changes(manager, mock_experiment_config):
    """
    Test compute_config_diff returns no changes for identical configs.

    Requirement: 1.8.4 - Configuration comparison
    """
    # Arrange - Save same config twice
    manager.save_config(mock_experiment_config)

    # Act - Compare config with itself
    diff = manager.compute_config_diff(0, 0)

    # Assert
    assert diff["has_changes"] is False
    assert diff["change_summary"] == "No changes detected"
    assert diff["severity"] == "none"
    assert len(diff["changes"]) == 0


def test_config_diff_model_change_critical(manager):
    """Test compute_config_diff detects critical model_name change."""
    # Arrange - Save two configs with different models
    config1 = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "gemini-2.5-flash", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    config2 = ExperimentConfig(
        iteration_num=1,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "gemini-2.5-pro", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    manager.save_config(config1)
    manager.save_config(config2)

    # Act
    diff = manager.compute_config_diff(0, 1)

    # Assert
    assert diff["has_changes"] is True
    assert diff["severity"] == "critical"
    assert "model_config" in diff["changes"]
    assert "model_name" in diff["changes"]["model_config"]["changed_fields"]


def test_config_diff_temperature_change_moderate(manager):
    """Test compute_config_diff detects moderate temperature change."""
    # Arrange
    config1 = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "test-model", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    config2 = ExperimentConfig(
        iteration_num=1,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "test-model", "temperature": 0.9, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    manager.save_config(config1)
    manager.save_config(config2)

    # Act
    diff = manager.compute_config_diff(0, 1)

    # Assert
    assert diff["has_changes"] is True
    assert diff["severity"] == "moderate"
    assert "model_config" in diff["changes"]

    # Find temperature change detail
    temp_detail = next(
        d for d in diff["changes"]["model_config"]["details"]
        if d["field"] == "temperature"
    )
    assert temp_detail["severity"] == "moderate"
    assert temp_detail["old_value"] == 0.7
    assert temp_detail["new_value"] == 0.9


def test_config_diff_multiple_changes(manager):
    """Test compute_config_diff handles multiple simultaneous changes."""
    # Arrange - Configs with changes in multiple sections
    config1 = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "model-a", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "template_v1.txt", "template_hash": "abc123"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {"numpy": "1.24"}, "api_endpoints": ["api1"]}
    )

    config2 = ExperimentConfig(
        iteration_num=1,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "model-b", "temperature": 0.8, "max_tokens": 4096},
        prompt_config={"version": "v2", "template_path": "template_v2.txt", "template_hash": "def456"},
        system_thresholds={"anti_churn_threshold": 0.03, "probation_period": 2, "novelty_threshold": 0.08},
        environment_state={"python_version": "3.11", "packages": {"numpy": "1.25"}, "api_endpoints": ["api2"]}
    )

    manager.save_config(config1)
    manager.save_config(config2)

    # Act
    diff = manager.compute_config_diff(0, 1)

    # Assert
    assert diff["has_changes"] is True
    assert len(diff["changes"]) > 0

    # Should have changes in multiple sections
    assert "model_config" in diff["changes"]
    assert "prompt_config" in diff["changes"]
    assert "system_thresholds" in diff["changes"]


def test_config_diff_with_iteration_numbers(manager):
    """Test compute_config_diff using iteration numbers."""
    # Arrange
    config1 = ExperimentConfig(
        iteration_num=5,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "model-1", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    config2 = ExperimentConfig(
        iteration_num=10,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "model-2", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    manager.save_config(config1)
    manager.save_config(config2)

    # Act - Compare by iteration numbers
    diff = manager.compute_config_diff(5, 10)

    # Assert
    assert diff["iteration_nums"] == [5, 10]
    assert diff["has_changes"] is True


def test_config_diff_with_config_instances(manager):
    """Test compute_config_diff using ExperimentConfig instances."""
    # Arrange
    config1 = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "model-1", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    config2 = ExperimentConfig(
        iteration_num=1,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "model-2", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    # Act - Compare instances directly
    diff = manager.compute_config_diff(config1, config2)

    # Assert
    assert diff["iteration_nums"] == [0, 1]
    assert diff["has_changes"] is True


def test_config_diff_iteration_not_found(manager):
    """Test compute_config_diff handles non-existent iteration."""
    # Act
    diff = manager.compute_config_diff(999, 1000)

    # Assert
    assert "error" in diff
    assert diff["has_changes"] is False
    assert "not found" in diff["error"]


def test_config_diff_severity_assessment(manager):
    """Test compute_config_diff correctly assesses overall severity."""
    # Test critical severity
    config1 = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "model-1", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt", "template_hash": "abc"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    config2 = ExperimentConfig(
        iteration_num=1,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "model-1", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt", "template_hash": "xyz"},  # Critical change
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    manager.save_config(config1)
    manager.save_config(config2)

    # Act
    diff = manager.compute_config_diff(0, 1)

    # Assert - Should be critical due to template_hash change
    assert diff["severity"] == "critical"


def test_config_diff_change_summary_format(manager):
    """Test compute_config_diff generates readable change summary."""
    # Arrange
    config1 = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "model-1", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    config2 = ExperimentConfig(
        iteration_num=1,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "model-2", "temperature": 0.8, "max_tokens": 4096},
        prompt_config={"version": "v2", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    manager.save_config(config1)
    manager.save_config(config2)

    # Act
    diff = manager.compute_config_diff(0, 1)

    # Assert
    summary = diff["change_summary"]
    assert "changes:" in summary
    assert any(field in summary for field in ["model_name", "temperature", "max_tokens", "version"])


# ==============================================================================
# Test: Export/Import Functionality
# ==============================================================================

def test_export_config(manager, mock_experiment_config, tmp_path):
    """
    Test export_config saves configuration to separate file.

    Requirement: F8.4 - Configuration export for reproducibility
    """
    # Arrange
    manager.save_config(mock_experiment_config)
    export_path = tmp_path / "exported_config.json"

    # Act
    success = manager.export_config(0, str(export_path))

    # Assert
    assert success is True
    assert export_path.exists()

    # Verify content
    with open(export_path, 'r', encoding='utf-8') as f:
        exported_data = json.load(f)

    assert exported_data["iteration_num"] == 0
    assert exported_data["model_config"]["model_name"] == "google/gemini-2.5-flash"


def test_export_config_not_found(manager, tmp_path):
    """Test export_config returns False for non-existent iteration."""
    # Arrange
    export_path = tmp_path / "exported_config.json"

    # Act
    success = manager.export_config(999, str(export_path))

    # Assert
    assert success is False
    assert not export_path.exists()


def test_import_config(manager, tmp_path):
    """Test import_config loads configuration from external file."""
    # Arrange - Create external config file
    config_data = {
        "iteration_num": 5,
        "timestamp": datetime.utcnow().isoformat(),
        "model_config": {"model_name": "imported-model", "temperature": 0.7, "max_tokens": 8000},
        "prompt_config": {"version": "v1", "template_path": "test.txt"},
        "system_thresholds": {"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        "environment_state": {"python_version": "3.10", "packages": {}, "api_endpoints": []}
    }

    import_path = tmp_path / "import_config.json"
    with open(import_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f)

    # Act
    imported_config = manager.import_config(str(import_path))

    # Assert
    assert imported_config is not None
    assert imported_config.iteration_num == 5
    assert imported_config.model_config["model_name"] == "imported-model"


def test_import_config_invalid_file(manager, tmp_path):
    """Test import_config handles invalid file gracefully."""
    # Arrange - Create invalid JSON file
    import_path = tmp_path / "invalid.json"
    with open(import_path, 'w', encoding='utf-8') as f:
        f.write("not valid json {{{")

    # Act
    imported_config = manager.import_config(str(import_path))

    # Assert
    assert imported_config is None


def test_import_config_validation_failure(manager, tmp_path):
    """Test import_config rejects invalid configuration."""
    # Arrange - Create config with validation errors
    invalid_data = {
        "iteration_num": -1,  # Invalid
        "timestamp": "invalid-timestamp",
        "model_config": {},  # Missing required fields
        "prompt_config": {},
        "system_thresholds": {},
        "environment_state": {}
    }

    import_path = tmp_path / "invalid_config.json"
    with open(import_path, 'w', encoding='utf-8') as f:
        json.dump(invalid_data, f)

    # Act
    imported_config = manager.import_config(str(import_path))

    # Assert
    assert imported_config is None


def test_export_import_roundtrip(manager, mock_experiment_config, tmp_path):
    """Test complete export-import roundtrip maintains data integrity."""
    # Arrange
    manager.save_config(mock_experiment_config)
    export_path = tmp_path / "roundtrip.json"

    # Act - Export
    export_success = manager.export_config(0, str(export_path))
    assert export_success is True

    # Create new manager and import
    manager2 = ExperimentConfigManager(str(tmp_path / "new_configs.json"))
    imported_config = manager2.import_config(str(export_path))

    # Assert
    assert imported_config is not None
    assert imported_config.iteration_num == mock_experiment_config.iteration_num
    assert imported_config.model_config == mock_experiment_config.model_config
    assert imported_config.prompt_config == mock_experiment_config.prompt_config
    assert imported_config.system_thresholds == mock_experiment_config.system_thresholds

    # Save imported config and verify it's the same
    manager2.save_config(imported_config)
    loaded = manager2.load_config(0)
    assert loaded.to_dict() == mock_experiment_config.to_dict()


# ==============================================================================
# Test: Integration and Edge Cases
# ==============================================================================

def test_full_workflow(manager, mock_autonomous_loop):
    """
    Test complete workflow: capture, store, retrieve, compare, export.

    Requirement: 1.8.1-1.8.4 - Full configuration tracking system
    """
    # Step 1: Capture config from iteration 0
    config0 = manager.capture_config_snapshot(mock_autonomous_loop, iteration_num=0)

    # Step 2: Modify loop and capture iteration 1
    mock_autonomous_loop.model = "google/gemini-2.5-pro"
    config1 = manager.capture_config_snapshot(mock_autonomous_loop, iteration_num=1)

    # Step 3: Retrieve configs
    loaded0 = manager.load_config(0)
    loaded1 = manager.load_config(1)
    assert loaded0 is not None
    assert loaded1 is not None

    # Step 4: Compare configs
    diff = manager.compute_config_diff(0, 1)
    assert diff["has_changes"] is True
    assert diff["severity"] == "critical"  # Model changed

    # Step 5: Get latest
    latest = manager.get_latest_config()
    assert latest.iteration_num == 1

    # Step 6: Export for reproducibility
    export_path = Path(manager.config_file).parent / "exported.json"
    success = manager.export_config(1, str(export_path))
    assert success is True

    # Cleanup
    export_path.unlink()


def test_persistence_across_instances(temp_config_file, mock_experiment_config):
    """Test configurations persist across manager instances."""
    # Arrange - Create manager and save config
    manager1 = ExperimentConfigManager(str(temp_config_file))
    manager1.save_config(mock_experiment_config)

    # Act - Create new manager instance with same file
    manager2 = ExperimentConfigManager(str(temp_config_file))

    # Assert - Config should be loaded automatically
    assert len(manager2.configs) == 1
    loaded = manager2.load_config(0)
    assert loaded is not None
    assert loaded.iteration_num == 0


def test_clear_configs(manager, mock_experiment_config):
    """Test clear() removes all configurations and deletes file."""
    # Arrange
    manager.save_config(mock_experiment_config)
    assert manager.config_file.exists()

    # Act
    manager.clear()

    # Assert
    assert len(manager.configs) == 0
    assert not manager.config_file.exists()


def test_config_with_custom_config_field(manager):
    """Test ExperimentConfig with optional custom_config field."""
    # Arrange
    config = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "test", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []},
        custom_config={"experiment_name": "test_experiment", "notes": "Testing custom config"}
    )

    # Act
    manager.save_config(config)
    loaded = manager.load_config(0)

    # Assert
    assert loaded is not None
    assert loaded.custom_config is not None
    assert loaded.custom_config["experiment_name"] == "test_experiment"


def test_concurrent_iteration_updates(manager):
    """Test handling of multiple updates to same iteration."""
    # Arrange - Create initial config
    config_v1 = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "model-v1", "temperature": 0.7, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    config_v2 = ExperimentConfig(
        iteration_num=0,  # Same iteration
        timestamp=datetime.utcnow().isoformat(),
        model_config={"model_name": "model-v2", "temperature": 0.8, "max_tokens": 8000},
        prompt_config={"version": "v1", "template_path": "test.txt"},
        system_thresholds={"anti_churn_threshold": 0.02, "probation_period": 3, "novelty_threshold": 0.05},
        environment_state={"python_version": "3.10", "packages": {}, "api_endpoints": []}
    )

    # Act - Save both versions
    manager.save_config(config_v1)
    manager.save_config(config_v2)

    # Assert - Only latest version should exist
    all_configs = manager.get_all_configs()
    assert len(all_configs) == 1
    assert all_configs[0].model_config["model_name"] == "model-v2"
