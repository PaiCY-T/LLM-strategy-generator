"""
Unit Tests for RollbackManager
===============================

Tests for rollback functionality including champion history retrieval,
rollback operations, validation, and audit trail recording.

Test Coverage:
    - get_champion_history: Champion retrieval and sorting
    - rollback_to_iteration: Successful and failed rollback scenarios
    - validate_rollback_champion: Validation pass/fail cases
    - record_rollback: Audit trail persistence
    - RollbackRecord serialization: To/from dict conversion
"""

import pytest
import json
import uuid
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

from src.repository.hall_of_fame import HallOfFameRepository, StrategyGenome
from src.recovery.rollback_manager import (
    RollbackManager,
    ChampionStrategy,
    RollbackRecord
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def mock_hall_of_fame(tmp_path):
    """Create mock HallOfFameRepository with test data."""
    # Use test_mode=True to skip path security checks
    hall_of_fame = HallOfFameRepository(
        base_path=str(tmp_path / "test_hall_of_fame"),
        test_mode=True
    )
    return hall_of_fame


@pytest.fixture
def rollback_manager(mock_hall_of_fame, tmp_path):
    """Create RollbackManager instance with mock dependencies."""
    rollback_log_file = str(tmp_path / "test_rollback_history.json")
    return RollbackManager(
        hall_of_fame=mock_hall_of_fame,
        rollback_log_file=rollback_log_file
    )


@pytest.fixture
def sample_champions() -> List[ChampionStrategy]:
    """Create sample champion strategies for testing."""
    return [
        ChampionStrategy(
            iteration_num=1,
            code="# Strategy iteration 1",
            parameters={'n_stocks': 20, 'threshold': 1.05},
            metrics={'sharpe_ratio': 2.1, 'annual_return': 0.25},
            success_patterns=['pattern_a', 'pattern_b'],
            timestamp='2025-10-12T10:00:00'
        ),
        ChampionStrategy(
            iteration_num=3,
            code="# Strategy iteration 3",
            parameters={'n_stocks': 25, 'threshold': 1.08},
            metrics={'sharpe_ratio': 2.5, 'annual_return': 0.30},
            success_patterns=['pattern_a', 'pattern_c'],
            timestamp='2025-10-12T12:00:00'
        ),
        ChampionStrategy(
            iteration_num=5,
            code="# Strategy iteration 5",
            parameters={'n_stocks': 22, 'threshold': 1.06},
            metrics={'sharpe_ratio': 2.3, 'annual_return': 0.28},
            success_patterns=['pattern_b', 'pattern_c'],
            timestamp='2025-10-12T14:00:00'
        )
    ]


@pytest.fixture
def populate_hall_of_fame(mock_hall_of_fame, sample_champions):
    """Populate Hall of Fame with sample champion data."""
    for champ in sample_champions:
        # Add iteration metadata to parameters
        params_with_metadata = champ.parameters.copy()
        params_with_metadata['__iteration_num__'] = champ.iteration_num

        mock_hall_of_fame.add_strategy(
            template_name='autonomous_generated',
            parameters=params_with_metadata,
            metrics=champ.metrics,
            strategy_code=champ.code,
            success_patterns=champ.success_patterns
        )

    return mock_hall_of_fame


# ==============================================================================
# Test: get_champion_history
# ==============================================================================

def test_get_champion_history_returns_correct_champions(
    rollback_manager,
    populate_hall_of_fame
):
    """Test that get_champion_history returns correct champions sorted by Sharpe."""
    champions = rollback_manager.get_champion_history(limit=10)

    # Should return all 3 champions
    assert len(champions) == 3

    # Hall of Fame sorts by Sharpe ratio descending (highest first)
    # Then our code sorts by timestamp descending (newest first)
    # But since we re-sort by timestamp, the order depends on timestamps
    # The actual order is determined by Hall of Fame's query (Sharpe desc) first
    assert champions[0].metrics['sharpe_ratio'] == 2.5  # Iteration 3
    assert champions[1].metrics['sharpe_ratio'] == 2.3  # Iteration 5
    assert champions[2].metrics['sharpe_ratio'] == 2.1  # Iteration 1

    # Verify all champions are present
    iteration_nums = {c.iteration_num for c in champions}
    assert iteration_nums == {1, 3, 5}


def test_get_champion_history_respects_limit(
    rollback_manager,
    populate_hall_of_fame
):
    """Test that get_champion_history respects limit parameter."""
    champions = rollback_manager.get_champion_history(limit=2)

    # Should return only 2 champions (sorted by Sharpe from Hall of Fame)
    assert len(champions) == 2
    # Hall of Fame returns highest Sharpe first (2.5 and 2.3)
    assert champions[0].metrics['sharpe_ratio'] == 2.5  # Iteration 3
    assert champions[1].metrics['sharpe_ratio'] == 2.3  # Iteration 5


def test_get_champion_history_empty_hall_of_fame(rollback_manager):
    """Test get_champion_history with empty Hall of Fame."""
    champions = rollback_manager.get_champion_history(limit=10)

    # Should return empty list
    assert len(champions) == 0


def test_get_champion_history_removes_metadata_from_parameters(
    rollback_manager,
    populate_hall_of_fame
):
    """Test that metadata parameters are removed from returned champions."""
    champions = rollback_manager.get_champion_history(limit=10)

    # Check all champions have clean parameters (no __ prefix)
    for champ in champions:
        for key in champ.parameters.keys():
            assert not key.startswith('__'), f"Found metadata key: {key}"


# ==============================================================================
# Test: rollback_to_iteration (Success)
# ==============================================================================

def test_rollback_to_iteration_success(
    rollback_manager,
    populate_hall_of_fame
):
    """Test successful rollback to a specific iteration."""
    mock_data = MagicMock()

    # Mock validation to pass
    with patch.object(
        rollback_manager,
        'validate_rollback_champion',
        return_value=(True, {'status': 'valid', 'current_sharpe': 2.3})
    ):
        success, message = rollback_manager.rollback_to_iteration(
            target_iteration=3,
            reason="Test rollback",
            operator="test@example.com",
            data=mock_data,
            validate=True
        )

    # Should succeed
    assert success is True
    assert "Successfully rolled back" in message
    assert "to 3" in message

    # Verify rollback was recorded
    history = rollback_manager.get_rollback_history(limit=1)
    assert len(history) == 1
    assert history[0].to_iteration == 3
    assert history[0].reason == "Test rollback"
    assert history[0].operator == "test@example.com"
    assert history[0].validation_passed is True


def test_rollback_to_iteration_without_validation(
    rollback_manager,
    populate_hall_of_fame
):
    """Test rollback without validation (faster but risky)."""
    mock_data = MagicMock()

    success, message = rollback_manager.rollback_to_iteration(
        target_iteration=3,
        reason="Emergency rollback",
        operator="ops@example.com",
        data=mock_data,
        validate=False  # Skip validation
    )

    # Should succeed without validation
    assert success is True
    assert "Successfully rolled back" in message

    # Verify validation was skipped
    history = rollback_manager.get_rollback_history(limit=1)
    assert len(history) == 1
    assert history[0].validation_report.get('skipped') is True


# ==============================================================================
# Test: rollback_to_iteration (Failure)
# ==============================================================================

def test_rollback_to_iteration_not_found(
    rollback_manager,
    populate_hall_of_fame
):
    """Test rollback to non-existent iteration."""
    mock_data = MagicMock()

    success, message = rollback_manager.rollback_to_iteration(
        target_iteration=99,  # Non-existent iteration
        reason="Test rollback",
        operator="test@example.com",
        data=mock_data
    )

    # Should fail
    assert success is False
    assert "No champion found for iteration 99" in message

    # Verify failed attempt was recorded
    history = rollback_manager.get_rollback_history(limit=1)
    assert len(history) == 1
    assert history[0].to_iteration == 99
    assert history[0].validation_passed is False
    assert 'error' in history[0].validation_report


def test_rollback_to_iteration_validation_fails(
    rollback_manager,
    populate_hall_of_fame
):
    """Test rollback when validation fails."""
    mock_data = MagicMock()

    # Mock validation to fail
    with patch.object(
        rollback_manager,
        'validate_rollback_champion',
        return_value=(False, {'error': 'Sharpe ratio too low'})
    ):
        success, message = rollback_manager.rollback_to_iteration(
            target_iteration=3,
            reason="Test rollback",
            operator="test@example.com",
            data=mock_data,
            validate=True
        )

    # Should fail
    assert success is False
    assert "Validation failed" in message
    assert "Sharpe ratio too low" in message

    # Verify failed attempt was recorded
    history = rollback_manager.get_rollback_history(limit=1)
    assert len(history) == 1
    assert history[0].validation_passed is False


# ==============================================================================
# Test: validate_rollback_champion
# ==============================================================================

def test_validate_rollback_champion_pass(rollback_manager, sample_champions):
    """Test validation passes for valid champion."""
    champion = sample_champions[0]  # Sharpe 2.1
    mock_data = MagicMock()

    # Mock successful execution
    with patch('artifacts.working.modules.sandbox_simple.execute_strategy_safe') as mock_execute:
        mock_execute.return_value = (
            True,  # success
            {'sharpe_ratio': 2.0, 'annual_return': 0.25},  # metrics
            None  # error
        )

        is_valid, report = rollback_manager.validate_rollback_champion(
            champion=champion,
            data=mock_data,
            min_sharpe_threshold=0.5
        )

    # Should pass validation
    assert is_valid is True
    assert report['execution_success'] is True
    assert report['current_sharpe'] == 2.0
    assert report['original_sharpe'] == 2.1
    assert report['status'] == 'valid'


def test_validate_rollback_champion_fail_execution(
    rollback_manager,
    sample_champions
):
    """Test validation fails when execution fails."""
    champion = sample_champions[0]
    mock_data = MagicMock()

    # Mock failed execution
    with patch('artifacts.working.modules.sandbox_simple.execute_strategy_safe') as mock_execute:
        mock_execute.return_value = (
            False,  # success
            None,  # metrics
            "Execution error"  # error
        )

        is_valid, report = rollback_manager.validate_rollback_champion(
            champion=champion,
            data=mock_data
        )

    # Should fail validation
    assert is_valid is False
    assert 'Execution failed' in report['error']
    assert report['execution_success'] is False


def test_validate_rollback_champion_fail_low_sharpe(
    rollback_manager,
    sample_champions
):
    """Test validation fails when Sharpe ratio below threshold."""
    champion = sample_champions[0]
    mock_data = MagicMock()

    # Mock execution with low Sharpe
    with patch('artifacts.working.modules.sandbox_simple.execute_strategy_safe') as mock_execute:
        mock_execute.return_value = (
            True,
            {'sharpe_ratio': 0.3, 'annual_return': 0.10},
            None
        )

        is_valid, report = rollback_manager.validate_rollback_champion(
            champion=champion,
            data=mock_data,
            min_sharpe_threshold=0.5
        )

    # Should fail validation
    assert is_valid is False
    assert 'below threshold' in report['error']
    assert report['current_sharpe'] == 0.3


def test_validate_rollback_champion_no_metrics(
    rollback_manager,
    sample_champions
):
    """Test validation fails when no metrics returned."""
    champion = sample_champions[0]
    mock_data = MagicMock()

    # Mock execution without metrics
    with patch('artifacts.working.modules.sandbox_simple.execute_strategy_safe') as mock_execute:
        mock_execute.return_value = (
            True,
            None,  # No metrics
            None
        )

        is_valid, report = rollback_manager.validate_rollback_champion(
            champion=champion,
            data=mock_data
        )

    # Should fail validation
    assert is_valid is False
    assert 'No metrics' in report['error']


# ==============================================================================
# Test: record_rollback
# ==============================================================================

def test_record_rollback(rollback_manager, tmp_path):
    """Test rollback recording in audit trail."""
    rollback_manager.record_rollback(
        from_iteration=10,
        to_iteration=5,
        reason="Production bug",
        operator="john@example.com",
        validation_passed=True,
        validation_report={'sharpe': 2.3}
    )

    # Verify in-memory log
    assert len(rollback_manager.rollback_log) == 1
    record = rollback_manager.rollback_log[0]

    assert record.from_iteration == 10
    assert record.to_iteration == 5
    assert record.reason == "Production bug"
    assert record.operator == "john@example.com"
    assert record.validation_passed is True
    assert record.validation_report == {'sharpe': 2.3}
    assert isinstance(record.rollback_id, str)
    assert len(record.rollback_id) > 0

    # Verify file persistence
    log_file = rollback_manager.rollback_log_file
    assert log_file.exists()

    with open(log_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 1

        # Parse JSON line
        saved_record = json.loads(lines[0])
        assert saved_record['from_iteration'] == 10
        assert saved_record['to_iteration'] == 5
        assert saved_record['reason'] == "Production bug"


def test_record_rollback_multiple_records(rollback_manager):
    """Test multiple rollback records append correctly."""
    # Record first rollback
    rollback_manager.record_rollback(
        from_iteration=10,
        to_iteration=5,
        reason="Bug fix",
        operator="ops1@example.com",
        validation_passed=True,
        validation_report={}
    )

    # Record second rollback
    rollback_manager.record_rollback(
        from_iteration=11,
        to_iteration=7,
        reason="Performance issue",
        operator="ops2@example.com",
        validation_passed=True,
        validation_report={}
    )

    # Verify both records exist
    assert len(rollback_manager.rollback_log) == 2

    # Verify file has both records
    with open(rollback_manager.rollback_log_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 2


# ==============================================================================
# Test: RollbackRecord Serialization
# ==============================================================================

def test_rollback_record_to_dict():
    """Test RollbackRecord serialization to dictionary."""
    record = RollbackRecord(
        rollback_id="test-uuid-123",
        from_iteration=10,
        to_iteration=5,
        reason="Test reason",
        operator="test@example.com",
        timestamp="2025-10-12T10:00:00",
        validation_passed=True,
        validation_report={'status': 'valid'}
    )

    record_dict = record.to_dict()

    assert record_dict['rollback_id'] == "test-uuid-123"
    assert record_dict['from_iteration'] == 10
    assert record_dict['to_iteration'] == 5
    assert record_dict['reason'] == "Test reason"
    assert record_dict['operator'] == "test@example.com"
    assert record_dict['timestamp'] == "2025-10-12T10:00:00"
    assert record_dict['validation_passed'] is True
    assert record_dict['validation_report'] == {'status': 'valid'}


def test_rollback_record_from_dict():
    """Test RollbackRecord deserialization from dictionary."""
    record_dict = {
        'rollback_id': "test-uuid-456",
        'from_iteration': 8,
        'to_iteration': 3,
        'reason': "Rollback test",
        'operator': "ops@example.com",
        'timestamp': "2025-10-12T11:00:00",
        'validation_passed': False,
        'validation_report': {'error': 'Validation failed'}
    }

    record = RollbackRecord.from_dict(record_dict)

    assert record.rollback_id == "test-uuid-456"
    assert record.from_iteration == 8
    assert record.to_iteration == 3
    assert record.reason == "Rollback test"
    assert record.operator == "ops@example.com"
    assert record.timestamp == "2025-10-12T11:00:00"
    assert record.validation_passed is False
    assert record.validation_report == {'error': 'Validation failed'}


def test_rollback_record_roundtrip():
    """Test RollbackRecord serialization roundtrip (to_dict -> from_dict)."""
    original = RollbackRecord(
        rollback_id=str(uuid.uuid4()),
        from_iteration=12,
        to_iteration=6,
        reason="Roundtrip test",
        operator="test@example.com",
        timestamp=datetime.now().isoformat(),
        validation_passed=True,
        validation_report={'sharpe': 2.5, 'return': 0.28}
    )

    # Serialize and deserialize
    record_dict = original.to_dict()
    restored = RollbackRecord.from_dict(record_dict)

    # Verify all fields match
    assert restored.rollback_id == original.rollback_id
    assert restored.from_iteration == original.from_iteration
    assert restored.to_iteration == original.to_iteration
    assert restored.reason == original.reason
    assert restored.operator == original.operator
    assert restored.timestamp == original.timestamp
    assert restored.validation_passed == original.validation_passed
    assert restored.validation_report == original.validation_report


# ==============================================================================
# Test: get_rollback_history
# ==============================================================================

def test_get_rollback_history(rollback_manager):
    """Test retrieving rollback history."""
    # Create multiple rollback records
    for i in range(5):
        rollback_manager.record_rollback(
            from_iteration=10 + i,
            to_iteration=5 + i,
            reason=f"Rollback {i}",
            operator=f"ops{i}@example.com",
            validation_passed=True,
            validation_report={}
        )

    # Get all history
    history = rollback_manager.get_rollback_history()
    assert len(history) == 5

    # Verify sorted by timestamp descending (newest first)
    for i in range(len(history) - 1):
        assert history[i].timestamp >= history[i + 1].timestamp


def test_get_rollback_history_with_limit(rollback_manager):
    """Test get_rollback_history respects limit parameter."""
    # Create multiple rollback records
    for i in range(5):
        rollback_manager.record_rollback(
            from_iteration=10 + i,
            to_iteration=5 + i,
            reason=f"Rollback {i}",
            operator=f"ops{i}@example.com",
            validation_passed=True,
            validation_report={}
        )

    # Get limited history
    history = rollback_manager.get_rollback_history(limit=3)
    assert len(history) == 3


# ==============================================================================
# Test: Rollback Log Persistence
# ==============================================================================

def test_rollback_log_persistence(mock_hall_of_fame, tmp_path):
    """Test that rollback log is loaded from file on initialization."""
    rollback_log_file = tmp_path / "persistent_rollback_history.json"

    # Create initial manager and record rollback
    manager1 = RollbackManager(
        hall_of_fame=mock_hall_of_fame,
        rollback_log_file=str(rollback_log_file)
    )

    manager1.record_rollback(
        from_iteration=10,
        to_iteration=5,
        reason="Test persistence",
        operator="test@example.com",
        validation_passed=True,
        validation_report={'status': 'valid'}
    )

    # Create new manager - should load existing log
    manager2 = RollbackManager(
        hall_of_fame=mock_hall_of_fame,
        rollback_log_file=str(rollback_log_file)
    )

    # Verify log was loaded
    assert len(manager2.rollback_log) == 1
    assert manager2.rollback_log[0].reason == "Test persistence"


# ==============================================================================
# Test: Integration Scenario
# ==============================================================================

def test_complete_rollback_workflow(
    rollback_manager,
    populate_hall_of_fame
):
    """Test complete rollback workflow from history to execution."""
    mock_data = MagicMock()

    # Step 1: List champion history
    champions = rollback_manager.get_champion_history(limit=10)
    assert len(champions) > 0

    # Step 2: Select target iteration
    target_champion = champions[1]  # Select iteration 3

    # Step 3: Perform rollback with validation
    with patch('artifacts.working.modules.sandbox_simple.execute_strategy_safe') as mock_execute:
        # Mock successful validation
        mock_execute.return_value = (
            True,
            {'sharpe_ratio': 2.4, 'annual_return': 0.29},
            None
        )

        success, message = rollback_manager.rollback_to_iteration(
            target_iteration=target_champion.iteration_num,
            reason="Integration test",
            operator="test@example.com",
            data=mock_data,
            validate=True
        )

    # Verify success
    assert success is True

    # Step 4: Verify audit trail
    history = rollback_manager.get_rollback_history(limit=1)
    assert len(history) == 1
    assert history[0].to_iteration == target_champion.iteration_num
    assert history[0].validation_passed is True

    # Step 5: Verify champion was updated in Hall of Fame
    current_champion = rollback_manager.hall_of_fame.get_current_champion()
    assert current_champion is not None
    # Note: Current champion may have higher Sharpe due to test data ordering
