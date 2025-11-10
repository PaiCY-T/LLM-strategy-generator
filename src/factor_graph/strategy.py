"""
Strategy DAG Structure

Implements Strategy class with DAG structure using NetworkX.
A Strategy is a composition of Factors arranged in a Directed Acyclic Graph
where edges represent data dependencies.

Architecture: Phase 2.0+ Factor Graph System
"""

from typing import Callable, Dict, List, Optional, Set
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

    def to_pipeline(self, data_module, skip_validation: bool = False) -> pd.DataFrame:
        """
        Compile strategy DAG to executable data pipeline (Matrix-Native V2).

        Phase 2.0 redesign: Executes all factors in topological order using
        FinLabDataFrame container for native Dates×Symbols matrix operations.

        This method creates a matrix container, executes the Factor DAG, and
        extracts the final 'position' matrix as output.

        Args:
            data_module: finlab.data module for matrix data access
                        Used to create FinLabDataFrame container with lazy loading
            skip_validation: If True, skip validation checks before execution.
                           Useful for testing error conditions. Default: False

        Returns:
            DataFrame (Dates×Symbols) containing final position signals

        Raises:
            ValueError: If DAG cannot be topologically sorted (contains cycles)
            RuntimeError: If any factor execution fails
            KeyError: If 'position' matrix not produced by strategy

        Example:
            >>> from finlab import data
            >>> from src.factor_graph.strategy import Strategy
            >>> strategy = Strategy(id="momentum")
            >>> strategy.add_factor(momentum_factor)
            >>> strategy.add_factor(position_factor, depends_on=["momentum"])
            >>>
            >>> # Execute pipeline on FinLab data
            >>> position = strategy.to_pipeline(data)
            >>>
            >>> # Result is Dates×Symbols position matrix
            >>> position.shape
            (4563, 2661)

        Performance:
            - <1 second for typical strategies (5-10 factors) on FinLab data
            - Execution time scales linearly with number of factors
            - Matrix operations are vectorized for performance
            - No parallel execution (factors executed sequentially)

        Design Notes:
            - Automatically calls validate() before execution
            - Creates FinLabDataFrame container with data_module
            - Factors executed in topological order (dependencies first)
            - Each factor modifies container (adds matrices)
            - Final 'position' matrix extracted and returned
            - Graceful error handling with context about which factor failed

        Phase 2 Changes:
            - Input changed from DataFrame to data_module
            - Uses FinLabDataFrame container instead of DataFrame
            - Factors receive container instead of DataFrame
            - Returns 'position' matrix instead of accumulated DataFrame
        """
        # Ensure strategy is valid before execution (unless skip_validation=True)
        if not skip_validation:
            self.validate()

        # Phase 2: Create FinLabDataFrame container
        from src.factor_graph.finlab_dataframe import FinLabDataFrame
        container = FinLabDataFrame(data_module=data_module)

        # Execute factors in topological order
        try:
            topo_order = list(nx.topological_sort(self.dag))
        except nx.NetworkXError as e:
            raise ValueError(
                f"Cannot compute topological sort for strategy '{self.id}': {str(e)}"
            ) from e

        # Execute each factor sequentially, container passed and returned
        for factor_id in topo_order:
            factor = self.factors[factor_id]
            try:
                container = factor.execute(container)
            except Exception as e:
                raise RuntimeError(
                    f"Pipeline execution failed at factor '{factor_id}' ({factor.name}): {str(e)}"
                ) from e

        # Phase 2: Extract final 'position' matrix from container
        if not container.has_matrix('position'):
            raise KeyError(
                f"Strategy '{self.id}' did not produce 'position' matrix. "
                f"Available matrices: {container.list_matrices()}"
            )

        return container.get_matrix('position')

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
        # Multiple root factors (in_degree=0) are allowed since they all depend on base OHLCV data
        # Only non-root isolated factors are considered true orphans
        if not nx.is_weakly_connected(self.dag):
            # Find isolated components
            components = list(nx.weakly_connected_components(self.dag))
            if len(components) > 1:
                # Check if all isolated components are root factors
                true_orphans = []
                for comp in components:
                    # A component is NOT orphaned if all its nodes are root factors (in_degree=0)
                    is_root_component = all(self.dag.in_degree(node) == 0 for node in comp)
                    if not is_root_component:
                        true_orphans.append(sorted(comp))

                if true_orphans:
                    raise ValueError(
                        f"Strategy validation failed: Found orphaned factors (not reachable from base data): "
                        f"{true_orphans}. All factors must be connected through dependencies. "
                        "Ensure all factors have a dependency path from base OHLCV data or other factors."
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

    def to_dict(self) -> Dict:
        """
        Serialize strategy to dictionary (metadata-only, no logic functions).

        This method creates a JSON-serializable dictionary containing all strategy
        metadata except Factor logic functions (which are Callables and cannot be
        serialized to JSON). The serialized format is suitable for:
        - Saving champion strategies to Hall of Fame
        - Transmitting strategies over network
        - Storing strategies in databases
        - Logging and debugging

        To reconstruct a Strategy from this dict, use from_dict() with a factor_registry
        that maps factor IDs to their logic functions.

        Returns:
            Dictionary with strategy metadata:
            {
                "id": str,
                "generation": int,
                "parent_ids": List[str],
                "factors": List[Dict] - factor metadata without logic
                "dag_edges": List[Tuple[str, str]] - DAG structure
            }

        Example:
            >>> strategy = Strategy(id="momentum_v1", generation=5)
            >>> strategy.add_factor(rsi_factor)
            >>> strategy.add_factor(signal_factor, depends_on=["rsi_14"])
            >>>
            >>> # Serialize to dict
            >>> metadata = strategy.to_dict()
            >>> metadata.keys()
            dict_keys(['id', 'generation', 'parent_ids', 'factors', 'dag_edges'])
            >>>
            >>> # Can be serialized to JSON
            >>> import json
            >>> json_str = json.dumps(metadata)

        Design Notes:
            - Factor logic functions are NOT serialized (Callables cannot be JSON-encoded)
            - FactorCategory enums are serialized as strings (e.g., "MOMENTUM")
            - DAG edges are serialized as list of [source, target] pairs
            - Empty parameters dict is preserved (for consistency)
            - Reconstruction requires factor_registry with logic functions
        """
        from typing import Dict, List, Any

        # Serialize factors (metadata only, no logic)
        factors_metadata = []
        for factor_id, factor in self.factors.items():
            factor_dict = {
                "id": factor.id,
                "name": factor.name,
                "category": factor.category.name,  # Enum to string
                "inputs": factor.inputs,
                "outputs": factor.outputs,
                "parameters": factor.parameters,
                "description": factor.description
                # NOTE: logic is NOT serialized (Callable cannot be JSON-encoded)
            }
            factors_metadata.append(factor_dict)

        # Serialize DAG edges
        dag_edges = list(self.dag.edges())

        return {
            "id": self.id,
            "generation": self.generation,
            "parent_ids": self.parent_ids,
            "factors": factors_metadata,
            "dag_edges": dag_edges
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict,
        factor_registry: Dict[str, Callable]
    ) -> "Strategy":
        """
        Reconstruct strategy from dictionary using factor_registry for logic.

        This method deserializes a strategy from a metadata dictionary (created by
        to_dict()) and reconstructs all Factors using logic functions from the
        provided factor_registry.

        The factor_registry maps factor IDs to their logic functions. This is necessary
        because logic functions (Callables) cannot be serialized to JSON. The registry
        must contain all logic functions needed by the strategy's factors.

        Args:
            data: Dictionary with strategy metadata (from to_dict())
                Required keys: id, generation, parent_ids, factors, dag_edges
            factor_registry: Dictionary mapping factor IDs to logic functions
                Example: {"rsi_14": calculate_rsi, "signal": generate_signal}
                Must contain logic for ALL factors in the strategy

        Returns:
            Reconstructed Strategy instance with all factors and DAG structure

        Raises:
            KeyError: If factor_registry is missing logic for any factor
            ValueError: If data is malformed or DAG validation fails
            TypeError: If data types are incorrect

        Example:
            >>> # Define logic functions
            >>> def calculate_rsi(data, params):
            ...     # RSI calculation logic
            ...     return data
            >>>
            >>> def generate_signal(data, params):
            ...     # Signal generation logic
            ...     return data
            >>>
            >>> # Create factor registry
            >>> factor_registry = {
            ...     "rsi_14": calculate_rsi,
            ...     "signal": generate_signal
            ... }
            >>>
            >>> # Serialize strategy
            >>> original = Strategy(id="test", generation=1)
            >>> # ... add factors ...
            >>> metadata = original.to_dict()
            >>>
            >>> # Reconstruct strategy
            >>> reconstructed = Strategy.from_dict(metadata, factor_registry)
            >>> reconstructed.id == original.id
            True
            >>> len(reconstructed.factors) == len(original.factors)
            True

        Design Notes:
            - factor_registry is required (logic cannot be serialized)
            - FactorCategory is reconstructed from string names
            - DAG structure is fully reconstructed from edges
            - Validation is performed during reconstruction (add_factor checks)
            - Missing registry entries raise KeyError with helpful message
        """
        from .factor_category import FactorCategory

        # Create strategy with basic metadata
        strategy = cls(
            id=data["id"],
            generation=data["generation"],
            parent_ids=data["parent_ids"]
        )

        # Build factor_id to dependencies mapping from DAG edges
        # This is needed to add factors in correct order
        factor_dependencies = {factor["id"]: [] for factor in data["factors"]}
        for source, target in data["dag_edges"]:
            factor_dependencies[target].append(source)

        # Reconstruct factors using topological order
        # We need to add factors in dependency order to avoid errors
        factors_to_add = data["factors"].copy()
        added_factors = set()

        while factors_to_add:
            # Find factors whose dependencies are all added
            ready_factors = [
                factor_dict for factor_dict in factors_to_add
                if all(dep in added_factors for dep in factor_dependencies[factor_dict["id"]])
            ]

            if not ready_factors:
                # No progress possible - circular dependency or malformed data
                remaining_ids = [f["id"] for f in factors_to_add]
                raise ValueError(
                    f"Cannot reconstruct strategy: circular dependencies or malformed data. "
                    f"Remaining factors: {remaining_ids}"
                )

            # Add ready factors
            for factor_dict in ready_factors:
                factor_id = factor_dict["id"]

                # Get logic from registry
                if factor_id not in factor_registry:
                    raise KeyError(
                        f"factor_registry is missing logic for factor '{factor_id}'. "
                        f"Available registry keys: {list(factor_registry.keys())}"
                    )

                logic = factor_registry[factor_id]

                # Reconstruct Factor
                factor = Factor(
                    id=factor_dict["id"],
                    name=factor_dict["name"],
                    category=FactorCategory[factor_dict["category"]],  # String to enum
                    inputs=factor_dict["inputs"],
                    outputs=factor_dict["outputs"],
                    logic=logic,
                    parameters=factor_dict["parameters"],
                    description=factor_dict.get("description", "")
                )

                # Add factor to strategy with dependencies
                dependencies = factor_dependencies[factor_id]
                strategy.add_factor(factor, depends_on=dependencies)

                # Mark as added
                added_factors.add(factor_id)
                factors_to_add.remove(factor_dict)

        return strategy

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
