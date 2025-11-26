"""
Tests for prompt_formatter.py - Two-Stage Prompting System

Task 23.3: Implement prompt formatting functions
TDD Methodology: Write failing tests first (RED phase)

Tests cover:
1. Field selection prompt generation (Stage 1)
2. Config creation prompt generation (Stage 2)
3. Integration with DataFieldManifest
4. Different strategy types
5. Prompt format validation
"""

import pytest
from typing import List

from src.prompts.prompt_formatter import (
    generate_field_selection_prompt,
    generate_config_creation_prompt,
)
from src.config.data_fields import DataFieldManifest
from src.config.field_metadata import FieldMetadata


class TestFieldSelectionPrompt:
    """Test suite for Stage 1: Field selection prompt generation"""

    @pytest.fixture
    def sample_fields(self) -> List[FieldMetadata]:
        """Create sample field metadata for testing"""
        return [
            FieldMetadata(
                canonical_name="price:收盤價",
                category="price",
                frequency="daily",
                dtype="float",
                description_zh="每日收盤價格",
                description_en="Daily closing price",
                aliases=["close", "closing_price", "收盤價"],
                valid_range=(0.0, 10000.0),
            ),
            FieldMetadata(
                canonical_name="price:成交金額",
                category="price",
                frequency="daily",
                dtype="float",
                description_zh="每日成交金額",
                description_en="Daily trading value",
                aliases=["volume", "trading_value", "成交金額"],
                valid_range=(0.0, 1e12),
            ),
            FieldMetadata(
                canonical_name="fundamental_features:ROE",
                category="fundamental",
                frequency="quarterly",
                dtype="float",
                description_zh="股東權益報酬率",
                description_en="Return on Equity",
                aliases=["roe", "return_on_equity", "ROE"],
                valid_range=(-100.0, 200.0),
            ),
        ]

    def test_generate_field_selection_prompt_basic(self, sample_fields):
        """
        Test basic field selection prompt generation

        RED: This test should fail initially
        """
        prompt = generate_field_selection_prompt(
            available_fields=sample_fields,
            strategy_type="momentum"
        )

        # Verify prompt is non-empty string
        assert isinstance(prompt, str)
        assert len(prompt) > 0

        # Verify prompt includes strategy type
        assert "momentum" in prompt.lower()

        # Verify prompt includes task description
        assert "Select Fields" in prompt or "Choose" in prompt.lower()

    def test_prompt_includes_all_field_metadata(self, sample_fields):
        """
        Test that prompt includes canonical names and descriptions

        RED: Should fail - need to format field list with metadata
        """
        prompt = generate_field_selection_prompt(
            available_fields=sample_fields,
            strategy_type="momentum"
        )

        # Verify all canonical names are included
        assert "price:收盤價" in prompt
        assert "price:成交金額" in prompt
        assert "fundamental_features:ROE" in prompt

        # Verify descriptions are included
        assert "closing price" in prompt.lower()
        assert "trading value" in prompt.lower()
        assert "return on equity" in prompt.lower()

    def test_prompt_includes_json_format_instruction(self, sample_fields):
        """
        Test that prompt requests JSON output format

        RED: Should fail - need to include JSON format example
        """
        prompt = generate_field_selection_prompt(
            available_fields=sample_fields,
            strategy_type="momentum"
        )

        # Verify JSON format instructions
        assert "json" in prompt.lower()
        assert "selected_fields" in prompt.lower()

        # Verify example format is shown
        assert "[" in prompt  # JSON array syntax
        assert "]" in prompt

    def test_different_strategy_types(self, sample_fields):
        """
        Test prompt generation for different strategy types

        RED: Should fail - need to support multiple strategy types
        """
        strategy_types = ["momentum", "breakout", "factor_scoring", "hybrid"]

        for strategy_type in strategy_types:
            prompt = generate_field_selection_prompt(
                available_fields=sample_fields,
                strategy_type=strategy_type
            )

            # Verify strategy type appears in prompt
            assert strategy_type in prompt.lower()

            # Verify prompt is unique for each strategy type
            assert len(prompt) > 100  # Reasonable minimum length

    def test_empty_fields_raises_error(self):
        """
        Test that empty field list raises appropriate error

        RED: Should fail - need error handling for empty input
        """
        with pytest.raises(ValueError, match="available_fields cannot be empty"):
            generate_field_selection_prompt(
                available_fields=[],
                strategy_type="momentum"
            )

    def test_integration_with_manifest(self):
        """
        Test integration with DataFieldManifest

        RED: Should fail - need to handle FieldMetadata from manifest
        """
        # Load fields from manifest
        manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')

        # Get fields from manifest
        price_fields = manifest.get_fields_by_category('price')

        # Generate prompt with real manifest fields
        prompt = generate_field_selection_prompt(
            available_fields=price_fields[:5],  # First 5 price fields
            strategy_type="momentum"
        )

        # Verify prompt is generated successfully
        assert isinstance(prompt, str)
        assert len(prompt) > 200

        # Verify at least one canonical name from manifest appears
        field_names = [f.canonical_name for f in price_fields[:5]]
        assert any(name in prompt for name in field_names)


class TestConfigCreationPrompt:
    """Test suite for Stage 2: Config generation prompt"""

    def test_generate_config_creation_prompt_basic(self):
        """
        Test basic config creation prompt generation

        RED: This test should fail initially
        """
        selected_fields = ["price:收盤價", "fundamental_features:ROE"]

        prompt = generate_config_creation_prompt(
            selected_fields=selected_fields,
            strategy_type="momentum",
            schema_example=""
        )

        # Verify prompt is non-empty string
        assert isinstance(prompt, str)
        assert len(prompt) > 0

        # Verify prompt includes strategy type
        assert "momentum" in prompt.lower()

    def test_prompt_includes_selected_fields(self):
        """
        Test that prompt includes all selected fields

        RED: Should fail - need to format selected fields into prompt
        """
        selected_fields = ["price:收盤價", "price:成交金額", "fundamental_features:ROE"]

        prompt = generate_config_creation_prompt(
            selected_fields=selected_fields,
            strategy_type="momentum",
            schema_example=""
        )

        # Verify all selected fields appear in prompt
        for field in selected_fields:
            assert field in prompt

    def test_prompt_includes_yaml_schema(self):
        """
        Test that prompt includes YAML schema structure

        RED: Should fail - need to include YAML schema in prompt
        """
        selected_fields = ["price:收盤價"]
        schema_example = """
name: "Pure Momentum"
type: "momentum"
required_fields:
  - field: "price:收盤價"
    alias: "close"
    usage: "Signal generation"
"""

        prompt = generate_config_creation_prompt(
            selected_fields=selected_fields,
            strategy_type="momentum",
            schema_example=schema_example
        )

        # Verify YAML keywords appear
        assert "yaml" in prompt.lower()
        assert "name:" in prompt or "required_fields:" in prompt

        # Verify schema example is included
        assert "Pure Momentum" in prompt or schema_example in prompt

    def test_prompt_requests_yaml_output(self):
        """
        Test that prompt explicitly requests YAML output format

        RED: Should fail - need clear YAML output instruction
        """
        selected_fields = ["price:收盤價"]

        prompt = generate_config_creation_prompt(
            selected_fields=selected_fields,
            strategy_type="momentum",
            schema_example=""
        )

        # Verify YAML output is requested
        assert "yaml" in prompt.lower()
        assert "return" in prompt.lower() or "output" in prompt.lower()

    def test_different_strategy_types_config(self):
        """
        Test config prompt for different strategy types

        RED: Should fail - need to support multiple strategy types
        """
        selected_fields = ["price:收盤價", "fundamental_features:ROE"]
        strategy_types = ["momentum", "breakout", "factor_scoring", "hybrid"]

        for strategy_type in strategy_types:
            prompt = generate_config_creation_prompt(
                selected_fields=selected_fields,
                strategy_type=strategy_type,
                schema_example=""
            )

            # Verify strategy type appears in prompt
            assert strategy_type in prompt.lower()

    def test_empty_selected_fields_raises_error(self):
        """
        Test that empty selected fields raises error

        RED: Should fail - need error handling for empty input
        """
        with pytest.raises(ValueError, match="selected_fields cannot be empty"):
            generate_config_creation_prompt(
                selected_fields=[],
                strategy_type="momentum",
                schema_example=""
            )

    def test_integration_with_schema_patterns(self):
        """
        Test integration with strategy_schema.yaml patterns

        RED: Should fail - need to format schema examples properly
        """
        selected_fields = ["price:收盤價", "price:成交金額"]

        # Example from strategy_schema.yaml pure_momentum pattern
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
logic:
  entry: "(price.pct_change(momentum_period).rolling(5).mean() > 0.02) & (volume > 1000000)"
  exit: "None"
"""

        prompt = generate_config_creation_prompt(
            selected_fields=selected_fields,
            strategy_type="momentum",
            schema_example=schema_example
        )

        # Verify schema example components appear
        assert "required_fields:" in prompt
        assert "parameters:" in prompt
        assert "logic:" in prompt


class TestPromptFormatIntegration:
    """Integration tests for complete two-stage prompting workflow"""

    def test_two_stage_workflow(self):
        """
        Test complete workflow: Stage 1 → Stage 2

        RED: Should fail - need both functions working together
        """
        # Load manifest
        manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')

        # Stage 1: Generate field selection prompt
        available_fields = manifest.get_fields_by_category('price')[:5]
        stage1_prompt = generate_field_selection_prompt(
            available_fields=available_fields,
            strategy_type="momentum"
        )

        # Verify Stage 1 prompt is valid
        assert len(stage1_prompt) > 100
        assert "momentum" in stage1_prompt.lower()

        # Simulate LLM field selection (hardcoded for test)
        selected_fields = ["price:收盤價", "price:成交金額"]

        # Stage 2: Generate config creation prompt
        schema_example = "name: Test\ntype: momentum"
        stage2_prompt = generate_config_creation_prompt(
            selected_fields=selected_fields,
            strategy_type="momentum",
            schema_example=schema_example
        )

        # Verify Stage 2 prompt is valid
        assert len(stage2_prompt) > 100
        assert all(field in stage2_prompt for field in selected_fields)

    def test_prompt_format_consistency(self):
        """
        Test that prompts maintain consistent format

        RED: Should fail - need consistent formatting across both stages
        """
        manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
        fields = manifest.get_fields_by_category('price')[:3]

        # Generate Stage 1 prompt
        prompt1 = generate_field_selection_prompt(
            available_fields=fields,
            strategy_type="momentum"
        )

        # Generate Stage 2 prompt
        prompt2 = generate_config_creation_prompt(
            selected_fields=["price:收盤價"],
            strategy_type="momentum",
            schema_example=""
        )

        # Both prompts should follow similar structure
        for prompt in [prompt1, prompt2]:
            # Should have clear sections
            assert "##" in prompt or "#" in prompt  # Markdown headers

            # Should have clear task description
            assert len(prompt.split('\n')) > 5  # Multi-line format

            # Should include strategy type
            assert "momentum" in prompt.lower()
