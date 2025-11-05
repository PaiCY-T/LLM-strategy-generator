"""
Unit tests for ExtendedTestHarness statistical methods - Task 3.7.

This module tests the ExtendedTestHarness statistical analysis methods:
- calculate_cohens_d: Effect size calculation for learning improvement
- calculate_significance: Statistical significance testing
- calculate_confidence_intervals: 95% confidence interval calculation
- generate_statistical_report: Production readiness assessment
- save_checkpoint/load_checkpoint: Checkpoint management

Design Reference: tasks.md lines 316-327 (Task 3.7 specification)
Test Data Requirements:
- Cohen's d effect size interpretation (d≥0.4 guideline)
- Significance test (p<0.05 threshold)
- 95% confidence intervals
- Production readiness criteria (p<0.05, d≥0.4, σ<0.5)
"""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from tests.integration.extended_test_harness import ExtendedTestHarness


# ==============================================================================
# Test Fixtures
# ==============================================================================

@pytest.fixture
def harness(tmp_path, monkeypatch):
    """Create ExtendedTestHarness instance for testing with mocked logging and AutonomousLoop."""
    # Use temporary directory to avoid file conflicts
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()

    # Mock both AutonomousLoop and logging.basicConfig to avoid file handle issues
    with patch('tests.integration.extended_test_harness.AutonomousLoop'), \
         patch('logging.basicConfig'):
        harness_instance = ExtendedTestHarness(
            model="google/gemini-2.5-flash",
            target_iterations=50,
            checkpoint_interval=10,
            checkpoint_dir=str(checkpoint_dir)
        )

        # Replace logger with a Mock to avoid any logging calls
        harness_instance.logger = Mock()

        yield harness_instance


@pytest.fixture
def negligible_effect_sharpes() -> List[float]:
    """
    Sharpe ratios with negligible effect size (d < 0.2).

    First 10: mean = 1.0, std ≈ 0.5
    Last 10: mean = 1.05, std ≈ 0.5
    Small difference (0.05) with large variance (0.5) → negligible d
    """
    first_10 = [1.5, 1.0, 0.5, 1.2, 0.8, 1.3, 0.7, 1.1, 0.9, 1.0]  # mean ≈ 1.0
    last_10 = [1.55, 1.05, 0.55, 1.25, 0.85, 1.35, 0.75, 1.15, 0.95, 1.05]  # mean ≈ 1.05
    return first_10 + last_10


@pytest.fixture
def small_effect_sharpes() -> List[float]:
    """
    Sharpe ratios with small effect size (0.2 ≤ d < 0.5).

    First 10: mean = 1.0, std ≈ 0.3
    Last 10: mean = 1.1, std ≈ 0.3
    d ≈ 0.1 / 0.3 = 0.33 (small)
    """
    first_10 = [1.3, 1.0, 0.7, 1.2, 0.9, 1.1, 0.8, 1.0, 1.1, 0.9]  # mean ≈ 1.0
    last_10 = [1.4, 1.1, 0.8, 1.3, 1.0, 1.2, 0.9, 1.1, 1.2, 1.0]  # mean ≈ 1.1
    return first_10 + last_10


@pytest.fixture
def medium_effect_sharpes() -> List[float]:
    """
    Sharpe ratios with medium effect size (0.5 ≤ d < 0.8).

    First 10: mean = 1.0, std ≈ 0.2
    Last 10: mean = 1.12, std ≈ 0.2
    d ≈ 0.12 / 0.2 = 0.6 (medium)
    """
    first_10 = [1.2, 1.0, 0.8, 1.1, 0.9, 1.0, 1.1, 0.9, 1.0, 1.0]  # mean = 1.0
    last_10 = [1.32, 1.12, 0.92, 1.22, 1.02, 1.12, 1.22, 1.02, 1.12, 1.12]  # mean = 1.12
    return first_10 + last_10


@pytest.fixture
def large_effect_sharpes() -> List[float]:
    """
    Sharpe ratios with large effect size (d ≥ 0.8).

    First 10: mean = 0.5, std ≈ 0.1
    Last 10: mean = 1.5, std ≈ 0.1
    d ≈ 1.0 / 0.1 = 10.0 (very large)
    """
    first_10 = [0.6, 0.5, 0.4, 0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5]
    last_10 = [1.6, 1.5, 1.4, 1.5, 1.6, 1.4, 1.5, 1.6, 1.4, 1.5]
    return first_10 + last_10


@pytest.fixture
def significant_sharpes() -> List[float]:
    """
    Sharpe ratios with statistically significant improvement (p < 0.05).

    First 10: mean ≈ 0.5, consistent values
    Last 10: mean ≈ 1.5, consistent values
    Large, consistent difference → high significance
    """
    first_10 = [0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5]
    last_10 = [1.5, 1.6, 1.4, 1.5, 1.6, 1.4, 1.5, 1.6, 1.4, 1.5]
    return first_10 + last_10


@pytest.fixture
def non_significant_sharpes() -> List[float]:
    """
    Sharpe ratios with non-significant difference (p ≥ 0.05).

    First 10: mean ≈ 1.0, high variance
    Last 10: mean ≈ 1.05, high variance
    Small difference + high variance → low significance
    """
    first_10 = [0.8, 1.2, 0.9, 1.1, 1.0, 0.9, 1.2, 0.8, 1.0, 1.1]
    last_10 = [0.85, 1.25, 0.95, 1.15, 1.05, 0.95, 1.25, 0.85, 1.05, 1.15]
    return first_10 + last_10


@pytest.fixture
def production_ready_sharpes() -> List[float]:
    """
    Sharpe ratios meeting production readiness criteria.

    Criteria:
    - Statistical significance: p < 0.05 (large consistent improvement)
    - Meaningful effect size: d ≥ 0.4 (large effect)
    - Convergence: rolling variance (last 10) < 0.5 (low variance)

    20 iterations with clear improvement and low final variance.
    """
    return [
        0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4,  # First 10
        1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4   # Last 10
    ]


@pytest.fixture
def not_ready_no_significance_sharpes() -> List[float]:
    """
    Sharpe ratios failing production readiness due to lack of significance.

    No clear improvement between first and second half.
    """
    # Same values in both halves → p ≥ 0.05
    return [1.0] * 10 + [1.0] * 10


@pytest.fixture
def not_ready_small_effect_sharpes() -> List[float]:
    """
    Sharpe ratios failing production readiness due to small effect size.

    Improvement exists but effect size d < 0.4.
    """
    # Small improvement: d ≈ 0.25 (< 0.4 threshold)
    first_10 = [1.0, 1.2, 0.8, 1.1, 0.9, 1.0, 1.1, 0.9, 1.0, 1.0]  # mean = 1.0, std ≈ 0.13
    last_10 = [1.03, 1.23, 0.83, 1.13, 0.93, 1.03, 1.13, 0.93, 1.03, 1.03]  # mean = 1.03, d ≈ 0.23
    return first_10 + last_10


@pytest.fixture
def not_ready_no_convergence_sharpes() -> List[float]:
    """
    Sharpe ratios failing production readiness due to lack of convergence.

    Large improvement but high final variance (rolling std ≥ 0.5).
    """
    # Large improvement but high variance in last 10
    first_10 = [0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5]
    # Last 10 with high variance
    last_10 = [1.0, 2.0, 0.5, 2.5, 1.0, 2.0, 0.5, 2.5, 1.0, 2.0]
    return first_10 + last_10


@pytest.fixture
def temp_checkpoint_dir(tmp_path):
    """Create temporary directory for checkpoint testing."""
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()
    return checkpoint_dir


# ==============================================================================
# Test: calculate_cohens_d - Effect Size Calculation
# ==============================================================================

def test_calculate_cohens_d_negligible_effect(harness, negligible_effect_sharpes):
    """Test Cohen's d calculation with negligible effect size (d < 0.2)."""
    # Act
    cohens_d, interpretation = harness.calculate_cohens_d(negligible_effect_sharpes)

    # Assert
    assert abs(cohens_d) < 0.2, f"Expected negligible effect (d < 0.2), got {cohens_d}"
    assert interpretation == "negligible", \
        f"Expected 'negligible' interpretation, got '{interpretation}'"


def test_calculate_cohens_d_small_effect(harness, small_effect_sharpes):
    """Test Cohen's d calculation with small effect size (0.2 ≤ d < 0.5)."""
    # Act
    cohens_d, interpretation = harness.calculate_cohens_d(small_effect_sharpes)

    # Assert
    assert 0.2 <= abs(cohens_d) < 0.5, \
        f"Expected small effect (0.2 ≤ d < 0.5), got {cohens_d}"
    assert interpretation == "small", \
        f"Expected 'small' interpretation, got '{interpretation}'"


def test_calculate_cohens_d_medium_effect(harness, medium_effect_sharpes):
    """Test Cohen's d calculation with medium effect size (0.5 ≤ d < 0.8)."""
    # Act
    cohens_d, interpretation = harness.calculate_cohens_d(medium_effect_sharpes)

    # Assert
    assert 0.5 <= abs(cohens_d) < 0.8, \
        f"Expected medium effect (0.5 ≤ d < 0.8), got {cohens_d}"
    assert interpretation == "medium", \
        f"Expected 'medium' interpretation, got '{interpretation}'"


def test_calculate_cohens_d_large_effect(harness, large_effect_sharpes):
    """Test Cohen's d calculation with large effect size (d ≥ 0.8)."""
    # Act
    cohens_d, interpretation = harness.calculate_cohens_d(large_effect_sharpes)

    # Assert
    assert abs(cohens_d) >= 0.8, \
        f"Expected large effect (d ≥ 0.8), got {cohens_d}"
    assert interpretation == "large", \
        f"Expected 'large' interpretation, got '{interpretation}'"


def test_calculate_cohens_d_zero_variance(harness):
    """Test Cohen's d with zero variance (identical groups)."""
    # Arrange - All identical values (zero variance)
    sharpes = [1.0] * 20

    # Act
    cohens_d, interpretation = harness.calculate_cohens_d(sharpes)

    # Assert
    assert cohens_d == 0.0, "Zero variance should result in d=0"
    assert interpretation == "negligible", \
        "Zero variance should be interpreted as negligible"


def test_calculate_cohens_d_negative_effect(harness):
    """Test Cohen's d with negative effect (performance decline)."""
    # Arrange - Last 10 worse than first 10
    first_10 = [1.5, 1.6, 1.4, 1.5, 1.6, 1.4, 1.5, 1.6, 1.4, 1.5]
    last_10 = [0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5]
    sharpes = first_10 + last_10

    # Act
    cohens_d, interpretation = harness.calculate_cohens_d(sharpes)

    # Assert
    assert cohens_d < 0, "Decline should result in negative Cohen's d"
    assert abs(cohens_d) >= 0.8, "Large decline should have large effect size"
    assert interpretation == "large", "Large decline should be interpreted as large"


def test_calculate_cohens_d_insufficient_data(harness):
    """Test Cohen's d raises ValueError with insufficient data (<20 iterations)."""
    # Arrange
    sharpes = [1.0] * 19  # Only 19 values (need 20)

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        harness.calculate_cohens_d(sharpes)

    assert "at least 20" in str(exc_info.value).lower()


# ==============================================================================
# Test: calculate_significance - Statistical Significance Testing
# ==============================================================================

def test_calculate_significance_significant(harness, significant_sharpes):
    """Test significance calculation with statistically significant data (p < 0.05)."""
    # Act
    p_value, is_significant, interpretation = harness.calculate_significance(significant_sharpes)

    # Assert
    assert p_value < 0.05, f"Expected p < 0.05 for significant data, got {p_value}"
    assert is_significant is True, "Should detect significance"
    assert "significant" in interpretation.lower(), \
        f"Expected 'significant' in interpretation, got '{interpretation}'"


def test_calculate_significance_non_significant(harness, non_significant_sharpes):
    """Test significance calculation with non-significant data (p ≥ 0.05)."""
    # Act
    p_value, is_significant, interpretation = harness.calculate_significance(non_significant_sharpes)

    # Assert
    assert p_value >= 0.05, f"Expected p ≥ 0.05 for non-significant data, got {p_value}"
    assert is_significant is False, "Should not detect significance"
    assert "no significant" in interpretation.lower(), \
        f"Expected 'no significant' in interpretation, got '{interpretation}'"


def test_calculate_significance_identical_halves(harness):
    """Test significance with identical first and second halves."""
    # Arrange - Identical values in both halves
    sharpes = [1.0] * 20

    # Act
    p_value, is_significant, interpretation = harness.calculate_significance(sharpes)

    # Assert
    assert p_value >= 0.05, "Identical halves should not be significant"
    assert is_significant is False, "Should not detect significance"
    assert "no significant" in interpretation.lower()


def test_calculate_significance_minimal_data(harness):
    """Test significance with minimal data (4 values - boundary case)."""
    # Arrange - 4 values minimum for paired t-test
    sharpes = [0.5, 0.6, 1.5, 1.6]  # Clear improvement

    # Act
    p_value, is_significant, interpretation = harness.calculate_significance(sharpes)

    # Assert
    # Should complete without error
    assert isinstance(p_value, float), "Should return float p-value"
    assert isinstance(is_significant, bool), "Should return boolean significance"
    assert isinstance(interpretation, str), "Should return string interpretation"


def test_calculate_significance_insufficient_data(harness):
    """Test significance raises ValueError with insufficient data (<4 iterations)."""
    # Arrange
    sharpes = [1.0, 1.5, 2.0]  # Only 3 values (need 4)

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        harness.calculate_significance(sharpes)

    assert "at least 4" in str(exc_info.value).lower()


def test_calculate_significance_decline_detected(harness):
    """Test significance detection for performance decline."""
    # Arrange - Second half worse than first half
    first_10 = [1.5] * 10
    last_10 = [0.5] * 10
    sharpes = first_10 + last_10

    # Act
    p_value, is_significant, interpretation = harness.calculate_significance(sharpes)

    # Assert
    assert is_significant is True, "Significant decline should be detected"
    assert "decline" in interpretation.lower(), \
        f"Expected 'decline' in interpretation, got '{interpretation}'"


# ==============================================================================
# Test: calculate_confidence_intervals - 95% CI Calculation
# ==============================================================================

def test_calculate_confidence_intervals_normal(harness):
    """Test 95% confidence interval calculation with known distribution."""
    # Arrange - Known mean and standard deviation
    sharpes = [1.0, 1.2, 0.8, 1.1, 0.9, 1.0, 1.2, 0.8, 1.1, 0.9]  # Mean ≈ 1.0

    # Act
    lower_bound, upper_bound = harness.calculate_confidence_intervals(sharpes)

    # Assert
    mean = np.mean(sharpes)
    assert lower_bound < mean < upper_bound, \
        "Mean should be within confidence interval"
    assert lower_bound < upper_bound, \
        "Lower bound should be less than upper bound"

    # CI width should be reasonable (not too wide)
    width = upper_bound - lower_bound
    assert width < 1.0, f"CI width seems too large: {width}"


def test_calculate_confidence_intervals_single_value(harness):
    """Test confidence intervals with single value repeated (zero variance)."""
    # Arrange - All identical values
    sharpes = [1.0] * 10

    # Act
    lower_bound, upper_bound = harness.calculate_confidence_intervals(sharpes)

    # Assert
    # With zero variance, CI should be very narrow (essentially the mean)
    assert abs(lower_bound - 1.0) < 0.001, "Lower bound should be ≈ mean"
    assert abs(upper_bound - 1.0) < 0.001, "Upper bound should be ≈ mean"


def test_calculate_confidence_intervals_minimal_data(harness):
    """Test confidence intervals with minimal data (2 values - boundary case)."""
    # Arrange - 2 values minimum for CI calculation
    sharpes = [1.0, 2.0]

    # Act
    lower_bound, upper_bound = harness.calculate_confidence_intervals(sharpes)

    # Assert
    mean = 1.5
    assert lower_bound < mean < upper_bound, "Mean should be within CI"

    # With only 2 values, CI should be relatively wide
    width = upper_bound - lower_bound
    assert width > 0.5, "CI should be wide with only 2 values"


def test_calculate_confidence_intervals_insufficient_data(harness):
    """Test confidence intervals raise ValueError with insufficient data (<2 iterations)."""
    # Arrange
    sharpes = [1.0]  # Only 1 value (need 2)

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        harness.calculate_confidence_intervals(sharpes)

    assert "at least 2" in str(exc_info.value).lower()


def test_calculate_confidence_intervals_accuracy(harness):
    """Test 95% CI calculation accuracy with known distribution."""
    # Arrange - Generate data with known mean (1.0) and std (0.1)
    np.random.seed(42)  # Reproducible
    sharpes = list(np.random.normal(1.0, 0.1, 100))

    # Act
    lower_bound, upper_bound = harness.calculate_confidence_intervals(sharpes)

    # Assert
    # For large sample (n=100), CI should be tight around mean
    mean = np.mean(sharpes)
    assert abs(mean - 1.0) < 0.05, "Sample mean should be ≈ 1.0"

    # CI width should be reasonable for n=100
    width = upper_bound - lower_bound
    assert width < 0.1, f"CI should be tight with n=100, got width={width}"


# ==============================================================================
# Test: generate_statistical_report - Production Readiness Assessment
# ==============================================================================

def test_generate_statistical_report_production_ready(harness, production_ready_sharpes):
    """Test statistical report generation for production-ready scenario."""
    # Arrange
    harness.sharpes = production_ready_sharpes
    harness.durations = [10.0] * len(production_ready_sharpes)
    harness.champion_updates = [False] * len(production_ready_sharpes)
    harness.champion_updates[0] = True  # Champion update on first iteration

    # Act
    report = harness.generate_statistical_report()

    # Assert - Production readiness
    assert report['production_ready'] is True, \
        "Should be production ready (p<0.05, d≥0.4, σ<0.5)"

    # Assert - Individual criteria
    assert report['is_significant'] is True, "Should have statistical significance"
    assert report['p_value'] < 0.05, f"p-value should be < 0.05, got {report['p_value']}"
    assert report['cohens_d'] >= 0.4, f"Cohen's d should be ≥ 0.4, got {report['cohens_d']}"
    assert report['rolling_variance'] < 0.5, \
        f"Rolling variance should be < 0.5, got {report['rolling_variance']}"
    assert report['convergence_achieved'] is True, "Should achieve convergence"

    # Assert - Readiness reasoning
    assert len(report['readiness_reasoning']) > 0, "Should have readiness reasoning"
    assert "READY FOR PRODUCTION" in report['readiness_reasoning'][0], \
        "Should indicate production readiness"


def test_generate_statistical_report_not_ready_no_significance(harness, not_ready_no_significance_sharpes):
    """Test statistical report for non-production-ready (no significance) scenario."""
    # Arrange
    harness.sharpes = not_ready_no_significance_sharpes
    harness.durations = [10.0] * len(not_ready_no_significance_sharpes)
    harness.champion_updates = [False] * len(not_ready_no_significance_sharpes)

    # Act
    report = harness.generate_statistical_report()

    # Assert
    assert report['production_ready'] is False, \
        "Should NOT be production ready (p ≥ 0.05)"
    assert report['is_significant'] is False, "Should not have significance"
    assert report['p_value'] >= 0.05, "p-value should be ≥ 0.05"

    # Assert - Readiness reasoning should explain failure
    reasoning_text = ' '.join(report['readiness_reasoning'])
    assert "NOT READY" in reasoning_text, "Should indicate not ready"
    assert "significance" in reasoning_text.lower(), \
        "Should mention significance failure"


def test_generate_statistical_report_not_ready_small_effect(harness, not_ready_small_effect_sharpes):
    """Test statistical report for non-production-ready (small effect size) scenario."""
    # Arrange
    harness.sharpes = not_ready_small_effect_sharpes
    harness.durations = [10.0] * len(not_ready_small_effect_sharpes)
    harness.champion_updates = [False] * len(not_ready_small_effect_sharpes)

    # Act
    report = harness.generate_statistical_report()

    # Assert
    assert report['production_ready'] is False, \
        "Should NOT be production ready (d < 0.4)"
    assert report['cohens_d'] < 0.4, "Cohen's d should be < 0.4"

    # Assert - Readiness reasoning should explain failure
    reasoning_text = ' '.join(report['readiness_reasoning'])
    assert "NOT READY" in reasoning_text, "Should indicate not ready"
    assert "effect size" in reasoning_text.lower(), \
        "Should mention effect size failure"


def test_generate_statistical_report_not_ready_no_convergence(harness, not_ready_no_convergence_sharpes):
    """Test statistical report for non-production-ready (no convergence) scenario."""
    # Arrange
    harness.sharpes = not_ready_no_convergence_sharpes
    harness.durations = [10.0] * len(not_ready_no_convergence_sharpes)
    harness.champion_updates = [False] * len(not_ready_no_convergence_sharpes)

    # Act
    report = harness.generate_statistical_report()

    # Assert
    assert report['production_ready'] is False, \
        "Should NOT be production ready (σ ≥ 0.5)"
    assert report['rolling_variance'] >= 0.5, "Rolling variance should be ≥ 0.5"
    assert report['convergence_achieved'] is False, "Should not achieve convergence"

    # Assert - Readiness reasoning should explain failure
    reasoning_text = ' '.join(report['readiness_reasoning'])
    assert "NOT READY" in reasoning_text, "Should indicate not ready"
    assert "convergence" in reasoning_text.lower(), \
        "Should mention convergence failure"


def test_generate_statistical_report_comprehensive_structure(harness, production_ready_sharpes):
    """Test that statistical report has complete structure."""
    # Arrange
    harness.sharpes = production_ready_sharpes
    harness.durations = [10.0] * len(production_ready_sharpes)
    harness.champion_updates = [True, False] * 10  # 50% update frequency

    # Act
    report = harness.generate_statistical_report()

    # Assert - All required fields present
    required_fields = [
        'sample_size', 'mean_sharpe', 'std_sharpe', 'min_sharpe', 'max_sharpe',
        'cohens_d', 'effect_size_interpretation',
        'p_value', 'is_significant',
        'confidence_interval_95',
        'rolling_variance', 'convergence_achieved',
        'production_ready', 'readiness_reasoning',
        'champion_update_frequency', 'avg_duration_per_iteration'
    ]

    for field in required_fields:
        assert field in report, f"Missing required field: {field}"

    # Assert - Field types
    assert isinstance(report['sample_size'], int)
    assert isinstance(report['mean_sharpe'], float)
    assert isinstance(report['cohens_d'], float)
    assert isinstance(report['p_value'], float)
    assert isinstance(report['is_significant'], bool)
    assert isinstance(report['confidence_interval_95'], tuple)
    assert len(report['confidence_interval_95']) == 2
    assert isinstance(report['production_ready'], bool)
    assert isinstance(report['readiness_reasoning'], list)
    assert isinstance(report['champion_update_frequency'], float)

    # Assert - Champion update frequency calculation
    expected_frequency = 50.0  # 50% updates
    assert abs(report['champion_update_frequency'] - expected_frequency) < 1.0, \
        f"Expected ~50% update frequency, got {report['champion_update_frequency']}"


def test_generate_statistical_report_insufficient_data(harness):
    """Test statistical report raises ValueError with insufficient data (<20 iterations)."""
    # Arrange
    harness.sharpes = [1.0] * 19  # Only 19 iterations (need 20)
    harness.durations = [10.0] * 19
    harness.champion_updates = [False] * 19

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        harness.generate_statistical_report()

    assert "at least 20" in str(exc_info.value).lower()


# ==============================================================================
# Test: save_checkpoint / load_checkpoint - Checkpoint Management
# ==============================================================================

def test_save_checkpoint_creates_valid_json(harness, temp_checkpoint_dir):
    """Test save_checkpoint creates valid JSON file with complete data."""
    # Arrange
    harness.checkpoint_dir = temp_checkpoint_dir
    harness.sharpes = [1.0, 1.5, 2.0]
    harness.durations = [10.0, 12.0, 11.0]
    harness.champion_updates = [True, False, True]
    harness.iteration_records = [
        {'iteration': 0, 'sharpe': 1.0},
        {'iteration': 1, 'sharpe': 1.5},
        {'iteration': 2, 'sharpe': 2.0}
    ]

    # Act
    checkpoint_path = harness.save_checkpoint(iteration=2)

    # Assert - File exists
    assert checkpoint_path != "", "Should return non-empty path"
    assert Path(checkpoint_path).exists(), "Checkpoint file should exist"

    # Assert - Valid JSON
    with open(checkpoint_path, 'r') as f:
        data = json.load(f)

    # Assert - Required fields
    required_fields = [
        'iteration_number', 'timestamp',
        'sharpes', 'durations', 'champion_updates', 'iteration_records',
        'champion_state'
    ]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Assert - Data integrity
    assert data['iteration_number'] == 2
    assert data['sharpes'] == harness.sharpes
    assert data['durations'] == harness.durations
    assert data['champion_updates'] == harness.champion_updates
    assert data['iteration_records'] == harness.iteration_records


def test_load_checkpoint_restores_state(harness, temp_checkpoint_dir):
    """Test load_checkpoint restores test state correctly."""
    # Arrange - Save checkpoint first
    harness.checkpoint_dir = temp_checkpoint_dir
    harness.sharpes = [1.0, 1.5, 2.0]
    harness.durations = [10.0, 12.0, 11.0]
    harness.champion_updates = [True, False, True]
    harness.iteration_records = [
        {'iteration': 0, 'sharpe': 1.0},
        {'iteration': 1, 'sharpe': 1.5},
        {'iteration': 2, 'sharpe': 2.0}
    ]
    checkpoint_path = harness.save_checkpoint(iteration=2)

    # Create new harness instance (simulating fresh start)
    harness2 = ExtendedTestHarness(
        model="google/gemini-2.5-flash",
        target_iterations=50,
        checkpoint_interval=10,
        checkpoint_dir=str(temp_checkpoint_dir)
    )

    # Act
    resume_iteration = harness2.load_checkpoint(checkpoint_path)

    # Assert - Resume iteration
    assert resume_iteration == 3, "Should resume from iteration 3 (2+1)"

    # Assert - State restored
    assert harness2.sharpes == [1.0, 1.5, 2.0], "Sharpes should be restored"
    assert harness2.durations == [10.0, 12.0, 11.0], "Durations should be restored"
    assert harness2.champion_updates == [True, False, True], \
        "Champion updates should be restored"
    assert len(harness2.iteration_records) == 3, "Records should be restored"


def test_load_checkpoint_handles_missing_file(harness):
    """Test load_checkpoint raises FileNotFoundError for missing file."""
    # Arrange
    nonexistent_path = "/nonexistent/checkpoint.json"

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        harness.load_checkpoint(nonexistent_path)


def test_load_checkpoint_handles_corrupted_json(harness, temp_checkpoint_dir):
    """Test load_checkpoint raises JSONDecodeError for corrupted file."""
    # Arrange - Create corrupted JSON file
    corrupted_file = temp_checkpoint_dir / "corrupted.json"
    with open(corrupted_file, 'w') as f:
        f.write("{ this is not valid JSON }")

    # Act & Assert
    with pytest.raises(json.JSONDecodeError):
        harness.load_checkpoint(str(corrupted_file))


def test_load_checkpoint_handles_missing_fields(harness, temp_checkpoint_dir):
    """Test load_checkpoint raises KeyError for incomplete checkpoint."""
    # Arrange - Create checkpoint missing required fields
    incomplete_file = temp_checkpoint_dir / "incomplete.json"
    incomplete_data = {
        'iteration_number': 5,
        'sharpes': [1.0, 1.5]
        # Missing: durations, champion_updates, iteration_records
    }
    with open(incomplete_file, 'w') as f:
        json.dump(incomplete_data, f)

    # Act & Assert
    with pytest.raises(KeyError):
        harness.load_checkpoint(str(incomplete_file))


def test_checkpoint_data_completeness(harness, temp_checkpoint_dir):
    """Test checkpoint contains all necessary data for full state restoration."""
    # Arrange - Set up complete state
    harness.checkpoint_dir = temp_checkpoint_dir
    harness.sharpes = [1.0, 1.5, 2.0, 2.5]
    harness.durations = [10.0, 11.0, 12.0, 13.0]
    harness.champion_updates = [True, False, True, False]
    harness.iteration_records = [
        {'iteration': i, 'sharpe': s, 'duration': d}
        for i, (s, d) in enumerate(zip(harness.sharpes, harness.durations))
    ]

    # Mock champion state
    harness.loop.champion = Mock()
    harness.loop.champion.get = lambda key: {
        'sharpe': 2.5,
        'iteration': 3,
        'metrics': {'sharpe_ratio': 2.5, 'total_return': 0.35}
    }.get(key)

    # Act - Save and load
    checkpoint_path = harness.save_checkpoint(iteration=3)
    harness2 = ExtendedTestHarness(
        model="google/gemini-2.5-flash",
        target_iterations=50,
        checkpoint_interval=10,
        checkpoint_dir=str(temp_checkpoint_dir)
    )
    resume_iteration = harness2.load_checkpoint(checkpoint_path)

    # Assert - All data preserved
    assert resume_iteration == 4
    assert harness2.sharpes == harness.sharpes
    assert harness2.durations == harness.durations
    assert harness2.champion_updates == harness.champion_updates
    assert harness2.iteration_records == harness.iteration_records

    # Verify checkpoint includes champion state
    with open(checkpoint_path, 'r') as f:
        checkpoint_data = json.load(f)
    assert checkpoint_data['champion_state'] is not None, \
        "Checkpoint should include champion state"
    assert checkpoint_data['champion_state']['sharpe'] == 2.5


# ==============================================================================
# Test: run_test - Main Orchestration (Mocked)
# ==============================================================================

@patch('tests.integration.extended_test_harness.AutonomousLoop')
def test_run_test_orchestration_basic(mock_loop_class, harness):
    """Test run_test orchestration with mocked AutonomousLoop (basic flow)."""
    # Arrange - Mock AutonomousLoop instance
    mock_loop = Mock()
    mock_loop_class.return_value = mock_loop

    # Mock successful iteration
    mock_loop.run_iteration.return_value = (True, "SUCCESS")
    mock_loop.champion = None

    # Mock history record
    mock_record = Mock()
    mock_record.metrics = {'sharpe_ratio': 1.5, 'total_return': 0.25}
    mock_loop.history.get_record.return_value = mock_record

    # Set small target for testing
    harness.target_iterations = 3
    harness.loop = mock_loop

    # Mock data
    mock_data = Mock()

    # Act
    results = harness.run_test(mock_data)

    # Assert - Test completion
    assert results['test_completed'] is True, "Test should complete"
    assert results['total_iterations'] == 3, "Should run 3 iterations"
    assert results['success_count'] == 3, "All iterations should succeed"
    assert results['failure_count'] == 0, "Should have no failures"

    # Assert - Loop interaction
    assert mock_loop.run_iteration.call_count == 3, \
        "Should call run_iteration 3 times"


@patch('tests.integration.extended_test_harness.AutonomousLoop')
def test_run_test_retry_logic(mock_loop_class, harness):
    """Test run_test retry logic on iteration failures."""
    # Arrange
    mock_loop = Mock()
    mock_loop_class.return_value = mock_loop
    harness.loop = mock_loop
    harness.target_iterations = 2

    # First iteration fails twice then succeeds
    # Second iteration succeeds immediately
    mock_loop.run_iteration.side_effect = [
        (False, "VALIDATION_FAILED"),  # First attempt fails
        (False, "VALIDATION_FAILED"),  # Second attempt fails
        (True, "SUCCESS"),              # Third attempt succeeds
        (True, "SUCCESS")               # Second iteration succeeds
    ]

    # Mock history records
    failed_record = Mock()
    failed_record.metrics = None
    failed_record.validation_passed = False
    failed_record.validation_errors = ["Error 1"]
    failed_record.execution_error = None

    success_record = Mock()
    success_record.metrics = {'sharpe_ratio': 1.5}

    mock_loop.history.get_record.side_effect = [
        failed_record, failed_record, success_record, success_record
    ]
    mock_loop.champion = None

    mock_data = Mock()

    # Act
    results = harness.run_test(mock_data)

    # Assert
    assert mock_loop.run_iteration.call_count == 4, \
        "Should retry failed iteration twice then succeed, plus second iteration"
    assert results['success_count'] == 2, "Should have 2 successful iterations"
    assert results['failure_count'] == 0, \
        "Retried iterations should count as success"


@patch('tests.integration.extended_test_harness.AutonomousLoop')
def test_run_test_checkpoint_interval(mock_loop_class, harness, temp_checkpoint_dir):
    """Test run_test saves checkpoints at correct intervals."""
    # Arrange
    mock_loop = Mock()
    mock_loop_class.return_value = mock_loop
    harness.loop = mock_loop
    harness.checkpoint_dir = temp_checkpoint_dir
    harness.checkpoint_interval = 2  # Save every 2 iterations
    harness.target_iterations = 5

    # Mock successful iterations
    mock_loop.run_iteration.return_value = (True, "SUCCESS")
    mock_loop.champion = None

    mock_record = Mock()
    mock_record.metrics = {'sharpe_ratio': 1.5}
    mock_loop.history.get_record.return_value = mock_record

    mock_data = Mock()

    # Act
    results = harness.run_test(mock_data)

    # Assert - Checkpoints created
    checkpoint_files = list(temp_checkpoint_dir.glob("checkpoint_iter_*.json"))

    # Should have checkpoints at iterations 1, 3, and final (4)
    assert len(checkpoint_files) >= 2, \
        f"Should have at least 2 checkpoint files, got {len(checkpoint_files)}"


@patch('tests.integration.extended_test_harness.AutonomousLoop')
def test_run_test_generates_statistical_report(mock_loop_class, harness):
    """Test run_test generates statistical report for sufficient data."""
    # Arrange
    mock_loop = Mock()
    mock_loop_class.return_value = mock_loop
    harness.loop = mock_loop
    harness.target_iterations = 20  # Minimum for statistical report

    # Mock successful iterations with improving Sharpe
    def mock_run_iteration(i, data):
        return (True, "SUCCESS")

    mock_loop.run_iteration.side_effect = mock_run_iteration
    mock_loop.champion = None

    # Mock records with improving Sharpe
    def mock_get_record(i):
        record = Mock()
        record.metrics = {'sharpe_ratio': 0.5 + i * 0.1}  # Improving
        return record

    mock_loop.history.get_record.side_effect = mock_get_record

    mock_data = Mock()

    # Act
    results = harness.run_test(mock_data)

    # Assert
    assert 'statistical_report' in results, "Should include statistical report"
    assert results['statistical_report'] is not None, \
        "Statistical report should not be None"
    assert 'production_ready' in results['statistical_report'], \
        "Report should include production_ready field"
