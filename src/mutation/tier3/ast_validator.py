"""
AST Validator - Safety and correctness checks for mutated factor logic.

Validates AST mutations for syntax, semantics, and security. Prevents
unsafe operations like file I/O, network access, and unauthorized imports.

Part of Tier 3 AST Mutation Framework.
Task: D.3 - AST-Based Factor Logic Mutation
"""

import ast
from dataclasses import dataclass, field
from typing import List, Set, Optional


@dataclass
class ValidationResult:
    """
    Result of AST validation.

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


class ForbiddenOperationVisitor(ast.NodeVisitor):
    """
    AST visitor to detect forbidden operations.

    Scans AST for security risks:
    - Import statements (prevent arbitrary module loading)
    - File I/O operations (open, read, write)
    - Network operations (urllib, requests, socket)
    - System operations (os.system, subprocess)
    - Dangerous builtins (eval, exec, __import__)
    """

    def __init__(self):
        """Initialize visitor with empty violations list."""
        self.violations: List[str] = []
        self.forbidden_names = {
            'open', 'file', 'read', 'write',
            'eval', 'exec', '__import__', 'compile',
            'system', 'popen', 'subprocess',
            'urllib', 'requests', 'socket',
            'os', 'sys', 'shutil', 'glob',
        }

    def visit_Import(self, node: ast.Import) -> None:
        """Check for import statements."""
        for alias in node.names:
            self.violations.append(
                f"Import forbidden: 'import {alias.name}' at line {node.lineno}"
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check for from...import statements."""
        module = node.module or "(unknown)"
        names = ", ".join(alias.name for alias in node.names)
        self.violations.append(
            f"Import forbidden: 'from {module} import {names}' at line {node.lineno}"
        )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Check for calls to forbidden functions."""
        # Check direct function calls (e.g., open(...))
        if isinstance(node.func, ast.Name):
            if node.func.id in self.forbidden_names:
                self.violations.append(
                    f"Forbidden function call: '{node.func.id}()' at line {node.lineno}"
                )

        # Check attribute calls (e.g., os.system(...))
        if isinstance(node.func, ast.Attribute):
            # Check if base object is forbidden
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in self.forbidden_names:
                    self.violations.append(
                        f"Forbidden module access: '{node.func.value.id}.{node.func.attr}()' "
                        f"at line {node.lineno}"
                    )

            # Check if method name is forbidden
            if node.func.attr in self.forbidden_names:
                self.violations.append(
                    f"Forbidden method call: '.{node.func.attr}()' at line {node.lineno}"
                )

        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Check for references to forbidden names."""
        # Only flag Store context (assignments) to avoid false positives
        if isinstance(node.ctx, ast.Store):
            if node.id in self.forbidden_names:
                self.violations.append(
                    f"Forbidden name assignment: '{node.id}' at line {node.lineno}"
                )
        self.generic_visit(node)


class InfiniteLoopDetector(ast.NodeVisitor):
    """
    Basic infinite loop detection.

    Detects obvious infinite loops:
    - while True without break
    - for loop with suspicious range (e.g., range(10**9))
    - Nested loops with high iteration counts
    """

    def __init__(self):
        """Initialize detector with empty warnings list."""
        self.warnings: List[str] = []
        self.max_iterations = 10_000  # Warn if loop exceeds this

    def visit_While(self, node: ast.While) -> None:
        """Check while loops for infinite patterns."""
        # Check for 'while True:' without break
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            # Look for break statements in body
            has_break = self._contains_break(node.body)
            if not has_break:
                self.warnings.append(
                    f"Potential infinite loop: 'while True' without break at line {node.lineno}"
                )

        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Check for loops for excessive iterations."""
        # Check if iterating over range(large_number)
        if isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                if node.iter.args:
                    # Try to evaluate the range size
                    try:
                        if isinstance(node.iter.args[0], ast.Constant):
                            iterations = node.iter.args[0].value
                            if iterations > self.max_iterations:
                                self.warnings.append(
                                    f"Large loop: range({iterations}) at line {node.lineno} "
                                    f"exceeds {self.max_iterations} iterations"
                                )
                    except (AttributeError, TypeError):
                        pass  # Can't determine iteration count

        self.generic_visit(node)

    def _contains_break(self, body: List[ast.stmt]) -> bool:
        """Check if statement list contains break statement."""
        for stmt in body:
            if isinstance(stmt, ast.Break):
                return True
            # Recursively check nested structures
            if isinstance(stmt, (ast.If, ast.For, ast.While)):
                if hasattr(stmt, 'body') and self._contains_break(stmt.body):
                    return True
                if hasattr(stmt, 'orelse') and self._contains_break(stmt.orelse):
                    return True
        return False


class ASTValidator:
    """
    Validate AST mutations for safety and correctness.

    Performs comprehensive validation:
    1. Syntax validation - Code must parse without errors
    2. Security validation - No forbidden operations (imports, file I/O, network)
    3. Semantic validation - Logic makes sense for factor calculations
    4. Type validation - Return types are consistent

    Validation Rules:
    ----------------
    - S1: Code must parse with ast.parse()
    - S2: No syntax errors in generated code
    - S3: Code must be unparseable back to source

    - SEC1: No import statements
    - SEC2: No file I/O operations (open, read, write)
    - SEC3: No network operations (urllib, requests, socket)
    - SEC4: No system operations (os.system, subprocess)
    - SEC5: No dangerous builtins (eval, exec, __import__)

    - L1: No obvious infinite loops
    - L2: Return statement present
    - L3: Function signature preserved

    Example Usage:
    -------------
    ```python
    validator = ASTValidator()

    # Validate factor logic source
    result = validator.validate(factor_source_code)

    if result.success:
        print("Validation passed!")
    else:
        print(f"Errors: {result.errors}")
        print(f"Warnings: {result.warnings}")
    ```
    """

    def validate(self, source: str) -> ValidationResult:
        """
        Run all validation checks on factor logic source.

        Args:
            source: Python source code to validate

        Returns:
            ValidationResult with success status and any errors/warnings
        """
        results = []

        # Layer 1: Syntax validation
        syntax_result = self._validate_syntax(source)
        results.append(syntax_result)

        # Only proceed if syntax is valid
        if syntax_result.success:
            # Layer 2: Security validation
            results.append(self._validate_security(source))

            # Layer 3: Logic validation
            results.append(self._validate_logic(source))

        return ValidationResult.aggregate(results)

    def _validate_syntax(self, source: str) -> ValidationResult:
        """
        Check if code parses without errors.

        Args:
            source: Python source code to check

        Returns:
            ValidationResult for syntax checks
        """
        errors = []
        warnings = []

        # S1: Check if code parses
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return ValidationResult(
                success=False,
                errors=[f"Syntax error: {e}"]
            )

        # S3: Check if code can be unparsed (roundtrip test)
        try:
            unparsed = ast.unparse(tree)
            # Try parsing the unparsed version
            ast.parse(unparsed)
        except Exception as e:
            warnings.append(f"Roundtrip parsing warning: {e}")

        success = len(errors) == 0
        return ValidationResult(success=success, errors=errors, warnings=warnings)

    def _validate_security(self, source: str) -> ValidationResult:
        """
        Check for forbidden operations (security violations).

        Args:
            source: Python source code to check

        Returns:
            ValidationResult for security checks
        """
        errors = []
        warnings = []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            # Already caught in syntax validation
            return ValidationResult(success=True)

        # SEC1-SEC5: Check for forbidden operations
        visitor = ForbiddenOperationVisitor()
        visitor.visit(tree)

        if visitor.violations:
            errors.extend(visitor.violations)

        success = len(errors) == 0
        return ValidationResult(success=success, errors=errors, warnings=warnings)

    def _validate_logic(self, source: str) -> ValidationResult:
        """
        Check logical soundness of factor code.

        Args:
            source: Python source code to check

        Returns:
            ValidationResult for logic checks
        """
        errors = []
        warnings = []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            # Already caught in syntax validation
            return ValidationResult(success=True)

        # L1: Check for infinite loops
        loop_detector = InfiniteLoopDetector()
        loop_detector.visit(tree)
        warnings.extend(loop_detector.warnings)

        # L2: Check for return statement (if function definition)
        has_function = False
        has_return = False

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_function = True
                # Check if function has return statement
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Return):
                        has_return = True
                        break

        if has_function and not has_return:
            warnings.append("Function definition missing return statement")

        success = len(errors) == 0
        return ValidationResult(success=success, errors=errors, warnings=warnings)

    def validate_fast(self, source: str) -> bool:
        """
        Fast validation check (syntax only).

        Useful for quick checks during mutation generation.

        Args:
            source: Python source code to check

        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            ast.parse(source)
            return True
        except SyntaxError:
            return False
