"""
TDD Tests for Spec B P0: Metrics Contract Bug Fix

This test module follows TDD methodology (RED → GREEN → REFACTOR) to verify
that MomentumTemplate._extract_metrics() returns all required fields for
proper strategy classification.

Bug Description:
    MomentumTemplate._extract_metrics() is missing required fields:
    - execution_success: Must be True when backtest succeeds
    - total_return: Required by StrategyMetrics.from_dict()

    This causes strategies to be incorrectly classified as LEVEL_0 by
    SuccessClassifier, breaking the learning loop.

Test Coverage:
    1. Metrics contract validation (required fields presence)
    2. Strategy classification behavior (not all LEVEL_0)
    3. Field types and value ranges
    4. Integration with StrategyMetrics and SuccessClassifier

Fixtures Used:
    - mock_data_cache: Mocked DataCache with synthetic data
    - mock_finlab_sim: Mocked backtest with predictable metrics
"""

import pytest
from src.templates.momentum_template import MomentumTemplate
from src.backtest.metrics import StrategyMetrics
from src.backtest.classifier import SuccessClassifier


class TestMomentumTemplateMetricsContract:
    """Test suite for Spec B P0: Metrics Contract Bug Fix."""

    def test_metrics_contract_execution_success_field(self, mock_data_cache, mock_finlab_sim):
        """
        TDD Test 1: Verify execution_success field is present and True.

        Requirement 1: WHEN _extract_metrics() is called THEN system SHALL
                      return dictionary containing 'execution_success': True

        This test will FAIL initially (RED phase) because current implementation
        does not include execution_success field.
        """
        template = MomentumTemplate()
        params = template.get_default_params()

        # Generate strategy to get metrics
        report, metrics = template.generate_strategy(params)

        # CRITICAL: execution_success must be present
        assert 'execution_success' in metrics, \
            "Missing 'execution_success' field in metrics dictionary"

        # CRITICAL: execution_success must be True for successful backtest
        assert metrics['execution_success'] is True, \
            "execution_success should be True for successful backtest"

    def test_metrics_contract_total_return_field(self, mock_data_cache, mock_finlab_sim):
        """
        TDD Test 2: Verify total_return field is present.

        Requirement 2: WHEN _extract_metrics() is called THEN system SHALL
                      return dictionary containing 'total_return' field

        This test will FAIL initially (RED phase) because current implementation
        does not include total_return field (StrategyMetrics compatibility).
        """
        template = MomentumTemplate()
        params = template.get_default_params()

        # Generate strategy to get metrics
        report, metrics = template.generate_strategy(params)

        # CRITICAL: total_return must be present
        assert 'total_return' in metrics, \
            "Missing 'total_return' field in metrics dictionary"

        # total_return should be a numeric value
        assert isinstance(metrics['total_return'], (int, float)), \
            "total_return should be numeric type"

    def test_metrics_contract_all_required_fields(self, mock_data_cache, mock_finlab_sim):
        """
        TDD Test 3: Verify all 7 required metrics fields are present.

        Requirement 4: IF backtest succeeds THEN system SHALL return complete
                      metrics dict with: execution_success, annual_return,
                      total_return, sharpe_ratio, max_drawdown, sortino_ratio,
                      calmar_ratio

        This test verifies the complete metrics contract.
        """
        template = MomentumTemplate()
        params = template.get_default_params()

        # Generate strategy to get metrics
        report, metrics = template.generate_strategy(params)

        # Define all required fields from requirements.md Line 29
        required_fields = {
            'execution_success',
            'annual_return',
            'total_return',
            'sharpe_ratio',
            'max_drawdown',
            'sortino_ratio',
            'calmar_ratio'
        }

        # Verify all required fields are present
        missing_fields = required_fields - set(metrics.keys())
        assert len(missing_fields) == 0, \
            f"Missing required fields in metrics: {missing_fields}"

        # Verify field types
        assert isinstance(metrics['execution_success'], bool), \
            "execution_success should be boolean"
        assert isinstance(metrics['annual_return'], (int, float)), \
            "annual_return should be numeric"
        assert isinstance(metrics['total_return'], (int, float)), \
            "total_return should be numeric"
        assert isinstance(metrics['sharpe_ratio'], (int, float)), \
            "sharpe_ratio should be numeric"
        assert isinstance(metrics['max_drawdown'], (int, float)), \
            "max_drawdown should be numeric"

    def test_strategy_classification_not_all_level_0(self, mock_data_cache, mock_finlab_sim):
        """
        TDD Test 4: Verify strategies are not all classified as LEVEL_0.

        Requirement 3: WHEN metrics returned after StrategyMetrics.classify()
                      THEN system SHALL correctly classify strategies (not all
                      as LEVEL_0)

        This test verifies the bug fix resolves the classification issue.
        At least one strategy should achieve LEVEL_2 or LEVEL_3 classification
        (not LEVEL_0/LEVEL_1).
        """
        template = MomentumTemplate()
        classifier = SuccessClassifier()

        # Generate multiple strategies with different parameters
        test_cases = [
            template.get_default_params(),
            {**template.get_default_params(), 'momentum_period': 20},
            {**template.get_default_params(), 'n_stocks': 15}
        ]

        classification_levels = []

        for params in test_cases:
            try:
                report, metrics_dict = template.generate_strategy(params)

                # Create StrategyMetrics object for classification
                strategy_metrics = StrategyMetrics(
                    sharpe_ratio=metrics_dict.get('sharpe_ratio'),
                    total_return=metrics_dict.get('total_return'),
                    max_drawdown=metrics_dict.get('max_drawdown'),
                    execution_success=metrics_dict.get('execution_success', False)
                )

                # Classify the strategy
                result = classifier.classify_single(strategy_metrics)
                classification_levels.append(result.level)

            except Exception as e:
                pytest.fail(f"Strategy generation failed: {e}")

        # CRITICAL: At least one strategy should NOT be LEVEL_0
        # With mock_finlab_sim returning good metrics (sharpe=2.0, return=0.25),
        # all strategies should be LEVEL_2 or LEVEL_3
        assert any(level >= 2 for level in classification_levels), \
            f"All strategies classified as LEVEL_0/LEVEL_1: {classification_levels}. " \
            f"This indicates missing execution_success or metrics fields."

        # With good mocked metrics, expect mostly LEVEL_2 or LEVEL_3
        level_2_or_3_count = sum(1 for level in classification_levels if level >= 2)
        assert level_2_or_3_count > 0, \
            "No strategies achieved LEVEL_2 or LEVEL_3 classification"

    def test_metrics_values_reasonable_ranges(self, mock_data_cache, mock_finlab_sim):
        """
        TDD Test 5: Verify metrics values are in reasonable ranges.

        Additional validation to ensure metrics extraction produces sensible values.
        """
        template = MomentumTemplate()
        params = template.get_default_params()

        # Generate strategy to get metrics
        report, metrics = template.generate_strategy(params)

        # Sharpe ratio: typically -5 to 5 for real strategies
        assert -5 <= metrics['sharpe_ratio'] <= 10, \
            f"sharpe_ratio {metrics['sharpe_ratio']} outside reasonable range"

        # Annual return: typically -100% to 500%
        assert -1.0 <= metrics['annual_return'] <= 5.0, \
            f"annual_return {metrics['annual_return']} outside reasonable range"

        # Total return should match annual return (for momentum template)
        assert metrics['total_return'] == metrics['annual_return'], \
            "total_return should equal annual_return"

        # Max drawdown: should be negative or zero
        assert metrics['max_drawdown'] <= 0, \
            f"max_drawdown {metrics['max_drawdown']} should be negative or zero"

        # Max drawdown: typically -100% to 0%
        assert -1.0 <= metrics['max_drawdown'] <= 0, \
            f"max_drawdown {metrics['max_drawdown']} outside reasonable range"

    def test_extract_metrics_directly_with_mock_report(self, mock_finlab_sim):
        """
        TDD Test 6: Test _extract_metrics() method directly with mock report.

        This unit test isolates _extract_metrics() to verify it extracts
        all required fields from the report object.
        """
        template = MomentumTemplate()

        # Use the mock report from fixture
        # mock_finlab_sim fixture creates a report with:
        # - sharpe_ratio() returns 2.0
        # - annual_return() returns 0.25
        # - max_drawdown() returns -0.15
        from unittest.mock import Mock

        mock_report = Mock()
        mock_report.metrics.sharpe_ratio = Mock(return_value=2.0)
        mock_report.metrics.annual_return = Mock(return_value=0.25)
        mock_report.metrics.max_drawdown = Mock(return_value=-0.15)
        mock_report.metrics.sortino_ratio = Mock(return_value=2.5)
        mock_report.metrics.calmar_ratio = Mock(return_value=1.5)

        # Call _extract_metrics() directly
        metrics = template._extract_metrics(mock_report)

        # Verify all required fields are extracted
        assert metrics['execution_success'] is True, \
            "execution_success should be True"
        assert metrics['annual_return'] == 0.25, \
            "annual_return should match report value"
        assert metrics['total_return'] == 0.25, \
            "total_return should match annual_return"
        assert metrics['sharpe_ratio'] == 2.0, \
            "sharpe_ratio should match report value"
        assert metrics['max_drawdown'] == -0.15, \
            "max_drawdown should match report value"

        # Verify the metrics can be used with StrategyMetrics
        strategy_metrics = StrategyMetrics(**{
            k: v for k, v in metrics.items()
            if k in {'sharpe_ratio', 'total_return', 'max_drawdown', 'execution_success'}
        })
        assert strategy_metrics.execution_success is True
        assert strategy_metrics.total_return == 0.25
