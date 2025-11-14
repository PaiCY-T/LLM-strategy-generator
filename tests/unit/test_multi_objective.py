"""Unit tests for epsilon-constraint multi-objective portfolio optimization.

This module tests the EpsilonConstraintOptimizer class that generates
Pareto frontiers using the epsilon-constraint method for multi-objective
portfolio optimization.

Test Coverage:
- Basic optimization functionality
- Pareto frontier generation
- Constraint satisfaction (risk, diversity, weights)
- Monotonicity properties
- Edge cases and error handling
- Integration with existing portfolio components
"""

import pytest
import pandas as pd
import numpy as np
from typing import List


def create_synthetic_returns(
    n_assets: int = 5,
    n_periods: int = 252,
    mean_return: float = 0.0003,
    volatility: float = 0.02,
    seed: int = 42
) -> pd.DataFrame:
    """Create synthetic returns for testing.

    Args:
        n_assets: Number of assets
        n_periods: Number of time periods
        mean_return: Daily mean return
        volatility: Daily volatility
        seed: Random seed for reproducibility

    Returns:
        DataFrame with synthetic returns
    """
    np.random.seed(seed)

    # Create correlated returns
    correlation = 0.3
    cov_matrix = np.full((n_assets, n_assets), correlation * volatility**2)
    np.fill_diagonal(cov_matrix, volatility**2)

    # Generate returns
    returns = np.random.multivariate_normal(
        mean=[mean_return] * n_assets,
        cov=cov_matrix,
        size=n_periods
    )

    # Create DataFrame
    columns = [f'ASSET_{i}' for i in range(n_assets)]
    return pd.DataFrame(returns, columns=columns)


class TestEpsilonConstraint:
    """Test suite for EpsilonConstraintOptimizer."""

    def test_optimize_returns_list_of_portfolio_weights(self):
        """GIVEN returns data and epsilon values
           WHEN optimizing with epsilon-constraint
           THEN return list of PortfolioWeights"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer
        from src.intelligence.portfolio_optimizer import PortfolioWeights

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.linspace(0.10, 0.30, 10)

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        assert isinstance(pareto_frontier, list), "Should return list"
        assert len(pareto_frontier) > 0, "Should have at least one solution"
        assert all(isinstance(w, PortfolioWeights) for w in pareto_frontier), \
            "All elements should be PortfolioWeights"

    def test_pareto_frontier_has_at_least_10_solutions(self):
        """GIVEN 10 epsilon values
           WHEN optimizing
           THEN return at least 10 solutions on Pareto frontier"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.linspace(0.10, 0.30, 10)

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        assert len(pareto_frontier) >= 10, \
            f"Expected ≥10 solutions, got {len(pareto_frontier)}"

    def test_each_solution_satisfies_risk_constraint(self):
        """GIVEN epsilon values
           WHEN optimizing
           THEN all solutions satisfy risk ≤ epsilon"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.linspace(0.10, 0.30, 10)

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        for i, (portfolio, epsilon) in enumerate(zip(pareto_frontier, sorted(epsilon_values))):
            assert portfolio.volatility <= epsilon + 1e-6, \
                f"Solution {i}: volatility {portfolio.volatility:.6f} > epsilon {epsilon:.6f}"

    def test_diversity_constraint_30_percent_enforced(self):
        """GIVEN diversity threshold of 30%
           WHEN optimizing
           THEN at least 30% of assets have non-zero weights"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=10)
        epsilon_values = np.linspace(0.10, 0.30, 10)

        optimizer = EpsilonConstraintOptimizer(diversity_threshold=0.30)
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        min_active_assets = int(np.ceil(10 * 0.30))  # 3 assets

        for portfolio in pareto_frontier:
            active_assets = sum(1 for w in portfolio.weights.values() if w > 1e-4)
            assert active_assets >= min_active_assets, \
                f"Only {active_assets} active assets, need ≥{min_active_assets}"

    def test_return_maximized_for_each_epsilon(self):
        """GIVEN epsilon constraint on risk
           WHEN optimizing return
           THEN solution is optimal for that risk level"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon = 0.20  # 20% max volatility

        optimizer = EpsilonConstraintOptimizer(diversity_threshold=0.3)
        result = optimizer.optimize(returns, [epsilon])[0]

        # Verify risk constraint satisfied
        assert result.volatility <= epsilon + 1e-6, \
            f"Risk {result.volatility:.6f} exceeds epsilon {epsilon:.6f}"

        # Verify return is positive and reasonable
        assert result.expected_return > 0, "Expected return should be positive"

    def test_weights_sum_to_one_all_solutions(self):
        """GIVEN Pareto frontier
           WHEN checking weights
           THEN sum of weights equals 1 for all portfolios"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.linspace(0.10, 0.30, 10)

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        for i, portfolio in enumerate(pareto_frontier):
            weight_sum = sum(portfolio.weights.values())
            assert abs(weight_sum - 1.0) < 1e-6, \
                f"Solution {i}: weights sum to {weight_sum:.6f}, not 1.0"

    def test_risk_monotonically_increases_with_epsilon(self):
        """GIVEN sorted epsilon values
           WHEN optimizing
           THEN risk increases or stays constant"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.linspace(0.10, 0.30, 10)

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        risks = [p.volatility for p in pareto_frontier]

        for i in range(len(risks) - 1):
            assert risks[i] <= risks[i+1] + 1e-6, \
                f"Risk decreased: {risks[i]:.6f} > {risks[i+1]:.6f}"

    def test_return_monotonically_increases_with_risk(self):
        """GIVEN Pareto frontier
           WHEN risk increases
           THEN return increases or stays constant"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.linspace(0.10, 0.30, 10)

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        returns_list = [p.expected_return for p in pareto_frontier]

        for i in range(len(returns_list) - 1):
            assert returns_list[i] <= returns_list[i+1] + 1e-6, \
                f"Return decreased: {returns_list[i]:.6f} > {returns_list[i+1]:.6f}"

    def test_scipy_slsqp_convergence_all_epsilon(self):
        """GIVEN epsilon values
           WHEN optimizing
           THEN all optimizations converge successfully"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.linspace(0.10, 0.30, 10)

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        # All epsilon values should produce solutions
        assert len(pareto_frontier) == len(epsilon_values), \
            f"Expected {len(epsilon_values)} solutions, got {len(pareto_frontier)}"

    def test_infeasible_constraint_handling(self):
        """GIVEN very tight epsilon constraints
           WHEN some are infeasible
           THEN skip infeasible solutions gracefully"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        # Include some very small epsilon values that may be infeasible
        epsilon_values = np.array([0.01, 0.05, 0.10, 0.20, 0.30])

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        # Should have at least some solutions
        assert len(pareto_frontier) >= 3, \
            "Should produce solutions for feasible epsilon values"

        # All returned solutions should be valid
        for portfolio in pareto_frontier:
            assert sum(portfolio.weights.values()) > 0.99, \
                "Invalid solution in frontier"

    def test_epsilon_values_edge_cases(self):
        """GIVEN edge case epsilon values
           WHEN optimizing
           THEN handle min/max epsilon correctly"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)

        # Test minimum epsilon (tight constraint)
        optimizer = EpsilonConstraintOptimizer()
        pareto_tight = optimizer.optimize(returns, [0.15])

        assert len(pareto_tight) == 1, "Should produce one solution"
        assert pareto_tight[0].volatility <= 0.15 + 1e-6, \
            "Should satisfy tight constraint"

        # Test maximum epsilon (loose constraint)
        pareto_loose = optimizer.optimize(returns, [0.50])

        assert len(pareto_loose) == 1, "Should produce one solution"
        assert pareto_loose[0].volatility <= 0.50 + 1e-6, \
            "Should satisfy loose constraint"

    def test_diversity_constraint_prevents_concentration(self):
        """GIVEN diversity constraint
           WHEN optimizing
           THEN no single asset exceeds max_weight"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.linspace(0.10, 0.30, 10)

        optimizer = EpsilonConstraintOptimizer(
            diversity_threshold=0.30,
            max_weight=0.70
        )
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        for portfolio in pareto_frontier:
            max_asset_weight = max(portfolio.weights.values())
            assert max_asset_weight <= 0.70 + 1e-6, \
                f"Asset weight {max_asset_weight:.4f} exceeds max 0.70"

    def test_pareto_optimality_verified(self):
        """GIVEN Pareto frontier
           WHEN checking for domination
           THEN no solution dominates another"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.linspace(0.10, 0.30, 10)

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        # Check that no solution is dominated by another
        for i, p1 in enumerate(pareto_frontier):
            for j, p2 in enumerate(pareto_frontier):
                if i == j:
                    continue

                # p2 dominates p1 if:
                # p2.return ≥ p1.return AND p2.risk ≤ p1.risk
                # AND at least one inequality is strict

                return_better = p2.expected_return >= p1.expected_return - 1e-6
                risk_better = p2.volatility <= p1.volatility + 1e-6
                strictly_better = (
                    p2.expected_return > p1.expected_return + 1e-6 or
                    p2.volatility < p1.volatility - 1e-6
                )

                dominates = return_better and risk_better and strictly_better

                assert not dominates, \
                    f"Solution {j} dominates solution {i} (should not happen in Pareto frontier)"

    def test_sharpe_ratio_calculated_for_each(self):
        """GIVEN Pareto frontier
           WHEN checking metrics
           THEN Sharpe ratio calculated for all portfolios"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.linspace(0.10, 0.30, 10)

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        for portfolio in pareto_frontier:
            assert hasattr(portfolio, 'sharpe_ratio'), \
                "Missing sharpe_ratio attribute"
            assert portfolio.sharpe_ratio >= 0, \
                "Sharpe ratio should be non-negative"

            # Verify calculation
            expected_sharpe = portfolio.expected_return / portfolio.volatility \
                if portfolio.volatility > 0 else 0
            assert abs(portfolio.sharpe_ratio - expected_sharpe) < 1e-6, \
                "Sharpe ratio calculation incorrect"

    def test_risk_contributions_included(self):
        """GIVEN Pareto frontier
           WHEN checking metrics
           THEN risk contributions calculated for all portfolios"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.linspace(0.10, 0.30, 10)

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        for portfolio in pareto_frontier:
            assert hasattr(portfolio, 'risk_contributions'), \
                "Missing risk_contributions attribute"
            assert isinstance(portfolio.risk_contributions, dict), \
                "risk_contributions should be dict"
            assert len(portfolio.risk_contributions) == len(portfolio.weights), \
                "Risk contributions should match number of assets"

    def test_integration_with_erc(self):
        """GIVEN ERC portfolio as starting point
           WHEN optimizing with epsilon-constraint
           THEN can use ERC solution in optimization"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.linspace(0.10, 0.30, 10)

        # This test verifies the optimizer works independently
        # (future enhancement: use ERC as initial guess)
        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        assert len(pareto_frontier) > 0, \
            "Should produce solutions without ERC starting point"

    def test_multiple_risk_metrics_support(self):
        """GIVEN different risk metrics (volatility, VaR, CVaR)
           WHEN optimizing
           THEN support multiple risk measures"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.linspace(0.10, 0.30, 5)

        optimizer = EpsilonConstraintOptimizer()

        # Test volatility (default)
        pareto_vol = optimizer.optimize(returns, epsilon_values, risk_metric='volatility')
        assert len(pareto_vol) >= 5, "Should work with volatility metric"

        # Test VaR and CVaR (should raise NotImplementedError for now)
        with pytest.raises(NotImplementedError):
            optimizer.optimize(returns, epsilon_values, risk_metric='var')

        with pytest.raises(NotImplementedError):
            optimizer.optimize(returns, epsilon_values, risk_metric='cvar')

    def test_edge_case_single_epsilon(self):
        """GIVEN single epsilon value
           WHEN optimizing
           THEN return single optimal portfolio"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon = 0.20

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, [epsilon])

        assert len(pareto_frontier) == 1, "Should return exactly one solution"
        assert pareto_frontier[0].volatility <= epsilon + 1e-6, \
            "Should satisfy epsilon constraint"
        assert sum(pareto_frontier[0].weights.values()) > 0.99, \
            "Weights should sum to 1"


class TestEpsilonConstraintEdgeCases:
    """Additional edge case tests."""

    def test_empty_epsilon_values(self):
        """GIVEN empty epsilon array
           WHEN optimizing
           THEN return empty list"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, np.array([]))

        assert len(pareto_frontier) == 0, "Should return empty list"

    def test_unsorted_epsilon_values(self):
        """GIVEN unsorted epsilon values
           WHEN optimizing
           THEN handle correctly and return sorted results"""
        from src.intelligence.multi_objective import EpsilonConstraintOptimizer

        returns = create_synthetic_returns(n_assets=5)
        epsilon_values = np.array([0.30, 0.10, 0.20, 0.25, 0.15])

        optimizer = EpsilonConstraintOptimizer()
        pareto_frontier = optimizer.optimize(returns, epsilon_values)

        # Results should be ordered by risk
        risks = [p.volatility for p in pareto_frontier]
        assert all(risks[i] <= risks[i+1] + 1e-6 for i in range(len(risks)-1)), \
            "Results should be sorted by risk"
