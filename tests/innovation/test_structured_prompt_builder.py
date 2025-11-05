#!/usr/bin/env python3
"""
Unit tests for StructuredPromptBuilder
Task 5: Structured Innovation MVP - Prompt Engineering Testing

Tests:
- Prompt generation for all 3 strategy types
- Schema inclusion in prompt
- Examples inclusion
- Token budget (<2000 tokens)
- Champion feedback integration
- Failure pattern integration
"""

import json
import os
import pytest
from pathlib import Path

from src.innovation.structured_prompt_builder import StructuredPromptBuilder


class TestStructuredPromptBuilder:
    """Test suite for StructuredPromptBuilder."""

    @pytest.fixture
    def builder(self):
        """Create StructuredPromptBuilder instance."""
        return StructuredPromptBuilder()

    @pytest.fixture
    def champion_metrics(self):
        """Sample champion metrics."""
        return {
            "sharpe_ratio": 2.48,
            "annual_return": 0.12,
            "max_drawdown": -0.15,
            "win_rate": 0.32,
            "position_count": 3277
        }

    @pytest.fixture
    def failure_patterns(self):
        """Sample failure patterns from actual data."""
        return [
            "Increasing liquidity threshold above 50M causes performance drop",
            "Smoothing ROE over 60-day window reduces Sharpe by 1.1",
            "Decreasing liquidity threshold below 50 causes -2.5 Sharpe drop",
            "Large drawdowns when P/E filter is removed",
            "Overtrading when rebalancing frequency set to daily"
        ]

    def test_builder_initialization(self, builder):
        """Test StructuredPromptBuilder initializes correctly."""
        assert builder is not None
        assert builder.schema is not None
        assert isinstance(builder.schema, dict)
        assert builder.examples is not None
        assert isinstance(builder.examples, dict)

    def test_schema_loading(self, builder):
        """Test schema is loaded correctly."""
        schema = builder.schema

        # Check critical schema fields
        assert "$schema" in schema
        assert "properties" in schema
        assert "required" in schema

        # Check required top-level fields
        required_fields = schema["required"]
        assert "metadata" in required_fields
        assert "indicators" in required_fields
        assert "entry_conditions" in required_fields

        # Check metadata properties
        metadata_props = schema["properties"]["metadata"]["properties"]
        assert "name" in metadata_props
        assert "strategy_type" in metadata_props
        assert "rebalancing_frequency" in metadata_props

    def test_examples_loading(self, builder):
        """Test all 3 strategy examples are loaded."""
        examples = builder.examples

        # Check all 3 strategy types present
        assert "momentum" in examples
        assert "mean_reversion" in examples
        assert "factor_combination" in examples

        # Check examples are non-empty
        for strategy_type, example in examples.items():
            assert len(example) > 0, f"{strategy_type} example is empty"
            assert "metadata:" in example, f"{strategy_type} missing metadata"
            assert "indicators:" in example, f"{strategy_type} missing indicators"
            assert "entry_conditions:" in example, f"{strategy_type} missing entry_conditions"

    def test_schema_excerpt(self, builder):
        """Test schema excerpt includes critical fields."""
        excerpt = builder._include_schema_excerpt()

        # Check critical sections present
        assert "metadata:" in excerpt
        assert "indicators:" in excerpt
        assert "entry_conditions:" in excerpt
        assert "position_sizing:" in excerpt

        # Check strategy types listed
        assert "momentum" in excerpt
        assert "mean_reversion" in excerpt
        assert "factor_combination" in excerpt

        # Check important fields
        assert "rebalancing_frequency" in excerpt
        assert "RSI" in excerpt or "technical_indicators" in excerpt
        assert "threshold_rules" in excerpt or "ranking_rules" in excerpt

    def test_prompt_generation_momentum(self, builder, champion_metrics, failure_patterns):
        """Test prompt generation for momentum strategy."""
        prompt = builder.build_yaml_generation_prompt(
            champion_metrics=champion_metrics,
            failure_patterns=failure_patterns,
            target_strategy_type="momentum"
        )

        # Check prompt contains key sections
        assert "momentum" in prompt.lower()
        assert "Champion Metrics" in prompt
        assert "Failure Patterns" in prompt
        assert "Schema" in prompt
        assert "Example" in prompt

        # Check champion metrics included
        assert str(champion_metrics["sharpe_ratio"]) in prompt or "2.48" in prompt
        assert "15%" in prompt or "12%" in prompt or "12.0%" in prompt  # annual return

        # Check failure patterns included (at least first few)
        for pattern in failure_patterns[:3]:
            # Might be truncated, check first part
            pattern_start = pattern.split()[0]
            assert pattern_start in prompt

        # Check instructions included
        assert "YAML" in prompt
        assert "metadata:" in prompt

    def test_prompt_generation_mean_reversion(self, builder, champion_metrics, failure_patterns):
        """Test prompt generation for mean_reversion strategy."""
        prompt = builder.build_yaml_generation_prompt(
            champion_metrics=champion_metrics,
            failure_patterns=failure_patterns,
            target_strategy_type="mean_reversion"
        )

        # Check strategy type mentioned
        assert "mean_reversion" in prompt or "mean reversion" in prompt.lower()

        # Check contains example
        assert "Example" in prompt
        assert "metadata:" in prompt

        # Check schema present
        assert "Schema" in prompt
        assert "indicators:" in prompt

    def test_prompt_generation_factor_combination(self, builder, champion_metrics, failure_patterns):
        """Test prompt generation for factor_combination strategy."""
        prompt = builder.build_yaml_generation_prompt(
            champion_metrics=champion_metrics,
            failure_patterns=failure_patterns,
            target_strategy_type="factor_combination"
        )

        # Check strategy type mentioned
        assert "factor_combination" in prompt or "factor combination" in prompt.lower()

        # Check contains example
        assert "Example" in prompt

        # Check schema present
        assert "Schema" in prompt

    def test_token_budget_full_prompt(self, builder, champion_metrics, failure_patterns):
        """Test full prompt respects token budget guidelines."""
        for strategy_type in ["momentum", "mean_reversion", "factor_combination"]:
            prompt = builder.build_yaml_generation_prompt(
                champion_metrics=champion_metrics,
                failure_patterns=failure_patterns,
                target_strategy_type=strategy_type
            )

            token_count = builder.count_tokens(prompt)

            # Full prompt should be reasonable (<3000 tokens is acceptable)
            # Compact prompt will be <2000
            assert token_count < 3000, f"{strategy_type} full prompt has {token_count} tokens (too large)"

    def test_token_budget_compact_prompt(self, builder, champion_metrics, failure_patterns):
        """Test compact prompt stays under 2000 tokens."""
        for strategy_type in ["momentum", "mean_reversion", "factor_combination"]:
            prompt = builder.build_compact_prompt(
                champion_metrics=champion_metrics,
                failure_patterns=failure_patterns,
                target_strategy_type=strategy_type
            )

            token_count = builder.count_tokens(prompt)

            # Compact prompt MUST be under 2000 tokens
            assert token_count < 2000, f"{strategy_type} compact prompt has {token_count} tokens (exceeds 2000)"

    def test_compact_prompt_includes_essentials(self, builder, champion_metrics, failure_patterns):
        """Test compact prompt still includes essential information."""
        prompt = builder.build_compact_prompt(
            champion_metrics=champion_metrics,
            failure_patterns=failure_patterns,
            target_strategy_type="momentum"
        )

        # Check essentials present
        assert "momentum" in prompt.lower()
        assert "Sharpe" in prompt or "sharpe" in prompt.lower()
        assert "Schema" in prompt or "schema" in prompt.lower()
        assert "metadata:" in prompt
        assert "YAML" in prompt

    def test_champion_feedback_integration(self, builder):
        """Test champion feedback is properly integrated into prompt."""
        champion = {
            "sharpe_ratio": 3.0,
            "annual_return": 0.25,
            "max_drawdown": -0.10
        }

        prompt = builder.build_yaml_generation_prompt(
            champion_metrics=champion,
            failure_patterns=[],
            target_strategy_type="momentum"
        )

        # Check champion metrics appear in prompt
        assert "3.0" in prompt or "3" in prompt  # Sharpe ratio
        assert "25%" in prompt or "0.25" in prompt  # Annual return
        assert "10%" in prompt or "0.10" in prompt or "0.1" in prompt  # Max drawdown

    def test_failure_pattern_integration(self, builder, champion_metrics):
        """Test failure patterns are integrated into prompt."""
        failures = [
            "Overtrading reduces Sharpe by 0.5",
            "Large positions (>15%) cause high drawdowns",
            "Missing liquidity filter causes execution issues"
        ]

        prompt = builder.build_yaml_generation_prompt(
            champion_metrics=champion_metrics,
            failure_patterns=failures,
            target_strategy_type="momentum"
        )

        # Check failure patterns section exists
        assert "Failure" in prompt or "Avoid" in prompt

        # Check at least some failure patterns present
        failure_mentions = sum(1 for f in failures if any(word in prompt for word in f.split()[:3]))
        assert failure_mentions >= 2, "Not enough failure patterns in prompt"

    def test_get_example(self, builder):
        """Test getting specific examples."""
        # Test getting each example
        for strategy_type in ["momentum", "mean_reversion", "factor_combination"]:
            example = builder.get_example(strategy_type)

            assert len(example) > 0, f"{strategy_type} example is empty"
            assert "metadata:" in example
            assert f'strategy_type: "{strategy_type}"' in example or \
                   f"strategy_type: '{strategy_type}'" in example or \
                   f"strategy_type: {strategy_type}" in example

    def test_default_parameters(self, builder):
        """Test prompt generation with default parameters."""
        # Should work with no champion metrics or failure patterns
        prompt = builder.build_yaml_generation_prompt()

        assert len(prompt) > 0
        assert "momentum" in prompt.lower()  # Default strategy type
        assert "YAML" in prompt
        assert "metadata:" in prompt

    def test_multiple_prompt_generations(self, builder, champion_metrics, failure_patterns):
        """Test generating prompts for all strategy types sequentially."""
        prompts = {}

        for strategy_type in ["momentum", "mean_reversion", "factor_combination"]:
            prompt = builder.build_yaml_generation_prompt(
                champion_metrics=champion_metrics,
                failure_patterns=failure_patterns,
                target_strategy_type=strategy_type
            )
            prompts[strategy_type] = prompt

        # Check all prompts generated
        assert len(prompts) == 3

        # Check prompts are different
        assert prompts["momentum"] != prompts["mean_reversion"]
        assert prompts["momentum"] != prompts["factor_combination"]
        assert prompts["mean_reversion"] != prompts["factor_combination"]

    def test_prompt_yaml_format_instructions(self, builder):
        """Test prompt includes clear YAML format instructions."""
        prompt = builder.build_yaml_generation_prompt(
            target_strategy_type="momentum"
        )

        # Check for YAML-specific instructions
        assert "YAML" in prompt
        assert "metadata:" in prompt

        # Check instructions mention output format
        instructions_keywords = ["Output", "valid", "metadata:"]
        matches = sum(1 for keyword in instructions_keywords if keyword in prompt)
        assert matches >= 2, "Missing clear output format instructions"

    def test_token_counting_accuracy(self, builder):
        """Test token counting is reasonable."""
        test_texts = [
            "This is a short test",  # ~5 tokens
            "metadata:\n  name: Test\n  description: Testing",  # ~10 tokens
            "A" * 400  # ~100 tokens
        ]

        for text in test_texts:
            count = builder.count_tokens(text)
            # Token count should be roughly len(text) / 4
            expected = len(text) // 4
            assert abs(count - expected) <= expected * 0.2, f"Token count {count} too far from expected {expected}"

    def test_schema_validation(self, builder):
        """Test loaded schema is valid JSON Schema."""
        schema = builder.schema

        # Basic JSON Schema validation
        assert "$schema" in schema
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert "type" in schema
        assert schema["type"] == "object"

    def test_example_yaml_validity(self, builder):
        """Test example YAMLs are syntactically valid."""
        import yaml

        for strategy_type, example_yaml in builder.examples.items():
            try:
                # Parse YAML
                parsed = yaml.safe_load(example_yaml)

                # Check basic structure
                assert "metadata" in parsed, f"{strategy_type} missing metadata"
                assert "indicators" in parsed, f"{strategy_type} missing indicators"
                assert "entry_conditions" in parsed, f"{strategy_type} missing entry_conditions"

                # Check metadata fields
                metadata = parsed["metadata"]
                assert "name" in metadata
                assert "strategy_type" in metadata
                assert metadata["strategy_type"] == strategy_type

            except yaml.YAMLError as e:
                pytest.fail(f"{strategy_type} example YAML is invalid: {e}")

    def test_prompt_includes_schema_constraints(self, builder):
        """Test prompt includes key schema constraints."""
        prompt = builder.build_yaml_generation_prompt(
            target_strategy_type="momentum"
        )

        # Check important constraints mentioned
        constraints = [
            "required",  # Required fields
            "RSI",  # Technical indicator types
            "ROE",  # Fundamental factor types
            "stop_loss",  # Exit conditions
            "equal_weight"  # Position sizing methods
        ]

        matches = sum(1 for constraint in constraints if constraint in prompt)
        assert matches >= 3, "Not enough schema constraints in prompt"


class TestPromptQuality:
    """Test prompt quality and completeness."""

    @pytest.fixture
    def builder(self):
        """Create StructuredPromptBuilder instance."""
        return StructuredPromptBuilder()

    def test_prompt_completeness(self, builder):
        """Test prompt contains all necessary components."""
        champion = {"sharpe_ratio": 2.0, "annual_return": 0.15, "max_drawdown": -0.10}
        failures = ["Pattern 1", "Pattern 2"]

        prompt = builder.build_yaml_generation_prompt(
            champion_metrics=champion,
            failure_patterns=failures,
            target_strategy_type="momentum"
        )

        # Key sections
        required_sections = [
            "Champion Metrics",
            "Failure Patterns",
            "Schema",
            "Example",
            "Instructions"
        ]

        for section in required_sections:
            assert section in prompt, f"Missing section: {section}"

    def test_examples_diversity(self, builder):
        """Test examples cover diverse patterns."""
        examples = builder.examples

        # Check momentum example has momentum-specific elements
        momentum = examples["momentum"]
        assert "rsi" in momentum.lower() or "momentum" in momentum.lower()

        # Check mean reversion has BB or reversion elements
        mean_rev = examples["mean_reversion"]
        assert "bollinger" in mean_rev.lower() or "reversion" in mean_rev.lower() or "bb_" in mean_rev

        # Check factor combination has multiple factors
        factor_combo = examples["factor_combination"]
        assert "roe" in factor_combo.lower()
        assert ("growth" in factor_combo.lower() or "revenue" in factor_combo.lower())
        assert ("pe" in factor_combo.lower() or "value" in factor_combo.lower())


class TestYAMLExtraction:
    """Test YAML extraction from LLM responses."""

    @pytest.fixture
    def builder(self):
        """Create StructuredPromptBuilder instance."""
        return StructuredPromptBuilder()

    def test_extract_yaml_with_yaml_marker(self, builder):
        """Test extracting YAML from ```yaml code block."""
        llm_response = """
Here is the strategy:

```yaml
metadata:
  name: "Test Strategy"
  strategy_type: "momentum"
  rebalancing_frequency: "M"

indicators:
  technical_indicators:
    - name: "rsi_14"
      type: "RSI"
      period: 14

entry_conditions:
  threshold_rules:
    - condition: "rsi_14 > 30"
```

This should work well!
"""
        yaml_content, success = builder.extract_yaml(llm_response)

        assert success, "Failed to extract YAML"
        assert yaml_content is not None
        assert "metadata:" in yaml_content
        assert "Test Strategy" in yaml_content
        assert "This should work well!" not in yaml_content  # Explanation excluded

    def test_extract_yaml_without_marker(self, builder):
        """Test extracting YAML from ``` generic code block."""
        llm_response = """
```
metadata:
  name: "Test Strategy"
  strategy_type: "mean_reversion"
  rebalancing_frequency: "W-FRI"

indicators:
  fundamental_factors:
    - name: "roe"
      field: "ROE"

entry_conditions:
  threshold_rules:
    - condition: "roe > 0.15"
```
"""
        yaml_content, success = builder.extract_yaml(llm_response)

        assert success, "Failed to extract YAML from generic code block"
        assert yaml_content is not None
        assert "metadata:" in yaml_content
        assert "mean_reversion" in yaml_content

    def test_extract_yaml_json_format(self, builder):
        """Test extracting JSON-formatted YAML from ```json code block."""
        llm_response = """
```json
{
  "metadata": {
    "name": "Test Strategy",
    "strategy_type": "factor_combination",
    "rebalancing_frequency": "M"
  },
  "indicators": {},
  "entry_conditions": {}
}
```
"""
        yaml_content, success = builder.extract_yaml(llm_response)

        # JSON is valid YAML
        assert success or yaml_content is not None, "Failed to extract JSON as YAML"

    def test_extract_yaml_no_code_blocks(self, builder):
        """Test extracting YAML when no code blocks present."""
        llm_response = """metadata:
  name: "Direct YAML"
  strategy_type: "momentum"
  rebalancing_frequency: "M"

indicators:
  technical_indicators:
    - name: "rsi_14"
      type: "RSI"

entry_conditions:
  threshold_rules:
    - condition: "rsi_14 > 30"
"""
        yaml_content, success = builder.extract_yaml(llm_response)

        assert success, "Failed to extract YAML without code blocks"
        assert yaml_content is not None
        assert "metadata:" in yaml_content

    def test_extract_yaml_failure_invalid_response(self, builder):
        """Test extraction fails gracefully for invalid responses."""
        invalid_responses = [
            "",  # Empty
            "This is just plain text without YAML",
            "```\nNot YAML at all\njust random text\n```",
            None,
        ]

        for response in invalid_responses:
            if response is None:
                continue
            yaml_content, success = builder.extract_yaml(response)
            assert not success, f"Should fail for invalid response: {response[:50]}"

    def test_looks_like_yaml_validation(self, builder):
        """Test _looks_like_yaml validation logic."""
        # Valid YAML-like text
        valid_yaml = """metadata:
  name: "Test"
indicators:
  technical_indicators:
    - name: "test"
entry_conditions:
  threshold_rules:
    - condition: "test > 0"
"""
        assert builder._looks_like_yaml(valid_yaml), "Valid YAML not recognized"

        # Invalid text (missing required sections)
        invalid_texts = [
            "",
            "Just plain text",
            "metadata:\n  name: test",  # Missing indicators and entry_conditions
            "key: value",  # No indentation
        ]

        for text in invalid_texts:
            assert not builder._looks_like_yaml(text), f"Invalid text recognized as YAML: {text[:50]}"

    def test_validate_extracted_yaml_success(self, builder):
        """Test validation of extracted YAML succeeds for valid YAML."""
        valid_yaml = """metadata:
  name: "Test Strategy"
  strategy_type: "momentum"
  rebalancing_frequency: "M"

indicators:
  technical_indicators:
    - name: "rsi_14"
      type: "RSI"
      period: 14

entry_conditions:
  threshold_rules:
    - condition: "rsi_14 > 30"

position_sizing:
  method: "equal_weight"
  max_positions: 20
"""
        parsed, errors = builder.validate_extracted_yaml(valid_yaml)

        assert parsed is not None, "Failed to parse valid YAML"
        assert len(errors) == 0, f"Unexpected errors: {errors}"
        assert isinstance(parsed, dict)
        assert "metadata" in parsed
        assert "indicators" in parsed
        assert "entry_conditions" in parsed

    def test_validate_extracted_yaml_missing_fields(self, builder):
        """Test validation fails for YAML missing required fields."""
        # Missing entry_conditions
        invalid_yaml = """metadata:
  name: "Test"
  strategy_type: "momentum"
  rebalancing_frequency: "M"

indicators:
  technical_indicators:
    - name: "rsi_14"
      type: "RSI"
"""
        parsed, errors = builder.validate_extracted_yaml(invalid_yaml)

        assert parsed is None, "Should fail for missing entry_conditions"
        assert len(errors) > 0
        assert any("entry_conditions" in err for err in errors)

    def test_validate_extracted_yaml_syntax_error(self, builder):
        """Test validation fails for invalid YAML syntax."""
        invalid_yaml = """metadata:
  name: "Test"
  strategy_type: momentum  # Missing quotes
  this is bad syntax: [
"""
        parsed, errors = builder.validate_extracted_yaml(invalid_yaml)

        assert parsed is None, "Should fail for syntax errors"
        assert len(errors) > 0

    def test_extraction_patterns_count(self, builder):
        """Test builder has multiple extraction patterns."""
        assert len(builder.yaml_patterns) >= 4, "Should have at least 4 extraction patterns"

    def test_extract_yaml_multiple_code_blocks(self, builder):
        """Test extraction works when multiple code blocks present."""
        llm_response = """
First, here's some code:
```python
def test():
    pass
```

Now the YAML strategy:
```yaml
metadata:
  name: "Real Strategy"
  strategy_type: "momentum"
  rebalancing_frequency: "M"

indicators:
  technical_indicators:
    - name: "rsi_14"
      type: "RSI"

entry_conditions:
  threshold_rules:
    - condition: "rsi_14 > 30"
```

And some more text.
```
Other stuff
```
"""
        yaml_content, success = builder.extract_yaml(llm_response)

        assert success, "Failed to extract YAML from multiple code blocks"
        assert "Real Strategy" in yaml_content
        assert "def test():" not in yaml_content  # Python code excluded
        assert "Other stuff" not in yaml_content  # Other code blocks excluded


class TestRetryLogic:
    """Test retry logic for malformed responses."""

    @pytest.fixture
    def builder(self):
        """Create StructuredPromptBuilder instance."""
        return StructuredPromptBuilder()

    @pytest.fixture
    def champion_metrics(self):
        """Sample champion metrics."""
        return {"sharpe_ratio": 2.0, "annual_return": 0.15, "max_drawdown": -0.10}

    def test_get_retry_prompt_includes_error(self, builder, champion_metrics):
        """Test retry prompt includes previous error message."""
        error_msg = "YAML parsing error: missing required field 'metadata'"

        retry_prompt = builder.get_retry_prompt(
            retry_attempt=1,
            previous_error=error_msg,
            champion_metrics=champion_metrics,
            target_strategy_type="momentum"
        )

        assert error_msg in retry_prompt, "Error message not in retry prompt"
        assert "RETRY" in retry_prompt.upper(), "Retry indicator missing"

    def test_get_retry_prompt_includes_instructions(self, builder, champion_metrics):
        """Test retry prompt includes enhanced instructions."""
        retry_prompt = builder.get_retry_prompt(
            retry_attempt=2,
            previous_error="Invalid YAML syntax",
            champion_metrics=champion_metrics,
            target_strategy_type="mean_reversion"
        )

        # Check for retry-specific instructions
        assert "RETRY ATTEMPT 2" in retry_prompt or "retry attempt 2" in retry_prompt.lower()
        assert "```yaml" in retry_prompt  # Format example
        assert "CRITICAL" in retry_prompt or "critical" in retry_prompt.lower()

    def test_get_retry_prompt_still_includes_base_content(self, builder, champion_metrics):
        """Test retry prompt still includes original prompt content."""
        retry_prompt = builder.get_retry_prompt(
            retry_attempt=1,
            previous_error="Test error",
            champion_metrics=champion_metrics,
            failure_patterns=["Pattern 1"],
            target_strategy_type="factor_combination"
        )

        # Should still have base prompt elements
        assert "Schema" in retry_prompt
        assert "Example" in retry_prompt or "metadata:" in retry_prompt
        assert "factor_combination" in retry_prompt or "factor combination" in retry_prompt.lower()

    def test_retry_attempts_increment(self, builder, champion_metrics):
        """Test retry attempt numbers increment correctly."""
        for attempt in [1, 2, 3]:
            retry_prompt = builder.get_retry_prompt(
                retry_attempt=attempt,
                previous_error="Test error",
                champion_metrics=champion_metrics,
                target_strategy_type="momentum"
            )

            assert f"RETRY ATTEMPT {attempt}" in retry_prompt or \
                   f"retry attempt {attempt}" in retry_prompt.lower()


class TestStatistics:
    """Test statistics and monitoring functionality."""

    @pytest.fixture
    def builder(self):
        """Create StructuredPromptBuilder instance."""
        return StructuredPromptBuilder()

    def test_get_statistics(self, builder):
        """Test statistics retrieval."""
        stats = builder.get_statistics()

        assert isinstance(stats, dict)
        assert "schema_loaded" in stats
        assert "examples_loaded" in stats
        assert "example_types" in stats
        assert "extraction_patterns" in stats

    def test_statistics_schema_info(self, builder):
        """Test statistics include schema information."""
        stats = builder.get_statistics()

        assert stats["schema_loaded"] is True
        assert "schema_version" in stats

    def test_statistics_examples_count(self, builder):
        """Test statistics show correct example count."""
        stats = builder.get_statistics()

        assert stats["examples_loaded"] == 3, "Should have 3 examples"
        assert len(stats["example_types"]) == 3
        assert "momentum" in stats["example_types"]
        assert "mean_reversion" in stats["example_types"]
        assert "factor_combination" in stats["example_types"]

    def test_statistics_extraction_patterns(self, builder):
        """Test statistics show extraction pattern count."""
        stats = builder.get_statistics()

        assert stats["extraction_patterns"] >= 4, "Should have at least 4 extraction patterns"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
