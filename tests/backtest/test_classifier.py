"""Tests for SuccessClassifier."""

import pytest

from src.backtest.classifier import ClassificationResult, SuccessClassifier
from src.backtest.metrics import StrategyMetrics


class TestClassificationResult:
    """Test ClassificationResult dataclass."""

    def test_dataclass_creation(self):
        """Test ClassificationResult creation with all fields."""
        result = ClassificationResult(
            level=2,
            reason="Valid metrics extracted",
            metrics_coverage=0.75,
            profitable_count=5,
            total_count=10
        )

        assert result.level == 2
        assert result.reason == "Valid metrics extracted"
        assert result.metrics_coverage == 0.75
        assert result.profitable_count == 5
        assert result.total_count == 10

    def test_dataclass_optional_fields(self):
        """Test ClassificationResult with optional fields as None."""
        result = ClassificationResult(
            level=0,
            reason="Execution failed",
            metrics_coverage=0.0,
            profitable_count=None,
            total_count=None
        )

        assert result.level == 0
        assert result.profitable_count is None
        assert result.total_count is None


class TestSuccessClassifierSingle:
    """Test SuccessClassifier.classify_single() method."""

    def setup_method(self):
        """Set up classifier for each test."""
        self.classifier = SuccessClassifier()

    def test_level_0_execution_failed(self):
        """Test Level 0: Execution failed."""
        metrics = StrategyMetrics(execution_success=False)

        result = self.classifier.classify_single(metrics)

        assert result.level == 0
        assert "Execution failed" in result.reason
        assert result.metrics_coverage == 0.0
        assert result.profitable_count is None

    def test_level_1_insufficient_metrics(self):
        """Test Level 1: Executed but insufficient metrics."""
        # Only sharpe_ratio extracted (1/3 = 0.33%)
        metrics = StrategyMetrics(
            sharpe_ratio=0.5,
            total_return=None,
            max_drawdown=None,
            execution_success=True
        )

        result = self.classifier.classify_single(metrics)

        assert result.level == 1
        assert "insufficient metrics" in result.reason
        assert result.metrics_coverage == pytest.approx(1.0 / 3.0)

    def test_level_2_valid_metrics_unprofitable(self):
        """Test Level 2: Valid metrics but not profitable."""
        # All metrics extracted but Sharpe <= 0
        metrics = StrategyMetrics(
            sharpe_ratio=-0.5,
            total_return=0.05,
            max_drawdown=-0.20,
            execution_success=True
        )

        result = self.classifier.classify_single(metrics)

        assert result.level == 2
        assert "Valid metrics" in result.reason
        assert "not profitable" in result.reason
        assert result.metrics_coverage == 1.0

    def test_level_2_valid_metrics_no_sharpe(self):
        """Test Level 2: Valid metrics but no Sharpe ratio."""
        # All metrics extracted but Sharpe is None
        metrics = StrategyMetrics(
            sharpe_ratio=None,
            total_return=0.25,
            max_drawdown=-0.15,
            execution_success=True
        )

        result = self.classifier.classify_single(metrics)

        assert result.level == 2
        assert "Valid metrics" in result.reason
        assert result.metrics_coverage == pytest.approx(2.0 / 3.0)

    def test_level_3_profitable(self):
        """Test Level 3: Valid metrics and profitable."""
        metrics = StrategyMetrics(
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=-0.15,
            execution_success=True
        )

        result = self.classifier.classify_single(metrics)

        assert result.level == 3
        assert "profitable" in result.reason.lower()
        assert result.metrics_coverage == 1.0

    def test_level_3_boundary_sharpe_zero(self):
        """Test that Sharpe=0 is not considered profitable."""
        metrics = StrategyMetrics(
            sharpe_ratio=0.0,
            total_return=0.10,
            max_drawdown=-0.20,
            execution_success=True
        )

        result = self.classifier.classify_single(metrics)

        assert result.level == 2  # Not profitable
        assert "not profitable" in result.reason

    def test_metrics_coverage_calculation(self):
        """Test metrics coverage is correctly calculated."""
        # 2/3 metrics (66.7% >= 60% threshold, and Sharpe > 0)
        metrics = StrategyMetrics(
            sharpe_ratio=1.0,
            total_return=0.20,
            max_drawdown=None,
            execution_success=True
        )

        result = self.classifier.classify_single(metrics)

        assert result.metrics_coverage == pytest.approx(2.0 / 3.0)
        assert result.level == 3  # Sufficient for Level 2+, and profitable for Level 3


class TestSuccessClassifierBatch:
    """Test SuccessClassifier.classify_batch() method."""

    def setup_method(self):
        """Set up classifier for each test."""
        self.classifier = SuccessClassifier()

    def test_empty_batch(self):
        """Test empty batch classification."""
        result = self.classifier.classify_batch([])

        assert result.level == 0
        assert "empty batch" in result.reason.lower()
        assert result.profitable_count == 0
        assert result.total_count == 0

    def test_all_failed(self):
        """Test batch where all strategies failed."""
        metrics_list = [
            StrategyMetrics(execution_success=False),
            StrategyMetrics(execution_success=False),
            StrategyMetrics(execution_success=False),
        ]

        result = self.classifier.classify_batch(metrics_list)

        assert result.level == 0
        assert "All strategies failed" in result.reason
        assert result.profitable_count == 0
        assert result.total_count == 3

    def test_level_1_insufficient_average_coverage(self):
        """Test Level 1: Average coverage below threshold."""
        metrics_list = [
            # First strategy: 1/3 coverage
            StrategyMetrics(
                sharpe_ratio=0.5,
                total_return=None,
                max_drawdown=None,
                execution_success=True
            ),
            # Second strategy: 2/3 coverage
            StrategyMetrics(
                sharpe_ratio=1.0,
                total_return=0.20,
                max_drawdown=None,
                execution_success=True
            ),
        ]
        # Average: (1/3 + 2/3) / 2 = 0.5 (50%) < 60%

        result = self.classifier.classify_batch(metrics_list)

        assert result.level == 1
        assert "insufficient metrics" in result.reason
        assert result.metrics_coverage == 0.5

    def test_level_2_valid_metrics_low_profitability(self):
        """Test Level 2: Valid metrics but < 40% profitable."""
        metrics_list = [
            # Profitable
            StrategyMetrics(
                sharpe_ratio=1.5,
                total_return=0.25,
                max_drawdown=-0.15,
                execution_success=True
            ),
            # Unprofitable
            StrategyMetrics(
                sharpe_ratio=-0.5,
                total_return=0.05,
                max_drawdown=-0.30,
                execution_success=True
            ),
            # Unprofitable
            StrategyMetrics(
                sharpe_ratio=-1.0,
                total_return=-0.10,
                max_drawdown=-0.40,
                execution_success=True
            ),
        ]
        # Profitability: 1/3 = 33.3% < 40%

        result = self.classifier.classify_batch(metrics_list)

        assert result.level == 2
        assert "limited profitability" in result.reason
        assert result.profitable_count == 1
        assert result.total_count == 3

    def test_level_3_profitable_batch(self):
        """Test Level 3: Valid metrics with >= 40% profitable."""
        metrics_list = [
            # Profitable
            StrategyMetrics(
                sharpe_ratio=1.5,
                total_return=0.25,
                max_drawdown=-0.15,
                execution_success=True
            ),
            # Profitable
            StrategyMetrics(
                sharpe_ratio=0.8,
                total_return=0.15,
                max_drawdown=-0.20,
                execution_success=True
            ),
            # Unprofitable
            StrategyMetrics(
                sharpe_ratio=-0.5,
                total_return=0.05,
                max_drawdown=-0.30,
                execution_success=True
            ),
        ]
        # Profitability: 2/3 = 66.7% >= 40%

        result = self.classifier.classify_batch(metrics_list)

        assert result.level == 3
        assert "strong profitability" in result.reason
        assert result.profitable_count == 2
        assert result.total_count == 3

    def test_mixed_executed_and_failed(self):
        """Test batch with mix of executed and failed strategies."""
        metrics_list = [
            StrategyMetrics(execution_success=False),  # Failed
            StrategyMetrics(
                sharpe_ratio=1.5,
                total_return=0.25,
                max_drawdown=-0.15,
                execution_success=True
            ),  # Executed, profitable
            StrategyMetrics(execution_success=False),  # Failed
        ]

        result = self.classifier.classify_batch(metrics_list)

        # Should classify based on executed strategies only (1 executed, 1 profitable)
        assert result.level == 3
        assert result.total_count == 1  # Only executed count

    def test_batch_boundary_40_percent_profitability(self):
        """Test batch at exactly 40% profitability threshold."""
        metrics_list = [
            # 2 profitable out of 5 = 40% exactly (should be >= 40%)
            StrategyMetrics(
                sharpe_ratio=1.5,
                total_return=0.25,
                max_drawdown=-0.15,
                execution_success=True
            ),
            StrategyMetrics(
                sharpe_ratio=0.8,
                total_return=0.15,
                max_drawdown=-0.20,
                execution_success=True
            ),
            StrategyMetrics(
                sharpe_ratio=-0.5,
                total_return=0.05,
                max_drawdown=-0.30,
                execution_success=True
            ),
            StrategyMetrics(
                sharpe_ratio=-1.0,
                total_return=-0.10,
                max_drawdown=-0.40,
                execution_success=True
            ),
            StrategyMetrics(
                sharpe_ratio=-0.3,
                total_return=0.01,
                max_drawdown=-0.25,
                execution_success=True
            ),
        ]
        # Profitability: 2/5 = 40% exactly >= 40%

        result = self.classifier.classify_batch(metrics_list)

        assert result.level == 3
        assert "strong profitability" in result.reason
        assert result.profitable_count == 2
        assert result.total_count == 5

    def test_batch_all_with_metrics_partial_coverage(self):
        """Test batch where all execute but only partial metrics coverage."""
        metrics_list = [
            # Strategy 1: 2/3 coverage
            StrategyMetrics(
                sharpe_ratio=0.8,
                total_return=0.15,
                max_drawdown=None,
                execution_success=True
            ),
            # Strategy 2: 1/3 coverage
            StrategyMetrics(
                sharpe_ratio=None,
                total_return=None,
                max_drawdown=-0.20,
                execution_success=True
            ),
            # Strategy 3: 3/3 coverage
            StrategyMetrics(
                sharpe_ratio=1.5,
                total_return=0.25,
                max_drawdown=-0.15,
                execution_success=True
            ),
        ]
        # Average coverage: (2/3 + 1/3 + 3/3) / 3 = 6/9 = 66.7% >= 60%
        # Profitability: 2/3 = 66.7% >= 40%

        result = self.classifier.classify_batch(metrics_list)

        assert result.level == 3
        assert result.metrics_coverage == pytest.approx(2.0 / 3.0)
        assert result.profitable_count == 2
        assert result.total_count == 3

    def test_batch_single_strategy(self):
        """Test batch with single strategy."""
        metrics_list = [
            StrategyMetrics(
                sharpe_ratio=1.5,
                total_return=0.25,
                max_drawdown=-0.15,
                execution_success=True
            ),
        ]

        result = self.classifier.classify_batch(metrics_list)

        assert result.level == 3
        assert result.profitable_count == 1
        assert result.total_count == 1

    def test_batch_level_1_single_failure_insufficient_metrics(self):
        """Test batch that is Level 1 due to insufficient metrics despite being executed."""
        metrics_list = [
            # All three fail to execute sufficiently
            StrategyMetrics(
                sharpe_ratio=None,
                total_return=None,
                max_drawdown=None,
                execution_success=True
            ),
            StrategyMetrics(
                sharpe_ratio=0.5,
                total_return=None,
                max_drawdown=None,
                execution_success=True
            ),
        ]
        # Average coverage: (0/3 + 1/3) / 2 = 1/6 = 16.7% < 60%

        result = self.classifier.classify_batch(metrics_list)

        assert result.level == 1
        assert "insufficient metrics" in result.reason
        assert result.metrics_coverage == pytest.approx(1.0 / 6.0)

    def test_batch_60_percent_threshold(self):
        """Test batch at exactly 60% metrics coverage threshold."""
        metrics_list = [
            # Each strategy has exactly 60% coverage (1.8/3 metrics)
            StrategyMetrics(
                sharpe_ratio=1.5,
                total_return=0.25,
                max_drawdown=None,  # 2/3 = 66.7%
                execution_success=True
            ),
            StrategyMetrics(
                sharpe_ratio=None,
                total_return=0.15,
                max_drawdown=-0.20,  # 2/3 = 66.7%
                execution_success=True
            ),
        ]
        # Average: (2/3 + 2/3) / 2 = 66.7% >= 60%
        # Profitability: 1/2 = 50% >= 40%

        result = self.classifier.classify_batch(metrics_list)

        assert result.level == 3
        assert result.metrics_coverage == pytest.approx(2.0 / 3.0)

    def test_batch_all_successful_none_profitable(self):
        """Test batch where all strategies executed with valid metrics but none are profitable."""
        metrics_list = [
            StrategyMetrics(
                sharpe_ratio=0.0,
                total_return=0.10,
                max_drawdown=-0.20,
                execution_success=True
            ),
            StrategyMetrics(
                sharpe_ratio=-0.5,
                total_return=0.05,
                max_drawdown=-0.30,
                execution_success=True
            ),
            StrategyMetrics(
                sharpe_ratio=-1.0,
                total_return=-0.10,
                max_drawdown=-0.40,
                execution_success=True
            ),
        ]
        # Profitability: 0/3 = 0% < 40%

        result = self.classifier.classify_batch(metrics_list)

        assert result.level == 2
        assert "limited profitability" in result.reason
        assert result.profitable_count == 0
        assert result.total_count == 3


class TestSuccessClassifierMetricsCoverage:
    """Test metrics coverage calculation in detail."""

    def setup_method(self):
        """Set up classifier for each test."""
        self.classifier = SuccessClassifier()

    def test_coverage_no_metrics(self):
        """Test coverage calculation with no metrics extracted."""
        metrics = StrategyMetrics(
            sharpe_ratio=None,
            total_return=None,
            max_drawdown=None,
            execution_success=True
        )

        coverage = self.classifier._calculate_metrics_coverage(metrics)

        assert coverage == 0.0

    def test_coverage_one_metric(self):
        """Test coverage calculation with one metric."""
        metrics = StrategyMetrics(
            sharpe_ratio=1.5,
            total_return=None,
            max_drawdown=None,
            execution_success=True
        )

        coverage = self.classifier._calculate_metrics_coverage(metrics)

        assert coverage == pytest.approx(1.0 / 3.0)

    def test_coverage_two_metrics(self):
        """Test coverage calculation with two metrics."""
        metrics = StrategyMetrics(
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=None,
            execution_success=True
        )

        coverage = self.classifier._calculate_metrics_coverage(metrics)

        assert coverage == pytest.approx(2.0 / 3.0)

    def test_coverage_all_metrics(self):
        """Test coverage calculation with all metrics."""
        metrics = StrategyMetrics(
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=-0.15,
            execution_success=True
        )

        coverage = self.classifier._calculate_metrics_coverage(metrics)

        assert coverage == 1.0

    def test_coverage_with_zero_values(self):
        """Test coverage calculation with zero values (not None)."""
        metrics = StrategyMetrics(
            sharpe_ratio=0.0,
            total_return=0.0,
            max_drawdown=0.0,
            execution_success=True
        )

        coverage = self.classifier._calculate_metrics_coverage(metrics)

        # Zero values count as extracted (not None)
        assert coverage == 1.0

    def test_coverage_negative_values(self):
        """Test coverage calculation with negative metric values."""
        metrics = StrategyMetrics(
            sharpe_ratio=-1.5,
            total_return=-0.10,
            max_drawdown=-0.25,
            execution_success=True
        )

        coverage = self.classifier._calculate_metrics_coverage(metrics)

        # Negative values still count as extracted (not None)
        assert coverage == 1.0


class TestSuccessClassifierClassificationLogic:
    """Test detailed classification logic and edge cases."""

    def setup_method(self):
        """Set up classifier for each test."""
        self.classifier = SuccessClassifier()

    def test_threshold_constants(self):
        """Test that threshold constants are as expected."""
        assert self.classifier.METRICS_COVERAGE_THRESHOLD == 0.60
        assert self.classifier.PROFITABILITY_THRESHOLD == 0.40

    def test_coverage_metrics_set(self):
        """Test that COVERAGE_METRICS set contains expected metrics."""
        assert 'sharpe_ratio' in self.classifier.COVERAGE_METRICS
        assert 'total_return' in self.classifier.COVERAGE_METRICS
        assert 'max_drawdown' in self.classifier.COVERAGE_METRICS
        assert len(self.classifier.COVERAGE_METRICS) == 3

    def test_single_classifier_instance_isolation(self):
        """Test that classifier instances are independent."""
        classifier1 = SuccessClassifier()
        classifier2 = SuccessClassifier()

        metrics = StrategyMetrics(
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=-0.15,
            execution_success=True
        )

        result1 = classifier1.classify_single(metrics)
        result2 = classifier2.classify_single(metrics)

        assert result1.level == result2.level
        assert result1.reason == result2.reason

    def test_single_low_sharpe_but_positive(self):
        """Test Level 3 with very low but positive Sharpe ratio."""
        metrics = StrategyMetrics(
            sharpe_ratio=0.001,  # Very small positive value
            total_return=0.01,
            max_drawdown=-0.05,
            execution_success=True
        )

        result = self.classifier.classify_single(metrics)

        assert result.level == 3
        assert "profitable" in result.reason.lower()

    def test_single_negative_sharpe_large(self):
        """Test Level 2 with large negative Sharpe ratio."""
        metrics = StrategyMetrics(
            sharpe_ratio=-10.5,  # Large negative
            total_return=0.25,
            max_drawdown=-0.15,
            execution_success=True
        )

        result = self.classifier.classify_single(metrics)

        assert result.level == 2
        assert "not profitable" in result.reason

    def test_batch_with_many_failures_one_success(self):
        """Test batch with many failures and one successful strategy."""
        metrics_list = [
            StrategyMetrics(execution_success=False),
            StrategyMetrics(execution_success=False),
            StrategyMetrics(execution_success=False),
            StrategyMetrics(execution_success=False),
            StrategyMetrics(
                sharpe_ratio=1.5,
                total_return=0.25,
                max_drawdown=-0.15,
                execution_success=True
            ),
        ]

        result = self.classifier.classify_batch(metrics_list)

        # One executed, profitable = Level 3
        assert result.level == 3
        assert result.profitable_count == 1
        assert result.total_count == 1

    def test_single_with_extreme_metrics(self):
        """Test classification with extreme metric values."""
        metrics = StrategyMetrics(
            sharpe_ratio=100.0,  # Very high Sharpe
            total_return=5.0,    # 500% return
            max_drawdown=-0.90,  # 90% drawdown
            execution_success=True
        )

        result = self.classifier.classify_single(metrics)

        assert result.level == 3
        assert result.metrics_coverage == 1.0

    def test_batch_reason_formatting(self):
        """Test that batch reason strings are well-formatted."""
        metrics_list = [
            StrategyMetrics(
                sharpe_ratio=1.5,
                total_return=0.25,
                max_drawdown=-0.15,
                execution_success=True
            ),
            StrategyMetrics(
                sharpe_ratio=-0.5,
                total_return=0.05,
                max_drawdown=-0.30,
                execution_success=True
            ),
        ]

        result = self.classifier.classify_batch(metrics_list)

        # Check that reason contains key information
        assert "1" in result.reason  # profitable count
        assert "2" in result.reason  # total count
        assert "50%" in result.reason or "50.0%" in result.reason  # profitability percentage


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
