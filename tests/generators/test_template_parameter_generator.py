"""
Tests for TemplateParameterGenerator - Template-aware parameter generation

Test Coverage:
    - Initialization (__init__)
    - Prompt building (_build_prompt)
    - Response parsing (_parse_response) with 4 fallback strategies
    - Parameter validation (_validate_params)
    - End-to-end parameter generation (generate_parameters)
    - Error handling and graceful failures
    - Exploration mode activation (every 5th iteration)
    - LLM integration

Fixtures Used:
    - None (uses mocks for LLM calls)

Target Coverage: ≥80% of TemplateParameterGenerator methods
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.generators.template_parameter_generator import (
    TemplateParameterGenerator,
    ParameterGenerationContext
)


class TestTemplateParameterGeneratorInit:
    """Test suite for __init__() method."""

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        generator = TemplateParameterGenerator()

        assert generator.template_name == "Momentum"
        assert generator.model == "gemini-2.5-flash"
        assert generator.exploration_interval == 5
        assert generator.template is not None
        assert generator.param_grid is not None

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters."""
        generator = TemplateParameterGenerator(
            template_name="Momentum",
            model="gpt-4",
            exploration_interval=10
        )

        assert generator.template_name == "Momentum"
        assert generator.model == "gpt-4"
        assert generator.exploration_interval == 10

    def test_init_loads_template(self):
        """Test __init__ successfully loads MomentumTemplate."""
        generator = TemplateParameterGenerator()

        # Verify template is MomentumTemplate instance
        from src.templates.momentum_template import MomentumTemplate
        assert isinstance(generator.template, MomentumTemplate)
        assert generator.template.name == "Momentum"

    def test_init_loads_param_grid(self):
        """Test __init__ successfully loads PARAM_GRID from template."""
        generator = TemplateParameterGenerator()

        # Verify param_grid has all 8 required parameters
        assert len(generator.param_grid) == 8
        assert 'momentum_period' in generator.param_grid
        assert 'ma_periods' in generator.param_grid
        assert 'catalyst_type' in generator.param_grid
        assert 'catalyst_lookback' in generator.param_grid
        assert 'n_stocks' in generator.param_grid
        assert 'stop_loss' in generator.param_grid
        assert 'resample' in generator.param_grid
        assert 'resample_offset' in generator.param_grid


class TestBuildPrompt:
    """Test suite for _build_prompt() method."""

    def test_build_prompt_basic_structure(self):
        """Test _build_prompt generates complete prompt with all 5 sections."""
        generator = TemplateParameterGenerator()
        context = ParameterGenerationContext(iteration_num=0)

        prompt = generator._build_prompt(context)

        # Check all 5 sections are present
        assert "# TASK: Select Parameters for Momentum Strategy" in prompt
        assert "## PARAMETER GRID" in prompt
        assert "## TRADING DOMAIN KNOWLEDGE" in prompt
        assert "## OUTPUT FORMAT" in prompt

        # Section 1: Task description
        assert "You are a quantitative trading expert" in prompt

        # Section 2: Parameter grid with all 8 parameters
        assert "momentum_period" in prompt
        assert "ma_periods" in prompt
        assert "catalyst_type" in prompt
        assert "catalyst_lookback" in prompt
        assert "n_stocks" in prompt
        assert "stop_loss" in prompt
        assert "resample" in prompt
        assert "resample_offset" in prompt

    def test_build_prompt_without_champion(self):
        """Test _build_prompt without champion context."""
        generator = TemplateParameterGenerator()
        context = ParameterGenerationContext(iteration_num=0)

        prompt = generator._build_prompt(context)

        # No champion context should be present
        assert "## CURRENT CHAMPION" not in prompt
        assert "EXPLORATION MODE" not in prompt
        assert "EXPLOITATION MODE" not in prompt

    def test_build_prompt_with_champion_exploitation(self):
        """Test _build_prompt with champion context (exploitation mode)."""
        generator = TemplateParameterGenerator()
        context = ParameterGenerationContext(
            iteration_num=1,
            champion_params={
                'momentum_period': 10,
                'ma_periods': 60,
                'catalyst_type': 'revenue',
                'catalyst_lookback': 3,
                'n_stocks': 10,
                'stop_loss': 0.10,
                'resample': 'M',
                'resample_offset': 0
            },
            champion_sharpe=1.25
        )

        prompt = generator._build_prompt(context)

        # Champion context should be present
        assert "## CURRENT CHAMPION" in prompt
        assert "Iteration: 1" in prompt
        assert "Sharpe Ratio: 1.2500" in prompt
        assert "momentum_period: 10" in prompt

        # Exploitation mode (not iteration 5, 10, 15, ...)
        assert "EXPLOITATION MODE" in prompt
        assert "Try parameters NEAR champion" in prompt
        assert "EXPLORATION MODE" not in prompt

    def test_build_prompt_with_champion_exploration(self):
        """Test _build_prompt with champion context (exploration mode)."""
        generator = TemplateParameterGenerator(exploration_interval=5)
        context = ParameterGenerationContext(
            iteration_num=5,
            champion_params={
                'momentum_period': 10,
                'ma_periods': 60,
                'catalyst_type': 'revenue',
                'catalyst_lookback': 3,
                'n_stocks': 10,
                'stop_loss': 0.10,
                'resample': 'M',
                'resample_offset': 0
            },
            champion_sharpe=1.25
        )

        prompt = generator._build_prompt(context)

        # Exploration mode (iteration 5)
        assert "EXPLORATION MODE" in prompt
        assert "Try DIFFERENT parameters" in prompt
        assert "Ignore champion, explore distant parameter space" in prompt
        assert "EXPLOITATION MODE" not in prompt

    def test_build_prompt_domain_knowledge(self):
        """Test _build_prompt includes domain knowledge section."""
        generator = TemplateParameterGenerator()
        context = ParameterGenerationContext(iteration_num=0)

        prompt = generator._build_prompt(context)

        # Check domain knowledge subsections
        assert "### Taiwan Stock Market Characteristics" in prompt
        assert "### Finlab Data Recommendations" in prompt
        assert "### Risk Management Best Practices" in prompt
        assert "### Parameter Relationships" in prompt

        # Check specific domain knowledge
        assert "liquidity filter" in prompt
        assert "10-15 stocks optimal" in prompt

    def test_build_prompt_output_format(self):
        """Test _build_prompt includes correct JSON output format."""
        generator = TemplateParameterGenerator()
        context = ParameterGenerationContext(iteration_num=0)

        prompt = generator._build_prompt(context)

        # Check output format section
        assert "## OUTPUT FORMAT" in prompt
        assert "Return ONLY valid JSON" in prompt
        assert '"momentum_period": 10' in prompt
        assert '"ma_periods": 60' in prompt


class TestParseResponse:
    """Test suite for _parse_response() method with 4 fallback strategies."""

    def test_parse_response_strategy1_direct_json(self):
        """Test _parse_response Strategy 1: Direct JSON.loads()."""
        generator = TemplateParameterGenerator()

        # Clean JSON response
        response = json.dumps({
            'momentum_period': 10,
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'resample_offset': 0
        })

        params = generator._parse_response(response)

        assert params is not None
        assert isinstance(params, dict)
        assert params['momentum_period'] == 10
        assert params['ma_periods'] == 60
        assert params['catalyst_type'] == 'revenue'

    def test_parse_response_strategy2_markdown_json(self):
        """Test _parse_response Strategy 2: Extract from ```json``` markdown block."""
        generator = TemplateParameterGenerator()

        # JSON wrapped in markdown code block
        response = """
Here are the parameters:

```json
{
    "momentum_period": 20,
    "ma_periods": 90,
    "catalyst_type": "earnings",
    "catalyst_lookback": 4,
    "n_stocks": 15,
    "stop_loss": 0.12,
    "resample": "W",
    "resample_offset": 1
}
```

These parameters should work well.
"""

        params = generator._parse_response(response)

        assert params is not None
        assert isinstance(params, dict)
        assert params['momentum_period'] == 20
        assert params['resample'] == 'W'

    def test_parse_response_strategy3_simple_braces(self):
        """Test _parse_response Strategy 3: Extract any {...} block."""
        generator = TemplateParameterGenerator()

        # JSON embedded in text without markdown
        response = """
Based on the analysis, I recommend these parameters:
{"momentum_period": 5, "ma_periods": 20, "catalyst_type": "revenue", "catalyst_lookback": 2, "n_stocks": 5, "stop_loss": 0.08, "resample": "M", "resample_offset": 0}
This should provide good returns.
"""

        params = generator._parse_response(response)

        assert params is not None
        assert isinstance(params, dict)
        assert params['momentum_period'] == 5
        assert params['n_stocks'] == 5

    def test_parse_response_strategy4_nested_braces(self):
        """Test _parse_response Strategy 4: Extract with nested braces."""
        generator = TemplateParameterGenerator()

        # Complex response with nested structures (valid JSON)
        response = """
Analysis: {"status": "ok"}
Parameters: {
    "momentum_period": 30,
    "ma_periods": 120,
    "catalyst_type": "earnings",
    "catalyst_lookback": 6,
    "n_stocks": 20,
    "stop_loss": 0.15,
    "resample": "M",
    "resample_offset": 4
}
"""

        params = generator._parse_response(response)

        assert params is not None
        assert isinstance(params, dict)
        # Strategy 4 extracts first complete JSON object
        # Could be either the Analysis object or Parameters object
        assert 'momentum_period' in params or 'status' in params

    def test_parse_response_all_strategies_fail(self):
        """Test _parse_response returns None when all strategies fail."""
        generator = TemplateParameterGenerator()

        # Invalid response with no JSON
        response = "I cannot provide parameters right now."

        params = generator._parse_response(response)

        assert params is None

    def test_parse_response_returns_dict_only(self):
        """Test _parse_response only returns dict type, not other types."""
        generator = TemplateParameterGenerator()

        # JSON array instead of object
        response = json.dumps([1, 2, 3, 4])

        params = generator._parse_response(response)

        # Should return None for non-dict results
        assert params is None

    def test_parse_response_handles_extra_whitespace(self):
        """Test _parse_response handles extra whitespace correctly."""
        generator = TemplateParameterGenerator()

        response = """


        ```json
        {
            "momentum_period": 10,
            "ma_periods": 60,
            "catalyst_type": "revenue",
            "catalyst_lookback": 3,
            "n_stocks": 10,
            "stop_loss": 0.10,
            "resample": "M",
            "resample_offset": 0
        }
        ```


        """

        params = generator._parse_response(response)

        assert params is not None
        assert isinstance(params, dict)


class TestValidateParams:
    """Test suite for _validate_params() method."""

    def test_validate_params_all_valid(self):
        """Test _validate_params with all valid parameters."""
        generator = TemplateParameterGenerator()

        params = {
            'momentum_period': 10,
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'resample_offset': 0
        }

        is_valid, errors = generator._validate_params(params)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_params_missing_required(self):
        """Test _validate_params detects missing required parameters."""
        generator = TemplateParameterGenerator()

        # Missing 'resample' and 'resample_offset'
        params = {
            'momentum_period': 10,
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10
        }

        is_valid, errors = generator._validate_params(params)

        assert is_valid is False
        assert len(errors) > 0
        assert any('Missing required parameters' in error for error in errors)

    def test_validate_params_extra_parameters(self):
        """Test _validate_params detects unknown/extra parameters."""
        generator = TemplateParameterGenerator()

        params = {
            'momentum_period': 10,
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'resample_offset': 0,
            'unknown_param': 999  # Extra parameter
        }

        is_valid, errors = generator._validate_params(params)

        assert is_valid is False
        assert len(errors) > 0
        assert any('Unknown parameters' in error for error in errors)

    def test_validate_params_wrong_type_int(self):
        """Test _validate_params detects wrong data type (int expected)."""
        generator = TemplateParameterGenerator()

        params = {
            'momentum_period': "10",  # String instead of int
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'resample_offset': 0
        }

        is_valid, errors = generator._validate_params(params)

        assert is_valid is False
        assert len(errors) > 0
        assert any('wrong type' in error for error in errors)

    def test_validate_params_wrong_type_float(self):
        """Test _validate_params detects wrong data type (float expected)."""
        generator = TemplateParameterGenerator()

        params = {
            'momentum_period': 10,
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': "0.10",  # String instead of float
            'resample': 'M',
            'resample_offset': 0
        }

        is_valid, errors = generator._validate_params(params)

        assert is_valid is False
        assert len(errors) > 0
        assert any('wrong type' in error for error in errors)

    def test_validate_params_invalid_value(self):
        """Test _validate_params detects value not in PARAM_GRID."""
        generator = TemplateParameterGenerator()

        params = {
            'momentum_period': 999,  # Not in PARAM_GRID [5, 10, 20, 30]
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'resample_offset': 0
        }

        is_valid, errors = generator._validate_params(params)

        assert is_valid is False
        assert len(errors) > 0
        assert any('not in allowed values' in error for error in errors)

    def test_validate_params_multiple_errors(self):
        """Test _validate_params detects multiple error types simultaneously."""
        generator = TemplateParameterGenerator()

        params = {
            'momentum_period': "10",  # Wrong type
            'ma_periods': 999,  # Invalid value
            'catalyst_type': 'revenue',
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'unknown_param': 123  # Extra parameter
            # Missing 'catalyst_lookback' and 'resample_offset'
        }

        is_valid, errors = generator._validate_params(params)

        assert is_valid is False
        assert len(errors) >= 3  # At least 3 different error types


class TestGenerateParameters:
    """Test suite for generate_parameters() end-to-end workflow."""

    @patch('src.generators.template_parameter_generator.TemplateParameterGenerator._call_llm_for_parameters')
    def test_generate_parameters_success(self, mock_llm):
        """Test generate_parameters() end-to-end success workflow."""
        generator = TemplateParameterGenerator()

        # Mock LLM response with valid JSON
        mock_llm.return_value = json.dumps({
            'momentum_period': 10,
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'resample_offset': 0
        })

        context = ParameterGenerationContext(iteration_num=0)
        params = generator.generate_parameters(context)

        # Verify successful generation
        assert params is not None
        assert isinstance(params, dict)
        assert len(params) == 8
        assert params['momentum_period'] == 10
        assert params['catalyst_type'] == 'revenue'

        # Verify LLM was called
        mock_llm.assert_called_once()

    @patch('src.generators.template_parameter_generator.TemplateParameterGenerator._call_llm_for_parameters')
    def test_generate_parameters_parse_failure(self, mock_llm):
        """Test generate_parameters() handles parse failure gracefully."""
        generator = TemplateParameterGenerator()

        # Mock LLM response with unparseable text
        mock_llm.return_value = "I cannot generate parameters right now."

        context = ParameterGenerationContext(iteration_num=0)

        # Should raise ValueError for parse failure
        with pytest.raises(ValueError) as exc_info:
            generator.generate_parameters(context)

        assert "Failed to parse LLM response" in str(exc_info.value)

    @patch('src.generators.template_parameter_generator.TemplateParameterGenerator._call_llm_for_parameters')
    def test_generate_parameters_validation_failure(self, mock_llm):
        """Test generate_parameters() handles validation failure gracefully."""
        generator = TemplateParameterGenerator()

        # Mock LLM response with invalid parameters
        mock_llm.return_value = json.dumps({
            'momentum_period': 999,  # Invalid value
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'resample_offset': 0
        })

        context = ParameterGenerationContext(iteration_num=0)

        # Should raise ValueError for validation failure
        with pytest.raises(ValueError) as exc_info:
            generator.generate_parameters(context)

        assert "Parameter validation failed" in str(exc_info.value)

    @patch('src.generators.template_parameter_generator.TemplateParameterGenerator._call_llm_for_parameters')
    def test_generate_parameters_llm_failure(self, mock_llm):
        """Test generate_parameters() handles LLM API failure gracefully."""
        generator = TemplateParameterGenerator()

        # Mock LLM raising RuntimeError
        mock_llm.side_effect = RuntimeError("LLM API call failed")

        context = ParameterGenerationContext(iteration_num=0)

        # Should propagate RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            generator.generate_parameters(context)

        assert "LLM API call failed" in str(exc_info.value)

    @patch('src.generators.template_parameter_generator.TemplateParameterGenerator._call_llm_for_parameters')
    def test_generate_parameters_with_champion_context(self, mock_llm):
        """Test generate_parameters() with champion context."""
        generator = TemplateParameterGenerator()

        # Mock LLM response
        mock_llm.return_value = json.dumps({
            'momentum_period': 20,  # Different from champion
            'ma_periods': 90,
            'catalyst_type': 'earnings',
            'catalyst_lookback': 4,
            'n_stocks': 15,
            'stop_loss': 0.12,
            'resample': 'W',
            'resample_offset': 1
        })

        context = ParameterGenerationContext(
            iteration_num=1,
            champion_params={
                'momentum_period': 10,
                'ma_periods': 60,
                'catalyst_type': 'revenue',
                'catalyst_lookback': 3,
                'n_stocks': 10,
                'stop_loss': 0.10,
                'resample': 'M',
                'resample_offset': 0
            },
            champion_sharpe=1.25
        )

        params = generator.generate_parameters(context)

        # Verify successful generation with champion context
        assert params is not None
        assert params['momentum_period'] == 20


class TestExplorationMode:
    """Test suite for exploration mode activation (every 5th iteration)."""

    def test_should_force_exploration_iteration_0(self):
        """Test _should_force_exploration returns False for iteration 0."""
        generator = TemplateParameterGenerator(exploration_interval=5)

        assert generator._should_force_exploration(0) is False

    def test_should_force_exploration_iteration_5(self):
        """Test _should_force_exploration returns True for iteration 5."""
        generator = TemplateParameterGenerator(exploration_interval=5)

        assert generator._should_force_exploration(5) is True

    def test_should_force_exploration_iteration_10(self):
        """Test _should_force_exploration returns True for iteration 10."""
        generator = TemplateParameterGenerator(exploration_interval=5)

        assert generator._should_force_exploration(10) is True

    def test_should_force_exploration_iteration_15(self):
        """Test _should_force_exploration returns True for iteration 15."""
        generator = TemplateParameterGenerator(exploration_interval=5)

        assert generator._should_force_exploration(15) is True

    def test_should_force_exploration_non_multiple(self):
        """Test _should_force_exploration returns False for non-multiples."""
        generator = TemplateParameterGenerator(exploration_interval=5)

        assert generator._should_force_exploration(1) is False
        assert generator._should_force_exploration(2) is False
        assert generator._should_force_exploration(3) is False
        assert generator._should_force_exploration(4) is False
        assert generator._should_force_exploration(6) is False
        assert generator._should_force_exploration(7) is False

    def test_exploration_interval_customization(self):
        """Test exploration interval can be customized."""
        generator = TemplateParameterGenerator(exploration_interval=3)

        assert generator._should_force_exploration(3) is True
        assert generator._should_force_exploration(6) is True
        assert generator._should_force_exploration(9) is True
        assert generator._should_force_exploration(5) is False

    @patch('src.generators.template_parameter_generator.TemplateParameterGenerator._call_llm_for_parameters')
    def test_exploration_mode_in_prompt(self, mock_llm):
        """Test exploration mode message appears in prompt for iteration 5."""
        generator = TemplateParameterGenerator(exploration_interval=5)

        # Mock LLM to capture the prompt
        captured_prompt = None
        def capture_prompt(prompt, iteration_num):
            nonlocal captured_prompt
            captured_prompt = prompt
            return json.dumps({
                'momentum_period': 10,
                'ma_periods': 60,
                'catalyst_type': 'revenue',
                'catalyst_lookback': 3,
                'n_stocks': 10,
                'stop_loss': 0.10,
                'resample': 'M',
                'resample_offset': 0
            })

        mock_llm.side_effect = capture_prompt

        context = ParameterGenerationContext(
            iteration_num=5,
            champion_params={
                'momentum_period': 10,
                'ma_periods': 60,
                'catalyst_type': 'revenue',
                'catalyst_lookback': 3,
                'n_stocks': 10,
                'stop_loss': 0.10,
                'resample': 'M',
                'resample_offset': 0
            },
            champion_sharpe=1.25
        )

        generator.generate_parameters(context)

        # Verify exploration mode appears in prompt
        assert captured_prompt is not None
        assert "EXPLORATION MODE" in captured_prompt
        assert "Try DIFFERENT parameters" in captured_prompt


class TestParameterGenerationContext:
    """Test suite for ParameterGenerationContext dataclass."""

    def test_context_initialization_minimal(self):
        """Test ParameterGenerationContext with minimal parameters."""
        context = ParameterGenerationContext(iteration_num=0)

        assert context.iteration_num == 0
        assert context.champion_params is None
        assert context.champion_sharpe is None
        assert context.feedback_history is None

    def test_context_initialization_full(self):
        """Test ParameterGenerationContext with all parameters."""
        context = ParameterGenerationContext(
            iteration_num=5,
            champion_params={'momentum_period': 10},
            champion_sharpe=1.25,
            feedback_history="Previous feedback"
        )

        assert context.iteration_num == 5
        assert context.champion_params == {'momentum_period': 10}
        assert context.champion_sharpe == 1.25
        assert context.feedback_history == "Previous feedback"


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_parse_response_empty_string(self):
        """Test _parse_response handles empty string."""
        generator = TemplateParameterGenerator()

        params = generator._parse_response("")

        assert params is None

    def test_parse_response_whitespace_only(self):
        """Test _parse_response handles whitespace-only string."""
        generator = TemplateParameterGenerator()

        params = generator._parse_response("   \n\n   \t\t   ")

        assert params is None

    def test_validate_params_empty_dict(self):
        """Test _validate_params handles empty dictionary."""
        generator = TemplateParameterGenerator()

        is_valid, errors = generator._validate_params({})

        assert is_valid is False
        assert len(errors) > 0
        assert any('Missing required parameters' in error for error in errors)

    @patch('src.generators.template_parameter_generator.TemplateParameterGenerator._call_llm_for_parameters')
    def test_generate_parameters_iteration_0(self, mock_llm):
        """Test generate_parameters() for iteration 0 (no champion)."""
        generator = TemplateParameterGenerator()

        mock_llm.return_value = json.dumps({
            'momentum_period': 10,
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'resample_offset': 0
        })

        context = ParameterGenerationContext(iteration_num=0)
        params = generator.generate_parameters(context)

        assert params is not None
        assert len(params) == 8

    def test_validate_params_all_parameters_at_boundaries(self):
        """Test _validate_params with all parameters at boundary values."""
        generator = TemplateParameterGenerator()

        # Test with minimum values
        params_min = {
            'momentum_period': 5,
            'ma_periods': 20,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 2,
            'n_stocks': 5,
            'stop_loss': 0.08,
            'resample': 'W',
            'resample_offset': 0
        }

        is_valid, errors = generator._validate_params(params_min)
        assert is_valid is True

        # Test with maximum values
        params_max = {
            'momentum_period': 30,
            'ma_periods': 120,
            'catalyst_type': 'earnings',
            'catalyst_lookback': 6,
            'n_stocks': 20,
            'stop_loss': 0.15,
            'resample': 'M',
            'resample_offset': 4
        }

        is_valid, errors = generator._validate_params(params_max)
        assert is_valid is True
