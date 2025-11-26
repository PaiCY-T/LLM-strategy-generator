"""
Comprehensive Scorer for Multi-Objective Strategy Evaluation (Spec B P1).

Implements weighted scoring for 40M TWD capital strategies,
balancing risk-adjusted returns, stability, and execution costs.

Score Formula:
    Score = w1×Calmar + w2×Sortino + w3×Stability
            - w4×Turnover_Cost - w5×Liquidity_Penalty

Default Weights (40M TWD):
    - Calmar: 30%
    - Sortino: 25%
    - Stability: 20%
    - Turnover_Cost: 15%
    - Liquidity_Penalty: 10%

Usage:
    from src.validation.comprehensive_scorer import ComprehensiveScorer

    scorer = ComprehensiveScorer(capital=40_000_000)
    result = scorer.compute_score(metrics)
    print(f"Total Score: {result['total_score']:.2f}")
"""

import logging
from typing import Any, Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ComprehensiveScorer:
    """Multi-Objective Comprehensive Scorer.

    Evaluates strategies using weighted combination of:
    - Risk-adjusted returns (Calmar, Sortino)
    - Return stability (consistency of monthly returns)
    - Execution costs (turnover, liquidity)

    Attributes:
        capital (float): Total capital in TWD
        weights (dict): Component weights (must sum to 1.0)

    Example:
        >>> scorer = ComprehensiveScorer(capital=40_000_000)
        >>> result = scorer.compute_score({
        ...     'calmar_ratio': 2.5,
        ...     'sortino_ratio': 3.0,
        ...     'monthly_returns': np.array([...]),
        ...     'annual_turnover': 2.0,
        ...     'avg_slippage_bps': 25,
        ... })
        >>> print(result['total_score'])
    """

    # Default weights for 40M TWD capital
    DEFAULT_WEIGHTS = {
        'calmar': 0.30,           # 30% - Calmar ratio (return/max DD)
        'sortino': 0.25,          # 25% - Sortino ratio (return/downside risk)
        'stability': 0.20,        # 20% - Return stability
        'turnover_cost': 0.15,    # 15% - Turnover cost penalty
        'liquidity_penalty': 0.10, # 10% - Liquidity penalty
    }

    def __init__(
        self,
        capital: float = 40_000_000,
        weights: Optional[Dict[str, float]] = None
    ):
        """Initialize ComprehensiveScorer.

        Args:
            capital: Total capital in TWD (default: 40M)
            weights: Custom weights (default: DEFAULT_WEIGHTS)
        """
        self.capital = capital
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

        logger.info(
            f"ComprehensiveScorer initialized: capital={capital:,.0f} TWD, "
            f"weights={self.weights}"
        )

    def compute_score(
        self,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute comprehensive score for a strategy.

        Args:
            metrics: Dictionary containing:
                - calmar_ratio (float): Calmar ratio
                - sortino_ratio (float): Sortino ratio
                - monthly_returns (np.ndarray): Array of monthly returns
                - annual_turnover (float): Annual turnover rate
                - avg_slippage_bps (float): Average slippage in bps

        Returns:
            Dictionary with:
                - total_score (float): Weighted score
                - components (dict): Individual component scores
                - weights (dict): Weights used
        """
        # Extract metrics with defaults
        calmar = metrics.get('calmar_ratio', 0.0)
        sortino = metrics.get('sortino_ratio', 0.0)
        monthly_returns = metrics.get('monthly_returns', np.array([]))
        annual_turnover = metrics.get('annual_turnover', 1.0)
        avg_slippage_bps = metrics.get('avg_slippage_bps', 20.0)

        # Calculate component scores
        calmar_score = self._normalize_ratio(calmar, max_val=5.0)
        sortino_score = self._normalize_ratio(sortino, max_val=5.0)
        stability_score = self.calculate_stability(monthly_returns)
        turnover_penalty = self.calculate_turnover_cost(annual_turnover)
        liquidity_penalty = self._calculate_liquidity_penalty(avg_slippage_bps)

        # Store components
        components = {
            'calmar_score': calmar_score,
            'sortino_score': sortino_score,
            'stability_score': stability_score,
            'turnover_penalty': turnover_penalty,
            'liquidity_penalty': liquidity_penalty,
        }

        # Calculate weighted total
        total_score = (
            self.weights['calmar'] * calmar_score +
            self.weights['sortino'] * sortino_score +
            self.weights['stability'] * stability_score -
            self.weights['turnover_cost'] * turnover_penalty -
            self.weights['liquidity_penalty'] * liquidity_penalty
        )

        return {
            'total_score': total_score,
            'components': components,
            'weights': self.weights.copy(),
        }

    def calculate_stability(
        self,
        monthly_returns: np.ndarray
    ) -> float:
        """Calculate return stability score.

        Stability measures consistency of returns:
        - High stability: Consistent positive returns
        - Low stability: Volatile or inconsistent returns

        Formula:
            Stability = 1 / (1 + CoV)
            where CoV = std(returns) / abs(mean(returns))

        Args:
            monthly_returns: Array of monthly returns

        Returns:
            Stability score in [0, 1]
        """
        if len(monthly_returns) == 0:
            return 0.0

        returns = np.array(monthly_returns)
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # Handle zero or negative mean
        if abs(mean_return) < 1e-10:
            # If returns average zero, stability depends on variance
            if std_return < 1e-10:
                return 1.0  # All zeros = stable
            else:
                return 0.0  # Zero mean with variance = unstable

        # Coefficient of variation
        cov = std_return / abs(mean_return)

        # Convert to stability: lower CoV = higher stability
        stability = 1.0 / (1.0 + cov)

        # Clip to [0, 1]
        return np.clip(stability, 0.0, 1.0)

    def calculate_turnover_cost(
        self,
        annual_turnover: float,
        commission_bps: float = 10.0
    ) -> float:
        """Calculate annualized turnover cost.

        Formula:
            Cost = Turnover × Commission_Rate

        Args:
            annual_turnover: Annual turnover rate (e.g., 2.0 for 200%)
            commission_bps: Commission per trade in basis points

        Returns:
            Annual cost as fraction (e.g., 0.002 for 0.2%)
        """
        return annual_turnover * (commission_bps / 10000)

    def _calculate_liquidity_penalty(
        self,
        avg_slippage_bps: float
    ) -> float:
        """Calculate liquidity penalty based on slippage.

        Same formula as ExecutionCostModel:
        - < 20 bps: No penalty
        - 20-50 bps: Linear penalty
        - > 50 bps: Quadratic penalty

        Args:
            avg_slippage_bps: Average slippage in basis points

        Returns:
            Penalty score in [0, 1]
        """
        if avg_slippage_bps < 20:
            return 0.0
        elif avg_slippage_bps <= 50:
            return (avg_slippage_bps - 20) / 60
        else:
            linear_penalty = 0.5
            quadratic_penalty = ((avg_slippage_bps - 50) ** 2) / 10000
            return min(1.0, linear_penalty + quadratic_penalty)

    def _normalize_ratio(
        self,
        ratio: float,
        max_val: float = 5.0
    ) -> float:
        """Normalize ratio to [0, 1] range.

        Uses sigmoid-like transformation:
        - Negative ratios → values < 0.5
        - Positive ratios → values > 0.5
        - Capped at max_val

        Args:
            ratio: Raw ratio value
            max_val: Maximum expected ratio

        Returns:
            Normalized score in [0, 1]
        """
        # Clip to reasonable range
        clipped = np.clip(ratio, -max_val, max_val)

        # Linear mapping from [-max, max] to [0, 1]
        normalized = (clipped + max_val) / (2 * max_val)

        return float(normalized)

    def rank_strategies(
        self,
        strategies: list,
        key: str = 'total_score'
    ) -> list:
        """Rank strategies by score.

        Args:
            strategies: List of strategy metrics dicts
            key: Score component to rank by

        Returns:
            List of (score_result, rank) tuples, sorted descending
        """
        scored = []
        for i, metrics in enumerate(strategies):
            result = self.compute_score(metrics)
            scored.append((result, i, result[key] if key == 'total_score'
                          else result['components'].get(key, 0)))

        # Sort by score descending
        scored.sort(key=lambda x: x[2], reverse=True)

        # Return with ranks
        ranked = []
        for rank, (result, orig_idx, score) in enumerate(scored, 1):
            ranked.append({
                'rank': rank,
                'original_index': orig_idx,
                'result': result,
            })

        return ranked

    def get_score_breakdown(
        self,
        metrics: Dict[str, Any]
    ) -> str:
        """Get human-readable score breakdown.

        Args:
            metrics: Strategy metrics

        Returns:
            Formatted string with score breakdown
        """
        result = self.compute_score(metrics)
        components = result['components']
        weights = result['weights']

        lines = [
            "Score Breakdown",
            "=" * 40,
            f"Total Score: {result['total_score']:.4f}",
            "",
            "Components:",
        ]

        for name, score in components.items():
            weight = weights.get(name.replace('_score', '').replace('_penalty', ''),
                                weights.get(name, 0))
            contribution = weight * score if 'penalty' not in name else -weight * score
            lines.append(f"  {name:20s}: {score:.4f} (weight: {weight:.0%}, contrib: {contribution:.4f})")

        return "\n".join(lines)
