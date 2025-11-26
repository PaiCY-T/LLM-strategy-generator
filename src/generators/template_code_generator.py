"""
TemplateCodeGenerator - Generate strategy code from validated JSON parameters

This module implements the core JSON-to-Code generation flow:
1. Extract JSON from LLM output (handles markdown blocks)
2. Validate parameters using Pydantic schemas
3. Inject validated params into template code

Requirements: F3.1, F3.2, F3.3, AC3
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional, List, Any

from pydantic import ValidationError

from src.schemas.strategy_params import MomentumStrategyParams, StrategyParamRequest
from src.templates.base_template import BaseTemplate


@dataclass
class GenerationResult:
    """
    Result of code generation attempt.

    Attributes:
        success: True if generation succeeded, False otherwise
        code: Generated Python code string (None if failed)
        params: Validated MomentumStrategyParams (None if failed)
        errors: List of error messages if generation failed
    """
    success: bool
    code: Optional[str] = None
    params: Optional[MomentumStrategyParams] = None
    errors: List[str] = field(default_factory=list)

    def get_feedback_prompt(self) -> str:
        """
        Generate LLM-friendly error feedback for retry.

        Returns:
            str: Formatted error feedback suitable for LLM retry prompt
        """
        if not self.errors:
            return ""

        feedback_lines = [
            "## VALIDATION ERRORS (Please Fix)\n"
        ]

        for i, error in enumerate(self.errors, 1):
            feedback_lines.append(f"{i}. {error}\n")

        feedback_lines.append("\nPlease output corrected JSON with valid values.")

        return "\n".join(feedback_lines)


class TemplateCodeGenerator:
    """
    Generates strategy code from validated JSON parameters.

    This class implements the core JSON-to-Code conversion flow:
    1. Extract JSON from LLM output (handles markdown code blocks)
    2. Validate parameters using Pydantic schemas
    3. Inject validated params into MomentumTemplate code generation

    Attributes:
        template: The strategy template to use for code generation
    """

    def __init__(self, template: BaseTemplate):
        """
        Initialize with strategy template.

        Args:
            template: Strategy template instance (e.g., MomentumTemplate)
        """
        self.template = template

    def generate(self, llm_output: str) -> GenerationResult:
        """
        Parse LLM output, validate parameters, generate code.

        This is the main entry point that orchestrates the entire flow:
        1. Extract JSON from raw LLM output
        2. Validate extracted JSON against Pydantic schema
        3. Inject validated params into template code generation

        Args:
            llm_output: Raw LLM response (may contain markdown)

        Returns:
            GenerationResult with either code or structured errors
        """
        try:
            # Step 1: Extract JSON from LLM output
            json_str = self._extract_json(llm_output)

            # Step 2: Validate against Pydantic schema
            request = self._validate_params(json_str)

            # Step 3: Generate code using template
            code = self._inject_params(request.params)

            return GenerationResult(
                success=True,
                code=code,
                params=request.params,
                errors=[]
            )

        except ValueError as e:
            # JSON extraction error
            return GenerationResult(
                success=False,
                code=None,
                params=None,
                errors=[f"JSON extraction error: {str(e)}"]
            )

        except ValidationError as e:
            # Pydantic validation error
            errors = self._format_validation_errors(e)
            return GenerationResult(
                success=False,
                code=None,
                params=None,
                errors=errors
            )

        except Exception as e:
            # Unexpected error
            return GenerationResult(
                success=False,
                code=None,
                params=None,
                errors=[f"Unexpected error: {str(e)}"]
            )

    def _extract_json(self, raw_output: str) -> str:
        """
        Extract JSON from LLM output (handles markdown blocks).

        Handles multiple formats:
        - Plain JSON string
        - ```json ... ``` markdown blocks
        - ``` ... ``` markdown blocks (no language)
        - JSON with surrounding text

        Args:
            raw_output: Raw LLM response string

        Returns:
            str: Clean JSON string

        Raises:
            ValueError: If no valid JSON can be extracted
        """
        # First, try to extract from markdown code blocks
        # Pattern for ```json ... ``` or ``` ... ```
        code_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
        matches = re.findall(code_block_pattern, raw_output)

        if matches:
            # Try to parse each match as JSON
            for match in matches:
                try:
                    json.loads(match.strip())
                    return match.strip()
                except json.JSONDecodeError:
                    continue

        # No code blocks or none contained valid JSON
        # Try to find JSON object in the raw text
        # Look for { ... } pattern
        json_pattern = r'\{[\s\S]*\}'
        json_matches = re.findall(json_pattern, raw_output)

        for match in json_matches:
            try:
                json.loads(match)
                return match
            except json.JSONDecodeError:
                continue

        # If the entire string is valid JSON, return it
        try:
            json.loads(raw_output.strip())
            return raw_output.strip()
        except json.JSONDecodeError:
            pass

        raise ValueError(
            "No valid JSON found in LLM output. "
            "Expected JSON object with 'reasoning' and 'params' fields."
        )

    def _validate_params(self, json_str: str) -> StrategyParamRequest:
        """
        Validate JSON against Pydantic schema.

        Args:
            json_str: JSON string to validate

        Returns:
            StrategyParamRequest: Validated request object

        Raises:
            ValidationError: If validation fails
        """
        data = json.loads(json_str)
        return StrategyParamRequest(**data)

    def _inject_params(self, params: MomentumStrategyParams) -> str:
        """
        Inject validated params into template code.

        Generates Python code string that creates a strategy with the
        given parameters by calling the template's internal methods.

        Args:
            params: Validated MomentumStrategyParams object

        Returns:
            str: Generated Python code string
        """
        # Convert Pydantic model to dict for template
        params_dict = params.model_dump()

        # Generate strategy code using the template's parameter format
        code = self._generate_strategy_code(params_dict)

        return code

    def _generate_strategy_code(self, params: dict) -> str:
        """
        Generate Python code string for the strategy.

        Args:
            params: Dictionary of strategy parameters

        Returns:
            str: Python code that implements the strategy
        """
        # Use the template name for the strategy class name
        template_name = self.template.name

        code = f'''"""
{template_name} Strategy - Generated Code
Parameters:
  momentum_period: {params['momentum_period']}
  ma_periods: {params['ma_periods']}
  catalyst_type: {params['catalyst_type']}
  catalyst_lookback: {params['catalyst_lookback']}
  n_stocks: {params['n_stocks']}
  stop_loss: {params['stop_loss']}
  resample: {params['resample']}
  resample_offset: {params['resample_offset']}
"""

# Strategy parameters
PARAMS = {{
    'momentum_period': {params['momentum_period']},
    'ma_periods': {params['ma_periods']},
    'catalyst_type': '{params['catalyst_type']}',
    'catalyst_lookback': {params['catalyst_lookback']},
    'n_stocks': {params['n_stocks']},
    'stop_loss': {params['stop_loss']},
    'resample': '{params['resample']}',
    'resample_offset': {params['resample_offset']}
}}


def create_strategy():
    """Create and return the {template_name} strategy."""
    from src.templates.momentum_template import MomentumTemplate

    template = MomentumTemplate()
    report, metrics = template.generate_strategy(PARAMS)
    return report, metrics


if __name__ == "__main__":
    report, metrics = create_strategy()
    print(f"Annual Return: {{metrics['annual_return']:.2%}}")
    print(f"Sharpe Ratio: {{metrics['sharpe_ratio']:.2f}}")
    print(f"Max Drawdown: {{metrics['max_drawdown']:.2%}}")
'''
        return code

    def _format_validation_errors(self, error: ValidationError) -> List[str]:
        """
        Format Pydantic validation errors into LLM-friendly messages.

        Args:
            error: Pydantic ValidationError

        Returns:
            List[str]: Formatted error messages
        """
        errors = []
        for err in error.errors():
            field_path = ".".join(str(loc) for loc in err['loc'])
            error_type = err['type']
            msg = err['msg']

            # Build friendly error message
            error_msg = f"**{field_path}**: {msg}"

            # Add context for specific error types
            if error_type == 'literal_error':
                # Get the expected values from the message if available
                error_msg = f"**{field_path}**: Invalid value - {msg}"
            elif error_type == 'missing':
                error_msg = f"**{field_path}**: Missing required field"
            elif error_type == 'string_too_short':
                error_msg = f"**{field_path}**: {msg}"
            elif error_type == 'string_too_long':
                error_msg = f"**{field_path}**: {msg}"

            errors.append(error_msg)

        return errors
