"""Strategy DAG metadata extraction for Champion tracking.

This module provides functions to extract meaningful metadata from Factor Graph
Strategy DAG objects for use in ChampionStrategy. This enables Factor Graph
strategies to have comparable metadata to LLM-generated strategies.

Functions:
    extract_dag_parameters: Extract factor parameters from Strategy DAG
    extract_dag_patterns: Extract success patterns (factor types) from Strategy DAG
"""

from typing import Dict, Any, List


def extract_dag_parameters(strategy: Any) -> Dict[str, Any]:
    """Extract key parameters from Strategy DAG for Champion tracking.

    Extracts the params attribute from each factor in the Strategy DAG.
    This provides a summary of configuration values that contributed to success,
    analogous to parameters extracted from LLM code strings.

    Args:
        strategy: Strategy DAG object (from src.factor_graph.strategy)
            Must have a .factors attribute (dict mapping factor_id to Factor objects)

    Returns:
        Dictionary mapping factor_id to factor.params
        Empty dict if strategy has no factors or factors have no params

    Examples:
        >>> from src.factor_graph.strategy import Strategy
        >>> strategy = Strategy(id="momentum_v1", generation=1)
        >>> # Assume strategy has factors with params...
        >>> params = extract_dag_parameters(strategy)
        >>> params
        {
            "rsi_14": {"period": 14, "overbought": 70, "oversold": 30},
            "ma_20": {"window": 20, "method": "sma"}
        }

        >>> # Strategy with no params
        >>> empty_strategy = Strategy(id="simple", generation=1)
        >>> extract_dag_parameters(empty_strategy)
        {}

    Design Notes:
        - Only extracts factors that have a non-empty params attribute
        - Preserves original param structure (no flattening)
        - Returns empty dict (not None) for consistency with LLM path
        - Gracefully handles factors without params attribute
    """
    parameters = {}

    # Validate strategy has factors attribute
    if not hasattr(strategy, 'factors'):
        return parameters

    # Extract params from each factor
    for factor_id, factor in strategy.factors.items():
        # Only include factors that have params
        if hasattr(factor, 'params') and factor.params:
            parameters[factor_id] = factor.params

    return parameters


def extract_dag_patterns(strategy: Any) -> List[str]:
    """Extract success patterns from Strategy DAG (factor types).

    Extracts unique factor type names from the Strategy DAG. These serve as
    high-level patterns that contributed to success, analogous to success
    patterns extracted from LLM code (e.g., "momentum", "volume_filter").

    Args:
        strategy: Strategy DAG object (from src.factor_graph.strategy)
            Must have a .factors attribute (dict mapping factor_id to Factor objects)

    Returns:
        Sorted list of unique factor type names
        Empty list if strategy has no factors

    Examples:
        >>> from src.factor_graph.strategy import Strategy
        >>> from src.factor_graph.factors import RSI, MA, Signal
        >>> strategy = Strategy(id="momentum_v1", generation=1)
        >>> strategy.add_factor(RSI(...))
        >>> strategy.add_factor(MA(...))
        >>> strategy.add_factor(Signal(...))
        >>> patterns = extract_dag_patterns(strategy)
        >>> patterns
        ['MA', 'RSI', 'Signal']

        >>> # Strategy with duplicate factor types
        >>> strategy2 = Strategy(id="multi_rsi", generation=1)
        >>> strategy2.add_factor(RSI(id="rsi_14", period=14))
        >>> strategy2.add_factor(RSI(id="rsi_21", period=21))
        >>> extract_dag_patterns(strategy2)
        ['RSI']  # Duplicates removed

    Design Notes:
        - Uses type(factor).__name__ to get class name (e.g., "RSI", "MA")
        - Automatically deduplicates (multiple RSI factors → single "RSI" pattern)
        - Sorted alphabetically for consistency
        - Returns empty list (not None) for consistency with LLM path
        - Gracefully handles empty strategies

    Future Enhancements:
        Could be extended to include DAG structure patterns:
        - "RSI → Signal" (dependency patterns)
        - "Parallel indicators" (independent factors)
        - "Multi-stage filtering" (sequential dependencies)
    """
    patterns = set()

    # Validate strategy has factors attribute
    if not hasattr(strategy, 'factors'):
        return []

    # Extract unique factor type names
    for factor in strategy.factors.values():
        factor_type = type(factor).__name__
        patterns.add(factor_type)

    # Return sorted list for deterministic ordering
    return sorted(patterns)


__all__ = [
    'extract_dag_parameters',
    'extract_dag_patterns',
]
