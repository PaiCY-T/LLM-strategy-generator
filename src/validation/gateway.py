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

from typing import Optional, Callable, Tuple, Dict, Any, List
import hashlib
import logging
import os
import threading
import time
from datetime import datetime, timezone

from src.config.feature_flags import FeatureFlagManager
from src.config.data_fields import DataFieldManifest
from src.validation.field_validator import FieldValidator
from src.execution.schema_validator import SchemaValidator

logger = logging.getLogger(__name__)


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

        # Thread Safety: Lock for concurrent access to shared state (Task 8.3 - H3)
        self._lock = threading.Lock()

        # Circuit Breaker: Error signature tracking (Task 6.1)
        self.error_signatures: Dict[str, int] = {}

        # Circuit Breaker: Activation logic (Task 6.2 + Task 8.2 - H2)
        self.circuit_breaker_threshold: int = self._validate_circuit_breaker_threshold()
        self.circuit_breaker_triggered: bool = False

        # Metrics Collector: Optional metrics tracking (Task 6.5)
        self.metrics_collector: Optional['MetricsCollector'] = None

        # LLM Success Rate Tracking (Task 7.3)
        self.llm_validation_stats: Dict[str, int] = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0
        }

    def _validate_circuit_breaker_threshold(self) -> int:
        """Validate CIRCUIT_BREAKER_THRESHOLD environment variable (Task 8.2 - H2).

        Validates that the circuit breaker threshold is within acceptable range
        (1-10) and provides clear warnings for invalid values. Falls back to
        default value of 2 for any invalid input.

        Valid Range Analysis:
        - Minimum: 1 (circuit breaker activates after first identical error)
        - Maximum: 10 (NFR-R3: prevent >10 identical retry attempts)
        - Default: 2 (balance between resilience and early failure detection)
        - Invalid: negative, zero, >10, or non-numeric values

        Returns:
            int: Validated threshold value (1-10), or default (2) if invalid

        Example:
            >>> os.environ['CIRCUIT_BREAKER_THRESHOLD'] = '5'
            >>> gateway = ValidationGateway()
            >>> assert gateway.circuit_breaker_threshold == 5

            >>> os.environ['CIRCUIT_BREAKER_THRESHOLD'] = '15'
            >>> gateway = ValidationGateway()  # Logs warning
            >>> assert gateway.circuit_breaker_threshold == 2  # Falls back to default

            >>> os.environ['CIRCUIT_BREAKER_THRESHOLD'] = 'invalid'
            >>> gateway = ValidationGateway()  # Logs warning
            >>> assert gateway.circuit_breaker_threshold == 2  # Falls back to default
        """
        default_threshold = 2
        threshold_str = os.getenv('CIRCUIT_BREAKER_THRESHOLD', str(default_threshold))

        try:
            threshold = int(threshold_str)

            # Validate range (1-10)
            if not (1 <= threshold <= 10):
                logger.warning(
                    f"CIRCUIT_BREAKER_THRESHOLD={threshold} out of valid range [1,10]. "
                    f"Using default={default_threshold}. "
                    f"NFR-R3 requirement: threshold must be 1-10 to prevent excessive retries."
                )
                return default_threshold

            return threshold

        except ValueError:
            logger.warning(
                f"Invalid CIRCUIT_BREAKER_THRESHOLD='{threshold_str}' (not an integer). "
                f"Using default={default_threshold}. "
                f"Valid values: 1-10 integer."
            )
            return default_threshold

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

    def _hash_error_signature(self, error_message: str) -> str:
        """Hash error message to create unique signature.

        Uses SHA256 truncated to 16 hex characters (64 bits) for error tracking.

        **Collision Risk Analysis (Task 8.1 - H1)**:
        - Hash space: 16 hex chars = 64 bits = 2^64 possible values (18.4 quintillion)
        - Birthday paradox: ~50% collision probability after 2^32 errors (~4.3 billion)
        - Expected usage: ~120 validations/week ≈ 6,240/year ≈ 62,400 in 10 years
        - Collision probability in 1 year: < 0.000001% (negligible)
        - Collision probability in 10 years: < 0.00001% (extremely low)

        **Mitigation Strategy**:
        - Monitor unique signature count via circuit breaker metrics
        - Future enhancement: Use full hash (64 chars) if collision detected
        - Current implementation: Acceptable risk for production deployment

        References:
        - Birthday problem: https://en.wikipedia.org/wiki/Birthday_problem
        - NFR-R3: Circuit breaker prevents >10 identical retry attempts

        Args:
            error_message: The error message string

        Returns:
            SHA256 hash of the error message (first 16 chars for readability)
        """
        return hashlib.sha256(error_message.encode()).hexdigest()[:16]

    def _track_error_signature(self, error_message: str) -> None:
        """Track error signature frequency (Task 8.4 - M2: Thread-safe).

        Thread-safe error tracking using lock to prevent race conditions
        when multiple threads validate strategies concurrently.

        Args:
            error_message: The error message to track
        """
        sig = self._hash_error_signature(error_message)

        # Thread-safe modification of shared error_signatures dict
        with self._lock:
            self.error_signatures[sig] = self.error_signatures.get(sig, 0) + 1

    def _is_error_repeated(self, error_message: str, threshold: int = 2) -> bool:
        """Check if error signature has reached repeat threshold.

        Args:
            error_message: The error message to check
            threshold: Number of occurrences to trigger circuit breaker (default: 2)

        Returns:
            True if error has occurred >= threshold times
        """
        sig = self._hash_error_signature(error_message)
        return self.error_signatures.get(sig, 0) >= threshold

    def _reset_error_signatures(self) -> None:
        """Reset error signatures for new validation cycle."""
        self.error_signatures = {}

    def _should_trigger_circuit_breaker(self, error_message: str) -> bool:
        """Check if circuit breaker should trigger for this error.

        Args:
            error_message: The error message to check

        Returns:
            True if error has reached threshold and circuit breaker should trigger
        """
        return self._is_error_repeated(error_message, threshold=self.circuit_breaker_threshold)

    def _reset_circuit_breaker(self) -> None:
        """Reset circuit breaker for new validation cycle."""
        self.circuit_breaker_triggered = False
        self._reset_error_signatures()

    def set_metrics_collector(self, collector: 'MetricsCollector') -> None:
        """Set metrics collector for validation monitoring (Task 6.5).

        Args:
            collector: MetricsCollector instance for recording validation metrics
        """
        self.metrics_collector = collector

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

    def validate_yaml(self, yaml_dict: 'Dict[str, Any]') -> 'List[ValidationError]':
        """Validate YAML structure using Layer 3 (SchemaValidator).

        Validates YAML dictionary against expected schema before parsing to catch
        structure errors early in the validation pipeline.

        Validation Flow:
            1. Check if Layer 3 (SchemaValidator) is enabled
            2. If enabled, call schema_validator.validate() for structure validation
            3. Return list of ValidationError objects with severity and suggestions
            4. If disabled, return empty list (graceful degradation)

        Args:
            yaml_dict: Parsed YAML dictionary to validate. Should contain strategy
                      definition with required keys (name, type, required_fields,
                      parameters, logic).

        Returns:
            List of ValidationError objects (empty if valid or Layer 3 disabled).
            Each ValidationError contains:
                - severity: ValidationSeverity enum (ERROR, WARNING, INFO)
                - message: Human-readable error description
                - field_path: Dot-notation path to invalid field
                - line_number: Optional line number in YAML (if available)
                - suggestion: Optional fix suggestion

        Performance:
            - Layer 3 validation: <5ms per validation (NFR-P1)
            - Schema structure checking: ~1-2ms overhead
            - Total budget: <5ms for typical YAML structure

        Requirements:
            - AC3.1: SchemaValidator integrated into ValidationGateway
            - NFR-P1: Layer 3 validation completes in <5ms
            - Task 5.1: YAML structure validation before parsing

        Example:
            >>> import os
            >>> from typing import Dict, Any, List
            >>> os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'
            >>> gateway = ValidationGateway()
            >>>
            >>> # Valid YAML
            >>> yaml_dict: Dict[str, Any] = {
            ...     "name": "Test Strategy",
            ...     "type": "factor_graph",
            ...     "required_fields": ["close", "volume"],
            ...     "parameters": [{"name": "period", "type": "int", "value": 20}],
            ...     "logic": {"entry": "close > 100", "exit": "close < 90"}
            ... }
            >>> errors = gateway.validate_yaml(yaml_dict)
            >>> assert len(errors) == 0  # Valid YAML
            >>>
            >>> # Invalid YAML (missing required keys)
            >>> invalid_yaml: Dict[str, Any] = {"name": "Incomplete"}
            >>> errors = gateway.validate_yaml(invalid_yaml)
            >>> assert len(errors) > 0  # Validation errors returned
            >>> assert all(hasattr(e, 'severity') for e in errors)
            >>>
            >>> # With Layer 3 disabled (graceful degradation)
            >>> os.environ['ENABLE_VALIDATION_LAYER3'] = 'false'
            >>> gateway = ValidationGateway()
            >>> errors = gateway.validate_yaml(invalid_yaml)
            >>> assert len(errors) == 0  # No validation performed
        """
        # Import types here to avoid circular imports at module level
        from typing import Dict, Any, List
        from src.execution.schema_validator import ValidationError

        # Layer 3: SchemaValidator (YAML structure validation)
        if self.schema_validator is not None:
            # Call SchemaValidator.validate() method
            # This performs:
            # 1. Required keys validation (name, type, required_fields, parameters, logic)
            # 2. Data type validation for each section
            # 3. Field reference validation (if DataFieldManifest available)
            # 4. Parameter type validation
            # 5. Logic section structure validation
            # 6. Constraints validation (if present)
            errors: List[ValidationError] = self.schema_validator.validate(yaml_dict)
            return errors

        # No validation layer enabled - return empty list (graceful degradation)
        # This ensures backward compatibility when Layer 3 is disabled
        return []

    def validate_and_fix(self, yaml_dict: 'Dict[str, Any]') -> 'ValidationResult':
        """Validate YAML with metadata tracking across all enabled layers.

        Task 7.1: Validation Metadata Integration
        Validates YAML dictionary through all enabled validation layers and returns
        ValidationResult with comprehensive metadata tracking including per-layer
        latency, error counts, and execution results.

        Validation Flow:
            1. Initialize metadata tracking structures
            2. Execute Layer 3 (YAML validation) if enabled
            3. Track layer execution time, results, and error counts
            4. Compile ValidationResult with complete metadata
            5. Return structured result for monitoring and persistence

        Args:
            yaml_dict: Parsed YAML dictionary to validate through enabled layers

        Returns:
            ValidationResult with:
                - is_valid: True if all layers passed
                - errors: List of ValidationError objects (if any)
                - metadata: ValidationMetadata with execution tracking

        Performance:
            - Per-layer validation: <5ms (NFR-P1)
            - Metadata overhead: <1ms
            - Total budget: <10ms for typical YAML

        Requirements:
            - Task 7.1: Integrate validation metadata into validate_and_fix
            - Metadata includes layer info, latency, error counts
            - Metadata returned with validation results
            - Metadata persisted with strategy records

        Example:
            >>> import os
            >>> os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'
            >>> gateway = ValidationGateway()
            >>>
            >>> yaml_dict = {
            ...     "name": "Test Strategy",
            ...     "type": "factor_graph",
            ...     "required_fields": ["close"],
            ...     "parameters": [],
            ...     "logic": {"entry": "close > 100", "exit": "close < 90"}
            ... }
            >>>
            >>> result = gateway.validate_and_fix(yaml_dict)
            >>> print(result.is_valid)
            True
            >>> print(result.metadata.layers_executed)
            ['Layer3']
            >>> print(result.metadata.total_latency_ms < 5.0)
            True
        """
        # Import types here to avoid circular imports
        from typing import Dict, Any
        from src.validation.validation_result import ValidationResult, ValidationMetadata
        from src.execution.schema_validator import ValidationError

        # Initialize metadata tracking
        start_time = time.time()
        layers_executed: List[str] = []
        layer_results: Dict[str, bool] = {}
        layer_latencies: Dict[str, float] = {}
        error_counts: Dict[str, int] = {}
        all_errors: List['ValidationError'] = []

        # Layer 3: YAML Schema Validation
        if self.schema_validator is not None:
            layer_start = time.time()
            errors = self.schema_validator.validate(yaml_dict)
            layer_end = time.time()

            # Track Layer 3 execution
            layers_executed.append("Layer3")
            layer_latencies["Layer3"] = (layer_end - layer_start) * 1000  # Convert to ms
            error_counts["Layer3"] = len(errors)
            layer_results["Layer3"] = (len(errors) == 0)

            # Accumulate errors
            all_errors.extend(errors)

        # Calculate total latency
        total_latency_ms = (time.time() - start_time) * 1000

        # Create metadata (Task 8.3 - M9: Use Python 3.12+ compatible datetime API)
        metadata = ValidationMetadata(
            layers_executed=layers_executed,
            layer_results=layer_results,
            layer_latencies=layer_latencies,
            total_latency_ms=total_latency_ms,
            error_counts=error_counts,
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        )

        # Create ValidationResult
        # Note: ValidationError objects from schema_validator need to be converted
        # to FieldError objects for ValidationResult
        result = ValidationResult(metadata=metadata)

        # Convert ValidationError to FieldError if there are errors
        if all_errors:
            for error in all_errors:
                # Extract relevant info from ValidationError
                error_msg = getattr(error, 'message', str(error))
                field_path = getattr(error, 'field_path', 'unknown')

                result.add_error(
                    line=0,  # YAML validation doesn't have line numbers in dict form
                    column=0,
                    field_name=field_path,
                    error_type='yaml_validation',
                    message=error_msg,
                    suggestion=getattr(error, 'suggestion', None)
                )

        return result

    def validate_yaml_structure_types(self, yaml_input: Any) -> 'ValidationResult':
        """Validate YAML structure has correct types (Task 7.2).

        Validates that YAML input is a dictionary and required sections have
        correct types. Prevents type-related runtime errors by catching type
        mismatches early.

        Args:
            yaml_input: Input to validate (should be dict)

        Returns:
            ValidationResult with type errors (if any)

        Example:
            >>> gateway = ValidationGateway()
            >>> result = gateway.validate_yaml_structure_types({"name": "Test"})
            >>> print(result.is_valid)
            True
        """
        from src.validation.validation_result import ValidationResult

        result = ValidationResult()

        # Check if input is a dictionary
        if not isinstance(yaml_input, dict):
            result.add_error(
                line=0,
                column=0,
                field_name='yaml_root',
                error_type='type_error',
                message=f'Strategy YAML must be a dictionary, got {type(yaml_input).__name__}',
                suggestion='Ensure YAML is parsed as dict, not str or list'
            )
            return result

        # Validate required top-level keys exist
        required_keys = ['name', 'type', 'required_fields', 'parameters', 'logic']
        for key in required_keys:
            if key not in yaml_input:
                result.add_error(
                    line=0,
                    column=0,
                    field_name=key,
                    error_type='missing_key',
                    message=f'Required key "{key}" missing from YAML structure',
                    suggestion=f'Add "{key}" key to strategy YAML'
                )

        # Validate field types for existing keys
        if 'name' in yaml_input and not isinstance(yaml_input['name'], str):
            result.add_error(
                line=0,
                column=0,
                field_name='name',
                error_type='type_error',
                message=f'Field "name" must be string, got {type(yaml_input["name"]).__name__}',
                suggestion='Ensure "name" is a string value'
            )

        if 'type' in yaml_input and not isinstance(yaml_input['type'], str):
            result.add_error(
                line=0,
                column=0,
                field_name='type',
                error_type='type_error',
                message=f'Field "type" must be string, got {type(yaml_input["type"]).__name__}',
                suggestion='Ensure "type" is a string value (e.g., "factor_graph")'
            )

        if 'required_fields' in yaml_input and not isinstance(yaml_input['required_fields'], list):
            result.add_error(
                line=0,
                column=0,
                field_name='required_fields',
                error_type='type_error',
                message=f'Field "required_fields" must be list, got {type(yaml_input["required_fields"]).__name__}',
                suggestion='Ensure "required_fields" is a list of strings'
            )

        if 'parameters' in yaml_input and not isinstance(yaml_input['parameters'], list):
            result.add_error(
                line=0,
                column=0,
                field_name='parameters',
                error_type='type_error',
                message=f'Field "parameters" must be list, got {type(yaml_input["parameters"]).__name__}',
                suggestion='Ensure "parameters" is a list of parameter dicts'
            )

        if 'logic' in yaml_input and not isinstance(yaml_input['logic'], dict):
            result.add_error(
                line=0,
                column=0,
                field_name='logic',
                error_type='type_error',
                message=f'Field "logic" must be dict, got {type(yaml_input["logic"]).__name__}',
                suggestion='Ensure "logic" is a dictionary with entry/exit keys'
            )

        return result

    def validate_strategy_metrics_type(self, metrics: Any) -> 'ValidationResult':
        """Validate that metrics object is StrategyMetrics type (Task 7.2).

        Ensures metrics is a StrategyMetrics dataclass instance, not a dict.
        Prevents Phase 7 regression where dict was used instead of dataclass.

        Args:
            metrics: Metrics object to validate

        Returns:
            ValidationResult with type errors (if any)

        Example:
            >>> from src.backtest.metrics import StrategyMetrics
            >>> gateway = ValidationGateway()
            >>> metrics = StrategyMetrics(sharpe_ratio=1.5)
            >>> result = gateway.validate_strategy_metrics_type(metrics)
            >>> print(result.is_valid)
            True
        """
        from src.validation.validation_result import ValidationResult
        from src.backtest.metrics import StrategyMetrics

        result = ValidationResult()

        # Check if metrics is None
        if metrics is None:
            result.add_error(
                line=0,
                column=0,
                field_name='metrics',
                error_type='type_error',
                message='Metrics cannot be None',
                suggestion='Provide StrategyMetrics instance'
            )
            return result

        # Check if metrics is StrategyMetrics instance
        if not isinstance(metrics, StrategyMetrics):
            result.add_error(
                line=0,
                column=0,
                field_name='metrics',
                error_type='type_error',
                message=f'Metrics must be StrategyMetrics instance, got {type(metrics).__name__}',
                suggestion='Use StrategyMetrics.from_dict() to convert dict to StrategyMetrics'
            )
            return result

        # Validate field types within StrategyMetrics
        if metrics.sharpe_ratio is not None and not isinstance(metrics.sharpe_ratio, (int, float)):
            result.add_error(
                line=0,
                column=0,
                field_name='sharpe_ratio',
                error_type='type_error',
                message=f'sharpe_ratio must be float, got {type(metrics.sharpe_ratio).__name__}',
                suggestion='Ensure sharpe_ratio is numeric'
            )

        if metrics.total_return is not None and not isinstance(metrics.total_return, (int, float)):
            result.add_error(
                line=0,
                column=0,
                field_name='total_return',
                error_type='type_error',
                message=f'total_return must be float, got {type(metrics.total_return).__name__}',
                suggestion='Ensure total_return is numeric'
            )

        if metrics.max_drawdown is not None and not isinstance(metrics.max_drawdown, (int, float)):
            result.add_error(
                line=0,
                column=0,
                field_name='max_drawdown',
                error_type='type_error',
                message=f'max_drawdown must be float, got {type(metrics.max_drawdown).__name__}',
                suggestion='Ensure max_drawdown is numeric'
            )

        if metrics.win_rate is not None and not isinstance(metrics.win_rate, (int, float)):
            result.add_error(
                line=0,
                column=0,
                field_name='win_rate',
                error_type='type_error',
                message=f'win_rate must be float, got {type(metrics.win_rate).__name__}',
                suggestion='Ensure win_rate is numeric'
            )

        if not isinstance(metrics.execution_success, bool):
            result.add_error(
                line=0,
                column=0,
                field_name='execution_success',
                error_type='type_error',
                message=f'execution_success must be bool, got {type(metrics.execution_success).__name__}',
                suggestion='Ensure execution_success is True or False'
            )

        return result

    def validate_parameter_types(self, parameters: List[Dict[str, Any]]) -> 'ValidationResult':
        """Validate parameter types match schema (Task 7.2).

        Validates that each parameter dict has correct structure and that
        parameter values match their declared types.

        Args:
            parameters: List of parameter dicts from YAML

        Returns:
            ValidationResult with type errors (if any)

        Example:
            >>> gateway = ValidationGateway()
            >>> params = [{"name": "period", "type": "int", "value": 20}]
            >>> result = gateway.validate_parameter_types(params)
            >>> print(result.is_valid)
            True
        """
        from src.validation.validation_result import ValidationResult

        result = ValidationResult()

        # Empty parameters list is valid
        if not parameters:
            return result

        # Check if parameters is a list
        if not isinstance(parameters, list):
            result.add_error(
                line=0,
                column=0,
                field_name='parameters',
                error_type='type_error',
                message=f'Parameters must be list, got {type(parameters).__name__}',
                suggestion='Ensure parameters is a list of dicts'
            )
            return result

        # Validate each parameter
        for idx, param in enumerate(parameters):
            # Check if parameter is a dict
            if not isinstance(param, dict):
                result.add_error(
                    line=0,
                    column=0,
                    field_name=f'parameters[{idx}]',
                    error_type='type_error',
                    message=f'Parameter at index {idx} must be dict, got {type(param).__name__}',
                    suggestion='Ensure each parameter is a dictionary'
                )
                continue

            # Check required keys
            required_keys = ['name', 'type', 'value']
            for key in required_keys:
                if key not in param:
                    result.add_error(
                        line=0,
                        column=0,
                        field_name=f'parameters[{idx}].{key}',
                        error_type='missing_key',
                        message=f'Parameter at index {idx} missing required key "{key}"',
                        suggestion=f'Add "{key}" to parameter dict'
                    )

            # Validate parameter value type matches declared type
            if 'type' in param and 'value' in param:
                param_type = param['type']
                param_value = param['value']

                type_mapping = {
                    'int': int,
                    'float': (int, float),
                    'bool': bool,
                    'str': str,
                    'string': str
                }

                if param_type in type_mapping:
                    expected_type = type_mapping[param_type]
                    if not isinstance(param_value, expected_type):
                        result.add_error(
                            line=0,
                            column=0,
                            field_name=f'parameters[{idx}].value',
                            error_type='type_mismatch',
                            message=f'Parameter "{param.get("name", "unknown")}" declared as {param_type} but value is {type(param_value).__name__}',
                            suggestion=f'Ensure value matches declared type {param_type}'
                        )

        return result

    def validate_required_field_types(self, yaml_dict: Dict[str, Any]) -> 'ValidationResult':
        """Validate required_fields has correct type (Task 7.2).

        Validates that required_fields is a list of strings.

        Args:
            yaml_dict: YAML dictionary to validate

        Returns:
            ValidationResult with type errors (if any)

        Example:
            >>> gateway = ValidationGateway()
            >>> yaml_dict = {"required_fields": ["close", "volume"]}
            >>> result = gateway.validate_required_field_types(yaml_dict)
            >>> print(result.is_valid)
            True
        """
        from src.validation.validation_result import ValidationResult

        result = ValidationResult()

        # Check if required_fields key exists
        if 'required_fields' not in yaml_dict:
            result.add_error(
                line=0,
                column=0,
                field_name='required_fields',
                error_type='missing_key',
                message='Required key "required_fields" missing from YAML',
                suggestion='Add "required_fields" list to YAML'
            )
            return result

        required_fields = yaml_dict['required_fields']

        # Check if required_fields is a list
        if not isinstance(required_fields, list):
            result.add_error(
                line=0,
                column=0,
                field_name='required_fields',
                error_type='type_error',
                message=f'required_fields must be list, got {type(required_fields).__name__}',
                suggestion='Ensure required_fields is a list of field name strings'
            )
            return result

        # Check if all items in required_fields are strings
        for idx, field in enumerate(required_fields):
            if not isinstance(field, str):
                result.add_error(
                    line=0,
                    column=0,
                    field_name=f'required_fields[{idx}]',
                    error_type='type_error',
                    message=f'Field at index {idx} must be string, got {type(field).__name__}',
                    suggestion='Ensure all field names are strings'
                )

        return result

    def record_llm_success_rate(self, validation_result: 'ValidationResult') -> None:
        """Record LLM validation result for success rate tracking (Task 7.3, Task 8.4 - M2: Thread-safe).

        Tracks LLM-generated strategy validation outcomes to calculate overall
        LLM validation success rate. This metric helps monitor whether LLM outputs
        meet the 70-85% validation success rate target.

        Thread-safe implementation prevents race conditions when multiple LLM
        validation threads update statistics concurrently.

        Args:
            validation_result: ValidationResult from validate_strategy() or validate_and_fix()

        Example:
            >>> gateway = ValidationGateway()
            >>> code = "def strategy(data): return data.get('close') > 100"
            >>> result = gateway.validate_strategy(code)
            >>> gateway.record_llm_success_rate(result)
            >>> stats = gateway.get_llm_success_rate_stats()
            >>> print(stats['success_rate'])
            100.0
        """
        # Thread-safe modification of shared llm_validation_stats dict
        with self._lock:
            self.llm_validation_stats['total_validations'] += 1

            if validation_result.is_valid:
                self.llm_validation_stats['successful_validations'] += 1
            else:
                self.llm_validation_stats['failed_validations'] += 1

        # If metrics collector is set, record success rate metric
        if self.metrics_collector is not None:
            success_rate = self.get_llm_success_rate()
            # Record metric (MetricsCollector should have record_llm_success_rate method)
            if hasattr(self.metrics_collector, 'record_llm_success_rate'):
                self.metrics_collector.record_llm_success_rate(success_rate)

    def track_llm_success_rate(self, validation_result: 'ValidationResult') -> float:
        """Track LLM validation and return current success rate (Task 7.3).

        Convenience method that combines record_llm_success_rate() and
        get_llm_success_rate() in one call.

        Args:
            validation_result: ValidationResult from validation

        Returns:
            Current LLM validation success rate (0-100%)

        Example:
            >>> gateway = ValidationGateway()
            >>> result = gateway.validate_strategy("def strategy(data): return data.get('close') > 100")
            >>> success_rate = gateway.track_llm_success_rate(result)
            >>> print(f"Success rate: {success_rate:.1f}%")
            Success rate: 100.0%
        """
        self.record_llm_success_rate(validation_result)
        return self.get_llm_success_rate()

    def get_llm_success_rate(self) -> float:
        """Calculate current LLM validation success rate (Task 7.3).

        Returns:
            Success rate as percentage (0-100%). Returns 0.0 if no validations recorded.

        Example:
            >>> gateway = ValidationGateway()
            >>> # No validations yet
            >>> assert gateway.get_llm_success_rate() == 0.0
            >>>
            >>> # After some validations
            >>> result = gateway.validate_strategy("def strategy(data): return data.get('close') > 100")
            >>> gateway.record_llm_success_rate(result)
            >>> success_rate = gateway.get_llm_success_rate()
            >>> assert 0.0 <= success_rate <= 100.0
        """
        total = self.llm_validation_stats['total_validations']
        if total == 0:
            return 0.0

        successful = self.llm_validation_stats['successful_validations']
        return (successful / total) * 100.0

    def get_llm_success_rate_stats(self) -> Dict[str, Any]:
        """Get detailed LLM validation statistics (Task 7.3).

        Returns:
            Dictionary with:
                - total_validations: Total number of validations tracked
                - successful_validations: Number passing validation
                - failed_validations: Number failing validation
                - success_rate: Success rate as percentage (0-100%)

        Example:
            >>> gateway = ValidationGateway()
            >>> stats = gateway.get_llm_success_rate_stats()
            >>> print(stats)
            {'total_validations': 0, 'successful_validations': 0, 'failed_validations': 0, 'success_rate': 0.0}
        """
        return {
            'total_validations': self.llm_validation_stats['total_validations'],
            'successful_validations': self.llm_validation_stats['successful_validations'],
            'failed_validations': self.llm_validation_stats['failed_validations'],
            'success_rate': self.get_llm_success_rate()
        }

    def reset_llm_success_rate_stats(self) -> None:
        """Reset LLM validation statistics (Task 7.3, Task 8.4 - M2: Thread-safe).

        Useful for starting fresh tracking or for testing.

        Thread-safe implementation prevents race conditions when resetting
        statistics while other threads are actively updating them.

        Example:
            >>> gateway = ValidationGateway()
            >>> # Track some validations
            >>> result = gateway.validate_strategy("def strategy(data): return data.get('close') > 100")
            >>> gateway.record_llm_success_rate(result)
            >>> assert gateway.get_llm_success_rate() > 0
            >>>
            >>> # Reset stats
            >>> gateway.reset_llm_success_rate_stats()
            >>> assert gateway.get_llm_success_rate() == 0.0
        """
        # Thread-safe reset of shared llm_validation_stats dict
        with self._lock:
            self.llm_validation_stats = {
                'total_validations': 0,
                'successful_validations': 0,
                'failed_validations': 0
            }
