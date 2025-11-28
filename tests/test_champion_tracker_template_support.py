"""Test ChampionTracker support for 'template' generation_method.

Phase 3 Bug Fix: ChampionTracker.update_champion() and _to_hall_of_fame()
only accept 'llm' or 'factor_graph', but should also accept 'template' since
template mode uses JSON-based LLM generation.
"""

import pytest
from src.learning.champion_tracker import ChampionTracker
from src.repository.hall_of_fame import HallOfFameRepository
from src.learning.iteration_history import IterationHistory
from src.config.anti_churn_manager import AntiChurnManager


@pytest.fixture
def setup_dependencies(tmp_path):
    """Create all required dependencies for ChampionTracker."""
    # Create temporary files
    hall_of_fame_file = tmp_path / "hall_of_fame.json"
    history_file = tmp_path / "history.jsonl"
    champion_file = tmp_path / "champion.json"

    # Initialize dependencies with test_mode=True to skip path validation
    hall_of_fame = HallOfFameRepository(str(hall_of_fame_file), test_mode=True)
    history = IterationHistory(str(history_file))
    anti_churn = AntiChurnManager()

    return {
        "hall_of_fame": hall_of_fame,
        "history": history,
        "anti_churn": anti_churn,
        "champion_file": str(champion_file)
    }


class TestChampionTrackerTemplateSupport:
    """Test that ChampionTracker accepts 'template' generation_method."""

    def test_update_champion_accepts_template_method(self, setup_dependencies):
        """update_champion() should accept generation_method='template'."""
        deps = setup_dependencies
        tracker = ChampionTracker(
            hall_of_fame=deps["hall_of_fame"],
            history=deps["history"],
            anti_churn=deps["anti_churn"],
            champion_file=deps["champion_file"]
        )

        # Should NOT raise ValueError
        tracker.update_champion(
            iteration_num=1,
            generation_method="template",
            code="def strategy(): pass",
            metrics={
                "sharpe_ratio": 1.5,
                "calmar_ratio": 2.0,
                "max_drawdown": -0.2,
                "total_return": 0.3
            },
            backtest_result={"returns": [0.1, 0.2]}
        )

        assert tracker.champion is not None
        assert tracker.champion.generation_method == "template"
        assert tracker.champion.metrics.sharpe_ratio == 1.5

    def test_to_hall_of_fame_accepts_template_method(self, setup_dependencies):
        """_to_hall_of_fame() should accept generation_method='template'."""
        deps = setup_dependencies
        tracker = ChampionTracker(
            hall_of_fame=deps["hall_of_fame"],
            history=deps["history"],
            anti_churn=deps["anti_churn"],
            champion_file=deps["champion_file"]
        )

        # Create a champion with template method
        tracker.update_champion(
            iteration_num=1,
            generation_method="template",
            code="def strategy(): pass",
            metrics={"sharpe_ratio": 1.5},
            backtest_result={"returns": [0.1, 0.2]}
        )

        # Should be able to convert to hall of fame format
        hof_data = tracker._to_hall_of_fame(
            iteration_num=1,
            generation_method="template",
            code="def strategy(): pass",
            metrics={"sharpe_ratio": 1.5},
            backtest_result={"returns": [0.1, 0.2]}
        )

        assert hof_data is not None
        assert hof_data["generation_method"] == "template"

    def test_template_champion_persists_across_sessions(self, setup_dependencies):
        """Template champion should persist correctly across sessions."""
        deps = setup_dependencies

        # Session 1: Create template champion
        tracker1 = ChampionTracker(
            hall_of_fame=deps["hall_of_fame"],
            history=deps["history"],
            anti_churn=deps["anti_churn"],
            champion_file=deps["champion_file"]
        )
        tracker1.update_champion(
            iteration_num=1,
            generation_method="template",
            code="def strategy(): pass",
            metrics={"sharpe_ratio": 2.0},
            backtest_result={"returns": [0.1, 0.2]}
        )

        # Session 2: Load and verify (reuse same dependencies)
        tracker2 = ChampionTracker(
            hall_of_fame=deps["hall_of_fame"],
            history=deps["history"],
            anti_churn=deps["anti_churn"],
            champion_file=deps["champion_file"]
        )
        assert tracker2.champion is not None
        assert tracker2.champion.generation_method == "template"
        assert tracker2.champion.metrics["sharpe_ratio"] == 2.0

    def test_template_champion_can_be_replaced(self, setup_dependencies):
        """Template champion can be replaced by better template/llm/factor_graph."""
        deps = setup_dependencies
        tracker = ChampionTracker(
            hall_of_fame=deps["hall_of_fame"],
            history=deps["history"],
            anti_churn=deps["anti_churn"],
            champion_file=deps["champion_file"]
        )

        # Initial template champion
        tracker.update_champion(
            iteration_num=1,
            generation_method="template",
            code="def strategy(): pass",
            metrics={"sharpe_ratio": 1.5},
            backtest_result={"returns": [0.1]}
        )

        # Better template champion
        tracker.update_champion(
            iteration_num=2,
            generation_method="template",
            code="def better_strategy(): pass",
            metrics={"sharpe_ratio": 2.0},
            backtest_result={"returns": [0.2]}
        )

        assert tracker.champion.iteration_num == 2
        assert tracker.champion.metrics["sharpe_ratio"] == 2.0

    def test_all_three_generation_methods_accepted(self, setup_dependencies):
        """ChampionTracker should accept llm, factor_graph, and template."""
        deps = setup_dependencies
        tracker = ChampionTracker(
            hall_of_fame=deps["hall_of_fame"],
            history=deps["history"],
            anti_churn=deps["anti_churn"],
            champion_file=deps["champion_file"]
        )

        methods = ["llm", "factor_graph", "template"]
        for i, method in enumerate(methods, 1):
            tracker.update_champion(
                iteration_num=i,
                generation_method=method,
                code="def strategy(): pass" if method != "factor_graph" else None,
                strategy_id=f"strat_{i}" if method == "factor_graph" else None,
                generation=i if method == "factor_graph" else None,
                metrics={"sharpe_ratio": float(i)},
                backtest_result={"returns": [0.1 * i]}
            )

            assert tracker.champion.generation_method == method
