"""Protocol compliance tests for ChampionTracker.

Tests that ChampionTracker implements IChampionTracker Protocol correctly
and enforces behavioral contracts.

**TDD Phase: RED - Failing Tests**
Expected to FAIL until ChampionTracker is updated to match Protocol.

Test Coverage:
1. Runtime Protocol Compliance
2. Type Signature Matching
3. Behavioral Contracts (idempotency, referential stability)
4. Edge Cases (None handling, missing metrics)
"""

import pytest
from typing import Optional, Dict, Any
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import json
import sys

from src.learning.champion_tracker import ChampionTracker, ChampionStrategy
from src.learning.interfaces import IChampionTracker
from src.learning.iteration_history import IterationHistory
from src.repository.hall_of_fame import HallOfFameRepository
from src.config.anti_churn_manager import AntiChurnManager


# Module-level Setup: Mock performance_attributor
@pytest.fixture(scope="module", autouse=True)
def mock_performance_attributor_module():
    """Mock the performance_attributor module for all tests."""
    mock_module = MagicMock()
    mock_module.extract_strategy_params = MagicMock(return_value={'param1': 1.0})
    mock_module.extract_success_patterns = MagicMock(return_value=['pattern1'])
    sys.modules['performance_attributor'] = mock_module
    yield
    if 'performance_attributor' in sys.modules:
        del sys.modules['performance_attributor']


# Mock strategy_metadata module for Factor Graph support
@pytest.fixture(scope="module", autouse=True)
def mock_strategy_metadata_module():
    """Mock the strategy_metadata module for all tests."""
    mock_module = MagicMock()
    mock_module.extract_dag_parameters = MagicMock(return_value={'dag_param1': 2.0})
    mock_module.extract_dag_patterns = MagicMock(return_value=['dag_pattern1'])
    sys.modules['src.learning.strategy_metadata'] = mock_module
    yield
    if 'src.learning.strategy_metadata' in sys.modules:
        del sys.modules['src.learning.strategy_metadata']


@pytest.fixture
def temp_files():
    """Create temporary files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "test_history.jsonl"
        champion_file = Path(tmpdir) / "test_champion.json"
        config_file = Path(tmpdir) / "test_config.json"
        hall_of_fame_path = Path(tmpdir) / "hall_of_fame"

        # Create minimal config file
        config_data = {
            "anti_churn": {
                "min_sharpe_for_champion": 0.5,
                "base_improvement_pct": 0.05,
                "additive_threshold": 0.1
            }
        }
        config_file.write_text(json.dumps(config_data))

        yield {
            "history_file": str(history_file),
            "champion_file": str(champion_file),
            "config_file": str(config_file),
            "hall_of_fame_path": str(hall_of_fame_path)
        }


@pytest.fixture
def champion_tracker(temp_files):
    """Create ChampionTracker instance for testing."""
    history = IterationHistory(filepath=temp_files["history_file"])
    hall_of_fame = HallOfFameRepository(
        base_path=temp_files["hall_of_fame_path"],
        test_mode=True
    )
    anti_churn = AntiChurnManager(config_path=temp_files["config_file"])

    tracker = ChampionTracker(
        hall_of_fame=hall_of_fame,
        history=history,
        anti_churn=anti_churn,
        champion_file=temp_files["champion_file"]
    )

    # Clear any existing champion (fresh start for each test)
    tracker.champion = None

    return tracker


class TestProtocolCompliance:
    """Test ChampionTracker implements IChampionTracker Protocol."""

    def test_runtime_protocol_check(self, champion_tracker):
        """Test ChampionTracker satisfies IChampionTracker at runtime.

        EXPECTED: FAIL - ChampionTracker doesn't have @runtime_checkable yet
        """
        assert isinstance(champion_tracker, IChampionTracker), (
            "ChampionTracker must implement IChampionTracker Protocol"
        )

    def test_champion_property_exists(self, champion_tracker):
        """Test .champion property exists and returns Optional type."""
        assert hasattr(champion_tracker, 'champion'), (
            "ChampionTracker must have .champion property"
        )

        # Property should be accessible
        result = champion_tracker.champion

        # Type should be Optional[ChampionStrategy]
        assert result is None or isinstance(result, ChampionStrategy), (
            f".champion must return None or ChampionStrategy, got {type(result)}"
        )

    def test_update_champion_method_exists(self, champion_tracker):
        """Test .update_champion() method exists with correct signature."""
        assert hasattr(champion_tracker, 'update_champion'), (
            "ChampionTracker must have .update_champion() method"
        )

        # Check method is callable
        assert callable(champion_tracker.update_champion), (
            ".update_champion must be callable"
        )

    def test_update_champion_return_type(self, champion_tracker):
        """Test .update_champion() returns bool.

        EXPECTED: FAIL - Current implementation doesn't enforce bool return type
        """
        metrics = {'sharpe_ratio': 1.5, 'max_drawdown': -0.15}

        # Call with LLM parameters
        result = champion_tracker.update_champion(
            iteration_num=0,
            code="# test strategy",
            metrics=metrics
        )

        # Must return bool
        assert isinstance(result, bool), (
            f".update_champion() must return bool, got {type(result)}"
        )


class TestBehavioralContracts:
    """Test behavioral contracts from IChampionTracker Protocol."""

    def test_champion_referential_stability(self, champion_tracker):
        """Test .champion returns same object if unchanged.

        Behavioral Contract:
        - MUST be referentially stable: returns same object if champion unchanged
        """
        # Create initial champion
        metrics = {'sharpe_ratio': 1.5, 'max_drawdown': -0.15, 'calmar_ratio': 1.0}
        champion_tracker.update_champion(
            iteration_num=0,
            code="# initial champion",
            metrics=metrics
        )

        # Get champion reference
        champion_1 = champion_tracker.champion
        champion_2 = champion_tracker.champion

        # Should return same object (referential identity)
        assert champion_1 is champion_2, (
            ".champion must return same object if unchanged (referential stability)"
        )

    def test_champion_never_raises_on_none(self, champion_tracker):
        """Test .champion never raises exception when no champion exists."""
        # No champion created yet
        assert champion_tracker.champion is None, (
            ".champion must return None if no champion exists (never raises)"
        )

        # Should not raise exception
        try:
            _ = champion_tracker.champion
        except Exception as e:
            pytest.fail(f".champion raised exception when it should return None: {e}")

    def test_update_champion_validates_sharpe_ratio(self, champion_tracker):
        """Test .update_champion() validates sharpe_ratio exists.

        Behavioral Contract:
        - MUST validate metrics['sharpe_ratio'] exists before comparison
        """
        # Missing sharpe_ratio should fail gracefully (return False)
        metrics_missing_sharpe = {'max_drawdown': -0.15}

        result = champion_tracker.update_champion(
            iteration_num=0,
            code="# test strategy",
            metrics=metrics_missing_sharpe
        )

        # Should return False (not raise exception)
        assert result is False, (
            ".update_champion() must return False when sharpe_ratio missing "
            "(not raise exception)"
        )

    def test_update_champion_idempotency(self, champion_tracker):
        """Test updating with same record twice is safe (idempotent).

        Behavioral Contract:
        - Updating with same iteration twice should be safe
        """
        metrics = {'sharpe_ratio': 1.5, 'max_drawdown': -0.15, 'calmar_ratio': 1.0}
        code = "# test strategy"

        # First update
        result1 = champion_tracker.update_champion(
            iteration_num=0,
            code=code,
            metrics=metrics
        )
        assert result1 is True, "First update should succeed"

        # Second update with same data
        result2 = champion_tracker.update_champion(
            iteration_num=0,
            code=code,
            metrics=metrics
        )

        # Should be safe (not crash), but not update (return False)
        assert result2 is False, (
            "Updating with same iteration should be safe (idempotent) "
            "but return False (no improvement)"
        )

        # Champion should remain unchanged
        assert champion_tracker.champion is not None
        assert champion_tracker.champion.iteration_num == 0

    def test_update_champion_atomicity(self, champion_tracker):
        """Test .update_champion() is atomic (all-or-nothing).

        Behavioral Contract:
        - MUST be atomic: either fully updates or leaves champion unchanged
        """
        # Create initial champion
        initial_metrics = {'sharpe_ratio': 1.5, 'max_drawdown': -0.15, 'calmar_ratio': 1.0}
        champion_tracker.update_champion(
            iteration_num=0,
            code="# initial champion",
            metrics=initial_metrics
        )

        initial_champion = champion_tracker.champion
        initial_sharpe = initial_champion.metrics['sharpe_ratio']

        # Try update that should fail (lower Sharpe)
        worse_metrics = {'sharpe_ratio': 1.0, 'max_drawdown': -0.20, 'calmar_ratio': 0.8}
        result = champion_tracker.update_champion(
            iteration_num=1,
            code="# worse strategy",
            metrics=worse_metrics
        )

        assert result is False, "Update should fail (worse Sharpe)"

        # Champion should be COMPLETELY unchanged (referential identity)
        assert champion_tracker.champion is initial_champion, (
            "Champion must remain unchanged (referential identity) when update fails"
        )
        assert champion_tracker.champion.metrics['sharpe_ratio'] == initial_sharpe, (
            "Champion metrics must remain unchanged when update fails"
        )

    def test_update_champion_post_condition(self, champion_tracker):
        """Test .update_champion() post-condition enforcement.

        Behavioral Contract:
        - If returns True, subsequent .champion must return new champion
        - If returns True, .champion.iteration_num must equal iteration_num
        """
        metrics = {'sharpe_ratio': 1.5, 'max_drawdown': -0.15, 'calmar_ratio': 1.0}

        result = champion_tracker.update_champion(
            iteration_num=5,
            code="# test champion",
            metrics=metrics
        )

        # If update succeeded
        if result:
            # Post-condition 1: champion must exist
            assert champion_tracker.champion is not None, (
                "If update_champion returns True, .champion must not be None"
            )

            # Post-condition 2: iteration_num must match
            assert champion_tracker.champion.iteration_num == 5, (
                f"If update_champion returns True, .champion.iteration_num must equal 5, "
                f"got {champion_tracker.champion.iteration_num}"
            )

            # Post-condition 3: sharpe_ratio must exist
            assert 'sharpe_ratio' in champion_tracker.champion.metrics, (
                "Champion metrics must contain sharpe_ratio"
            )


class TestEdgeCases:
    """Test edge cases for Protocol compliance."""

    def test_champion_with_none_code(self, champion_tracker):
        """Test champion creation with None code (Factor Graph mode)."""
        # Factor Graph mode: code=None, strategy parameters in kwargs
        metrics = {'sharpe_ratio': 2.0, 'max_drawdown': -0.10, 'calmar_ratio': 1.5}

        # Create mock Strategy DAG object
        mock_strategy = MagicMock()
        mock_strategy.id = "momentum_v1"
        mock_strategy.generation = 1

        result = champion_tracker.update_champion(
            iteration_num=0,
            code=None,  # Factor Graph mode
            metrics=metrics,
            generation_method="factor_graph",
            strategy=mock_strategy,  # Required for Factor Graph
            strategy_id="momentum_v1",
            strategy_generation=1
        )

        # Should succeed if sharpe_ratio exists
        assert isinstance(result, bool), ".update_champion() must return bool"

    def test_champion_metrics_validation(self, champion_tracker):
        """Test champion validates required metrics exist."""
        # Create champion
        metrics = {'sharpe_ratio': 1.5, 'max_drawdown': -0.15, 'calmar_ratio': 1.0}
        champion_tracker.update_champion(
            iteration_num=0,
            code="# test strategy",
            metrics=metrics
        )

        champion = champion_tracker.champion

        # Champion must have sharpe_ratio
        assert champion is not None, "Champion must exist after successful update"
        assert 'sharpe_ratio' in champion.metrics, (
            "Champion metrics must contain sharpe_ratio (Protocol contract)"
        )

        # iteration_num must be non-negative
        assert champion.iteration_num >= 0, (
            "Champion iteration_num must be non-negative (Protocol contract)"
        )
