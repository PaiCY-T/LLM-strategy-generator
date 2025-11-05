"""
Exit Mechanism Detector - AST-based exit strategy analysis.

Part of Phase 1 Exit Strategy Mutation Framework.
Analyzes Python source code to detect and extract exit strategy characteristics.

Task: 1.1
Purpose: Foundation for AST-based exit mutations
"""

import ast
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ExitStrategyProfile:
    """
    Detected exit strategy characteristics from source code.

    Attributes:
        mechanisms: List of detected exit types (e.g., ['stop_loss', 'profit_target', 'time_based'])
        parameters: Extracted parameter values (e.g., {'stop_atr_mult': 2.0, 'profit_atr_mult': 3.0})
        ast_nodes: Mapping of mechanism names to their AST nodes for later mutation
        method_node: AST node of _apply_exit_strategies method (if found)
    """
    mechanisms: List[str] = field(default_factory=list)
    parameters: Dict[str, float] = field(default_factory=dict)
    ast_nodes: Dict[str, ast.AST] = field(default_factory=dict)
    method_node: Optional[ast.FunctionDef] = None


class ExitMechanismDetector:
    """
    Detect exit logic in strategy code via AST analysis.

    Analyzes Python source code to identify:
    1. Exit mechanisms (stop-loss, profit target, time-based)
    2. Parameter values (ATR multipliers, time periods)
    3. AST node locations for targeted mutations

    Detection Strategy:
    -------------------
    - Variable names: look for stop_exit, profit_exit, time_exit assignments
    - Parameters: extract from params.get('param_name', default_value) calls
    - Exit combinations: find BoolOp nodes with Or() combining exits

    Example Usage:
    --------------
    ```python
    detector = ExitMechanismDetector()
    profile = detector.detect(strategy_code)

    print(f"Detected mechanisms: {profile.mechanisms}")
    # Output: ['stop_loss', 'profit_target', 'time_based']

    print(f"Parameters: {profile.parameters}")
    # Output: {'stop_atr_mult': 2.0, 'profit_atr_mult': 3.0, 'max_hold_days': 30}
    ```
    """

    # Exit mechanism variable name mappings
    MECHANISM_NAMES = {
        'stop_exit': 'stop_loss',
        'profit_exit': 'profit_target',
        'time_exit': 'time_based'
    }

    # Parameter name mappings
    PARAMETER_NAMES = {
        'stop_atr_mult',
        'profit_atr_mult',
        'max_hold_days',
        'atr_period'
    }

    def detect(self, code: str) -> ExitStrategyProfile:
        """
        Analyze code and extract exit strategy profile.

        Args:
            code: Python source code containing exit strategy logic

        Returns:
            ExitStrategyProfile with detected mechanisms, parameters, and AST nodes

        Raises:
            SyntaxError: If code cannot be parsed
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise SyntaxError(f"Failed to parse code: {e}") from e

        # Find the _apply_exit_strategies method
        method_node = self._find_exit_method(tree)

        # Detect exit mechanisms
        mechanisms = self._find_exit_mechanisms(tree)

        # Extract parameters
        parameters = self._extract_parameters(tree)

        # Map AST nodes for each mechanism
        ast_nodes = self._map_ast_nodes(tree, mechanisms)

        return ExitStrategyProfile(
            mechanisms=mechanisms,
            parameters=parameters,
            ast_nodes=ast_nodes,
            method_node=method_node
        )

    def _find_exit_method(self, tree: ast.AST) -> Optional[ast.FunctionDef]:
        """
        Find the _apply_exit_strategies method node.

        Args:
            tree: AST tree to search

        Returns:
            FunctionDef node if found, None otherwise
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == '_apply_exit_strategies':
                return node
        return None

    def _find_exit_mechanisms(self, tree: ast.AST) -> List[str]:
        """
        Identify which exit types are present in the code.

        Looks for variable assignments with names:
        - stop_exit → 'stop_loss'
        - profit_exit → 'profit_target'
        - time_exit → 'time_based'

        Args:
            tree: AST tree to analyze

        Returns:
            List of detected mechanism types (e.g., ['stop_loss', 'profit_target'])
        """
        mechanisms = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        if var_name in self.MECHANISM_NAMES:
                            mechanism_type = self.MECHANISM_NAMES[var_name]
                            if mechanism_type not in mechanisms:
                                mechanisms.append(mechanism_type)

        return sorted(mechanisms)  # Sort for consistency

    def _extract_parameters(self, tree: ast.AST) -> Dict[str, float]:
        """
        Extract parameter values from params.get() calls.

        Looks for patterns like:
        - stop_atr_mult = params.get('stop_atr_mult', 2.0)
        - max_hold_days = params.get('max_hold_days', 30)

        Args:
            tree: AST tree to analyze

        Returns:
            Dictionary of parameter names to their default values
        """
        parameters = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Check if right side is a params.get() call
                if isinstance(node.value, ast.Call):
                    if self._is_params_get_call(node.value):
                        param_name, default_value = self._extract_param_from_call(node.value)
                        if param_name in self.PARAMETER_NAMES and default_value is not None:
                            parameters[param_name] = default_value

        return parameters

    def _is_params_get_call(self, node: ast.Call) -> bool:
        """
        Check if a Call node is params.get('key', default).

        Args:
            node: AST Call node to check

        Returns:
            True if this is a params.get() call
        """
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'get':
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == 'params':
                        return True
        return False

    def _extract_param_from_call(self, node: ast.Call) -> tuple:
        """
        Extract parameter name and default value from params.get() call.

        Args:
            node: AST Call node for params.get()

        Returns:
            Tuple of (parameter_name, default_value)
        """
        param_name = None
        default_value = None

        if len(node.args) >= 1:
            # First argument is the parameter name
            if isinstance(node.args[0], ast.Constant):
                param_name = node.args[0].value

        if len(node.args) >= 2:
            # Second argument is the default value
            if isinstance(node.args[1], ast.Constant):
                default_value = node.args[1].value

        return param_name, default_value

    def _map_ast_nodes(self, tree: ast.AST, mechanisms: List[str]) -> Dict[str, ast.AST]:
        """
        Map mechanism names to their corresponding AST nodes.

        Finds the assignment nodes for each exit mechanism variable:
        - stop_exit = ... → maps 'stop_loss' to this Assign node
        - profit_exit = ... → maps 'profit_target' to this Assign node
        - time_exit = ... → maps 'time_based' to this Assign node

        Also finds the any_exit combination node (BoolOp with Or).

        Note: Handles assignments inside loops and nested structures.

        Args:
            tree: AST tree to search
            mechanisms: List of mechanism types to map

        Returns:
            Dictionary mapping mechanism types to their AST nodes
        """
        ast_nodes = {}

        # Reverse mapping: mechanism type → variable name
        reverse_mapping = {v: k for k, v in self.MECHANISM_NAMES.items()}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Handle both simple Name and Subscript targets
                target_name = None
                if node.targets:
                    target = node.targets[0]
                    if isinstance(target, ast.Name):
                        target_name = target.id
                    elif isinstance(target, ast.Subscript):
                        # Handle subscript like `exit_var.loc[date]` (ignore for mapping)
                        continue

                if target_name:
                    # Check if this is an exit mechanism variable
                    # target_name is the variable name like 'stop_exit'
                    # We need to check if it's in MECHANISM_NAMES keys (not reverse_mapping)
                    if target_name in self.MECHANISM_NAMES:
                        mechanism_type = self.MECHANISM_NAMES[target_name]
                        if mechanism_type in mechanisms:
                            ast_nodes[mechanism_type] = node

                    # Check if this is the any_exit combination
                    if target_name == 'any_exit':
                        if isinstance(node.value, ast.BoolOp) and isinstance(node.value.op, ast.Or):
                            ast_nodes['any_exit'] = node

        return ast_nodes
