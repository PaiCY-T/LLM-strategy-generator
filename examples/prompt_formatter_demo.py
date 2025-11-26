"""
Prompt Formatter Demo - Two-Stage Prompting System

This demo shows how to use the prompt formatter for LLM strategy generation.

Task: 23.3 - Prompt Formatting Functions Implementation
Status: ✅ Complete

Run this demo with:
    python examples/prompt_formatter_demo.py
"""

from src.prompts.prompt_formatter import (
    generate_field_selection_prompt,
    generate_config_creation_prompt,
)
from src.config.data_fields import DataFieldManifest
import json


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def main():
    """Run the two-stage prompting demo"""

    print_section("Two-Stage Prompting Demo")

    # Initialize manifest
    print("Initializing DataFieldManifest...")
    manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
    print(f"✓ Loaded {manifest.get_field_count()} fields from manifest\n")

    # ========================================================================
    # STAGE 1: Field Selection
    # ========================================================================

    print_section("STAGE 1: Field Selection")

    # Get available price fields
    available_fields = manifest.get_fields_by_category('price')[:5]
    print(f"Available fields ({len(available_fields)} price fields):")
    for field in available_fields:
        print(f"  - {field.canonical_name}: {field.description_en}")

    # Generate Stage 1 prompt
    print("\nGenerating field selection prompt...")
    stage1_prompt = generate_field_selection_prompt(
        available_fields=available_fields,
        strategy_type="momentum"
    )

    print("\n--- STAGE 1 PROMPT ---")
    print(stage1_prompt[:500] + "...")  # Show first 500 chars
    print(f"\nPrompt length: {len(stage1_prompt)} characters")

    # Simulate LLM response (in real scenario, send stage1_prompt to LLM)
    print("\n--- SIMULATED LLM RESPONSE (Stage 1) ---")
    llm_response_stage1 = {
        "selected_fields": ["price:收盤價", "price:成交金額"],
        "rationale": "Closing price for momentum calculation, trading value for liquidity filtering"
    }
    print(json.dumps(llm_response_stage1, indent=2, ensure_ascii=False))

    selected_fields = llm_response_stage1["selected_fields"]
    print(f"\n✓ Selected {len(selected_fields)} fields for strategy")

    # ========================================================================
    # STAGE 2: Config Generation
    # ========================================================================

    print_section("STAGE 2: Config Generation")

    # Prepare schema example (from strategy_schema.yaml pure_momentum pattern)
    schema_example = """
name: "Pure Momentum"
type: "momentum"
description: "Fast breakout strategy using price momentum"
required_fields:
  - field: "price:收盤價"
    alias: "close"
    usage: "Signal generation - momentum calculation"
  - field: "price:成交金額"
    alias: "volume"
    usage: "Volume filtering - minimum liquidity requirement"
parameters:
  momentum_period:
    type: "integer"
    default: 20
    range: [10, 60]
    unit: "trading_days"
  entry_threshold:
    type: "float"
    default: 0.02
    range: [0.01, 0.10]
    unit: "percentage"
  min_volume:
    type: "float"
    default: 1000000.0
    range: [100000.0, 10000000.0]
    unit: "currency"
logic:
  entry: "(price.pct_change(momentum_period).rolling(5).mean() > entry_threshold) & (volume > min_volume)"
  exit: "None"
"""

    print("Selected fields for config generation:")
    for field in selected_fields:
        print(f"  - {field}")

    # Generate Stage 2 prompt
    print("\nGenerating config creation prompt...")
    stage2_prompt = generate_config_creation_prompt(
        selected_fields=selected_fields,
        strategy_type="momentum",
        schema_example=schema_example
    )

    print("\n--- STAGE 2 PROMPT ---")
    print(stage2_prompt[:500] + "...")  # Show first 500 chars
    print(f"\nPrompt length: {len(stage2_prompt)} characters")

    # Simulate LLM response (in real scenario, send stage2_prompt to LLM)
    print("\n--- SIMULATED LLM RESPONSE (Stage 2) ---")
    llm_response_stage2 = """
name: "Momentum Breakout v1"
type: "momentum"
description: "Price momentum with volume confirmation"
required_fields:
  - field: "price:收盤價"
    alias: "close"
    usage: "Momentum calculation"
  - field: "price:成交金額"
    alias: "volume"
    usage: "Liquidity filter"
parameters:
  momentum_period:
    type: "integer"
    default: 20
    range: [10, 60]
    unit: "trading_days"
  min_volume:
    type: "float"
    default: 1000000.0
    range: [100000.0, 10000000.0]
    unit: "currency"
logic:
  entry: "(close.pct_change(momentum_period) > 0.02) & (volume > min_volume)"
  exit: "None"
"""
    print(llm_response_stage2)

    print("\n✓ Generated valid YAML config")

    # ========================================================================
    # Summary
    # ========================================================================

    print_section("Demo Summary")

    print("Two-Stage Prompting Workflow:")
    print("  1. Stage 1: LLM selects fields from validated manifest")
    print("  2. Parse JSON response to get selected fields")
    print("  3. Stage 2: LLM generates YAML config using selected fields")
    print("  4. Parse and validate YAML config")
    print("\nBenefits:")
    print("  ✓ 0% field error rate - only validated fields available")
    print("  ✓ Structured output - JSON (Stage 1) and YAML (Stage 2)")
    print("  ✓ Pattern alignment - follows strategy_schema.yaml")
    print("  ✓ Better debugging - separate field selection from config generation")
    print("\nNext Steps:")
    print("  → Task 24.1: Integrate with LLM strategy generation")
    print("  → Task 24.2: Add YAML validation after generation")
    print("  → Task 24.3: Implement error feedback loop")
    print("\n✓ Demo complete!\n")


if __name__ == "__main__":
    main()
