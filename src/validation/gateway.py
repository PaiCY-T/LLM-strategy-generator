"""ValidationGateway - Central orchestrator for all validation layers.

This module implements the ValidationGateway class which serves as the central
coordinator for all validation layers (Layer 1, Layer 2, Layer 3).

Key Features:
- Feature flag-based conditional initialization
- Layer dependency management (Layer 2 requires Layer 1)
- Field suggestions injection for LLM prompts
- Graceful degradation when layers are disabled
- Strategy code validation workflow (Task 3.2)

Architecture:
- Layer 1 (DataFieldManifest): Field name validation and suggestions
- Layer 2 (FieldValidator): AST-based code validation (requires Layer 1)
- Layer 3 (SchemaValidator): YAML schema validation (independent)

Usage:
    from src.validation.gateway import ValidationGateway

    # Initialize gateway (reads feature flags automatically)
    gateway = ValidationGateway()

    # Validate strategy code (Task 3.2)
    code = "def strategy(data): return data.get('close') > 100"
    result = gateway.validate_strategy(code)
    if not result.is_valid:
        for error in result.errors:
            print(f"Line {error.line}: {error.message}")

    # Inject field suggestions into LLM prompt
    if gateway.manifest:
        field_hints = gateway.inject_field_suggestions()
        prompt = f"{base_prompt}\n{field_hints}"

    # Use validators if enabled
    if gateway.field_validator:
        result = gateway.field_validator.validate(code)
        if not result.is_valid:
            print(result.errors)

    if gateway.schema_validator:
        errors = gateway.schema_validator.validate(yaml_dict)
        if errors:
            print(errors)

Requirements:
- AC3.1: Gateway initializes components based on feature flags
- AC3.2: Layer 2 requires Layer 1 to be enabled
- AC3.3: inject_field_suggestions() provides formatted field reference
- AC2.1: FieldValidator integrated into ValidationGateway (Task 3.2)
- AC2.2: validate_strategy() calls FieldValidator after YAML parsing (Task 3.2)
- NFR-P1: Layer 2 validation completes in <5ms (Task 3.2)
"""

from typing import Optional, Callable, Tuple

from src.config.feature_flags import FeatureFlagManager
from src.config.data_fields import DataFieldManifest
from src.validation.field_validator import FieldValidator
from src.execution.schema_validator import SchemaValidator


class ValidationGateway:
    """Central orchestrator for all validation layers.

    Manages Layer 1 (DataFieldManifest), Layer 2 (FieldValidator),
    and Layer 3 (SchemaValidator) based on feature flags.

    This class provides a unified interface for all validation functionality,
    with conditional initialization based on ENABLE_VALIDATION_LAYER1/2/3
    environment variables. It ensures proper dependency management (Layer 2
    requires Layer 1) and provides field suggestion injection for LLM prompts.

    Attributes:
        manifest: Optional DataFieldManifest for field validation (Layer 1)
        field_validator: Optional FieldValidator for code validation (Layer 2)
        schema_validator: Optional SchemaValidator for YAML validation (Layer 3)

    Example:
        >>> # Initialize with all layers disabled (default)
        >>> gateway = ValidationGateway()
        >>> assert gateway.manifest is None
        >>> assert gateway.field_validator is None
        >>> assert gateway.schema_validator is None

        >>> # Initialize with Layer 1 enabled
        >>> os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        >>> gateway = ValidationGateway()
        >>> assert gateway.manifest is not None
        >>> field_suggestions = gateway.inject_field_suggestions()
        >>> assert "Valid Data Fields Reference" in field_suggestions
    """

    def __init__(self):
        """Initialize validation components based on feature flags.

        Reads feature flags from FeatureFlagManager and conditionally
        initializes validation components:

        - Layer 1 enabled → Initialize DataFieldManifest
        - Layer 2 enabled AND Layer 1 enabled → Initialize FieldValidator
        - Layer 3 enabled → Initialize SchemaValidator

        The initialization follows dependency rules:
        - Layer 2 requires Layer 1 (FieldValidator needs DataFieldManifest)
        - Layer 3 is independent
        - All layers default to disabled (fail-safe)

        Example:
            >>> # With Layer 1 and Layer 2 enabled
            >>> os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
            >>> os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
            >>> gateway = ValidationGateway()
            >>> assert gateway.manifest is not None
            >>> assert gateway.field_validator is not None
            >>> assert gateway.field_validator.manifest is gateway.manifest
        """
        # Get feature flags
        flags = FeatureFlagManager()

        # Layer 1: DataFieldManifest
        self.manifest: Optional[DataFieldManifest] = None
        if flags.is_layer1_enabled:
            self.manifest = DataFieldManifest()

        # Layer 2: FieldValidator (requires Layer 1)
        self.field_validator: Optional[FieldValidator] = None
        if flags.is_layer2_enabled and self.manifest is not None:
            self.field_validator = FieldValidator(self.manifest)

        # Layer 3: SchemaValidator (independent)
        self.schema_validator: Optional[SchemaValidator] = None
        if flags.is_layer3_enabled:
            self.schema_validator = SchemaValidator()

    def inject_field_suggestions(self) -> str:
        """Inject valid field names and corrections into LLM prompt.

        Generates formatted field suggestions for LLM prompt injection,
        including:
        - Valid field names by category (price, fundamental)
        - Common field corrections (21 entries from COMMON_CORRECTIONS)

        This method helps guide LLM to use correct field names, reducing
        the 29.4% field error rate observed in unguided generations.

        Returns:
            Formatted field suggestions string if Layer 1 enabled,
            empty string otherwise (graceful degradation)

        Example:
            >>> gateway = ValidationGateway()  # Layer 1 disabled
            >>> assert gateway.inject_field_suggestions() == ""

            >>> os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
            >>> gateway = ValidationGateway()
            >>> suggestions = gateway.inject_field_suggestions()
            >>> assert "Valid Data Fields Reference" in suggestions
            >>> assert "Common Field Corrections:" in suggestions
            >>> assert "price:成交量" in suggestions  # Common mistake
            >>> assert "price:成交金額" in suggestions  # Correction target
        """
        # Return empty string if Layer 1 disabled
        if self.manifest is None:
            return ""

        # Build field suggestions using helper methods
        sections = [
            "\n## Valid Data Fields Reference\n",
            "The following field names are valid for use in your strategy:",
            self._format_field_categories(),
            self._format_common_corrections(),
            "\nPlease use only these valid field names in your strategy code."
        ]

        return "\n".join(sections)

    def _format_field_categories(self) -> str:
        """Format valid fields by category for LLM prompt.

        Returns:
            Formatted string with price and fundamental fields

        Example:
            >>> # Internal helper method
            >>> gateway = ValidationGateway()
            >>> if gateway.manifest:
            ...     formatted = gateway._format_field_categories()
            ...     assert "Price Fields:" in formatted
        """
        lines = []

        # Get fields by category
        price_fields = self.manifest.get_fields_by_category('price')
        fundamental_fields = self.manifest.get_fields_by_category('fundamental')

        # Format price fields
        if price_fields:
            lines.append("\nPrice Fields:")
            for field in price_fields:
                alias_hint = f" (alias: {field.aliases[0]})" if field.aliases else ""
                lines.append(f"- {field.canonical_name}{alias_hint}")

        # Format fundamental fields
        if fundamental_fields:
            lines.append("\nFundamental Fields:")
            for field in fundamental_fields:
                alias_hint = f" (alias: {field.aliases[0]})" if field.aliases else ""
                lines.append(f"- {field.canonical_name}{alias_hint}")

        return "\n".join(lines)

    def _format_common_corrections(self) -> str:
        """Format common field corrections for LLM prompt.

        Returns:
            Formatted string with all 21 common corrections

        Example:
            >>> # Internal helper method
            >>> gateway = ValidationGateway()
            >>> if gateway.manifest:
            ...     formatted = gateway._format_common_corrections()
            ...     assert "Common Field Corrections:" in formatted
        """
        lines = ["\nCommon Field Corrections:"]

        # Get corrections from DataFieldManifest
        corrections = DataFieldManifest.COMMON_CORRECTIONS

        # Format each correction in sorted order
        for wrong_field, correct_field in sorted(corrections.items()):
            lines.append(f'- "{wrong_field}" → "{correct_field}"')

        return "\n".join(lines)

    def validate_strategy(self, strategy_code: str) -> 'ValidationResult':
        """Validate strategy code through enabled validation layers.

        Validates strategy code using Layer 2 (FieldValidator) if enabled.
        This method is called after YAML parsing but before execution to catch
        field errors early in the validation pipeline.

        Validation Flow:
            1. Check if Layer 2 (FieldValidator) is enabled
            2. If enabled, parse code with AST and validate field usage
            3. Return structured ValidationResult with FieldError objects
            4. If disabled, return valid result (graceful degradation)

        Args:
            strategy_code: Python code string to validate. Must be syntactically
                          valid Python code containing strategy logic.

        Returns:
            ValidationResult: Structured result with validation outcome.
                - is_valid: True if no errors found, False otherwise
                - errors: List of FieldError objects with line/column info
                - warnings: List of non-critical warnings (if any)

        Performance:
            - Layer 2 validation: <5ms per validation (NFR-P1)
            - AST parsing overhead: ~1-2ms
            - Field validation: O(1) dict lookups

        Raises:
            No exceptions raised - all errors captured in ValidationResult

        Requirements:
            - AC2.1: FieldValidator integrated into ValidationGateway
            - AC2.2: Call FieldValidator.validate() after YAML parsing
            - NFR-P1: Layer 2 performance <5ms per validation

        Example:
            >>> # With Layer 2 enabled
            >>> import os
            >>> os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
            >>> os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
            >>> gateway = ValidationGateway()
            >>>
            >>> # Valid code passes
            >>> code = "def strategy(data):\\n    return data.get('close') > 100"
            >>> result = gateway.validate_strategy(code)
            >>> assert result.is_valid is True
            >>> assert len(result.errors) == 0
            >>>
            >>> # Invalid code fails with structured errors
            >>> code = "def strategy(data):\\n    return data.get('price:成交量') > 100"
            >>> result = gateway.validate_strategy(code)
            >>> assert result.is_valid is False
            >>> assert len(result.errors) > 0
            >>> assert result.errors[0].line > 0
            >>> assert result.errors[0].suggestion is not None
            >>>
            >>> # With Layer 2 disabled (graceful degradation)
            >>> os.environ['ENABLE_VALIDATION_LAYER2'] = 'false'
            >>> gateway = ValidationGateway()
            >>> result = gateway.validate_strategy(code)
            >>> assert result.is_valid is True  # No validation performed
        """
        # Import ValidationResult here to avoid circular imports
        from src.validation.validation_result import ValidationResult

        # Layer 2: FieldValidator (AST-based code validation)
        if self.field_validator is not None:
            # Call FieldValidator.validate() method
            # This performs:
            # 1. AST parsing for line/column tracking
            # 2. Field name validation against DataFieldManifest
            # 3. Auto-correction suggestions for common mistakes
            result = self.field_validator.validate(strategy_code)
            return result

        # No validation layers enabled - return valid result (graceful degradation)
        # This ensures backward compatibility when Layer 2 is disabled
        return ValidationResult()

    def validate_and_retry(
        self,
        llm_generate_func: Callable[[str], str],
        initial_prompt: str,
        max_retries: int = 3
    ) -> Tuple[str, 'ValidationResult']:
        """Validate LLM-generated code and retry with error feedback if invalid.

        Integrates ErrorFeedbackLoop for automatic retry when code validation fails.
        Uses Layer 2 (FieldValidator) to validate generated code and provides
        structured error feedback to the LLM for correction.

        Validation & Retry Flow:
            1. Generate code using llm_generate_func with initial_prompt
            2. Validate code using validate_strategy()
            3. If valid: return code and ValidationResult
            4. If invalid: generate retry prompt with errors
            5. Repeat steps 1-4 up to max_retries times
            6. Return last code and ValidationResult (even if invalid)

        Args:
            llm_generate_func: Callable that takes prompt string and returns generated code.
                              Signature: (prompt: str) -> str
                              Example: lambda p: openai.generate(p)
            initial_prompt: Initial prompt for LLM generation
                           Should include strategy requirements and field references
            max_retries: Maximum retry attempts (default: 3)
                        Range: 1-10 recommended
                        0 = no retries (single attempt)

        Returns:
            Tuple of (final_code, final_validation_result):
                - final_code: Last generated code (may be invalid if retries exhausted)
                - final_validation_result: ValidationResult from last validation

        Performance:
            - Retry overhead: ~5-10ms per retry (validation + prompt generation)
            - LLM call time not included (depends on LLM provider)

        Requirements:
            - AC2.4: ErrorFeedbackLoop integrated into ValidationGateway
            - AC2.5: Retry prompt includes validation errors and suggestions
            - Task 4.1: Automatic retry mechanism integration
            - Task 4.2: Retry prompt generation with field errors

        Example:
            >>> import os
            >>> os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
            >>> os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
            >>> gateway = ValidationGateway()
            >>>
            >>> # Define LLM generation function
            >>> def my_llm(prompt: str) -> str:
            ...     return generate_strategy_code(prompt)
            >>>
            >>> # Validate with automatic retry
            >>> code, result = gateway.validate_and_retry(
            ...     llm_generate_func=my_llm,
            ...     initial_prompt="Create a momentum strategy using close prices",
            ...     max_retries=3
            ... )
            >>>
            >>> if result.is_valid:
            ...     print(f"Success! Generated code:\\n{code}")
            ... else:
            ...     print(f"Failed after {max_retries + 1} attempts")
            ...     for error in result.errors:
            ...         print(f"  - {error}")
            >>>
            >>> # With Layer 2 disabled (graceful degradation)
            >>> os.environ['ENABLE_VALIDATION_LAYER2'] = 'false'
            >>> gateway = ValidationGateway()
            >>> code, result = gateway.validate_and_retry(my_llm, "Create strategy")
            >>> # Returns after single attempt (no validation to retry)
        """
        # Import here to avoid circular dependency
        from src.prompts.error_feedback import generate_retry_prompt_for_code

        # Execute retry loop
        return self._retry_with_feedback(
            llm_generate_func=llm_generate_func,
            initial_prompt=initial_prompt,
            max_retries=max_retries
        )

    def _retry_with_feedback(
        self,
        llm_generate_func: Callable[[str], str],
        initial_prompt: str,
        max_retries: int
    ) -> Tuple[str, 'ValidationResult']:
        """Execute retry loop with error feedback.

        Internal helper method that orchestrates the validation-retry cycle.
        Separated for cleaner code organization and easier testing.

        Args:
            llm_generate_func: LLM code generation function
            initial_prompt: Initial prompt for generation
            max_retries: Maximum retry attempts

        Returns:
            Tuple of (final_code, final_validation_result)
        """
        from src.prompts.error_feedback import generate_retry_prompt_for_code

        current_prompt = initial_prompt

        for attempt_number in range(max_retries + 1):
            # Generate code
            code = llm_generate_func(current_prompt)

            # Validate generated code
            result = self.validate_strategy(code)

            # Early exit conditions
            if result.is_valid:
                return code, result

            if self.field_validator is None:
                # No validation layer to guide retry - return immediately
                return code, result

            # Generate retry prompt if not last attempt
            if attempt_number < max_retries:
                current_prompt = generate_retry_prompt_for_code(
                    original_code=code,
                    field_errors=result.errors,
                    attempt_number=attempt_number + 1
                )

        # Max retries exhausted
        return code, result
