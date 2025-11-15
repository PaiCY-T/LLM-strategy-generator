"""Multi-objective portfolio optimization using epsilon-constraint method.

This module implements the epsilon-constraint method for multi-objective
portfolio optimization, generating Pareto frontiers that balance return
maximization with risk constraints.

Classes:
    EpsilonConstraintOptimizer: Multi-objective optimizer using epsilon-constraint

References:
    - Miettinen, K. (1999). Nonlinear Multiobjective Optimization
    - Haimes, Y. Y., et al. (1971). On a Bicriterion Formulation of the
      Problems of Integrated System Identification and System Optimization
"""

from typing import List, Optional
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .portfolio_optimizer import PortfolioWeights


class EpsilonConstraintOptimizer:
    """Multi-objective portfolio optimization using epsilon-constraint method.

    Generates Pareto frontier by solving a series of single-objective
    problems with varying risk constraints.

    Algorithm:
        For each epsilon (risk level):
            1. Maximize: expected return
            2. Subject to:
               - Portfolio risk ≤ epsilon
               - Sum of weights = 1
               - Weight bounds: [min_weight, max_weight]
               - Diversity: at least threshold fraction of assets active

    This approach transforms the multi-objective problem:
        max return(w), min risk(w)
    into a series of single-objective problems:
        max return(w) s.t. risk(w) ≤ ε_i

    Attributes:
        diversity_threshold: Minimum fraction of assets required (0.30 = 30%)
        max_weight: Maximum weight per asset (0.70 = 70%)
        min_weight: Minimum weight per asset (0.0 = 0%)

    Example:
        >>> returns = pd.DataFrame(...)  # Historical returns
        >>> epsilon_values = np.linspace(0.10, 0.30, 10)
        >>> optimizer = EpsilonConstraintOptimizer(diversity_threshold=0.30)
        >>> pareto_frontier = optimizer.optimize(returns, epsilon_values)
        >>> len(pareto_frontier)
        10
        >>> pareto_frontier[0].volatility <= 0.10
        True
    """

    def __init__(
        self,
        diversity_threshold: float = 0.30,
        max_weight: float = 0.70,
        min_weight: float = 0.0
    ):
        """Initialize epsilon-constraint optimizer.

        Args:
            diversity_threshold: Minimum fraction of assets (0.30 = 30% of assets)
            max_weight: Maximum weight per asset (0.70 = 70%)
            min_weight: Minimum weight per asset (0.0 = 0%)

        Raises:
            ValueError: If thresholds are invalid
        """
        if not 0.0 <= diversity_threshold <= 1.0:
            raise ValueError(f"diversity_threshold must be in [0, 1], got {diversity_threshold}")
        if not 0.0 <= min_weight < max_weight <= 1.0:
            raise ValueError(f"Invalid weight bounds: [{min_weight}, {max_weight}]")

        self.diversity_threshold = diversity_threshold
        self.max_weight = max_weight
        self.min_weight = min_weight

    def optimize(
        self,
        returns: pd.DataFrame,
        epsilon_values: np.ndarray,
        risk_metric: str = 'volatility'
    ) -> List[PortfolioWeights]:
        """Generate Pareto frontier using epsilon-constraint method.

        Args:
            returns: Asset returns DataFrame (rows=dates, columns=assets)
            epsilon_values: Array of risk constraint values
            risk_metric: Risk measure ('volatility', 'var', 'cvar')

        Returns:
            List of PortfolioWeights on Pareto frontier, sorted by risk

        Raises:
            ValueError: If returns is empty or epsilon_values is invalid
            NotImplementedError: If risk_metric not supported

        Algorithm:
            For each ε in sorted(epsilon_values):
                1. Maximize: w^T μ (expected return)
                2. Subject to:
                   - Risk(w) ≤ ε
                   - ∑w_i = 1
                   - w_i ∈ [min_weight, max_weight]
                   - At least ⌈diversity_threshold × n⌉ assets active
                3. Store optimized portfolio if convergence successful

        Example:
            >>> returns = create_synthetic_returns(n_assets=5)
            >>> epsilon_values = np.linspace(0.10, 0.30, 10)
            >>> optimizer = EpsilonConstraintOptimizer()
            >>> frontier = optimizer.optimize(returns, epsilon_values)
            >>> all(p.volatility <= e + 1e-6 for p, e in zip(frontier, sorted(epsilon_values)))
            True
        """
        if returns.empty:
            raise ValueError("Returns DataFrame cannot be empty")

        if len(epsilon_values) == 0:
            return []

        # Calculate statistics
        n_assets = len(returns.columns)
        mean_returns = returns.mean().values
        cov_matrix = returns.cov().values

        # Add regularization for numerical stability
        cov_matrix += np.eye(n_assets) * 1e-8

        # Calculate minimum number of active assets
        min_active_assets = int(np.ceil(n_assets * self.diversity_threshold))

        pareto_frontier = []
        previous_weights = None

        # Iterate through epsilon values in sorted order
        for epsilon in sorted(epsilon_values):
            # Objective: maximize return (minimize negative return)
            def objective(w):
                return -(w @ mean_returns)

            # Risk constraint
            def risk_constraint(w):
                if risk_metric == 'volatility':
                    # Annualized volatility
                    risk = np.sqrt(w @ cov_matrix @ w) * np.sqrt(252)
                elif risk_metric == 'var':
                    raise NotImplementedError("VaR risk metric not yet implemented")
                elif risk_metric == 'cvar':
                    raise NotImplementedError("CVaR risk metric not yet implemented")
                else:
                    raise NotImplementedError(f"Risk metric '{risk_metric}' not implemented")

                return epsilon - risk  # Must be ≥ 0

            # Diversity constraint: at least min_active_assets with weight > threshold
            def diversity_constraint(w):
                active_count = np.sum(w > 1e-4)
                return active_count - min_active_assets  # Must be ≥ 0

            # Define constraints
            constraints = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},  # Weights sum to 1
                {'type': 'ineq', 'fun': risk_constraint},  # Risk ≤ epsilon
                {'type': 'ineq', 'fun': diversity_constraint}  # Diversity requirement
            ]

            # Define bounds
            bounds = [(self.min_weight, self.max_weight)] * n_assets

            # Try multiple initial guesses to improve convergence
            best_result = None

            # Initial guess 1: equal weights
            x0_options = [np.array([1.0 / n_assets] * n_assets)]

            # Initial guess 2: previous solution (if available)
            if previous_weights is not None:
                x0_options.append(previous_weights)

            # Initial guess 3: random feasible weights
            if len(pareto_frontier) == 0 or len(pareto_frontier) < 3:
                # Only try random for first few to save time
                np.random.seed(42 + len(pareto_frontier))
                random_weights = np.random.dirichlet(np.ones(n_assets))
                # Ensure diversity by setting at least min_active_assets to non-zero
                if np.sum(random_weights > 1e-4) < min_active_assets:
                    random_weights[:min_active_assets] = 1.0 / min_active_assets
                    random_weights = random_weights / random_weights.sum()
                x0_options.append(random_weights)

            # Try each initial guess
            for x0 in x0_options:
                result = minimize(
                    objective,
                    x0,
                    method='SLSQP',
                    constraints=constraints,
                    bounds=bounds,
                    options={'maxiter': 2000, 'ftol': 1e-9}
                )

                if result.success:
                    if best_result is None or result.fun < best_result.fun:
                        best_result = result

            # Use best result if found
            if best_result is not None:
                # Create PortfolioWeights instance
                weights_dict = dict(zip(returns.columns, best_result.x))

                # Calculate metrics
                expected_return = (returns.mean() @ best_result.x) * 252  # Annualized
                volatility = np.sqrt(best_result.x @ cov_matrix @ best_result.x) * np.sqrt(252)
                sharpe_ratio = expected_return / volatility if volatility > 0 else 0

                # Calculate risk contributions
                marginal_contrib = cov_matrix @ best_result.x
                risk_contrib = best_result.x * marginal_contrib
                risk_contrib_dict = dict(zip(returns.columns, risk_contrib))

                portfolio = PortfolioWeights(
                    weights=weights_dict,
                    expected_return=expected_return,
                    volatility=volatility,
                    sharpe_ratio=sharpe_ratio,
                    risk_contributions=risk_contrib_dict
                )

                pareto_frontier.append(portfolio)
                previous_weights = best_result.x

        return pareto_frontier
