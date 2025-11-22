"""
Test Suite for JSON-only Prompt Builder (TDD RED Phase)

Tests for JSON-only prompt generation in TemplateParameterGenerator.
Following TDD methodology: these tests are written FIRST before implementation.

Requirements: F2.1, F2.2, F2.3, F2.4, AC2
"""

import pytest


class TestJsonPromptBuilder:
    """Test suite for JSON-only prompt building."""

    def test_build_prompt_includes_json_schema_description(self):
        """
        GIVEN a TemplateParameterGenerator
        WHEN building a JSON-only prompt
        THEN the prompt includes JSON Schema description
        """
        from src.generators.json_prompt_builder import JsonPromptBuilder

        builder = JsonPromptBuilder()
        prompt = builder.build_prompt(
            template_name="Momentum",
            performance_context="High volatility market",
            feedback_context=""
        )

        # Should include JSON Schema or schema-like description
        assert "JSON" in prompt or "json" in prompt
        # Should describe the expected structure
        assert "reasoning" in prompt.lower()
        assert "params" in prompt.lower()

    def test_build_prompt_includes_parameter_constraints(self):
        """
        GIVEN a TemplateParameterGenerator
        WHEN building a JSON-only prompt
        THEN the prompt includes parameter constraints
        """
        from src.generators.json_prompt_builder import JsonPromptBuilder

        builder = JsonPromptBuilder()
        prompt = builder.build_prompt(
            template_name="Momentum",
            performance_context="",
            feedback_context=""
        )

        # Should include all 8 parameters with their allowed values
        assert "momentum_period" in prompt
        assert "ma_periods" in prompt
        assert "catalyst_type" in prompt
        assert "catalyst_lookback" in prompt
        assert "n_stocks" in prompt
        assert "stop_loss" in prompt
        assert "resample" in prompt
        assert "resample_offset" in prompt

        # Should show allowed values for at least some parameters
        # momentum_period: [5, 10, 20, 30]
        assert "5" in prompt and "10" in prompt and "20" in prompt and "30" in prompt

    def test_build_prompt_includes_few_shot_examples(self):
        """
        GIVEN a TemplateParameterGenerator
        WHEN building a JSON-only prompt
        THEN the prompt includes at least 2 few-shot examples
        """
        from src.generators.json_prompt_builder import JsonPromptBuilder

        builder = JsonPromptBuilder()
        prompt = builder.build_prompt(
            template_name="Momentum",
            performance_context="",
            feedback_context=""
        )

        # Count JSON-like structures in the prompt (at least 2 examples)
        # Look for example markers or JSON blocks
        example_count = prompt.lower().count("example")
        json_block_count = prompt.count('```')

        # Should have at least 2 examples
        assert example_count >= 2 or json_block_count >= 4  # 4 backtick groups = 2 examples

    def test_build_prompt_requests_json_only_output(self):
        """
        GIVEN a TemplateParameterGenerator
        WHEN building a JSON-only prompt
        THEN the prompt explicitly requests JSON-only output
        """
        from src.generators.json_prompt_builder import JsonPromptBuilder

        builder = JsonPromptBuilder()
        prompt = builder.build_prompt(
            template_name="Momentum",
            performance_context="",
            feedback_context=""
        )

        # Should explicitly request JSON output
        prompt_lower = prompt.lower()
        assert (
            "json only" in prompt_lower or
            "json-only" in prompt_lower or
            "only json" in prompt_lower or
            "respond with json" in prompt_lower or
            "output json" in prompt_lower or
            "return json" in prompt_lower
        )

    def test_build_prompt_includes_reasoning_constraints(self):
        """
        GIVEN a TemplateParameterGenerator
        WHEN building a JSON-only prompt
        THEN the prompt specifies reasoning field constraints (50-500 chars)
        """
        from src.generators.json_prompt_builder import JsonPromptBuilder

        builder = JsonPromptBuilder()
        prompt = builder.build_prompt(
            template_name="Momentum",
            performance_context="",
            feedback_context=""
        )

        # Should mention reasoning length constraints
        assert "50" in prompt or "fifty" in prompt.lower()
        assert "500" in prompt or "five hundred" in prompt.lower()

    def test_build_prompt_includes_cross_validation_rules(self):
        """
        GIVEN a TemplateParameterGenerator
        WHEN building a JSON-only prompt
        THEN mentions cross-parameter validation rules
        """
        from src.generators.json_prompt_builder import JsonPromptBuilder

        builder = JsonPromptBuilder()
        prompt = builder.build_prompt(
            template_name="Momentum",
            performance_context="",
            feedback_context=""
        )

        # Should mention momentum_period <= ma_periods rule
        prompt_lower = prompt.lower()
        assert (
            "momentum_period" in prompt_lower and "ma_periods" in prompt_lower
        )
        # Should indicate the relationship
        assert (
            "<=" in prompt or
            "less than" in prompt_lower or
            "smaller" in prompt_lower or
            "not exceed" in prompt_lower or
            "should be" in prompt_lower
        )

    def test_build_prompt_integrates_feedback_context(self):
        """
        GIVEN feedback from previous failed attempt
        WHEN building a JSON-only prompt
        THEN the prompt includes the feedback
        """
        from src.generators.json_prompt_builder import JsonPromptBuilder

        builder = JsonPromptBuilder()
        feedback = "Previous error: momentum_period=25 is invalid"
        prompt = builder.build_prompt(
            template_name="Momentum",
            performance_context="",
            feedback_context=feedback
        )

        # Should include the feedback
        assert "momentum_period" in prompt
        assert "25" in prompt or "invalid" in prompt.lower()

    def test_build_prompt_integrates_performance_context(self):
        """
        GIVEN performance context
        WHEN building a JSON-only prompt
        THEN the prompt includes performance considerations
        """
        from src.generators.json_prompt_builder import JsonPromptBuilder

        builder = JsonPromptBuilder()
        prompt = builder.build_prompt(
            template_name="Momentum",
            performance_context="High volatility market conditions",
            feedback_context=""
        )

        # Should include the performance context
        assert "volatility" in prompt.lower() or "market" in prompt.lower()

    def test_build_prompt_returns_valid_string(self):
        """
        GIVEN valid inputs
        WHEN building a JSON-only prompt
        THEN returns a non-empty string
        """
        from src.generators.json_prompt_builder import JsonPromptBuilder

        builder = JsonPromptBuilder()
        prompt = builder.build_prompt(
            template_name="Momentum",
            performance_context="",
            feedback_context=""
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial


class TestJsonPromptBuilderSchema:
    """Test suite for JSON Schema generation in prompt builder."""

    def test_get_json_schema_includes_all_fields(self):
        """
        GIVEN JsonPromptBuilder
        WHEN getting JSON schema
        THEN includes all required fields
        """
        from src.generators.json_prompt_builder import JsonPromptBuilder

        builder = JsonPromptBuilder()
        schema_str = builder.get_json_schema_description()

        assert "momentum_period" in schema_str
        assert "ma_periods" in schema_str
        assert "catalyst_type" in schema_str
        assert "catalyst_lookback" in schema_str
        assert "n_stocks" in schema_str
        assert "stop_loss" in schema_str
        assert "resample" in schema_str
        assert "resample_offset" in schema_str
        assert "reasoning" in schema_str

    def test_get_few_shot_examples_returns_valid_examples(self):
        """
        GIVEN JsonPromptBuilder
        WHEN getting few-shot examples
        THEN returns at least 2 valid JSON examples
        """
        from src.generators.json_prompt_builder import JsonPromptBuilder
        import json

        builder = JsonPromptBuilder()
        examples = builder.get_few_shot_examples()

        assert isinstance(examples, list)
        assert len(examples) >= 2

        # Each example should be valid JSON string
        for example in examples:
            parsed = json.loads(example)
            assert "reasoning" in parsed
            assert "params" in parsed
