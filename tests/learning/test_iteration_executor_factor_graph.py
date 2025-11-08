"""
Unit Tests for Factor Graph Integration in IterationExecutor

Tests the 6 changes implemented for Factor Graph support:
1. Internal registries (_strategy_registry, _factor_logic_registry)
2. _generate_with_factor_graph() - template creation and mutation
3. _create_template_strategy() - baseline strategy
4. Factor Graph execution path
5. Champion update with Factor Graph parameters (CRITICAL)
6. Registry cleanup

Author: Claude
Date: 2025-11-08
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

from src.learning.iteration_executor import IterationExecutor
from src.backtest.executor import ExecutionResult
from src.learning.champion_tracker import ChampionStrategy


@pytest.fixture
def mock_components():
    """Create mock components for IterationExecutor."""
    return {
        'llm_client': Mock(),
        'feedback_generator': Mock(),
        'backtest_executor': Mock(),
        'champion_tracker': Mock(),
        'history': Mock(),
        'config': {
            'innovation_rate': 0,  # Force Factor Graph
            'history_window': 5,
            'timeout_seconds': 420,
            'start_date': '2018-01-01',
            'end_date': '2024-12-31',
            'fee_ratio': 0.001425,
            'tax_ratio': 0.003,
            'resample': 'M',
        }
    }


@pytest.fixture
def executor(mock_components):
    """Create IterationExecutor with mocked dependencies."""
    return IterationExecutor(**mock_components)


class TestInternalRegistries:
    """Test Change #1: Internal registries initialization."""

    def test_strategy_registry_initialized(self, executor):
        """Verify _strategy_registry is initialized as empty dict."""
        assert hasattr(executor, '_strategy_registry')
        assert isinstance(executor._strategy_registry, dict)
        assert len(executor._strategy_registry) == 0

    def test_factor_logic_registry_initialized(self, executor):
        """Verify _factor_logic_registry is initialized as empty dict."""
        assert hasattr(executor, '_factor_logic_registry')
        assert isinstance(executor._factor_logic_registry, dict)
        assert len(executor._factor_logic_registry) == 0


class TestCreateTemplateStrategy:
    """Test Change #3: _create_template_strategy() method."""

    @patch('src.learning.iteration_executor.FactorRegistry')
    @patch('src.learning.iteration_executor.Strategy')
    def test_create_template_strategy_structure(self, mock_strategy_class, mock_registry_class, executor):
        """Test template creation with correct structure."""
        # Setup mocks
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry

        mock_strategy = MagicMock()
        mock_strategy_class.return_value = mock_strategy

        # Create mock factors
        mock_momentum = MagicMock()
        mock_momentum.id = "momentum_factor_id"
        mock_breakout = MagicMock()
        mock_breakout.id = "breakout_factor_id"
        mock_trailing_stop = MagicMock()
        mock_trailing_stop.id = "trailing_stop_factor_id"

        mock_registry.create_factor.side_effect = [mock_momentum, mock_breakout, mock_trailing_stop]

        # Execute
        result = executor._create_template_strategy(iteration_num=5)

        # Verify Strategy created with correct ID and generation
        mock_strategy_class.assert_called_once_with(id="template_5", generation=0)

        # Verify 3 factors created
        assert mock_registry.create_factor.call_count == 3

        # Verify momentum factor
        mock_registry.create_factor.assert_any_call(
            "momentum_factor",
            parameters={"momentum_period": 20}
        )

        # Verify breakout factor
        mock_registry.create_factor.assert_any_call(
            "breakout_factor",
            parameters={"entry_window": 20}
        )

        # Verify trailing stop factor
        mock_registry.create_factor.assert_any_call(
            "trailing_stop_factor",
            parameters={"trail_percent": 0.10, "activation_profit": 0.05}
        )

        # Verify factors added to strategy
        assert mock_strategy.add_factor.call_count == 3

        # Verify momentum added with no dependencies
        mock_strategy.add_factor.assert_any_call(mock_momentum, depends_on=[])

        # Verify breakout added with no dependencies
        mock_strategy.add_factor.assert_any_call(mock_breakout, depends_on=[])

        # Verify trailing stop added with dependencies on momentum and breakout
        mock_strategy.add_factor.assert_any_call(
            mock_trailing_stop,
            depends_on=["momentum_factor_id", "breakout_factor_id"]
        )

    @patch('src.learning.iteration_executor.FactorRegistry')
    @patch('src.learning.iteration_executor.Strategy')
    def test_create_template_strategy_returns_strategy(self, mock_strategy_class, mock_registry_class, executor):
        """Test that template creation returns Strategy object."""
        mock_strategy = MagicMock()
        mock_strategy_class.return_value = mock_strategy

        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        mock_registry.create_factor.return_value = MagicMock(id="test_factor")

        result = executor._create_template_strategy(iteration_num=10)

        assert result == mock_strategy


class TestGenerateWithFactorGraphNoChampion:
    """Test Change #2: _generate_with_factor_graph() without champion."""

    @patch('src.learning.iteration_executor.FactorRegistry')
    @patch('src.learning.iteration_executor.Strategy')
    def test_generate_without_champion_creates_template(self, mock_strategy_class, mock_registry_class, executor):
        """Test that template is created when no champion exists."""
        # No champion
        executor.champion_tracker.get_champion.return_value = None

        # Mock template creation
        mock_strategy = MagicMock()
        mock_strategy.id = "template_0"
        mock_strategy.generation = 0
        mock_strategy_class.return_value = mock_strategy

        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        mock_registry.create_factor.return_value = MagicMock(id="test_factor")

        # Execute
        code, strategy_id, strategy_generation = executor._generate_with_factor_graph(iteration_num=0)

        # Verify template created
        mock_strategy_class.assert_called_once_with(id="template_0", generation=0)

        # Verify return values
        assert code is None
        assert strategy_id == "template_0"
        assert strategy_generation == 0

        # Verify strategy registered
        assert "template_0" in executor._strategy_registry
        assert executor._strategy_registry["template_0"] == mock_strategy

    @patch('src.learning.iteration_executor.FactorRegistry')
    @patch('src.learning.iteration_executor.Strategy')
    def test_generate_with_llm_champion_creates_template(self, mock_strategy_class, mock_registry_class, executor):
        """Test that template is created when only LLM champion exists."""
        # LLM champion (not Factor Graph)
        llm_champion = ChampionStrategy(
            iteration_num=5,
            generation_method="llm",
            code="# LLM code",
            metrics={"sharpe_ratio": 1.5},
            timestamp="2025-11-08T10:00:00"
        )
        executor.champion_tracker.get_champion.return_value = llm_champion

        # Mock template creation
        mock_strategy = MagicMock()
        mock_strategy.id = "template_10"
        mock_strategy.generation = 0
        mock_strategy_class.return_value = mock_strategy

        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        mock_registry.create_factor.return_value = MagicMock(id="test_factor")

        # Execute
        code, strategy_id, strategy_generation = executor._generate_with_factor_graph(iteration_num=10)

        # Verify template created (not mutation)
        assert code is None
        assert strategy_id == "template_10"
        assert strategy_generation == 0


class TestGenerateWithFactorGraphWithChampion:
    """Test Change #2: _generate_with_factor_graph() with champion."""

    @patch('src.learning.iteration_executor.FactorRegistry')
    @patch('src.learning.iteration_executor.Strategy')
    @patch('src.learning.iteration_executor.add_factor')
    def test_generate_with_champion_mutates(self, mock_add_factor, mock_strategy_class, mock_registry_class, executor):
        """Test that champion is mutated when Factor Graph champion exists."""
        # Factor Graph champion
        fg_champion = ChampionStrategy(
            iteration_num=10,
            generation_method="factor_graph",
            strategy_id="fg_10_1",
            strategy_generation=1,
            metrics={"sharpe_ratio": 2.0},
            timestamp="2025-11-08T11:00:00"
        )
        executor.champion_tracker.get_champion.return_value = fg_champion

        # Champion in registry
        mock_parent_strategy = MagicMock()
        executor._strategy_registry["fg_10_1"] = mock_parent_strategy

        # Mock mutation
        mock_mutated_strategy = MagicMock()
        mock_add_factor.return_value = mock_mutated_strategy

        # Mock registry
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        mock_registry.list_by_category.return_value = ["momentum_factor", "ma_filter_factor"]
        mock_registry.get_metadata.return_value = {"parameters": {"period": 20}}

        # Execute
        with patch('src.learning.iteration_executor.random.choice', side_effect=lambda x: x[0]):
            code, strategy_id, strategy_generation = executor._generate_with_factor_graph(iteration_num=15)

        # Verify mutation was attempted
        mock_add_factor.assert_called_once()
        call_args = mock_add_factor.call_args
        assert call_args.kwargs['strategy'] == mock_parent_strategy
        assert call_args.kwargs['insert_point'] == "smart"

        # Verify return values
        assert code is None
        assert strategy_id == "fg_15_2"
        assert strategy_generation == 2

        # Verify strategy registered
        assert "fg_15_2" in executor._strategy_registry

    @patch('src.learning.iteration_executor.FactorRegistry')
    @patch('src.learning.iteration_executor.Strategy')
    def test_generate_with_champion_not_in_registry_creates_template(
        self, mock_strategy_class, mock_registry_class, executor
    ):
        """Test fallback to template when champion not in registry."""
        # Factor Graph champion
        fg_champion = ChampionStrategy(
            iteration_num=5,
            generation_method="factor_graph",
            strategy_id="fg_5_1",
            strategy_generation=1,
            metrics={"sharpe_ratio": 2.0},
            timestamp="2025-11-08T11:00:00"
        )
        executor.champion_tracker.get_champion.return_value = fg_champion

        # Champion NOT in registry (empty registry)
        assert "fg_5_1" not in executor._strategy_registry

        # Mock template creation
        mock_template = MagicMock()
        mock_template.id = "template_20"
        mock_template.generation = 0
        mock_strategy_class.return_value = mock_template

        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        mock_registry.create_factor.return_value = MagicMock(id="test_factor")

        # Execute (will warn and create template)
        code, strategy_id, strategy_generation = executor._generate_with_factor_graph(iteration_num=20)

        # Should create template (fallback)
        assert strategy_id == "template_20"
        assert strategy_generation == 0


class TestGenerateWithFactorGraphMutationFailure:
    """Test Change #2: _generate_with_factor_graph() mutation failure fallback."""

    @patch('src.learning.iteration_executor.FactorRegistry')
    @patch('src.learning.iteration_executor.Strategy')
    @patch('src.learning.iteration_executor.add_factor')
    def test_mutation_failure_falls_back_to_template(
        self, mock_add_factor, mock_strategy_class, mock_registry_class, executor
    ):
        """Test that mutation failure falls back to template creation."""
        # Factor Graph champion
        fg_champion = ChampionStrategy(
            iteration_num=10,
            generation_method="factor_graph",
            strategy_id="fg_10_1",
            strategy_generation=1,
            metrics={"sharpe_ratio": 2.0},
            timestamp="2025-11-08T11:00:00"
        )
        executor.champion_tracker.get_champion.return_value = fg_champion

        # Champion in registry
        executor._strategy_registry["fg_10_1"] = MagicMock()

        # Mock mutation to raise exception
        mock_add_factor.side_effect = ValueError("Factor incompatible")

        # Mock template creation
        mock_template = MagicMock()
        mock_template.id = "template_15"
        mock_template.generation = 0
        mock_strategy_class.return_value = mock_template

        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        mock_registry.list_by_category.return_value = ["momentum_factor"]
        mock_registry.get_metadata.return_value = {"parameters": {}}
        mock_registry.create_factor.return_value = MagicMock(id="test_factor")

        # Execute
        code, strategy_id, strategy_generation = executor._generate_with_factor_graph(iteration_num=15)

        # Verify fell back to template
        assert code is None
        assert strategy_id == "template_15"
        assert strategy_generation == 0

        # Verify template in registry
        assert "template_15" in executor._strategy_registry


class TestExecuteStrategyFactorGraph:
    """Test Change #4: Factor Graph execution path."""

    def test_execute_factor_graph_success(self, executor):
        """Test successful Factor Graph strategy execution."""
        # Create mock strategy
        mock_strategy = MagicMock()
        executor._strategy_registry["fg_10_1"] = mock_strategy

        # Mock successful execution
        mock_result = ExecutionResult(
            success=True,
            sharpe_ratio=2.5,
            total_return=0.45,
            max_drawdown=-0.12,
            execution_time=5.2,
            report=MagicMock()
        )
        executor.backtest_executor.execute_strategy.return_value = mock_result

        # Mock finlab initialization
        executor.data = MagicMock()
        executor.sim = MagicMock()

        # Execute
        result = executor._execute_strategy(
            strategy_code=None,
            strategy_id="fg_10_1",
            strategy_generation=1,
            generation_method="factor_graph"
        )

        # Verify BacktestExecutor.execute_strategy called
        executor.backtest_executor.execute_strategy.assert_called_once_with(
            strategy=mock_strategy,
            data=executor.data,
            sim=executor.sim,
            timeout=420,
            start_date='2018-01-01',
            end_date='2024-12-31',
            fee_ratio=0.001425,
            tax_ratio=0.003,
            resample='M'
        )

        # Verify result
        assert result.success is True
        assert result.sharpe_ratio == 2.5

    def test_execute_factor_graph_strategy_not_found(self, executor):
        """Test error handling when strategy not in registry."""
        # Strategy NOT in registry
        assert "missing_strategy" not in executor._strategy_registry

        # Mock finlab
        executor.data = MagicMock()
        executor.sim = MagicMock()

        # Execute
        result = executor._execute_strategy(
            strategy_code=None,
            strategy_id="missing_strategy",
            strategy_generation=1,
            generation_method="factor_graph"
        )

        # Verify error result
        assert result.success is False
        assert result.error_type == "ValueError"
        assert "not found in internal registry" in result.error_message


class TestUpdateChampionFactorGraph:
    """Test Change #5: Champion update with Factor Graph parameters (CRITICAL)."""

    def test_update_champion_passes_all_factor_graph_parameters(self, executor):
        """CRITICAL: Verify all Factor Graph parameters passed to update_champion()."""
        # Mock successful strategy
        metrics = {"sharpe_ratio": 2.5, "total_return": 0.45, "max_drawdown": -0.12}

        # Mock champion update
        executor.champion_tracker.update_champion.return_value = True

        # Execute
        updated = executor._update_champion_if_better(
            iteration_num=15,
            generation_method="factor_graph",
            strategy_code=None,
            strategy_id="fg_15_2",
            strategy_generation=2,
            metrics=metrics,
            classification_level="LEVEL_3"
        )

        # CRITICAL VERIFICATION: All parameters must be passed
        executor.champion_tracker.update_champion.assert_called_once_with(
            iteration_num=15,
            metrics=metrics,
            generation_method="factor_graph",  # CRITICAL
            code=None,
            strategy_id="fg_15_2",              # CRITICAL
            strategy_generation=2                # CRITICAL
        )

        # Verify update successful
        assert updated is True

    def test_update_champion_llm_parameters(self, executor):
        """Verify LLM parameters also work correctly."""
        # Mock LLM strategy
        metrics = {"sharpe_ratio": 1.8, "total_return": 0.35, "max_drawdown": -0.15}

        executor.champion_tracker.update_champion.return_value = True

        # Execute
        updated = executor._update_champion_if_better(
            iteration_num=20,
            generation_method="llm",
            strategy_code="# LLM code",
            strategy_id=None,
            strategy_generation=None,
            metrics=metrics,
            classification_level="LEVEL_3"
        )

        # Verify LLM parameters
        executor.champion_tracker.update_champion.assert_called_once_with(
            iteration_num=20,
            metrics=metrics,
            generation_method="llm",
            code="# LLM code",
            strategy_id=None,
            strategy_generation=None
        )


class TestCleanupOldStrategies:
    """Test Change #6: Registry cleanup."""

    def test_cleanup_when_registry_small(self, executor):
        """Test no cleanup when registry size < threshold."""
        # Add 50 strategies (below threshold of 100)
        for i in range(50):
            executor._strategy_registry[f"fg_{i}_0"] = MagicMock()

        # Execute cleanup
        executor._cleanup_old_strategies(keep_last_n=100)

        # Verify no cleanup (all 50 still present)
        assert len(executor._strategy_registry) == 50

    def test_cleanup_removes_old_strategies(self, executor):
        """Test cleanup removes old strategies but keeps recent."""
        # Add 150 strategies
        for i in range(150):
            executor._strategy_registry[f"fg_{i}_0"] = MagicMock()

        # No champion
        executor.champion_tracker.get_champion.return_value = None

        # Execute cleanup (keep last 100)
        executor._cleanup_old_strategies(keep_last_n=100)

        # Verify only 100 strategies remain
        assert len(executor._strategy_registry) == 100

        # Verify newest strategies kept (fg_50_0 through fg_149_0)
        for i in range(50, 150):
            assert f"fg_{i}_0" in executor._strategy_registry

        # Verify oldest strategies removed (fg_0_0 through fg_49_0)
        for i in range(50):
            assert f"fg_{i}_0" not in executor._strategy_registry

    def test_cleanup_preserves_champion(self, executor):
        """Test cleanup always preserves champion even if old."""
        # Add 150 strategies
        for i in range(150):
            executor._strategy_registry[f"fg_{i}_0"] = MagicMock()

        # Set champion to an old strategy (fg_10_0)
        fg_champion = ChampionStrategy(
            iteration_num=10,
            generation_method="factor_graph",
            strategy_id="fg_10_0",
            strategy_generation=0,
            metrics={"sharpe_ratio": 3.0},
            timestamp="2025-11-08T10:00:00"
        )
        executor.champion_tracker.get_champion.return_value = fg_champion

        # Execute cleanup (keep last 100)
        executor._cleanup_old_strategies(keep_last_n=100)

        # Verify champion preserved even though it's old
        assert "fg_10_0" in executor._strategy_registry

        # Verify total count is 101 (100 recent + 1 champion)
        assert len(executor._strategy_registry) == 101

    def test_cleanup_handles_template_format(self, executor):
        """Test cleanup works with template_N format."""
        # Add mix of fg_ and template_ strategies
        for i in range(150):
            if i % 2 == 0:
                executor._strategy_registry[f"template_{i}"] = MagicMock()
            else:
                executor._strategy_registry[f"fg_{i}_0"] = MagicMock()

        # No champion
        executor.champion_tracker.get_champion.return_value = None

        # Execute cleanup
        executor._cleanup_old_strategies(keep_last_n=100)

        # Verify cleanup worked (should keep last 100)
        assert len(executor._strategy_registry) == 100


class TestFactorGraphEndToEnd:
    """Integration-style test for complete Factor Graph flow."""

    @patch('src.learning.iteration_executor.FactorRegistry')
    @patch('src.learning.iteration_executor.Strategy')
    def test_complete_factor_graph_flow(self, mock_strategy_class, mock_registry_class, executor):
        """Test complete flow: generate template → execute → update champion."""
        # Setup: No champion
        executor.champion_tracker.get_champion.return_value = None
        executor.champion_tracker.update_champion.return_value = True

        # Mock template creation
        mock_strategy = MagicMock()
        mock_strategy.id = "template_0"
        mock_strategy.generation = 0
        mock_strategy_class.return_value = mock_strategy

        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        mock_registry.create_factor.return_value = MagicMock(id="test_factor")

        # Mock finlab
        executor.data = MagicMock()
        executor.sim = MagicMock()
        executor._finlab_initialized = True

        # Mock successful execution
        mock_exec_result = ExecutionResult(
            success=True,
            sharpe_ratio=2.5,
            total_return=0.45,
            max_drawdown=-0.12,
            execution_time=5.2,
            report=MagicMock()
        )
        executor.backtest_executor.execute_strategy.return_value = mock_exec_result

        # Mock metrics extraction
        executor.metrics_extractor.extract.return_value = {
            "sharpe_ratio": 2.5,
            "total_return": 0.45,
            "max_drawdown": -0.12
        }

        # Mock classification
        executor.success_classifier.classify_single.return_value = MagicMock(level=3)

        # Mock history
        executor.history.get_all.return_value = []
        executor.feedback_generator.generate_feedback.return_value = "Test feedback"

        # Execute complete iteration (innovation_rate=0 forces Factor Graph)
        with patch('src.learning.iteration_executor.random.random', return_value=1.0):
            record = executor.execute_iteration(iteration_num=0)

        # Verify flow
        assert record.generation_method == "factor_graph"
        assert record.strategy_id == "template_0"
        assert record.strategy_generation == 0
        assert record.classification_level == "LEVEL_3"
        assert record.champion_updated is True

        # Verify strategy in registry
        assert "template_0" in executor._strategy_registry


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
