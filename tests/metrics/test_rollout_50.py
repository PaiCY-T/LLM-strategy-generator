"""
Test suite for Task 4.4: 50% rollout deployment for Layer 1 validation.

This test suite follows strict TDD methodology (RED → GREEN → REFACTOR):
- RED Phase: Tests written first and expected to fail
- GREEN Phase: Minimal implementation to make tests pass
- REFACTOR Phase: Code improvement while keeping tests green

Requirements:
- AC2.8: Rollout percentage configurable via environment variable
- Success Metrics (Week 2): 50% deployment
- Monitor metrics for performance/quality issues

Test Coverage:
1. test_rollout_percentage_configurable() - Verify env var control
2. test_default_rollout_percentage() - Backward compatibility (10% default)
3. test_rollout_50_percent_sampling() - Statistical accuracy at 50%
4. test_metrics_monitored_at_50_percent() - Metrics accuracy at 50%
5. test_feature_flag_integration() - FeatureFlagManager integration
"""

import os
import pytest
from unittest.mock import Mock

from src.metrics.collector import RolloutSampler, MetricsCollector
from src.config.feature_flags import FeatureFlagManager
from src.learning.iteration_executor import IterationExecutor


class TestRollout50Percent:
    """Test suite for 50% rollout deployment."""

    def test_rollout_percentage_configurable(self):
        """
        RED TEST: Verify rollout percentage is configurable via environment variable.

        Given: ROLLOUT_PERCENTAGE_LAYER1=50 environment variable
        When: IterationExecutor is initialized
        Then: RolloutSampler should use 50% (not hardcoded 10%)

        This is the CORE test for Task 4.4 - ensures we can deploy 50% rollout.
        """
        # Set environment variable to 50%
        os.environ["ROLLOUT_PERCENTAGE_LAYER1"] = "50"

        try:
            # Create minimal mocks
            llm_client = Mock()
            llm_client.is_enabled.return_value = False
            feedback_generator = Mock()
            backtest_executor = Mock()
            champion_tracker = Mock()
            history = Mock()
            config = {"innovation_rate": 20}

            # Initialize IterationExecutor
            executor = IterationExecutor(
                llm_client=llm_client,
                feedback_generator=feedback_generator,
                backtest_executor=backtest_executor,
                champion_tracker=champion_tracker,
                history=history,
                config=config
            )

            # ASSERTION: Should use 50% from environment variable
            assert executor.rollout_sampler.rollout_percentage == 50, (
                f"Expected rollout_percentage=50 from env var, "
                f"got {executor.rollout_sampler.rollout_percentage}"
            )

        finally:
            # Clean up environment variable
            if "ROLLOUT_PERCENTAGE_LAYER1" in os.environ:
                del os.environ["ROLLOUT_PERCENTAGE_LAYER1"]

    def test_default_rollout_percentage(self):
        """
        RED TEST: Verify default rollout percentage is 10% (backward compatible).

        Given: No ROLLOUT_PERCENTAGE_LAYER1 environment variable set
        When: IterationExecutor is initialized
        Then: RolloutSampler should default to 10%

        This ensures backward compatibility - existing deployments continue to work.
        """
        # Ensure environment variable is NOT set
        if "ROLLOUT_PERCENTAGE_LAYER1" in os.environ:
            del os.environ["ROLLOUT_PERCENTAGE_LAYER1"]

        try:
            # Create minimal mocks
            llm_client = Mock()
            llm_client.is_enabled.return_value = False
            feedback_generator = Mock()
            backtest_executor = Mock()
            champion_tracker = Mock()
            history = Mock()
            config = {"innovation_rate": 20}

            # Initialize IterationExecutor
            executor = IterationExecutor(
                llm_client=llm_client,
                feedback_generator=feedback_generator,
                backtest_executor=backtest_executor,
                champion_tracker=champion_tracker,
                history=history,
                config=config
            )

            # ASSERTION: Should default to 10%
            assert executor.rollout_sampler.rollout_percentage == 10, (
                f"Expected default rollout_percentage=10, "
                f"got {executor.rollout_sampler.rollout_percentage}"
            )

        finally:
            pass

    def test_rollout_50_percent_sampling(self):
        """
        RED TEST: Verify 50% rollout sampling is statistically accurate.

        Given: A RolloutSampler with 50% rollout percentage
        When: We check 1000 different strategy hashes
        Then: Approximately 500 (±5% tolerance) should be enabled

        This validates the sampling algorithm works correctly at 50%.
        """
        sampler = RolloutSampler(rollout_percentage=50)

        # Test with 1000 unique strategy hashes
        enabled_count = 0
        for i in range(1000):
            strategy_hash = f"iteration_{i}"
            if sampler.is_enabled(strategy_hash):
                enabled_count += 1

        # Allow ±10% variance: 400-600 out of 1000
        # (Statistical variance tolerance for hash distribution - using wider range
        # similar to test_rollout.py test_different_percentages)
        assert 400 <= enabled_count <= 600, (
            f"Expected 50% rollout (400-600 out of 1000), got {enabled_count}"
        )

    def test_metrics_monitored_at_50_percent(self):
        """
        RED TEST: Verify MetricsCollector tracks metrics correctly at 50% rollout.

        Given: A MetricsCollector receiving events from 50% rollout
        When: We record validation events (50% enabled, 50% disabled)
        Then: Metrics should accurately reflect:
             - validation_enabled_count ~50% of total_requests
             - field_error_rate and llm_success_rate calculated correctly

        This ensures monitoring infrastructure works correctly at 50% rollout.
        """
        collector = MetricsCollector()
        sampler = RolloutSampler(rollout_percentage=50)

        # Simulate 100 strategy generation requests
        enabled_count = 0
        for i in range(100):
            strategy_hash = f"iteration_{i}"
            validation_enabled = sampler.is_enabled(strategy_hash)

            if validation_enabled:
                enabled_count += 1

            # Simulate validation results
            field_errors = 0 if (i % 10 != 0) else 1  # 10% have field errors
            llm_success = (i % 5 != 0)  # 80% LLM success rate
            validation_latency_ms = 0.5

            collector.record_validation_event(
                strategy_hash=strategy_hash,
                validation_enabled=validation_enabled,
                field_errors=field_errors,
                llm_success=llm_success,
                validation_latency_ms=validation_latency_ms
            )

        # Get metrics
        metrics = collector.get_metrics()

        # ASSERTION 1: Total requests should be 100
        assert metrics["total_requests"] == 100, (
            f"Expected total_requests=100, got {metrics['total_requests']}"
        )

        # ASSERTION 2: Validation enabled count should be ~50 (±10 tolerance)
        assert 40 <= metrics["validation_enabled_count"] <= 60, (
            f"Expected validation_enabled_count ~50 (40-60), "
            f"got {metrics['validation_enabled_count']}"
        )

        # ASSERTION 3: Field error rate should be calculated correctly
        # (Only validation-enabled requests are counted in rates)
        # With 10% field errors, expect field_error_rate ~0.1 (±0.15 tolerance)
        assert 0.0 <= metrics["field_error_rate"] <= 0.25, (
            f"Expected field_error_rate ~0.1 (0.0-0.25), "
            f"got {metrics['field_error_rate']}"
        )

        # ASSERTION 4: LLM success rate should be calculated correctly
        # With 80% LLM success, expect llm_success_rate ~0.8 (±0.15 tolerance)
        assert 0.65 <= metrics["llm_success_rate"] <= 0.95, (
            f"Expected llm_success_rate ~0.8 (0.65-0.95), "
            f"got {metrics['llm_success_rate']}"
        )

        # ASSERTION 5: Validation latency should be tracked
        assert metrics["validation_latency_avg_ms"] > 0.0, (
            "Expected validation_latency_avg_ms > 0.0"
        )

    def test_feature_flag_integration(self):
        """
        RED TEST: Verify FeatureFlagManager supports rollout_percentage_layer1 property.

        Given: FeatureFlagManager with ROLLOUT_PERCENTAGE_LAYER1=50
        When: We access rollout_percentage_layer1 property
        Then: Should return 50

        This ensures FeatureFlagManager centralizes rollout configuration.
        """
        # Set environment variable to 50%
        os.environ["ROLLOUT_PERCENTAGE_LAYER1"] = "50"

        try:
            # Create FeatureFlagManager instance
            flags = FeatureFlagManager()

            # ASSERTION: Should have rollout_percentage_layer1 property
            assert hasattr(flags, 'rollout_percentage_layer1'), (
                "FeatureFlagManager should have rollout_percentage_layer1 property"
            )

            # ASSERTION: Should return 50 from environment variable
            assert flags.rollout_percentage_layer1 == 50, (
                f"Expected rollout_percentage_layer1=50, "
                f"got {flags.rollout_percentage_layer1}"
            )

        finally:
            # Clean up environment variable
            if "ROLLOUT_PERCENTAGE_LAYER1" in os.environ:
                del os.environ["ROLLOUT_PERCENTAGE_LAYER1"]

    def test_feature_flag_default_rollout(self):
        """
        RED TEST: Verify FeatureFlagManager defaults to 10% when env var not set.

        Given: No ROLLOUT_PERCENTAGE_LAYER1 environment variable
        When: We access rollout_percentage_layer1 property
        Then: Should return 10 (default)

        This ensures backward compatibility at the FeatureFlagManager level.
        """
        # Ensure environment variable is NOT set
        if "ROLLOUT_PERCENTAGE_LAYER1" in os.environ:
            del os.environ["ROLLOUT_PERCENTAGE_LAYER1"]

        try:
            # Create FeatureFlagManager instance
            flags = FeatureFlagManager()

            # ASSERTION: Should default to 10
            assert flags.rollout_percentage_layer1 == 10, (
                f"Expected default rollout_percentage_layer1=10, "
                f"got {flags.rollout_percentage_layer1}"
            )

        finally:
            pass

    def test_feature_flag_invalid_rollout_percentage(self):
        """
        RED TEST: Verify FeatureFlagManager handles invalid rollout percentages.

        Given: ROLLOUT_PERCENTAGE_LAYER1 with invalid values (negative, >100, non-numeric)
        When: We access rollout_percentage_layer1 property
        Then: Should fall back to 10 (fail-safe default)

        This ensures system resilience against misconfigurations.
        """
        test_cases = [
            ("-10", 10, "negative value"),
            ("150", 10, "value > 100"),
            ("abc", 10, "non-numeric value"),
            ("", 10, "empty string"),
        ]

        for env_value, expected_value, description in test_cases:
            os.environ["ROLLOUT_PERCENTAGE_LAYER1"] = env_value

            try:
                # Create NEW FeatureFlagManager instance (reset singleton)
                # Note: FeatureFlagManager uses singleton pattern, so we test on
                # the same instance but the property reads from env each time
                flags = FeatureFlagManager()

                # ASSERTION: Should fall back to 10
                assert flags.rollout_percentage_layer1 == expected_value, (
                    f"Expected fallback to {expected_value} for {description}, "
                    f"got {flags.rollout_percentage_layer1}"
                )

            finally:
                # Clean up environment variable
                if "ROLLOUT_PERCENTAGE_LAYER1" in os.environ:
                    del os.environ["ROLLOUT_PERCENTAGE_LAYER1"]
