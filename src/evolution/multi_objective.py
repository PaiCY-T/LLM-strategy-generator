"""
Multi-objective optimization functions for NSGA-II evolutionary algorithm.

Provides Pareto front calculation, crowding distance computation, and other
multi-objective optimization utilities for population-based learning.

Core Functions:
    pareto_dominates: Check if one metrics set Pareto-dominates another
    calculate_pareto_front: Identify non-dominated strategies in a population
    assign_pareto_ranks: NSGA-II fast non-dominated sorting for ranking
    calculate_crowding_distance: NSGA-II diversity metric for Pareto front

Pareto Dominance:
    Metrics A dominates metrics B if A is at least as good in all objectives
    and strictly better in at least one objective.

    Maximization objectives: sharpe_ratio, calmar_ratio, total_return, win_rate, annual_return
    Minimization objective: max_drawdown (less negative is better, e.g., -0.10 > -0.20)

References:
    - Deb, K., et al. (2002). "A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II"
    - Coello, C. A. C., et al. (2007). "Evolutionary Algorithms for Solving Multi-Objective Problems"
"""

from typing import List, Dict
from .types import Strategy, MultiObjectiveMetrics

def pareto_dominates(metrics_a: MultiObjectiveMetrics, metrics_b: MultiObjectiveMetrics) -> bool:
    """
    Check if metrics A Pareto-dominates metrics B.

    Pareto dominance occurs when metrics_a is at least as good as metrics_b in
    all objectives and strictly better in at least one objective. This function
    is the core of NSGA-II non-dominated sorting and Pareto front identification.

    Maximization objectives (higher is better):
        - sharpe_ratio: Risk-adjusted return (return / volatility)
        - calmar_ratio: Return / abs(max_drawdown) ratio
        - total_return: Cumulative return over backtest period
        - win_rate: Percentage of winning trades (0.0 to 1.0)
        - annual_return: Annualized return

    Minimization objective (less negative is better):
        - max_drawdown: Maximum peak-to-trough decline (negative value)
          Example: -0.10 (10% drawdown) is better than -0.20 (20% drawdown)

    Args:
        metrics_a: First MultiObjectiveMetrics to compare
        metrics_b: Second MultiObjectiveMetrics to compare against

    Returns:
        bool: True if metrics_a Pareto-dominates metrics_b, False otherwise

    Example:
        >>> from src.evolution.types import MultiObjectiveMetrics
        >>> m1 = MultiObjectiveMetrics(
        ...     sharpe_ratio=1.5,
        ...     calmar_ratio=2.0,
        ...     max_drawdown=-0.10,  # Better: -10% drawdown
        ...     total_return=0.50,
        ...     win_rate=0.60,
        ...     annual_return=0.20,
        ...     success=True
        ... )
        >>> m2 = MultiObjectiveMetrics(
        ...     sharpe_ratio=1.2,
        ...     calmar_ratio=1.8,
        ...     max_drawdown=-0.20,  # Worse: -20% drawdown
        ...     total_return=0.40,
        ...     win_rate=0.55,
        ...     annual_return=0.18,
        ...     success=True
        ... )
        >>> pareto_dominates(m1, m2)
        True
        >>> pareto_dominates(m2, m1)
        False

    Example (Non-dominated):
        >>> m3 = MultiObjectiveMetrics(
        ...     sharpe_ratio=1.8,   # Better
        ...     calmar_ratio=1.5,   # Worse
        ...     max_drawdown=-0.12,
        ...     total_return=0.45,
        ...     win_rate=0.58,
        ...     annual_return=0.19,
        ...     success=True
        ... )
        >>> m4 = MultiObjectiveMetrics(
        ...     sharpe_ratio=1.4,   # Worse
        ...     calmar_ratio=2.2,   # Better
        ...     max_drawdown=-0.11,
        ...     total_return=0.48,
        ...     win_rate=0.59,
        ...     annual_return=0.21,
        ...     success=True
        ... )
        >>> pareto_dominates(m3, m4)  # Neither dominates
        False
        >>> pareto_dominates(m4, m3)
        False

    Example (Failed Backtests):
        >>> m_success = MultiObjectiveMetrics(1.5, 2.0, -0.10, 0.50, 0.60, 0.20, success=True)
        >>> m_failed = MultiObjectiveMetrics(1.2, 1.8, -0.20, 0.40, 0.55, 0.18, success=False)
        >>> pareto_dominates(m_success, m_failed)  # Success cannot dominate failure
        False
        >>> pareto_dominates(m_failed, m_success)  # Failure cannot dominate
        False

    Notes:
        - Failed backtests (success=False) are never dominant and cannot be dominated
        - Requires strict improvement in at least one objective
        - Used in NSGA-II non-dominated sorting and Pareto front identification
        - For max_drawdown: -0.10 > -0.20 (less negative is better)
        - Dominance is not symmetric: if A dominates B, then B does not dominate A
        - Two solutions can be non-dominated (neither dominates the other)

    References:
        - Deb, K., et al. (2002). "A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II"
        - IEEE Transactions on Evolutionary Computation, 6(2), 182-197
    """
    # Failed backtests cannot dominate or be dominated
    if not metrics_a.success or not metrics_b.success:
        return False

    # Check if metrics_a is at least as good in all objectives
    at_least_as_good = (
        metrics_a.sharpe_ratio >= metrics_b.sharpe_ratio and
        metrics_a.calmar_ratio >= metrics_b.calmar_ratio and
        metrics_a.max_drawdown >= metrics_b.max_drawdown and  # Less negative is better
        metrics_a.total_return >= metrics_b.total_return and
        metrics_a.win_rate >= metrics_b.win_rate and
        metrics_a.annual_return >= metrics_b.annual_return
    )

    # Check if metrics_a is strictly better in at least one objective
    strictly_better = (
        metrics_a.sharpe_ratio > metrics_b.sharpe_ratio or
        metrics_a.calmar_ratio > metrics_b.calmar_ratio or
        metrics_a.max_drawdown > metrics_b.max_drawdown or  # Less negative is better
        metrics_a.total_return > metrics_b.total_return or
        metrics_a.win_rate > metrics_b.win_rate or
        metrics_a.annual_return > metrics_b.annual_return
    )

    # Pareto dominance requires both conditions
    return at_least_as_good and strictly_better



def calculate_pareto_front(population: List[Strategy]) -> List[Strategy]:
    """
    Identify the Pareto optimal front from a population of strategies.

    Uses brute-force pairwise comparison to find all non-dominated strategies.
    A strategy is non-dominated if no other strategy dominates it according to
    Pareto dominance criteria across all objectives.

    Algorithm:
        1. Filter out unevaluated strategies (metrics=None)
        2. For each strategy, check if any other strategy dominates it
        3. If no strategy dominates it, add it to the Pareto front
        4. Return all non-dominated strategies

    Time Complexity: O(n²·m) where n is population size, m is number of objectives
    Space Complexity: O(n) for the result list

    Args:
        population: List of Strategy instances to analyze

    Returns:
        List[Strategy]: Non-dominated strategies forming the Pareto front.
                       Empty list if no evaluated strategies exist.

    Example:
        >>> from src.evolution.types import Strategy, MultiObjectiveMetrics
        >>> strategies = [
        ...     Strategy(
        ...         metrics=MultiObjectiveMetrics(
        ...             sharpe_ratio=1.5, calmar_ratio=2.0,
        ...             max_drawdown=-0.10, total_return=0.50,
        ...             win_rate=0.60, annual_return=0.20, success=True
        ...         )
        ...     ),
        ...     Strategy(
        ...         metrics=MultiObjectiveMetrics(
        ...             sharpe_ratio=1.2, calmar_ratio=1.8,
        ...             max_drawdown=-0.15, total_return=0.40,
        ...             win_rate=0.55, annual_return=0.18, success=True
        ...         )
        ...     ),
        ...     Strategy(metrics=None)  # Unevaluated strategy
        ... ]
        >>> pareto_front = calculate_pareto_front(strategies)
        >>> len(pareto_front)
        1
        >>> pareto_front[0].metrics.sharpe_ratio
        1.5

    Notes:
        - Strategies with metrics=None are filtered out before analysis
        - Failed backtests (metrics.success=False) are excluded
        - For n=20-50 strategies, O(n²) is acceptable performance
        - Returns empty list if all strategies are unevaluated
        - Used in NSGA-II selection and population analysis
    """
    # Filter out unevaluated strategies and failed backtests
    evaluated = [s for s in population if s.metrics is not None and s.metrics.success]

    # Empty population or no evaluated strategies
    if not evaluated:
        return []

    pareto_front = []

    # Check each strategy for dominance
    for candidate in evaluated:
        is_dominated = False

        # Check if any other strategy dominates this candidate
        for other in evaluated:
            if other is candidate:
                continue

            # If other dominates candidate, candidate is not in Pareto front
            if other.dominates(candidate):
                is_dominated = True
                break

        # If no strategy dominates this candidate, it's in the Pareto front
        if not is_dominated:
            pareto_front.append(candidate)

    return pareto_front


def assign_pareto_ranks(population: List[Strategy]) -> Dict[str, int]:
    """
    Assign Pareto ranks to all strategies using NSGA-II fast non-dominated sorting.

    Implements the fast non-dominated sorting algorithm from NSGA-II (Deb et al., 2002).
    Strategies are assigned ranks where:
    - Rank 1: Pareto front (non-dominated strategies)
    - Rank 2: Dominated only by rank 1 strategies
    - Rank 3+: Dominated by higher-ranked strategies
    - Rank 0: Invalid (no metrics or failed backtest)

    Algorithm Steps:
    ===============
    1. Initialize domination tracking:
       - For each strategy, count how many strategies dominate it (domination_count)
       - Track which strategies it dominates (dominated_set)

    2. Find Rank 1 (Pareto front):
       - Identify all strategies with domination_count = 0
       - These are non-dominated strategies

    3. Iteratively find subsequent ranks:
       - For each strategy in current rank:
         * For each strategy it dominates, decrement its domination_count
         * If domination_count reaches 0, add to next rank
       - Repeat until all strategies are ranked

    Mathematical Definition:
    =======================
    For strategy i, its Pareto rank R(i) is defined as:
        R(i) = 1 + max{R(j) : j dominates i}

    Where:
        - R(i) = 1 if no strategy dominates i (Pareto front)
        - R(i) = 0 if strategy has no metrics or failed evaluation (invalid)
        - Lower rank is better (rank 1 is best)

    Domination Relationship:
    ========================
    Strategy A dominates strategy B if:
        - A is at least as good as B in all objectives
        - A is strictly better than B in at least one objective

    Time Complexity: O(MN²) where M is number of objectives (6), N is population size
    Space Complexity: O(N²) worst case for dominated sets

    Args:
        population: List of Strategy instances to rank

    Returns:
        Dict[str, int]: Mapping of strategy_id to Pareto rank (0, 1, 2, 3, ...)
                       Rank 0 indicates invalid strategy (no metrics or failed)
                       Rank 1 is best (Pareto front), higher ranks are worse

    Example:
        >>> from src.evolution.types import Strategy, MultiObjectiveMetrics
        >>> strategies = [
        ...     Strategy(
        ...         id='s1',
        ...         metrics=MultiObjectiveMetrics(
        ...             sharpe_ratio=1.5, calmar_ratio=2.0,
        ...             max_drawdown=-0.10, total_return=0.50,
        ...             win_rate=0.60, annual_return=0.20, success=True
        ...         )
        ...     ),
        ...     Strategy(
        ...         id='s2',
        ...         metrics=MultiObjectiveMetrics(
        ...             sharpe_ratio=1.2, calmar_ratio=1.8,
        ...             max_drawdown=-0.15, total_return=0.40,
        ...             win_rate=0.55, annual_return=0.18, success=True
        ...         )
        ...     ),
        ...     Strategy(id='s3', metrics=None)  # No metrics
        ... ]
        >>> ranks = assign_pareto_ranks(strategies)
        >>> ranks['s1']  # s1 on Pareto front (dominates s2)
        1
        >>> ranks['s2']  # s2 dominated by s1
        2
        >>> ranks['s3']  # s3 has no metrics
        0

    Notes:
        - Strategies without metrics are assigned rank 0 (invalid)
        - Failed backtests (success=False) are assigned rank 0
        - Lower rank is better (rank 1 is best, Pareto optimal)
        - Used in NSGA-II tournament selection to favor better ranks
        - Crowding distance is used to break ties within same rank
        - Reference: Deb, K., et al. (2002). "A fast and elitist multiobjective
          genetic algorithm: NSGA-II". IEEE Transactions on Evolutionary Computation, 6(2), 182-197.
    """
    # Initialize result dictionary with all strategy IDs
    ranks: Dict[str, int] = {}

    # Filter valid strategies (with metrics and successful backtests)
    valid_strategies = [
        s for s in population
        if s.metrics is not None and s.metrics.success
    ]

    # Assign rank 0 to invalid strategies (no metrics or failed backtests)
    for strategy in population:
        if strategy.metrics is None or not strategy.metrics.success:
            ranks[strategy.id] = 0

    # Handle empty population or no valid strategies
    if not valid_strategies:
        return ranks

    # Step 1: Initialize domination tracking structures
    # domination_count[id] = number of strategies that dominate this strategy
    # dominated_set[id] = list of strategies that this strategy dominates
    domination_count: Dict[str, int] = {}
    dominated_set: Dict[str, List[Strategy]] = {}

    # Initialize tracking structures for all valid strategies
    for strategy in valid_strategies:
        domination_count[strategy.id] = 0
        dominated_set[strategy.id] = []

    # Calculate domination relationships between all pairs
    for i, strategy_i in enumerate(valid_strategies):
        for j, strategy_j in enumerate(valid_strategies):
            # Skip self-comparison
            if i == j:
                continue

            # Check if strategy_i dominates strategy_j
            if strategy_i.dominates(strategy_j):
                # strategy_i dominates strategy_j
                # Add strategy_j to the set of strategies dominated by strategy_i
                dominated_set[strategy_i.id].append(strategy_j)
            elif strategy_j.dominates(strategy_i):
                # strategy_j dominates strategy_i
                # Increment the count of strategies that dominate strategy_i
                domination_count[strategy_i.id] += 1

    # Step 2: Find Rank 1 (Pareto front) - strategies with domination_count = 0
    current_rank = 1
    current_front = [
        s for s in valid_strategies
        if domination_count[s.id] == 0
    ]

    # Step 3: Iteratively assign ranks to all strategies
    while current_front:
        # Assign current rank to all strategies in current front
        for strategy in current_front:
            ranks[strategy.id] = current_rank

        # Prepare next front by processing strategies dominated by current front
        next_front = []
        for strategy in current_front:
            # For each strategy dominated by this strategy
            for dominated_strategy in dominated_set[strategy.id]:
                # Decrement its domination count (remove this dominator)
                domination_count[dominated_strategy.id] -= 1

                # If domination count reaches 0, it belongs to next front
                if domination_count[dominated_strategy.id] == 0:
                    # Avoid duplicates (strategy might be dominated by multiple strategies in current front)
                    if dominated_strategy not in next_front:
                        next_front.append(dominated_strategy)

        # Move to next rank level
        current_rank += 1
        current_front = next_front

    return ranks


def calculate_crowding_distance(strategies: List[Strategy]) -> Dict[str, float]:
    """
    Calculate NSGA-II crowding distance for diversity maintenance on Pareto front.

    The crowding distance is a density estimation metric that measures how close an
    individual is to its neighbors in the objective space. It promotes diversity by
    preferring solutions in less crowded regions of the Pareto front during selection.

    Algorithm (NSGA-II Crowding Distance):
    ======================================
    1. Initialize all crowding distances to 0
    2. For each objective (Sharpe, Calmar, Max Drawdown, etc.):
        a. Sort strategies by objective value (ascending)
        b. Assign infinite distance to boundary solutions (best and worst)
        c. For each interior solution i:
            distance[i] += (objective[i+1] - objective[i-1]) / (max - min)
    3. Sum distances across all objectives to get final crowding distance
    4. Boundary solutions have infinite distance (always preserved)

    Mathematical Definition:
    -----------------------
    For strategy i and objective m:
        crowding_distance[i] = Σ_m [(f_m[i+1] - f_m[i-1]) / (f_m_max - f_m_min)]

    Where:
        - f_m[i]: Value of objective m for strategy i
        - f_m_max, f_m_min: Maximum and minimum values for objective m
        - Boundary solutions (i=0, i=n-1) get infinite distance

    Properties:
    -----------
    - Boundary preservation: Edge solutions always have infinite distance
    - Scale normalization: Each objective normalized to [0, 1] range
    - Additive aggregation: Sum distances across all objectives
    - Higher is better: Larger distance indicates less crowding

    Objectives Used:
    ---------------
    All objectives from MultiObjectiveMetrics (6 total):
        1. sharpe_ratio: Risk-adjusted return (higher is better)
        2. calmar_ratio: Return / max drawdown (higher is better)
        3. max_drawdown: Peak-to-trough decline (less negative is better)
        4. total_return: Cumulative return (higher is better)
        5. win_rate: Percentage of winning trades (higher is better)
        6. annual_return: Annualized return (higher is better)

    Args:
        strategies: List of Strategy objects to calculate crowding distance for.
                   All strategies should have evaluated metrics (metrics not None).
                   Typically, this is a single Pareto front (all non-dominated strategies).

    Returns:
        Dict[str, float]: Mapping from strategy ID to crowding distance.
                         Boundary strategies have distance = float('inf').
                         Interior strategies have distance ≥ 0.0.

    Raises:
        ValueError: If strategies list is empty or has fewer than 2 strategies.
        ValueError: If any strategy lacks evaluated metrics (metrics is None).

    Example:
        >>> from src.evolution.types import Strategy, MultiObjectiveMetrics
        >>>
        >>> # Create strategies with different metrics
        >>> s1 = Strategy(
        ...     id='strat_1',
        ...     metrics=MultiObjectiveMetrics(
        ...         sharpe_ratio=1.5, calmar_ratio=2.0, max_drawdown=-0.10,
        ...         total_return=0.50, win_rate=0.60, annual_return=0.20, success=True
        ...     )
        ... )
        >>> s2 = Strategy(
        ...     id='strat_2',
        ...     metrics=MultiObjectiveMetrics(
        ...         sharpe_ratio=1.2, calmar_ratio=1.8, max_drawdown=-0.15,
        ...         total_return=0.40, win_rate=0.55, annual_return=0.18, success=True
        ...     )
        ... )
        >>> s3 = Strategy(
        ...     id='strat_3',
        ...     metrics=MultiObjectiveMetrics(
        ...         sharpe_ratio=1.8, calmar_ratio=2.2, max_drawdown=-0.12,
        ...         total_return=0.55, win_rate=0.62, annual_return=0.22, success=True
        ...     )
        ... )
        >>>
        >>> # Calculate crowding distances
        >>> distances = calculate_crowding_distance([s1, s2, s3])
        >>>
        >>> # Boundary solutions have infinite distance
        >>> distances['strat_1'] == float('inf')  # Best in some objectives
        True
        >>> distances['strat_3'] == float('inf')  # Best in other objectives
        True
        >>>
        >>> # Interior solution has finite distance
        >>> 0.0 < distances['strat_2'] < float('inf')
        True

    Notes:
        - Designed for single Pareto front (non-dominated strategies)
        - Can handle any number of strategies ≥ 2
        - Boundary solutions (best/worst in each objective) get infinite distance
        - Used in NSGA-II selection to maintain diversity
        - Higher crowding distance = less crowded = more likely to be selected
        - Failed evaluations (metrics.success=False) are excluded from calculation

    Complexity:
        - Time: O(M * N * log(N)) where M=objectives, N=strategies
        - Space: O(M * N) for sorting and distance storage

    References:
        Deb, K., et al. (2002). NSGA-II Section 3.2: "Crowding-distance assignment"
        IEEE Transactions on Evolutionary Computation, 6(2), 182-197.
    """
    # Validation: Check for empty or insufficient strategies
    if not strategies:
        raise ValueError("Cannot calculate crowding distance: strategies list is empty")

    if len(strategies) < 2:
        raise ValueError(
            f"Cannot calculate crowding distance: need at least 2 strategies, got {len(strategies)}"
        )

    # Filter out strategies without metrics or failed evaluations
    valid_strategies = [s for s in strategies if s.metrics and s.metrics.success]

    if not valid_strategies:
        raise ValueError(
            "Cannot calculate crowding distance: no strategies with successful evaluations"
        )

    if len(valid_strategies) < 2:
        raise ValueError(
            f"Cannot calculate crowding distance: only {len(valid_strategies)} strategy "
            f"with successful evaluation, need at least 2"
        )

    # Initialize crowding distances to 0 for all valid strategies
    distances: Dict[str, float] = {s.id: 0.0 for s in valid_strategies}

    # Define all objectives to consider (all metrics from MultiObjectiveMetrics)
    # Each objective is a tuple of (attribute_name, maximize_flag)
    # maximize_flag=True means higher is better, False means lower is better
    objectives = [
        ('sharpe_ratio', True),      # Higher is better
        ('calmar_ratio', True),      # Higher is better
        ('max_drawdown', True),      # Less negative is better (so we maximize)
        ('total_return', True),      # Higher is better
        ('win_rate', True),          # Higher is better
        ('annual_return', True),     # Higher is better
    ]

    # Calculate crowding distance for each objective
    for objective_name, maximize in objectives:
        # Sort strategies by current objective value
        sorted_strategies = sorted(
            valid_strategies,
            key=lambda s: getattr(s.metrics, objective_name),
            reverse=False  # Always sort ascending (smallest to largest)
        )

        # Get objective values for normalization
        objective_values = [getattr(s.metrics, objective_name) for s in sorted_strategies]
        obj_min = min(objective_values)
        obj_max = max(objective_values)
        obj_range = obj_max - obj_min

        # Handle edge case: all strategies have same value for this objective
        if obj_range == 0:
            # No diversity in this objective, skip (all distances remain unchanged)
            continue

        # Assign infinite distance to boundary solutions (best and worst)
        # Boundary solutions are always preserved in NSGA-II selection
        distances[sorted_strategies[0].id] = float('inf')   # Worst solution
        distances[sorted_strategies[-1].id] = float('inf')  # Best solution

        # Calculate distance for interior solutions
        for i in range(1, len(sorted_strategies) - 1):
            prev_value = getattr(sorted_strategies[i - 1].metrics, objective_name)
            next_value = getattr(sorted_strategies[i + 1].metrics, objective_name)

            # Normalized distance: (next - prev) / (max - min)
            # This scales the distance to [0, 1] range for each objective
            normalized_distance = (next_value - prev_value) / obj_range

            # Add to cumulative crowding distance (sum across all objectives)
            # If distance is already infinite (from another objective), keep it infinite
            if distances[sorted_strategies[i].id] != float('inf'):
                distances[sorted_strategies[i].id] += normalized_distance

    return distances
