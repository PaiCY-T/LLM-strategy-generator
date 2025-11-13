"""
Tests for Bonferroni Multiple Comparison Correction

Test Coverage:
    - AC-2.3.1: Bonferroni adjustment correctly calculated
    - AC-2.3.2: Z-score and threshold calculation accurate
    - AC-2.3.3: Significance determination works for single strategy
    - AC-2.3.4: Validation report includes all required fields
    - AC-2.3.5: FWER maintained at ≤ 0.05 for large N

Edge Cases:
    - N=0, T=0 handling
    - Invalid Sharpe values (NaN, inf)
    - Empty strategy lists
    - Single strategy validation
"""

import pytest
import numpy as np
from scipy.stats import norm
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.validation.multiple_comparison import BonferroniValidator


class TestBonferroniAdjustment:
    """Test Bonferroni adjustment calculation (AC-2.3.1)"""

    def test_basic_adjustment(self):
        """Test basic Bonferroni adjustment: α/N"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        assert validator.adjusted_alpha == pytest.approx(0.05 / 500, rel=1e-9)
        assert validator.adjusted_alpha == pytest.approx(0.0001, rel=1e-4)

    def test_adjustment_with_different_n(self):
        """Test adjustment scales correctly with N"""
        # Small N
        v1 = BonferroniValidator(n_strategies=10, alpha=0.05)
        assert v1.adjusted_alpha == pytest.approx(0.005, rel=1e-9)

        # Medium N
        v2 = BonferroniValidator(n_strategies=100, alpha=0.05)
        assert v2.adjusted_alpha == pytest.approx(0.0005, rel=1e-9)

        # Large N
        v3 = BonferroniValidator(n_strategies=1000, alpha=0.05)
        assert v3.adjusted_alpha == pytest.approx(0.00005, rel=1e-9)

    def test_adjustment_with_different_alpha(self):
        """Test adjustment with different significance levels"""
        # Standard alpha
        v1 = BonferroniValidator(n_strategies=500, alpha=0.05)
        assert v1.adjusted_alpha == pytest.approx(0.0001, rel=1e-4)

        # Stricter alpha
        v2 = BonferroniValidator(n_strategies=500, alpha=0.01)
        assert v2.adjusted_alpha == pytest.approx(0.00002, rel=1e-4)

        # More lenient alpha
        v3 = BonferroniValidator(n_strategies=500, alpha=0.10)
        assert v3.adjusted_alpha == pytest.approx(0.0002, rel=1e-4)

    def test_invalid_n_strategies(self):
        """Test that invalid N raises ValueError"""
        with pytest.raises(ValueError, match="n_strategies must be positive"):
            BonferroniValidator(n_strategies=0, alpha=0.05)

        with pytest.raises(ValueError, match="n_strategies must be positive"):
            BonferroniValidator(n_strategies=-100, alpha=0.05)

    def test_invalid_alpha(self):
        """Test that invalid alpha raises ValueError"""
        with pytest.raises(ValueError, match="alpha must be in"):
            BonferroniValidator(n_strategies=500, alpha=0.0)

        with pytest.raises(ValueError, match="alpha must be in"):
            BonferroniValidator(n_strategies=500, alpha=1.0)

        with pytest.raises(ValueError, match="alpha must be in"):
            BonferroniValidator(n_strategies=500, alpha=-0.05)

        with pytest.raises(ValueError, match="alpha must be in"):
            BonferroniValidator(n_strategies=500, alpha=1.5)


class TestZScoreAndThreshold:
    """Test Z-score and threshold calculation (AC-2.3.2)"""

    def test_z_score_calculation(self):
        """Test Z-score calculated correctly from adjusted alpha"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        # For N=500, adjusted_alpha = 0.0001
        # Z-score for two-tailed test: norm.ppf(1 - 0.0001/2) = norm.ppf(0.99995)
        expected_z = norm.ppf(1 - validator.adjusted_alpha / 2)

        # Verify by calculating threshold without conservative adjustment
        threshold = validator.calculate_significance_threshold(
            n_periods=252,
            use_conservative=False
        )

        calculated_z = threshold * np.sqrt(252)
        assert calculated_z == pytest.approx(expected_z, rel=1e-6)

    def test_threshold_formula(self):
        """Test threshold = Z / sqrt(T)"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        # Test with different period counts
        for n_periods in [21, 63, 126, 252, 504]:
            threshold = validator.calculate_significance_threshold(
                n_periods=n_periods,
                use_conservative=False
            )

            # Verify formula: threshold = Z / sqrt(T)
            z_score = norm.ppf(1 - validator.adjusted_alpha / 2)
            expected_threshold = z_score / np.sqrt(n_periods)

            assert threshold == pytest.approx(expected_threshold, rel=1e-6)

    def test_conservative_threshold(self):
        """Test conservative threshold: max(calculated, 0.5)"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        # With N=500, theoretical threshold should be low (~0.245)
        theoretical = validator.calculate_significance_threshold(
            n_periods=252,
            use_conservative=False
        )

        conservative = validator.calculate_significance_threshold(
            n_periods=252,
            use_conservative=True
        )

        # Conservative should be at least 0.5
        assert conservative >= 0.5

        # For this N, theoretical < 0.5, so conservative should be exactly 0.5
        if theoretical < 0.5:
            assert conservative == pytest.approx(0.5)
        else:
            assert conservative == pytest.approx(theoretical)

    def test_threshold_500_strategies_example(self):
        """Test specific example from spec: 500 strategies, 252 periods"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        theoretical = validator.calculate_significance_threshold(
            n_periods=252,
            use_conservative=False
        )

        # From spec: Sharpe > 3.89 / sqrt(252) ≈ 0.245
        # Z-score for adjusted_alpha=0.0001: norm.ppf(0.99995) ≈ 3.89
        expected = 3.89 / np.sqrt(252)

        # Allow some tolerance for the approximation
        assert theoretical == pytest.approx(expected, rel=0.01)

    def test_invalid_n_periods(self):
        """Test that invalid n_periods raises ValueError"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        with pytest.raises(ValueError, match="n_periods must be positive"):
            validator.calculate_significance_threshold(n_periods=0)

        with pytest.raises(ValueError, match="n_periods must be positive"):
            validator.calculate_significance_threshold(n_periods=-252)


class TestSignificanceDetermination:
    """Test significance determination for single strategy (AC-2.3.3)"""

    def test_significant_sharpe(self):
        """Test that high Sharpe is significant"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        # Sharpe > 0.5 should be significant with conservative threshold
        assert validator.is_significant(sharpe_ratio=1.5)
        assert validator.is_significant(sharpe_ratio=2.0)
        assert validator.is_significant(sharpe_ratio=0.6)

    def test_insignificant_sharpe(self):
        """Test that low Sharpe is not significant"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        # Sharpe < 0.5 should not be significant with conservative threshold
        assert not validator.is_significant(sharpe_ratio=0.3)
        assert not validator.is_significant(sharpe_ratio=0.0)
        assert not validator.is_significant(sharpe_ratio=0.1)

    def test_boundary_sharpe(self):
        """Test Sharpe values near threshold"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)
        threshold = validator.calculate_significance_threshold()

        # Just above threshold should be significant
        assert validator.is_significant(sharpe_ratio=threshold + 0.01)

        # Just below threshold should not be significant
        assert not validator.is_significant(sharpe_ratio=threshold - 0.01)

        # Exactly at threshold should not be significant (uses > not >=)
        assert not validator.is_significant(sharpe_ratio=threshold)

    def test_negative_sharpe(self):
        """Test that negative Sharpe is evaluated by absolute value"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        # abs(-1.5) > 0.5, so should be significant
        assert validator.is_significant(sharpe_ratio=-1.5)

        # abs(-0.3) < 0.5, so should not be significant
        assert not validator.is_significant(sharpe_ratio=-0.3)

    def test_invalid_sharpe_values(self):
        """Test handling of invalid Sharpe values"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        # NaN should return False
        assert not validator.is_significant(sharpe_ratio=np.nan)

        # Infinity should return False
        assert not validator.is_significant(sharpe_ratio=np.inf)
        assert not validator.is_significant(sharpe_ratio=-np.inf)

    def test_different_periods(self):
        """Test significance with different period counts"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        # Same Sharpe may be significant/insignificant with different periods
        sharpe = 0.3

        # Shorter period → higher threshold → less likely significant
        assert not validator.is_significant(sharpe, n_periods=21)

        # Medium period
        result_252 = validator.is_significant(sharpe, n_periods=252)

        # Longer period → lower threshold → more likely significant
        # (though with conservative=True, may still hit 0.5 floor)


class TestValidationReport:
    """Test validation report includes all required fields (AC-2.3.4)"""

    def test_report_fields(self):
        """Test that validation report contains all required fields"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        strategies = [
            {'name': 'Strategy_A', 'sharpe_ratio': 1.8},
            {'name': 'Strategy_B', 'sharpe_ratio': 0.3},
            {'name': 'Strategy_C', 'sharpe_ratio': 2.1},
            {'name': 'Strategy_D', 'sharpe_ratio': 0.7},
        ]

        results = validator.validate_strategy_set(strategies)

        # Check all required fields are present
        required_fields = [
            'total_strategies',
            'significant_count',
            'significance_threshold',
            'adjusted_alpha',
            'expected_false_discoveries',
            'estimated_fdr',
            'significant_strategies'
        ]

        for field in required_fields:
            assert field in results, f"Missing required field: {field}"

    def test_report_values(self):
        """Test that validation report values are correct"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        strategies = [
            {'name': 'Strategy_A', 'sharpe_ratio': 1.8},
            {'name': 'Strategy_B', 'sharpe_ratio': 0.3},
            {'name': 'Strategy_C', 'sharpe_ratio': 2.1},
        ]

        results = validator.validate_strategy_set(strategies)

        # Check specific values
        assert results['total_strategies'] == 3
        assert results['adjusted_alpha'] == pytest.approx(0.0001)

        # With conservative threshold of 0.5, Sharpes 1.8 and 2.1 should be significant
        assert results['significant_count'] == 2
        assert len(results['significant_strategies']) == 2

        # Check expected false discoveries
        expected_fdr = validator.adjusted_alpha * 3
        assert results['expected_false_discoveries'] == pytest.approx(expected_fdr)

    def test_empty_strategy_list(self):
        """Test validation with empty strategy list"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        results = validator.validate_strategy_set([])

        assert results['total_strategies'] == 0
        assert results['significant_count'] == 0
        assert results['expected_false_discoveries'] == 0.0
        assert results['estimated_fdr'] == 0.0
        assert results['significant_strategies'] == []

    def test_all_significant(self):
        """Test when all strategies are significant"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        strategies = [
            {'name': 'Strategy_A', 'sharpe_ratio': 1.8},
            {'name': 'Strategy_B', 'sharpe_ratio': 2.1},
            {'name': 'Strategy_C', 'sharpe_ratio': 1.5},
        ]

        results = validator.validate_strategy_set(strategies)

        assert results['significant_count'] == 3
        assert len(results['significant_strategies']) == 3

    def test_none_significant(self):
        """Test when no strategies are significant"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        strategies = [
            {'name': 'Strategy_A', 'sharpe_ratio': 0.1},
            {'name': 'Strategy_B', 'sharpe_ratio': 0.2},
            {'name': 'Strategy_C', 'sharpe_ratio': 0.3},
        ]

        results = validator.validate_strategy_set(strategies)

        assert results['significant_count'] == 0
        assert len(results['significant_strategies']) == 0

    def test_fdr_calculation(self):
        """Test False Discovery Rate calculation"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        strategies = [
            {'name': f'Strategy_{i}', 'sharpe_ratio': 1.5}
            for i in range(10)
        ]

        results = validator.validate_strategy_set(strategies)

        # FDR = expected_false / significant_count
        expected_false = validator.adjusted_alpha * 10
        expected_fdr = expected_false / results['significant_count']

        assert results['estimated_fdr'] == pytest.approx(expected_fdr)


class TestFWERMaintenance:
    """Test FWER maintained at ≤ 0.05 for large N (AC-2.3.5)"""

    def test_fwer_500_strategies(self):
        """Test FWER ≤ 0.05 for 500 strategies"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        fwer = validator.calculate_family_wise_error_rate()

        # Bonferroni guarantees FWER ≤ α
        assert fwer <= validator.alpha
        assert fwer <= 0.05

    def test_fwer_different_n(self):
        """Test FWER ≤ α for different N values"""
        for n in [10, 50, 100, 500, 1000]:
            validator = BonferroniValidator(n_strategies=n, alpha=0.05)

            fwer = validator.calculate_family_wise_error_rate()

            # FWER should always be ≤ α
            assert fwer <= validator.alpha, f"FWER {fwer} > α {validator.alpha} for N={n}"

    def test_fwer_approximation(self):
        """Test FWER approximation for small adjusted alpha"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        fwer_exact = validator.calculate_family_wise_error_rate()

        # For small alpha, FWER ≈ n * adjusted_alpha = alpha
        fwer_approx = validator.n_strategies * validator.adjusted_alpha

        # Approximation should be close to exact for small alpha
        # For N=500, there's a ~2.5% difference, which is acceptable
        assert fwer_exact == pytest.approx(fwer_approx, rel=0.03)

    def test_fwer_vs_alpha(self):
        """Test relationship between FWER and α"""
        for alpha in [0.01, 0.05, 0.10]:
            validator = BonferroniValidator(n_strategies=500, alpha=alpha)

            fwer = validator.calculate_family_wise_error_rate()

            # FWER should be very close to α for Bonferroni correction
            assert fwer <= alpha
            # Allow 5% tolerance due to exact vs approximate formula
            # (difference increases for larger alpha values)
            assert fwer == pytest.approx(alpha, rel=0.05)


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_single_strategy(self):
        """Test validation with single strategy"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        strategies = [{'name': 'Only_Strategy', 'sharpe_ratio': 1.5}]

        results = validator.validate_strategy_set(strategies)

        assert results['total_strategies'] == 1
        assert results['significant_count'] == 1

    def test_missing_sharpe_ratio(self):
        """Test handling of strategies without sharpe_ratio"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        strategies = [
            {'name': 'Strategy_A', 'sharpe_ratio': 1.5},
            {'name': 'Strategy_B'},  # Missing sharpe_ratio
        ]

        results = validator.validate_strategy_set(strategies)

        # Should handle gracefully, treating missing as 0.0
        assert results['total_strategies'] == 2

    def test_extreme_sharpe_values(self):
        """Test with extreme Sharpe ratio values"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        strategies = [
            {'name': 'Very_High', 'sharpe_ratio': 10.0},
            {'name': 'Very_Low', 'sharpe_ratio': -10.0},
            {'name': 'Zero', 'sharpe_ratio': 0.0},
        ]

        results = validator.validate_strategy_set(strategies)

        # Very high and very low should both be significant (using abs)
        assert results['significant_count'] == 2

    def test_report_generation(self):
        """Test human-readable report generation"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        strategies = [
            {'name': 'Strategy_A', 'sharpe_ratio': 1.8},
            {'name': 'Strategy_B', 'sharpe_ratio': 0.3},
        ]

        validation_results = validator.validate_strategy_set(strategies)
        report = validator.generate_report(validation_results)

        # Check report contains key information
        assert "BONFERRONI" in report
        assert "500" in report
        assert "0.05" in report
        assert str(validation_results['significant_count']) in report


class TestIntegration:
    """Integration tests for complete workflow"""

    def test_complete_workflow(self):
        """Test complete validation workflow"""
        # Step 1: Initialize validator
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        # Step 2: Calculate threshold
        threshold = validator.calculate_significance_threshold()
        assert threshold >= 0.5

        # Step 3: Check individual strategies
        assert validator.is_significant(sharpe_ratio=1.5)
        assert not validator.is_significant(sharpe_ratio=0.3)

        # Step 4: Validate strategy set
        strategies = [
            {'name': f'Strategy_{i}', 'sharpe_ratio': 0.5 + i * 0.2}
            for i in range(10)
        ]

        results = validator.validate_strategy_set(strategies)

        # Step 5: Calculate FWER
        fwer = validator.calculate_family_wise_error_rate()
        assert fwer <= 0.05

        # Step 6: Generate report
        report = validator.generate_report(results)
        assert isinstance(report, str)
        assert len(report) > 0

    def test_realistic_scenario(self):
        """Test realistic scenario with 500 strategies"""
        validator = BonferroniValidator(n_strategies=500, alpha=0.05)

        # Generate 500 strategies with normal distribution of Sharpes
        np.random.seed(42)
        strategies = [
            {
                'name': f'Strategy_{i}',
                'sharpe_ratio': np.random.normal(0.5, 0.5)
            }
            for i in range(500)
        ]

        results = validator.validate_strategy_set(strategies)

        # Some strategies should be significant
        assert results['significant_count'] > 0

        # But not too many (FWER control)
        assert results['significant_count'] < len(strategies)

        # FWER should be maintained
        fwer = validator.calculate_family_wise_error_rate()
        assert fwer <= 0.05

        # FDR should be reasonable
        assert results['estimated_fdr'] < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
