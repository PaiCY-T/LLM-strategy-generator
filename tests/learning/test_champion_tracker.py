"""
Comprehensive test suite for ChampionTracker and ChampionStrategy.

Test Coverage:
1. Champion Creation
   - First champion (no existing champion)
   - Champion creation from valid strategy
   - Champion creation validation

2. Champion Update Logic
   - Champion updated (higher Sharpe)
   - Champion NOT updated (lower Sharpe)
   - Tie-breaking (equal Sharpe, lower Max Drawdown wins)
   - Multi-objective validation (Calmar, drawdown)
   - Hybrid threshold (relative vs absolute)

3. Staleness Detection
   - Check staleness after N iterations (default 50)
   - Cohort comparison logic
   - Stale champion detection
   - Edge cases (no data, insufficient cohort)

4. Persistence
   - Load champion from Hall of Fame
   - Save champion to Hall of Fame
   - Handle missing champion file
   - Legacy champion migration

5. Integration
   - Integration with IterationHistory
   - Integration with HallOfFameRepository
   - Integration with AntiChurnManager
   - Integration with ConfigManager

Test Strategy:
- Mock all external dependencies (Hall of Fame, History, AntiChurn)
- No real file I/O operations
- Test both success and failure scenarios
- Focus on public API coverage
"""

import json
import pytest
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, Any

from src.learning.champion_tracker import ChampionTracker, ChampionStrategy
from src.learning.iteration_history import IterationHistory, IterationRecord


# ==============================================================================
# Module-level Setup: Mock performance_attributor
# ==============================================================================

@pytest.fixture(scope='session', autouse=True)
def mock_performance_attributor_module():
    """Mock the performance_attributor module for all tests."""
    # Create mock module
    mock_module = MagicMock()
    mock_module.extract_strategy_params = MagicMock(return_value={})
    mock_module.extract_success_patterns = MagicMock(return_value=[])
    mock_module.compare_strategies = MagicMock(return_value=None)

    # Inject into sys.modules
    sys.modules['performance_attributor'] = mock_module

    yield mock_module

    # Cleanup
    if 'performance_attributor' in sys.modules:
        del sys.modules['performance_attributor']


# ==============================================================================
# Test ChampionStrategy Dataclass
# ==============================================================================

class TestChampionStrategy:
    """Test ChampionStrategy dataclass serialization and deserialization."""

    def test_champion_strategy_creation(self):
        """Create ChampionStrategy with valid data."""
        champion = ChampionStrategy(
            iteration_num=10,
            code="# strategy code",
            parameters={'param1': 1.0, 'param2': 2.0},
            metrics={'sharpe_ratio': 2.5, 'max_drawdown': -0.15},
            success_patterns=['pattern1', 'pattern2'],
            timestamp='2025-11-04T10:00:00'
        )

        assert champion.iteration_num == 10
        assert champion.code == "# strategy code"
        assert champion.parameters == {'param1': 1.0, 'param2': 2.0}
        assert champion.metrics['sharpe_ratio'] == 2.5
        assert len(champion.success_patterns) == 2
        assert champion.timestamp == '2025-11-04T10:00:00'

    def test_champion_strategy_to_dict(self):
        """Serialize ChampionStrategy to dict."""
        champion = ChampionStrategy(
            iteration_num=5,
            code="# code",
            parameters={'param': 1.0},
            metrics={'sharpe_ratio': 2.0},
            success_patterns=['pattern'],
            timestamp='2025-11-04T10:00:00'
        )

        data = champion.to_dict()

        assert isinstance(data, dict)
        assert data['iteration_num'] == 5
        assert data['code'] == "# code"
        assert data['parameters'] == {'param': 1.0}
        assert data['metrics'] == {'sharpe_ratio': 2.0}
        assert data['success_patterns'] == ['pattern']
        assert data['timestamp'] == '2025-11-04T10:00:00'

    def test_champion_strategy_from_dict(self):
        """Deserialize ChampionStrategy from dict."""
        data = {
            'iteration_num': 15,
            'code': "# strategy",
            'parameters': {'param1': 1.5},
            'metrics': {'sharpe_ratio': 3.0, 'annual_return': 0.30},
            'success_patterns': ['pattern1', 'pattern2'],
            'timestamp': '2025-11-04T11:00:00'
        }

        champion = ChampionStrategy.from_dict(data)

        assert champion.iteration_num == 15
        assert champion.code == "# strategy"
        assert champion.parameters == {'param1': 1.5}
        assert champion.metrics['sharpe_ratio'] == 3.0
        assert champion.metrics['annual_return'] == 0.30
        assert len(champion.success_patterns) == 2

    def test_champion_strategy_roundtrip(self):
        """Test serialization roundtrip (to_dict -> from_dict)."""
        original = ChampionStrategy(
            iteration_num=20,
            code="# original code",
            parameters={'p1': 1.0, 'p2': 2.0},
            metrics={'sharpe_ratio': 2.5, 'max_drawdown': -0.12},
            success_patterns=['pattern1'],
            timestamp='2025-11-04T12:00:00'
        )

        # Serialize and deserialize
        data = original.to_dict()
        restored = ChampionStrategy.from_dict(data)

        # Verify all fields match
        assert restored.iteration_num == original.iteration_num
        assert restored.code == original.code
        assert restored.parameters == original.parameters
        assert restored.metrics == original.metrics
        assert restored.success_patterns == original.success_patterns
        assert restored.timestamp == original.timestamp


# ==============================================================================
# Test ChampionTracker
# ==============================================================================

class TestChampionTracker:
    """Test ChampionTracker class."""

    # --------------------------------------------------------------------------
    # Fixtures
    # --------------------------------------------------------------------------

    @pytest.fixture
    def mock_hall_of_fame(self):
        """Mock HallOfFameRepository."""
        mock = MagicMock()
        mock.get_current_champion.return_value = None  # No existing champion
        mock.add_strategy.return_value = None
        return mock

    @pytest.fixture
    def mock_history(self):
        """Mock IterationHistory."""
        mock = MagicMock()
        mock.get_successful_iterations.return_value = []
        mock.get_all.return_value = []
        return mock

    @pytest.fixture
    def mock_anti_churn(self):
        """Mock AntiChurnManager."""
        mock = MagicMock()
        mock.min_sharpe_for_champion = 0.5
        mock.get_required_improvement.return_value = 0.05  # 5% improvement
        mock.get_additive_threshold.return_value = 0.1  # +0.1 absolute threshold
        mock.track_champion_update.return_value = None
        return mock

    @pytest.fixture
    def champion_tracker(self, mock_hall_of_fame, mock_history, mock_anti_churn):
        """Create ChampionTracker with mocked dependencies."""
        with patch('src.learning.champion_tracker.os.path.exists', return_value=False):
            tracker = ChampionTracker(
                hall_of_fame=mock_hall_of_fame,
                history=mock_history,
                anti_churn=mock_anti_churn,
                champion_file="artifacts/data/champion_strategy.json",
                multi_objective_enabled=True,
                calmar_retention_ratio=0.80,
                max_drawdown_tolerance=1.10
            )
        return tracker

    @pytest.fixture
    def sample_metrics(self):
        """Sample metrics dictionary."""
        return {
            'sharpe_ratio': 2.5,
            'annual_return': 0.30,
            'max_drawdown': -0.15,
            'calmar_ratio': 0.85
        }

    # --------------------------------------------------------------------------
    # Champion Creation Tests
    # --------------------------------------------------------------------------

    def test_first_champion_creation(self, champion_tracker, mock_anti_churn, sample_metrics):
        """First strategy becomes champion when Sharpe exceeds minimum threshold."""
        # Setup: No existing champion
        assert champion_tracker.champion is None

        # Mock parameter extraction (imported from performance_attributor)
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            # Update champion
            updated = champion_tracker.update_champion(
                iteration_num=0,
                code="# first strategy",
                metrics=sample_metrics
            )

        assert updated is True
        assert champion_tracker.champion is not None
        assert champion_tracker.champion.iteration_num == 0
        assert champion_tracker.champion.metrics['sharpe_ratio'] == 2.5

        # Verify anti-churn tracking
        mock_anti_churn.track_champion_update.assert_called_once()
        call_args = mock_anti_churn.track_champion_update.call_args
        assert call_args[1]['was_updated'] is True
        assert call_args[1]['new_sharpe'] == 2.5

    def test_first_champion_rejected_low_sharpe(self, champion_tracker, mock_anti_churn):
        """First strategy rejected when Sharpe below minimum threshold."""
        # Setup: Sharpe below threshold (0.5)
        low_sharpe_metrics = {
            'sharpe_ratio': 0.3,
            'annual_return': 0.10,
            'max_drawdown': -0.20
        }

        updated = champion_tracker.update_champion(
            iteration_num=0,
            code="# weak strategy",
            metrics=low_sharpe_metrics
        )

        assert updated is False
        assert champion_tracker.champion is None

        # Verify anti-churn tracking
        mock_anti_churn.track_champion_update.assert_called_once()
        call_args = mock_anti_churn.track_champion_update.call_args
        assert call_args[1]['was_updated'] is False

    def test_create_champion_valid_metrics(self, champion_tracker, sample_metrics):
        """Create champion with valid metrics and verify persistence."""
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            champion_tracker._create_champion(
                iteration_num=10,
                code="# strategy code",
                metrics=sample_metrics
            )

        assert champion_tracker.champion is not None
        assert champion_tracker.champion.iteration_num == 10
        assert champion_tracker.champion.code == "# strategy code"
        assert champion_tracker.champion.parameters == {'param1': 1.0}
        assert champion_tracker.champion.success_patterns == ['pattern1']

        # Verify Hall of Fame save was called
        champion_tracker.hall_of_fame.add_strategy.assert_called_once()

    # --------------------------------------------------------------------------
    # Champion Update Logic Tests
    # --------------------------------------------------------------------------

    def test_champion_updated_higher_sharpe(self, champion_tracker, sample_metrics):
        """Champion updated when new strategy has higher Sharpe."""
        # Setup: Create initial champion
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# old champion",
                metrics={'sharpe_ratio': 2.0, 'max_drawdown': -0.15, 'calmar_ratio': 0.80}
            )

        # New strategy with higher Sharpe (2.5 vs 2.0)
        better_metrics = {
            'sharpe_ratio': 2.5,
            'annual_return': 0.35,
            'max_drawdown': -0.14,
            'calmar_ratio': 0.85
        }

        with patch('performance_attributor.extract_strategy_params', return_value={'param2': 2.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern2']):

            updated = champion_tracker.update_champion(
                iteration_num=5,
                code="# new champion",
                metrics=better_metrics
            )

        assert updated is True
        assert champion_tracker.champion.iteration_num == 5
        assert champion_tracker.champion.metrics['sharpe_ratio'] == 2.5

    def test_champion_not_updated_lower_sharpe(self, champion_tracker):
        """Champion NOT updated when new strategy has lower Sharpe."""
        # Setup: Create initial champion
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={'sharpe_ratio': 2.5, 'max_drawdown': -0.15, 'calmar_ratio': 0.85}
            )

        # New strategy with lower Sharpe (2.0 vs 2.5)
        worse_metrics = {
            'sharpe_ratio': 2.0,
            'annual_return': 0.25,
            'max_drawdown': -0.16,
            'calmar_ratio': 0.75
        }

        updated = champion_tracker.update_champion(
            iteration_num=5,
            code="# weaker strategy",
            metrics=worse_metrics
        )

        assert updated is False
        assert champion_tracker.champion.iteration_num == 0  # Still old champion
        assert champion_tracker.champion.metrics['sharpe_ratio'] == 2.5

    def test_champion_updated_hybrid_threshold_relative(self, champion_tracker, mock_anti_churn):
        """Champion updated via relative threshold (percentage improvement)."""
        # Setup: mock_anti_churn returns 5% improvement required
        mock_anti_churn.get_required_improvement.return_value = 0.05
        mock_anti_churn.get_additive_threshold.return_value = 0.5  # High absolute threshold

        # Create initial champion (Sharpe 2.0)
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={'sharpe_ratio': 2.0, 'max_drawdown': -0.15, 'calmar_ratio': 0.80}
            )

        # New strategy: Sharpe 2.11 (5.5% improvement, meets relative threshold)
        new_metrics = {
            'sharpe_ratio': 2.11,
            'annual_return': 0.28,
            'max_drawdown': -0.14,
            'calmar_ratio': 0.82
        }

        with patch('performance_attributor.extract_strategy_params', return_value={'param2': 2.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern2']):

            updated = champion_tracker.update_champion(
                iteration_num=10,
                code="# new champion",
                metrics=new_metrics
            )

        assert updated is True
        assert champion_tracker.champion.metrics['sharpe_ratio'] == 2.11

    def test_champion_updated_hybrid_threshold_absolute(self, champion_tracker, mock_anti_churn):
        """Champion updated via absolute threshold (additive improvement)."""
        # Setup: mock_anti_churn returns 10% improvement required (hard to meet)
        mock_anti_churn.get_required_improvement.return_value = 0.10
        mock_anti_churn.get_additive_threshold.return_value = 0.1  # +0.1 absolute

        # Create initial champion (Sharpe 2.0)
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={'sharpe_ratio': 2.0, 'max_drawdown': -0.15, 'calmar_ratio': 0.80}
            )

        # New strategy: Sharpe 2.11 (5.5% improvement, fails relative but passes absolute)
        new_metrics = {
            'sharpe_ratio': 2.11,
            'annual_return': 0.28,
            'max_drawdown': -0.14,
            'calmar_ratio': 0.82
        }

        with patch('performance_attributor.extract_strategy_params', return_value={'param2': 2.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern2']):

            updated = champion_tracker.update_champion(
                iteration_num=10,
                code="# new champion",
                metrics=new_metrics
            )

        assert updated is True
        assert champion_tracker.champion.metrics['sharpe_ratio'] == 2.11

    def test_multi_objective_validation_calmar_failure(self, champion_tracker):
        """Champion update rejected due to Calmar degradation."""
        # Setup: Create initial champion
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={
                    'sharpe_ratio': 2.0,
                    'max_drawdown': -0.15,
                    'calmar_ratio': 1.0,  # Good Calmar
                    'annual_return': 0.30
                }
            )

        # New strategy: Higher Sharpe but Calmar degrades below 80% retention
        new_metrics = {
            'sharpe_ratio': 2.15,  # Higher Sharpe
            'annual_return': 0.28,
            'max_drawdown': -0.14,
            'calmar_ratio': 0.70  # Below 0.80 (80% of 1.0)
        }

        updated = champion_tracker.update_champion(
            iteration_num=5,
            code="# brittle strategy",
            metrics=new_metrics
        )

        # Update rejected due to multi-objective validation failure
        assert updated is False
        assert champion_tracker.champion.iteration_num == 0  # Still old champion

    def test_multi_objective_validation_drawdown_failure(self, champion_tracker):
        """Champion update rejected due to excessive drawdown."""
        # Setup: Create initial champion
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={
                    'sharpe_ratio': 2.0,
                    'max_drawdown': -0.10,  # Good drawdown
                    'calmar_ratio': 0.90,
                    'annual_return': 0.30
                }
            )

        # New strategy: Higher Sharpe but drawdown too large (>10% worse)
        new_metrics = {
            'sharpe_ratio': 2.15,  # Higher Sharpe
            'annual_return': 0.32,
            'max_drawdown': -0.20,  # Much worse (2x worse, exceeds 1.10 tolerance)
            'calmar_ratio': 0.92
        }

        updated = champion_tracker.update_champion(
            iteration_num=5,
            code="# risky strategy",
            metrics=new_metrics
        )

        # Update rejected due to drawdown violation
        assert updated is False
        assert champion_tracker.champion.iteration_num == 0

    def test_multi_objective_validation_disabled(self, champion_tracker):
        """Champion update succeeds when multi-objective validation disabled."""
        # Disable multi-objective validation
        champion_tracker.multi_objective_enabled = False

        # Setup: Create initial champion
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={'sharpe_ratio': 2.0, 'max_drawdown': -0.15, 'calmar_ratio': 1.0}
            )

        # New strategy: Higher Sharpe but terrible Calmar/drawdown
        new_metrics = {
            'sharpe_ratio': 2.15,
            'annual_return': 0.32,
            'max_drawdown': -0.30,  # Very bad
            'calmar_ratio': 0.50  # Very bad
        }

        with patch('performance_attributor.extract_strategy_params', return_value={'param2': 2.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern2']):

            updated = champion_tracker.update_champion(
                iteration_num=5,
                code="# risky strategy",
                metrics=new_metrics
            )

        # Update succeeds because validation is disabled
        assert updated is True
        assert champion_tracker.champion.metrics['sharpe_ratio'] == 2.15

    # --------------------------------------------------------------------------
    # Staleness Detection Tests
    # --------------------------------------------------------------------------

    def test_staleness_no_champion(self, champion_tracker):
        """Staleness check returns False when no champion exists."""
        # No champion
        assert champion_tracker.champion is None

        with patch('src.learning.config_manager.ConfigManager') as MockConfig:
            mock_config = MockConfig.get_instance.return_value
            mock_config.load_config.return_value = None
            mock_config.get.return_value = {
                'staleness_check_interval': 50,
                'staleness_cohort_percentile': 0.10,
                'staleness_min_cohort_size': 5
            }

            result = champion_tracker.check_champion_staleness()

        assert result['should_demote'] is False
        assert result['reason'] == "No champion exists"

    def test_staleness_insufficient_data(self, champion_tracker, mock_history):
        """Staleness check returns False when insufficient history data."""
        # Setup: Create champion
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={'sharpe_ratio': 2.5}
            )

        # Mock: Not enough successful iterations (< min_cohort_size)
        mock_history.get_successful_iterations.return_value = []

        with patch('src.learning.config_manager.ConfigManager') as MockConfig:
            mock_config = MockConfig.get_instance.return_value
            mock_config.load_config.return_value = None
            mock_config.get.return_value = {
                'staleness_check_interval': 50,
                'staleness_cohort_percentile': 0.10,
                'staleness_min_cohort_size': 5
            }

            result = champion_tracker.check_champion_staleness()

        assert result['should_demote'] is False
        assert "No successful iterations" in result['reason']

    def test_staleness_champion_competitive(self, champion_tracker, mock_history):
        """Staleness check: Champion remains when competitive with cohort."""
        # Setup: Create champion with Sharpe 2.5
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={'sharpe_ratio': 2.5}
            )

        # Mock: Recent cohort with lower median Sharpe (2.0)
        # Need at least 50 records to ensure cohort size >= 5 after percentile filtering
        mock_records = []
        for i in range(50):
            record = MagicMock()
            record.iteration_num = i
            record.code = f"# code {i}"
            record.metrics = {'sharpe_ratio': 1.8 + (i * 0.01)}  # 1.8 to 2.29
            mock_records.append(record)

        mock_history.get_successful_iterations.return_value = mock_records

        with patch('src.learning.config_manager.ConfigManager') as MockConfig:
            mock_config = MockConfig.get_instance.return_value
            mock_config.load_config.return_value = None
            mock_config.get.return_value = {
                'staleness_check_interval': 50,
                'staleness_cohort_percentile': 0.10,
                'staleness_min_cohort_size': 5
            }

            result = champion_tracker.check_champion_staleness()

        # Champion Sharpe 2.5 > cohort median ~1.9 → Keep champion
        assert result['should_demote'] is False
        assert "competitive" in result['reason'].lower()
        assert result['metrics']['champion_sharpe'] == 2.5

    def test_staleness_champion_stale(self, champion_tracker, mock_history):
        """Staleness check: Champion demoted when below cohort median."""
        # Setup: Create champion with Sharpe 1.5 (weak)
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={'sharpe_ratio': 1.5}
            )

        # Mock: Recent cohort with higher median Sharpe (2.0)
        # Need at least 50 records to ensure cohort size >= 5 after percentile filtering
        mock_records = []
        for i in range(50):
            record = MagicMock()
            record.iteration_num = i
            record.code = f"# code {i}"
            record.metrics = {'sharpe_ratio': 1.8 + (i * 0.02)}  # 1.8 to 2.78
            mock_records.append(record)

        mock_history.get_successful_iterations.return_value = mock_records

        with patch('src.learning.config_manager.ConfigManager') as MockConfig:
            mock_config = MockConfig.get_instance.return_value
            mock_config.load_config.return_value = None
            mock_config.get.return_value = {
                'staleness_check_interval': 50,
                'staleness_cohort_percentile': 0.10,
                'staleness_min_cohort_size': 5
            }

            result = champion_tracker.check_champion_staleness()

        # Champion Sharpe 1.5 < cohort median → Demote champion
        assert result['should_demote'] is True
        assert "stale" in result['reason'].lower()
        assert result['metrics']['champion_sharpe'] == 1.5
        assert result['metrics']['cohort_median'] > 1.5

    def test_get_best_cohort_strategy(self, champion_tracker, mock_history):
        """Get best strategy from recent cohort for promotion."""
        # Mock: Recent successful strategies
        mock_records = []
        for i in range(20):
            record = MagicMock()
            record.iteration_num = i
            record.code = f"# strategy code {i}"
            record.metrics = {'sharpe_ratio': 2.0 + (i * 0.05)}  # 2.0 to 2.95
            mock_records.append(record)

        mock_history.get_successful_iterations.return_value = mock_records

        with patch('src.learning.config_manager.ConfigManager') as MockConfig:
            mock_config = MockConfig.get_instance.return_value
            mock_config.load_config.return_value = None
            mock_config.get.return_value = {
                'staleness_check_interval': 50,
                'staleness_cohort_percentile': 0.10
            }

            with patch('performance_attributor.extract_strategy_params', return_value={'param': 1.0}), \
                 patch('performance_attributor.extract_success_patterns', return_value=['pattern']):

                best = champion_tracker.get_best_cohort_strategy()

        # Should return strategy with highest Sharpe (iteration 19, Sharpe 2.95)
        assert best is not None
        assert best.iteration_num == 19
        assert best.metrics['sharpe_ratio'] == 2.95

    # --------------------------------------------------------------------------
    # Persistence Tests
    # --------------------------------------------------------------------------

    def test_load_champion_from_hall_of_fame(self, mock_hall_of_fame, mock_history, mock_anti_churn):
        """Load existing champion from Hall of Fame."""
        # Mock: Hall of Fame returns existing champion
        mock_genome = MagicMock()
        mock_genome.strategy_code = "# champion code"
        mock_genome.parameters = {'__iteration_num__': 10, 'param1': 1.0}
        mock_genome.metrics = {'sharpe_ratio': 2.5, 'max_drawdown': -0.15}
        mock_genome.success_patterns = ['pattern1', 'pattern2']
        mock_genome.created_at = '2025-11-04T10:00:00'

        mock_hall_of_fame.get_current_champion.return_value = mock_genome

        with patch('src.learning.champion_tracker.os.path.exists', return_value=False):
            tracker = ChampionTracker(
                hall_of_fame=mock_hall_of_fame,
                history=mock_history,
                anti_churn=mock_anti_churn
            )

        # Verify champion loaded
        assert tracker.champion is not None
        assert tracker.champion.iteration_num == 10
        assert tracker.champion.code == "# champion code"
        assert tracker.champion.parameters == {'param1': 1.0}  # __iteration_num__ stripped
        assert tracker.champion.metrics['sharpe_ratio'] == 2.5

    def test_load_champion_legacy_migration(self, mock_hall_of_fame, mock_history, mock_anti_churn):
        """Load champion from legacy file and migrate to Hall of Fame."""
        # Mock: No champion in Hall of Fame
        mock_hall_of_fame.get_current_champion.return_value = None

        # Mock: Legacy champion file exists
        legacy_data = {
            'iteration_num': 5,
            'code': '# legacy champion',
            'parameters': {'param1': 1.0},
            'metrics': {'sharpe_ratio': 2.0},
            'success_patterns': ['pattern1'],
            'timestamp': '2025-11-04T09:00:00'
        }

        with patch('src.learning.champion_tracker.os.path.exists', return_value=True), \
             patch('builtins.open', create=True) as mock_open, \
             patch('json.load', return_value=legacy_data):

            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            tracker = ChampionTracker(
                hall_of_fame=mock_hall_of_fame,
                history=mock_history,
                anti_churn=mock_anti_churn
            )

        # Verify champion loaded
        assert tracker.champion is not None
        assert tracker.champion.iteration_num == 5

        # Verify migration to Hall of Fame
        mock_hall_of_fame.add_strategy.assert_called_once()

    def test_load_champion_missing_file(self, mock_hall_of_fame, mock_history, mock_anti_churn):
        """Handle missing champion file gracefully."""
        # Mock: No champion in Hall of Fame
        mock_hall_of_fame.get_current_champion.return_value = None

        with patch('src.learning.champion_tracker.os.path.exists', return_value=False):
            tracker = ChampionTracker(
                hall_of_fame=mock_hall_of_fame,
                history=mock_history,
                anti_churn=mock_anti_churn
            )

        # Verify no champion loaded
        assert tracker.champion is None

    def test_save_champion_to_hall_of_fame(self, champion_tracker):
        """Save champion to Hall of Fame."""
        # Create champion
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            champion_tracker._create_champion(
                iteration_num=10,
                code="# strategy",
                metrics={'sharpe_ratio': 2.5}
            )

        # Verify Hall of Fame save was called
        champion_tracker.hall_of_fame.add_strategy.assert_called_once()

        # Verify call arguments
        call_args = champion_tracker.hall_of_fame.add_strategy.call_args
        assert call_args[1]['template_name'] == 'autonomous_generated'
        assert call_args[1]['strategy_code'] == "# strategy"
        assert '__iteration_num__' in call_args[1]['parameters']
        assert call_args[1]['parameters']['__iteration_num__'] == 10

    # --------------------------------------------------------------------------
    # Integration Tests
    # --------------------------------------------------------------------------

    def test_integration_with_iteration_history(self, champion_tracker, mock_history):
        """ChampionTracker works with IterationHistory for staleness checks."""
        # Setup: Create champion
        with patch('performance_attributor.extract_strategy_params', return_value={}), \
             patch('performance_attributor.extract_success_patterns', return_value=[]):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={'sharpe_ratio': 2.5}
            )

        # Mock history returns recent strategies
        mock_records = []
        for i in range(10):
            record = MagicMock()
            record.iteration_num = i
            record.metrics = {'sharpe_ratio': 2.0 + (i * 0.05)}
            mock_records.append(record)

        mock_history.get_successful_iterations.return_value = mock_records

        with patch('src.learning.config_manager.ConfigManager') as MockConfig:
            mock_config = MockConfig.get_instance.return_value
            mock_config.load_config.return_value = None
            mock_config.get.return_value = {
                'staleness_check_interval': 50,
                'staleness_cohort_percentile': 0.10,
                'staleness_min_cohort_size': 5
            }

            result = champion_tracker.check_champion_staleness()

        # Verify history was queried
        mock_history.get_successful_iterations.assert_called_once()
        assert result is not None

    def test_integration_with_anti_churn_manager(self, champion_tracker, mock_anti_churn):
        """ChampionTracker uses AntiChurnManager for dynamic thresholds."""
        # Setup: Create initial champion
        with patch('performance_attributor.extract_strategy_params', return_value={}), \
             patch('performance_attributor.extract_success_patterns', return_value=[]):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={'sharpe_ratio': 2.0, 'max_drawdown': -0.15, 'calmar_ratio': 0.85}
            )

        # Attempt update
        new_metrics = {
            'sharpe_ratio': 2.11,
            'max_drawdown': -0.14,
            'calmar_ratio': 0.87
        }

        with patch('performance_attributor.extract_strategy_params', return_value={}), \
             patch('performance_attributor.extract_success_patterns', return_value=[]):

            champion_tracker.update_champion(
                iteration_num=10,
                code="# new strategy",
                metrics=new_metrics
            )

        # Verify AntiChurnManager methods were called
        mock_anti_churn.get_required_improvement.assert_called_once()
        mock_anti_churn.get_additive_threshold.assert_called_once()
        mock_anti_churn.track_champion_update.assert_called()

    def test_compare_with_champion(self, champion_tracker):
        """Compare current strategy with champion for attribution."""
        # Setup: Create champion
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 1.0}), \
             patch('performance_attributor.extract_success_patterns', return_value=['pattern1']):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={'sharpe_ratio': 2.5}
            )

        # Mock: performance_attributor functions
        with patch('performance_attributor.extract_strategy_params', return_value={'param1': 2.0}), \
             patch('performance_attributor.compare_strategies', return_value={
                 'assessment': 'improvement',
                 'performance_delta': 0.2,
                 'critical_changes': [{'parameter': 'param1', 'from': 1.0, 'to': 2.0}]
             }):

            attribution = champion_tracker.compare_with_champion(
                current_code="# new code",
                current_metrics={'sharpe_ratio': 2.7}
            )

        assert attribution is not None
        assert attribution['assessment'] == 'improvement'
        assert attribution['performance_delta'] == 0.2

    def test_compare_with_champion_no_champion(self, champion_tracker):
        """Comparison returns None when no champion exists."""
        # No champion
        assert champion_tracker.champion is None

        attribution = champion_tracker.compare_with_champion(
            current_code="# code",
            current_metrics={'sharpe_ratio': 2.0}
        )

        assert attribution is None

    def test_demote_champion_to_hall_of_fame(self, champion_tracker):
        """Demote current champion (logging only)."""
        # Setup: Create champion
        with patch('performance_attributor.extract_strategy_params', return_value={}), \
             patch('performance_attributor.extract_success_patterns', return_value=[]):

            champion_tracker._create_champion(
                iteration_num=10,
                code="# champion",
                metrics={'sharpe_ratio': 2.5}
            )

        # Demote champion
        champion_tracker.demote_champion_to_hall_of_fame()

        # Champion still exists (demotion is just logging)
        assert champion_tracker.champion is not None

    def test_promote_to_champion(self, champion_tracker):
        """Promote cohort strategy to new champion."""
        # Create new strategy
        new_champion = ChampionStrategy(
            iteration_num=20,
            code="# new champion",
            parameters={'param': 2.0},
            metrics={'sharpe_ratio': 2.8, 'max_drawdown': -0.12},
            success_patterns=['pattern'],
            timestamp='2025-11-04T12:00:00'
        )

        # Promote to champion
        champion_tracker.promote_to_champion(new_champion)

        # Verify promotion
        assert champion_tracker.champion is not None
        assert champion_tracker.champion.iteration_num == 20
        assert champion_tracker.champion.metrics['sharpe_ratio'] == 2.8

        # Verify Hall of Fame save
        champion_tracker.hall_of_fame.add_strategy.assert_called()

    def test_promote_to_champion_none_strategy(self, champion_tracker):
        """Handle None strategy promotion gracefully."""
        # Attempt to promote None
        champion_tracker.promote_to_champion(None)

        # Champion should remain None
        assert champion_tracker.champion is None

    # --------------------------------------------------------------------------
    # Edge Cases and Error Handling
    # --------------------------------------------------------------------------

    def test_update_champion_missing_sharpe_ratio(self, champion_tracker):
        """Handle missing sharpe_ratio in metrics."""
        # Metrics without sharpe_ratio
        invalid_metrics = {
            'annual_return': 0.25,
            'max_drawdown': -0.15
        }

        updated = champion_tracker.update_champion(
            iteration_num=0,
            code="# strategy",
            metrics=invalid_metrics
        )

        # Update fails due to missing Sharpe (defaults to 0)
        assert updated is False

    def test_multi_objective_validation_missing_metrics(self, champion_tracker):
        """Multi-objective validation rejects strategies with missing required metrics."""
        # Setup: Create champion (bypass validation by using _create_champion directly)
        with patch('performance_attributor.extract_strategy_params', return_value={}), \
             patch('performance_attributor.extract_success_patterns', return_value=[]):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={'sharpe_ratio': 2.0, 'calmar_ratio': 1.5, 'max_drawdown': -0.15}
            )

        # New strategy: Missing required metrics (calmar_ratio, max_drawdown)
        new_metrics = {'sharpe_ratio': 2.15}

        with patch('performance_attributor.extract_strategy_params', return_value={}), \
             patch('performance_attributor.extract_success_patterns', return_value=[]):

            updated = champion_tracker.update_champion(
                iteration_num=5,
                code="# new strategy",
                metrics=new_metrics
            )

        # Update fails due to missing required metrics (validation kicks in)
        assert updated is False

    def test_staleness_config_error_handling(self, champion_tracker):
        """Staleness check handles config loading errors gracefully."""
        # Setup: Create champion
        with patch('performance_attributor.extract_strategy_params', return_value={}), \
             patch('performance_attributor.extract_success_patterns', return_value=[]):

            champion_tracker._create_champion(
                iteration_num=0,
                code="# champion",
                metrics={'sharpe_ratio': 2.5}
            )

        # Mock: ConfigManager raises exception
        with patch('src.learning.config_manager.ConfigManager') as MockConfig:
            MockConfig.get_instance.side_effect = Exception("Config error")

            result = champion_tracker.check_champion_staleness()

        # Should return safe default (no demotion)
        assert result['should_demote'] is False
        assert "Configuration error" in result['reason']

    def test_get_best_cohort_strategy_no_data(self, champion_tracker, mock_history):
        """get_best_cohort_strategy returns None when no successful iterations."""
        mock_history.get_successful_iterations.return_value = []

        with patch('src.learning.config_manager.ConfigManager') as MockConfig:
            mock_config = MockConfig.get_instance.return_value
            mock_config.load_config.return_value = None
            mock_config.get.return_value = {
                'staleness_check_interval': 50,
                'staleness_cohort_percentile': 0.10
            }

            best = champion_tracker.get_best_cohort_strategy()

        assert best is None
