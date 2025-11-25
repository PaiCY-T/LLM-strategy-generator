"""
TDD Tests for Comprehensive Scorer (Spec B P1).

Tests written FIRST following Red-Green-Refactor cycle.
Multi-objective comprehensive scorer for 40M TWD capital strategies.

Test Coverage:
- Score calculation with weighted components
- Stability metric calculation
- Turnover cost calculation
- Edge cases
"""

import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any


class TestComprehensiveScorer:
    """TDD tests for Comprehensive Scorer - Write FIRST (RED phase)."""

    @pytest.fixture
    def scorer(self):
        """Create ComprehensiveScorer with default weights."""
        from src.validation.comprehensive_scorer import ComprehensiveScorer
        return ComprehensiveScorer(capital=40_000_000)

    @pytest.fixture
    def sample_metrics(self) -> Dict[str, Any]:
        """Sample strategy metrics."""
        return {
            'calmar_ratio': 2.5,
            'sortino_ratio': 3.0,
            'monthly_returns': np.array([0.02, 0.03, -0.01, 0.04, 0.02, 0.01,
                                          0.03, -0.02, 0.05, 0.01, 0.02, 0.03]),
            'annual_turnover': 2.0,  # 200% turnover
            'avg_slippage_bps': 25,  # 25 bps average slippage
        }

    def test_compute_score_returns_dict(self, scorer, sample_metrics):
        """RED: compute_score should return dict with score and components"""
        result = scorer.compute_score(sample_metrics)

        assert isinstance(result, dict)
        assert 'total_score' in result
        assert 'components' in result

    def test_score_includes_all_components(self, scorer, sample_metrics):
        """RED: Score should include all weighted components"""
        result = scorer.compute_score(sample_metrics)
        components = result['components']

        # Check all expected components exist
        assert 'calmar_score' in components
        assert 'sortino_score' in components
        assert 'stability_score' in components
        assert 'turnover_penalty' in components
        assert 'liquidity_penalty' in components

    def test_score_formula_correct(self, scorer, sample_metrics):
        """RED: Score = w1*Calmar + w2*Sortino + w3*Stability - w4*Turnover - w5*Liquidity"""
        result = scorer.compute_score(sample_metrics)

        # Manually verify score calculation
        components = result['components']
        weights = scorer.weights

        expected_score = (
            weights['calmar'] * components['calmar_score'] +
            weights['sortino'] * components['sortino_score'] +
            weights['stability'] * components['stability_score'] -
            weights['turnover_cost'] * components['turnover_penalty'] -
            weights['liquidity_penalty'] * components['liquidity_penalty']
        )

        assert abs(result['total_score'] - expected_score) < 0.001, \
            "Score formula does not match expected calculation"

    def test_default_weights_sum_to_100(self, scorer):
        """RED: Default weights should sum to 100%"""
        weights = scorer.weights
        total = sum(weights.values())

        assert abs(total - 1.0) < 0.001, f"Weights should sum to 1.0, got {total}"

    def test_default_weight_values(self, scorer):
        """RED: Default weights should match spec (40M TWD)"""
        weights = scorer.weights

        assert abs(weights['calmar'] - 0.30) < 0.01, "Calmar weight should be 30%"
        assert abs(weights['sortino'] - 0.25) < 0.01, "Sortino weight should be 25%"
        assert abs(weights['stability'] - 0.20) < 0.01, "Stability weight should be 20%"
        assert abs(weights['turnover_cost'] - 0.15) < 0.01, "Turnover weight should be 15%"
        assert abs(weights['liquidity_penalty'] - 0.10) < 0.01, "Liquidity weight should be 10%"


class TestStabilityCalculation:
    """Tests for stability metric calculation."""

    @pytest.fixture
    def scorer(self):
        from src.validation.comprehensive_scorer import ComprehensiveScorer
        return ComprehensiveScorer()

    def test_stability_high_for_consistent_returns(self, scorer):
        """RED: High stability for consistent positive returns"""
        # Consistent ~2% monthly returns
        consistent_returns = np.array([0.02] * 12)
        stability = scorer.calculate_stability(consistent_returns)

        assert stability > 0.8, "Consistent returns should have high stability"

    def test_stability_low_for_volatile_returns(self, scorer):
        """RED: Low stability for volatile returns"""
        # Very volatile returns
        volatile_returns = np.array([0.10, -0.15, 0.20, -0.10, 0.15, -0.20,
                                      0.05, -0.08, 0.12, -0.05, 0.08, -0.10])
        stability = scorer.calculate_stability(volatile_returns)

        assert stability < 0.5, "Volatile returns should have low stability"

    def test_stability_range_0_to_1(self, scorer):
        """RED: Stability should be in [0, 1]"""
        returns_cases = [
            np.array([0.02] * 12),           # Consistent
            np.array([0.10, -0.10] * 6),     # Alternating
            np.array([0.50, -0.40] * 6),     # Very volatile
            np.array([0.0] * 12),            # Zero returns
        ]

        for returns in returns_cases:
            stability = scorer.calculate_stability(returns)
            assert 0 <= stability <= 1, f"Stability {stability} out of range [0,1]"


class TestTurnoverCostCalculation:
    """Tests for turnover cost calculation."""

    @pytest.fixture
    def scorer(self):
        from src.validation.comprehensive_scorer import ComprehensiveScorer
        return ComprehensiveScorer()

    def test_turnover_cost_increases_with_turnover(self, scorer):
        """RED: Higher turnover should result in higher cost"""
        cost_low = scorer.calculate_turnover_cost(0.5)   # 50% turnover
        cost_med = scorer.calculate_turnover_cost(1.0)   # 100% turnover
        cost_high = scorer.calculate_turnover_cost(2.0)  # 200% turnover

        assert cost_high > cost_med > cost_low

    def test_turnover_cost_formula(self, scorer):
        """RED: Turnover cost = turnover × commission_bps / 100"""
        # With 10 bps commission, 200% turnover = 200 × 0.10% = 0.20%
        cost = scorer.calculate_turnover_cost(2.0, commission_bps=10)

        # Cost should be approximately 0.20% = 0.002
        assert abs(cost - 0.002) < 0.001

    def test_zero_turnover_zero_cost(self, scorer):
        """RED: Zero turnover should have zero cost"""
        cost = scorer.calculate_turnover_cost(0.0)
        assert cost == 0.0


class TestCustomWeights:
    """Tests for custom weight configuration."""

    def test_custom_weights_applied(self):
        """RED: Custom weights should be applied"""
        from src.validation.comprehensive_scorer import ComprehensiveScorer

        custom_weights = {
            'calmar': 0.40,
            'sortino': 0.30,
            'stability': 0.15,
            'turnover_cost': 0.10,
            'liquidity_penalty': 0.05,
        }

        scorer = ComprehensiveScorer(weights=custom_weights)

        assert scorer.weights['calmar'] == 0.40
        assert scorer.weights['sortino'] == 0.30

    def test_custom_capital_stored(self):
        """RED: Custom capital should be stored"""
        from src.validation.comprehensive_scorer import ComprehensiveScorer

        scorer_20m = ComprehensiveScorer(capital=20_000_000)
        scorer_80m = ComprehensiveScorer(capital=80_000_000)

        assert scorer_20m.capital == 20_000_000
        assert scorer_80m.capital == 80_000_000


class TestComprehensiveScorerEdgeCases:
    """Edge case tests."""

    @pytest.fixture
    def scorer(self):
        from src.validation.comprehensive_scorer import ComprehensiveScorer
        return ComprehensiveScorer()

    def test_missing_metrics_handled(self, scorer):
        """RED: Missing metrics should use defaults"""
        partial_metrics = {
            'calmar_ratio': 2.0,
            # Missing other metrics
        }

        # Should not crash
        result = scorer.compute_score(partial_metrics)
        assert 'total_score' in result

    def test_negative_ratios_handled(self, scorer):
        """RED: Negative ratios should be handled"""
        bad_metrics = {
            'calmar_ratio': -1.0,  # Negative Calmar
            'sortino_ratio': -0.5,  # Negative Sortino
            'monthly_returns': np.array([-0.05] * 12),  # All losses
            'annual_turnover': 1.0,
            'avg_slippage_bps': 20,
        }

        result = scorer.compute_score(bad_metrics)

        # Score should be negative but not crash
        assert isinstance(result['total_score'], float)

    def test_zero_turnover(self, scorer):
        """RED: Zero turnover should not cause errors"""
        metrics = {
            'calmar_ratio': 2.0,
            'sortino_ratio': 2.5,
            'monthly_returns': np.array([0.02] * 12),
            'annual_turnover': 0.0,  # No turnover
            'avg_slippage_bps': 10,
        }

        result = scorer.compute_score(metrics)
        assert result['components']['turnover_penalty'] == 0.0

    def test_empty_monthly_returns(self, scorer):
        """RED: Empty returns should default to 0 stability"""
        stability = scorer.calculate_stability(np.array([]))
        assert stability == 0.0


class TestScoreComparison:
    """Tests for comparing strategies using scores."""

    @pytest.fixture
    def scorer(self):
        from src.validation.comprehensive_scorer import ComprehensiveScorer
        return ComprehensiveScorer()

    def test_better_strategy_higher_score(self, scorer):
        """RED: Better strategy should have higher score"""
        good_strategy = {
            'calmar_ratio': 3.0,
            'sortino_ratio': 4.0,
            'monthly_returns': np.array([0.03] * 12),
            'annual_turnover': 1.0,
            'avg_slippage_bps': 15,
        }

        poor_strategy = {
            'calmar_ratio': 0.5,
            'sortino_ratio': 0.8,
            'monthly_returns': np.array([0.01, -0.02] * 6),
            'annual_turnover': 3.0,
            'avg_slippage_bps': 50,
        }

        good_score = scorer.compute_score(good_strategy)['total_score']
        poor_score = scorer.compute_score(poor_strategy)['total_score']

        assert good_score > poor_score, \
            "Better strategy should have higher score"
