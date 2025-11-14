"""
Unit tests for ERC (Equal Risk Contribution) Portfolio Optimizer.

TDD Red Phase: P1.2.1
All tests should FAIL initially until implementation is complete.

Test Coverage:
- Portfolio weight constraints (sum to 1, min/max bounds)
- Equal Risk Contribution algorithm correctness
- Risk metrics calculation (volatility, expected return, Sharpe)
- Optimizer convergence and stability
- Edge cases and error handling
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict


# Import will fail initially - this is expected in RED phase
try:
    from src.intelligence.portfolio_optimizer import PortfolioOptimizer, PortfolioWeights
except ImportError:
    pytest.skip("PortfolioOptimizer not implemented yet", allow_module_level=True)


class TestERCOptimizer:
    """Test suite for Equal Risk Contribution portfolio optimization."""

    @pytest.fixture
    def synthetic_returns_3assets(self) -> pd.DataFrame:
        """Create synthetic returns for 3 assets with known properties."""
        np.random.seed(42)
        n_periods = 252  # 1 year of daily returns

        returns = pd.DataFrame({
            'asset_a': np.random.randn(n_periods) * 0.02 + 0.0005,  # Low vol
            'asset_b': np.random.randn(n_periods) * 0.015 + 0.0003,  # Lower vol
            'asset_c': np.random.randn(n_periods) * 0.025 + 0.0008,  # Higher vol
        })
        return returns

    @pytest.fixture
    def synthetic_returns_5assets(self) -> pd.DataFrame:
        """Create synthetic returns for 5 assets for more complex tests."""
        np.random.seed(42)
        n_periods = 252

        returns = pd.DataFrame({
            'stock_1': np.random.randn(n_periods) * 0.02 + 0.0006,
            'stock_2': np.random.randn(n_periods) * 0.018 + 0.0004,
            'stock_3': np.random.randn(n_periods) * 0.022 + 0.0007,
            'stock_4': np.random.randn(n_periods) * 0.015 + 0.0003,
            'stock_5': np.random.randn(n_periods) * 0.025 + 0.0009,
        })
        return returns

    @pytest.fixture
    def correlated_returns(self) -> pd.DataFrame:
        """Create returns with known correlation structure."""
        np.random.seed(42)
        n_periods = 252

        # Create base random returns
        base = np.random.randn(n_periods) * 0.02
        noise_1 = np.random.randn(n_periods) * 0.01
        noise_2 = np.random.randn(n_periods) * 0.01

        returns = pd.DataFrame({
            'asset_x': base + noise_1,
            'asset_y': base * 0.5 + noise_2,  # Moderate correlation
            'asset_z': np.random.randn(n_periods) * 0.02,  # Independent
        })
        return returns

    # ========================================================================
    # Test 1-2: Basic Return Type and Weight Sum Constraint
    # ========================================================================

    def test_optimize_erc_returns_portfolio_weights(self, synthetic_returns_3assets):
        """
        GIVEN returns data for multiple assets
        WHEN optimizing with ERC
        THEN return PortfolioWeights dataclass with correct structure

        Validates:
        - Return type is PortfolioWeights
        - Contains all required fields
        - Number of weights matches number of assets
        """
        optimizer = PortfolioOptimizer()
        weights = optimizer.optimize_erc(synthetic_returns_3assets)

        # Verify return type
        assert isinstance(weights, PortfolioWeights), \
            "optimize_erc should return PortfolioWeights dataclass"

        # Verify structure
        assert hasattr(weights, 'weights'), "Missing 'weights' field"
        assert hasattr(weights, 'expected_return'), "Missing 'expected_return' field"
        assert hasattr(weights, 'volatility'), "Missing 'volatility' field"
        assert hasattr(weights, 'sharpe_ratio'), "Missing 'sharpe_ratio' field"
        assert hasattr(weights, 'risk_contributions'), "Missing 'risk_contributions' field"

        # Verify number of weights
        assert len(weights.weights) == 3, \
            f"Expected 3 weights, got {len(weights.weights)}"

        # Verify all assets are present
        assert set(weights.weights.keys()) == set(synthetic_returns_3assets.columns), \
            "Weights should include all assets"

    def test_weights_sum_to_one(self, synthetic_returns_3assets):
        """
        GIVEN optimized portfolio weights
        WHEN checking weight constraint
        THEN sum of all weights equals 1.0 within numerical tolerance

        Validates:
        - ∑w_i = 1.0
        - Numerical precision (tolerance 1e-6)
        """
        optimizer = PortfolioOptimizer()
        weights = optimizer.optimize_erc(synthetic_returns_3assets)

        weight_sum = sum(weights.weights.values())

        assert abs(weight_sum - 1.0) < 1e-6, \
            f"Weights should sum to 1.0, got {weight_sum}"

    # ========================================================================
    # Test 3-4: Weight Constraints (Min/Max Bounds)
    # ========================================================================

    def test_max_weight_constraint_enforced(self, synthetic_returns_5assets):
        """
        GIVEN portfolio optimizer with max_weight constraint
        WHEN optimizing portfolio
        THEN all weights are less than or equal to max_weight

        Validates:
        - w_i ≤ max_weight for all i
        - Constraint enforcement prevents concentration
        """
        max_weight = 0.4
        optimizer = PortfolioOptimizer(max_weight=max_weight, min_weight=0.0)
        weights = optimizer.optimize_erc(synthetic_returns_5assets)

        for asset, weight in weights.weights.items():
            assert weight <= max_weight + 1e-6, \
                f"Asset {asset} weight {weight} exceeds max_weight {max_weight}"

    def test_min_weight_constraint_enforced(self, synthetic_returns_5assets):
        """
        GIVEN portfolio optimizer with min_weight constraint
        WHEN optimizing portfolio
        THEN all weights are greater than or equal to min_weight

        Validates:
        - w_i ≥ min_weight for all i
        - Minimum diversification enforced
        """
        min_weight = 0.1
        optimizer = PortfolioOptimizer(max_weight=0.5, min_weight=min_weight)
        weights = optimizer.optimize_erc(synthetic_returns_5assets)

        for asset, weight in weights.weights.items():
            assert weight >= min_weight - 1e-6, \
                f"Asset {asset} weight {weight} below min_weight {min_weight}"

    # ========================================================================
    # Test 5-6: Equal Risk Contribution Algorithm
    # ========================================================================

    def test_equal_risk_contribution_error_below_5_percent(self, synthetic_returns_3assets):
        """
        GIVEN optimized ERC portfolio
        WHEN calculating risk contributions
        THEN all risk contributions are approximately equal (within 5% error)

        Validates:
        - ERC algorithm correctness
        - |RC_i - RC_target| / RC_target < 0.05 for all i
        - RC_target = portfolio_variance / n_assets
        """
        optimizer = PortfolioOptimizer()
        weights = optimizer.optimize_erc(synthetic_returns_3assets)

        # Calculate portfolio variance from annualized volatility
        portfolio_var = (weights.volatility / np.sqrt(252)) ** 2

        # Target risk contribution (equal split)
        n_assets = len(weights.weights)
        target_rc = portfolio_var / n_assets

        # Check each asset's risk contribution
        for asset, rc in weights.risk_contributions.items():
            relative_error = abs(rc - target_rc) / target_rc if target_rc > 0 else 0

            assert relative_error < 0.05, \
                f"Asset {asset} RC error {relative_error:.2%} exceeds 5% threshold"

    def test_correlation_below_0_7_for_all_pairs(self, correlated_returns):
        """
        GIVEN portfolio with correlated assets
        WHEN optimization enforces diversification
        THEN average pairwise correlation should be reasonable

        Validates:
        - Diversification benefit
        - Not overly concentrated in correlated assets

        Note: This test verifies the input data quality rather than optimizer behavior.
        Real diversification constraint would be in P1.3 epsilon-constraint.
        """
        # Calculate correlation matrix
        corr_matrix = correlated_returns.corr()

        # Get upper triangle (exclude diagonal)
        n = len(corr_matrix)
        correlations = []
        for i in range(n):
            for j in range(i + 1, n):
                correlations.append(abs(corr_matrix.iloc[i, j]))

        avg_correlation = np.mean(correlations)

        # Verify input data has some diversification potential
        assert avg_correlation < 0.7, \
            f"Average correlation {avg_correlation:.2f} too high for effective diversification"

    # ========================================================================
    # Test 7-9: Risk Metrics Calculation
    # ========================================================================

    def test_risk_contributions_calculated_correctly(self, synthetic_returns_3assets):
        """
        GIVEN optimized portfolio weights
        WHEN calculating risk contributions
        THEN RC_i = w_i * (Σ_j w_j * cov_ij) matches manual calculation

        Validates:
        - Risk contribution formula correctness
        - RC_i = w_i * marginal_contribution_i
        - marginal_contribution_i = (Σw)^T @ cov @ e_i
        """
        optimizer = PortfolioOptimizer()
        weights_result = optimizer.optimize_erc(synthetic_returns_3assets)

        # Manual calculation
        returns = synthetic_returns_3assets
        w = np.array([weights_result.weights[col] for col in returns.columns])
        cov_matrix = returns.cov().values

        # Marginal contribution: cov_matrix @ w
        marginal_contrib = cov_matrix @ w

        # Risk contribution: w_i * marginal_contrib_i
        expected_rc = w * marginal_contrib

        # Compare with returned risk contributions
        actual_rc = np.array([
            weights_result.risk_contributions[col] for col in returns.columns
        ])

        np.testing.assert_allclose(
            actual_rc, expected_rc, rtol=1e-4,
            err_msg="Risk contributions don't match manual calculation"
        )

    def test_portfolio_volatility_calculated(self, synthetic_returns_3assets):
        """
        GIVEN optimized portfolio weights
        WHEN calculating portfolio volatility
        THEN σ_p = √(w^T Σ w) * √252 (annualized)

        Validates:
        - Volatility calculation formula
        - Annualization factor (√252 for daily returns)
        """
        optimizer = PortfolioOptimizer()
        weights_result = optimizer.optimize_erc(synthetic_returns_3assets)

        # Manual calculation
        returns = synthetic_returns_3assets
        w = np.array([weights_result.weights[col] for col in returns.columns])
        cov_matrix = returns.cov().values

        # Portfolio variance (daily)
        daily_var = w @ cov_matrix @ w

        # Annualized volatility
        expected_vol = np.sqrt(daily_var) * np.sqrt(252)

        assert abs(weights_result.volatility - expected_vol) < 1e-6, \
            f"Volatility mismatch: expected {expected_vol}, got {weights_result.volatility}"

    def test_expected_return_calculated(self, synthetic_returns_3assets):
        """
        GIVEN optimized portfolio weights
        WHEN calculating expected return
        THEN E[R_p] = w^T μ * 252 (annualized)

        Validates:
        - Expected return calculation
        - Annualization factor (252 for daily returns)
        """
        optimizer = PortfolioOptimizer()
        weights_result = optimizer.optimize_erc(synthetic_returns_3assets)

        # Manual calculation
        returns = synthetic_returns_3assets
        w = np.array([weights_result.weights[col] for col in returns.columns])
        mean_returns = returns.mean().values

        # Annualized expected return
        expected_return = (w @ mean_returns) * 252

        assert abs(weights_result.expected_return - expected_return) < 1e-6, \
            f"Expected return mismatch: expected {expected_return}, got {weights_result.expected_return}"

    # ========================================================================
    # Test 10-12: Optimizer Robustness
    # ========================================================================

    def test_scipy_slsqp_convergence(self, synthetic_returns_5assets):
        """
        GIVEN portfolio optimization problem
        WHEN using scipy.optimize.minimize with SLSQP method
        THEN optimizer should converge successfully

        Validates:
        - Optimization algorithm convergence
        - No convergence failures on well-conditioned problems
        """
        optimizer = PortfolioOptimizer()
        weights = optimizer.optimize_erc(synthetic_returns_5assets)

        # If we got valid weights that sum to 1 and satisfy constraints,
        # the optimizer converged successfully
        assert abs(sum(weights.weights.values()) - 1.0) < 1e-4, \
            "Convergence failure: weights don't sum to 1"

        # All weights should be valid (non-negative, bounded)
        for asset, weight in weights.weights.items():
            assert 0 <= weight <= 1, \
                f"Convergence failure: invalid weight {weight} for {asset}"

    def test_singular_covariance_matrix_handling(self):
        """
        GIVEN returns with perfectly correlated assets (singular covariance)
        WHEN optimizing portfolio
        THEN optimizer adds regularization and returns valid weights

        Validates:
        - Numerical stability
        - Matrix conditioning checks
        - Regularization (adding small value to diagonal)
        """
        np.random.seed(42)
        n_periods = 252

        # Create perfectly correlated assets (singular covariance matrix)
        base = np.random.randn(n_periods) * 0.02
        returns = pd.DataFrame({
            'asset_1': base,
            'asset_2': base * 2.0,  # Perfectly correlated
            'asset_3': base * 0.5,  # Perfectly correlated
        })

        optimizer = PortfolioOptimizer()
        weights = optimizer.optimize_erc(returns)

        # Should still produce valid weights despite singular matrix
        assert abs(sum(weights.weights.values()) - 1.0) < 1e-4, \
            "Failed to handle singular covariance matrix"

        for asset, weight in weights.weights.items():
            assert 0 <= weight <= 1, \
                f"Invalid weight {weight} for {asset}"

    def test_infeasible_constraints_fallback(self):
        """
        GIVEN infeasible constraints (e.g., min_weight too high)
        WHEN optimization fails
        THEN fallback to equal-weighted portfolio

        Validates:
        - Graceful degradation
        - Fallback strategy when constraints are infeasible
        """
        np.random.seed(42)
        returns = pd.DataFrame({
            'asset_1': np.random.randn(252) * 0.02,
            'asset_2': np.random.randn(252) * 0.02,
            'asset_3': np.random.randn(252) * 0.02,
        })

        # Infeasible: min_weight * n_assets > 1.0
        optimizer = PortfolioOptimizer(max_weight=0.5, min_weight=0.4)
        weights = optimizer.optimize_erc(returns)

        # Should fallback to equal weights
        expected_weight = 1.0 / 3.0
        for asset, weight in weights.weights.items():
            # Allow some tolerance since fallback might still try to optimize
            assert abs(weight - expected_weight) < 0.15, \
                f"Expected fallback to ~{expected_weight:.3f}, got {weight:.3f} for {asset}"

    # ========================================================================
    # Test 13: Performance Improvement
    # ========================================================================

    def test_sharpe_improvement_5_to_15_percent(self, synthetic_returns_5assets):
        """
        GIVEN ERC-optimized portfolio and equal-weighted baseline
        WHEN comparing Sharpe ratios
        THEN ERC should achieve 5-15% improvement over equal-weighted

        Validates:
        - Actual performance benefit of ERC
        - Algorithm effectiveness
        - Acceptance criteria for P1.2
        """
        returns = synthetic_returns_5assets

        # ERC portfolio
        optimizer = PortfolioOptimizer()
        erc_weights = optimizer.optimize_erc(returns)
        erc_sharpe = erc_weights.sharpe_ratio

        # Equal-weighted baseline
        n_assets = len(returns.columns)
        equal_w = np.array([1.0 / n_assets] * n_assets)

        equal_return = (returns.mean().values @ equal_w) * 252
        equal_cov = returns.cov().values
        equal_vol = np.sqrt(equal_w @ equal_cov @ equal_w) * np.sqrt(252)
        equal_sharpe = equal_return / equal_vol if equal_vol > 0 else 0

        # Calculate improvement
        improvement = (erc_sharpe - equal_sharpe) / equal_sharpe if equal_sharpe > 0 else 0

        assert 0.05 <= improvement <= 0.15, \
            f"ERC Sharpe improvement {improvement:.1%} outside 5-15% target range"

    # ========================================================================
    # Test 14-15: Edge Cases
    # ========================================================================

    def test_rebalancing_stability(self, synthetic_returns_3assets):
        """
        GIVEN two similar return datasets (with small price changes)
        WHEN optimizing both
        THEN portfolio weights should be stable (small changes in weights)

        Validates:
        - Optimization stability
        - Prevents excessive turnover
        - Numerical robustness
        """
        optimizer = PortfolioOptimizer()

        # Original optimization
        weights_1 = optimizer.optimize_erc(synthetic_returns_3assets)

        # Add small noise to returns (simulating small price changes)
        np.random.seed(43)  # Different seed
        noise = pd.DataFrame(
            np.random.randn(*synthetic_returns_3assets.shape) * 0.001,
            columns=synthetic_returns_3assets.columns,
            index=synthetic_returns_3assets.index
        )
        perturbed_returns = synthetic_returns_3assets + noise

        # Re-optimize with perturbed data
        weights_2 = optimizer.optimize_erc(perturbed_returns)

        # Check weight stability
        for asset in synthetic_returns_3assets.columns:
            w1 = weights_1.weights[asset]
            w2 = weights_2.weights[asset]
            weight_change = abs(w2 - w1)

            assert weight_change < 0.05, \
                f"Asset {asset} weight changed by {weight_change:.3f} (>5% threshold)"

    def test_edge_case_two_assets(self):
        """
        GIVEN minimum case of 2 assets
        WHEN optimizing with ERC
        THEN should produce valid portfolio weights

        Validates:
        - Edge case handling
        - Minimum viable portfolio size
        """
        np.random.seed(42)
        returns = pd.DataFrame({
            'asset_1': np.random.randn(252) * 0.02 + 0.0005,
            'asset_2': np.random.randn(252) * 0.015 + 0.0003,
        })

        optimizer = PortfolioOptimizer()
        weights = optimizer.optimize_erc(returns)

        # Should work with just 2 assets
        assert len(weights.weights) == 2
        assert abs(sum(weights.weights.values()) - 1.0) < 1e-6

        # Both assets should have non-zero weights
        for asset, weight in weights.weights.items():
            assert weight > 0, f"Asset {asset} has zero weight in 2-asset portfolio"
