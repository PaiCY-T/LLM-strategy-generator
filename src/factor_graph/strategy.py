"""
Strategy DAG Structure

Implements Strategy class with DAG structure using NetworkX.
A Strategy is a composition of Factors arranged in a Directed Acyclic Graph
where edges represent data dependencies.

Architecture: Phase 2.0+ Factor Graph System
"""

from typing import Dict, List, Optional, Set
import networkx as nx
import pandas as pd
import copy

from .factor import Factor


class Strategy:
    """
    Trading strategy represented as DAG of Factors.

    A Strategy is a composition of Factors arranged in a Directed Acyclic Graph
    where edges represent data dependencies. The Strategy validates DAG integrity,
    compiles to executable pipeline, and supports Factor-level mutations.

    The Strategy class enables:
    - Compositional strategy design through Factor DAG
    - Dependency validation through topological sorting
    - Cycle detection to prevent invalid compositions
    - Lineage tracking for evolutionary provenance
    - Strategy cloning for mutation operations

    Attributes:
        id: Unique strategy identifier
            Format: alphanumeric with underscores (e.g., "strategy_001", "momentum_v2")
        generation: Generation number in evolution (0 for initial templates)
        parent_ids: Parent strategy IDs for lineage tracking
        factors: Dictionary mapping factor IDs to Factor instances
        dag: NetworkX DiGraph representing factor dependencies
            Nodes: Factor IDs
            Edges: Data dependencies (from factor A to factor B if B depends on A's outputs)

    Example:
        >>> # Create strategy
        >>> strategy = Strategy(id="momentum_strategy", generation=0)
        >>>
        >>> # Add factors with dependencies
        >>> strategy.add_factor(rsi_factor)  # No dependencies
        >>> strategy.add_factor(entry_signal, depends_on=["rsi_14"])  # Depends on RSI
        >>> strategy.add_factor(exit_signal, depends_on=["entry_signal_id"])
        >>>
        >>> # Get factors in execution order
        >>> factors = strategy.get_factors()  # Returns [rsi_factor, entry_signal, exit_signal]
        >>>
        >>> # Clone for mutation
        >>> mutated = strategy.copy()
        >>> mutated.remove_factor("exit_signal")
        >>> mutated.add_factor(new_exit_factor, depends_on=["entry_signal_id"])

    Design Notes:
        - DAG validation ensures no cycles (topological sort possible)
        - Orphan detection prevents removing factors with active dependents
        - Lineage tracking enables evolutionary provenance analysis
        - Copy/clone creates independent instances for safe mutation
    """

    def __init__(
        self,
        id: str,
        generation: int = 0,
        parent_ids: Optional[List[str]] = None
    ):
        """
        Initialize Strategy with DAG structure.

        Args:
            id: Unique strategy identifier (alphanumeric with underscores)
            generation: Generation number in evolution (default: 0 for templates)
            parent_ids: List of parent strategy IDs for lineage tracking (default: empty)

        Raises:
            ValueError: If id is empty or invalid format
            TypeError: If generation is not int or parent_ids is not list

        Example:
            >>> # Create initial template strategy
            >>> strategy = Strategy(id="momentum_template", generation=0)
            >>>
            >>> # Create evolved strategy with lineage
            >>> child = Strategy(
            ...     id="momentum_v2",
            ...     generation=1,
            ...     parent_ids=["momentum_template"]
            ... )
        """
        # Validate id
        if not id:
            raise ValueError("Strategy id cannot be empty")
        if not isinstance(id, str):
            raise TypeError(f"Strategy id must be str, got {type(id)}")

        # Validate generation
        if not isinstance(generation, int):
            raise TypeError(f"Strategy generation must be int, got {type(generation)}")
        if generation < 0:
            raise ValueError(f"Strategy generation must be non-negative, got {generation}")

        # Validate parent_ids
        if parent_ids is not None:
            if not isinstance(parent_ids, list):
                raise TypeError(f"Strategy parent_ids must be list, got {type(parent_ids)}")
            if not all(isinstance(p, str) for p in parent_ids):
                raise TypeError("Strategy parent_ids must be list of strings")

        self.id = id
        self.generation = generation
        self.parent_ids = parent_ids if parent_ids is not None else []
        self.factors: Dict[str, Factor] = {}
        self.dag: nx.DiGraph = nx.DiGraph()

    def add_factor(
        self,
        factor: Factor,
        depends_on: Optional[List[str]] = None
    ) -> None:
        """
        Add factor to strategy DAG with dependency validation.

        This method adds a factor to the strategy and creates dependency edges
        in the DAG. It performs cycle detection to ensure the DAG remains acyclic.
        If adding the factor would create a cycle, the operation is rolled back.

        Args:
            factor: Factor instance to add to the strategy
            depends_on: List of factor IDs that this factor depends on
                These must be existing factors in the strategy
                If None or empty, factor has no dependencies (root factor)

        Raises:
            TypeError: If factor is not a Factor instance
            ValueError: If depends_on contains non-existent factor IDs
            ValueError: If adding factor would create a cycle in the DAG
            ValueError: If factor ID already exists in the strategy

        Example:
            >>> strategy = Strategy(id="test")
            >>>
            >>> # Add root factor (no dependencies)
            >>> strategy.add_factor(rsi_factor)
            >>>
            >>> # Add dependent factor
            >>> strategy.add_factor(
            ...     entry_signal,
            ...     depends_on=["rsi_14"]  # Depends on RSI factor output
            ... )
            >>>
            >>> # Try to add factor that would create cycle (raises ValueError)
            >>> try:
            ...     strategy.add_factor(
            ...         cyclic_factor,
            ...         depends_on=["entry_signal", "cyclic_factor"]  # Self-cycle
            ...     )
            ... except ValueError as e:
            ...     print(f"Cycle detected: {e}")
        """
        # Validate factor type
        if not isinstance(factor, Factor):
            raise TypeError(f"Expected Factor instance, got {type(factor)}")

        # Check for duplicate factor ID
        if factor.id in self.factors:
            raise ValueError(f"Factor with id '{factor.id}' already exists in strategy")

        # Validate dependencies exist
        depends_on = depends_on or []
        for dependency in depends_on:
            if dependency not in self.factors:
                raise ValueError(
                    f"Dependency '{dependency}' not found in strategy. "
                    f"Available factors: {list(self.factors.keys())}"
                )

        # Add factor to DAG
        self.dag.add_node(factor.id, factor=factor)

        # Add dependency edges
        for dependency in depends_on:
            self.dag.add_edge(dependency, factor.id)

        # Check for cycles (DAG must remain acyclic)
        if not nx.is_directed_acyclic_graph(self.dag):
            # Rollback: remove node and all its edges
            self.dag.remove_node(factor.id)
            raise ValueError(
                f"Adding factor '{factor.id}' with dependencies {depends_on} "
                f"would create a cycle in the strategy DAG"
            )

        # If validation passed, add factor to storage
        self.factors[factor.id] = factor

    def remove_factor(self, factor_id: str) -> None:
        """
        Remove factor from strategy with orphan detection.

        This method removes a factor from the strategy DAG. It checks for
        dependent factors (factors that depend on the removed factor's outputs)
        and raises an error if any exist, preventing orphaned factors.

        Args:
            factor_id: ID of factor to remove from the strategy

        Raises:
            ValueError: If factor_id does not exist in the strategy
            ValueError: If removing factor would orphan dependent factors
                (other factors depend on this factor's outputs)

        Example:
            >>> strategy = Strategy(id="test")
            >>> strategy.add_factor(rsi_factor)
            >>> strategy.add_factor(entry_signal, depends_on=["rsi_14"])
            >>>
            >>> # Try to remove factor with dependents (raises ValueError)
            >>> try:
            ...     strategy.remove_factor("rsi_14")
            ... except ValueError as e:
            ...     print(f"Cannot remove: {e}")
            >>>
            >>> # Remove leaf factor (no dependents) - success
            >>> strategy.remove_factor("entry_signal")
            >>> "entry_signal" in strategy.factors
            False
        """
        # Validate factor exists
        if factor_id not in self.factors:
            raise ValueError(
                f"Factor '{factor_id}' not found in strategy. "
                f"Available factors: {list(self.factors.keys())}"
            )

        # Check for dependent factors (successors in DAG)
        dependents = list(self.dag.successors(factor_id))
        if dependents:
            raise ValueError(
                f"Cannot remove factor '{factor_id}': "
                f"factors {dependents} depend on its outputs. "
                f"Remove dependent factors first."
            )

        # Remove from DAG and storage
        self.dag.remove_node(factor_id)
        del self.factors[factor_id]

    def get_factors(self) -> List[Factor]:
        """
        Get factors in topologically sorted order (execution order).

        Returns factors ordered such that all dependencies of a factor
        appear before the factor itself. This order is suitable for
        sequential execution where each factor's outputs become available
        for subsequent factors.

        Returns:
            List of Factor instances in topological order
            If strategy has no factors, returns empty list

        Raises:
            ValueError: If DAG contains cycles (should never happen if
                add_factor validation is working correctly)

        Example:
            >>> strategy = Strategy(id="test")
            >>> strategy.add_factor(rsi_factor)  # id="rsi_14"
            >>> strategy.add_factor(ma_factor)   # id="ma_20"
            >>> strategy.add_factor(
            ...     signal_factor,  # id="signal"
            ...     depends_on=["rsi_14", "ma_20"]
            ... )
            >>>
            >>> factors = strategy.get_factors()
            >>> # Returns factors such that rsi_14 and ma_20 come before signal
            >>> # Possible orders: [rsi_14, ma_20, signal] or [ma_20, rsi_14, signal]
            >>> factor_ids = [f.id for f in factors]
            >>> factor_ids.index("signal") > factor_ids.index("rsi_14")
            True
            >>> factor_ids.index("signal") > factor_ids.index("ma_20")
            True
        """
        # Handle empty strategy
        if not self.factors:
            return []

        # Verify DAG is acyclic (should always be true)
        if not nx.is_directed_acyclic_graph(self.dag):
            raise ValueError(
                "Strategy DAG contains cycles. This should not happen - "
                "add_factor validation may be failing."
            )

        # Get topological order and retrieve factor instances
        try:
            topo_order = list(nx.topological_sort(self.dag))
        except nx.NetworkXError as e:
            raise ValueError(f"Failed to compute topological sort: {str(e)}") from e

        # Map factor IDs to Factor instances
        factors = [self.factors[factor_id] for factor_id in topo_order]

        return factors

    def copy(self) -> "Strategy":
        """
        Create independent copy of strategy for mutation.

        Creates a deep copy of the strategy including all factors and DAG structure.
        The copied strategy is completely independent - mutations to the copy do not
        affect the original strategy.

        The copy has the same generation and parent_ids as the original.
        When using the copy for evolution, update these fields appropriately:
        - Increment generation for evolved strategies
        - Add original strategy ID to parent_ids for lineage tracking

        Returns:
            New Strategy instance with copied factors and DAG structure
            The new strategy has a different id (original_id + "_copy")

        Example:
            >>> original = Strategy(id="momentum_v1", generation=5)
            >>> original.add_factor(rsi_factor)
            >>> original.add_factor(signal_factor, depends_on=["rsi_14"])
            >>>
            >>> # Create copy for mutation
            >>> mutated = original.copy()
            >>> mutated.id = "momentum_v2"  # Update ID
            >>> mutated.generation = 6  # Increment generation
            >>> mutated.parent_ids = ["momentum_v1"]  # Track lineage
            >>>
            >>> # Mutate copy (original unchanged)
            >>> mutated.remove_factor("signal_factor")
            >>> mutated.add_factor(new_signal_factor, depends_on=["rsi_14"])
            >>>
            >>> # Verify original is unchanged
            >>> "signal_factor" in original.factors
            True
            >>> "signal_factor" in mutated.factors
            False
        """
        # Create new strategy with copied metadata
        new_strategy = Strategy(
            id=f"{self.id}_copy",
            generation=self.generation,
            parent_ids=self.parent_ids.copy()
        )

        # Deep copy all factors
        # Note: Factor.logic is a callable and will be shallow-copied (shared reference)
        # This is acceptable because logic functions should be pure/immutable
        for factor_id, factor in self.factors.items():
            # Create new factor with copied attributes
            new_factor = Factor(
                id=factor.id,
                name=factor.name,
                category=factor.category,
                inputs=factor.inputs.copy(),
                outputs=factor.outputs.copy(),
                logic=factor.logic,  # Shallow copy of callable (acceptable)
                parameters=copy.deepcopy(factor.parameters),  # Deep copy of parameters
                description=factor.description
            )
            new_strategy.factors[factor_id] = new_factor

        # Deep copy DAG structure
        # NetworkX DiGraph.copy() creates a deep copy of the graph structure
        new_strategy.dag = self.dag.copy()

        # Update node attributes to reference new factor instances
        for node_id in new_strategy.dag.nodes():
            new_strategy.dag.nodes[node_id]['factor'] = new_strategy.factors[node_id]

        return new_strategy

    def to_pipeline(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Compile strategy DAG to executable data pipeline.

        This method compiles the strategy DAG into an executable data pipeline
        that transforms input OHLCV data into a DataFrame with all factor outputs.
        Factors are executed in topological order, respecting all dependencies.

        The method performs automatic validation before execution to ensure the
        strategy is valid and executable.

        Args:
            data: Input DataFrame with OHLCV data (open, high, low, close, volume)
                Must contain all base columns required by the strategy's factors

        Returns:
            DataFrame with all factor outputs computed in dependency order
            Original data columns are preserved, factor outputs are added

        Raises:
            ValueError: If strategy validation fails (invalid DAG structure)
            KeyError: If required input columns are missing from data
            RuntimeError: If factor execution fails during pipeline execution

        Example:
            >>> strategy = Strategy(id="momentum")
            >>> strategy.add_factor(rsi_factor)  # Produces "rsi"
            >>> strategy.add_factor(signal_factor, depends_on=["rsi_14"])  # Produces "positions"
            >>>
            >>> # Execute pipeline
            >>> data = pd.DataFrame({
            ...     "open": [100, 101, 102],
            ...     "high": [101, 102, 103],
            ...     "low": [99, 100, 101],
            ...     "close": [100.5, 101.5, 102.5],
            ...     "volume": [1000, 1100, 1200]
            ... })
            >>> result = strategy.to_pipeline(data)
            >>>
            >>> # Result contains all factor outputs
            >>> "rsi" in result.columns
            True
            >>> "positions" in result.columns
            True

        Performance:
            - <1 second for typical strategies (5-10 factors) on 1000 rows
            - Execution time scales linearly with number of factors and data size
            - No parallel execution (factors executed sequentially)

        Design Notes:
            - Automatically calls validate() before execution
            - Factors executed in topological order (dependencies first)
            - Each factor receives cumulative output from all previous factors
            - Original data is copied to avoid modifying input DataFrame
            - Graceful error handling with context about which factor failed
        """
        # Ensure strategy is valid before execution
        self.validate()

        # Start with a copy of input data to avoid modifying original
        result = data.copy()

        # Execute factors in topological order
        try:
            topo_order = list(nx.topological_sort(self.dag))
        except nx.NetworkXError as e:
            raise ValueError(
                f"Cannot compute topological sort for strategy '{self.id}': {str(e)}"
            ) from e

        # Execute each factor sequentially, accumulating outputs
        for factor_id in topo_order:
            factor = self.factors[factor_id]
            try:
                result = factor.execute(result)
            except Exception as e:
                raise RuntimeError(
                    f"Pipeline execution failed at factor '{factor_id}' ({factor.name}): {str(e)}"
                ) from e

        return result

    def validate(self) -> bool:
        """
        Validate strategy DAG integrity.

        Performs comprehensive validation of the strategy DAG to ensure it represents
        a valid, executable trading strategy. All checks must pass for the strategy
        to be considered valid.

        Validation Checks:
        1. DAG is acyclic (topological sorting possible)
        2. All factor input dependencies are satisfied
        3. At least one factor produces position signals
        4. No orphaned factors (all factors reachable from base data)
        5. No duplicate output columns across factors

        Returns:
            True if strategy is valid

        Raises:
            ValueError: If any validation check fails, with detailed error message
                explaining which check failed and why

        Example:
            >>> strategy = Strategy(id="momentum")
            >>> strategy.add_factor(rsi_factor)
            >>> strategy.add_factor(signal_factor, depends_on=["rsi_14"])
            >>> strategy.validate()  # Returns True if valid
            True
            >>>
            >>> # Invalid strategy (no position signals)
            >>> bad_strategy = Strategy(id="bad")
            >>> bad_strategy.add_factor(rsi_factor)  # Only produces "rsi", not "positions"
            >>> try:
            ...     bad_strategy.validate()
            ... except ValueError as e:
            ...     print(f"Validation failed: {e}")
            Validation failed: Strategy must have at least one factor producing position signals...

        Design Notes:
            - Empty strategies are invalid (must have at least one factor)
            - Position signal columns: "positions", "position", "signal", "signals"
            - Base data columns assumed: OHLCV (open, high, low, close, volume)
            - Orphan detection uses weak connectivity (ignoring edge direction)
        """
        # Check 0: Strategy must have at least one factor
        if not self.factors:
            raise ValueError(
                "Strategy validation failed: Strategy must contain at least one factor"
            )

        # Check 1: DAG is acyclic (topological sorting possible)
        if not nx.is_directed_acyclic_graph(self.dag):
            raise ValueError(
                "Strategy validation failed: DAG contains cycles. "
                "A valid strategy must be a Directed Acyclic Graph (DAG) where "
                "topological sorting is possible. Cycles prevent deterministic execution order."
            )

        # Check 2: All factor input dependencies satisfied
        # Track available columns as we traverse DAG in topological order
        # Start with base OHLCV data columns
        available_columns = {"open", "high", "low", "close", "volume"}

        try:
            topo_order = list(nx.topological_sort(self.dag))
        except nx.NetworkXError as e:
            raise ValueError(
                f"Strategy validation failed: Cannot compute topological sort: {str(e)}"
            ) from e

        for factor_id in topo_order:
            factor = self.factors[factor_id]

            # Check if all inputs are available
            if not factor.validate_inputs(list(available_columns)):
                missing_inputs = [inp for inp in factor.inputs if inp not in available_columns]
                raise ValueError(
                    f"Strategy validation failed: Factor '{factor_id}' requires inputs "
                    f"{missing_inputs} which are not available. "
                    f"Available columns at this point: {sorted(available_columns)}. "
                    f"Ensure all dependencies are added before this factor."
                )

            # Add this factor's outputs to available columns
            available_columns.update(factor.outputs)

        # Check 3: At least one factor produces position signals
        # Position signal columns: "positions", "position", "signal", "signals"
        position_columns = {"positions", "position", "signal", "signals"}

        has_position_signal = False
        for factor in self.factors.values():
            if any(output in position_columns for output in factor.outputs):
                has_position_signal = True
                break

        if not has_position_signal:
            raise ValueError(
                "Strategy validation failed: Strategy must have at least one factor "
                f"producing position signals (columns: {sorted(position_columns)}). "
                f"Current outputs: {sorted(available_columns)}. "
                "Add a signal or position factor to make this a valid trading strategy."
            )

        # Check 4: No orphaned factors (all factors reachable from base data)
        # Use weak connectivity (ignoring edge direction) to check if all nodes are connected
        if not nx.is_weakly_connected(self.dag):
            # Find isolated components
            components = list(nx.weakly_connected_components(self.dag))
            if len(components) > 1:
                orphaned_factors = [
                    sorted(comp) for comp in components[1:]  # Skip the main component
                ]
                raise ValueError(
                    f"Strategy validation failed: Found orphaned factors (not reachable from base data): "
                    f"{orphaned_factors}. All factors must be connected through dependencies. "
                    "Ensure all factors have a dependency path from base OHLCV data."
                )

        # Check 5: No duplicate output columns across factors
        output_to_factors = {}
        for factor_id, factor in self.factors.items():
            for output in factor.outputs:
                if output in output_to_factors:
                    raise ValueError(
                        f"Strategy validation failed: Duplicate output column '{output}' "
                        f"produced by factors '{output_to_factors[output]}' and '{factor_id}'. "
                        "Each output column must be produced by exactly one factor. "
                        "Rename outputs or consolidate logic into a single factor."
                    )
                output_to_factors[output] = factor_id

        # All validation checks passed
        return True

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"Strategy(id='{self.id}', generation={self.generation}, "
            f"parent_ids={self.parent_ids}, factors={len(self.factors)})"
        )

    def __str__(self) -> str:
        """Human-readable representation."""
        factor_list = ", ".join(self.factors.keys()) if self.factors else "empty"
        return (
            f"Strategy '{self.id}' (gen {self.generation}): "
            f"{len(self.factors)} factors [{factor_list}]"
        )
