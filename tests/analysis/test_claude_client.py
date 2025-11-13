"""Tests for Claude API client."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from anthropic import APIError, RateLimitError, APITimeoutError  # type: ignore[import-untyped]

from src.analysis.claude_client import (
    ClaudeClient,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState
)


class TestCircuitBreaker:
    """Tests for circuit breaker."""

    def test_initial_state_closed(self) -> None:
        """Test circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker(CircuitBreakerConfig())
        assert cb.get_state() == CircuitState.CLOSED
        assert cb.can_attempt()

    def test_opens_after_failures(self) -> None:
        """Test circuit opens after threshold failures."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)

        # Record failures
        cb.record_failure()
        cb.record_failure()
        assert cb.get_state() == CircuitState.CLOSED

        cb.record_failure()
        assert cb.get_state() == CircuitState.OPEN
        assert not cb.can_attempt()

    def test_half_open_after_timeout(self) -> None:
        """Test circuit transitions to HALF_OPEN after timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout_seconds=0  # Immediate timeout for testing
        )
        cb = CircuitBreaker(config)

        # Open circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.get_state() == CircuitState.OPEN

        # Should transition to HALF_OPEN
        assert cb.can_attempt()
        assert cb.get_state() == CircuitState.HALF_OPEN

    def test_closes_from_half_open_on_success(self) -> None:
        """Test circuit closes from HALF_OPEN after successes."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout_seconds=0
        )
        cb = CircuitBreaker(config)

        # Open circuit
        cb.record_failure()
        cb.record_failure()

        # Half-open
        cb.can_attempt()
        assert cb.get_state() == CircuitState.HALF_OPEN

        # Record successes
        cb.record_success()
        assert cb.get_state() == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.get_state() == CircuitState.CLOSED


class TestClaudeClient:
    """Tests for Claude API client."""

    def test_initialization(self) -> None:
        """Test client initialization."""
        client = ClaudeClient(api_key="test-key", model="test-model")
        assert client.api_key == "test-key"
        assert client.model == "test-model"
        assert client.get_circuit_state() == CircuitState.CLOSED

    def test_initialization_without_api_key(self) -> None:
        """Test initialization fails without API key."""
        with pytest.raises(ValueError, match="API key is required"):
            ClaudeClient(api_key="")

    @pytest.mark.asyncio
    async def test_generate_analysis_success(self) -> None:
        """Test successful analysis generation."""
        client = ClaudeClient(api_key="test-key")

        # Mock response
        mock_content = Mock()
        mock_content.text = "Test analysis result"

        mock_response = Mock()
        mock_response.content = [mock_content]

        # Mock client
        with patch.object(client, '_make_request', return_value=mock_response):
            result = await client.generate_analysis(
                prompt="Test prompt",
                max_tokens=100
            )

        assert result == "Test analysis result"
        assert client.get_circuit_state() == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_generate_analysis_rate_limit_retry(self) -> None:
        """Test retry on rate limit error."""
        client = ClaudeClient(
            api_key="test-key",
            max_retries=2,
            initial_retry_delay=0.01
        )

        # Mock response (success on 2nd try)
        mock_content = Mock()
        mock_content.text = "Success"
        mock_response = Mock()
        mock_response.content = [mock_content]

        call_count = 0

        def mock_request(*args, **kwargs):  # type: ignore[no-untyped-def]
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Create proper RateLimitError with required parameters
                mock_err_response = Mock()
                mock_err_response.status_code = 429
                raise RateLimitError("Rate limit", response=mock_err_response, body={})
            return mock_response

        with patch.object(client, '_make_request', side_effect=mock_request):
            result = await client.generate_analysis(prompt="Test")

        assert result == "Success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self) -> None:
        """Test circuit breaker opens after repeated failures."""
        client = ClaudeClient(
            api_key="test-key",
            max_retries=0,
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=2)
        )

        # Fail twice - use RuntimeError since we changed APIError to RuntimeError in client
        for _ in range(2):
            with patch.object(client, '_make_request', side_effect=RuntimeError("Test error")):
                with pytest.raises(RuntimeError):
                    await client.generate_analysis(prompt="Test")

        # Circuit should be open
        assert client.get_circuit_state() == CircuitState.OPEN

        # Should reject requests
        with pytest.raises(RuntimeError, match="Circuit breaker is OPEN"):
            await client.generate_analysis(prompt="Test")

    @pytest.mark.asyncio
    async def test_timeout_error_retry(self) -> None:
        """Test retry on timeout error."""
        client = ClaudeClient(
            api_key="test-key",
            max_retries=1,
            initial_retry_delay=0.01
        )

        # Mock timeout then success
        mock_content = Mock()
        mock_content.text = "Success"
        mock_response = Mock()
        mock_response.content = [mock_content]

        call_count = 0

        def mock_request(*args, **kwargs):  # type: ignore[no-untyped-def]
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise APITimeoutError("Timeout")
            return mock_response

        with patch.object(client, '_make_request', side_effect=mock_request):
            result = await client.generate_analysis(prompt="Test")

        assert result == "Success"

    def test_reset_circuit(self) -> None:
        """Test manual circuit reset."""
        client = ClaudeClient(
            api_key="test-key",
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=1)
        )

        # Open circuit
        client.circuit_breaker.record_failure()
        assert client.get_circuit_state() == CircuitState.OPEN

        # Reset
        client.reset_circuit()
        assert client.get_circuit_state() == CircuitState.CLOSED
