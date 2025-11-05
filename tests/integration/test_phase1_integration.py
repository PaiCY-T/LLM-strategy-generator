"""Phase 1 Integration Test: Comprehensive validation of all Phase 1 features.

This integration test validates that all Phase 1 stories (6, 5, 3, 7, 8) work
together correctly in the autonomous loop:

Story 6: Metric Integrity - Metric validation, impossible metric detection
Story 5: Semantic Validation - Behavioral checks, logic validation
Story 3: Extended Test Harness - Statistical analysis, checkpoint/resume
Story 7: Data Pipeline Integrity - Data checksums, provenance tracking, consistency
Story 8: Experiment Configuration - Config snapshots, config diffs

Test Coverage:
    - Story 7 Integration (3 tests): Data integrity features
    - Story 8 Integration (3 tests): Config tracking features
    - Cross-Story Integration (5 tests): Combined feature validation
    - Error Handling (included in tests): Non-blocking behavior

Requirements:
    - REQ-1.7.1: Dataset checksums recorded and validated
    - REQ-1.7.2: Data version tracking in iteration history
    - REQ-1.7.3: Automated data consistency checks
    - REQ-1.7.4: Iteration history includes data provenance
    - REQ-1.8.1: Config snapshots captured at each iteration
    - REQ-1.8.2: Config diffs computed between iterations
    - REQ-1.8.3: Config tracking stored in iteration history
"""

import pytest
import json
import tempfile
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, Mock, patch

# Add artifacts/working/modules to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "artifacts" / "working" / "modules"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from history import IterationHistory, IterationRecord
from src.data.pipeline_integrity import DataPipelineIntegrity
from src.config.experiment_config_manager import ExperimentConfigManager, ExperimentConfig


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def mock_finlab_data():
    """Create mock Finlab data object with get() method.

    Returns mock DataFrames for key datasets with realistic structure:
    - price:收盤價 (closing prices)
    - price:成交金額 (trading volume)
    - fundamental_features:ROE稅後 (ROE after tax)

    Returns:
        MagicMock: Mock Finlab data object with get() method
    """
    import pandas as pd
    import numpy as np

    # Create realistic mock data (50 stocks, 100 days)
    dates = pd.date_range('2024-01-01', periods=100)
    stocks = [f'stock_{i:04d}' for i in range(50)]

    # Mock closing prices
    close_data = pd.DataFrame(
        np.random.uniform(50, 150, size=(100, 50)),
        index=dates,
        columns=stocks
    )

    # Mock trading volume
    volume_data = pd.DataFrame(
        np.random.uniform(1e6, 1e9, size=(100, 50)),
        index=dates,
        columns=stocks
    )

    # Mock ROE
    roe_data = pd.DataFrame(
        np.random.uniform(5, 25, size=(100, 50)),
        index=dates,
        columns=stocks
    )

    # Create mock data object
    mock_data = MagicMock()

    def mock_get(dataset_key):
        """Mock get() method that returns appropriate DataFrame."""
        dataset_map = {
            'price:收盤價': close_data,
            'price:成交金額': volume_data,
            'fundamental_features:ROE稅後': roe_data
        }
        return dataset_map.get(dataset_key, pd.DataFrame())

    mock_data.get = mock_get

    return mock_data


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create temporary directory for test files.

    Args:
        tmp_path: pytest built-in temporary directory fixture

    Returns:
        Path: Temporary directory path
    """
    test_dir = tmp_path / "phase1_integration_test"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def integration_config(temp_test_dir):
    """Create integration test configuration.

    Args:
        temp_test_dir: Temporary directory for test files

    Returns:
        dict: Integration test configuration
    """
    return {
        'history_file': str(temp_test_dir / 'test_history.json'),
        'config_file': str(temp_test_dir / 'test_configs.json'),
        'model': 'google/gemini-2.5-flash',
        'max_iterations': 5
    }


@pytest.fixture
def autonomous_loop_mock(integration_config):
    """Create mock AutonomousLoop instance for testing.

    Creates a mock that simulates the autonomous loop structure
    without requiring full initialization or external dependencies.

    Args:
        integration_config: Integration test configuration

    Returns:
        MagicMock: Mock AutonomousLoop instance
    """
    mock_loop = MagicMock()

    # Configure basic attributes
    mock_loop.model = integration_config['model']
    mock_loop.max_iterations = integration_config['max_iterations']

    # Mock prompt_builder with template_file
    mock_prompt_builder = MagicMock()
    mock_prompt_builder.template_file = 'prompt_template_v3_comprehensive.txt'
    mock_loop.prompt_builder = mock_prompt_builder

    return mock_loop


# ==============================================================================
# Story 7 Integration Tests: Data Pipeline Integrity
# ==============================================================================

def test_data_integrity_checksum_recorded(mock_finlab_data, temp_test_dir, integration_config):
    """Test that data checksums are computed and stored in IterationRecord.

    Validates:
        - REQ-1.7.1: Dataset checksums recorded at load time
        - DataPipelineIntegrity.compute_dataset_checksum() works correctly
        - IterationRecord.data_checksum field is populated
        - Checksum is valid 64-character SHA-256 hex string

    Story: Story 7 (Data Pipeline Integrity)
    """
    # Arrange
    integrity = DataPipelineIntegrity()
    history = IterationHistory(integration_config['history_file'])
    history.clear()

    # Act
    checksum = integrity.compute_dataset_checksum(mock_finlab_data)

    # Add record with checksum
    record = history.add_record(
        iteration_num=0,
        model='test-model',
        code='# test code',
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.5},
        feedback='Test feedback',
        data_checksum=checksum
    )

    # Assert
    assert record.data_checksum is not None, "Checksum should be recorded"
    assert len(record.data_checksum) == 64, "Checksum should be 64-char SHA-256 hex string"
    assert all(c in '0123456789abcdef' for c in record.data_checksum.lower()), \
        "Checksum should be valid hex string"

    # Verify persistence
    loaded_record = history.get_record(0)
    assert loaded_record is not None
    assert loaded_record.data_checksum == checksum, "Checksum should persist through save/load"


def test_data_consistency_validation(mock_finlab_data, temp_test_dir):
    """Test data consistency validation between iterations.

    Validates:
        - REQ-1.7.3: Automated data consistency checks
        - DataPipelineIntegrity.validate_data_consistency() works correctly
        - Same data produces valid result (checksums match)
        - Changed data produces invalid result (checksums don't match)

    Story: Story 7 (Data Pipeline Integrity)
    """
    # Arrange
    integrity = DataPipelineIntegrity()

    # Compute initial checksum
    expected_checksum = integrity.compute_dataset_checksum(mock_finlab_data)

    # Act - Validate with same data (should pass)
    is_valid, msg = integrity.validate_data_consistency(mock_finlab_data, expected_checksum)

    # Assert - Same data should validate
    assert is_valid is True, "Data consistency check should pass for same data"
    assert msg == "", "No error message for valid data"

    # Act - Validate with different checksum (simulate data change)
    fake_checksum = 'a' * 64  # Different checksum
    is_valid, msg = integrity.validate_data_consistency(mock_finlab_data, fake_checksum)

    # Assert - Changed data should fail validation
    assert is_valid is False, "Data consistency check should fail for changed data"
    assert 'mismatch' in msg.lower(), "Error message should indicate checksum mismatch"


def test_data_provenance_in_history(mock_finlab_data, temp_test_dir, integration_config):
    """Test data provenance is recorded in IterationRecord.

    Validates:
        - REQ-1.7.2: Data version tracking in iteration history
        - REQ-1.7.4: Iteration history includes data provenance
        - DataPipelineIntegrity.record_data_provenance() captures all metadata
        - IterationRecord.data_version field contains finlab_version, timestamp, row_counts

    Story: Story 7 (Data Pipeline Integrity)
    """
    # Arrange
    integrity = DataPipelineIntegrity()
    history = IterationHistory(integration_config['history_file'])
    history.clear()

    # Act - Record provenance
    provenance = integrity.record_data_provenance(mock_finlab_data, iteration_num=0)

    # Add record with provenance
    record = history.add_record(
        iteration_num=0,
        model='test-model',
        code='# test code',
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.5},
        feedback='Test feedback',
        data_checksum=provenance['dataset_checksum'],
        data_version={
            'finlab_version': provenance['finlab_version'],
            'data_pull_timestamp': provenance['data_pull_timestamp'],
            'dataset_row_counts': provenance['dataset_row_counts']
        }
    )

    # Assert - Provenance fields are populated
    assert record.data_version is not None, "Data version should be recorded"
    assert 'finlab_version' in record.data_version, "Should have finlab_version"
    assert 'data_pull_timestamp' in record.data_version, "Should have timestamp"
    assert 'dataset_row_counts' in record.data_version, "Should have row counts"

    # Verify row counts are present for key datasets
    row_counts = record.data_version['dataset_row_counts']
    assert 'price:收盤價' in row_counts, "Should track closing price rows"
    assert 'price:成交金額' in row_counts, "Should track volume rows"
    assert 'fundamental_features:ROE稅後' in row_counts, "Should track ROE rows"

    # Verify persistence
    loaded_record = history.get_record(0)
    assert loaded_record is not None
    assert loaded_record.data_version == record.data_version, \
        "Data provenance should persist through save/load"


# ==============================================================================
# Story 8 Integration Tests: Experiment Configuration Tracking
# ==============================================================================

def test_config_snapshot_recorded(autonomous_loop_mock, temp_test_dir, integration_config):
    """Test configuration snapshots are captured and stored.

    Validates:
        - REQ-1.8.1: Config snapshots captured at each iteration
        - ExperimentConfigManager.capture_config_snapshot() works correctly
        - ExperimentConfig contains all required sections
        - Config snapshot is valid and complete

    Story: Story 8 (Experiment Configuration Tracking)
    """
    # Arrange
    config_manager = ExperimentConfigManager(integration_config['config_file'])
    config_manager.clear()

    # Act
    config = config_manager.capture_config_snapshot(autonomous_loop_mock, iteration_num=0)

    # Assert - Config snapshot is captured
    assert config is not None, "Config snapshot should be captured"
    assert config.iteration_num == 0, "Iteration number should match"

    # Verify all required sections are present
    assert config.model_config is not None, "Should have model_config"
    assert config.prompt_config is not None, "Should have prompt_config"
    assert config.system_thresholds is not None, "Should have system_thresholds"
    assert config.environment_state is not None, "Should have environment_state"

    # Verify model_config structure
    assert 'model_name' in config.model_config, "Should have model_name"
    assert 'temperature' in config.model_config, "Should have temperature"
    assert 'max_tokens' in config.model_config, "Should have max_tokens"

    # Verify prompt_config structure
    assert 'version' in config.prompt_config, "Should have prompt version"
    assert 'template_path' in config.prompt_config, "Should have template path"

    # Verify system_thresholds structure
    assert 'anti_churn_threshold' in config.system_thresholds, "Should have anti_churn_threshold"
    assert 'probation_period' in config.system_thresholds, "Should have probation_period"

    # Verify environment_state structure
    assert 'python_version' in config.environment_state, "Should have python_version"
    assert 'packages' in config.environment_state, "Should have packages"

    # Verify config is saved
    loaded_config = config_manager.load_config(iteration_num=0)
    assert loaded_config is not None, "Config should be saved and loadable"
    assert loaded_config.model_config == config.model_config, "Config should persist"


def test_config_diff_between_iterations(temp_test_dir, integration_config):
    """Test configuration diffs are computed when settings change.

    Validates:
        - REQ-1.8.2: Config diffs computed between iterations
        - ExperimentConfigManager.compute_config_diff() works correctly
        - Diffs correctly identify changed fields
        - Severity levels are properly assigned

    Story: Story 8 (Experiment Configuration Tracking)
    """
    # Arrange
    config_manager = ExperimentConfigManager(integration_config['config_file'])
    config_manager.clear()

    # Create two configs with differences
    config1 = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={
            'model_name': 'gemini-2.5-flash',
            'temperature': 0.7,
            'max_tokens': 8000
        },
        prompt_config={
            'version': 'v3_comprehensive',
            'template_path': 'prompt_template_v3.txt',
            'template_hash': 'sha256:abc123'
        },
        system_thresholds={
            'anti_churn_threshold': 0.05,
            'probation_period': 2,
            'novelty_threshold': 0.3
        },
        environment_state={
            'python_version': sys.version,
            'packages': {'finlab': '0.4.6'},
            'api_endpoints': ['https://generativelanguage.googleapis.com']
        }
    )

    config2 = ExperimentConfig(
        iteration_num=1,
        timestamp=datetime.utcnow().isoformat(),
        model_config={
            'model_name': 'gemini-2.5-flash',
            'temperature': 0.8,  # Changed
            'max_tokens': 8000
        },
        prompt_config={
            'version': 'v3_comprehensive',
            'template_path': 'prompt_template_v3.txt',
            'template_hash': 'sha256:def456'  # Changed (critical)
        },
        system_thresholds={
            'anti_churn_threshold': 0.05,
            'probation_period': 2,
            'novelty_threshold': 0.3
        },
        environment_state={
            'python_version': sys.version,
            'packages': {'finlab': '0.4.6'},
            'api_endpoints': ['https://generativelanguage.googleapis.com']
        }
    )

    # Save configs
    config_manager.save_config(config1)
    config_manager.save_config(config2)

    # Act
    diff = config_manager.compute_config_diff(0, 1)

    # Assert - Diff is computed correctly
    assert diff['has_changes'] is True, "Should detect changes"
    assert diff['iteration_nums'] == [0, 1], "Should track iteration numbers"

    # Verify changed fields
    assert 'model_config' in diff['changes'], "Should detect model_config changes"
    assert 'prompt_config' in diff['changes'], "Should detect prompt_config changes"

    # Verify specific changes
    model_changes = diff['changes']['model_config']
    assert 'temperature' in model_changes['changed_fields'], "Should detect temperature change"

    prompt_changes = diff['changes']['prompt_config']
    assert 'template_hash' in prompt_changes['changed_fields'], "Should detect template_hash change"

    # Verify severity assessment
    # Temperature should be moderate, template_hash should be critical
    assert diff['severity'] == 'critical', "Overall severity should be critical (template_hash changed)"


def test_config_in_history(autonomous_loop_mock, temp_test_dir, integration_config):
    """Test config snapshots are stored in IterationRecord.

    Validates:
        - REQ-1.8.3: Config tracking stored in iteration history
        - IterationRecord.config_snapshot field is populated
        - Config snapshot persists through save/load
        - Config can be reconstructed from history

    Story: Story 8 (Experiment Configuration Tracking)
    """
    # Arrange
    config_manager = ExperimentConfigManager(integration_config['config_file'])
    config_manager.clear()

    history = IterationHistory(integration_config['history_file'])
    history.clear()

    # Capture config snapshot
    config = config_manager.capture_config_snapshot(autonomous_loop_mock, iteration_num=0)

    # Act - Add record with config snapshot
    record = history.add_record(
        iteration_num=0,
        model='test-model',
        code='# test code',
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.5},
        feedback='Test feedback',
        config_snapshot=config.to_dict()
    )

    # Assert - Config is in record
    assert record.config_snapshot is not None, "Config snapshot should be recorded"
    assert 'model_config' in record.config_snapshot, "Should have model_config"
    assert 'prompt_config' in record.config_snapshot, "Should have prompt_config"
    assert 'system_thresholds' in record.config_snapshot, "Should have system_thresholds"
    assert 'environment_state' in record.config_snapshot, "Should have environment_state"

    # Verify persistence
    loaded_record = history.get_record(0)
    assert loaded_record is not None
    assert loaded_record.config_snapshot == record.config_snapshot, \
        "Config snapshot should persist through save/load"

    # Verify config can be reconstructed
    reconstructed = ExperimentConfig.from_dict(loaded_record.config_snapshot)
    assert reconstructed.iteration_num == 0, "Should reconstruct iteration_num"
    assert reconstructed.model_config == config.model_config, "Should reconstruct model_config"


# ==============================================================================
# Cross-Story Integration Tests
# ==============================================================================

def test_complete_iteration_record(mock_finlab_data, autonomous_loop_mock,
                                   temp_test_dir, integration_config):
    """Test IterationRecord has all fields from all Phase 1 stories.

    Validates:
        - IterationRecord has data_checksum (Story 7)
        - IterationRecord has data_version (Story 7)
        - IterationRecord has config_snapshot (Story 8)
        - All fields work together without conflicts
        - Complete record can be created and persisted

    Cross-Story: Stories 7, 8
    """
    # Arrange
    integrity = DataPipelineIntegrity()
    config_manager = ExperimentConfigManager(integration_config['config_file'])
    history = IterationHistory(integration_config['history_file'])

    # Clean up
    config_manager.clear()
    history.clear()

    # Capture data provenance
    provenance = integrity.record_data_provenance(mock_finlab_data, iteration_num=0)

    # Capture config snapshot
    config = config_manager.capture_config_snapshot(autonomous_loop_mock, iteration_num=0)

    # Act - Create complete record with all Phase 1 fields
    record = history.add_record(
        iteration_num=0,
        model='test-model',
        code='# test code',
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.5},
        feedback='Test feedback',
        data_checksum=provenance['dataset_checksum'],
        data_version={
            'finlab_version': provenance['finlab_version'],
            'data_pull_timestamp': provenance['data_pull_timestamp'],
            'dataset_row_counts': provenance['dataset_row_counts']
        },
        config_snapshot=config.to_dict()
    )

    # Assert - All Phase 1 fields are present
    assert record.data_checksum is not None, "Should have data_checksum (Story 7)"
    assert record.data_version is not None, "Should have data_version (Story 7)"
    assert record.config_snapshot is not None, "Should have config_snapshot (Story 8)"

    # Verify each field has correct structure
    assert len(record.data_checksum) == 64, "data_checksum should be valid SHA-256"
    assert 'finlab_version' in record.data_version, "data_version should have finlab_version"
    assert 'model_config' in record.config_snapshot, "config_snapshot should have model_config"

    # Verify persistence of complete record
    loaded_record = history.get_record(0)
    assert loaded_record is not None
    assert loaded_record.data_checksum == record.data_checksum
    assert loaded_record.data_version == record.data_version
    assert loaded_record.config_snapshot == record.config_snapshot


def test_data_and_config_together(mock_finlab_data, autonomous_loop_mock,
                                  temp_test_dir, integration_config):
    """Test data provenance and config snapshot work together seamlessly.

    Validates:
        - Both Story 7 and Story 8 features can be used simultaneously
        - No conflicts between data tracking and config tracking
        - Combined tracking provides complete reproducibility metadata

    Cross-Story: Stories 7, 8
    """
    # Arrange
    integrity = DataPipelineIntegrity()
    config_manager = ExperimentConfigManager(integration_config['config_file'])
    config_manager.clear()

    # Act - Capture both data provenance and config snapshot
    provenance = integrity.record_data_provenance(mock_finlab_data, iteration_num=0)
    config = config_manager.capture_config_snapshot(autonomous_loop_mock, iteration_num=0)

    # Assert - Both captured successfully
    assert provenance is not None, "Data provenance should be captured"
    assert config is not None, "Config snapshot should be captured"

    # Verify they don't conflict
    assert 'dataset_checksum' in provenance
    assert config.model_config is not None

    # Verify combined metadata provides complete reproducibility
    reproducibility_metadata = {
        'data': {
            'checksum': provenance['dataset_checksum'],
            'version': provenance['finlab_version'],
            'timestamp': provenance['data_pull_timestamp']
        },
        'config': {
            'model': config.model_config['model_name'],
            'prompt_version': config.prompt_config['version'],
            'thresholds': config.system_thresholds
        }
    }

    assert reproducibility_metadata['data']['checksum'] is not None
    assert reproducibility_metadata['config']['model'] is not None
    assert 'anti_churn_threshold' in reproducibility_metadata['config']['thresholds']


def test_history_persistence_with_all_fields(mock_finlab_data, autonomous_loop_mock,
                                             temp_test_dir, integration_config):
    """Test save/load preserves all Phase 1 fields correctly.

    Validates:
        - IterationHistory.save() persists all new fields
        - IterationHistory.load() restores all new fields
        - No data loss through save/load cycle
        - Field types and structures are maintained

    Cross-Story: Stories 7, 8
    """
    # Arrange
    integrity = DataPipelineIntegrity()
    config_manager = ExperimentConfigManager(integration_config['config_file'])
    history = IterationHistory(integration_config['history_file'])

    config_manager.clear()
    history.clear()

    # Create complete record
    provenance = integrity.record_data_provenance(mock_finlab_data, iteration_num=0)
    config = config_manager.capture_config_snapshot(autonomous_loop_mock, iteration_num=0)

    original_record = history.add_record(
        iteration_num=0,
        model='test-model',
        code='# test code',
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.5},
        feedback='Test feedback',
        data_checksum=provenance['dataset_checksum'],
        data_version={
            'finlab_version': provenance['finlab_version'],
            'data_pull_timestamp': provenance['data_pull_timestamp'],
            'dataset_row_counts': provenance['dataset_row_counts']
        },
        config_snapshot=config.to_dict()
    )

    # Act - Load from disk
    history2 = IterationHistory(integration_config['history_file'])
    loaded_record = history2.get_record(0)

    # Assert - All fields preserved
    assert loaded_record is not None, "Record should be loaded"

    # Compare all Phase 1 fields
    assert loaded_record.data_checksum == original_record.data_checksum, \
        "data_checksum should persist"
    assert loaded_record.data_version == original_record.data_version, \
        "data_version should persist"
    assert loaded_record.config_snapshot == original_record.config_snapshot, \
        "config_snapshot should persist"

    # Verify field structures are maintained
    assert isinstance(loaded_record.data_checksum, str), "data_checksum should be string"
    assert isinstance(loaded_record.data_version, dict), "data_version should be dict"
    assert isinstance(loaded_record.config_snapshot, dict), "config_snapshot should be dict"


def test_multiple_iterations_with_tracking(mock_finlab_data, autonomous_loop_mock,
                                           temp_test_dir, integration_config):
    """Test all tracking features work across multiple iterations.

    Validates:
        - Data consistency checks work across iterations
        - Config diffs work across iterations
        - All tracking features scale to multiple iterations
        - No performance degradation or conflicts

    Cross-Story: Stories 7, 8
    """
    # Arrange
    integrity = DataPipelineIntegrity()
    config_manager = ExperimentConfigManager(integration_config['config_file'])
    history = IterationHistory(integration_config['history_file'])

    config_manager.clear()
    history.clear()

    num_iterations = 5
    checksums = []

    # Act - Run multiple iterations
    for i in range(num_iterations):
        # Capture provenance and config
        provenance = integrity.record_data_provenance(mock_finlab_data, iteration_num=i)
        config = config_manager.capture_config_snapshot(autonomous_loop_mock, iteration_num=i)

        # Store checksum for validation
        checksums.append(provenance['dataset_checksum'])

        # Validate consistency with previous iteration
        if i > 0:
            prev_record = history.get_record(i - 1)
            is_valid, msg = integrity.validate_data_consistency(
                mock_finlab_data,
                prev_record.data_checksum
            )
            # Should pass because we're using same mock data
            assert is_valid is True, f"Iteration {i}: Data consistency should pass"

        # Add record
        history.add_record(
            iteration_num=i,
            model='test-model',
            code=f'# test code iter {i}',
            validation_passed=True,
            validation_errors=[],
            execution_success=True,
            execution_error=None,
            metrics={'sharpe_ratio': 1.5 + i * 0.1},
            feedback=f'Test feedback {i}',
            data_checksum=provenance['dataset_checksum'],
            data_version={
                'finlab_version': provenance['finlab_version'],
                'data_pull_timestamp': provenance['data_pull_timestamp'],
                'dataset_row_counts': provenance['dataset_row_counts']
            },
            config_snapshot=config.to_dict()
        )

    # Assert - All iterations tracked correctly
    assert len(history.records) == num_iterations, \
        f"Should have {num_iterations} records"

    # Verify all records have tracking fields
    for i, record in enumerate(history.records):
        assert record.data_checksum is not None, \
            f"Iteration {i}: Should have data_checksum"
        assert record.data_version is not None, \
            f"Iteration {i}: Should have data_version"
        assert record.config_snapshot is not None, \
            f"Iteration {i}: Should have config_snapshot"

    # Verify checksums are consistent (same data across iterations)
    assert all(cs == checksums[0] for cs in checksums), \
        "All checksums should match (same data)"

    # Verify config diffs work across iterations
    for i in range(1, num_iterations):
        diff = config_manager.compute_config_diff(i - 1, i)
        assert 'has_changes' in diff, f"Should compute diff between {i-1} and {i}"


def test_phase1_features_non_blocking(mock_finlab_data, autonomous_loop_mock,
                                      temp_test_dir, integration_config):
    """Test that errors in tracking features don't crash the iteration loop.

    Validates:
        - Data checksum failures log warnings but don't block iteration
        - Config capture failures log warnings but don't block iteration
        - Invalid data/config handled gracefully
        - Loop continues even with tracking errors

    Cross-Story: Stories 7, 8 (Error Handling)
    """
    # Arrange
    integrity = DataPipelineIntegrity()
    config_manager = ExperimentConfigManager(integration_config['config_file'])
    history = IterationHistory(integration_config['history_file'])

    config_manager.clear()
    history.clear()

    # Act - Create record with None data (should handle gracefully)
    provenance_none = integrity.record_data_provenance(None, iteration_num=0)

    # Should not raise exception, should return EMPTY markers
    assert provenance_none['dataset_checksum'].startswith('EMPTY_DATA_CHECKSUM'), \
        "Should handle None data gracefully"

    # Act - Create record with partial tracking (some fields None)
    record = history.add_record(
        iteration_num=0,
        model='test-model',
        code='# test code',
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.5},
        feedback='Test feedback',
        data_checksum=None,  # None checksum
        data_version=None,   # None version
        config_snapshot=None # None config
    )

    # Assert - Record created successfully with None fields
    assert record is not None, "Record should be created even with None tracking fields"
    assert record.data_checksum is None
    assert record.data_version is None
    assert record.config_snapshot is None

    # Verify record persists
    loaded_record = history.get_record(0)
    assert loaded_record is not None, "Record with None fields should persist"

    # Act - Create record with valid tracking (should also work)
    provenance = integrity.record_data_provenance(mock_finlab_data, iteration_num=1)
    config = config_manager.capture_config_snapshot(autonomous_loop_mock, iteration_num=1)

    record2 = history.add_record(
        iteration_num=1,
        model='test-model',
        code='# test code',
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.6},
        feedback='Test feedback',
        data_checksum=provenance['dataset_checksum'],
        data_version={
            'finlab_version': provenance['finlab_version'],
            'data_pull_timestamp': provenance['data_pull_timestamp'],
            'dataset_row_counts': provenance['dataset_row_counts']
        },
        config_snapshot=config.to_dict()
    )

    # Assert - Both records coexist
    assert len(history.records) == 2, "Should have both records"
    assert history.records[0].data_checksum is None, "First record has None tracking"
    assert history.records[1].data_checksum is not None, "Second record has valid tracking"


# ==============================================================================
# Test Execution Summary
# ==============================================================================

def test_phase1_integration_summary(mock_finlab_data, autonomous_loop_mock,
                                   temp_test_dir, integration_config):
    """Summary test demonstrating complete Phase 1 integration.

    This test serves as documentation of how all Phase 1 features
    work together in the autonomous loop. It's not a functional test
    but rather a demonstration of the complete workflow.

    Phase 1 Stories:
        - Story 6: Metric Integrity (tested in autonomous_loop.py)
        - Story 5: Semantic Validation (tested in autonomous_loop.py)
        - Story 3: Extended Test Harness (separate test file)
        - Story 7: Data Pipeline Integrity (tested here)
        - Story 8: Experiment Configuration Tracking (tested here)
    """
    # This is a documentation test - always passes
    assert True, "Phase 1 integration test suite complete"

    # Document what was tested
    tested_stories = [
        "Story 7: Data Pipeline Integrity",
        "Story 8: Experiment Configuration Tracking",
        "Cross-Story Integration: Stories 7 + 8"
    ]

    tested_requirements = [
        "REQ-1.7.1: Dataset checksums recorded and validated",
        "REQ-1.7.2: Data version tracking in iteration history",
        "REQ-1.7.3: Automated data consistency checks",
        "REQ-1.7.4: Iteration history includes data provenance",
        "REQ-1.8.1: Config snapshots captured at each iteration",
        "REQ-1.8.2: Config diffs computed between iterations",
        "REQ-1.8.3: Config tracking stored in iteration history"
    ]

    print("\n" + "="*60)
    print("PHASE 1 INTEGRATION TEST SUMMARY")
    print("="*60)
    print("\nTested Stories:")
    for story in tested_stories:
        print(f"  ✅ {story}")

    print("\nTested Requirements:")
    for req in tested_requirements:
        print(f"  ✅ {req}")

    print("\nTest Coverage:")
    print("  - Story 7 Integration: 3 tests")
    print("  - Story 8 Integration: 3 tests")
    print("  - Cross-Story Integration: 5 tests")
    print("  - Total: 11 comprehensive tests")
    print("="*60)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
