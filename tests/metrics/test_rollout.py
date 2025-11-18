"""
Test suite for Task 2.3: 10% rollout mechanism for Layer 1 validation.

This test suite follows strict TDD methodology (RED → GREEN → REFACTOR):
- RED Phase: Tests written first and expected to fail
- GREEN Phase: Minimal implementation to make tests pass
- REFACTOR Phase: Code improvement while keeping tests green

Requirements:
- AC1.5: 10% rollout deployed successfully with baseline metrics established
- NFR-O1: Real-time metrics for field_error_rate, llm_success_rate, validation_latency

Test Coverage:
1. test_rollout_percentage_respected() - Verify 10% traffic gets validation
2. test_deterministic_sampling() - Same strategy hash always gets same result
3. test_metrics_collection_enabled() - Verify metrics collected during rollout
"""

import pytest
from src.metrics.collector import RolloutSampler, MetricsCollector


class TestRolloutSampler:
    """Test suite for RolloutSampler class - deterministic 10% sampling."""

    def test_rollout_percentage_respected(self):
        """
        RED TEST: Verify 10% of strategies get Layer 1 validation.

        Given: A RolloutSampler with 10% rollout percentage
        When: We check 1000 different strategy hashes
        Then: Approximately 10% (90-110 out of 1000) should be enabled

        This test verifies that the sampling mechanism respects the configured
        rollout percentage with acceptable statistical variance.
        """
        sampler = RolloutSampler(rollout_percentage=10)

        # Test with 1000 unique strategy hashes
        enabled_count = 0
        for i in range(1000):
            strategy_hash = f"strategy_{i}"
            if sampler.is_enabled(strategy_hash):
                enabled_count += 1

        # Allow 10% variance: 90-110 out of 1000
        # (Using wider range to account for hash distribution variance)
        assert 80 <= enabled_count <= 120, (
            f"Expected 10% rollout (90-110 out of 1000), got {enabled_count}"
        )

    def test_deterministic_sampling(self):
        """
        RED TEST: Same strategy hash always returns same result.

        Given: A RolloutSampler instance
        When: We call is_enabled() multiple times with the same hash
        Then: Result should be identical every time (deterministic)

        This ensures consistency - a strategy is either always in the rollout
        group or always excluded, preventing flip-flopping behavior.
        """
        sampler = RolloutSampler(rollout_percentage=10)

        # Test 100 different strategies, each checked 10 times
        for i in range(100):
            strategy_hash = f"test_strategy_{i}"

            # First call establishes expected result
            first_result = sampler.is_enabled(strategy_hash)

            # All subsequent calls must match
            for _ in range(9):
                assert sampler.is_enabled(strategy_hash) == first_result, (
                    f"is_enabled() returned inconsistent results for {strategy_hash}"
                )

    def test_different_percentages(self):
        """
        RED TEST: Verify different rollout percentages work correctly.

        Given: RolloutSamplers with different percentages (0%, 50%, 100%)
        When: We check the same set of strategy hashes
        Then: Enabled counts should match expected percentages

        This validates that the rollout mechanism is configurable.
        """
        strategy_hashes = [f"strategy_{i}" for i in range(1000)]

        # Test 0% rollout
        sampler_0 = RolloutSampler(rollout_percentage=0)
        enabled_0 = sum(1 for h in strategy_hashes if sampler_0.is_enabled(h))
        assert enabled_0 == 0, "0% rollout should enable nothing"

        # Test 100% rollout
        sampler_100 = RolloutSampler(rollout_percentage=100)
        enabled_100 = sum(1 for h in strategy_hashes if sampler_100.is_enabled(h))
        assert enabled_100 == 1000, "100% rollout should enable everything"

        # Test 50% rollout (allow wider variance due to hash distribution)
        sampler_50 = RolloutSampler(rollout_percentage=50)
        enabled_50 = sum(1 for h in strategy_hashes if sampler_50.is_enabled(h))
        # Allow ±10% variance (400-600 out of 1000) due to hash distribution
        assert 400 <= enabled_50 <= 600, (
            f"50% rollout should enable ~500 strategies, got {enabled_50}"
        )


class TestMetricsCollector:
    """Test suite for MetricsCollector class - baseline metrics tracking."""

    def test_metrics_collection_enabled(self):
        """
        RED TEST: Verify metrics are collected during rollout.

        Given: A MetricsCollector instance
        When: We record validation events (enabled/disabled)
        Then: Collector should track field_error_rate, llm_success_rate

        This ensures we can measure baseline performance for comparison.
        """
        collector = MetricsCollector()

        # Record some validation events
        collector.record_validation_event(
            strategy_hash="strategy_1",
            validation_enabled=True,
            field_errors=0,
            llm_success=True,
            validation_latency_ms=0.5
        )

        collector.record_validation_event(
            strategy_hash="strategy_2",
            validation_enabled=True,
            field_errors=2,
            llm_success=False,
            validation_latency_ms=0.8
        )

        collector.record_validation_event(
            strategy_hash="strategy_3",
            validation_enabled=False,
            field_errors=5,
            llm_success=False,
            validation_latency_ms=0.0
        )

        # Get metrics
        metrics = collector.get_metrics()

        # Verify metrics structure
        assert "field_error_rate" in metrics
        assert "llm_success_rate" in metrics
        assert "validation_latency_avg_ms" in metrics
        assert "total_requests" in metrics
        assert "validation_enabled_count" in metrics

        # Verify metrics values
        assert metrics["total_requests"] == 3
        assert metrics["validation_enabled_count"] == 2

        # Field error rate: 1 strategy with errors out of 2 validated = 50%
        # (strategy_1: 0 errors, strategy_2: 2 errors, strategy_3 not counted)
        # Only strategy_2 has errors, so 1/2 = 50%
        assert metrics["field_error_rate"] == 0.5  # 1/2 = 50%

        # LLM success rate: 1 success out of 2 validated requests = 50%
        assert metrics["llm_success_rate"] == 0.5  # 1/2 = 50%

        # Avg validation latency: (0.5 + 0.8) / 2 = 0.65ms
        assert abs(metrics["validation_latency_avg_ms"] - 0.65) < 0.01

    def test_metrics_export_format(self):
        """
        RED TEST: Verify metrics can be exported for monitoring systems.

        Given: A MetricsCollector with recorded events
        When: We call export_metrics()
        Then: Should return dict suitable for Prometheus/CloudWatch

        This ensures metrics are properly formatted for external monitoring.
        """
        collector = MetricsCollector()

        # Record a few events
        for i in range(10):
            collector.record_validation_event(
                strategy_hash=f"strategy_{i}",
                validation_enabled=(i % 2 == 0),  # 50% enabled
                field_errors=(i % 3),  # Varies
                llm_success=(i % 2 == 0),
                validation_latency_ms=0.5
            )

        # Export metrics
        exported = collector.export_metrics()

        # Verify export format
        assert isinstance(exported, dict)
        assert "timestamp" in exported
        assert "metrics" in exported

        # Verify metrics are present
        assert "field_error_rate" in exported["metrics"]
        assert "llm_success_rate" in exported["metrics"]
        assert "validation_latency_avg_ms" in exported["metrics"]

    def test_no_division_by_zero(self):
        """
        RED TEST: Handle edge case when no validation events recorded.

        Given: A MetricsCollector with no events
        When: We call get_metrics()
        Then: Should return 0.0 for rates (not crash with division by zero)

        This ensures graceful handling of empty state.
        """
        collector = MetricsCollector()

        metrics = collector.get_metrics()

        # All rates should be 0.0 when no events
        assert metrics["field_error_rate"] == 0.0
        assert metrics["llm_success_rate"] == 0.0
        assert metrics["validation_latency_avg_ms"] == 0.0
        assert metrics["total_requests"] == 0
        assert metrics["validation_enabled_count"] == 0
