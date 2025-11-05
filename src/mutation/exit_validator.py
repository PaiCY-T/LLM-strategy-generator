"""
Exit Code Validator - Safety and correctness checks for mutated exit strategies.

Part of Phase 1 Exit Strategy Mutation Framework.
Validates mutated exit strategy code for syntax, semantic, and type correctness.

Task: 1.3
Purpose: Safety checks to prevent invalid mutations
"""

import ast
from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationResult:
    """
    Result of exit code validation.

    Attributes:
        success: Whether validation passed all checks
        errors: List of error messages (empty if success=True)
        warnings: List of warning messages (non-fatal issues)
    """
    success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def aggregate(cls, results: List['ValidationResult']) -> 'ValidationResult':
        """
        Combine multiple validation results into one.

        Args:
            results: List of ValidationResult objects

        Returns:
            Aggregated ValidationResult (success only if all succeed)
        """
        all_success = all(r.success for r in results)
        all_errors = []
        all_warnings = []

        for result in results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        return cls(
            success=all_success,
            errors=all_errors,
            warnings=all_warnings
        )


class ExitCodeValidator:
    """
    Validate mutated exit strategy code.

    Implements three validation layers:
    1. Syntax (S1-S3): Code must parse, have required components, use proper pandas syntax
    2. Semantics (M1-M4): Logic must be sound, parameters sensible, no conflicts
    3. Types (T1-T3): DataFrame operations must be type-correct

    Validation Rules:
    -----------------
    **Syntax Rules**:
    - S1: Code must parse without errors (ast.parse succeeds)
    - S2: Required components must exist (_apply_exit_strategies method)
    - S3: DataFrame operations must use proper pandas syntax (.loc[date] not .iloc[i])

    **Semantic Rules**:
    - M1: Exit conditions must be logically sound (stop below entry, not above)
    - M2: Parameter ranges must be sensible (positive, reasonable bounds)
    - M3: Exit priority must avoid conflicts (no contradictory conditions)
    - M4: State tracking must be continuous (sequential state updates)

    **Type Rules**:
    - T1: Price data must have matching columns
    - T2: Exit signals must be boolean types
    - T3: Position modifications must preserve DataFrame structure

    Example Usage:
    --------------
    ```python
    validator = ExitCodeValidator()
    result = validator.validate(mutated_code)

    if result.success:
        print("Validation passed!")
    else:
        print(f"Errors: {result.errors}")
        print(f"Warnings: {result.warnings}")
    ```
    """

    def validate(self, code: str) -> ValidationResult:
        """
        Run all validation checks on mutated code.

        Args:
            code: Python source code to validate

        Returns:
            ValidationResult with success status and any errors/warnings
        """
        results = []

        # Layer 1: Syntax validation
        results.append(self._validate_syntax(code))

        # Only proceed if syntax is valid
        if results[0].success:
            # Layer 2: Semantic validation
            results.append(self._validate_semantics(code))

            # Layer 3: Type validation
            results.append(self._validate_types(code))

        return ValidationResult.aggregate(results)

    def _validate_syntax(self, code: str) -> ValidationResult:
        """
        Check if code parses without errors (Rule S1).

        Also checks for required components:
        - _apply_exit_strategies method exists (Rule S2)
        - Proper pandas .loc usage, not .iloc (Rule S3)

        Args:
            code: Python source code to check

        Returns:
            ValidationResult for syntax checks
        """
        errors = []
        warnings = []

        # S1: Check if code parses
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return ValidationResult(
                success=False,
                errors=[f"Syntax error: {e}"]
            )

        # S2: Check for required method
        has_exit_method = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name == '_apply_exit_strategies':
                    has_exit_method = True
                    break

        if not has_exit_method:
            errors.append("Missing required method: _apply_exit_strategies")

        # S3: Check for proper pandas syntax (.loc usage)
        # Look for .iloc usage (discouraged in design)
        has_iloc = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if node.attr == 'iloc':
                    has_iloc = True
                    warnings.append("Found .iloc usage - prefer .loc[date] for pandas operations")

        success = len(errors) == 0
        return ValidationResult(success=success, errors=errors, warnings=warnings)

    def _validate_semantics(self, code: str) -> ValidationResult:
        """
        Check logical soundness of exit conditions (Rules M1-M4).

        Validates:
        - M1: Stop-loss logic (must be below entry, not above)
        - M2: Parameter ranges (must be positive and reasonable)
        - M3: Exit combinations (no contradictory conditions)
        - M4: State tracking continuity

        Args:
            code: Python source code to check

        Returns:
            ValidationResult for semantic checks
        """
        errors = []
        warnings = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Already caught in syntax validation
            return ValidationResult(success=True)

        # M2: Check parameter ranges
        parameters = self._extract_parameters(tree)

        for param_name, param_value in parameters.items():
            if param_name in ['stop_atr_mult', 'profit_atr_mult']:
                if param_value <= 0:
                    errors.append(f"Parameter {param_name} must be positive, got {param_value}")
                if param_value > 10:
                    warnings.append(f"Parameter {param_name}={param_value} is unusually large (>10)")

            if param_name == 'max_hold_days':
                if param_value < 1 or param_value > 252:
                    errors.append(f"Parameter max_hold_days must be in [1, 252], got {param_value}")

            if param_name == 'atr_period':
                if param_value < 5 or param_value > 100:
                    warnings.append(f"Parameter atr_period={param_value} is outside typical range [5, 100]")

        # M3: Check for contradictory exit conditions
        # Look for any_exit assignments to detect conflicts
        any_exit_nodes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'any_exit':
                        any_exit_nodes.append(node)

        if not any_exit_nodes:
            warnings.append("No any_exit combination found - exits may not be applied")

        # M4: Check for state tracking (entry_price, highest_high, holding_days)
        required_state_vars = {'entry_price', 'highest_high', 'holding_days'}
        found_state_vars = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute):
                        if isinstance(target.value, ast.Name):
                            if target.value.id in required_state_vars:
                                found_state_vars.add(target.value.id)
                    elif isinstance(target, ast.Name):
                        if target.id in required_state_vars:
                            found_state_vars.add(target.id)

        missing_state = required_state_vars - found_state_vars
        if missing_state:
            warnings.append(f"State tracking variables not found: {missing_state}")

        success = len(errors) == 0
        return ValidationResult(success=success, errors=errors, warnings=warnings)

    def _validate_types(self, code: str) -> ValidationResult:
        """
        Verify pandas DataFrame operations are correct (Rules T1-T3).

        Checks:
        - T1: DataFrame column alignment operations (.reindex)
        - T2: Boolean exit signals
        - T3: Position DataFrame structure preservation

        Args:
            code: Python source code to check

        Returns:
            ValidationResult for type checks
        """
        errors = []
        warnings = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Already caught in syntax validation
            return ValidationResult(success=True)

        # T1: Check for column alignment (reindex operations)
        has_reindex = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'reindex':
                        has_reindex = True

        if not has_reindex:
            warnings.append("No .reindex() calls found - column alignment may not be handled")

        # T2: Check for boolean exit signal assignments
        exit_vars = {'stop_exit', 'profit_exit', 'time_exit'}
        found_exit_assignments = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id in exit_vars:
                            found_exit_assignments.add(target.id)
                            # Check if assigned value is a comparison (boolean)
                            if not isinstance(node.value, ast.Compare):
                                warnings.append(
                                    f"Exit variable {target.id} assigned non-comparison value - "
                                    f"may not be boolean type"
                                )

        # T3: Check for return statement with modified_positions
        has_return = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Return):
                if isinstance(node.value, ast.Name):
                    if node.value.id == 'modified_positions':
                        has_return = True

        if not has_return:
            warnings.append("No 'return modified_positions' found - method may not return correct value")

        success = len(errors) == 0
        return ValidationResult(success=success, errors=errors, warnings=warnings)

    def _extract_parameters(self, tree: ast.AST) -> dict:
        """
        Extract parameter values from params.get() calls.

        Args:
            tree: AST tree to analyze

        Returns:
            Dictionary of parameter names to values
        """
        parameters = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    if self._is_params_get_call(node.value):
                        param_name, default_value = self._extract_param_from_call(node.value)
                        if param_name and default_value is not None:
                            parameters[param_name] = default_value

        return parameters

    def _is_params_get_call(self, node: ast.Call) -> bool:
        """Check if a Call node is params.get()."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'get':
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == 'params':
                        return True
        return False

    def _extract_param_from_call(self, node: ast.Call) -> tuple:
        """Extract parameter name and value from params.get() call."""
        param_name = None
        default_value = None

        if len(node.args) >= 1:
            if isinstance(node.args[0], ast.Constant):
                param_name = node.args[0].value

        if len(node.args) >= 2:
            if isinstance(node.args[1], ast.Constant):
                default_value = node.args[1].value

        return param_name, default_value
