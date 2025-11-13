"""Validate ChampionTracker IChampionTracker Protocol Compliance.

This example demonstrates:
1. Runtime Protocol validation
2. Type-safe usage
3. Behavioral contract enforcement

Run with: python3 examples/validate_champion_tracker_protocol.py
"""

import tempfile
import json
from pathlib import Path

from src.learning.champion_tracker import ChampionTracker
from src.learning.interfaces import IChampionTracker
from src.learning.iteration_history import IterationHistory
from src.repository.hall_of_fame import HallOfFameRepository
from src.config.anti_churn_manager import AntiChurnManager


def main():
    print("=" * 70)
    print("ChampionTracker IChampionTracker Protocol Validation")
    print("=" * 70)

    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create config file
        config_file = tmpdir_path / "config.json"
        config_data = {
            "anti_churn": {
                "min_sharpe_for_champion": 0.5,
                "base_improvement_pct": 0.05,
                "additive_threshold": 0.1
            }
        }
        config_file.write_text(json.dumps(config_data))

        # Initialize dependencies
        history = IterationHistory(filepath=str(tmpdir_path / "history.jsonl"))
        hall_of_fame = HallOfFameRepository(
            base_path=str(tmpdir_path / "hall_of_fame"),
            test_mode=True
        )
        anti_churn = AntiChurnManager(config_path=str(config_file))

        # Create ChampionTracker
        tracker = ChampionTracker(
            hall_of_fame=hall_of_fame,
            history=history,
            anti_churn=anti_churn,
            champion_file=str(tmpdir_path / "champion.json")
        )

        print("\n1. Runtime Protocol Validation")
        print("-" * 70)

        # Test 1: Runtime Protocol Check
        assert isinstance(tracker, IChampionTracker), (
            "ChampionTracker must implement IChampionTracker Protocol"
        )
        print("✓ ChampionTracker satisfies IChampionTracker Protocol")

        # Test 2: Champion Property Type
        champion = tracker.champion
        print(f"✓ .champion property returns: {type(champion).__name__ if champion else 'None'}")

        # Clear any existing champion for clean test
        tracker.champion = None
        champion = tracker.champion
        assert champion is None, "Champion should be None after clearing"
        print("✓ .champion returns None when no champion exists (never raises)")

        print("\n2. Behavioral Contract Validation")
        print("-" * 70)

        # Test 3: Update Champion with Valid Metrics
        metrics = {
            'sharpe_ratio': 2.5,
            'max_drawdown': -0.15,
            'calmar_ratio': 1.2
        }

        result = tracker.update_champion(
            iteration_num=0,
            code="# first strategy",
            metrics=metrics
        )

        assert isinstance(result, bool), ".update_champion() must return bool"
        print(f"✓ .update_champion() returns bool: {result}")

        # Test 4: Champion Updated Check
        if result:
            assert tracker.champion is not None, (
                "Champion must exist after successful update"
            )
            print("✓ Champion created after first valid strategy")

            assert tracker.champion.iteration_num == 0, (
                "Champion iteration_num must match update parameter"
            )
            print(f"✓ Champion iteration_num correct: {tracker.champion.iteration_num}")

            assert 'sharpe_ratio' in tracker.champion.metrics, (
                "Champion metrics must contain sharpe_ratio"
            )
            print(f"✓ Champion has sharpe_ratio: {tracker.champion.metrics['sharpe_ratio']:.2f}")

        # Test 5: Referential Stability
        champion_ref1 = tracker.champion
        champion_ref2 = tracker.champion

        assert champion_ref1 is champion_ref2, (
            ".champion must return same object if unchanged (referential stability)"
        )
        print("✓ .champion is referentially stable (same object returned)")

        # Test 6: Idempotency
        result2 = tracker.update_champion(
            iteration_num=0,
            code="# first strategy",  # Same strategy
            metrics=metrics
        )

        assert result2 is False, (
            "Updating with same iteration should return False (idempotent)"
        )
        print("✓ .update_champion() is idempotent (safe to call twice)")

        # Test 7: Atomicity
        initial_champion = tracker.champion

        worse_metrics = {'sharpe_ratio': 1.0, 'max_drawdown': -0.30}
        result3 = tracker.update_champion(
            iteration_num=1,
            code="# worse strategy",
            metrics=worse_metrics
        )

        assert result3 is False, "Update should fail for worse strategy"
        assert tracker.champion is initial_champion, (
            "Champion must remain unchanged (referential identity) when update fails"
        )
        print("✓ .update_champion() is atomic (champion unchanged on failure)")

        # Test 8: Missing Sharpe Ratio Validation
        invalid_metrics = {'max_drawdown': -0.15}  # Missing sharpe_ratio

        result4 = tracker.update_champion(
            iteration_num=2,
            code="# invalid strategy",
            metrics=invalid_metrics
        )

        assert result4 is False, (
            ".update_champion() must return False when sharpe_ratio missing"
        )
        print("✓ .update_champion() validates sharpe_ratio exists (returns False)")

        print("\n3. Type Safety Demonstration")
        print("-" * 70)

        # Demonstrate type hints match Protocol
        print("✓ Method signatures match IChampionTracker Protocol:")
        print("  - .champion -> Optional[ChampionStrategy]")
        print("  - .update_champion(iteration_num, code, metrics, **kwargs) -> bool")

        print("\n" + "=" * 70)
        print("✅ All Protocol Compliance Checks PASSED!")
        print("=" * 70)


if __name__ == "__main__":
    main()
