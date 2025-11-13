"""
Risk Assessor - Calculate risk scores for tier selection.

Assesses strategy complexity, market conditions, and mutation history
to calculate risk scores that guide adaptive tier selection.

Architecture: Phase 2.0+ Factor Graph System
Task: D.4 - Adaptive Mutation Tier Selection
"""

import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass
import ast


@dataclass
class RiskMetrics:
    """
    Container for risk assessment metrics.

    Attributes:
        strategy_risk: Risk score from strategy complexity [0.0-1.0]
        market_risk: Risk score from market conditions [0.0-1.0]
        mutation_risk: Risk score from historical mutation success [0.0-1.0]
        overall_risk: Combined risk score [0.0-1.0]
        details: Additional details about risk assessment
    """
    strategy_risk: float
    market_risk: float
    mutation_risk: float
    overall_risk: float
    details: Dict[str, Any]


class RiskAssessor:
    """
    Assess risk for adaptive tier selection.

    Evaluates multiple dimensions of risk to guide mutation tier selection:
    - Strategy complexity (DAG structure, factor count, code complexity)
    - Market conditions (volatility, regime stability)
    - Historical mutation success rates per tier

    Higher risk scores suggest more conservative mutations (Tier 1 YAML),
    while lower risk scores enable more aggressive mutations (Tier 3 AST).

    Attributes:
        strategy_complexity_weight: Weight for strategy complexity (default: 0.4)
        market_risk_weight: Weight for market risk (default: 0.3)
        mutation_risk_weight: Weight for mutation history (default: 0.3)

    Example:
        >>> assessor = RiskAssessor()
        >>> risk = assessor.assess_strategy_risk(strategy)
        >>> if risk < 0.3:
        ...     # Low risk - can use Tier 3 AST mutations
        ...     pass
        >>> elif risk < 0.7:
        ...     # Medium risk - use Tier 2 Factor mutations
        ...     pass
        >>> else:
        ...     # High risk - use Tier 1 YAML mutations
        ...     pass
    """

    def __init__(
        self,
        strategy_complexity_weight: float = 0.4,
        market_risk_weight: float = 0.3,
        mutation_risk_weight: float = 0.3
    ):
        """
        Initialize risk assessor with configurable weights.

        Args:
            strategy_complexity_weight: Weight for strategy complexity component
            market_risk_weight: Weight for market risk component
            mutation_risk_weight: Weight for mutation history component

        Raises:
            ValueError: If weights don't sum to 1.0
        """
        total_weight = strategy_complexity_weight + market_risk_weight + mutation_risk_weight
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        self.strategy_complexity_weight = strategy_complexity_weight
        self.market_risk_weight = market_risk_weight
        self.mutation_risk_weight = mutation_risk_weight

    def assess_strategy_risk(self, strategy: Any) -> float:
        """
        Calculate risk score from strategy complexity.

        Evaluates:
        - DAG depth (deeper = more complex = higher risk)
        - Factor count (more factors = more dependencies = higher risk)
        - Code complexity (more complex logic = higher risk)

        Risk mapping:
        - Simple strategies (linear, few factors): 0.0-0.3
        - Moderate strategies (some branching, 5-10 factors): 0.3-0.6
        - Complex strategies (deep DAG, many factors): 0.6-1.0

        Args:
            strategy: Strategy object with DAG structure

        Returns:
            Risk score [0.0-1.0], higher = more complex/risky

        Example:
            >>> strategy = Strategy(id="simple_momentum")
            >>> strategy.add_factor(rsi_factor)
            >>> strategy.add_factor(signal_factor, depends_on=["rsi_14"])
            >>> risk = assessor.assess_strategy_risk(strategy)
            >>> assert 0.0 <= risk <= 0.3  # Simple linear strategy
        """
        if not hasattr(strategy, 'dag') or not hasattr(strategy, 'factors'):
            # Invalid strategy, return high risk
            return 1.0

        # Calculate DAG depth (longest path)
        dag_depth = self._calculate_dag_depth(strategy.dag)

        # Calculate factor count
        factor_count = len(strategy.factors)

        # Calculate code complexity (lines of code in factor logic)
        code_complexity = self._calculate_code_complexity(strategy)

        # Normalize metrics to [0, 1]
        # DAG depth: 1-3 = low, 4-7 = medium, 8+ = high
        depth_score = min(dag_depth / 10.0, 1.0)

        # Factor count: 1-5 = low, 6-15 = medium, 16+ = high
        count_score = min(factor_count / 20.0, 1.0)

        # Code complexity: <50 lines = low, 50-200 = medium, 200+ = high
        complexity_score = min(code_complexity / 300.0, 1.0)

        # Combine scores (equal weight)
        risk_score = (depth_score + count_score + complexity_score) / 3.0

        return risk_score

    def assess_market_risk(self, market_data: pd.DataFrame) -> float:
        """
        Calculate market condition risk.

        Evaluates:
        - Volatility (higher volatility = higher risk)
        - Regime stability (frequent regime changes = higher risk)
        - Recent drawdowns (large drawdowns = higher risk)

        Risk mapping:
        - Stable markets (low volatility): 0.0-0.3
        - Normal markets: 0.3-0.6
        - Turbulent markets (high volatility, regime changes): 0.6-1.0

        Args:
            market_data: DataFrame with price/volume data
                Required columns: 'close' (price)
                Optional: 'volume'

        Returns:
            Risk score [0.0-1.0], higher = more volatile/risky

        Example:
            >>> # Stable market
            >>> stable_data = pd.DataFrame({
            ...     'close': [100, 101, 100, 102, 101]
            ... })
            >>> risk = assessor.assess_market_risk(stable_data)
            >>> assert risk < 0.3
            >>>
            >>> # Volatile market
            >>> volatile_data = pd.DataFrame({
            ...     'close': [100, 110, 95, 115, 90]
            ... })
            >>> risk = assessor.assess_market_risk(volatile_data)
            >>> assert risk > 0.6
        """
        if market_data is None or market_data.empty:
            # No data, assume moderate risk
            return 0.5

        if 'close' not in market_data.columns:
            # Missing required data, assume moderate risk
            return 0.5

        # Calculate volatility (rolling std of returns)
        returns = market_data['close'].pct_change(fill_method=None)
        volatility = returns.std()

        # Calculate regime instability (number of significant trend changes)
        regime_instability = self._calculate_regime_instability(market_data['close'])

        # Calculate drawdown risk
        drawdown_risk = self._calculate_drawdown_risk(market_data['close'])

        # Normalize metrics
        # Volatility: <1% = low, 1-3% = medium, >3% = high
        volatility_score = min(volatility / 0.05, 1.0) if not np.isnan(volatility) else 0.5

        # Regime instability: 0-2 changes = stable, 3-5 = moderate, 6+ = unstable
        regime_score = min(regime_instability / 8.0, 1.0)

        # Combine scores
        risk_score = (volatility_score + regime_score + drawdown_risk) / 3.0

        return risk_score

    def assess_mutation_risk(
        self,
        mutation_type: str,
        historical_stats: Dict[str, Any]
    ) -> float:
        """
        Calculate mutation-specific risk from historical success rates.

        Evaluates historical performance of mutation tiers to assess risk:
        - High success rates (>60%) = low risk
        - Moderate success rates (30-60%) = medium risk
        - Low success rates (<30%) = high risk

        Args:
            mutation_type: Type of mutation being considered
            historical_stats: Historical statistics by tier
                Format: {
                    'tier1': {'attempts': int, 'successes': int},
                    'tier2': {'attempts': int, 'successes': int},
                    'tier3': {'attempts': int, 'successes': int}
                }

        Returns:
            Risk score [0.0-1.0], higher = lower historical success

        Example:
            >>> stats = {
            ...     'tier1': {'attempts': 100, 'successes': 80},  # 80% success
            ...     'tier2': {'attempts': 100, 'successes': 50},  # 50% success
            ...     'tier3': {'attempts': 100, 'successes': 20}   # 20% success
            ... }
            >>> risk = assessor.assess_mutation_risk('add_factor', stats)
        """
        if not historical_stats:
            # No history, assume moderate risk
            return 0.5

        # Calculate success rates per tier
        tier_risks = {}
        for tier_name, stats in historical_stats.items():
            attempts = stats.get('attempts', 0)
            successes = stats.get('successes', 0)

            if attempts == 0:
                # No history for this tier, assume moderate risk
                tier_risks[tier_name] = 0.5
            else:
                success_rate = successes / attempts
                # Invert success rate to get risk (high success = low risk)
                tier_risks[tier_name] = 1.0 - success_rate

        # Average risk across tiers
        if tier_risks:
            avg_risk = sum(tier_risks.values()) / len(tier_risks)
        else:
            avg_risk = 0.5

        return avg_risk

    def assess_overall_risk(
        self,
        strategy: Any,
        market_data: Optional[pd.DataFrame] = None,
        mutation_type: str = "generic",
        historical_stats: Optional[Dict[str, Any]] = None
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk assessment combining all factors.

        Args:
            strategy: Strategy object to assess
            market_data: Optional market data for risk assessment
            mutation_type: Type of mutation being considered
            historical_stats: Optional historical success stats

        Returns:
            RiskMetrics object with detailed risk breakdown

        Example:
            >>> metrics = assessor.assess_overall_risk(
            ...     strategy=my_strategy,
            ...     market_data=recent_data,
            ...     mutation_type="add_factor",
            ...     historical_stats=stats
            ... )
            >>> if metrics.overall_risk < 0.3:
            ...     # Use Tier 1 (safe)
            ...     pass
        """
        # Assess individual risk components
        strategy_risk = self.assess_strategy_risk(strategy)

        if market_data is not None:
            market_risk = self.assess_market_risk(market_data)
        else:
            market_risk = 0.5  # Default moderate risk

        if historical_stats is not None:
            mutation_risk = self.assess_mutation_risk(mutation_type, historical_stats)
        else:
            mutation_risk = 0.5  # Default moderate risk

        # Calculate weighted overall risk
        overall_risk = (
            strategy_risk * self.strategy_complexity_weight +
            market_risk * self.market_risk_weight +
            mutation_risk * self.mutation_risk_weight
        )

        # Compile details
        details = {
            'strategy_complexity': {
                'dag_depth': self._calculate_dag_depth(strategy.dag) if hasattr(strategy, 'dag') else 0,
                'factor_count': len(strategy.factors) if hasattr(strategy, 'factors') else 0,
            },
            'market_conditions': {
                'has_data': market_data is not None and not market_data.empty,
            },
            'historical_performance': {
                'has_stats': historical_stats is not None,
            }
        }

        return RiskMetrics(
            strategy_risk=strategy_risk,
            market_risk=market_risk,
            mutation_risk=mutation_risk,
            overall_risk=overall_risk,
            details=details
        )

    def _calculate_dag_depth(self, dag: nx.DiGraph) -> int:
        """Calculate maximum depth of DAG (longest path)."""
        if not dag or dag.number_of_nodes() == 0:
            return 0

        try:
            # Use longest path length as depth
            return nx.dag_longest_path_length(dag)
        except:
            # If there's an issue, return node count as approximation
            return dag.number_of_nodes()

    def _calculate_code_complexity(self, strategy: Any) -> int:
        """Calculate total lines of code across all factors."""
        if not hasattr(strategy, 'factors'):
            return 0

        total_lines = 0
        for factor in strategy.factors.values():
            if hasattr(factor, 'logic') and factor.logic is not None:
                try:
                    # Get source code and count lines
                    import inspect
                    source = inspect.getsource(factor.logic)
                    total_lines += len(source.split('\n'))
                except:
                    # If we can't get source, assume moderate complexity
                    total_lines += 10

        return total_lines

    def _calculate_regime_instability(self, prices: pd.Series) -> float:
        """Calculate number of significant regime changes."""
        if len(prices) < 10:
            return 0.0

        # Calculate rolling mean trend
        short_window = min(5, len(prices) // 2)
        long_window = min(20, len(prices) - 1)

        short_ma = prices.rolling(window=short_window, min_periods=1).mean()
        long_ma = prices.rolling(window=long_window, min_periods=1).mean()

        # Detect trend changes (short MA crosses long MA)
        trend = (short_ma > long_ma).astype(int)
        changes = trend.diff().abs().sum()

        # Return 0.0 if NaN
        return changes if not np.isnan(changes) else 0.0

    def _calculate_drawdown_risk(self, prices: pd.Series) -> float:
        """Calculate drawdown risk from recent price action."""
        if len(prices) < 2:
            return 0.0

        # Calculate maximum drawdown
        cummax = prices.expanding(min_periods=1).max()
        drawdown = (prices - cummax) / cummax
        max_drawdown = abs(drawdown.min())

        # Normalize: <5% = low, 5-15% = medium, >15% = high
        drawdown_score = min(max_drawdown / 0.20, 1.0)

        return drawdown_score if not np.isnan(drawdown_score) else 0.0
