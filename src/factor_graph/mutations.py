"""
Factor Mutation Operators Module
=================================

Implements Tier 2 structural mutations for Strategy DAG:
- add_factor(): Intelligently add factors with automatic dependency resolution
- remove_factor(): Safe factor removal with dependency checking and cascade support
- replace_factor(): Swap factors while preserving dependencies

Architecture: Phase 2.0+ Factor Graph System
Tasks: C.1 - add_factor(), C.2 - remove_factor() Mutation Operators

Core Features:
-------------
1. Smart Insertion: Category-aware positioning (ENTRY → MOMENTUM/VALUE → EXIT)
2. Auto-Dependencies: Automatic dependency resolution based on inputs/outputs
3. Multiple Strategies: Root, after-factor, leaf, and smart insertion modes
4. Safe Removal: Dependency checking with cascade support
5. Validation: Cycle prevention, dependency checking, DAG integrity
6. Pure Functions: Return new strategies, preserve originals

Insertion Strategies:
--------------------
- Root Insertion: Add factor with no dependencies (root factor)
- After-Factor Insertion: Add factor after specified factor
- Leaf Insertion: Add factor at end, depending on all leaf factors
- Smart Insertion: Auto-determine optimal location based on category

Removal Strategies:
------------------
- Safe Removal: Only remove factors with no dependents (default)
- Cascade Removal: Remove factor and all dependent factors
- Signal Protection: Cannot remove only signal-producing factor

Category-Aware Positioning:
--------------------------
ENTRY factors → near roots (early in pipeline)
MOMENTUM/VALUE/QUALITY → middle layers (feature calculation)
EXIT factors → near leaves (late in pipeline)
RISK factors → depends on positions, typically mid-to-late
SIGNAL factors → final aggregation layers

Example Usage:
-------------
    from src.factor_graph.mutations import add_factor, remove_factor
    from src.factor_library.registry import FactorRegistry

    registry = FactorRegistry.get_instance()

    # Add exit factor at end of strategy
    mutated = add_factor(
        strategy=original_strategy,
        factor_name="trailing_stop_factor",
        parameters={"trail_percent": 0.10},
        insert_point="leaf"
    )

    # Safe removal (fails if dependents exist)
    mutated = remove_factor(
        strategy=original_strategy,
        factor_id="old_exit_factor",
        cascade=False
    )

    # Cascade removal (removes dependents too)
    mutated = remove_factor(
        strategy=original_strategy,
        factor_id="old_momentum_factor",
        cascade=True
    )
"""

from typing import Dict, Any, List, Optional
import copy

from .factor import Factor
from .factor_category import FactorCategory
from .strategy import Strategy
from src.factor_library.registry import FactorRegistry


def add_factor(
    strategy: Strategy,
    factor_name: str,
    parameters: Optional[Dict[str, Any]] = None,
    insert_point: str = "smart"
) -> Strategy:
    """
    Add factor to strategy with intelligent insertion and dependency resolution.

    This function implements Tier 2 structural mutation by adding a new factor
    to an existing strategy. It supports multiple insertion strategies (root,
    after, leaf, smart) and automatically resolves dependencies based on the
    factor's inputs and the strategy's existing outputs.

    The function is pure - it returns a new strategy and does not modify the
    original strategy.

    Args:
        strategy: Strategy to mutate (not modified)
        factor_name: Factor name from registry (e.g., "momentum_factor")
        parameters: Factor parameters (uses registry defaults if not provided)
        insert_point: Where to insert factor, one of:
            - "root": Add as root factor (no dependencies)
            - "leaf": Add at end (depends on all leaf factors)
            - "smart": Auto-determine optimal location (default)
            - <factor_id>: Add after specified factor

    Returns:
        New Strategy with factor added (original strategy unchanged)

    Raises:
        ValueError: If factor not found in registry
        ValueError: If parameters invalid
        ValueError: If insert_point factor not found
        ValueError: If adding factor would create cycle
        ValueError: If factor inputs cannot be satisfied

    Example:
        >>> from src.factor_graph.mutations import add_factor
        >>> from src.factor_library.registry import FactorRegistry
        >>>
        >>> # Load registry and strategy
        >>> registry = FactorRegistry.get_instance()
        >>> original = load_momentum_strategy()
        >>>
        >>> # Add trailing stop exit factor at end
        >>> mutated = add_factor(
        ...     strategy=original,
        ...     factor_name="trailing_stop_factor",
        ...     parameters={"trail_percent": 0.10, "activation_profit": 0.05},
        ...     insert_point="leaf"
        ... )
        >>>
        >>> # Validate and execute
        >>> mutated.validate()
        True
        >>> result = mutated.to_pipeline(data)

    Design Notes:
        - Returns new strategy (pure function, no side effects)
        - Validates parameters before creation
        - Automatically resolves dependencies based on inputs/outputs
        - Prevents cycles through DAG validation
        - Category-aware smart insertion
        - Performance: <10ms for typical operations
    """
    # Get factor registry
    registry = FactorRegistry.get_instance()

    # Validate factor exists in registry
    if not registry.get_factor(factor_name):
        available = registry.list_factors()
        raise ValueError(
            f"Factor '{factor_name}' not found in registry. "
            f"Available factors: {available}"
        )

    # Create factor instance with parameters
    try:
        new_factor = registry.create_factor(factor_name, parameters)
    except ValueError as e:
        raise ValueError(f"Failed to create factor '{factor_name}': {str(e)}") from e

    # Create copy of strategy for mutation
    mutated_strategy = strategy.copy()

    # Resolve dependencies based on insert_point
    dependencies = _resolve_dependencies(
        mutated_strategy,
        new_factor,
        insert_point
    )

    # Add factor to strategy with dependencies
    try:
        mutated_strategy.add_factor(new_factor, depends_on=dependencies)
    except ValueError as e:
        raise ValueError(
            f"Failed to add factor '{factor_name}' to strategy: {str(e)}"
        ) from e

    return mutated_strategy


def _resolve_dependencies(
    strategy: Strategy,
    new_factor: Factor,
    insert_point: str
) -> List[str]:
    """
    Resolve dependencies for new factor based on insertion strategy.

    This internal function determines which existing factors the new factor
    should depend on, based on:
    1. The insertion strategy (root, after, leaf, smart)
    2. The new factor's input requirements
    3. The existing factors' output availability
    4. Category-aware positioning for smart insertion

    Args:
        strategy: Existing strategy (for dependency analysis)
        new_factor: New factor to add
        insert_point: Insertion strategy ("root", "leaf", "smart", or factor_id)

    Returns:
        List of factor IDs that new_factor should depend on

    Raises:
        ValueError: If insert_point factor not found
        ValueError: If required inputs cannot be satisfied
    """
    # Root insertion: no dependencies
    if insert_point == "root":
        return []

    # Leaf insertion: depend on all current leaf factors
    if insert_point == "leaf":
        return _get_leaf_factors(strategy)

    # Smart insertion: determine optimal location based on category and inputs
    if insert_point == "smart":
        return _smart_insertion(strategy, new_factor)

    # After-factor insertion: depend on specified factor
    if insert_point in strategy.factors:
        return [insert_point]

    # Invalid insert_point
    raise ValueError(
        f"Invalid insert_point '{insert_point}'. "
        f"Must be 'root', 'leaf', 'smart', or an existing factor ID. "
        f"Available factors: {list(strategy.factors.keys())}"
    )


def _get_leaf_factors(strategy: Strategy) -> List[str]:
    """
    Get all leaf factors (factors with no dependents) in strategy.

    Args:
        strategy: Strategy to analyze

    Returns:
        List of factor IDs that are leaves (have no successors in DAG)
    """
    if not strategy.factors:
        return []

    leaf_factors = []
    for factor_id in strategy.factors.keys():
        # Leaf factors have no successors (no factors depend on them)
        successors = list(strategy.dag.successors(factor_id))
        if not successors:
            leaf_factors.append(factor_id)

    return leaf_factors


def _smart_insertion(strategy: Strategy, new_factor: Factor) -> List[str]:
    """
    Determine optimal insertion point based on factor category and inputs.

    Smart insertion uses the following logic:
    1. Find all factors that provide the new factor's required inputs
    2. Apply category-aware positioning rules:
       - ENTRY factors: early in pipeline (near roots)
       - MOMENTUM/VALUE/QUALITY: middle layers
       - EXIT factors: late in pipeline (near leaves)
       - RISK factors: mid-to-late (after positions available)
    3. Choose optimal dependencies that respect natural factor ordering

    Args:
        strategy: Existing strategy
        new_factor: New factor to add

    Returns:
        List of factor IDs that new_factor should depend on

    Raises:
        ValueError: If required inputs cannot be satisfied by any factors
    """
    # Identify factors that provide required inputs
    available_inputs = {"open", "high", "low", "close", "volume"}  # Base data
    candidate_dependencies = []

    # Traverse factors in topological order to build available inputs
    factors_in_order = strategy.get_factors()

    for factor in factors_in_order:
        # Check if this factor provides any required inputs
        provides_required = any(
            output in new_factor.inputs
            for output in factor.outputs
        )

        if provides_required:
            candidate_dependencies.append(factor.id)

        # Add this factor's outputs to available inputs
        available_inputs.update(factor.outputs)

    # Validate all required inputs can be satisfied
    missing_inputs = [
        inp for inp in new_factor.inputs
        if inp not in available_inputs
    ]

    if missing_inputs:
        raise ValueError(
            f"Cannot add factor '{new_factor.id}': "
            f"required inputs {missing_inputs} are not available. "
            f"Available inputs: {sorted(available_inputs)}"
        )

    # Apply category-aware positioning
    dependencies = _apply_category_rules(
        strategy,
        new_factor,
        candidate_dependencies
    )

    return dependencies


def _apply_category_rules(
    strategy: Strategy,
    new_factor: Factor,
    candidate_dependencies: List[str]
) -> List[str]:
    """
    Apply category-aware positioning rules for smart insertion.

    Category positioning rules:
    - ENTRY: Depend on root factors (early pipeline entry)
    - MOMENTUM/VALUE/QUALITY: Depend on immediate providers (middle layers)
    - EXIT: Depend on all candidates (late pipeline aggregation)
    - RISK: Depend on position-producing factors (mid-to-late)
    - SIGNAL: Depend on all candidates (final aggregation)

    Args:
        strategy: Existing strategy
        new_factor: New factor to add
        candidate_dependencies: Factors that could provide required inputs

    Returns:
        Filtered list of dependencies based on category rules
    """
    category = new_factor.category

    # ENTRY factors: depend on minimal inputs (early in pipeline)
    if category == FactorCategory.ENTRY:
        # Only depend on base data if possible, otherwise first candidate
        if not candidate_dependencies:
            return []  # Root factor
        return [candidate_dependencies[0]]

    # EXIT factors: depend on all candidates (need complete signal information)
    if category == FactorCategory.EXIT:
        return candidate_dependencies

    # SIGNAL factors: depend on all candidates (final aggregation)
    if category == FactorCategory.SIGNAL:
        return candidate_dependencies

    # RISK factors: depend on position-producing factors
    if category == FactorCategory.RISK:
        position_factors = [
            fid for fid in candidate_dependencies
            if any(
                output in {"positions", "position", "signal", "signals"}
                for output in strategy.factors[fid].outputs
            )
        ]
        # If no position factors, use all candidates
        return position_factors if position_factors else candidate_dependencies

    # MOMENTUM/VALUE/QUALITY: depend on immediate providers (middle layers)
    # Use all candidates that directly provide required inputs
    return candidate_dependencies


def remove_factor(
    strategy: Strategy,
    factor_id: str,
    cascade: bool = False
) -> Strategy:
    """
    Remove factor from strategy with dependency checking and optional cascade.

    This function implements safe factor removal with comprehensive dependency
    checking. It supports two removal modes:

    1. Safe Removal (cascade=False, default): Only removes factors with no
       dependents. Raises error if removal would orphan other factors.

    2. Cascade Removal (cascade=True): Removes factor and all dependent factors
       recursively. Useful for removing entire factor chains.

    The function validates that the resulting strategy still produces position
    signals and maintains DAG integrity.

    Args:
        strategy: Strategy to mutate (not modified)
        factor_id: ID of factor to remove
        cascade: If True, also remove dependent factors; if False, raise error
                if dependents exist (default: False for safety)

    Returns:
        New Strategy with factor removed (original strategy unchanged)

    Raises:
        ValueError: If factor not found
        ValueError: If removing factor would orphan dependents (cascade=False)
        ValueError: If removing factor would eliminate all position signals
        ValueError: If resulting strategy would be invalid

    Example:
        >>> from src.factor_graph.mutations import remove_factor
        >>>
        >>> # Safe removal (fails if dependents exist)
        >>> try:
        ...     mutated = remove_factor(
        ...         strategy=original,
        ...         factor_id="ma_filter_20",
        ...         cascade=False
        ...     )
        ... except ValueError as e:
        ...     print(f"Cannot remove: {e}")
        >>>
        >>> # Cascade removal (removes dependents too)
        >>> mutated = remove_factor(
        ...     strategy=original,
        ...     factor_id="ma_filter_20",
        ...     cascade=True
        ... )
        >>>
        >>> # Validate result
        >>> mutated.validate()
        True

    Design Notes:
        - Returns new strategy (pure function, no side effects)
        - Default safe mode (cascade=False) prevents accidental orphans
        - Cascade mode removes entire subtrees of dependent factors
        - Validates resulting strategy still produces position signals
        - Cannot remove only signal-producing factor
        - Performance: <5ms for typical operations
    """
    # Validate factor exists
    if factor_id not in strategy.factors:
        raise ValueError(
            f"Factor '{factor_id}' not found in strategy. "
            f"Available factors: {list(strategy.factors.keys())}"
        )

    # Check if this is the only position signal producer
    position_columns = {"positions", "position", "signal", "signals"}
    factor_to_remove = strategy.factors[factor_id]

    # Check if removing factor produces position signals
    produces_positions = any(
        output in position_columns
        for output in factor_to_remove.outputs
    )

    # If it does, check if there are other position signal producers
    if produces_positions:
        # Get all factors that would remain after removal
        if cascade:
            # With cascade, find all factors that won't be removed
            factors_to_remove_set = set(_get_transitive_dependents(strategy, factor_id))
            remaining_factors = [
                (fid, factor) for fid, factor in strategy.factors.items()
                if fid not in factors_to_remove_set
            ]
        else:
            # Without cascade, all other factors remain
            remaining_factors = [
                (fid, factor) for fid, factor in strategy.factors.items()
                if fid != factor_id
            ]

        # Check if any remaining factors produce position signals
        other_position_producers = [
            fid for fid, factor in remaining_factors
            if any(output in position_columns for output in factor.outputs)
        ]

        if not other_position_producers:
            raise ValueError(
                f"Cannot remove factor '{factor_id}': it is the only factor "
                f"producing position signals. A valid trading strategy must have "
                f"at least one factor producing position signals (columns: {sorted(position_columns)}). "
                "Add another signal-producing factor before removing this one."
            )

    # Get dependent factors (factors that depend on this factor's outputs)
    dependents = list(strategy.dag.successors(factor_id))

    # Safe removal: error if dependents exist
    if not cascade and dependents:
        raise ValueError(
            f"Cannot remove factor '{factor_id}': "
            f"factors {dependents} depend on its outputs. "
            f"Either remove dependent factors first, or use cascade=True to "
            f"remove all dependent factors automatically."
        )

    # Create copy of strategy for mutation
    mutated_strategy = strategy.copy()

    # Cascade removal: recursively remove all dependents first
    if cascade and dependents:
        # Build complete set of factors to remove (factor + all transitive dependents)
        factors_to_remove = _get_transitive_dependents(mutated_strategy, factor_id)

        # Remove in reverse topological order (leaves first)
        removal_order = _get_removal_order(mutated_strategy, factors_to_remove)

        for fid in removal_order:
            # Use Strategy.remove_factor which validates no dependents
            try:
                mutated_strategy.remove_factor(fid)
            except ValueError as e:
                # This should not happen if we computed removal order correctly
                raise RuntimeError(
                    f"Cascade removal failed at factor '{fid}': {str(e)}. "
                    "This is likely a bug in removal order computation."
                ) from e

    else:
        # Simple removal (no dependents or cascade not needed)
        try:
            mutated_strategy.remove_factor(factor_id)
        except ValueError as e:
            raise ValueError(
                f"Failed to remove factor '{factor_id}': {str(e)}"
            ) from e

    # Validate resulting strategy (skip if empty - this is allowed for testing)
    if len(mutated_strategy.factors) > 0:
        try:
            mutated_strategy.validate()
        except ValueError as e:
            raise ValueError(
                f"Removing factor '{factor_id}' resulted in invalid strategy: {str(e)}. "
                "This may indicate missing dependencies or orphaned factors."
            ) from e

    return mutated_strategy


def _get_transitive_dependents(strategy: Strategy, factor_id: str) -> List[str]:
    """
    Get all factors that transitively depend on the given factor.

    This includes direct dependents and all factors that depend on them
    (recursive transitive closure).

    Args:
        strategy: Strategy to analyze
        factor_id: Root factor ID

    Returns:
        List of factor IDs including root and all transitive dependents
    """
    result = [factor_id]
    visited = {factor_id}

    # BFS to find all transitive dependents
    queue = [factor_id]
    while queue:
        current = queue.pop(0)
        dependents = list(strategy.dag.successors(current))

        for dependent in dependents:
            if dependent not in visited:
                visited.add(dependent)
                result.append(dependent)
                queue.append(dependent)

    return result


def _get_removal_order(strategy: Strategy, factors_to_remove: List[str]) -> List[str]:
    """
    Compute removal order for factors (reverse topological, leaves first).

    Args:
        strategy: Strategy to analyze
        factors_to_remove: Factors to be removed

    Returns:
        List of factor IDs in removal order (leaves first, roots last)
    """
    import networkx as nx

    # Create subgraph containing only factors to remove
    subgraph = strategy.dag.subgraph(factors_to_remove)

    # Get topological order (roots to leaves)
    try:
        topo_order = list(nx.topological_sort(subgraph))
    except nx.NetworkXError as e:
        raise ValueError(f"Failed to compute removal order: {str(e)}") from e

    # Reverse to get leaves-first order
    return list(reversed(topo_order))


def replace_factor(
    strategy: Strategy,
    old_factor_id: str,
    new_factor_name: str,
    parameters: Optional[Dict[str, Any]] = None,
    match_category: bool = True
) -> Strategy:
    """
    Replace factor with compatible alternative while preserving DAG structure.

    This function implements factor replacement by swapping one factor with another
    while maintaining the DAG topology and dependencies. It's more surgical than
    remove+add and better preserves the strategy structure.

    The function supports two replacement modes:
    1. Same-Category Replacement (match_category=True, default): Ensures semantic
       consistency by only allowing factors from the same category.
    2. Compatible Replacement (match_category=False): Allows any factor with
       compatible inputs/outputs, enabling more flexible mutations.

    Replacement Process:
    1. Validate old factor exists and new factor available in registry
    2. Create new factor instance with provided parameters
    3. Check category match if required (match_category=True)
    4. Validate input/output compatibility with existing dependencies
    5. Preserve all incoming edges (factors that old factor depends on)
    6. Preserve all outgoing edges (factors that depend on old factor)
    7. Remove old factor and add new factor with same dependencies
    8. Validate resulting strategy

    Args:
        strategy: Strategy to mutate (not modified)
        old_factor_id: ID of factor to replace
        new_factor_name: Name of replacement factor from registry
        parameters: Parameters for new factor (uses defaults if None)
        match_category: If True, validate new factor is same category as old
            (default: True for semantic consistency)

    Returns:
        New Strategy with factor replaced (original strategy unchanged)

    Raises:
        ValueError: If old factor not found in strategy
        ValueError: If new factor not found in registry
        ValueError: If match_category=True and categories don't match
        ValueError: If new factor has incompatible inputs (cannot be satisfied)
        ValueError: If new factor has incompatible outputs (dependents need them)
        ValueError: If resulting strategy would be invalid

    Example:
        >>> from src.factor_graph.mutations import replace_factor
        >>> from src.factor_library.registry import FactorRegistry
        >>>
        >>> # Load strategy
        >>> strategy = load_momentum_strategy()
        >>>
        >>> # Replace momentum factor with MA filter (same category)
        >>> mutated = replace_factor(
        ...     strategy=strategy,
        ...     old_factor_id="momentum_20",
        ...     new_factor_name="ma_filter_factor",
        ...     parameters={"ma_periods": 60},
        ...     match_category=True  # Ensure both are MOMENTUM
        ... )
        >>>
        >>> # Replace exit strategy
        >>> mutated = replace_factor(
        ...     strategy=mutated,
        ...     old_factor_id="profit_target",
        ...     new_factor_name="trailing_stop_factor",
        ...     parameters={"trail_percent": 0.10, "activation_profit": 0.05},
        ...     match_category=True  # Both are EXIT
        ... )
        >>>
        >>> # Validate and execute
        >>> mutated.validate()
        True
        >>> result = mutated.to_pipeline(data)

    Design Notes:
        - Returns new strategy (pure function, no side effects)
        - Category matching reduces invalid mutations (default behavior)
        - Input/output compatibility ensures DAG integrity
        - Preserves dependency structure better than remove+add
        - Useful for evolutionary algorithms (swap underperforming factors)
        - Performance: <10ms for typical operations

    Common Replacements by Category:
        - MOMENTUM: MomentumFactor ↔ MAFilterFactor ↔ DualMAFilterFactor
        - EXIT: TrailingStopFactor ↔ ProfitTargetFactor ↔ VolatilityStopFactor
        - RISK: ATRFactor ↔ VolatilityFactor
        - ENTRY: BreakoutFactor ↔ other entry signals
    """
    # Validate old factor exists
    if old_factor_id not in strategy.factors:
        raise ValueError(
            f"Factor '{old_factor_id}' not found in strategy. "
            f"Available factors: {list(strategy.factors.keys())}"
        )

    # Get old factor for comparison
    old_factor = strategy.factors[old_factor_id]

    # Get factor registry
    registry = FactorRegistry.get_instance()

    # Validate new factor exists in registry
    if not registry.get_factor(new_factor_name):
        available = registry.list_factors()
        raise ValueError(
            f"Factor '{new_factor_name}' not found in registry. "
            f"Available factors: {available}"
        )

    # Create new factor instance with parameters
    try:
        new_factor = registry.create_factor(new_factor_name, parameters)
    except ValueError as e:
        raise ValueError(
            f"Failed to create replacement factor '{new_factor_name}': {str(e)}"
        ) from e

    # Check category match if required
    if match_category:
        if new_factor.category != old_factor.category:
            raise ValueError(
                f"Category mismatch: old factor '{old_factor_id}' is {old_factor.category.name}, "
                f"but new factor '{new_factor_name}' is {new_factor.category.name}. "
                f"To allow cross-category replacement, set match_category=False. "
                f"Same-category alternatives: {registry.list_by_category(old_factor.category)}"
            )

    # Get old factor's dependencies (predecessors) and dependents (successors)
    old_dependencies = list(strategy.dag.predecessors(old_factor_id))
    old_dependents = list(strategy.dag.successors(old_factor_id))

    # Validate input compatibility: new factor's inputs can be satisfied
    # Build available columns from base data and predecessor outputs
    available_columns = {"open", "high", "low", "close", "volume"}  # Base data

    for dependency_id in old_dependencies:
        dependency_factor = strategy.factors[dependency_id]
        available_columns.update(dependency_factor.outputs)

    # Check if new factor's inputs can be satisfied
    missing_inputs = [
        inp for inp in new_factor.inputs
        if inp not in available_columns
    ]

    if missing_inputs:
        raise ValueError(
            f"Input compatibility error: Replacement factor '{new_factor_name}' requires "
            f"inputs {missing_inputs} which are not available. "
            f"Available columns: {sorted(available_columns)}. "
            f"Old factor '{old_factor_id}' inputs: {old_factor.inputs}"
        )

    # Validate output compatibility: new factor can provide required outputs
    # Collect all outputs that dependents need from the old factor
    required_outputs = set()

    for dependent_id in old_dependents:
        dependent = strategy.factors[dependent_id]
        # Only include inputs that come from the old factor
        for inp in dependent.inputs:
            if inp in old_factor.outputs:
                required_outputs.add(inp)

    # Check if new factor can provide all required outputs
    missing_outputs = required_outputs - set(new_factor.outputs)
    if missing_outputs:
        raise ValueError(
            f"Output compatibility error: Replacement factor '{new_factor_name}' cannot provide "
            f"outputs {missing_outputs} required by dependent factors {old_dependents}. "
            f"Old factor outputs: {old_factor.outputs}, "
            f"New factor outputs: {new_factor.outputs}"
        )

    # Create mutated strategy by removing old and adding new
    mutated_strategy = strategy.copy()

    # Get ALL transitive dependents (including old_factor itself and all recursive dependents)
    # This prevents the bug where we try to remove factors that have dependents
    factors_to_remove = _get_transitive_dependents(mutated_strategy, old_factor_id)

    # Store complete information for all factors that will be removed (except old_factor)
    # We need to preserve their full dependency information for reconstruction
    removed_factors_info = []
    for factor_id in factors_to_remove:
        if factor_id != old_factor_id:  # Skip old_factor, it won't be re-added
            factor = mutated_strategy.factors[factor_id]
            # Get ALL dependencies (predecessors), not just the old_factor
            dependencies = list(mutated_strategy.dag.predecessors(factor_id))
            removed_factors_info.append((factor, dependencies))

    # Remove all factors in correct order (leaves first, using reverse topological sort)
    # This ensures we never try to remove a factor that still has dependents
    removal_order = _get_removal_order(mutated_strategy, factors_to_remove)
    for factor_id in removal_order:
        mutated_strategy.remove_factor(factor_id)

    # Add new factor with old_factor's dependencies
    mutated_strategy.add_factor(new_factor, depends_on=old_dependencies)

    # Re-add all removed dependents, updating their dependencies
    # Replace references to old_factor_id with new_factor.id
    for dependent_factor, dependent_deps in removed_factors_info:
        # Update dependencies: replace old_factor_id with new_factor.id
        updated_deps = [
            new_factor.id if dep == old_factor_id else dep
            for dep in dependent_deps
        ]
        mutated_strategy.add_factor(dependent_factor, depends_on=updated_deps)

    # Validate resulting strategy
    try:
        mutated_strategy.validate()
    except ValueError as e:
        raise ValueError(
            f"Replacing factor '{old_factor_id}' with '{new_factor_name}' resulted in "
            f"invalid strategy: {str(e)}"
        ) from e

    return mutated_strategy
