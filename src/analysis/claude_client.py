"""
Claude API client with retry logic and circuit breaker pattern.

Provides robust integration with Claude API including:
- Automatic retry with exponential backoff
- Circuit breaker to prevent cascading failures
- Rate limiting protection
- Comprehensive error handling
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import anthropic  # type: ignore[import-untyped]
from anthropic import (  # type: ignore[import-untyped]
    APIError,
    APITimeoutError,
    RateLimitError
)

# Configure logging
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout_seconds: int = 60  # Time before trying half-open
    reset_timeout_seconds: int = 300  # Time before fully resetting


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures.

    Implements the circuit breaker pattern to protect against
    repeated failures and give the service time to recover.
    """

    def __init__(self, config: CircuitBreakerConfig) -> None:
        """Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration
        """
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_attempt_time: Optional[float] = None

    def record_success(self) -> None:
        """Record a successful request."""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            self.success_count += 1

    def record_failure(self) -> None:
        """Record a failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.config.failure_threshold:
            self._open_circuit()

    def can_attempt(self) -> bool:
        """Check if a request attempt is allowed.

        Returns:
            True if request can be attempted
        """
        current_time = time.time()

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self.last_failure_time is None:
                return False

            time_since_failure = current_time - self.last_failure_time
            if time_since_failure >= self.config.timeout_seconds:
                self._half_open_circuit()
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def _open_circuit(self) -> None:
        """Open the circuit (block requests)."""
        self.state = CircuitState.OPEN
        self.success_count = 0
        logger.warning("Circuit breaker OPENED - blocking Claude API requests")

    def _half_open_circuit(self) -> None:
        """Half-open the circuit (test if service recovered)."""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        logger.info("Circuit breaker HALF-OPEN - testing Claude API recovery")

    def _close_circuit(self) -> None:
        """Close the circuit (resume normal operation)."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info("Circuit breaker CLOSED - resuming normal operation")

    def get_state(self) -> CircuitState:
        """Get current circuit state.

        Returns:
            Current circuit state
        """
        return self.state


class ClaudeClient:
    """Claude API client with retry logic and circuit breaker.

    Provides robust integration with Claude API including automatic
    retry with exponential backoff and circuit breaker protection.

    Attributes:
        api_key: Claude API key
        model: Model name to use (default: claude-sonnet-4.5)
        max_retries: Maximum retry attempts (default: 3)
        initial_retry_delay: Initial retry delay in seconds (default: 1.0)
        max_retry_delay: Maximum retry delay in seconds (default: 60.0)
        timeout: Request timeout in seconds (default: 120)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4.5",
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
        timeout: int = 120,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ) -> None:
        """Initialize Claude client.

        Args:
            api_key: Claude API key
            model: Model name to use
            max_retries: Maximum retry attempts
            initial_retry_delay: Initial retry delay in seconds
            max_retry_delay: Maximum retry delay in seconds
            timeout: Request timeout in seconds
            circuit_breaker_config: Circuit breaker configuration
        """
        if not api_key:
            raise ValueError("Claude API key is required")

        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        self.timeout = timeout

        # Initialize circuit breaker
        cb_config = circuit_breaker_config or CircuitBreakerConfig()
        self.circuit_breaker = CircuitBreaker(cb_config)

        # Initialize Anthropic client
        self._client = anthropic.Anthropic(api_key=api_key)

        logger.info(f"ClaudeClient initialized with model={model}")

    async def generate_analysis(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> str:
        """Generate analysis using Claude API.

        Args:
            prompt: User prompt for analysis
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Generated analysis text

        Raises:
            RuntimeError: If circuit breaker is open
            APIError: If all retry attempts fail
        """
        # Check circuit breaker
        if not self.circuit_breaker.can_attempt():
            raise RuntimeError(
                "Circuit breaker is OPEN - Claude API requests are blocked. "
                f"State: {self.circuit_breaker.get_state().value}"
            )

        # Attempt with retries
        last_error: Optional[Exception] = None
        retry_delay = self.initial_retry_delay

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    f"Claude API request attempt {attempt + 1}/{self.max_retries + 1}"
                )

                # Make API request (run in executor for async)
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    self._make_request,
                    prompt,
                    system_prompt,
                    max_tokens,
                    temperature
                )

                # Record success
                self.circuit_breaker.record_success()
                logger.info("Claude API request successful")

                # Extract response text
                return self._extract_response_text(response)

            except RateLimitError as e:
                last_error = e
                logger.warning(f"Rate limit error (attempt {attempt + 1}): {e}")

                if attempt < self.max_retries:
                    # Exponential backoff with jitter
                    jitter = retry_delay * 0.1
                    sleep_time = min(retry_delay + jitter, self.max_retry_delay)
                    logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                    await asyncio.sleep(sleep_time)
                    retry_delay *= 2
                else:
                    self.circuit_breaker.record_failure()

            except APITimeoutError as e:
                last_error = e
                logger.warning(f"Timeout error (attempt {attempt + 1}): {e}")

                if attempt < self.max_retries:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    self.circuit_breaker.record_failure()

            except APIError as e:
                last_error = e
                logger.error(f"API error (attempt {attempt + 1}): {e}")

                # Don't retry on client errors (4xx)
                if hasattr(e, 'status_code') and 400 <= e.status_code < 500:  # type: ignore[attr-defined]
                    self.circuit_breaker.record_failure()
                    raise

                if attempt < self.max_retries:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    self.circuit_breaker.record_failure()

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
                self.circuit_breaker.record_failure()
                raise

        # All retries failed
        self.circuit_breaker.record_failure()
        raise RuntimeError(
            f"All {self.max_retries + 1} attempts failed. "
            f"Last error: {last_error}"
        )

    def _make_request(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> Any:
        """Make synchronous API request.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens
            temperature: Sampling temperature

        Returns:
            API response object
        """
        messages: List[Dict[str, str]] = [
            {"role": "user", "content": prompt}
        ]

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        return self._client.messages.create(**kwargs)

    def _extract_response_text(self, response: Any) -> str:
        """Extract text from API response.

        Args:
            response: API response object

        Returns:
            Response text

        Raises:
            ValueError: If response format is unexpected
        """
        try:
            # Handle Anthropic message response
            if hasattr(response, 'content') and len(response.content) > 0:
                first_content = response.content[0]
                if hasattr(first_content, 'text'):
                    return str(first_content.text)
                return str(first_content)
            raise ValueError(f"Unexpected response format: {type(response)}")
        except Exception as e:
            logger.error(f"Failed to extract response text: {e}")
            raise ValueError(f"Failed to extract response text: {e}") from e

    def get_circuit_state(self) -> CircuitState:
        """Get current circuit breaker state.

        Returns:
            Current circuit state
        """
        return self.circuit_breaker.get_state()

    def reset_circuit(self) -> None:
        """Manually reset circuit breaker to CLOSED state.

        Use this to manually override circuit breaker state
        after resolving issues.
        """
        self.circuit_breaker._close_circuit()
        logger.info("Circuit breaker manually reset to CLOSED")
