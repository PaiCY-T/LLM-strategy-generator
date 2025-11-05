"""
Exit Mutation Operator - Unified interface for exit strategy mutations.

Part of Phase 1 Exit Strategy Mutation Framework.
Integrates detector, mutator, and validator into a single operator.

Task: 1.4
Purpose: Unified interface for exit strategy mutation pipeline
"""

import ast
from typing import Optional

from src.mutation.exit_detector import ExitMechanismDetector, ExitStrategyProfile
from src.mutation.exit_mutator import ExitStrategyMutator, MutationConfig
from src.mutation.exit_validator import ExitCodeValidator, ValidationResult


class ExitMutationOperator:
    """
    Unified operator for exit strategy mutations.

    Integrates the full mutation pipeline:
    1. Detect current exit strategy (ExitMechanismDetector)
    2. Apply mutation (ExitStrategyMutator)
    3. Validate mutated code (ExitCodeValidator)
    4. Generate Python code (ast.unparse)
    5. Retry with different mutations if validation fails (max 3 attempts)

    Example Usage:
    --------------
    ```python
    operator = ExitMutationOperator()
    config = MutationConfig(seed=42)

    # Mutate exit strategy code
    result = operator.mutate_exit_strategy(original_code, config)

    if result.success:
        print(f"Mutation successful!")
        print(f"New code: {result.code}")
    else:
        print(f"Mutation failed: {result.errors}")
    ```
    """

    def __init__(self, max_retries: int = 3):
        """
        Initialize operator with component instances.

        Args:
            max_retries: Maximum mutation attempts if validation fails
        """
        self.detector = ExitMechanismDetector()
        self.mutator = ExitStrategyMutator()
        self.validator = ExitCodeValidator()
        self.max_retries = max_retries

    def mutate_exit_strategy(
        self,
        code: str,
        config: Optional[MutationConfig] = None
    ) -> 'MutationResult':
        """
        Apply mutation to exit strategy code with validation and retry.

        Pipeline:
        ---------
        1. Detect current exit strategy profile
        2. Apply mutation to AST
        3. Generate new Python code
        4. Validate mutated code
        5. Retry with different mutation if validation fails (max 3 attempts)

        Args:
            code: Original Python source code with exit strategies
            config: Mutation configuration (uses default if None)

        Returns:
            MutationResult with success status, code, and validation details
        """
        if config is None:
            config = MutationConfig()

        # Step 1: Detect current exit strategy
        try:
            profile = self.detector.detect(code)
        except Exception as e:
            return MutationResult(
                success=False,
                code=code,
                errors=[f"Detection failed: {e}"],
                profile=None,
                validation_result=None
            )

        if not profile.mechanisms:
            return MutationResult(
                success=False,
                code=code,
                errors=["No exit mechanisms detected in code"],
                profile=profile,
                validation_result=None
            )

        # Try mutation with retries
        for attempt in range(self.max_retries):
            try:
                # Step 2: Apply mutation
                mutated_ast = self.mutator.mutate(profile, config)

                # Step 3: Generate code
                new_code = ast.unparse(mutated_ast)

                # Step 4: Validate
                validation_result = self.validator.validate(new_code)

                if validation_result.success:
                    # Success! Return mutated code
                    return MutationResult(
                        success=True,
                        code=new_code,
                        errors=[],
                        warnings=validation_result.warnings,
                        profile=profile,
                        validation_result=validation_result,
                        attempts=attempt + 1
                    )

                # Validation failed, will retry with different mutation
                # (unless this is the last attempt)
                if attempt == self.max_retries - 1:
                    return MutationResult(
                        success=False,
                        code=new_code,
                        errors=validation_result.errors,
                        warnings=validation_result.warnings,
                        profile=profile,
                        validation_result=validation_result,
                        attempts=attempt + 1
                    )

            except Exception as e:
                # Mutation or generation failed
                if attempt == self.max_retries - 1:
                    return MutationResult(
                        success=False,
                        code=code,
                        errors=[f"Mutation failed after {self.max_retries} attempts: {e}"],
                        profile=profile,
                        validation_result=None,
                        attempts=attempt + 1
                    )

        # Should not reach here, but safety fallback
        return MutationResult(
            success=False,
            code=code,
            errors=["Mutation failed after all retry attempts"],
            profile=profile,
            validation_result=None,
            attempts=self.max_retries
        )

    def detect_profile(self, code: str) -> ExitStrategyProfile:
        """
        Detect exit strategy profile without mutation.

        Utility method for analyzing code without applying mutations.

        Args:
            code: Python source code to analyze

        Returns:
            ExitStrategyProfile with detected characteristics
        """
        return self.detector.detect(code)

    def validate_code(self, code: str) -> ValidationResult:
        """
        Validate exit strategy code without mutation.

        Utility method for checking code validity without applying mutations.

        Args:
            code: Python source code to validate

        Returns:
            ValidationResult with validation status
        """
        return self.validator.validate(code)


class MutationResult:
    """
    Result of exit strategy mutation operation.

    Attributes:
        success: Whether mutation and validation succeeded
        code: Generated Python code (mutated if success=True, original if failed)
        errors: List of error messages (empty if success=True)
        warnings: List of warning messages (non-fatal issues)
        profile: Detected exit strategy profile
        validation_result: Validation result from validator
        attempts: Number of mutation attempts made
    """

    def __init__(
        self,
        success: bool,
        code: str,
        errors: list = None,
        warnings: list = None,
        profile: Optional[ExitStrategyProfile] = None,
        validation_result: Optional[ValidationResult] = None,
        attempts: int = 1
    ):
        self.success = success
        self.code = code
        self.errors = errors or []
        self.warnings = warnings or []
        self.profile = profile
        self.validation_result = validation_result
        self.attempts = attempts

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"MutationResult(status={status}, attempts={self.attempts}, "
            f"errors={len(self.errors)}, warnings={len(self.warnings)})"
        )

    def summary(self) -> str:
        """
        Generate human-readable summary of mutation result.

        Returns:
            Multi-line string with mutation details
        """
        lines = []
        lines.append(f"Mutation Status: {'SUCCESS' if self.success else 'FAILED'}")
        lines.append(f"Attempts: {self.attempts}")

        if self.profile:
            lines.append(f"Detected Mechanisms: {', '.join(self.profile.mechanisms)}")
            lines.append(f"Parameters: {self.profile.parameters}")

        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  - {error}")

        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)
