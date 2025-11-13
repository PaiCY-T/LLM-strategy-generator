"""Performance benchmarks for runtime Protocol validation.

Validates that validate_protocol_compliance() adds minimal overhead (<5ms target).
"""

import time
import pytest
from src.learning.validation import validate_protocol_compliance
from src.learning.interfaces import IChampionTracker, IIterationHistory
from src.learning.champion_tracker import ChampionTracker
from src.learning.iteration_history import IterationHistory
from src.repository.hall_of_fame import HallOfFameRepository
from src.config.anti_churn_manager import AntiChurnManager


def measure_execution_time(func, iterations=100):
    """Measure average execution time over multiple iterations."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to milliseconds

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    return {
        'avg_ms': avg_time,
        'min_ms': min_time,
        'max_ms': max_time,
        'total_ms': sum(times)
    }


class TestRuntimeValidationPerformance:
    """Performance benchmarks for Protocol validation."""

    def test_validate_protocol_compliance_overhead(self, tmp_path):
        """Measure overhead of validate_protocol_compliance() call."""
        # Setup
        history_file = tmp_path / "test.jsonl"
        history = IterationHistory(filepath=str(history_file))

        # Measure validation time
        def validate():
            validate_protocol_compliance(
                history,
                IIterationHistory,
                "performance_test"
            )

        results = measure_execution_time(validate, iterations=1000)

        # Assert: Average time should be <1ms (strict), <5ms (acceptable)
        assert results['avg_ms'] < 5.0, f"Validation too slow: {results['avg_ms']:.3f}ms"

        print(f"\n✓ validate_protocol_compliance() performance:")
        print(f"  Average: {results['avg_ms']:.3f}ms")
        print(f"  Min: {results['min_ms']:.3f}ms")
        print(f"  Max: {results['max_ms']:.3f}ms")

        # Ideal target
        if results['avg_ms'] < 1.0:
            print(f"  ✓ Excellent performance (<1ms)")
        elif results['avg_ms'] < 5.0:
            print(f"  ✓ Acceptable performance (<5ms)")

    def test_champion_tracker_validation_overhead(self, tmp_path):
        """Measure ChampionTracker validation overhead."""
        # Setup
        hall_of_fame = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)
        history = IterationHistory(filepath=str(tmp_path / "history.jsonl"))
        anti_churn = AntiChurnManager(config_path="config/learning_system.yaml")

        # Measure validation time
        def validate():
            tracker = ChampionTracker(
                hall_of_fame=hall_of_fame,
                history=history,
                anti_churn=anti_churn,
                champion_file=str(tmp_path / "champion.json")
            )
            validate_protocol_compliance(
                tracker,
                IChampionTracker,
                "performance_test"
            )

        results = measure_execution_time(validate, iterations=100)

        assert results['avg_ms'] < 10.0, f"ChampionTracker validation too slow: {results['avg_ms']:.3f}ms"

        print(f"\n✓ ChampionTracker validation performance:")
        print(f"  Average: {results['avg_ms']:.3f}ms")
        print(f"  Min: {results['min_ms']:.3f}ms")
        print(f"  Max: {results['max_ms']:.3f}ms")

    def test_learning_loop_initialization_overhead(self, tmp_path):
        """Measure total LearningLoop initialization time with validation."""
        # Import only what we need and handle the import error gracefully
        try:
            from src.learning.learning_config import LearningConfig
            from src.learning.learning_loop import LearningLoop
        except (ImportError, NameError) as e:
            pytest.skip(f"Cannot import LearningConfig/LearningLoop: {e}")

        # Create test config
        config = LearningConfig(
            max_iterations=10,
            history_file=str(tmp_path / "history.jsonl"),
            champion_file=str(tmp_path / "champion.json"),
            config_file="config/learning_system.yaml",
            log_to_console=False,
            log_to_file=False
        )

        # Measure initialization time
        def init_loop():
            loop = LearningLoop(config)
            return loop

        results = measure_execution_time(init_loop, iterations=10)

        # LearningLoop initialization includes many components, so allow more time
        assert results['avg_ms'] < 500.0, f"LearningLoop init too slow: {results['avg_ms']:.3f}ms"

        print(f"\n✓ LearningLoop initialization performance:")
        print(f"  Average: {results['avg_ms']:.3f}ms")
        print(f"  Min: {results['min_ms']:.3f}ms")
        print(f"  Max: {results['max_ms']:.3f}ms")

        # Validation overhead should be minimal (<5% of total)
        validation_overhead = 2 * 5.0  # 2 validations * 5ms target
        overhead_percentage = (validation_overhead / results['avg_ms']) * 100

        print(f"  Estimated validation overhead: ~{overhead_percentage:.1f}%")
