"""
JsonPromptBuilder - Build JSON-only prompts for LLM strategy parameter generation

This module creates prompts that guide LLMs to output structured JSON
parameters instead of full code generation.

Requirements: F2.1, F2.2, F2.3, F2.4, AC2
"""

import json
from typing import List

from src.schemas.param_constants import get_param_constraints


class JsonPromptBuilder:
    """
    Builds JSON-only prompts for LLM strategy parameter generation.

    This class creates prompts that include:
    - JSON Schema description
    - Parameter constraints (Literal types)
    - Few-shot examples
    - Cross-parameter validation rules
    """

    # Parameter constraints from centralized source (DRY)
    PARAM_CONSTRAINTS = get_param_constraints()

    def build_prompt(
        self,
        template_name: str,
        performance_context: str = "",
        feedback_context: str = ""
    ) -> str:
        """
        Build a JSON-only prompt for LLM parameter generation.

        Args:
            template_name: Name of the strategy template
            performance_context: Performance-related context (market conditions, etc.)
            feedback_context: Error feedback from previous attempts

        Returns:
            str: Complete prompt for LLM
        """
        schema_description = self.get_json_schema_description()
        examples = self.get_few_shot_examples()
        examples_text = "\n\n".join([
            f"Example {i+1}:\n```json\n{ex}\n```"
            for i, ex in enumerate(examples)
        ])

        prompt = f"""You are a quantitative trading strategy parameter optimizer.

## Task
Generate parameters for the {template_name} strategy. You must output ONLY JSON, no other text.

## Output Format
Return JSON only with this exact structure:
{schema_description}

## Parameter Constraints
Each parameter must use EXACTLY one of the allowed values:

{self._format_parameter_constraints()}

## Validation Rules
- `reasoning`: Must be between 50 and 500 characters
- `momentum_period` should be less than or equal to `ma_periods` for proper trend confirmation
  (momentum calculation window should not exceed trend confirmation window)

## Few-Shot Examples

{examples_text}

## Important Instructions
1. Output JSON only - no explanations before or after
2. Use ONLY the allowed values listed above
3. Ensure momentum_period <= ma_periods
4. Provide reasoning of 50-500 characters explaining your parameter choices
"""

        # Add performance context if provided
        if performance_context:
            prompt += f"""
## Performance Context
Consider the following market/performance context:
{performance_context}
"""

        # Add feedback context if provided (for retries)
        if feedback_context:
            prompt += f"""
## Previous Errors to Fix
{feedback_context}
"""

        prompt += """
## Your Response
Respond with JSON only:
"""

        return prompt

    def get_json_schema_description(self) -> str:
        """
        Get a human-readable JSON Schema description.

        Returns:
            str: Schema description for the prompt
        """
        schema = """{
  "reasoning": "string (50-500 characters explaining parameter choices)",
  "params": {
    "momentum_period": int (5, 10, 20, or 30),
    "ma_periods": int (20, 60, 90, or 120),
    "catalyst_type": string ("revenue" or "earnings"),
    "catalyst_lookback": int (2, 3, 4, or 6),
    "n_stocks": int (5, 10, 15, or 20),
    "stop_loss": float (0.08, 0.10, 0.12, or 0.15),
    "resample": string ("W" or "M"),
    "resample_offset": int (0, 1, 2, 3, or 4)
  }
}"""
        return schema

    def get_few_shot_examples(self) -> List[str]:
        """
        Get few-shot examples for the prompt.

        Returns:
            List[str]: List of valid JSON example strings
        """
        example1 = {
            "reasoning": "For a trending market, I choose a 20-day momentum period with 60-day MA confirmation. Revenue catalyst is more reliable in Taiwan stocks. 15 stocks balance diversification and concentration. 10% stop loss is moderate for momentum strategies.",
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

        example2 = {
            "reasoning": "For volatile markets, I use shorter 10-day momentum to capture quick moves, with longer 90-day MA to filter noise. Earnings catalyst captures quarterly surprises. Concentrated 10-stock portfolio with tight 8% stops for risk control.",
            "params": {
                "momentum_period": 10,
                "ma_periods": 90,
                "catalyst_type": "earnings",
                "catalyst_lookback": 4,
                "n_stocks": 10,
                "stop_loss": 0.08,
                "resample": "M",
                "resample_offset": 2
            }
        }

        return [
            json.dumps(example1, indent=2),
            json.dumps(example2, indent=2)
        ]

    def _format_parameter_constraints(self) -> str:
        """
        Format parameter constraints for the prompt.

        Returns:
            str: Formatted parameter constraints
        """
        lines = []
        for param_name, constraint in self.PARAM_CONSTRAINTS.items():
            allowed = constraint["allowed"]
            desc = constraint["description"]
            lines.append(f"- `{param_name}`: {allowed}")
            lines.append(f"  Description: {desc}")

        return "\n".join(lines)
