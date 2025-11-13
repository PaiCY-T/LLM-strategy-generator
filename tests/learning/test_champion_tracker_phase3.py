"""Phase 3: ChampionTracker Hybrid Architecture Tests

Tests the refactored ChampionTracker methods that support both LLM and Factor Graph champions:
- _create_champion() dual path logic
- update_champion() with both generation methods
- promote_to_champion() handling Strategy DAG objects
- get_best_cohort_strategy() hybrid support
- _load_champion() hybrid loading
- Transition scenarios (LLM ↔ Factor Graph)

Total: 20+ comprehensive tests covering all edge cases and scenarios.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime
from typing import Dict, Any, List

# Import the classes we're testing
from src.learning.champion_tracker import ChampionTracker, ChampionStrategy
from src.learning.iteration_history import IterationRecord


class MockStrategy:
    """Mock Strategy DAG object for testing Factor Graph champions."""
    def __init__(self, strategy_id: str, generation: int, factors: Dict[str, Any] = None):
        self.id = strategy_id
        self.generation = generation
        self.factors = factors or {
            'rsi_14': Mock(params={'period': 14, 'overbought': 70}),
            'ma_20': Mock(params={'window': 20, 'method': 'sma'})
        }

    def __repr__(self):
        return f"MockStrategy(id='{self.id}', generation={self.generation})"


class TestCreateChampion(unittest.TestCase):
    """Test _create_champion() method with dual path logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.hall_of_fame = Mock()
        self.hall_of_fame.get_current_champion.return_value = None  # No champion on init
        self.history = Mock()
        self.anti_churn = Mock()

        # Patch CHAMPION_FILE to avoid file system access
        with patch('src.learning.champion_tracker.os.path.exists', return_value=False):
            self.tracker = ChampionTracker(
                hall_of_fame=self.hall_of_fame,
                history=self.history,
                anti_churn=self.anti_churn
            )

    def test_create_llm_champion(self):
        """Test creating LLM champion with code extraction."""
        code = "data.get('price:收盤價').ewm(span=20).mean()"
        metrics = {'sharpe_ratio': 1.5, 'max_drawdown': -0.10}

        with patch('src.learning.champion_tracker.extract_strategy_params') as mock_params, \
             patch('src.learning.champion_tracker.extract_success_patterns') as mock_patterns:

            mock_params.return_value = {'dataset': 'price:收盤價'}
            mock_patterns.return_value = ['momentum', 'ewm']

            self.tracker._create_champion(
                iteration_num=10,
                generation_method="llm",
                metrics=metrics,
                code=code
            )

            # Verify champion created correctly
            self.assertIsNotNone(self.tracker.champion)
            self.assertEqual(self.tracker.champion.generation_method, "llm")
            self.assertEqual(self.tracker.champion.code, code)
            self.assertEqual(self.tracker.champion.iteration_num, 10)
            self.assertIsNone(self.tracker.champion.strategy_id)
            self.assertIsNone(self.tracker.champion.strategy_generation)

    def test_create_factor_graph_champion(self):
        """Test creating Factor Graph champion with DAG extraction."""
        strategy = MockStrategy(strategy_id="momentum_v2", generation=2)
        metrics = {'sharpe_ratio': 2.0, 'max_drawdown': -0.12}

        self.tracker._create_champion(
            iteration_num=15,
            generation_method="factor_graph",
            metrics=metrics,
            strategy=strategy,
            strategy_id="momentum_v2",
            strategy_generation=2
        )

        # Verify champion created correctly
        self.assertIsNotNone(self.tracker.champion)
        self.assertEqual(self.tracker.champion.generation_method, "factor_graph")
        self.assertIsNone(self.tracker.champion.code)
        self.assertEqual(self.tracker.champion.strategy_id, "momentum_v2")
        self.assertEqual(self.tracker.champion.strategy_generation, 2)
        self.assertEqual(self.tracker.champion.iteration_num, 15)

    def test_create_champion_missing_llm_code(self):
        """Test creating LLM champion without code raises ValueError."""
        metrics = {'sharpe_ratio': 1.5}

        with self.assertRaises(ValueError) as context:
            self.tracker._create_champion(
                iteration_num=10,
                generation_method="llm",
                metrics=metrics
                # Missing code parameter
            )

        self.assertIn("LLM champion requires 'code'", str(context.exception))

    def test_create_champion_missing_factor_graph_params(self):
        """Test creating Factor Graph champion without strategy raises ValueError."""
        metrics = {'sharpe_ratio': 2.0}

        with self.assertRaises(ValueError) as context:
            self.tracker._create_champion(
                iteration_num=15,
                generation_method="factor_graph",
                metrics=metrics
                # Missing strategy, strategy_id, strategy_generation
            )

        self.assertIn("Factor Graph champion requires 'strategy'", str(context.exception))


class TestUpdateChampion(unittest.TestCase):
    """Test update_champion() method with both generation methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.hall_of_fame = Mock()
        self.hall_of_fame.get_current_champion.return_value = None  # No champion on init
        self.history = Mock()
        self.anti_churn = Mock()
        self.anti_churn.min_sharpe_for_champion = 0.5
        self.anti_churn.get_required_improvement = Mock(return_value=0.05)
        self.anti_churn.get_additive_threshold = Mock(return_value=0.10)
        self.anti_churn.track_champion_update = Mock()

        # Patch CHAMPION_FILE to avoid file system access
        with patch('src.learning.champion_tracker.os.path.exists', return_value=False):
            self.tracker = ChampionTracker(
                hall_of_fame=self.hall_of_fame,
                history=self.history,
                anti_churn=self.anti_churn,
                multi_objective_enabled=False  # Disable for simpler testing
            )

    def test_first_llm_champion_creation(self):
        """Test first LLM champion creation when no champion exists."""
        code = "data.get('price:收盤價')"
        metrics = {'sharpe_ratio': 1.5, 'max_drawdown': -0.10}

        with patch('src.learning.champion_tracker.extract_strategy_params') as mock_params, \
             patch('src.learning.champion_tracker.extract_success_patterns') as mock_patterns:

            mock_params.return_value = {}
            mock_patterns.return_value = []

            updated = self.tracker.update_champion(
                iteration_num=1,
                metrics=metrics,
                generation_method="llm",
                code=code
            )

            self.assertTrue(updated)
            self.assertIsNotNone(self.tracker.champion)
            self.assertEqual(self.tracker.champion.generation_method, "llm")

    def test_first_factor_graph_champion_creation(self):
        """Test first Factor Graph champion creation when no champion exists."""
        strategy = MockStrategy(strategy_id="momentum_v1", generation=1)
        metrics = {'sharpe_ratio': 1.8, 'max_drawdown': -0.12}

        updated = self.tracker.update_champion(
            iteration_num=1,
            metrics=metrics,
            generation_method="factor_graph",
            strategy=strategy,
            strategy_id="momentum_v1",
            strategy_generation=1
        )

        self.assertTrue(updated)
        self.assertIsNotNone(self.tracker.champion)
        self.assertEqual(self.tracker.champion.generation_method, "factor_graph")
        self.assertEqual(self.tracker.champion.strategy_id, "momentum_v1")

    def test_llm_update_with_invalid_generation_method(self):
        """Test update_champion() with invalid generation_method raises ValueError."""
        metrics = {'sharpe_ratio': 1.5}

        with self.assertRaises(ValueError) as context:
            self.tracker.update_champion(
                iteration_num=1,
                metrics=metrics,
                generation_method="invalid_method"
            )

        self.assertIn("generation_method must be 'llm' or 'factor_graph'", str(context.exception))

    def test_factor_graph_update_missing_parameters(self):
        """Test Factor Graph update without required parameters raises ValueError."""
        metrics = {'sharpe_ratio': 2.0}

        with self.assertRaises(ValueError) as context:
            self.tracker.update_champion(
                iteration_num=1,
                metrics=metrics,
                generation_method="factor_graph"
                # Missing strategy, strategy_id, strategy_generation
            )

        self.assertIn("Factor Graph champion update requires 'strategy'", str(context.exception))


class TestPromoteToChampion(unittest.TestCase):
    """Test promote_to_champion() method with both ChampionStrategy and Strategy DAG."""

    def setUp(self):
        """Set up test fixtures."""
        self.hall_of_fame = Mock()
        self.hall_of_fame.get_current_champion.return_value = None  # No champion on init
        self.history = Mock()
        self.anti_churn = Mock()

        # Patch CHAMPION_FILE to avoid file system access
        with patch('src.learning.champion_tracker.os.path.exists', return_value=False):
            self.tracker = ChampionTracker(
                hall_of_fame=self.hall_of_fame,
                history=self.history,
                anti_churn=self.anti_churn
            )

    def test_promote_champion_strategy_object(self):
        """Test promoting ChampionStrategy object (existing behavior)."""
        champion = ChampionStrategy(
            iteration_num=50,
            generation_method="llm",
            code="# strategy code",
            metrics={'sharpe_ratio': 2.5, 'max_drawdown': -0.10},
            timestamp=datetime.now().isoformat()
        )

        self.tracker.promote_to_champion(champion)

        self.assertEqual(self.tracker.champion, champion)
        self.hall_of_fame.add_strategy.assert_called_once()

    def test_promote_strategy_dag_object(self):
        """Test promoting Strategy DAG object (new behavior)."""
        strategy = MockStrategy(strategy_id="momentum_v3", generation=3)
        metrics = {'sharpe_ratio': 2.8, 'max_drawdown': -0.08}

        self.tracker.promote_to_champion(
            strategy=strategy,
            iteration_num=80,
            metrics=metrics
        )

        self.assertIsNotNone(self.tracker.champion)
        self.assertEqual(self.tracker.champion.generation_method, "factor_graph")
        self.assertEqual(self.tracker.champion.strategy_id, "momentum_v3")
        self.assertEqual(self.tracker.champion.strategy_generation, 3)
        self.assertEqual(self.tracker.champion.iteration_num, 80)

    def test_promote_strategy_dag_missing_iteration_num(self):
        """Test promoting Strategy DAG without iteration_num raises ValueError."""
        strategy = MockStrategy(strategy_id="momentum_v3", generation=3)
        metrics = {'sharpe_ratio': 2.8}

        with self.assertRaises(ValueError) as context:
            self.tracker.promote_to_champion(
                strategy=strategy,
                # Missing iteration_num
                metrics=metrics
            )

        self.assertIn("iteration_num is required", str(context.exception))

    def test_promote_invalid_object_type(self):
        """Test promoting object without id/generation raises TypeError."""
        invalid_object = {"not": "a strategy"}

        with self.assertRaises(TypeError) as context:
            self.tracker.promote_to_champion(
                strategy=invalid_object,
                iteration_num=80,
                metrics={'sharpe_ratio': 2.0}
            )

        self.assertIn("Strategy object must have 'id' and 'generation'", str(context.exception))


class TestGetBestCohortStrategy(unittest.TestCase):
    """Test get_best_cohort_strategy() method with hybrid support."""

    def setUp(self):
        """Set up test fixtures."""
        self.hall_of_fame = Mock()
        self.hall_of_fame.get_current_champion.return_value = None  # No champion on init
        self.history = Mock()
        self.anti_churn = Mock()

        # Patch CHAMPION_FILE to avoid file system access
        with patch('src.learning.champion_tracker.os.path.exists', return_value=False):
            self.tracker = ChampionTracker(
                hall_of_fame=self.hall_of_fame,
                history=self.history,
                anti_churn=self.anti_churn
            )

    @patch('src.learning.champion_tracker.ConfigManager')
    @patch('src.learning.champion_tracker.np')
    def test_cohort_with_llm_strategies(self, mock_np, mock_config_mgr):
        """Test get_best_cohort_strategy() with LLM strategies."""
        # Mock configuration
        mock_config_instance = Mock()
        mock_config_instance.get.return_value = {
            'staleness_check_interval': 10,
            'staleness_cohort_percentile': 0.10
        }
        mock_config_mgr.get_instance.return_value = mock_config_instance

        # Mock iteration history with LLM strategies
        llm_records = [
            IterationRecord(
                iteration_num=i,
                generation_method="llm",
                strategy_code=f"# strategy {i}",
                metrics={'sharpe_ratio': 1.5 + i*0.1},
                classification_level="LEVEL_3",
                timestamp=datetime.now().isoformat()
            )
            for i in range(1, 11)
        ]
        self.history.get_successful_iterations.return_value = llm_records

        # Mock numpy percentile
        mock_np.percentile.return_value = 1.8

        with patch('src.learning.champion_tracker.extract_strategy_params') as mock_params, \
             patch('src.learning.champion_tracker.extract_success_patterns') as mock_patterns:

            mock_params.return_value = {}
            mock_patterns.return_value = []

            best = self.tracker.get_best_cohort_strategy()

            self.assertIsNotNone(best)
            self.assertEqual(best.generation_method, "llm")
            self.assertEqual(best.iteration_num, 10)  # Highest Sharpe

    @patch('src.learning.champion_tracker.ConfigManager')
    @patch('src.learning.champion_tracker.np')
    def test_cohort_with_factor_graph_strategies(self, mock_np, mock_config_mgr):
        """Test get_best_cohort_strategy() with Factor Graph strategies."""
        # Mock configuration
        mock_config_instance = Mock()
        mock_config_instance.get.return_value = {
            'staleness_check_interval': 10,
            'staleness_cohort_percentile': 0.10
        }
        mock_config_mgr.get_instance.return_value = mock_config_instance

        # Mock iteration history with Factor Graph strategies
        fg_records = [
            IterationRecord(
                iteration_num=i,
                generation_method="factor_graph",
                strategy_id=f"momentum_v{i}",
                strategy_generation=i,
                metrics={'sharpe_ratio': 2.0 + i*0.1},
                classification_level="LEVEL_3",
                timestamp=datetime.now().isoformat()
            )
            for i in range(1, 11)
        ]
        self.history.get_successful_iterations.return_value = fg_records

        # Mock numpy percentile
        mock_np.percentile.return_value = 2.5

        best = self.tracker.get_best_cohort_strategy()

        self.assertIsNotNone(best)
        self.assertEqual(best.generation_method, "factor_graph")
        self.assertEqual(best.strategy_id, "momentum_v10")
        self.assertEqual(best.iteration_num, 10)  # Highest Sharpe


class TestLoadChampion(unittest.TestCase):
    """Test _load_champion() method with hybrid loading."""

    def setUp(self):
        """Set up test fixtures."""
        self.hall_of_fame = Mock()
        self.history = Mock()
        self.anti_churn = Mock()

    def test_load_llm_champion_from_hall_of_fame(self):
        """Test loading LLM champion from Hall of Fame."""
        # Mock StrategyGenome with LLM champion data
        mock_genome = Mock()
        mock_genome.strategy_code = "# LLM strategy code"
        mock_genome.parameters = {
            '__iteration_num__': 25,
            '__generation_method__': 'llm',
            'dataset': 'price:收盤價'
        }
        mock_genome.metrics = {'sharpe_ratio': 1.8, 'max_drawdown': -0.12}
        mock_genome.success_patterns = ['momentum']
        mock_genome.created_at = datetime.now().isoformat()

        self.hall_of_fame.get_current_champion.return_value = mock_genome

        tracker = ChampionTracker(
            hall_of_fame=self.hall_of_fame,
            history=self.history,
            anti_churn=self.anti_churn
        )

        self.assertIsNotNone(tracker.champion)
        self.assertEqual(tracker.champion.generation_method, "llm")
        self.assertEqual(tracker.champion.code, "# LLM strategy code")
        self.assertEqual(tracker.champion.iteration_num, 25)
        self.assertIsNone(tracker.champion.strategy_id)

    def test_load_factor_graph_champion_from_hall_of_fame(self):
        """Test loading Factor Graph champion from Hall of Fame."""
        # Mock StrategyGenome with Factor Graph champion data
        mock_genome = Mock()
        mock_genome.strategy_code = None
        mock_genome.parameters = {
            '__iteration_num__': 30,
            '__generation_method__': 'factor_graph',
            '__strategy_id__': 'momentum_v2',
            '__strategy_generation__': 2,
            'rsi_14': {'period': 14}
        }
        mock_genome.metrics = {'sharpe_ratio': 2.2, 'max_drawdown': -0.10}
        mock_genome.success_patterns = ['RSI', 'Signal']
        mock_genome.created_at = datetime.now().isoformat()

        self.hall_of_fame.get_current_champion.return_value = mock_genome

        tracker = ChampionTracker(
            hall_of_fame=self.hall_of_fame,
            history=self.history,
            anti_churn=self.anti_churn
        )

        self.assertIsNotNone(tracker.champion)
        self.assertEqual(tracker.champion.generation_method, "factor_graph")
        self.assertIsNone(tracker.champion.code)
        self.assertEqual(tracker.champion.strategy_id, "momentum_v2")
        self.assertEqual(tracker.champion.strategy_generation, 2)
        self.assertEqual(tracker.champion.iteration_num, 30)


class TestTransitionScenarios(unittest.TestCase):
    """Test transition scenarios between LLM and Factor Graph champions."""

    def setUp(self):
        """Set up test fixtures."""
        self.hall_of_fame = Mock()
        self.hall_of_fame.get_current_champion.return_value = None  # No champion on init
        self.history = Mock()
        self.anti_churn = Mock()
        self.anti_churn.min_sharpe_for_champion = 0.5
        self.anti_churn.get_required_improvement = Mock(return_value=0.05)
        self.anti_churn.get_additive_threshold = Mock(return_value=0.10)
        self.anti_churn.track_champion_update = Mock()

        # Patch CHAMPION_FILE to avoid file system access
        with patch('src.learning.champion_tracker.os.path.exists', return_value=False):
            self.tracker = ChampionTracker(
                hall_of_fame=self.hall_of_fame,
                history=self.history,
                anti_churn=self.anti_churn,
                multi_objective_enabled=False
            )

    def test_transition_llm_to_factor_graph(self):
        """Test transition from LLM champion to Factor Graph champion."""
        # Create initial LLM champion
        with patch('src.learning.champion_tracker.extract_strategy_params') as mock_params, \
             patch('src.learning.champion_tracker.extract_success_patterns') as mock_patterns:

            mock_params.return_value = {}
            mock_patterns.return_value = []

            self.tracker.update_champion(
                iteration_num=10,
                metrics={'sharpe_ratio': 1.5, 'max_drawdown': -0.10},
                generation_method="llm",
                code="# LLM strategy"
            )

        self.assertEqual(self.tracker.champion.generation_method, "llm")

        # Update to Factor Graph champion
        strategy = MockStrategy(strategy_id="momentum_v1", generation=1)
        self.tracker.update_champion(
            iteration_num=20,
            metrics={'sharpe_ratio': 2.5, 'max_drawdown': -0.08},  # Much better
            generation_method="factor_graph",
            strategy=strategy,
            strategy_id="momentum_v1",
            strategy_generation=1
        )

        self.assertEqual(self.tracker.champion.generation_method, "factor_graph")
        self.assertEqual(self.tracker.champion.strategy_id, "momentum_v1")

    def test_transition_factor_graph_to_llm(self):
        """Test transition from Factor Graph champion to LLM champion."""
        # Create initial Factor Graph champion
        strategy = MockStrategy(strategy_id="momentum_v1", generation=1)
        self.tracker.update_champion(
            iteration_num=10,
            metrics={'sharpe_ratio': 1.8, 'max_drawdown': -0.12},
            generation_method="factor_graph",
            strategy=strategy,
            strategy_id="momentum_v1",
            strategy_generation=1
        )

        self.assertEqual(self.tracker.champion.generation_method, "factor_graph")

        # Update to LLM champion
        with patch('src.learning.champion_tracker.extract_strategy_params') as mock_params, \
             patch('src.learning.champion_tracker.extract_success_patterns') as mock_patterns:

            mock_params.return_value = {}
            mock_patterns.return_value = []

            self.tracker.update_champion(
                iteration_num=20,
                metrics={'sharpe_ratio': 2.8, 'max_drawdown': -0.08},  # Much better
                generation_method="llm",
                code="# Better LLM strategy"
            )

        self.assertEqual(self.tracker.champion.generation_method, "llm")
        self.assertEqual(self.tracker.champion.code, "# Better LLM strategy")

    @patch('src.learning.champion_tracker.ConfigManager')
    @patch('src.learning.champion_tracker.np')
    def test_mixed_cohort_selection(self, mock_np, mock_config_mgr):
        """Test cohort selection with mixed LLM and Factor Graph strategies."""
        # Mock configuration
        mock_config_instance = Mock()
        mock_config_instance.get.return_value = {
            'staleness_check_interval': 10,
            'staleness_cohort_percentile': 0.10
        }
        mock_config_mgr.get_instance.return_value = mock_config_instance

        # Mock iteration history with mixed strategies
        mixed_records = [
            # LLM strategies
            IterationRecord(
                iteration_num=1,
                generation_method="llm",
                strategy_code="# strategy 1",
                metrics={'sharpe_ratio': 1.5},
                classification_level="LEVEL_3",
                timestamp=datetime.now().isoformat()
            ),
            # Factor Graph strategies
            IterationRecord(
                iteration_num=2,
                generation_method="factor_graph",
                strategy_id="momentum_v1",
                strategy_generation=1,
                metrics={'sharpe_ratio': 2.5},  # Best
                classification_level="LEVEL_3",
                timestamp=datetime.now().isoformat()
            ),
        ]
        self.history.get_successful_iterations.return_value = mixed_records

        # Mock numpy percentile
        mock_np.percentile.return_value = 1.0

        best = self.tracker.get_best_cohort_strategy()

        # Should select Factor Graph strategy (highest Sharpe)
        self.assertIsNotNone(best)
        self.assertEqual(best.generation_method, "factor_graph")
        self.assertEqual(best.iteration_num, 2)

    def test_save_and_load_hybrid_champion(self):
        """Test save/load cycle preserves generation_method."""
        # Save Factor Graph champion
        strategy = MockStrategy(strategy_id="momentum_v2", generation=2)
        self.tracker.update_champion(
            iteration_num=15,
            metrics={'sharpe_ratio': 2.2, 'max_drawdown': -0.10},
            generation_method="factor_graph",
            strategy=strategy,
            strategy_id="momentum_v2",
            strategy_generation=2
        )

        # Verify save was called with correct metadata
        self.hall_of_fame.add_strategy.assert_called()
        call_args = self.hall_of_fame.add_strategy.call_args
        params = call_args[1]['parameters']

        self.assertEqual(params['__generation_method__'], "factor_graph")
        self.assertEqual(params['__strategy_id__'], "momentum_v2")
        self.assertEqual(params['__strategy_generation__'], 2)


if __name__ == '__main__':
    unittest.main()
