"""
Template Parameter Generator Module

This module provides functionality for generating optimal parameter combinations
for template-based trading strategies. It bridges templates with parameter
exploration, enabling systematic testing and optimization of strategy parameters.

Key Features:
- Template-aware parameter generation
- Integration with template metadata and constraints
- Support for various parameter types (numerical, categorical, conditional)
- Efficient parameter space exploration strategies
- Validation against template requirements

Classes:
    TemplateParameterGenerator: Main class for generating template parameters
    ParameterGenerationContext: Context for parameter generation

Usage:
    from src.generators import TemplateParameterGenerator, ParameterGenerationContext

    generator = TemplateParameterGenerator(template)
    context = ParameterGenerationContext(
        iteration_num=0,
        champion_params=None,
        champion_sharpe=None
    )
    parameters = generator.generate_parameters(context)
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging
import os

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ParameterGenerationContext:
    """Context for parameter generation."""
    iteration_num: int
    champion_params: Optional[Dict[str, Any]] = None
    champion_sharpe: Optional[float] = None
    feedback_history: Optional[str] = None


class TemplateParameterGenerator:
    """
    Generate optimal parameter combinations for template-based strategies.

    This class is responsible for creating parameter sets that are compatible
    with a given strategy template, respecting template constraints and
    exploring the parameter space efficiently.

    Attributes:
        template: The strategy template to generate parameters for

    Methods:
        generate_parameters: Generate a parameter combination
    """

    def __init__(self, template_name="Momentum", model="gemini-2.5-flash", exploration_interval=5):
        """
        Initialize the TemplateParameterGenerator.

        Args:
            template_name (str): Name of the template to use. Default: "Momentum"
            model (str): AI model to use for parameter generation. Default: "gemini-2.5-flash"
            exploration_interval (int): Interval for exploration vs exploitation. Default: 5
        """
        self.template_name = template_name
        self.model = model
        self.exploration_interval = exploration_interval
        from src.templates.momentum_template import MomentumTemplate
        self.template = MomentumTemplate()
        self.param_grid = self.template.PARAM_GRID

    def _build_prompt(self, context):
        """
        Build prompt for parameter selection.

        This method constructs a comprehensive prompt for LLM parameter generation,
        including task description, parameter grid with explanations, champion context,
        domain knowledge, and output format specification.

        Args:
            context: ParameterGenerationContext with champion info and feedback

        Returns:
            str: Formatted prompt string ready for LLM

        Prompt Structure (5 sections):
            1. Task description - Explains parameter selection goal
            2. PARAM_GRID - Shows all 8 parameters with value explanations
            3. Champion context - Current best strategy (if exists, with exploration mode)
            4. Domain knowledge - Trading best practices and Taiwan market specifics
            5. Output format - JSON structure specification with example
        """
        sections = []

        # Section 1: Task Description
        sections.append("# TASK: Select Parameters for Momentum Strategy")
        sections.append("")
        sections.append("You are a quantitative trading expert selecting parameters")
        sections.append("for a momentum + catalyst strategy on Taiwan stock market.")
        sections.append("")

        # Section 2: PARAM_GRID with explanations
        sections.append("## PARAMETER GRID")
        sections.append("Select ONE value for each parameter:")
        sections.append("")

        # Parameter explanations matching design.md structure
        grid_explanations = {
            'momentum_period': [
                "5 days: Very short-term momentum (1 week)",
                "10 days: Short-term momentum (2 weeks)",
                "20 days: Medium-term momentum (1 month)",
                "30 days: Longer-term momentum (1.5 months)"
            ],
            'ma_periods': [
                "20 days: Short-term trend (1 month)",
                "60 days: Medium-term trend (3 months)",
                "90 days: Long-term trend (4.5 months)",
                "120 days: Very long-term trend (6 months)"
            ],
            'catalyst_type': [
                "'revenue': Revenue acceleration (short-term > long-term MA)",
                "'earnings': Earnings momentum (ROE improvement)"
            ],
            'catalyst_lookback': [
                "2 months: Very recent catalyst",
                "3 months: Recent catalyst",
                "4 months: Short-term catalyst",
                "6 months: Medium-term catalyst"
            ],
            'n_stocks': [
                "5: Highly concentrated (top momentum plays)",
                "10: Concentrated portfolio",
                "15: Balanced diversification",
                "20: Diversified momentum portfolio"
            ],
            'stop_loss': [
                "0.08: Tight stop (8% loss limit)",
                "0.10: Moderate stop (10% loss limit)",
                "0.12: Moderate-loose stop (12% loss limit)",
                "0.15: Loose stop (15% loss limit)"
            ],
            'resample': [
                "'W': Weekly rebalancing (higher turnover, faster reaction)",
                "'M': Monthly rebalancing (lower turnover, reduced costs)"
            ],
            'resample_offset': [
                "0: Monday/1st of month",
                "1: Tuesday/offset 1 day",
                "2: Wednesday/offset 2 days",
                "3: Thursday/offset 3 days",
                "4: Friday/offset 4 days"
            ]
        }

        # Format each parameter with its options and explanations
        for param, values in self.param_grid.items():
            sections.append(f"### {param}: {values}")
            for explanation in grid_explanations[param]:
                sections.append(f"  - {explanation}")
            sections.append("")

        # Section 3: Champion Context
        if context.champion_params:
            sections.append("## CURRENT CHAMPION")
            sections.append(f"Iteration: {context.iteration_num}")
            sections.append(f"Sharpe Ratio: {context.champion_sharpe:.4f}")
            sections.append("")
            sections.append("Parameters:")
            for key, value in context.champion_params.items():
                sections.append(f"  - {key}: {value}")
            sections.append("")

            # Exploration vs Exploitation
            if self._should_force_exploration(context.iteration_num):
                sections.append("⚠️  EXPLORATION MODE: Try DIFFERENT parameters")
                sections.append("    Ignore champion, explore distant parameter space")
            else:
                sections.append("💡 EXPLOITATION MODE: Try parameters NEAR champion")
                sections.append("    Adjust 1-2 parameters by ±1 step from champion")
            sections.append("")

        # Section 4: Domain Knowledge
        sections.append("## TRADING DOMAIN KNOWLEDGE")
        sections.append("")

        sections.append("### Taiwan Stock Market Characteristics")
        sections.append("- T+2 settlement, 10% daily price limit")
        sections.append("- High retail participation, momentum effects strong")
        sections.append("- Market cap concentration in tech/finance sectors")
        sections.append("")

        sections.append("### Finlab Data Recommendations")
        sections.append("- ALWAYS include liquidity filter (trading_value > 50M-100M TWD)")
        sections.append("- Smooth fundamentals with .rolling().mean() to reduce noise")
        sections.append("- Use .shift(1) to avoid look-ahead bias")
        sections.append("- Revenue catalyst works well with shorter momentum windows")
        sections.append("- Earnings (ROE) catalyst better for longer-term strategies")
        sections.append("")

        sections.append("### Risk Management Best Practices")
        sections.append("- Portfolio: 10-15 stocks optimal (balance concentration vs diversification)")
        sections.append("- Stop loss: 10-12% recommended for momentum strategies")
        sections.append("- Rebalancing: Weekly for aggressive, Monthly for conservative")
        sections.append("- Avoid over-diversification (>20 stocks reduces alpha)")
        sections.append("")

        sections.append("### Parameter Relationships")
        sections.append("- Short momentum (5-10 days) → use shorter MA (20-60 days)")
        sections.append("- Long momentum (20-30 days) → use longer MA (60-120 days)")
        sections.append("- Weekly rebalancing → prefer shorter momentum windows")
        sections.append("- Monthly rebalancing → can use longer momentum windows")
        sections.append("- Tight stop loss (8%) → use smaller position size (10-12 stocks)")
        sections.append("- Loose stop loss (15%) → can use larger positions (15-20 stocks)")
        sections.append("")

        # Section 5: Output Format
        sections.append("## OUTPUT FORMAT")
        sections.append("Return ONLY valid JSON (no explanations):")
        sections.append("{")
        sections.append('  "momentum_period": 10,')
        sections.append('  "ma_periods": 60,')
        sections.append('  "catalyst_type": "revenue",')
        sections.append('  "catalyst_lookback": 3,')
        sections.append('  "n_stocks": 10,')
        sections.append('  "stop_loss": 0.10,')
        sections.append('  "resample": "M",')
        sections.append('  "resample_offset": 0')
        sections.append("}")

        # Return complete prompt (all 5 sections assembled)
        return "\n".join(sections)

    def _should_force_exploration(self, iteration_num):
        """
        Force exploration every N iterations.

        Args:
            iteration_num (int): Current iteration number

        Returns:
            bool: True if exploration should be forced, False otherwise
        """
        return (iteration_num > 0 and
                iteration_num % self.exploration_interval == 0)

    def _sanitize_parsed_dict(self, parsed):
        """
        Sanitize parsed dictionary to prevent security issues.

        This method validates that the parsed LLM response is safe to use,
        preventing common JSON-based attacks including:
        - Nested objects/arrays (DoS via deep nesting, memory exhaustion)
        - Excessive keys (DoS attack)
        - Prototype pollution attempts (__proto__, constructor, prototype)

        Args:
            parsed (dict): Parsed dictionary from LLM response

        Returns:
            dict or None: Sanitized dictionary if safe, None if unsafe

        Security Checks:
            1. Type validation: Must be flat dict
            2. Key limit: Max 20 keys (8 expected parameters + margin)
            3. No nested structures: All values must be primitives
            4. No dangerous keys: Reject __proto__, constructor, prototype
        """
        # Check 1: Must be dict
        if not isinstance(parsed, dict):
            logger.warning("Sanitization failed: parsed result is not a dict")
            return None

        # Check 2: Limit number of keys (DoS prevention)
        # Expected: 8 parameters, allow up to 20 as safety margin
        if len(parsed) > 20:
            logger.warning(
                f"Sanitization failed: Too many keys ({len(parsed)} > 20). "
                f"Possible DoS attempt."
            )
            return None

        # Check 3: Reject nested structures (all values must be primitives)
        # Allowed types: int, float, str, bool, None
        # Rejected types: dict, list, tuple, set
        for key, value in parsed.items():
            if isinstance(value, (dict, list, tuple, set)):
                logger.warning(
                    f"Sanitization failed: Key '{key}' has nested structure "
                    f"(type={type(value).__name__}). Rejecting to prevent "
                    f"deep nesting DoS or memory exhaustion."
                )
                return None

        # Check 4: Reject dangerous keys (prototype pollution prevention)
        dangerous_keys = {'__proto__', 'constructor', 'prototype'}
        found_dangerous = dangerous_keys.intersection(parsed.keys())
        if found_dangerous:
            logger.warning(
                f"Sanitization failed: Dangerous keys detected: {found_dangerous}. "
                f"Possible prototype pollution attempt."
            )
            return None

        # All checks passed
        return parsed

    def _parse_response(self, response_text):
        """
        Parse LLM response with 4-tier fallback strategy and security validation.

        This method implements a robust JSON extraction pipeline with multiple
        fallback strategies to handle various LLM response formats. It attempts
        increasingly aggressive extraction techniques until valid JSON is found,
        then validates the result for security issues.

        Args:
            response_text (str): Raw text response from LLM

        Returns:
            dict or None: Parsed and sanitized parameter dictionary, or None if
                         parsing fails, non-dict result, or security validation fails

        Strategy Tiers:
            1. Direct JSON.loads() - Cleanest response
            2. Extract from ```json``` markdown block
            3. Extract any {...} block
            4. Extract with nested braces (first complete JSON object)

        Security Validation:
            - Sanitizes parsed result to prevent nested objects, DoS, prototype pollution
            - See _sanitize_parsed_dict() for details

        Validation:
            - Returns dict type only
            - Rejects nested structures (lists, dicts)
            - Limits key count to 20 (DoS prevention)
            - None if parsing fails or security checks fail
        """
        import json
        import re

        # Strategy 1: Direct JSON.loads()
        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, dict):
                # Security validation before returning
                return self._sanitize_parsed_dict(parsed)
        except (json.JSONDecodeError, ValueError):
            pass

        # Strategy 2: Extract from markdown ```json``` block
        try:
            markdown_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            match = re.search(markdown_pattern, response_text, re.DOTALL)
            if match:
                parsed = json.loads(match.group(1))
                if isinstance(parsed, dict):
                    # Security validation before returning
                    return self._sanitize_parsed_dict(parsed)
        except (json.JSONDecodeError, ValueError, AttributeError):
            pass

        # Strategy 3: Extract any {...} block
        try:
            simple_pattern = r'\{[^{}]*\}'
            match = re.search(simple_pattern, response_text, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    # Security validation before returning
                    return self._sanitize_parsed_dict(parsed)
        except (json.JSONDecodeError, ValueError, AttributeError):
            pass

        # Strategy 4: Extract with nested braces (first complete JSON object)
        try:
            # Find first { and match until balanced closing }
            start_idx = response_text.find('{')
            if start_idx == -1:
                return None

            brace_count = 0
            end_idx = start_idx

            for i in range(start_idx, len(response_text)):
                if response_text[i] == '{':
                    brace_count += 1
                elif response_text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break

            if brace_count == 0 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                parsed = json.loads(json_text)
                if isinstance(parsed, dict):
                    # Security validation before returning
                    return self._sanitize_parsed_dict(parsed)
        except (json.JSONDecodeError, ValueError, IndexError):
            pass

        # All strategies failed
        return None

    def _validate_params(self, params):
        """
        Validate parsed parameters against PARAM_GRID.

        This method performs comprehensive validation of parameter dictionaries
        returned by LLM parsing. It checks for completeness, validity of values,
        and correct data types.

        Args:
            params (dict): Parameter dictionary to validate

        Returns:
            tuple: (is_valid: bool, errors: List[str])
                - is_valid: True if all validations pass, False otherwise
                - errors: List of validation error messages (empty if valid)

        Validation Checks:
            1. All required parameters present (8 parameters from PARAM_GRID)
            2. No extra parameters beyond PARAM_GRID
            3. Each parameter value exists in PARAM_GRID
            4. Data types correct (int, float, str)

        Example:
            >>> generator = TemplateParameterGenerator()
            >>> params = {'momentum_period': 10, 'ma_periods': 60, ...}
            >>> is_valid, errors = generator._validate_params(params)
            >>> if not is_valid:
            ...     print("Validation errors:", errors)
        """
        errors = []

        # Check 1: All required parameters present
        required_params = set(self.param_grid.keys())
        provided_params = set(params.keys())
        missing_params = required_params - provided_params

        if missing_params:
            errors.append(f"Missing required parameters: {sorted(missing_params)}")

        # Check 2: No extra parameters
        extra_params = provided_params - required_params
        if extra_params:
            errors.append(f"Unknown parameters: {sorted(extra_params)}")

        # Check 3 & 4: Validate each parameter value against PARAM_GRID
        for param_name, param_value in params.items():
            # Skip validation for unknown parameters (already reported)
            if param_name not in self.param_grid:
                continue

            allowed_values = self.param_grid[param_name]

            # Type checking: compare to type of first allowed value
            if allowed_values:
                expected_type = type(allowed_values[0])
                if not isinstance(param_value, expected_type):
                    errors.append(
                        f"Parameter '{param_name}' has wrong type: "
                        f"expected {expected_type.__name__}, got {type(param_value).__name__}"
                    )
                    continue  # Skip range check if type is wrong

            # Range validation: value must be in PARAM_GRID list
            if param_value not in allowed_values:
                errors.append(
                    f"Parameter '{param_name}' value {param_value} not in allowed values: {allowed_values}"
                )

        # Return validation result
        is_valid = len(errors) == 0
        return is_valid, errors

    def _call_llm_for_parameters(self, prompt, iteration_num=0):
        """
        Call LLM directly to generate parameter selection (bypassing code generation).

        This method calls the LLM API directly with only the parameter selection
        prompt, avoiding conflicts with strategy code generation templates.
        It uses dynamic temperature control for exploration vs exploitation.

        Args:
            prompt (str): Formatted prompt for parameter selection
            iteration_num (int): Current iteration number (for exploration control)

        Returns:
            str: LLM response text containing JSON parameter selection

        Raises:
            RuntimeError: If LLM API call fails after retries
        """
        # Temperature control for exploration vs exploitation
        # Higher temperature = more exploration
        # Lower temperature = more exploitation (closer to champion)
        is_exploration = self._should_force_exploration(iteration_num)
        temperature = 1.0 if is_exploration else 0.7

        logger.info(f"Calling LLM for parameters (iteration={iteration_num}, "
                   f"exploration={is_exploration}, temperature={temperature})")

        # Try Google AI first, fallback to OpenRouter
        try:
            print("🎯 Attempting Google AI (primary)...")
            return self._call_google_ai(prompt, temperature)
        except Exception as e:
            print(f"⚠️ Google AI failed: {e}")
            print("🔄 Falling back to OpenRouter...")
            try:
                return self._call_openrouter(prompt, temperature)
            except Exception as e2:
                print(f"❌ OpenRouter fallback also failed: {e2}")
                raise RuntimeError(f"Both APIs failed. Google AI: {e}, OpenRouter: {e2}")

    def _call_google_ai(self, prompt, temperature):
        """Call Google AI API directly with parameter selection prompt."""
        import google.generativeai as genai

        # Load API key
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        # Configure Google AI
        genai.configure(api_key=api_key)

        # Create model instance (extract model name if it has google/ prefix)
        model_name = self.model.split('/')[-1] if '/' in self.model else self.model
        gemini_model = genai.GenerativeModel(model_name)

        # Generate response
        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=1024  # Parameters are small, don't need 4K
            )
        )

        return response.text

    def _call_openrouter(self, prompt, temperature):
        """Call OpenRouter API directly with parameter selection prompt."""
        import requests

        # Load API key
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

        # Convert model to OpenRouter format if needed
        openrouter_model = f"google/{self.model}" if '/' not in self.model else self.model

        # Call OpenRouter API
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            timeout=60,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": openrouter_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": 1024  # Parameters are small, don't need 4K
            }
        )

        response.raise_for_status()
        result = response.json()

        return result['choices'][0]['message']['content']

    def generate_parameters(self, context):
        """
        Generate a parameter combination for the template.

        This is the main orchestration method that coordinates the full parameter
        generation workflow. It builds the prompt, calls the LLM, parses the response,
        validates the parameters, and returns the final parameter dictionary.

        Args:
            context (ParameterGenerationContext): Generation context with champion
                info and feedback. Contains:
                - iteration_num: Current iteration number
                - champion_params: Current best parameters (if exists)
                - champion_sharpe: Sharpe ratio of champion (if exists)
                - feedback_history: Historical feedback (optional)

        Returns:
            dict: Generated parameter combination with 8 keys matching PARAM_GRID:
                - momentum_period: int (5, 10, 20, or 30)
                - ma_periods: int (20, 60, 90, or 120)
                - catalyst_type: str ('revenue' or 'earnings')
                - catalyst_lookback: int (2, 3, 4, or 6)
                - n_stocks: int (5, 10, 15, or 20)
                - stop_loss: float (0.08, 0.10, 0.12, or 0.15)
                - resample: str ('W' or 'M')
                - resample_offset: int (0, 1, 2, 3, or 4)

        Raises:
            ValueError: If LLM response cannot be parsed or validation fails
            RuntimeError: If LLM API call fails

        Example:
            >>> generator = TemplateParameterGenerator()
            >>> context = ParameterGenerationContext(iteration_num=0)
            >>> params = generator.generate_parameters(context)
            >>> print(params)
            {'momentum_period': 10, 'ma_periods': 60, ...}
        """
        logger.info(f"Starting parameter generation for iteration {context.iteration_num}")

        try:
            # Step 1: Build prompt using context
            logger.debug("Building prompt from context")
            prompt = self._build_prompt(context)
            logger.debug(f"Prompt built: {len(prompt)} characters")

            # Step 2: Call LLM with prompt
            logger.debug("Calling LLM for parameter selection")
            response = self._call_llm_for_parameters(prompt, context.iteration_num)
            logger.debug(f"LLM response received: {len(response)} characters")

            # Step 3: Parse response to extract parameters
            logger.debug("Parsing LLM response")
            params = self._parse_response(response)

            if params is None:
                error_msg = (
                    f"Failed to parse LLM response. Response preview: "
                    f"{response[:200]}..."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.debug(f"Parsed parameters: {params}")

            # Step 4: Validate parsed parameters
            logger.debug("Validating parsed parameters")
            is_valid, errors = self._validate_params(params)

            if not is_valid:
                error_msg = (
                    f"Parameter validation failed. Errors: {errors}. "
                    f"Parameters: {params}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Step 5: Return validated parameters
            logger.info(f"Successfully generated parameters: {params}")
            return params

        except ValueError as e:
            # Re-raise ValueError with context
            logger.error(f"Parameter generation failed with ValueError: {e}")
            raise

        except RuntimeError as e:
            # Re-raise RuntimeError with context
            logger.error(f"Parameter generation failed with RuntimeError: {e}")
            raise

        except Exception as e:
            # Catch any unexpected errors and wrap in RuntimeError
            error_msg = f"Unexpected error during parameter generation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
