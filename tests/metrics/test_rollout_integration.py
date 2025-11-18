"""
Integration test for Task 2.3: Verify rollout mechanism integrates with IterationExecutor.

This test ensures:
1. RolloutSampler is properly initialized in IterationExecutor
2. MetricsCollector is accessible for metrics tracking
3. Environment variable ROLLOUT_PERCENTAGE_LAYER1 is respected
"""

import os
import pytest
from unittest.mock import Mock, MagicMock

from src.learning.iteration_executor import IterationExecutor
from src.metrics.collector import RolloutSampler, MetricsCollector


class TestRolloutIntegration:
    """Integration tests for rollout mechanism in IterationExecutor."""

    def test_iteration_executor_has_rollout_components(self):
        """
        Verify IterationExecutor initializes rollout components.

        Given: A configured IterationExecutor
        When: Initialized with default settings
        Then: Should have rollout_sampler and metrics_collector attributes
        """
        # Create minimal mocks
        llm_client = Mock()
        llm_client.is_enabled.return_value = False

        feedback_generator = Mock()
        backtest_executor = Mock()
        champion_tracker = Mock()
        history = Mock()
        config = {
            "innovation_rate": 20,
            "history_window": 5
        }

        # Initialize IterationExecutor
        executor = IterationExecutor(
            llm_client=llm_client,
            feedback_generator=feedback_generator,
            backtest_executor=backtest_executor,
            champion_tracker=champion_tracker,
            history=history,
            config=config
        )

        # Verify rollout components exist
        assert hasattr(executor, 'rollout_sampler')
        assert hasattr(executor, 'metrics_collector')
        assert isinstance(executor.rollout_sampler, RolloutSampler)
        assert isinstance(executor.metrics_collector, MetricsCollector)

    def test_rollout_percentage_from_environment(self):
        """
        Verify rollout percentage is read from environment variable.

        Given: ROLLOUT_PERCENTAGE_LAYER1 environment variable set to 25
        When: IterationExecutor is initialized
        Then: RolloutSampler should use 25% rollout
        """
        # Set environment variable
        os.environ["ROLLOUT_PERCENTAGE_LAYER1"] = "25"

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

            # Verify rollout percentage is 25%
            assert executor.rollout_sampler.rollout_percentage == 25

        finally:
            # Clean up environment variable
            if "ROLLOUT_PERCENTAGE_LAYER1" in os.environ:
                del os.environ["ROLLOUT_PERCENTAGE_LAYER1"]

    def test_should_apply_layer1_validation_method_exists(self):
        """
        Verify _should_apply_layer1_validation method exists and works.

        Given: An IterationExecutor instance
        When: We call _should_apply_layer1_validation(iteration_num)
        Then: Should return boolean (True/False) based on rollout sampling
        """
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

        # Verify method exists
        assert hasattr(executor, '_should_apply_layer1_validation')

        # Verify method returns boolean
        result = executor._should_apply_layer1_validation(iteration_num=0)
        assert isinstance(result, bool)

        # Verify deterministic (same iteration returns same result)
        result1 = executor._should_apply_layer1_validation(iteration_num=5)
        result2 = executor._should_apply_layer1_validation(iteration_num=5)
        assert result1 == result2

    def test_record_validation_metrics_method_exists(self):
        """
        Verify _record_validation_metrics method exists and works.

        Given: An IterationExecutor instance
        When: We call _record_validation_metrics()
        Then: Should record event in metrics_collector
        """
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

        # Verify method exists
        assert hasattr(executor, '_record_validation_metrics')

        # Record a validation event
        executor._record_validation_metrics(
            iteration_num=0,
            validation_enabled=True,
            field_errors=0,
            llm_success=True,
            validation_latency_ms=0.5
        )

        # Verify metrics were recorded
        metrics = executor.metrics_collector.get_metrics()
        assert metrics["total_requests"] == 1
        assert metrics["validation_enabled_count"] == 1
