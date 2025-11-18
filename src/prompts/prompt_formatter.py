"""
Prompt Formatter for Two-Stage LLM Strategy Generation

Task 23.3: Implement prompt formatting functions
Integration: Layer 1 (DataFieldManifest), Layer 3 (strategy_schema.yaml)

This module provides functions to format prompts for two-stage LLM interaction:
- Stage 1: Field selection from available fields (generate_field_selection_prompt)
- Stage 2: YAML config generation using selected fields (generate_config_creation_prompt)

Usage:
    from src.prompts.prompt_formatter import (
        generate_field_selection_prompt,
        generate_config_creation_prompt
    )
    from src.config.data_fields import DataFieldManifest

    # Stage 1: Field selection
    manifest = DataFieldManifest()
    fields = manifest.get_fields_by_category('price')
    prompt1 = generate_field_selection_prompt(fields, 'momentum')

    # LLM responds with: ["price:收盤價", "price:成交金額"]

    # Stage 2: Config generation
    selected = ["price:收盤價", "price:成交金額"]
    schema_example = "..."  # From strategy_schema.yaml
    prompt2 = generate_config_creation_prompt(selected, 'momentum', schema_example)

    # LLM responds with valid YAML config

See Also:
    - .spec-workflow/specs/llm-field-validation-fix/design.md: Prompt templates
    - src/config/data_fields.py: DataFieldManifest integration
    - src/config/strategy_schema.yaml: Pattern schemas for examples
"""

from typing import List
from src.config.field_metadata import FieldMetadata


# Stage 1 Prompt Template
STAGE1_PROMPT_TEMPLATE = """
## Task: Select Fields for {strategy_type} Strategy

Choose 2-5 fields from the following validated list for a {strategy_type} strategy.

## Available Fields (All Validated):
{field_list_with_descriptions}

## Guidelines:
1. Choose fields relevant to {strategy_type} strategies
2. All fields are guaranteed to exist in finlab API
3. Use canonical names (e.g., 'price:收盤價', not 'close')
4. Return ONLY a JSON list of field names

## Output Format:
```json
{{
  "selected_fields": ["price:收盤價", "fundamental_features:ROE"],
  "rationale": "Brief explanation of why these fields work together"
}}
```
"""

# Stage 2 Prompt Template
STAGE2_PROMPT_TEMPLATE = """
## Task: Generate Strategy Configuration YAML

Create a YAML config for a {strategy_type} strategy using these validated fields:
{selected_fields}

## YAML Schema:
```yaml
name: "<strategy_name>"
type: "{strategy_type}"
required_fields:
  - field: "<canonical_field_name>"
    alias: "<short_alias>"
    usage: "<how_field_is_used>"
parameters:
  <param_name>:
    type: int|float|str
    default: <value>
    range: [min, max]
logic:
  entry: "<entry_condition>"
  exit: "<exit_condition>"
```

{schema_example}

## Return ONLY valid YAML. No explanation.
"""


def generate_field_selection_prompt(
    available_fields: List[FieldMetadata],
    strategy_type: str
) -> str:
    """
    Generate Stage 1 prompt for LLM to select fields from manifest.

    This function formats the STAGE1_PROMPT_TEMPLATE with available field
    metadata and strategy type, guiding the LLM to select 2-5 relevant fields
    for strategy generation.

    Args:
        available_fields: List of FieldMetadata objects from DataFieldManifest
                         Must contain at least 1 field
        strategy_type: Strategy type/pattern name
                      Examples: "momentum", "breakout", "factor_scoring", "hybrid"

    Returns:
        Formatted prompt string ready for LLM input

    Raises:
        ValueError: If available_fields is empty or strategy_type is empty

    Example:
        >>> from src.config.data_fields import DataFieldManifest
        >>> manifest = DataFieldManifest()
        >>> fields = manifest.get_fields_by_category('price')
        >>> prompt = generate_field_selection_prompt(fields, 'momentum')
        >>> assert 'momentum' in prompt
        >>> assert 'price:收盤價' in prompt  # Canonical name appears

    Integration:
        - Layer 1: Receives FieldMetadata from DataFieldManifest
        - LLM: Returns JSON with selected_fields list
        - Next: Pass selected fields to generate_config_creation_prompt()
    """
    # Validate inputs
    if not available_fields:
        raise ValueError("available_fields cannot be empty")

    if not strategy_type or not isinstance(strategy_type, str):
        raise ValueError("strategy_type must be a non-empty string")

    # Format field list with descriptions
    field_lines = []
    for field in available_fields:
        # Format: canonical_name - description_en (aliases: alias1, alias2, ...)
        aliases_str = ", ".join(field.aliases[:3])  # Show first 3 aliases
        field_line = (
            f"- **{field.canonical_name}** - {field.description_en}\n"
            f"  - Category: {field.category}, Frequency: {field.frequency}\n"
            f"  - Common aliases: {aliases_str}"
        )
        field_lines.append(field_line)

    field_list_with_descriptions = "\n\n".join(field_lines)

    # Format template with parameters
    prompt = STAGE1_PROMPT_TEMPLATE.format(
        strategy_type=strategy_type,
        field_list_with_descriptions=field_list_with_descriptions
    )

    return prompt


def generate_config_creation_prompt(
    selected_fields: List[str],
    strategy_type: str,
    schema_example: str = ""
) -> str:
    """
    Generate Stage 2 prompt for LLM to create YAML config from selected fields.

    This function formats the STAGE2_PROMPT_TEMPLATE with selected fields,
    strategy type, and an optional schema example, guiding the LLM to generate
    a valid YAML configuration following the strategy schema structure.

    Args:
        selected_fields: List of canonical field names selected in Stage 1
                        Must contain at least 1 field
                        Examples: ["price:收盤價", "fundamental_features:ROE"]
        strategy_type: Strategy type/pattern name
                      Must match Stage 1 strategy_type
                      Examples: "momentum", "breakout", "factor_scoring"
        schema_example: Optional YAML schema example from strategy_schema.yaml
                       Shows pattern-specific structure and parameters
                       If empty, only generic schema is shown

    Returns:
        Formatted prompt string ready for LLM input

    Raises:
        ValueError: If selected_fields is empty or strategy_type is empty

    Example:
        >>> selected = ["price:收盤價", "price:成交金額"]
        >>> schema = "name: Pure Momentum\\ntype: momentum\\n..."
        >>> prompt = generate_config_creation_prompt(
        ...     selected,
        ...     'momentum',
        ...     schema
        ... )
        >>> assert 'price:收盤價' in prompt
        >>> assert 'yaml' in prompt.lower()

    Integration:
        - Layer 1: Uses canonical field names from DataFieldManifest
        - Layer 3: Includes schema example from strategy_schema.yaml
        - LLM: Returns valid YAML configuration
        - Next: Parse and validate YAML using yaml.safe_load()
    """
    # Validate inputs
    if not selected_fields:
        raise ValueError("selected_fields cannot be empty")

    if not strategy_type or not isinstance(strategy_type, str):
        raise ValueError("strategy_type must be a non-empty string")

    # Format selected fields as bullet list
    field_list = "\n".join(f"- {field}" for field in selected_fields)

    # Format schema example section
    schema_section = ""
    if schema_example and schema_example.strip():
        schema_section = f"\n## Example Pattern:\n```yaml\n{schema_example.strip()}\n```\n"

    # Format template with parameters
    prompt = STAGE2_PROMPT_TEMPLATE.format(
        strategy_type=strategy_type,
        selected_fields=field_list,
        schema_example=schema_section
    )

    return prompt
