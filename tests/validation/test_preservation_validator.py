"""Unit tests for PreservationValidator (Story 2: Enhanced Preservation).

Tests comprehensive preservation validation including:
- Parameter preservation (ROE type, liquidity threshold)
- Behavioral similarity checks (Sharpe, turnover, concentration)
- False positive risk calculation
- PreservationReport generation
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch

from src.validation.preservation_validator import (
    PreservationValidator,
    PreservationReport,
    BehavioralCheck
)


# Test Fixtures
@pytest.fixture
def champion_strategy():
    """Mock champion strategy with typical parameters."""
    champion = Mock()
    champion.parameters = {
        'roe_type': 'smoothed',
        'roe_smoothing_window': 4,
        'liquidity_threshold': 100_000_000,
        'revenue_handling': 'forward_fill',
        'value_factor': 'pe_ratio'
    }
    champion.metrics = {
        'sharpe_ratio': 1.5,
        'annual_return': 0.25,
        'max_drawdown': -0.15
    }
    return champion


@pytest.fixture
def validator():
    """PreservationValidator instance with default tolerances."""
    return PreservationValidator(
        sharpe_tolerance=0.10,
        turnover_tolerance=0.20,
        concentration_tolerance=0.15
    )


# Test Suite 1: Parameter Preservation
class TestParameterPreservation:
    """Test parameter preservation validation."""

    def test_roe_smoothing_preserved(self, validator, champion_strategy):
        """Test ROE smoothing preservation within ±20%."""
        code_with_roe = """
        roe_avg = roe.rolling(window=4, min_periods=1).mean().shift(1)
        liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000
        """

        is_preserved, report = validator.validate_preservation(
            generated_code=code_with_roe,
            champion=champion_strategy,
            execution_metrics=None
        )

        assert is_preserved, "ROE smoothing should be preserved"
        assert 'roe_smoothing' in report.critical_params_preserved
        assert len(report.missing_params) == 0

    def test_roe_type_violation(self, validator, champion_strategy):
        """Test ROE type change detection (smoothed → raw)."""
        code_without_smoothing = """
        roe_shift = roe.shift(1)  # Raw ROE, no smoothing
        liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000
        """

        is_preserved, report = validator.validate_preservation(
            generated_code=code_without_smoothing,
            champion=champion_strategy,
            execution_metrics=None
        )

        assert not is_preserved, "ROE type change should violate preservation"
        assert 'roe_smoothing' in report.missing_params
        assert any('ROE type changed' in str(reason) for _, reason in report.parameter_checks.values())

    def test_roe_window_deviation_excessive(self, validator, champion_strategy):
        """Test ROE window change exceeding ±20%."""
        code_with_large_window = """
        roe_avg = roe.rolling(window=8, min_periods=1).mean().shift(1)  # 100% increase
        liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000
        """

        is_preserved, report = validator.validate_preservation(
            generated_code=code_with_large_window,
            champion=champion_strategy,
            execution_metrics=None
        )

        assert not is_preserved, "Excessive window change should violate preservation"
        assert any('Window changed by' in str(reason) for _, reason in report.parameter_checks.values())

    def test_liquidity_threshold_preserved(self, validator, champion_strategy):
        """Test liquidity threshold preservation (≥80% of champion)."""
        code_with_liquidity = """
        roe_avg = roe.rolling(window=4).mean().shift(1)
        liquidity_filter = trading_value.rolling(20).mean().shift(1) > 90_000_000  # 90% of champion
        """

        is_preserved, report = validator.validate_preservation(
            generated_code=code_with_liquidity,
            champion=champion_strategy,
            execution_metrics=None
        )

        assert is_preserved, "Liquidity at 90% of champion should be preserved"
        assert 'liquidity_threshold' in report.critical_params_preserved

    def test_liquidity_threshold_relaxed(self, validator, champion_strategy):
        """Test liquidity threshold relaxation (<80%)."""
        code_relaxed_liquidity = """
        roe_avg = roe.rolling(window=4).mean().shift(1)
        liquidity_filter = trading_value.rolling(20).mean().shift(1) > 70_000_000  # 70% of champion
        """

        is_preserved, report = validator.validate_preservation(
            generated_code=code_relaxed_liquidity,
            champion=champion_strategy,
            execution_metrics=None
        )

        assert not is_preserved, "Liquidity below 80% should violate preservation"
        assert any('Threshold relaxed by' in str(reason) for _, reason in report.parameter_checks.values())

    def test_liquidity_filter_removed(self, validator, champion_strategy):
        """Test liquidity filter removal detection."""
        code_without_liquidity = """
        roe_avg = roe.rolling(window=4).mean().shift(1)
        # No liquidity filter
        """

        is_preserved, report = validator.validate_preservation(
            generated_code=code_without_liquidity,
            champion=champion_strategy,
            execution_metrics=None
        )

        assert not is_preserved, "Liquidity filter removal should violate preservation"
        assert 'liquidity_threshold' in report.missing_params


# Test Suite 2: Behavioral Similarity
class TestBehavioralSimilarity:
    """Test behavioral similarity checks."""

    def test_sharpe_similarity_within_bounds(self, validator, champion_strategy):
        """Test Sharpe ratio within ±10%."""
        execution_metrics = {
            'sharpe_ratio': 1.55,  # +3.3% from champion (1.5)
            'annual_return': 0.26
        }

        is_preserved, report = validator.validate_preservation(
            generated_code="roe_avg = roe.rolling(window=4).mean().shift(1)\nliquidity_filter = trading_value > 100_000_000",
            champion=champion_strategy,
            execution_metrics=execution_metrics
        )

        assert is_preserved, "Sharpe within ±10% should pass"
        assert report.behavioral_similarity_score >= 0.7
        assert any(check.check_name == 'sharpe_similarity' and check.passed for check in report.behavioral_checks)

    def test_sharpe_deviation_excessive(self, validator, champion_strategy):
        """Test Sharpe ratio exceeding ±10%."""
        execution_metrics = {
            'sharpe_ratio': 1.8,  # +20% from champion (excessive)
            'annual_return': 0.30
        }

        is_preserved, report = validator.validate_preservation(
            generated_code="roe_avg = roe.rolling(window=4).mean().shift(1)\nliquidity_filter = trading_value > 100_000_000",
            champion=champion_strategy,
            execution_metrics=execution_metrics
        )

        assert not is_preserved, "Sharpe exceeding ±10% should fail"
        assert report.behavioral_similarity_score < 0.7
        assert any(check.check_name == 'sharpe_similarity' and not check.passed for check in report.behavioral_checks)

    def test_behavioral_checks_without_positions(self, validator, champion_strategy):
        """Test behavioral checks work without position data."""
        execution_metrics = {
            'sharpe_ratio': 1.52,
            'annual_return': 0.25
        }

        is_preserved, report = validator.validate_preservation(
            generated_code="roe_avg = roe.rolling(window=4).mean().shift(1)\nliquidity_filter = trading_value > 100_000_000",
            champion=champion_strategy,
            execution_metrics=execution_metrics
        )

        # Should only check Sharpe (no position data available)
        assert len(report.behavioral_checks) == 1
        assert report.behavioral_checks[0].check_name == 'sharpe_similarity'


# Test Suite 3: False Positive Detection
class TestFalsePositiveRisk:
    """Test false positive risk calculation."""

    def test_low_risk_both_pass(self, validator, champion_strategy):
        """Test low risk when both parameters and behavior pass."""
        execution_metrics = {
            'sharpe_ratio': 1.52,  # Within ±10%
            'annual_return': 0.25
        }

        is_preserved, report = validator.validate_preservation(
            generated_code="roe_avg = roe.rolling(window=4).mean().shift(1)\nliquidity_filter = trading_value > 100_000_000",
            champion=champion_strategy,
            execution_metrics=execution_metrics
        )

        assert report.false_positive_risk < 0.5, "Risk should be low when both pass"
        assert len(report.false_positive_indicators) == 0

    def test_high_risk_parameter_pass_behavior_fail(self, validator, champion_strategy):
        """Test high risk when parameters pass but behavior fails."""
        execution_metrics = {
            'sharpe_ratio': 0.8,  # -46% from champion (large deviation)
            'annual_return': 0.15
        }

        is_preserved, report = validator.validate_preservation(
            generated_code="roe_avg = roe.rolling(window=4).mean().shift(1)\nliquidity_filter = trading_value > 100_000_000",
            champion=champion_strategy,
            execution_metrics=execution_metrics
        )

        assert report.false_positive_risk >= 0.7, "Risk should be high when behavior deviates"
        assert any('behavioral similarity low' in indicator.lower() for indicator in report.false_positive_indicators)

    def test_risk_without_metrics(self, validator, champion_strategy):
        """Test risk calculation without execution metrics."""
        is_preserved, report = validator.validate_preservation(
            generated_code="roe_avg = roe.rolling(window=4).mean().shift(1)\nliquidity_filter = trading_value > 100_000_000",
            champion=champion_strategy,
            execution_metrics=None
        )

        # Risk based on parameters only
        assert 0.0 <= report.false_positive_risk <= 1.0
        assert report.behavioral_similarity_score == 0.5  # Neutral score


# Test Suite 4: PreservationReport
class TestPreservationReport:
    """Test PreservationReport generation and formatting."""

    def test_report_structure_complete(self, validator, champion_strategy):
        """Test report contains all required fields."""
        execution_metrics = {
            'sharpe_ratio': 1.52,
            'annual_return': 0.25
        }

        is_preserved, report = validator.validate_preservation(
            generated_code="roe_avg = roe.rolling(window=4).mean().shift(1)\nliquidity_filter = trading_value > 100_000_000",
            champion=champion_strategy,
            execution_metrics=execution_metrics
        )

        assert isinstance(report, PreservationReport)
        assert hasattr(report, 'is_preserved')
        assert hasattr(report, 'parameter_checks')
        assert hasattr(report, 'critical_params_preserved')
        assert hasattr(report, 'missing_params')
        assert hasattr(report, 'behavioral_checks')
        assert hasattr(report, 'behavioral_similarity_score')
        assert hasattr(report, 'false_positive_risk')
        assert hasattr(report, 'false_positive_indicators')
        assert hasattr(report, 'recommendations')
        assert hasattr(report, 'requires_manual_review')
        assert hasattr(report, 'timestamp')

    def test_report_summary_format(self, validator, champion_strategy):
        """Test report summary format."""
        is_preserved, report = validator.validate_preservation(
            generated_code="roe_avg = roe.rolling(window=4).mean().shift(1)\nliquidity_filter = trading_value > 100_000_000",
            champion=champion_strategy,
            execution_metrics={'sharpe_ratio': 1.52}
        )

        summary = report.summary()
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert ('✅ PRESERVED' in summary) or ('❌ NOT PRESERVED' in summary)

    def test_recommendations_generated(self, validator, champion_strategy):
        """Test recommendations are generated for violations."""
        code_with_violations = """
        roe_shift = roe.shift(1)  # No smoothing
        # No liquidity filter
        """

        is_preserved, report = validator.validate_preservation(
            generated_code=code_with_violations,
            champion=champion_strategy,
            execution_metrics=None
        )

        assert len(report.recommendations) > 0, "Violations should generate recommendations"
        assert any('missing critical parameters' in rec.lower() for rec in report.recommendations)

    def test_manual_review_flag(self, validator, champion_strategy):
        """Test manual review flag for high-risk cases."""
        execution_metrics = {
            'sharpe_ratio': 0.7,  # Large deviation
            'annual_return': 0.12
        }

        is_preserved, report = validator.validate_preservation(
            generated_code="roe_avg = roe.rolling(window=4).mean().shift(1)\nliquidity_filter = trading_value > 100_000_000",
            champion=champion_strategy,
            execution_metrics=execution_metrics
        )

        if report.false_positive_risk > 0.7 or not is_preserved:
            assert report.requires_manual_review, "High risk cases should require manual review"


# Test Suite 5: Helper Methods
class TestHelperMethods:
    """Test turnover and concentration calculation helpers."""

    def test_calculate_turnover(self, validator):
        """Test portfolio turnover calculation."""
        # Simple position DataFrame
        positions = pd.DataFrame({
            'stock_a': [0.5, 0.4, 0.3],
            'stock_b': [0.3, 0.4, 0.5],
            'stock_c': [0.2, 0.2, 0.2]
        })

        turnover = validator._calculate_turnover(positions)
        assert turnover > 0, "Turnover should be positive"
        assert isinstance(turnover, float)

    def test_calculate_turnover_empty(self, validator):
        """Test turnover calculation with empty DataFrame."""
        positions = pd.DataFrame()
        turnover = validator._calculate_turnover(positions)
        assert turnover == 0.0, "Empty DataFrame should have zero turnover"

    def test_calculate_concentration(self, validator):
        """Test position concentration (Herfindahl index)."""
        # Concentrated portfolio
        concentrated = pd.DataFrame({
            'stock_a': [0.8, 0.85, 0.9],
            'stock_b': [0.15, 0.1, 0.08],
            'stock_c': [0.05, 0.05, 0.02]
        })

        concentration = validator._calculate_concentration(concentrated)
        assert concentration > 0.5, "Concentrated portfolio should have high index"
        assert concentration <= 1.0, "Concentration index should be ≤1.0"

    def test_calculate_concentration_diversified(self, validator):
        """Test concentration for diversified portfolio."""
        # Diversified portfolio
        diversified = pd.DataFrame({
            'stock_a': [0.25, 0.25, 0.25],
            'stock_b': [0.25, 0.25, 0.25],
            'stock_c': [0.25, 0.25, 0.25],
            'stock_d': [0.25, 0.25, 0.25]
        })

        concentration = validator._calculate_concentration(diversified)
        assert concentration < 0.5, "Diversified portfolio should have low index"


# Test Suite 6: Edge Cases
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_extraction_failure(self, validator, champion_strategy):
        """Test handling of parameter extraction with minimal code."""
        # Code with no parameters - should detect missing critical params
        minimal_code = "# minimal code with no parameters"

        is_preserved, report = validator.validate_preservation(
            generated_code=minimal_code,
            champion=champion_strategy,
            execution_metrics=None
        )

        # Should not be preserved - missing all critical parameters
        assert not is_preserved, "Code missing critical parameters should not be preserved"
        assert report.false_positive_risk == 1.0, "Missing all params should have max risk"
        # Check that missing params are detected
        assert len(report.missing_params) > 0, "Should detect missing parameters"
        assert 'roe_smoothing' in report.missing_params or 'liquidity_threshold' in report.missing_params

    def test_champion_without_liquidity(self, validator):
        """Test validation when champion has no liquidity filter."""
        champion = Mock()
        champion.parameters = {
            'roe_type': 'smoothed',
            'roe_smoothing_window': 4,
            'liquidity_threshold': None  # No liquidity filter
        }
        champion.metrics = {'sharpe_ratio': 1.5}

        code = "roe_avg = roe.rolling(window=4).mean().shift(1)"

        is_preserved, report = validator.validate_preservation(
            generated_code=code,
            champion=champion,
            execution_metrics=None
        )

        # Should pass - no liquidity requirement
        assert is_preserved or 'liquidity_threshold' not in report.missing_params

    def test_champion_sharpe_zero(self, validator, champion_strategy):
        """Test behavioral check when champion Sharpe is zero."""
        champion_strategy.metrics['sharpe_ratio'] = 0

        execution_metrics = {'sharpe_ratio': 1.5}

        is_preserved, report = validator.validate_preservation(
            generated_code="roe_avg = roe.rolling(window=4).mean().shift(1)\nliquidity_filter = trading_value > 100_000_000",
            champion=champion_strategy,
            execution_metrics=execution_metrics
        )

        # Should handle gracefully (no division by zero)
        assert isinstance(report, PreservationReport)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
