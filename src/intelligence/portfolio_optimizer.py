"""
Portfolio optimization using Equal Risk Contribution (ERC).

This module implements risk parity portfolio optimization to ensure
balanced risk allocation across multiple assets.

TDD GREEN Phase: P1.2.2
Complete implementation to make all tests pass.
"""

from dataclasses import dataclass
from typing import Dict
import numpy as np
import pandas as pd
from scipy.optimize import minimize


@dataclass
class PortfolioWeights:
    """
    Portfolio allocation with risk metrics.

    Attributes:
        weights: Dictionary mapping asset names to portfolio weights (sum to 1.0)
        expected_return: Annualized expected return of the portfolio
        volatility: Annualized volatility (standard deviation) of the portfolio
        sharpe_ratio: Risk-adjusted return (expected_return / volatility)
        risk_contributions: Dictionary mapping asset names to risk contributions
    """
    weights: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    risk_contributions: Dict[str, float]


class PortfolioOptimizer:
    """
    Equal Risk Contribution (ERC) portfolio optimizer.

    Implements risk parity optimization where each asset contributes
    equally to portfolio risk. Uses scipy's SLSQP optimizer to minimize
    the sum of squared deviations from equal risk contribution.

    Algorithm:
        1. Calculate covariance matrix Σ from returns
        2. Minimize: ∑(RC_i - RC_target)^2
        3. Subject to: ∑w_i = 1, w_i ∈ [min_weight, max_weight]
        4. Where RC_i = w_i * (Σ_j w_j * cov_ij)

    Attributes:
        max_weight: Maximum weight allowed for any single asset
        min_weight: Minimum weight allowed for any single asset
    """

    def __init__(self, max_weight: float = 0.5, min_weight: float = 0.0):
        """
        Initialize optimizer with weight constraints.

        Args:
            max_weight: Maximum weight for any asset (default: 0.5)
            min_weight: Minimum weight for any asset (default: 0.0)

        Raises:
            ValueError: If constraints are invalid
        """
        if max_weight <= min_weight:
            raise ValueError(f"max_weight ({max_weight}) must be > min_weight ({min_weight})")

        if max_weight > 1.0 or max_weight <= 0.0:
            raise ValueError(f"max_weight ({max_weight}) must be in (0, 1]")

        if min_weight < 0.0 or min_weight >= 1.0:
            raise ValueError(f"min_weight ({min_weight}) must be in [0, 1)")

        self.max_weight = max_weight
        self.min_weight = min_weight

    def optimize_erc(self, returns: pd.DataFrame) -> PortfolioWeights:
        """
        Optimize portfolio using Equal Risk Contribution.

        Args:
            returns: DataFrame with asset returns (rows=dates, cols=assets)
                    Expected to be daily returns for proper annualization

        Returns:
            PortfolioWeights with optimized allocation and metrics

        Algorithm Details:
            - Objective: Minimize sum of squared deviations from equal RC
            - RC_i = w_i * (Σ_j w_j * cov_ij) = w_i * marginal_contribution_i
            - RC_target = portfolio_variance / n_assets
            - Uses SLSQP optimizer with weight constraints
            - Adds regularization (1e-8 * I) for numerical stability
            - Falls back to equal-weighted if optimization fails
        """
        n_assets = len(returns.columns)
        asset_names = returns.columns.tolist()

        # Calculate covariance matrix
        cov_matrix_original = returns.cov().values

        # Add minimal regularization for numerical stability (handle singular matrices)
        regularization = 1e-10 * np.trace(cov_matrix_original) / n_assets
        cov_matrix = cov_matrix_original + np.eye(n_assets) * regularization

        def objective(weights: np.ndarray) -> float:
            """
            Objective function: sum of squared deviations from equal risk contribution.

            The optimal ERC portfolio minimizes the variance of risk contributions.
            """
            # Portfolio variance
            portfolio_var = weights @ cov_matrix @ weights

            # Avoid division by zero
            if portfolio_var < 1e-10:
                return 1e10

            # Marginal contribution to risk for each asset
            marginal_contrib = cov_matrix @ weights

            # Risk contribution for each asset
            risk_contrib = weights * marginal_contrib

            # Target risk contribution (equal split)
            target_rc = portfolio_var / n_assets

            # Sum of squared deviations (normalized)
            deviations = (risk_contrib - target_rc) / (target_rc + 1e-10)
            return np.sum(deviations ** 2)

        # Constraints: weights sum to 1
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]

        # Bounds: each weight in [min_weight, max_weight]
        bounds = [(self.min_weight, self.max_weight)] * n_assets

        # Initial guess: inverse volatility weights (better than equal weights)
        volatilities = np.sqrt(np.diag(cov_matrix))
        inv_vol = 1.0 / (volatilities + 1e-10)
        x0 = inv_vol / np.sum(inv_vol)

        # Ensure initial guess satisfies bounds
        x0 = np.clip(x0, self.min_weight, self.max_weight)
        x0 = x0 / np.sum(x0)  # Renormalize

        # Check if constraints are feasible
        if n_assets * self.min_weight > 1.0:
            # Infeasible: fallback to equal weights
            optimal_weights = np.array([1.0 / n_assets] * n_assets)
            success = False
        else:
            # Optimize using SLSQP
            result = minimize(
                objective,
                x0,
                method='SLSQP',
                constraints=constraints,
                bounds=bounds,
                options={'maxiter': 1000, 'ftol': 1e-12}
            )

            if result.success:
                optimal_weights = result.x
                success = True
            else:
                # Fallback to equal weights on failure
                optimal_weights = np.array([1.0 / n_assets] * n_assets)
                success = False

        # Normalize weights to ensure they sum exactly to 1.0
        optimal_weights = optimal_weights / np.sum(optimal_weights)

        # Calculate portfolio metrics using ORIGINAL covariance (without regularization)
        weights_dict = dict(zip(asset_names, optimal_weights))

        # Expected return (annualized)
        mean_returns = returns.mean().values
        expected_return = (optimal_weights @ mean_returns) * 252

        # Volatility (annualized) - use original cov matrix
        daily_var = optimal_weights @ cov_matrix_original @ optimal_weights
        volatility = np.sqrt(daily_var) * np.sqrt(252)

        # Sharpe ratio
        sharpe_ratio = expected_return / volatility if volatility > 0 else 0.0

        # Risk contributions - use original cov matrix
        marginal_contrib = cov_matrix_original @ optimal_weights
        risk_contrib = optimal_weights * marginal_contrib
        risk_contrib_dict = dict(zip(asset_names, risk_contrib))

        return PortfolioWeights(
            weights=weights_dict,
            expected_return=expected_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            risk_contributions=risk_contrib_dict
        )
