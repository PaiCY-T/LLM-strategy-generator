"""
InnovationEngine - LLM-driven feedback loop for strategy generation

Integrates LLMProvider and PromptBuilder into a complete feedback-driven
generation pipeline with validation, retry logic, and cost tracking.

Task: LLM Integration Activation - Task 3
Requirements: 1.3, 1.4, 1.5
"""

import re
import time
import yaml
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

from .llm_providers import create_provider, LLMResponse, LLMProviderInterface
from .prompt_builder import PromptBuilder
from .structured_prompt_builder import StructuredPromptBuilder
from ..sandbox.security_validator import SecurityValidator
from ..generators.yaml_to_code_generator import YAMLToCodeGenerator
from ..generators.yaml_schema_validator import YAMLSchemaValidator


@dataclass
class GenerationResult:
    """Result of a code generation attempt."""
    success: bool
    code: Optional[str]
    metadata: Dict[str, Any]
    cost_usd: float
    attempts: int
    total_time_seconds: float
    error_message: Optional[str] = None


class InnovationEngine:
    """
    LLM-driven innovation engine with feedback loops.

    Integrates:
    - LLMProvider: API calls to OpenRouter/Gemini/OpenAI
    - PromptBuilder: Constructs prompts with champion feedback and failure patterns
    - SecurityValidator: AST-based code validation
    - Retry logic: Exponential backoff on failures
    - Cost tracking: Token usage and API costs

    Key Features:
    - Feedback-driven generation using champion metrics and failure history
    - Automatic validation with SecurityValidator
    - Retry with error feedback (up to 3 attempts)
    - Cost tracking across all API calls
    - Token budget enforcement (<2000 tokens per prompt)
    """

    def __init__(
        self,
        provider_name: str = 'gemini',
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 60,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        failure_patterns_path: str = "artifacts/data/failure_patterns.json",
        generation_mode: str = 'full_code'
    ):
        """
        Initialize InnovationEngine.

        Args:
            provider_name: LLM provider ('openrouter', 'gemini', 'openai')
            model: Model name (uses provider default if None)
            api_key: API key (reads from env if None)
            max_retries: Maximum retry attempts on failures (default: 3)
            timeout: Request timeout in seconds (default: 60)
            max_tokens: Maximum tokens in LLM response (default: 2000)
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)
            failure_patterns_path: Path to failure patterns JSON
            generation_mode: 'full_code' or 'yaml' (default: 'full_code')
        """
        # Initialize LLM Provider
        try:
            self.provider: LLMProviderInterface = create_provider(
                provider_name=provider_name,
                api_key=api_key,
                model=model,
                timeout=timeout
            )
            self.provider_available = True

            # Task 4.3: Diagnostic logging for LLM initialization
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"LLM initialized: provider='{provider_name}', model='{model or 'default'}'")

        except ValueError as e:
            print(f"⚠️  Failed to initialize LLM provider: {e}")
            print("   InnovationEngine will signal fallback on all attempts")
            self.provider = None
            self.provider_available = False

        # Initialize PromptBuilder
        self.prompt_builder = PromptBuilder(failure_patterns_path=failure_patterns_path)

        # Initialize SecurityValidator
        self.validator = SecurityValidator()

        # Generation mode configuration
        self.generation_mode = generation_mode

        # Initialize structured mode components
        if generation_mode == 'yaml':
            self.structured_prompt_builder = StructuredPromptBuilder()
            schema_validator = YAMLSchemaValidator()
            self.yaml_generator = YAMLToCodeGenerator(schema_validator)
        else:
            self.structured_prompt_builder = None
            self.yaml_generator = None

        # Configuration
        self.max_retries = max_retries
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Statistics tracking
        self.total_attempts = 0
        self.successful_generations = 0
        self.failed_generations = 0
        self.total_cost_usd = 0.0
        self.total_tokens = 0
        self.validation_failures = 0
        self.api_failures = 0

        # Mode-specific statistics
        self.yaml_successes = 0
        self.yaml_failures = 0
        self.yaml_validation_failures = 0

        # History
        self.generation_history: List[GenerationResult] = []

    def generate_innovation(
        self,
        champion_code: str,
        champion_metrics: Dict[str, float],
        failure_history: Optional[List[Dict[str, Any]]] = None,
        target_metric: str = "sharpe_ratio"
    ) -> Optional[str]:
        """
        Generate improved strategy code using LLM with feedback loop.

        Main entry point for LLM-driven innovation. Uses champion feedback
        and failure patterns to guide code generation with automatic validation
        and retry logic. Supports both full_code and yaml generation modes.

        Args:
            champion_code: Current champion strategy code
            champion_metrics: Champion performance metrics (sharpe, mdd, win_rate, etc.)
            failure_history: Optional list of recent failures (last 3)
            target_metric: Which metric to optimize (default: sharpe_ratio)

        Returns:
            Generated strategy code as string, or None if all attempts failed

        Example:
            >>> engine = InnovationEngine(provider_name='gemini', generation_mode='yaml')
            >>> code = engine.generate_innovation(
            ...     champion_code="def strategy(data): return data.get('fundamental_features:ROE稅後') > 15",
            ...     champion_metrics={"sharpe_ratio": 0.85, "max_drawdown": 0.15},
            ...     target_metric="sharpe_ratio"
            ... )
            >>> if code:
            ...     print("Success! Generated code:", code[:100])
            ... else:
            ...     print("Failed - fallback to Factor Graph mutation")
        """
        # Route to appropriate generation method based on mode
        if self.generation_mode == 'yaml':
            return self._generate_yaml_innovation(
                champion_metrics, failure_history, target_metric
            )
        else:
            return self._generate_full_code_innovation(
                champion_code, champion_metrics, failure_history, target_metric
            )

    def _generate_full_code_innovation(
        self,
        champion_code: str,
        champion_metrics: Dict[str, float],
        failure_history: Optional[List[Dict[str, Any]]] = None,
        target_metric: str = "sharpe_ratio"
    ) -> Optional[str]:
        """
        Generate innovation via full Python code generation (original mode).

        Args:
            champion_code: Current champion strategy code
            champion_metrics: Champion performance metrics
            failure_history: Optional list of recent failures
            target_metric: Which metric to optimize

        Returns:
            Generated strategy code as string, or None if failed
        """
        start_time = time.time()
        self.total_attempts += 1

        # Check if provider is available
        if not self.provider_available or not self.provider:
            error_msg = "LLM provider not available - API key missing or invalid"
            self._record_failure(start_time, error_msg, 0, 0.0)
            return None

        # Build modification prompt
        try:
            prompt = self.prompt_builder.build_modification_prompt(
                champion_code=champion_code,
                champion_metrics=champion_metrics,
                failure_history=failure_history,
                target_metric=target_metric
            )
        except Exception as e:
            error_msg = f"Failed to build prompt: {str(e)}"
            self._record_failure(start_time, error_msg, 0, 0.0)
            return None

        # Attempt generation with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                # Call LLM API
                response = self.provider.generate(
                    prompt=prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    max_retries=1  # Provider handles its own retries
                )

                if not response:
                    # API call failed
                    if attempt < self.max_retries:
                        print(f"⚠️  API call failed (attempt {attempt}/{self.max_retries}), retrying...")
                        self._exponential_backoff(attempt - 1)
                        continue
                    else:
                        self.api_failures += 1
                        error_msg = "LLM API call failed after all retries"
                        self._record_failure(start_time, error_msg, attempt, 0.0)
                        return None

                # Track cost
                cost = self.provider.estimate_cost(response.prompt_tokens, response.completion_tokens)
                self.total_cost_usd += cost
                self.total_tokens += response.total_tokens

                # Extract code from response
                code = self._extract_code(response.content)

                if not code:
                    # Code extraction failed
                    if attempt < self.max_retries:
                        print(f"⚠️  Code extraction failed (attempt {attempt}/{self.max_retries}), retrying with feedback...")
                        # Retry with feedback about extraction failure
                        prompt = self._build_retry_prompt(
                            original_prompt=prompt,
                            error_msg="Failed to extract Python code from response. Please provide code in ```python ... ``` block.",
                            previous_response=response.content
                        )
                        self._exponential_backoff(attempt - 1)
                        continue
                    else:
                        error_msg = "Failed to extract code from LLM response"
                        self._record_failure(start_time, error_msg, attempt, cost)
                        return None

                # Validate generated code
                is_valid, validation_errors = self.validate_generated_code(code)

                if not is_valid:
                    self.validation_failures += 1

                    if attempt < self.max_retries:
                        print(f"⚠️  Validation failed (attempt {attempt}/{self.max_retries}), retrying with feedback...")
                        # Retry with validation feedback
                        error_feedback = "\n".join(validation_errors)
                        prompt = self._build_retry_prompt(
                            original_prompt=prompt,
                            error_msg=f"Generated code failed validation:\n{error_feedback}\n\nPlease fix these issues.",
                            previous_response=code
                        )
                        self._exponential_backoff(attempt - 1)
                        continue
                    else:
                        error_msg = f"Validation failed: {validation_errors[0]}"
                        self._record_failure(start_time, error_msg, attempt, cost)
                        return None

                # Success!
                elapsed = time.time() - start_time
                self.successful_generations += 1

                result = GenerationResult(
                    success=True,
                    code=code,
                    metadata={
                        'provider': response.provider,
                        'model': response.model,
                        'prompt_tokens': response.prompt_tokens,
                        'completion_tokens': response.completion_tokens,
                        'total_tokens': response.total_tokens,
                        'target_metric': target_metric,
                        'champion_sharpe': champion_metrics.get('sharpe_ratio', 0)
                    },
                    cost_usd=cost,
                    attempts=attempt,
                    total_time_seconds=elapsed
                )

                self.generation_history.append(result)

                print(f"✅ Innovation generated successfully (attempt {attempt}/{self.max_retries})")
                print(f"   Cost: ${cost:.6f}, Tokens: {response.total_tokens}, Time: {elapsed:.2f}s")

                return code

            except Exception as e:
                if attempt < self.max_retries:
                    print(f"⚠️  Unexpected error (attempt {attempt}/{self.max_retries}): {str(e)}")
                    self._exponential_backoff(attempt - 1)
                    continue
                else:
                    error_msg = f"Unexpected error: {str(e)}"
                    self._record_failure(start_time, error_msg, attempt, 0.0)
                    return None

        # Should never reach here, but just in case
        self._record_failure(start_time, "Max retries exceeded", self.max_retries, 0.0)
        return None

    def _generate_yaml_innovation(
        self,
        champion_metrics: Dict[str, float],
        failure_history: Optional[List[Dict[str, Any]]] = None,
        target_metric: str = "sharpe_ratio"
    ) -> Optional[str]:
        """
        Generate innovation via YAML intermediate format.

        YAML mode workflow:
        1. Extract failure patterns from history
        2. Build YAML-specific prompt using StructuredPromptBuilder
        3. Call LLM to generate YAML spec
        4. Extract and parse YAML from response
        5. Validate YAML against schema
        6. Convert YAML to Python code using YAMLToCodeGenerator
        7. Return Python code

        Args:
            champion_metrics: Champion performance metrics
            failure_history: Optional list of recent failures
            target_metric: Which metric to optimize

        Returns:
            Generated strategy code as string, or None if failed
        """
        start_time = time.time()
        self.total_attempts += 1

        # Check if provider is available
        if not self.provider_available or not self.provider:
            error_msg = "LLM provider not available - API key missing or invalid"
            self._record_failure(start_time, error_msg, 0, 0.0)
            return None

        # Check if structured mode components are initialized
        if not self.structured_prompt_builder or not self.yaml_generator:
            error_msg = "YAML mode not initialized - use generation_mode='yaml' in constructor"
            self._record_failure(start_time, error_msg, 0, 0.0)
            return None

        # Extract failure patterns from history
        failure_patterns = []
        if failure_history:
            for failure in failure_history[-5:]:  # Last 5 failures
                error_type = failure.get('error_type', 'unknown')
                description = failure.get('description', '')
                if description:
                    failure_patterns.append(f"{error_type}: {description}")
                else:
                    failure_patterns.append(error_type)

        # Build YAML-specific prompt
        try:
            prompt = self.structured_prompt_builder.build_compact_prompt(
                champion_metrics=champion_metrics,
                failure_patterns=failure_patterns,
                target_strategy_type='momentum'  # Could be made dynamic based on history
            )
        except Exception as e:
            error_msg = f"Failed to build YAML prompt: {str(e)}"
            self._record_failure(start_time, error_msg, 0, 0.0)
            return None

        # Attempt YAML generation with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                # Call LLM API for YAML generation
                response = self.provider.generate(
                    prompt=prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    max_retries=1
                )

                if not response:
                    # API call failed
                    if attempt < self.max_retries:
                        print(f"⚠️  API call failed (attempt {attempt}/{self.max_retries}), retrying...")
                        self._exponential_backoff(attempt - 1)
                        continue
                    else:
                        self.api_failures += 1
                        error_msg = "LLM API call failed after all retries"
                        self._record_failure(start_time, error_msg, attempt, 0.0)
                        return None

                # Track cost
                cost = self.provider.estimate_cost(response.prompt_tokens, response.completion_tokens)
                self.total_cost_usd += cost
                self.total_tokens += response.total_tokens

                # Extract YAML from response
                yaml_text = self._extract_yaml(response.content)

                if not yaml_text:
                    # YAML extraction failed
                    if attempt < self.max_retries:
                        print(f"⚠️  YAML extraction failed (attempt {attempt}/{self.max_retries}), retrying...")
                        prompt = self._build_retry_prompt_yaml(
                            "Failed to extract YAML from response. Please provide YAML spec starting with 'metadata:'",
                            response.content
                        )
                        self._exponential_backoff(attempt - 1)
                        continue
                    else:
                        error_msg = "Failed to extract YAML from LLM response"
                        self._record_failure(start_time, error_msg, attempt, cost)
                        return None

                # Parse YAML
                try:
                    yaml_spec = yaml.safe_load(yaml_text)
                except yaml.YAMLError as e:
                    self.yaml_validation_failures += 1
                    if attempt < self.max_retries:
                        print(f"⚠️  YAML parsing failed (attempt {attempt}/{self.max_retries}): {str(e)}")
                        prompt = self._build_retry_prompt_yaml(
                            f"YAML parsing error: {str(e)}\n\nPlease provide valid YAML.",
                            yaml_text
                        )
                        self._exponential_backoff(attempt - 1)
                        continue
                    else:
                        error_msg = f"YAML parsing error: {str(e)}"
                        self._record_failure(start_time, error_msg, attempt, cost)
                        return None

                # Generate Python code from YAML
                code, errors = self.yaml_generator.generate(yaml_spec)

                if code:
                    # Success!
                    elapsed = time.time() - start_time
                    self.successful_generations += 1
                    self.yaml_successes += 1

                    result = GenerationResult(
                        success=True,
                        code=code,
                        metadata={
                            'provider': response.provider,
                            'model': response.model,
                            'prompt_tokens': response.prompt_tokens,
                            'completion_tokens': response.completion_tokens,
                            'total_tokens': response.total_tokens,
                            'target_metric': target_metric,
                            'champion_sharpe': champion_metrics.get('sharpe_ratio', 0),
                            'generation_mode': 'yaml'
                        },
                        cost_usd=cost,
                        attempts=attempt,
                        total_time_seconds=elapsed
                    )

                    self.generation_history.append(result)

                    print(f"✅ YAML innovation generated successfully (attempt {attempt}/{self.max_retries})")
                    print(f"   Cost: ${cost:.6f}, Tokens: {response.total_tokens}, Time: {elapsed:.2f}s")

                    return code

                elif attempt < self.max_retries:
                    # YAML validation/generation errors - retry with feedback
                    self.yaml_validation_failures += 1
                    error_feedback = "\n".join(errors)
                    print(f"⚠️  YAML validation failed (attempt {attempt}/{self.max_retries})")
                    prompt = self._build_retry_prompt_yaml(
                        f"YAML validation errors:\n{error_feedback}\n\nPlease fix these issues.",
                        yaml_text
                    )
                    self._exponential_backoff(attempt - 1)
                    continue
                else:
                    # Final attempt failed
                    self.yaml_failures += 1
                    error_msg = f"YAML validation failed: {errors[0] if errors else 'unknown error'}"
                    self._record_failure(start_time, error_msg, attempt, cost)
                    return None

            except Exception as e:
                if attempt < self.max_retries:
                    print(f"⚠️  Unexpected error in YAML mode (attempt {attempt}/{self.max_retries}): {str(e)}")
                    self._exponential_backoff(attempt - 1)
                    continue
                else:
                    self.yaml_failures += 1
                    error_msg = f"Unexpected error in YAML mode: {str(e)}"
                    self._record_failure(start_time, error_msg, attempt, 0.0)
                    return None

        # Should never reach here
        self.yaml_failures += 1
        self._record_failure(start_time, "Max retries exceeded in YAML mode", self.max_retries, 0.0)
        return None

    def validate_generated_code(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate generated code using SecurityValidator.

        Checks for:
        - Syntax errors
        - Dangerous imports (subprocess, os, etc.)
        - Dangerous operations (eval, exec, open, etc.)
        - Network operations

        Args:
            code: Python code to validate

        Returns:
            (is_valid, error_messages) tuple
            - is_valid: True if code passes all checks
            - error_messages: List of validation errors (empty if valid)

        Example:
            >>> engine = InnovationEngine()
            >>> is_valid, errors = engine.validate_generated_code("def strategy(data): return data.get('price:收盤價') > 100")
            >>> is_valid
            True
            >>> errors
            []
        """
        return self.validator.validate(code)

    def retry_with_feedback(
        self,
        error_msg: str,
        previous_attempt: str,
        original_champion_code: str,
        original_champion_metrics: Dict[str, float]
    ) -> Optional[str]:
        """
        Retry generation with error feedback from previous attempt.

        Builds a new prompt that includes the error message and previous
        attempt to guide the LLM to fix the issues.

        Args:
            error_msg: Error message from previous attempt
            previous_attempt: Previous generated code that failed
            original_champion_code: Original champion code
            original_champion_metrics: Original champion metrics

        Returns:
            Generated code or None if retry failed

        Example:
            >>> engine = InnovationEngine()
            >>> code = engine.retry_with_feedback(
            ...     error_msg="Syntax error on line 5",
            ...     previous_attempt="def strategy(data): return data.get('ROE' > 15",
            ...     original_champion_code=champion_code,
            ...     original_champion_metrics=champion_metrics
            ... )
        """
        # Build retry prompt with error feedback
        retry_prompt = self.prompt_builder.build_modification_prompt(
            champion_code=original_champion_code,
            champion_metrics=original_champion_metrics,
            failure_history=[{
                'pattern_type': 'validation_error',
                'description': error_msg,
                'code_snippet': previous_attempt[:200],
                'performance_impact': 0.0
            }],
            target_metric='sharpe_ratio'
        )

        # Add explicit feedback section
        retry_prompt += f"\n\n## CRITICAL: Previous Attempt Failed\n\n"
        retry_prompt += f"**Error**: {error_msg}\n\n"
        retry_prompt += f"**Previous Code**:\n```python\n{previous_attempt[:300]}\n```\n\n"
        retry_prompt += f"Please fix the error and provide corrected code."

        # Attempt generation
        try:
            response = self.provider.generate(
                prompt=retry_prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                max_retries=1
            )

            if not response:
                return None

            # Track cost
            cost = self.provider.estimate_cost(response.prompt_tokens, response.completion_tokens)
            self.total_cost_usd += cost
            self.total_tokens += response.total_tokens

            # Extract and validate
            code = self._extract_code(response.content)
            if not code:
                return None

            is_valid, _ = self.validate_generated_code(code)
            if not is_valid:
                return None

            return code

        except Exception as e:
            print(f"❌ Retry with feedback failed: {str(e)}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get innovation engine statistics including mode-specific metrics.

        Returns:
            Statistics dictionary with:
            - Attempt counts (total, successful, failed)
            - Success rate
            - Cost tracking (total cost, average cost per attempt)
            - Token usage
            - Failure breakdown (validation, API failures)
            - Mode-specific metrics (YAML mode)
        """
        success_rate = (
            self.successful_generations / self.total_attempts
            if self.total_attempts > 0 else 0.0
        )

        avg_cost = (
            self.total_cost_usd / self.total_attempts
            if self.total_attempts > 0 else 0.0
        )

        stats = {
            'generation_mode': self.generation_mode,
            'total_attempts': self.total_attempts,
            'successful_generations': self.successful_generations,
            'failed_generations': self.failed_generations,
            'success_rate': success_rate,
            'total_cost_usd': self.total_cost_usd,
            'average_cost_usd': avg_cost,
            'total_tokens': self.total_tokens,
            'validation_failures': self.validation_failures,
            'api_failures': self.api_failures,
            'provider_available': self.provider_available,
            'provider_name': self.provider._get_provider_name() if self.provider else None,
            'model': self.provider.model if self.provider else None
        }

        # Add YAML mode specific statistics
        if self.generation_mode == 'yaml':
            yaml_total = self.yaml_successes + self.yaml_failures
            yaml_success_rate = (
                self.yaml_successes / yaml_total
                if yaml_total > 0 else 0.0
            )
            stats.update({
                'yaml_successes': self.yaml_successes,
                'yaml_failures': self.yaml_failures,
                'yaml_validation_failures': self.yaml_validation_failures,
                'yaml_success_rate': yaml_success_rate
            })

        return stats

    def get_cost_report(self) -> Dict[str, Any]:
        """
        Get detailed cost tracking report.

        Returns:
            Cost report with total cost, token usage, and per-generation breakdown
        """
        successful_results = [r for r in self.generation_history if r.success]

        if not successful_results:
            return {
                'total_cost_usd': self.total_cost_usd,
                'total_tokens': self.total_tokens,
                'successful_generations': 0,
                'average_cost_per_success': 0.0,
                'cost_breakdown': []
            }

        avg_cost_per_success = (
            sum(r.cost_usd for r in successful_results) / len(successful_results)
            if successful_results else 0.0
        )

        return {
            'total_cost_usd': self.total_cost_usd,
            'total_tokens': self.total_tokens,
            'successful_generations': len(successful_results),
            'average_cost_per_success': avg_cost_per_success,
            'cost_breakdown': [
                {
                    'timestamp': r.metadata.get('timestamp', 'unknown'),
                    'cost_usd': r.cost_usd,
                    'tokens': r.metadata.get('total_tokens', 0),
                    'model': r.metadata.get('model', 'unknown')
                }
                for r in successful_results
            ]
        }

    def reset_statistics(self):
        """Reset all statistics and history (useful for testing)."""
        self.total_attempts = 0
        self.successful_generations = 0
        self.failed_generations = 0
        self.total_cost_usd = 0.0
        self.total_tokens = 0
        self.validation_failures = 0
        self.api_failures = 0
        self.yaml_successes = 0
        self.yaml_failures = 0
        self.yaml_validation_failures = 0
        self.generation_history = []

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _extract_code(self, llm_response: str) -> Optional[str]:
        """
        Extract Python code from LLM response.

        Looks for code in ```python ... ``` blocks or tries to extract
        function definitions directly.

        Args:
            llm_response: Full LLM response text

        Returns:
            Extracted Python code or None if extraction failed
        """
        # Try to find code in ```python ... ``` block
        pattern = r'```python\s*(.*?)\s*```'
        matches = re.findall(pattern, llm_response, re.DOTALL)

        if matches:
            # Return the first Python code block
            return matches[0].strip()

        # Try to find code in ``` ... ``` block (no language specified)
        pattern = r'```\s*(.*?)\s*```'
        matches = re.findall(pattern, llm_response, re.DOTALL)

        if matches:
            # Check if it looks like Python code (contains 'def strategy')
            for match in matches:
                if 'def strategy' in match:
                    return match.strip()

        # Try to extract function definition directly
        if 'def strategy' in llm_response:
            # Extract from 'def strategy' to end or next major section
            start_idx = llm_response.find('def strategy')
            code_candidate = llm_response[start_idx:]

            # Truncate at common section markers
            for marker in ['\n\n#', '\n\n##', '\n\n**', '\n\nNote:', '\n\nExample:']:
                if marker in code_candidate:
                    code_candidate = code_candidate[:code_candidate.find(marker)]

            return code_candidate.strip()

        # Failed to extract code
        return None

    def _build_retry_prompt(
        self,
        original_prompt: str,
        error_msg: str,
        previous_response: str
    ) -> str:
        """
        Build retry prompt with error feedback.

        Args:
            original_prompt: Original prompt that was sent
            error_msg: Error message from validation/extraction
            previous_response: Previous LLM response or extracted code

        Returns:
            New prompt with feedback
        """
        retry_prompt = original_prompt

        # Add critical feedback section
        retry_prompt += f"\n\n## ⚠️  CRITICAL: Previous Attempt Failed\n\n"
        retry_prompt += f"**Error**: {error_msg}\n\n"

        # Show previous response (truncated)
        preview = previous_response[:300] + "..." if len(previous_response) > 300 else previous_response
        retry_prompt += f"**Previous Response**:\n```\n{preview}\n```\n\n"

        retry_prompt += "**Required**: Fix the error and provide valid Python code in ```python ... ``` block."

        return retry_prompt

    def _extract_yaml(self, text: str) -> Optional[str]:
        """
        Extract YAML content from LLM response.

        Tries multiple extraction strategies:
        1. ```yaml ... ``` blocks
        2. Generic ``` ... ``` blocks
        3. Entire response (if it looks like YAML)

        Args:
            text: LLM response text

        Returns:
            Extracted YAML content or None if extraction failed
        """
        # Try to find YAML in ```yaml ... ``` block
        yaml_match = re.search(r'```yaml\s*\n(.*?)\n```', text, re.DOTALL)
        if yaml_match:
            return yaml_match.group(1).strip()

        # Try to find YAML in ``` ... ``` block (no language specified)
        code_match = re.search(r'```\s*\n(.*?)\n```', text, re.DOTALL)
        if code_match:
            content = code_match.group(1).strip()
            # Check if it looks like YAML (starts with 'metadata:')
            if content.startswith('metadata:'):
                return content

        # Try to find YAML without code blocks (check if text starts with metadata:)
        if 'metadata:' in text:
            # Extract from 'metadata:' to end or next major section
            start_idx = text.find('metadata:')
            yaml_candidate = text[start_idx:]

            # Truncate at common section markers or markdown headers
            for marker in ['\n\n#', '\n\n##', '\n\n**Note:', '\n\nExample:', '---']:
                if marker in yaml_candidate:
                    yaml_candidate = yaml_candidate[:yaml_candidate.find(marker)]

            return yaml_candidate.strip()

        # Failed to extract YAML
        return None

    def _build_retry_prompt_yaml(
        self,
        error_msg: str,
        previous_yaml: str
    ) -> str:
        """
        Build retry prompt for YAML generation with error feedback.

        Args:
            error_msg: Error message from YAML validation/parsing
            previous_yaml: Previous YAML or response that failed

        Returns:
            New prompt with feedback for YAML generation
        """
        retry_prompt = "You previously attempted to generate a YAML trading strategy, but it failed validation.\n\n"

        # Add error feedback
        retry_prompt += f"## ⚠️  CRITICAL: Previous YAML Failed\n\n"
        retry_prompt += f"**Error**: {error_msg}\n\n"

        # Show previous YAML (truncated)
        preview = previous_yaml[:500] + "..." if len(previous_yaml) > 500 else previous_yaml
        retry_prompt += f"**Previous YAML**:\n```yaml\n{preview}\n```\n\n"

        # Add instructions
        retry_prompt += "**Required**: Fix the errors and provide valid YAML strategy specification.\n"
        retry_prompt += "- Start with 'metadata:' at the top level\n"
        retry_prompt += "- Follow the schema exactly\n"
        retry_prompt += "- Ensure all required fields are present\n"
        retry_prompt += "- Use valid YAML syntax (proper indentation, quotes, etc.)\n\n"
        retry_prompt += "Output ONLY valid YAML starting with 'metadata:':"

        return retry_prompt

    def _exponential_backoff(self, attempt: int):
        """Sleep with exponential backoff between retries."""
        sleep_time = 2 ** attempt  # 1s, 2s, 4s, ...
        time.sleep(sleep_time)

    def _record_failure(
        self,
        start_time: float,
        error_msg: str,
        attempts: int,
        cost: float
    ):
        """Record a failed generation attempt."""
        self.failed_generations += 1
        elapsed = time.time() - start_time

        result = GenerationResult(
            success=False,
            code=None,
            metadata={'error': error_msg},
            cost_usd=cost,
            attempts=attempts,
            total_time_seconds=elapsed,
            error_message=error_msg
        )

        self.generation_history.append(result)

        print(f"❌ Innovation generation failed: {error_msg}")


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("INNOVATION ENGINE - Example Usage")
    print("=" * 80)

    # Example 1: Initialize engine
    print("\nExample 1: Initialize InnovationEngine")
    print("-" * 80)

    try:
        engine = InnovationEngine(
            provider_name='gemini',  # Use free Gemini model
            max_retries=3,
            temperature=0.7
        )
        print(f"✅ InnovationEngine initialized")
        print(f"   Provider: {engine.provider._get_provider_name() if engine.provider else 'None'}")
        print(f"   Model: {engine.provider.model if engine.provider else 'None'}")
        print(f"   Max retries: {engine.max_retries}")
    except Exception as e:
        print(f"⚠️  {e}")

    # Example 2: Generate innovation (mock data)
    print("\nExample 2: Generate Innovation (requires API key)")
    print("-" * 80)

    champion_code = """
def strategy(data):
    # Simple ROE filter
    roe = data.get('fundamental_features:ROE稅後')
    return roe > 15
"""

    champion_metrics = {
        'sharpe_ratio': 0.85,
        'max_drawdown': 0.15,
        'win_rate': 0.58,
        'calmar_ratio': 2.3
    }

    # Only attempt if API key is configured
    if engine.provider_available:
        print("Attempting LLM generation...")
        code = engine.generate_innovation(
            champion_code=champion_code,
            champion_metrics=champion_metrics,
            target_metric='sharpe_ratio'
        )

        if code:
            print(f"✅ Generated code:")
            print(f"\n{code}\n")
        else:
            print(f"❌ Generation failed - would fallback to Factor Graph")
    else:
        print("⚠️  Skipping - API key not configured")

    # Example 3: Validate code
    print("\nExample 3: Validate Generated Code")
    print("-" * 80)

    test_code = """
def strategy(data):
    roe = data.get('fundamental_features:ROE稅後')
    growth = data.get('fundamental_features:營收成長率')
    return (roe > 15) & (growth > 0.1)
"""

    is_valid, errors = engine.validate_generated_code(test_code)
    print(f"Code validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")
    if errors:
        print(f"Errors: {errors}")

    # Example 4: Statistics
    print("\nExample 4: Engine Statistics")
    print("-" * 80)

    stats = engine.get_statistics()
    print(f"Total attempts: {stats['total_attempts']}")
    print(f"Successful: {stats['successful_generations']}")
    print(f"Failed: {stats['failed_generations']}")
    print(f"Success rate: {stats['success_rate']:.1%}")
    print(f"Total cost: ${stats['total_cost_usd']:.6f}")
    print(f"Total tokens: {stats['total_tokens']}")

    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETE")
    print("=" * 80)
