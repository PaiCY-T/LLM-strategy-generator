"""
Test Suite for TemplateCodeGenerator (TDD RED Phase)

Tests for JSON extraction, parameter validation, and code generation.
Following TDD methodology: these tests are written FIRST before implementation.

Requirements: F3.1, F3.2, F3.3, AC3
"""

import pytest
from pydantic import ValidationError


class TestJsonExtraction:
    """Test suite for _extract_json method."""

    # ==========================================================================
    # Happy Path Tests - JSON Extraction from Various Formats
    # ==========================================================================

    def test_extract_plain_json(self):
        """
        GIVEN plain JSON string
        WHEN calling _extract_json
        THEN returns the JSON string unchanged
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate

        generator = TemplateCodeGenerator(MomentumTemplate())
        raw_output = '{"reasoning": "test", "params": {}}'

        result = generator._extract_json(raw_output)

        assert result == '{"reasoning": "test", "params": {}}'

    def test_extract_json_from_markdown_json_block(self):
        """
        GIVEN JSON wrapped in ```json markdown block
        WHEN calling _extract_json
        THEN returns clean JSON string
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate

        generator = TemplateCodeGenerator(MomentumTemplate())
        raw_output = '''Here is my response:

```json
{
  "reasoning": "test reasoning",
  "params": {
    "momentum_period": 10
  }
}
```

Hope this helps!'''

        result = generator._extract_json(raw_output)

        # Should extract just the JSON part
        assert '"reasoning": "test reasoning"' in result
        assert '"momentum_period": 10' in result
        assert '```' not in result

    def test_extract_json_from_markdown_block_no_language(self):
        """
        GIVEN JSON wrapped in ``` markdown block (no language specifier)
        WHEN calling _extract_json
        THEN returns clean JSON string
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate

        generator = TemplateCodeGenerator(MomentumTemplate())
        raw_output = '''```
{"reasoning": "simple test", "params": {}}
```'''

        result = generator._extract_json(raw_output)

        assert '{"reasoning": "simple test", "params": {}}' in result

    def test_extract_json_with_surrounding_text(self):
        """
        GIVEN JSON with surrounding text but no code blocks
        WHEN calling _extract_json
        THEN extracts the JSON object
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate

        generator = TemplateCodeGenerator(MomentumTemplate())
        raw_output = '''Here is my analysis:

{"reasoning": "extracted json", "params": {"momentum_period": 5}}

Thank you for your question!'''

        result = generator._extract_json(raw_output)

        assert '"reasoning": "extracted json"' in result

    # ==========================================================================
    # Error Cases
    # ==========================================================================

    def test_extract_json_malformed_raises_error(self):
        """
        GIVEN malformed JSON string
        WHEN calling _extract_json
        THEN raises ValueError with descriptive message
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate

        generator = TemplateCodeGenerator(MomentumTemplate())
        raw_output = '{"reasoning": "unclosed string}'

        with pytest.raises(ValueError) as exc_info:
            generator._extract_json(raw_output)

        assert "JSON" in str(exc_info.value) or "parse" in str(exc_info.value).lower()

    def test_extract_json_no_json_found_raises_error(self):
        """
        GIVEN string with no JSON content
        WHEN calling _extract_json
        THEN raises ValueError
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate

        generator = TemplateCodeGenerator(MomentumTemplate())
        raw_output = 'This is just plain text with no JSON.'

        with pytest.raises(ValueError) as exc_info:
            generator._extract_json(raw_output)

        assert "JSON" in str(exc_info.value)


class TestParameterValidation:
    """Test suite for _validate_params method."""

    def test_validate_valid_params(self):
        """
        GIVEN valid JSON string with correct parameters
        WHEN calling _validate_params
        THEN returns StrategyParamRequest object
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate
        from src.schemas.strategy_params import StrategyParamRequest

        generator = TemplateCodeGenerator(MomentumTemplate())
        json_str = '''{
            "reasoning": "選擇 20 天動量週期配合 60 天均線。收入催化劑可靠。15 支股票平衡分散。10% 停損適合動量策略。",
            "params": {
                "momentum_period": 20,
                "ma_periods": 60,
                "catalyst_type": "revenue",
                "catalyst_lookback": 3,
                "n_stocks": 15,
                "stop_loss": 0.10,
                "resample": "W",
                "resample_offset": 0
            }
        }'''

        result = generator._validate_params(json_str)

        assert isinstance(result, StrategyParamRequest)
        assert result.params.momentum_period == 20
        assert result.params.catalyst_type == "revenue"

    def test_validate_invalid_param_value_raises_error(self):
        """
        GIVEN JSON with invalid parameter value
        WHEN calling _validate_params
        THEN raises ValidationError
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate

        generator = TemplateCodeGenerator(MomentumTemplate())
        json_str = '''{
            "reasoning": "This is at least fifty characters of reasoning text for validation purposes.",
            "params": {
                "momentum_period": 25,
                "ma_periods": 60,
                "catalyst_type": "revenue",
                "catalyst_lookback": 3,
                "n_stocks": 15,
                "stop_loss": 0.10,
                "resample": "W",
                "resample_offset": 0
            }
        }'''

        with pytest.raises(ValidationError) as exc_info:
            generator._validate_params(json_str)

        assert "momentum_period" in str(exc_info.value)

    def test_validate_missing_field_raises_error(self):
        """
        GIVEN JSON with missing required field
        WHEN calling _validate_params
        THEN raises ValidationError
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate

        generator = TemplateCodeGenerator(MomentumTemplate())
        json_str = '''{
            "reasoning": "This is at least fifty characters of reasoning text for validation purposes.",
            "params": {
                "ma_periods": 60,
                "catalyst_type": "revenue",
                "catalyst_lookback": 3,
                "n_stocks": 15,
                "stop_loss": 0.10,
                "resample": "W",
                "resample_offset": 0
            }
        }'''

        with pytest.raises(ValidationError) as exc_info:
            generator._validate_params(json_str)

        assert "momentum_period" in str(exc_info.value)


class TestParameterInjection:
    """Test suite for _inject_params method."""

    def test_inject_valid_params_generates_code(self):
        """
        GIVEN valid MomentumStrategyParams
        WHEN calling _inject_params
        THEN returns generated Python code string
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate
        from src.schemas.strategy_params import MomentumStrategyParams

        generator = TemplateCodeGenerator(MomentumTemplate())
        params = MomentumStrategyParams(
            momentum_period=20,
            ma_periods=60,
            catalyst_type="revenue",
            catalyst_lookback=3,
            n_stocks=15,
            stop_loss=0.10,
            resample="W",
            resample_offset=0
        )

        code = generator._inject_params(params)

        # Verify code is a non-empty string
        assert isinstance(code, str)
        assert len(code) > 0
        # Should contain key parameter values
        assert "20" in code or "momentum_period" in code
        assert "60" in code or "ma_periods" in code

    def test_inject_params_all_values_present(self):
        """
        GIVEN MomentumStrategyParams with specific values
        WHEN calling _inject_params
        THEN all 8 parameter values appear in generated code
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate
        from src.schemas.strategy_params import MomentumStrategyParams

        generator = TemplateCodeGenerator(MomentumTemplate())
        params = MomentumStrategyParams(
            momentum_period=10,
            ma_periods=90,
            catalyst_type="earnings",
            catalyst_lookback=4,
            n_stocks=10,
            stop_loss=0.12,
            resample="M",
            resample_offset=2
        )

        code = generator._inject_params(params)

        # All parameter values should be present in the code
        assert "10" in code  # momentum_period
        assert "90" in code  # ma_periods
        assert "earnings" in code  # catalyst_type
        assert "4" in code  # catalyst_lookback
        assert "0.12" in code  # stop_loss
        assert "M" in code or "resample" in code  # resample


class TestGenerateMethod:
    """Test suite for main generate() method."""

    def test_generate_success_returns_result(self):
        """
        GIVEN valid LLM output with correct JSON
        WHEN calling generate()
        THEN returns GenerationResult with success=True and code
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate

        generator = TemplateCodeGenerator(MomentumTemplate())
        llm_output = '''```json
{
    "reasoning": "選擇 20 天動量週期配合 60 天均線。收入催化劑可靠。15 支股票平衡分散。10% 停損適合動量策略。",
    "params": {
        "momentum_period": 20,
        "ma_periods": 60,
        "catalyst_type": "revenue",
        "catalyst_lookback": 3,
        "n_stocks": 15,
        "stop_loss": 0.10,
        "resample": "W",
        "resample_offset": 0
    }
}
```'''

        result = generator.generate(llm_output)

        assert result.success is True
        assert result.code is not None
        assert len(result.code) > 0
        assert result.params is not None
        assert result.params.momentum_period == 20
        assert len(result.errors) == 0

    def test_generate_validation_error_returns_errors(self):
        """
        GIVEN LLM output with invalid parameter value
        WHEN calling generate()
        THEN returns GenerationResult with success=False and errors
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate

        generator = TemplateCodeGenerator(MomentumTemplate())
        llm_output = '''{
            "reasoning": "This is at least fifty characters of reasoning text for validation purposes.",
            "params": {
                "momentum_period": 25,
                "ma_periods": 60,
                "catalyst_type": "revenue",
                "catalyst_lookback": 3,
                "n_stocks": 15,
                "stop_loss": 0.10,
                "resample": "W",
                "resample_offset": 0
            }
        }'''

        result = generator.generate(llm_output)

        assert result.success is False
        assert result.code is None
        assert len(result.errors) > 0

    def test_generate_json_error_returns_errors(self):
        """
        GIVEN LLM output with malformed JSON
        WHEN calling generate()
        THEN returns GenerationResult with success=False and errors
        """
        from src.generators.template_code_generator import TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate

        generator = TemplateCodeGenerator(MomentumTemplate())
        llm_output = '{"reasoning": "unclosed'

        result = generator.generate(llm_output)

        assert result.success is False
        assert result.code is None
        assert len(result.errors) > 0


class TestGenerationResult:
    """Test suite for GenerationResult dataclass."""

    def test_generation_result_success_structure(self):
        """
        GIVEN a successful generation
        WHEN accessing GenerationResult
        THEN has correct structure with success, code, params, errors
        """
        from src.generators.template_code_generator import GenerationResult
        from src.schemas.strategy_params import MomentumStrategyParams

        params = MomentumStrategyParams(
            momentum_period=20,
            ma_periods=60,
            catalyst_type="revenue",
            catalyst_lookback=3,
            n_stocks=15,
            stop_loss=0.10,
            resample="W",
            resample_offset=0
        )

        result = GenerationResult(
            success=True,
            code="def strategy(): pass",
            params=params,
            errors=[]
        )

        assert result.success is True
        assert result.code == "def strategy(): pass"
        assert result.params == params
        assert result.errors == []

    def test_generation_result_failure_structure(self):
        """
        GIVEN a failed generation
        WHEN accessing GenerationResult
        THEN has correct structure with success=False and errors
        """
        from src.generators.template_code_generator import GenerationResult

        result = GenerationResult(
            success=False,
            code=None,
            params=None,
            errors=["Invalid momentum_period: 25"]
        )

        assert result.success is False
        assert result.code is None
        assert result.params is None
        assert len(result.errors) == 1

    def test_generation_result_get_feedback_prompt(self):
        """
        GIVEN a GenerationResult with errors
        WHEN calling get_feedback_prompt()
        THEN returns LLM-friendly error feedback string
        """
        from src.generators.template_code_generator import GenerationResult

        result = GenerationResult(
            success=False,
            code=None,
            params=None,
            errors=["momentum_period: 25 is not valid, use [5, 10, 20, 30]"]
        )

        feedback = result.get_feedback_prompt()

        assert isinstance(feedback, str)
        assert len(feedback) > 0
        # Should contain error information
        assert "momentum_period" in feedback or "error" in feedback.lower()
