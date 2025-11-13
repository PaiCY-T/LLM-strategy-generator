#!/usr/bin/env python3
"""
StructuredPromptBuilder for YAML Strategy Generation
Task 5: Structured Innovation MVP - Prompt Engineering Expert

This module generates YAML-specific prompts for LLMs, including schema
and examples to guide generation of valid trading strategies.

Key features:
- Include JSON Schema to constrain LLM output
- Provide 3 complete strategy examples (momentum, mean_reversion, factor_combination)
- Include champion feedback and failure patterns
- Token budget control (<2000 tokens)
- Clear instructions for YAML format
- YAML extraction from LLM responses using regex
- Retry logic for malformed responses

Requirements:
- Task 5 of structured-innovation-mvp spec
- Requirements 3.1-3.5 (Prompt structure for YAML generation)
"""

import json
import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class StructuredPromptBuilder:
    """
    Build prompts specifically for YAML strategy generation.

    Includes schema constraints, examples, and champion feedback
    to guide LLM towards valid YAML output.
    """

    def __init__(self, schema_path: str = "schemas/strategy_schema_v1.json"):
        """
        Initialize StructuredPromptBuilder.

        Args:
            schema_path: Path to JSON Schema file (relative to project root)
        """
        # Get project root (src/innovation -> src -> root)
        self.project_root = Path(__file__).parent.parent.parent
        self.schema_path = self.project_root / schema_path

        # Load schema
        self.schema = self._load_schema(self.schema_path)

        # Load examples
        self.examples = self._load_examples()

        # YAML extraction patterns (ordered by preference)
        # Requirement 3.4: YAML extraction using regex
        self.yaml_patterns = [
            # Pattern 1: YAML code block with explicit yaml marker
            r'```yaml\s*\n(.*?)\n```',
            # Pattern 2: YAML code block without marker
            r'```\s*\n(.*?)\n```',
            # Pattern 3: JSON code block (also valid YAML)
            r'```json\s*\n(.*?)\n```',
            # Pattern 4: Triple backticks with yml marker
            r'```yml\s*\n(.*?)\n```',
        ]

    def _load_schema(self, schema_path: Path) -> Dict:
        """
        Load JSON Schema from file.

        Args:
            schema_path: Path to schema file

        Returns:
            Schema dictionary
        """
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_examples(self) -> Dict[str, str]:
        """
        Load 3 complete YAML strategy examples.

        Returns:
            Dictionary mapping strategy type to YAML content
        """
        examples_dir = self.project_root / "examples" / "yaml_strategies"

        # Map strategy types to example files
        example_files = {
            "momentum": "test_valid_momentum.yaml",
            "mean_reversion": "test_valid_mean_reversion.yaml",
            "factor_combination": "test_valid_factor_combo.yaml"
        }

        examples = {}
        for strategy_type, filename in example_files.items():
            file_path = examples_dir / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    examples[strategy_type] = f.read()
            else:
                # Use empty placeholder if file not found
                examples[strategy_type] = f"# {strategy_type} example not found"

        return examples

    def _include_schema_excerpt(self) -> str:
        """
        Include critical schema fields in prompt (save tokens).

        Returns:
            Schema excerpt as string
        """
        excerpt = """
Required fields and structure:

metadata:
  name: string (5-100 chars, alphanumeric)
  description: string (10-500 chars)
  strategy_type: "momentum" | "mean_reversion" | "factor_combination"
  rebalancing_frequency: "M" | "W-FRI" | "W-MON" | "Q"
  version: "1.0.0" (default)
  risk_level: "low" | "medium" | "high" (default: medium)

indicators:
  technical_indicators: (optional)
    - name: string (lowercase_with_underscores)
      type: "RSI" | "MACD" | "BB" | "SMA" | "EMA" | "ATR" | etc.
      period: integer (1-250)
      source: "data.get('FIELD_NAME')"

  fundamental_factors: (optional)
    - name: string (lowercase_with_underscores)
      field: "ROE" | "PE_ratio" | "revenue_growth" | etc.
      source: "data.get('FIELD_NAME')"
      transformation: "none" | "log" | "rank" | "zscore" | "winsorize"

  custom_calculations: (optional)
    - name: string (lowercase_with_underscores)
      expression: "mathematical expression using other indicators"
      description: string

entry_conditions:
  threshold_rules: (optional)
    - condition: "boolean expression (e.g., 'rsi_14 > 30')"
      description: string

  ranking_rules: (optional)
    - field: string (must be defined in indicators)
      method: "top_percent" | "bottom_percent" | "top_n" | "bottom_n"
      value: number
      ascending: boolean (default: false)

  logical_operator: "AND" | "OR" (default: AND)
  min_liquidity:
    average_volume_20d: number (optional)

exit_conditions: (optional)
  stop_loss_pct: number (0.01-0.50)
  take_profit_pct: number (0.05-2.0)
  trailing_stop:
    trail_percent: number (0.01-0.30)
    activation_profit: number (0-0.50)
  holding_period_days: integer (1-365)
  conditional_exits:
    - condition: "boolean expression"
      description: string
  exit_operator: "AND" | "OR" (default: OR)

position_sizing:
  method: "equal_weight" | "factor_weighted" | "risk_parity" | "volatility_weighted"
  max_positions: integer (1-100)
  max_position_pct: number (0.01-1.0)
  weighting_field: string (required if method=factor_weighted)

risk_management: (optional)
  max_sector_exposure: number (0.05-1.0)
  rebalance_threshold: number (0.01-0.50)
  max_drawdown_limit: number (0.05-0.50)
"""
        return excerpt.strip()

    def build_yaml_generation_prompt(
        self,
        champion_metrics: Optional[Dict] = None,
        failure_patterns: Optional[List[str]] = None,
        target_strategy_type: str = "momentum"
    ) -> str:
        """
        Build prompt for LLM to generate YAML strategy.

        Args:
            champion_metrics: Current champion metrics (Sharpe, Return, MaxDD, etc.)
            failure_patterns: List of failure patterns to avoid
            target_strategy_type: Type of strategy to generate

        Returns:
            Complete prompt string for LLM
        """
        # Default values
        if champion_metrics is None:
            champion_metrics = {
                "sharpe_ratio": 1.5,
                "annual_return": 0.15,
                "max_drawdown": -0.20
            }

        if failure_patterns is None:
            failure_patterns = [
                "Overtrading (>100 trades/year)",
                "Large drawdowns (>20%)",
                "Low liquidity stocks causing slippage"
            ]

        # Build sections
        intro = f"""Generate a trading strategy in YAML format that improves upon the champion.

Target Strategy Type: {target_strategy_type}

Champion Metrics (to beat):
- Sharpe Ratio: {champion_metrics.get('sharpe_ratio', 'N/A')}
- Annual Return: {champion_metrics.get('annual_return', 'N/A'):.1%}
- Max Drawdown: {champion_metrics.get('max_drawdown', 'N/A'):.1%}
"""

        # Failure patterns section
        failures = "\nFailure Patterns to Avoid:\n"
        for pattern in failure_patterns[:5]:  # Limit to 5 patterns to save tokens
            failures += f"- {pattern}\n"

        # Schema section
        schema_section = f"\n=== YAML Schema (follow this exactly) ===\n{self._include_schema_excerpt()}\n"

        # Examples section
        examples_section = "\n=== Strategy Examples ===\n\n"

        # Include requested target type + 1 other example (save tokens)
        example_types = [target_strategy_type]
        for strategy_type in ["momentum", "mean_reversion", "factor_combination"]:
            if strategy_type != target_strategy_type and len(example_types) < 2:
                example_types.append(strategy_type)
                break

        for strategy_type in example_types:
            example_yaml = self.examples.get(strategy_type, "# Example not found")
            examples_section += f"## Example {strategy_type.replace('_', ' ').title()} Strategy:\n```yaml\n{example_yaml}\n```\n\n"

        # Instructions
        instructions = f"""
=== Instructions ===

1. Generate a {target_strategy_type} strategy in YAML format
2. Follow the schema exactly - all required fields must be present
3. Use valid indicator types and parameter ranges
4. Create conditions that beat the champion metrics
5. Avoid the failure patterns listed above
6. Output ONLY valid YAML, no markdown code fences, no explanations
7. Start directly with 'metadata:' at the top level

Begin YAML output now:
"""

        # Combine all sections
        prompt = (
            intro +
            failures +
            schema_section +
            examples_section +
            instructions
        )

        return prompt

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation: 1 token ≈ 4 chars).

        Args:
            text: Text to count tokens for

        Returns:
            Approximate token count
        """
        return len(text) // 4

    def build_compact_prompt(
        self,
        champion_metrics: Optional[Dict] = None,
        failure_patterns: Optional[List[str]] = None,
        target_strategy_type: str = "momentum"
    ) -> str:
        """
        Build compact prompt under 2000 tokens.

        Uses abbreviated schema and single example.

        Args:
            champion_metrics: Current champion metrics
            failure_patterns: List of failure patterns to avoid
            target_strategy_type: Type of strategy to generate

        Returns:
            Compact prompt string for LLM
        """
        # Default values
        if champion_metrics is None:
            champion_metrics = {
                "sharpe_ratio": 1.5,
                "annual_return": 0.15,
                "max_drawdown": -0.20
            }

        if failure_patterns is None:
            failure_patterns = []

        # Compact intro
        intro = f"""Generate {target_strategy_type} YAML strategy to beat champion (Sharpe={champion_metrics.get('sharpe_ratio', 1.5):.2f}).

Avoid: {', '.join(failure_patterns[:3]) if failure_patterns else 'overtrading, large drawdowns'}
"""

        # Compact schema (most critical fields only)
        compact_schema = """
Schema (ALL fields required unless marked optional):

metadata:
  name: string (5-100 chars)
  description: string (10-500 chars)
  strategy_type: "momentum" | "mean_reversion" | "factor_combination"
  rebalancing_frequency: "M" | "W-FRI" | "W-MON" | "Q"

indicators:  # MUST include at least ONE of these subsections:
  technical_indicators:     # array of {name, type, period, source}
    - name: "rsi_14"
      type: "RSI" | "MACD" | "BB" | "SMA" | "EMA" | "ATR" | ...
      period: 1-250
      source: "data.get('FIELD_NAME')"
  fundamental_factors:      # array of {name, field, source}
    - name: "roe"
      field: "ROE" | "PE_ratio" | "revenue_growth" | ...
      source: "data.get('ROE')"
  custom_calculations:      # array of {name, expression}
    - name: "momentum_score"
      expression: "rsi_14 * (1 + revenue_growth)"

entry_conditions:
  threshold_rules:          # array of {condition, description}
    - condition: "rsi_14 > 50"
      description: "RSI shows momentum"
  logical_operator: "AND" | "OR"

exit_conditions: (optional but recommended)
  stop_loss_pct: 0.10
  take_profit_pct: 0.25

position_sizing:
  method: "equal_weight" | "volatility_weighted" | "rank_weighted"
  max_positions: 10-50
"""

        # Single example
        example_yaml = self.examples.get(target_strategy_type, "")
        # Truncate example if too long
        if len(example_yaml) > 2000:
            example_yaml = example_yaml[:2000] + "\n# ... truncated"

        example_section = f"\nExample:\n```yaml\n{example_yaml}\n```\n"

        # Compact instructions
        instructions = """
Output ONLY valid YAML starting with 'metadata:'.

CRITICAL REQUIREMENTS:
1. Include ALL required top-level fields: metadata, indicators, entry_conditions, position_sizing
2. The 'indicators' section MUST contain at least ONE subsection with at least ONE item:
   - technical_indicators: array with 1+ indicators, OR
   - fundamental_factors: array with 1+ factors, OR
   - custom_calculations: array with 1+ calculations
3. Do NOT output any text before or after the YAML
4. Use proper YAML syntax (indentation, colons, dashes)
"""

        prompt = intro + compact_schema + example_section + instructions

        # Ensure under 2000 tokens (8000 chars)
        if len(prompt) > 8000:
            # Remove example and use ultra-compact version
            prompt = intro + compact_schema + instructions

        return prompt

    def get_example(self, strategy_type: str) -> str:
        """
        Get a specific example YAML.

        Args:
            strategy_type: Type of strategy example to retrieve

        Returns:
            YAML example content
        """
        return self.examples.get(strategy_type, "")

    def extract_yaml(self, llm_response: str) -> Tuple[Optional[str], bool]:
        """
        Extract YAML specification from LLM response using regex patterns.

        Requirement 3.4: YAML extraction from LLM response using regex

        Tries multiple extraction patterns in order of preference:
        1. ```yaml code blocks
        2. ``` generic code blocks
        3. ```json code blocks (JSON is valid YAML)
        4. ```yml code blocks

        Args:
            llm_response: Raw text response from LLM

        Returns:
            Tuple of (yaml_string, success_flag)
            - yaml_string: Extracted YAML content or None if extraction failed
            - success_flag: True if extraction succeeded, False otherwise
        """
        if not llm_response:
            return None, False

        # Try each pattern in order
        for pattern in self.yaml_patterns:
            match = re.search(pattern, llm_response, re.DOTALL | re.IGNORECASE)
            if match:
                yaml_content = match.group(1).strip()

                # Validate it's actually YAML-like (basic sanity check)
                if self._looks_like_yaml(yaml_content):
                    return yaml_content, True

        # If no pattern matched, try to find YAML without code blocks
        # (fallback for responses that don't use markdown)
        if self._looks_like_yaml(llm_response):
            return llm_response.strip(), True

        return None, False

    def _looks_like_yaml(self, text: str) -> bool:
        """
        Basic sanity check to verify text looks like YAML.

        Checks for:
        1. Contains required top-level keys (metadata, indicators, entry_conditions)
        2. Uses YAML-like syntax (key: value pairs)
        3. Doesn't look like plain text explanation

        Args:
            text: Text to validate

        Returns:
            True if text appears to be YAML, False otherwise
        """
        if not text:
            return False

        # Check for required top-level sections
        required_sections = ['metadata', 'indicators', 'entry_conditions']
        has_required = all(section in text.lower() for section in required_sections)

        # Check for YAML-like key:value syntax
        has_yaml_syntax = ':' in text and '\n' in text

        # Check it's not just plain text (should have indentation structure)
        lines = text.split('\n')
        has_indentation = any(line.startswith('  ') or line.startswith('\t') for line in lines)

        return has_required and has_yaml_syntax and has_indentation

    def validate_extracted_yaml(self, yaml_string: str) -> Tuple[Optional[Dict], List[str]]:
        """
        Validate extracted YAML string and parse to dict.

        Args:
            yaml_string: YAML content string

        Returns:
            Tuple of (parsed_dict, error_messages)
            - parsed_dict: Parsed YAML as dictionary, or None if parsing failed
            - error_messages: List of validation error messages (empty if valid)
        """
        errors = []

        try:
            # Parse YAML
            parsed = yaml.safe_load(yaml_string)

            if not isinstance(parsed, dict):
                errors.append("YAML did not parse to a dictionary")
                return None, errors

            # Check required top-level fields
            required_fields = ['metadata', 'indicators', 'entry_conditions']
            for field in required_fields:
                if field not in parsed:
                    errors.append(f"Missing required field: {field}")

            # If we have errors, return None
            if errors:
                return None, errors

            return parsed, []

        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error: {str(e)}")
            return None, errors
        except Exception as e:
            errors.append(f"Unexpected error during YAML validation: {str(e)}")
            return None, errors

    def get_retry_prompt(
        self,
        retry_attempt: int,
        previous_error: str,
        champion_metrics: Optional[Dict] = None,
        failure_patterns: Optional[List[str]] = None,
        target_strategy_type: str = "momentum"
    ) -> str:
        """
        Build enhanced prompt for retry attempts.

        Requirement 3.5: Retry logic for malformed responses

        Args:
            retry_attempt: Current retry attempt number (1-based)
            previous_error: Error message from previous attempt
            champion_metrics: Current champion metrics
            failure_patterns: List of failure patterns to avoid
            target_strategy_type: Type of strategy to generate

        Returns:
            Enhanced prompt string with retry instructions
        """
        # Build retry-specific instructions
        retry_header = f"""
⚠️ **RETRY ATTEMPT {retry_attempt}**

Your previous attempt failed with error:
{previous_error}

**CRITICAL REQUIREMENTS FOR THIS RETRY:**
1. Return ONLY the YAML specification wrapped in ```yaml code blocks
2. Do NOT include any explanatory text before or after the YAML
3. Do NOT include markdown headers or sections outside the code block
4. Ensure all required fields are present: metadata, indicators, entry_conditions, position_sizing
5. Use proper YAML syntax with correct indentation (2 spaces per level)
6. Validate field names match the schema exactly (e.g., "strategy_type" not "type")

**CORRECT FORMAT:**
```yaml
metadata:
  name: "Strategy Name"
  strategy_type: "momentum"
  rebalancing_frequency: "M"
# ... rest of YAML spec
```

**INCORRECT FORMATS TO AVOID:**
- Adding explanatory text outside code blocks
- Using wrong field names
- Missing required sections
- Invalid YAML syntax

---
"""

        # Get base prompt
        base_prompt = self.build_yaml_generation_prompt(
            champion_metrics=champion_metrics,
            failure_patterns=failure_patterns,
            target_strategy_type=target_strategy_type
        )

        # Combine retry header with base prompt
        return retry_header + base_prompt

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about prompt builder usage (for monitoring).

        Returns:
            Dictionary with statistics
        """
        return {
            'schema_loaded': self.schema is not None,
            'schema_version': self.schema.get('version', 'unknown') if self.schema else None,
            'examples_loaded': len(self.examples),
            'example_types': list(self.examples.keys()),
            'extraction_patterns': len(self.yaml_patterns)
        }


if __name__ == "__main__":
    # Test the builder
    builder = StructuredPromptBuilder()

    # Test champion metrics
    champion = {
        "sharpe_ratio": 2.48,
        "annual_return": 0.12,
        "max_drawdown": -0.15
    }

    # Test failure patterns (from actual data)
    failures = [
        "Increasing liquidity threshold above 50M causes performance drop",
        "Smoothing ROE over 60-day window reduces Sharpe by 1.1",
        "Decreasing liquidity threshold below 50 causes -2.5 Sharpe drop"
    ]

    print("="*70)
    print("FULL PROMPT (MOMENTUM)")
    print("="*70)
    prompt = builder.build_yaml_generation_prompt(
        champion_metrics=champion,
        failure_patterns=failures,
        target_strategy_type="momentum"
    )
    print(prompt)
    print(f"\nToken count: ~{builder.count_tokens(prompt)}")

    print("\n" + "="*70)
    print("COMPACT PROMPT (FACTOR_COMBINATION)")
    print("="*70)
    compact = builder.build_compact_prompt(
        champion_metrics=champion,
        failure_patterns=failures,
        target_strategy_type="factor_combination"
    )
    print(compact)
    print(f"\nToken count: ~{builder.count_tokens(compact)}")
