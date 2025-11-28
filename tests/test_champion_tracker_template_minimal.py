"""Minimal test for ChampionTracker 'template' generation_method support.

Phase 3 Bug Fix: Verify that ChampionTracker.update_champion() accepts 'template'
as a valid generation_method without raising ValueError.
"""

import pytest
from src.learning.champion_tracker import ChampionTracker
from src.repository.hall_of_fame import HallOfFameRepository
from src.learning.iteration_history import IterationHistory
from src.config.anti_churn_manager import AntiChurnManager


@pytest.fixture
def champion_tracker(tmp_path):
    """Create a ChampionTracker with minimal dependencies."""
    hall_of_fame = HallOfFameRepository(str(tmp_path / "hof"), test_mode=True)
    history = IterationHistory(str(tmp_path / "history.jsonl"))
    anti_churn = AntiChurnManager()

    return ChampionTracker(
        hall_of_fame=hall_of_fame,
        history=history,
        anti_churn=anti_churn,
        champion_file=str(tmp_path / "champion.json")
    )


def test_update_champion_accepts_template(champion_tracker):
    """Core test: update_champion() must accept generation_method='template'."""
    # This should NOT raise ValueError
    champion_tracker.update_champion(
        iteration_num=1,
        generation_method="template",
        code="def strategy(): pass",
        metrics={
            "sharpe_ratio": 3.0,
            "calmar_ratio": 2.5,
            "max_drawdown": -0.15,
            "total_return": 0.5
        },
        backtest_result={"returns": [0.1, 0.2, 0.3]}
    )

    # Verify champion was updated
    assert champion_tracker.champion is not None
    assert champion_tracker.champion.generation_method == "template"
    assert champion_tracker.champion.metrics.sharpe_ratio == 3.0


def test_validation_error_message_includes_template():
    """Verify error message lists 'template' as valid option."""
    # Create minimal tracker
    from pathlib import Path
    tmp = Path("temp_test_dir")
    tmp.mkdir(exist_ok=True)

    try:
        hall_of_fame = HallOfFameRepository(str(tmp / "hof"), test_mode=True)
        history = IterationHistory(str(tmp / "history.jsonl"))
        anti_churn = AntiChurnManager()
        tracker = ChampionTracker(
            hall_of_fame=hall_of_fame,
            history=history,
            anti_churn=anti_churn,
            champion_file=str(tmp / "champion.json")
        )

        # Try invalid generation_method
        with pytest.raises(ValueError) as exc_info:
            tracker.update_champion(
                iteration_num=1,
                generation_method="invalid_method",
                code="def strategy(): pass",
                metrics={"sharpe_ratio": 3.0, "calmar_ratio": 2.5, "max_drawdown": -0.15},
                backtest_result={}
            )

        # Error message should mention 'template' as a valid option
        error_msg = str(exc_info.value)
        assert "'template'" in error_msg or '"template"' in error_msg
    finally:
        # Cleanup
        import shutil
        if tmp.exists():
            shutil.rmtree(tmp)
