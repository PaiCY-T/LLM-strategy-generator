"""
Exit Strategy Mutator - AST-based exit logic mutations.

Part of Phase 1 Exit Strategy Mutation Framework.
Mutates exit strategies through AST manipulation with three mutation tiers.

Task: 1.2
Purpose: Core mutation logic for exit strategy evolution
"""

import ast
import random
from dataclasses import dataclass, field
from typing import Dict, List

from src.mutation.exit_detector import ExitStrategyProfile


@dataclass
class MutationConfig:
    """
    Configuration for exit strategy mutations.

    Attributes:
        mutation_tier: Tier selection ('parametric', 'structural', 'relational')
        probability_weights: Probability distribution for tier selection
        parameter_ranges: Valid values for each parameter
        seed: Random seed for reproducibility
    """
    mutation_tier: str = 'parametric'
    probability_weights: Dict[str, float] = field(default_factory=lambda: {
        'parametric': 0.80,   # 80% - high-impact, low-risk
        'structural': 0.15,   # 15% - medium-impact, medium-risk
        'relational': 0.05    # 5% - high-impact, high-risk
    })
    parameter_ranges: Dict[str, List[float]] = field(default_factory=lambda: {
        'atr_period': [10, 14, 20, 30],
        'stop_atr_mult': [1.5, 2.0, 2.5, 3.0],
        'profit_atr_mult': [2.0, 3.0, 4.0, 5.0],
        'max_hold_days': [20, 30, 40, 60]
    })
    seed: int = None


class ExitStrategyMutator:
    """
    Mutate exit strategies via AST manipulation.

    Implements three mutation tiers:
    1. Parametric (80%): Change parameter values (ATR multipliers, time periods)
    2. Structural (15%): Add/remove/swap exit mechanisms
    3. Relational (5%): Change comparison operators (< vs <=)

    Mutation Strategy:
    ------------------
    - Tier 1 (Parametric): Low risk, high impact - modify numerical constants
    - Tier 2 (Structural): Medium risk, medium impact - change exit combinations
    - Tier 3 (Relational): High risk, high impact - alter comparison logic

    Example Usage:
    --------------
    ```python
    mutator = ExitStrategyMutator()
    config = MutationConfig(seed=42)

    # Detect current strategy
    profile = detector.detect(code)

    # Apply mutation
    mutated_ast = mutator.mutate(profile, config)

    # Generate new code
    new_code = ast.unparse(mutated_ast)
    ```
    """

    def __init__(self, seed: int = None):
        """
        Initialize mutator with optional random seed.

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)

    def mutate(
        self,
        profile: ExitStrategyProfile,
        config: MutationConfig
    ) -> ast.AST:
        """
        Apply mutation operations to exit strategy AST.

        Args:
            profile: Detected exit strategy profile
            config: Mutation configuration

        Returns:
            Modified AST tree with mutations applied

        Raises:
            ValueError: If profile doesn't contain required AST nodes
        """
        if profile.method_node is None:
            raise ValueError("Profile must contain _apply_exit_strategies method node")

        # Set random seed if specified
        if config.seed is not None:
            random.seed(config.seed)

        # Select mutation tier based on probability weights
        mutation_tier = self._select_mutation_tier(config)

        # Make a deep copy of the method node for mutation
        mutated_method = ast.parse(ast.unparse(profile.method_node)).body[0]

        # Apply the appropriate mutation
        if mutation_tier == 'parametric':
            self._mutate_parameters(mutated_method, profile, config)
        elif mutation_tier == 'structural':
            self._mutate_mechanisms(mutated_method, profile, config)
        elif mutation_tier == 'relational':
            self._mutate_conditions(mutated_method, profile, config)

        return mutated_method

    def _select_mutation_tier(self, config: MutationConfig) -> str:
        """
        Select mutation tier based on weighted probabilities.

        Args:
            config: Mutation configuration with probability weights

        Returns:
            Selected tier name ('parametric', 'structural', or 'relational')
        """
        tiers = list(config.probability_weights.keys())
        weights = list(config.probability_weights.values())

        # Normalize weights to sum to 1.0
        total = sum(weights)
        normalized_weights = [w / total for w in weights]

        # Random selection based on weights
        return random.choices(tiers, weights=normalized_weights, k=1)[0]

    def _mutate_parameters(
        self,
        method_node: ast.FunctionDef,
        profile: ExitStrategyProfile,
        config: MutationConfig
    ) -> None:
        """
        Modify parameter values in AST (Tier 1 - Parametric).

        Locates params.get() calls and replaces default values with
        new values from valid parameter ranges.

        Mutations:
        ----------
        - Change ATR multipliers: 1.5, 2.0, 2.5, 3.0 (stop); 2.0, 3.0, 4.0, 5.0 (profit)
        - Change time periods: 20, 30, 40, 60 days
        - Change ATR periods: 10, 14, 20, 30 days

        Args:
            method_node: Method AST node to mutate (modified in-place)
            profile: Current exit strategy profile
            config: Mutation configuration with parameter ranges
        """
        # Find all params.get() calls in the method
        for node in ast.walk(method_node):
            if isinstance(node, ast.Call):
                if self._is_params_get_call(node):
                    param_name, current_value = self._extract_param_from_call(node)

                    if param_name in config.parameter_ranges:
                        # Get valid values for this parameter
                        valid_values = config.parameter_ranges[param_name]

                        # Select a different value (not the current one if possible)
                        if len(valid_values) > 1:
                            other_values = [v for v in valid_values if v != current_value]
                            if other_values:
                                new_value = random.choice(other_values)
                            else:
                                new_value = random.choice(valid_values)
                        else:
                            new_value = valid_values[0]

                        # Replace the default value constant
                        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                            node.args[1].value = new_value

    def _mutate_mechanisms(
        self,
        method_node: ast.FunctionDef,
        profile: ExitStrategyProfile,
        config: MutationConfig
    ) -> None:
        """
        Add/remove/swap exit mechanisms (Tier 2 - Structural).

        Modifies the any_exit BoolOp to add or remove exit mechanisms.
        Ensures at least one exit mechanism remains active.

        Mutations:
        ----------
        - Add time_exit to (stop_exit | profit_exit)
        - Remove profit_exit from (time_exit | stop_exit | profit_exit)
        - Swap stop_exit with profit_exit

        Safety Rule: At least one exit mechanism must remain

        Args:
            method_node: Method AST node to mutate (modified in-place)
            profile: Current exit strategy profile
            config: Mutation configuration
        """
        # Find the any_exit assignment node
        any_exit_node = None
        for node in ast.walk(method_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'any_exit':
                        if isinstance(node.value, ast.BoolOp) and isinstance(node.value.op, ast.Or):
                            any_exit_node = node
                            break

        if any_exit_node is None:
            # No any_exit node found, cannot mutate
            return

        # Get current exit variables in the BoolOp
        bool_op = any_exit_node.value
        current_exits = []
        for value in bool_op.values:
            if isinstance(value, ast.Name):
                current_exits.append(value.id)

        # Define all possible exit mechanisms
        all_exits = ['time_exit', 'stop_exit', 'profit_exit']

        # Decide mutation operation
        operations = []
        if len(current_exits) < len(all_exits):
            operations.append('add')
        if len(current_exits) > 1:  # Must keep at least one exit
            operations.append('remove')
        if len(current_exits) >= 2:
            operations.append('swap')

        if not operations:
            return  # No valid operations

        operation = random.choice(operations)

        if operation == 'add':
            # Add a mechanism that's not currently present
            missing_exits = [e for e in all_exits if e not in current_exits]
            if missing_exits:
                new_exit = random.choice(missing_exits)
                bool_op.values.append(ast.Name(id=new_exit, ctx=ast.Load()))

        elif operation == 'remove':
            # Remove a random mechanism (but keep at least one)
            if len(current_exits) > 1:
                exit_to_remove = random.choice(current_exits)
                bool_op.values = [v for v in bool_op.values
                                 if not (isinstance(v, ast.Name) and v.id == exit_to_remove)]

        elif operation == 'swap':
            # Swap two mechanisms
            if len(current_exits) >= 2:
                idx1, idx2 = random.sample(range(len(bool_op.values)), 2)
                bool_op.values[idx1], bool_op.values[idx2] = bool_op.values[idx2], bool_op.values[idx1]

    def _mutate_conditions(
        self,
        method_node: ast.FunctionDef,
        profile: ExitStrategyProfile,
        config: MutationConfig
    ) -> None:
        """
        Change comparison operators in exit conditions (Tier 3 - Relational).

        Modifies comparison operators while maintaining logical soundness:
        - < ↔ <= (less than to less than or equal)
        - > ↔ >= (greater than to greater than or equal)

        Safety Rule: Does not invert logic (< to >, etc.) to avoid impossible conditions

        Args:
            method_node: Method AST node to mutate (modified in-place)
            profile: Current exit strategy profile
            config: Mutation configuration
        """
        # Find all Compare nodes in exit conditions
        compare_nodes = []
        for node in ast.walk(method_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Check if this is an exit variable
                        if target.id in ['stop_exit', 'profit_exit', 'time_exit']:
                            # Check if value is a Compare
                            if isinstance(node.value, ast.Compare):
                                compare_nodes.append(node.value)

        if not compare_nodes:
            return  # No comparison nodes to mutate

        # Select a random comparison to mutate
        compare_node = random.choice(compare_nodes)

        # Mutate the first operator (most common case)
        if compare_node.ops:
            current_op = compare_node.ops[0]

            # Define safe operator swaps (maintain logic direction)
            operator_swaps = {
                ast.Lt: ast.LtE,
                ast.LtE: ast.Lt,
                ast.Gt: ast.GtE,
                ast.GtE: ast.Gt
            }

            current_op_type = type(current_op)
            if current_op_type in operator_swaps:
                new_op_type = operator_swaps[current_op_type]
                compare_node.ops[0] = new_op_type()

    def _is_params_get_call(self, node: ast.Call) -> bool:
        """Check if a Call node is params.get('key', default)."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'get':
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == 'params':
                        return True
        return False

    def _extract_param_from_call(self, node: ast.Call) -> tuple:
        """Extract parameter name and default value from params.get() call."""
        param_name = None
        default_value = None

        if len(node.args) >= 1:
            if isinstance(node.args[0], ast.Constant):
                param_name = node.args[0].value

        if len(node.args) >= 2:
            if isinstance(node.args[1], ast.Constant):
                default_value = node.args[1].value

        return param_name, default_value
