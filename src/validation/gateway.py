"""ValidationGateway - Central orchestrator for all validation layers.

This module implements the ValidationGateway class which serves as the central
coordinator for all validation layers (Layer 1, Layer 2, Layer 3).

Key Features:
- Feature flag-based conditional initialization
- Layer dependency management (Layer 2 requires Layer 1)
- Field suggestions injection for LLM prompts
- Graceful degradation when layers are disabled

Architecture:
- Layer 1 (DataFieldManifest): Field name validation and suggestions
- Layer 2 (FieldValidator): AST-based code validation (requires Layer 1)
- Layer 3 (SchemaValidator): YAML schema validation (independent)

Usage:
    from src.validation.gateway import ValidationGateway

    # Initialize gateway (reads feature flags automatically)
    gateway = ValidationGateway()

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
"""

from typing import Optional

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
