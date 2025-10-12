"""Claude API client for strategy generation via OpenRouter.

Handles API calls to Claude models through OpenRouter API with robust
error handling, retry logic, and response extraction.
"""

import os
import json
import time
import re
from typing import Optional
from pathlib import Path
import logging

# OpenAI library for OpenRouter API compatibility
try:
    from openai import OpenAI
except ImportError:
    raise ImportError(
        "OpenAI library required. Install with: pip install openai"
    )


logger = logging.getLogger(__name__)


class ClaudeAPIClient:
    """Client for calling Claude API via OpenRouter."""

    # API Configuration
    DEFAULT_MODEL = "anthropic/claude-sonnet-4"
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 8000
    DEFAULT_TIMEOUT = 120  # seconds

    # Retry Configuration
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 2.0  # seconds
    MAX_BACKOFF = 60.0  # seconds

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ):
        """Initialize Claude API client.

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            model: Model to use (default: anthropic/claude-sonnet-4)
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum tokens in response

        Raises:
            ValueError: If API key is not provided or found in environment
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY environment "
                "variable or pass api_key parameter."
            )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize OpenAI client with OpenRouter base URL
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        logger.info(f"Initialized Claude API client: model={model}, temp={temperature}")

    def generate_strategy_with_claude(
        self,
        iteration: int,
        feedback: str = "",
        model: Optional[str] = None
    ) -> str:
        """Call Claude API to generate strategy code.

        Loads prompt template, injects iteration context and feedback,
        calls Claude API, and extracts clean Python code from response.

        Args:
            iteration: Current iteration number
            feedback: Feedback from previous iteration (optional)
            model: Override default model (optional)

        Returns:
            Clean Python code string for trading strategy

        Raises:
            FileNotFoundError: If prompt template or datasets file not found
            RuntimeError: If API call fails after all retries
            ValueError: If response format is invalid
        """
        logger.info(f"Generating strategy for iteration {iteration}")

        # Build complete prompt
        prompt = self._build_prompt(iteration, feedback)

        # Call API with retry logic
        model_to_use = model or self.model
        response_text = self._call_api_with_retry(prompt, model_to_use)

        # Extract code from response
        code = self._extract_code(response_text)

        logger.info(f"Successfully generated strategy code ({len(code)} chars)")
        return code

    def _build_prompt(self, iteration: int, feedback: str) -> str:
        """Build complete prompt with template, iteration, and feedback.

        Args:
            iteration: Current iteration number
            feedback: Feedback from previous iteration

        Returns:
            Complete prompt string

        Raises:
            FileNotFoundError: If template or datasets file not found
        """
        # Load prompt template (v2 with dataset hallucination prevention)
        template_path = Path("prompt_template_v2_with_datasets.txt")
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Load dataset list
        datasets_path = Path("config/datasets_curated_50.json")
        if not datasets_path.exists():
            raise FileNotFoundError(f"Datasets file not found: {datasets_path}")

        with open(datasets_path, 'r', encoding='utf-8') as f:
            datasets_data = json.load(f)

        # Build dataset list text (already included in template v1)
        # Template v1 already has datasets embedded, so we just use it as-is

        # Build iteration context
        context = f"\n\n## ITERATION {iteration}\n\n"

        if iteration == 0:
            context += "This is the first iteration. Generate an innovative trading strategy.\n"
        else:
            context += f"This is iteration {iteration}. Based on feedback below, create an improved strategy.\n"

        # Add feedback if provided
        if feedback:
            context += f"\n## FEEDBACK FROM ITERATION {iteration - 1}\n\n"
            context += feedback + "\n"
            context += "\n**Your task**: Learn from the feedback above and generate a BETTER strategy.\n"
            context += "- Fix any errors mentioned\n"
            context += "- Improve upon weaknesses identified\n"
            context += "- Try different factor combinations or approaches\n"

        # Combine template + context
        complete_prompt = template + context

        logger.debug(f"Built prompt: {len(complete_prompt)} chars")
        return complete_prompt

    def _call_api_with_retry(self, prompt: str, model: str) -> str:
        """Call OpenRouter API with exponential backoff retry logic.

        Args:
            prompt: Complete prompt text
            model: Model identifier

        Returns:
            API response text

        Raises:
            RuntimeError: If all retries fail
        """
        backoff = self.INITIAL_BACKOFF
        last_error = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.info(f"API call attempt {attempt}/{self.MAX_RETRIES}")

                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=self.DEFAULT_TIMEOUT
                )

                # Extract response text
                if not response.choices:
                    raise ValueError("API returned no choices")

                response_text = response.choices[0].message.content
                if not response_text:
                    raise ValueError("API returned empty response")

                logger.info(f"API call successful: {len(response_text)} chars")
                return response_text

            except Exception as e:
                last_error = e
                logger.warning(f"API call failed (attempt {attempt}): {e}")

                # Check if we should retry
                if attempt < self.MAX_RETRIES:
                    # Handle rate limiting with longer backoff
                    if "rate" in str(e).lower() or "429" in str(e):
                        backoff = min(backoff * 3, self.MAX_BACKOFF)
                        logger.info(f"Rate limited - backing off {backoff:.1f}s")
                    else:
                        backoff = min(backoff * 2, self.MAX_BACKOFF)

                    logger.info(f"Retrying in {backoff:.1f} seconds...")
                    time.sleep(backoff)
                else:
                    # All retries exhausted
                    logger.error(f"All {self.MAX_RETRIES} retries failed")
                    break

        # If we get here, all retries failed
        raise RuntimeError(
            f"API call failed after {self.MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )

    def _extract_code(self, response_text: str) -> str:
        """Extract Python code from Claude's response.

        Handles various formats:
        - Markdown code blocks (```python ... ```)
        - Raw code (starts with # or variable assignment)
        - Mixed text and code (extracts largest code block)

        Args:
            response_text: Raw API response text

        Returns:
            Clean Python code string

        Raises:
            ValueError: If no valid code found in response
        """
        # Try to find markdown code blocks first (robust pattern matching)
        # Handles: ```python, ```py, ``` python, ``` with extra spaces/newlines
        code_blocks = re.findall(
            r'```(?:python|py)?\s*\n(.*?)```',
            response_text,
            re.DOTALL | re.IGNORECASE
        )

        if code_blocks:
            # Use the largest code block (most likely the strategy)
            code = max(code_blocks, key=len).strip()
            logger.debug(f"Extracted code from markdown block: {len(code)} chars")
            return code

        # If no code blocks, try to extract raw code
        # Look for lines that start with Python syntax
        lines = response_text.split('\n')
        code_lines = []
        in_code = False

        for line in lines:
            stripped = line.strip()

            # Start collecting if line looks like Python code
            if stripped.startswith(('#', 'close =', 'volume =', 'data.')):
                in_code = True

            # Collect code lines
            if in_code:
                code_lines.append(line)

                # Stop if we hit obvious non-code
                if stripped and not any(c in stripped for c in ['=', '#', '(', ')', '[', ']']):
                    if not stripped.endswith(':'):
                        in_code = False

        if code_lines:
            code = '\n'.join(code_lines).strip()
            logger.debug(f"Extracted raw code: {len(code)} chars")
            return code

        # No code found
        logger.error("No code found in API response")
        logger.debug(f"Response preview: {response_text[:500]}")
        raise ValueError(
            "Could not extract Python code from API response. "
            "Response may not contain valid code blocks."
        )


def generate_strategy_with_claude(
    iteration: int,
    feedback: str = "",
    model: str = ClaudeAPIClient.DEFAULT_MODEL
) -> str:
    """Convenience function to generate strategy code.

    Creates client instance and calls API in one step.

    Args:
        iteration: Current iteration number
        feedback: Feedback from previous iteration (optional)
        model: Model to use (default: anthropic/claude-sonnet-4)

    Returns:
        Clean Python code string for trading strategy

    Raises:
        ValueError: If API key not found
        RuntimeError: If API call fails
    """
    client = ClaudeAPIClient(model=model)
    return client.generate_strategy_with_claude(iteration, feedback, model)


def main():
    """Test the Claude API client."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Testing Claude API Client")
    print("=" * 60)

    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set in environment")
        print("Set it with: export OPENROUTER_API_KEY='your-key-here'")
        return

    print(f"✅ API key found: {api_key[:10]}...{api_key[-10:]}")
    print()

    try:
        # Test generation
        print("Generating test strategy (iteration 0)...")
        code = generate_strategy_with_claude(
            iteration=0,
            feedback="",
            model="anthropic/claude-sonnet-4"
        )

        print(f"\n✅ Generated code: {len(code)} characters")
        print("\nFirst 500 chars:")
        print("-" * 60)
        print(code[:500])
        print("-" * 60)

        # Validate code structure
        checks = {
            "Has data.get()": "data.get(" in code,
            "Has shift(1)": ".shift(1)" in code,
            "Has rank()": ".rank(" in code,
            "Has is_largest()": ".is_largest(" in code,
            "Has sim()": "sim(" in code
        }

        print("\nCode validation:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")

        print("\n✅ Test complete!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
