"""
Test Risk Assessor - Unit tests for risk assessment logic.

Tests:
- Strategy complexity calculation
- Market risk assessment
- Mutation risk assessment
- Overall risk aggregation
- Edge cases (empty strategy, extreme volatility)

Architecture: Phase 2.0+ Factor Graph System
Task: D.4 - Adaptive Mutation Tier Selection
"""

import pytest
import pandas as pd
import numpy as np
import networkx as nx
from unittest.mock import Mock, MagicMock

from src.mutation.tier_selection.risk_assessor import RiskAssessor, RiskMetrics


class TestRiskAssessorInitialization:
    """Test risk assessor initialization."""

    def test_default_initialization(self):
        """Test default initialization with standard weights."""
        assessor = RiskAssessor()
        assert assessor.strategy_complexity_weight == 0.4
        assert assessor.market_risk_weight == 0.3
        assert assessor.mutation_risk_weight == 0.3

    def test_custom_weights(self):
        """Test initialization with custom weights."""
        assessor = RiskAssessor(
            strategy_complexity_weight=0.5,
            market_risk_weight=0.3,
            mutation_risk_weight=0.2
        )
        assert assessor.strategy_complexity_weight == 0.5
        assert assessor.market_risk_weight == 0.3
        assert assessor.mutation_risk_weight == 0.2

    def test_invalid_weights_sum(self):
        """Test that weights must sum to 1.0."""
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            RiskAssessor(
                strategy_complexity_weight=0.5,
                market_risk_weight=0.3,
                mutation_risk_weight=0.3  # Sum = 1.1
            )


class TestStrategyRiskAssessment:
    """Test strategy complexity risk assessment."""

    def test_simple_linear_strategy_low_risk(self):
        """Test simple linear strategy has low risk."""
        # Create simple strategy mock
        strategy = Mock()
        strategy.dag = nx.DiGraph()
        strategy.dag.add_edge("factor1", "factor2")
        strategy.factors = {"factor1": Mock(), "factor2": Mock()}

        # Mock factor logic
        for factor in strategy.factors.values():
            factor.logic = lambda data, params: data

        assessor = RiskAssessor()
        risk = assessor.assess_strategy_risk(strategy)

        assert 0.0 <= risk <= 0.4  # Simple strategy should be low risk

    def test_complex_strategy_higher_risk(self):
        """Test complex strategy with many factors has higher risk."""
        strategy = Mock()
        strategy.dag = nx.DiGraph()

        # Create complex DAG (10 factors, depth 5)
        for i in range(10):
            strategy.dag.add_node(f"factor{i}")
            if i > 0:
                strategy.dag.add_edge(f"factor{i-1}", f"factor{i}")

        strategy.factors = {f"factor{i}": Mock() for i in range(10)}

        # Mock complex logic
        for factor in strategy.factors.values():
            factor.logic = lambda data, params: data  # Simple function

        assessor = RiskAssessor()
        risk = assessor.assess_strategy_risk(strategy)

        assert 0.3 <= risk <= 1.0  # Complex strategy should have higher risk

    def test_invalid_strategy_returns_high_risk(self):
        """Test invalid strategy returns maximum risk."""
        strategy = Mock(spec=[])  # No dag or factors attributes
        assessor = RiskAssessor()
        risk = assessor.assess_strategy_risk(strategy)
        assert risk == 1.0

    def test_empty_strategy_low_risk(self):
        """Test empty strategy has low risk."""
        strategy = Mock()
        strategy.dag = nx.DiGraph()
        strategy.factors = {}

        assessor = RiskAssessor()
        risk = assessor.assess_strategy_risk(strategy)
        assert 0.0 <= risk <= 0.2


class TestMarketRiskAssessment:
    """Test market condition risk assessment."""

    def test_stable_market_low_risk(self):
        """Test stable market (low volatility) has low risk."""
        # Create stable price data
        stable_data = pd.DataFrame({
            'close': [100, 101, 100, 102, 101, 100, 101]
        })

        assessor = RiskAssessor()
        risk = assessor.assess_market_risk(stable_data)

        assert 0.0 <= risk <= 0.4  # Stable market should be low risk

    def test_volatile_market_high_risk(self):
        """Test volatile market has high risk."""
        # Create volatile price data
        volatile_data = pd.DataFrame({
            'close': [100, 110, 95, 115, 90, 120, 85]
        })

        assessor = RiskAssessor()
        risk = assessor.assess_market_risk(volatile_data)

        assert 0.5 <= risk <= 1.0  # Volatile market should be high risk

    def test_empty_dataframe_moderate_risk(self):
        """Test empty DataFrame returns moderate risk."""
        empty_data = pd.DataFrame()
        assessor = RiskAssessor()
        risk = assessor.assess_market_risk(empty_data)
        assert risk == 0.5  # Default moderate risk

    def test_none_data_moderate_risk(self):
        """Test None data returns moderate risk."""
        assessor = RiskAssessor()
        risk = assessor.assess_market_risk(None)
        assert risk == 0.5

    def test_missing_close_column(self):
        """Test data without 'close' column returns moderate risk."""
        data = pd.DataFrame({'open': [100, 101, 102]})
        assessor = RiskAssessor()
        risk = assessor.assess_market_risk(data)
        assert risk == 0.5

    def test_trending_market(self):
        """Test trending market (stable trend) has low risk."""
        # Create trending data (smooth, low volatility)
        trending_data = pd.DataFrame({
            'close': [100, 102, 104, 106, 108, 110]
        })

        assessor = RiskAssessor()
        risk = assessor.assess_market_risk(trending_data)

        # Smooth trending is low risk (low volatility, no drawdown)
        assert 0.0 <= risk <= 0.3  # Trending should be low-moderate


class TestMutationRiskAssessment:
    """Test mutation-specific risk assessment."""

    def test_high_success_rate_low_risk(self):
        """Test high historical success rate gives low risk."""
        historical_stats = {
            'tier1': {'attempts': 100, 'successes': 80},  # 80% success
            'tier2': {'attempts': 100, 'successes': 70},  # 70% success
            'tier3': {'attempts': 100, 'successes': 60}   # 60% success
        }

        assessor = RiskAssessor()
        risk = assessor.assess_mutation_risk('add_factor', historical_stats)

        assert 0.0 <= risk <= 0.4  # High success = low risk

    def test_low_success_rate_high_risk(self):
        """Test low historical success rate gives high risk."""
        historical_stats = {
            'tier1': {'attempts': 100, 'successes': 20},  # 20% success
            'tier2': {'attempts': 100, 'successes': 30},  # 30% success
            'tier3': {'attempts': 100, 'successes': 15}   # 15% success
        }

        assessor = RiskAssessor()
        risk = assessor.assess_mutation_risk('add_factor', historical_stats)

        assert 0.6 <= risk <= 1.0  # Low success = high risk

    def test_no_history_moderate_risk(self):
        """Test no history returns moderate risk."""
        assessor = RiskAssessor()
        risk = assessor.assess_mutation_risk('add_factor', {})
        assert risk == 0.5

    def test_zero_attempts_moderate_risk(self):
        """Test tier with zero attempts returns moderate risk."""
        historical_stats = {
            'tier1': {'attempts': 0, 'successes': 0},
            'tier2': {'attempts': 0, 'successes': 0},
            'tier3': {'attempts': 0, 'successes': 0}
        }

        assessor = RiskAssessor()
        risk = assessor.assess_mutation_risk('add_factor', historical_stats)
        assert risk == 0.5


class TestOverallRiskAssessment:
    """Test comprehensive risk assessment."""

    def test_overall_risk_combines_components(self):
        """Test overall risk combines all components with weights."""
        # Create test data
        strategy = Mock()
        strategy.dag = nx.DiGraph()
        strategy.dag.add_edge("f1", "f2")
        strategy.factors = {"f1": Mock(), "f2": Mock()}
        for f in strategy.factors.values():
            f.logic = lambda data, params: data

        market_data = pd.DataFrame({'close': [100, 101, 100, 102]})

        historical_stats = {
            'tier1': {'attempts': 50, 'successes': 40},
            'tier2': {'attempts': 50, 'successes': 30},
            'tier3': {'attempts': 50, 'successes': 25}
        }

        assessor = RiskAssessor()
        metrics = assessor.assess_overall_risk(
            strategy=strategy,
            market_data=market_data,
            mutation_type='add_factor',
            historical_stats=historical_stats
        )

        # Check all components calculated
        assert isinstance(metrics, RiskMetrics)
        assert 0.0 <= metrics.strategy_risk <= 1.0
        assert 0.0 <= metrics.market_risk <= 1.0
        assert 0.0 <= metrics.mutation_risk <= 1.0
        assert 0.0 <= metrics.overall_risk <= 1.0

        # Check overall is weighted average
        expected = (
            metrics.strategy_risk * 0.4 +
            metrics.market_risk * 0.3 +
            metrics.mutation_risk * 0.3
        )
        assert abs(metrics.overall_risk - expected) < 0.01

    def test_overall_risk_with_defaults(self):
        """Test overall risk with missing optional parameters."""
        strategy = Mock()
        strategy.dag = nx.DiGraph()
        strategy.factors = {}

        assessor = RiskAssessor()
        metrics = assessor.assess_overall_risk(strategy=strategy)

        # Should use defaults for missing components
        assert metrics.market_risk == 0.5
        assert metrics.mutation_risk == 0.5
        assert 0.0 <= metrics.overall_risk <= 1.0

    def test_risk_metrics_contains_details(self):
        """Test risk metrics includes detailed information."""
        strategy = Mock()
        strategy.dag = nx.DiGraph()
        strategy.factors = {"f1": Mock()}

        assessor = RiskAssessor()
        metrics = assessor.assess_overall_risk(strategy=strategy)

        assert 'details' in metrics.__dict__
        assert isinstance(metrics.details, dict)
        assert 'strategy_complexity' in metrics.details


class TestPrivateHelpers:
    """Test private helper methods."""

    def test_calculate_dag_depth_empty(self):
        """Test DAG depth calculation for empty graph."""
        assessor = RiskAssessor()
        dag = nx.DiGraph()
        depth = assessor._calculate_dag_depth(dag)
        assert depth == 0

    def test_calculate_dag_depth_linear(self):
        """Test DAG depth for linear graph."""
        assessor = RiskAssessor()
        dag = nx.DiGraph()
        dag.add_edge("a", "b")
        dag.add_edge("b", "c")
        dag.add_edge("c", "d")
        depth = assessor._calculate_dag_depth(dag)
        assert depth == 3  # Longest path length

    def test_calculate_code_complexity_no_factors(self):
        """Test code complexity for strategy without factors."""
        assessor = RiskAssessor()
        strategy = Mock(spec=[])
        complexity = assessor._calculate_code_complexity(strategy)
        assert complexity == 0

    def test_calculate_regime_instability(self):
        """Test regime instability calculation."""
        assessor = RiskAssessor()

        # Stable prices (smooth uptrend)
        stable = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110])
        instability = assessor._calculate_regime_instability(stable)
        assert instability <= 3  # Few regime changes

        # Volatile prices (oscillating - need enough data for detection)
        volatile = pd.Series([100, 110, 95, 120, 85, 130, 80, 125, 90, 135, 75, 140])
        instability = assessor._calculate_regime_instability(volatile)
        assert instability >= 1  # Some regime changes detected

    def test_calculate_drawdown_risk(self):
        """Test drawdown risk calculation."""
        assessor = RiskAssessor()

        # No drawdown
        no_dd = pd.Series([100, 101, 102, 103])
        risk = assessor._calculate_drawdown_risk(no_dd)
        assert risk == 0.0

        # Large drawdown
        large_dd = pd.Series([100, 110, 90, 85])  # ~23% drawdown
        risk = assessor._calculate_drawdown_risk(large_dd)
        assert risk > 0.5


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_nan_in_market_data(self):
        """Test handling of NaN values in market data."""
        data = pd.DataFrame({
            'close': [100, np.nan, 102, np.nan, 104]
        })

        assessor = RiskAssessor()
        risk = assessor.assess_market_risk(data)

        # Should handle NaN gracefully
        assert 0.0 <= risk <= 1.0

    def test_single_price_point(self):
        """Test handling of single price point."""
        data = pd.DataFrame({'close': [100]})

        assessor = RiskAssessor()
        risk = assessor.assess_market_risk(data)

        assert 0.0 <= risk <= 1.0

    def test_negative_prices(self):
        """Test handling of negative prices (invalid data)."""
        data = pd.DataFrame({'close': [-100, -95, -90]})

        assessor = RiskAssessor()
        risk = assessor.assess_market_risk(data)

        # Should still calculate risk
        assert 0.0 <= risk <= 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
