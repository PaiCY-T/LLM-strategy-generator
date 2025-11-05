"""
AST Factor Mutator - Mutate factor logic at AST level.

Implements advanced structural mutations by modifying factor logic
at the Abstract Syntax Tree (AST) level. Enables breakthrough innovations
beyond parameter tuning.

Part of Tier 3 AST Mutation Framework.
Task: D.3 - AST-Based Factor Logic Mutation
"""

import ast
import inspect
import random
import copy
from typing import Dict, Any, Callable, List, Optional
import pandas as pd

from src.factor_graph.factor import Factor
from .ast_validator import ASTValidator, ValidationResult


class ComparisonOperatorMutator(ast.NodeTransformer):
    """
    AST transformer to mutate comparison operators.

    Mutations:
    - < ↔ <= (less than to less than or equal)
    - > ↔ >= (greater than to greater than or equal)
    - == ↔ != (equal to not equal, with caution)
    """

    def visit_Compare(self, node: ast.Compare) -> ast.Compare:
        """Mutate comparison operators."""
        # Define operator swaps
        operator_swaps = {
            ast.Lt: ast.LtE,
            ast.LtE: ast.Lt,
            ast.Gt: ast.GtE,
            ast.GtE: ast.Gt,
            # Be cautious with == and != (can invert logic)
            # ast.Eq: ast.NotEq,
            # ast.NotEq: ast.Eq,
        }

        # Mutate operators with 50% probability
        if node.ops and random.random() < 0.5:
            current_op_type = type(node.ops[0])
            if current_op_type in operator_swaps:
                new_op_type = operator_swaps[current_op_type]
                node.ops[0] = new_op_type()

        self.generic_visit(node)
        return node


class ThresholdAdjuster(ast.NodeTransformer):
    """
    AST transformer to adjust numeric thresholds.

    Mutations:
    - Multiply constants by factor (0.8, 1.2, etc.)
    - Add/subtract small values
    """

    def __init__(self, adjustment_factor: float = 1.1):
        """
        Initialize threshold adjuster.

        Args:
            adjustment_factor: Multiply thresholds by this factor
        """
        self.adjustment_factor = adjustment_factor

    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        """Adjust numeric constants."""
        # Only adjust numeric constants
        if isinstance(node.value, (int, float)):
            # Apply adjustment with 30% probability
            if random.random() < 0.3:
                # Preserve type (int or float)
                if isinstance(node.value, int):
                    node.value = int(node.value * self.adjustment_factor)
                else:
                    node.value = node.value * self.adjustment_factor

        self.generic_visit(node)
        return node


class BinaryOperatorMutator(ast.NodeTransformer):
    """
    AST transformer to mutate binary operators.

    Mutations:
    - + ↔ - (addition to subtraction)
    - * ↔ / (multiplication to division)
    """

    def visit_BinOp(self, node: ast.BinOp) -> ast.BinOp:
        """Mutate binary operators."""
        # Define operator swaps
        operator_swaps = {
            ast.Add: ast.Sub,
            ast.Sub: ast.Add,
            ast.Mult: ast.Div,
            ast.Div: ast.Mult,
        }

        # Mutate operators with 30% probability
        if random.random() < 0.3:
            current_op_type = type(node.op)
            if current_op_type in operator_swaps:
                new_op_type = operator_swaps[current_op_type]
                node.op = new_op_type()

        self.generic_visit(node)
        return node


class ASTFactorMutator:
    """
    Mutate factor logic at AST level.

    Capabilities:
    - Modify comparison operators (> to >=, etc.)
    - Change mathematical operations (+/-, *//)
    - Adjust thresholds and constants
    - Add conditional logic
    - Combine expressions

    Uses Phase 1 AST infrastructure (ast.parse, ast.unparse).

    Mutation Types:
    --------------
    1. operator_mutation: Change comparison/binary operators
    2. threshold_adjustment: Modify numeric constants
    3. expression_modification: Change calculations

    Example Usage:
    -------------
    ```python
    mutator = ASTFactorMutator()

    # Mutate factor logic
    config = {
        "mutation_type": "operator_mutation",
        "seed": 42
    }

    mutated_factor = mutator.mutate(rsi_factor, config)

    # Validate mutated logic
    validator = ASTValidator()
    result = validator.validate(mutator.get_source(mutated_factor))
    assert result.success
    ```

    Configuration Format:
    --------------------
    {
        "mutation_type": str,  # "operator_mutation", "threshold_adjustment", "expression_modification"
        "adjustment_factor": float,  # For threshold_adjustment (default: 1.1)
        "seed": int,  # Optional random seed
        "validate": bool  # Validate after mutation (default: True)
    }
    """

    def __init__(self):
        """Initialize AST mutator with validator."""
        self.validator = ASTValidator()

    def mutate(self, factor: Factor, config: Dict[str, Any]) -> Factor:
        """
        Apply AST mutation to factor logic.

        Args:
            factor: Factor with logic callable
            config: Mutation configuration

        Returns:
            New Factor with mutated logic

        Raises:
            ValueError: If logic cannot be extracted
            ValueError: If mutation produces invalid code
        """
        # Extract config parameters
        mutation_type = config.get("mutation_type", "operator_mutation")
        adjustment_factor = config.get("adjustment_factor", 1.1)
        seed = config.get("seed", None)
        validate = config.get("validate", True)

        if seed is not None:
            random.seed(seed)

        # Extract source code from logic callable
        source = self._extract_logic_source(factor.logic)

        # Parse to AST
        tree = ast.parse(source)

        # Apply transformation based on mutation type
        if mutation_type == "operator_mutation":
            transformer = ComparisonOperatorMutator()
            tree = transformer.visit(tree)

        elif mutation_type == "threshold_adjustment":
            transformer = ThresholdAdjuster(adjustment_factor)
            tree = transformer.visit(tree)

        elif mutation_type == "expression_modification":
            transformer = BinaryOperatorMutator()
            tree = transformer.visit(tree)

        else:
            raise ValueError(
                f"Unknown mutation_type: {mutation_type}. "
                f"Valid types: operator_mutation, threshold_adjustment, expression_modification"
            )

        # Fix missing locations for AST nodes
        ast.fix_missing_locations(tree)

        # Unparse to source
        mutated_source = ast.unparse(tree)

        # Validate mutated code
        if validate:
            result = self.validator.validate(mutated_source)
            if not result.success:
                raise ValueError(
                    f"Mutation produced invalid code:\n"
                    f"Errors: {result.errors}\n"
                    f"Warnings: {result.warnings}"
                )

        # Compile to callable
        mutated_logic = self._compile_logic(mutated_source)

        # Create new factor with mutated logic
        mutated_factor = Factor(
            id=factor.id,
            name=factor.name,
            category=factor.category,
            inputs=factor.inputs.copy(),
            outputs=factor.outputs.copy(),
            logic=mutated_logic,
            parameters=copy.deepcopy(factor.parameters),
            description=f"{factor.description} [AST mutated: {mutation_type}]"
        )

        return mutated_factor

    def _extract_logic_source(self, logic: Callable) -> str:
        """
        Extract source code from callable.

        Args:
            logic: Callable to extract source from

        Returns:
            Source code string (dedented)

        Raises:
            ValueError: If source cannot be extracted
        """
        try:
            source = inspect.getsource(logic)
            # Dedent to remove leading indentation
            import textwrap
            source = textwrap.dedent(source)
            return source
        except (OSError, TypeError) as e:
            raise ValueError(
                f"Cannot extract source from logic callable: {e}. "
                "Logic must be a regular function, not a lambda or builtin."
            ) from e

    def _compile_logic(self, source: str) -> Callable:
        """
        Compile modified source to callable.

        Args:
            source: Python source code defining a function

        Returns:
            Compiled function callable

        Raises:
            ValueError: If compilation fails
        """
        try:
            # Create namespace for execution
            from typing import Dict, Any
            namespace = {
                'pd': pd,
                'DataFrame': pd.DataFrame,
                'Series': pd.Series,
                'Dict': Dict,
                'Any': Any,
            }

            # Compile and execute source
            compiled = compile(source, '<mutated>', 'exec')
            exec(compiled, namespace)

            # Extract function from namespace
            # Assume source defines a single function
            functions = [
                v for v in namespace.values()
                if callable(v) and not isinstance(v, type)
            ]

            if not functions:
                raise ValueError("No function found in compiled source")

            # Return first function found
            return functions[0]

        except Exception as e:
            raise ValueError(f"Failed to compile mutated logic: {e}") from e

    def get_source(self, factor: Factor) -> str:
        """
        Get source code of factor logic.

        Args:
            factor: Factor to extract source from

        Returns:
            Source code string

        Raises:
            ValueError: If source cannot be extracted
        """
        return self._extract_logic_source(factor.logic)

    def apply_multiple_mutations(
        self,
        factor: Factor,
        mutations: List[Dict[str, Any]]
    ) -> Factor:
        """
        Apply multiple mutations sequentially.

        Args:
            factor: Factor to mutate
            mutations: List of mutation configs

        Returns:
            Factor with all mutations applied

        Example:
            >>> mutations = [
            ...     {"mutation_type": "operator_mutation"},
            ...     {"mutation_type": "threshold_adjustment", "adjustment_factor": 1.2}
            ... ]
            >>> mutated = mutator.apply_multiple_mutations(factor, mutations)
        """
        current_factor = factor

        for mutation_config in mutations:
            current_factor = self.mutate(current_factor, mutation_config)

        return current_factor

    def mutate_with_rollback(
        self,
        factor: Factor,
        config: Dict[str, Any]
    ) -> Optional[Factor]:
        """
        Apply mutation with automatic rollback on failure.

        Args:
            factor: Factor to mutate
            config: Mutation configuration

        Returns:
            Mutated factor if successful, None if mutation failed
        """
        try:
            return self.mutate(factor, config)
        except (ValueError, SyntaxError, Exception):
            # Rollback - return None to indicate failure
            return None
