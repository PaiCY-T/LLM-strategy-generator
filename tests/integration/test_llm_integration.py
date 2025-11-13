"""
Integration tests for LLM Integration with Mock Providers

Task 11: Test LLM Integration with Mock Providers
- Create mock LLM provider for testing
- Test PromptManager with mock responses
- Verify prompt selection logic
- Test retry behavior
- Create comprehensive integration tests

This file provides end-to-end integration tests for the complete LLM pipeline:
PromptManager -> LLMProvider -> Response Handling -> Validation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Optional

from src.innovation.prompt_manager import (
    PromptManager,
    PromptContext,
    PromptType,
    GenerationMode
)
from src.innovation.llm_providers import (
    LLMProviderInterface,
    LLMResponse,
    create_provider
)


class MockLLMProvider(LLMProviderInterface):
    """
    Mock LLM provider for testing.

    Allows simulating different responses without actual API calls:
    - Success responses with valid code
    - Validation failures that trigger retries
    - API errors (timeouts, rate limits)
    - Custom response content
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = None,
        timeout: int = 60,
        response_content: Optional[str] = None,
        should_fail: bool = False,
        fail_count: int = 0
    ):
        """
        Initialize mock provider.

        Args:
            api_key: Mock API key (default: 'mock-key')
            model: Mock model name (default: 'mock-model')
            timeout: Timeout (default: 60)
            response_content: Content to return (default: valid Python code)
            should_fail: If True, always return None (simulate API failure)
            fail_count: Number of times to fail before succeeding
        """
        self.api_key = api_key or 'mock-key'
        self.model = model or 'mock-model'
        self.timeout = timeout
        self.response_content = response_content
        self.should_fail = should_fail
        self.fail_count = fail_count
        self._call_count = 0

    def _get_api_key_from_env(self) -> Optional[str]:
        """Mock environment key retrieval."""
        return 'mock-key'

    def _get_default_model(self) -> str:
        """Mock default model."""
        return 'mock-model'

    def _get_provider_name(self) -> str:
        """Mock provider name."""
        return 'MockProvider'

    def _make_api_call(self, prompt: str, max_tokens: int, temperature: float):
        """Mock API call - not used directly."""
        pass

    def _parse_response(self, response_data):
        """Mock response parsing - not used directly."""
        pass

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> Optional[LLMResponse]:
        """
        Generate mock response.

        Returns None if should_fail is True or call_count < fail_count.
        Otherwise returns mock LLMResponse with configured content.
        """
        self._call_count += 1

        # Simulate failures for first N calls
        if self._call_count <= self.fail_count:
            return None

        # Simulate permanent failure
        if self.should_fail:
            return None

        # Return successful response
        content = self.response_content or self._get_default_response()

        prompt_tokens = len(prompt) // 4  # Rough estimate: 1 token ≈ 4 chars
        completion_tokens = len(content) // 4
        total_tokens = prompt_tokens + completion_tokens  # Sum of both

        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=self.model,
            provider='mock'
        )

    def _get_default_response(self) -> str:
        """Default response with valid Python strategy code."""
        return """
Here's a strategy that combines ROE with momentum:

```python
def strategy(data):
    '''
    ROE + Momentum combination strategy

    Selects stocks with strong fundamentals (ROE > 15%)
    and positive momentum (price above 20-day MA).
    '''
    # Get fundamental data
    roe = data.get('fundamental_features:ROE稅後')

    # Get price data
    close = data.get('price:收盤價')
    ma_20 = close.rolling(20).mean()

    # Combine signals
    fundamental_signal = roe > 15
    momentum_signal = close > ma_20

    return fundamental_signal & momentum_signal
```

This strategy combines quality (high ROE) with momentum (price > MA20).
"""


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_provider():
    """Create basic mock provider."""
    return MockLLMProvider()


@pytest.fixture
def failing_provider():
    """Create mock provider that always fails."""
    return MockLLMProvider(should_fail=True)


@pytest.fixture
def retry_provider():
    """Create mock provider that fails twice then succeeds."""
    return MockLLMProvider(fail_count=2)


@pytest.fixture
def prompt_manager():
    """Create PromptManager for testing."""
    return PromptManager()


@pytest.fixture
def strong_champion_context():
    """Context with strong champion (should select MODIFICATION)."""
    return PromptContext(
        champion_code="""
def strategy(data):
    roe = data.get('fundamental_features:ROE稅後')
    return roe > 15
""",
        champion_metrics={
            "sharpe_ratio": 0.95,
            "max_drawdown": 0.12,
            "win_rate": 0.65,
            "calmar_ratio": 3.2
        },
        target_metric="sharpe_ratio"
    )


@pytest.fixture
def weak_champion_context():
    """Context with weak champion (should select CREATION)."""
    return PromptContext(
        champion_code="""
def strategy(data):
    roe = data.get('fundamental_features:ROE稅後')
    return roe > 15
""",
        champion_metrics={
            "sharpe_ratio": 0.35,
            "max_drawdown": 0.28,
            "win_rate": 0.42
        },
        target_metric="sharpe_ratio"
    )


# ============================================================================
# Integration Tests - PromptManager + MockLLMProvider
# ============================================================================

class TestPromptManagerIntegration:
    """Test PromptManager integrated with mock LLM provider."""

    def test_modification_prompt_with_mock_response(
        self,
        prompt_manager,
        mock_provider,
        strong_champion_context
    ):
        """
        Test complete flow: PromptManager -> MockProvider -> Response

        Verifies:
        - PromptManager selects MODIFICATION for strong champion
        - Mock provider returns valid response
        - Response contains expected code structure
        """
        # Step 1: Generate prompt with PromptManager
        prompt_type, prompt = prompt_manager.select_and_build_prompt(
            strong_champion_context
        )

        assert prompt_type == PromptType.MODIFICATION
        assert len(prompt) > 500  # Substantial prompt

        # Step 2: Send prompt to mock provider
        response = mock_provider.generate(prompt)

        assert response is not None
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 100

        # Step 3: Verify response contains Python code
        assert 'def strategy' in response.content or '```python' in response.content

        # Step 4: Verify token tracking
        assert response.prompt_tokens > 0
        assert response.completion_tokens > 0
        assert response.total_tokens == response.prompt_tokens + response.completion_tokens

    def test_creation_prompt_with_mock_response(
        self,
        prompt_manager,
        mock_provider,
        weak_champion_context
    ):
        """
        Test creation prompt flow with weak champion.

        Verifies:
        - PromptManager selects CREATION for weak champion
        - Mock provider returns novel strategy
        """
        # Step 1: Generate creation prompt
        prompt_type, prompt = prompt_manager.select_and_build_prompt(
            weak_champion_context
        )

        assert prompt_type == PromptType.CREATION

        # Step 2: Get response from mock provider
        response = mock_provider.generate(prompt)

        assert response is not None
        assert 'def strategy' in response.content or '```python' in response.content

    def test_multiple_prompts_track_statistics(
        self,
        prompt_manager,
        mock_provider,
        strong_champion_context,
        weak_champion_context
    ):
        """
        Test that statistics are tracked across multiple generations.

        Verifies:
        - Statistics increment correctly
        - Ratios are calculated properly
        """
        # Generate 3 modification prompts (strong champion)
        for _ in range(3):
            prompt_type, prompt = prompt_manager.select_and_build_prompt(
                strong_champion_context
            )
            response = mock_provider.generate(prompt)
            assert response is not None

        # Generate 2 creation prompts (weak champion)
        for _ in range(2):
            prompt_type, prompt = prompt_manager.select_and_build_prompt(
                weak_champion_context
            )
            response = mock_provider.generate(prompt)
            assert response is not None

        # Verify statistics
        stats = prompt_manager.get_statistics()
        assert stats['total_prompts_generated'] == 5
        assert stats['modification_prompts'] == 3
        assert stats['creation_prompts'] == 2
        assert abs(stats['modification_ratio'] - 0.6) < 0.01
        assert abs(stats['creation_ratio'] - 0.4) < 0.01


class TestDynamicPromptSelection:
    """Test dynamic prompt selection with different champion scenarios."""

    def test_strong_champion_selects_modification(
        self,
        prompt_manager,
        strong_champion_context
    ):
        """Strong champion (Sharpe > 0.8) should select MODIFICATION."""
        prompt_type, prompt = prompt_manager.select_and_build_prompt(
            strong_champion_context
        )

        assert prompt_type == PromptType.MODIFICATION
        assert "champion" in prompt.lower() or "modify" in prompt.lower()

    def test_weak_champion_selects_creation(
        self,
        prompt_manager,
        weak_champion_context
    ):
        """Weak champion (Sharpe < 0.5) should select CREATION."""
        prompt_type, prompt = prompt_manager.select_and_build_prompt(
            weak_champion_context
        )

        assert prompt_type == PromptType.CREATION
        assert "novel" in prompt.lower() or "create" in prompt.lower()

    def test_no_champion_selects_creation(self, prompt_manager):
        """No champion should select CREATION."""
        context = PromptContext(
            champion_approach="Momentum-based exploration",
            innovation_directive="Find profitable strategies"
        )

        prompt_type, prompt = prompt_manager.select_and_build_prompt(context)

        assert prompt_type == PromptType.CREATION

    def test_medium_champion_defaults_modification(self, prompt_manager):
        """Medium champion (0.5 < Sharpe < 0.8) defaults to MODIFICATION."""
        context = PromptContext(
            champion_code="def strategy(data): return data.get('ROE') > 15",
            champion_metrics={"sharpe_ratio": 0.65},
            target_metric="sharpe_ratio"
        )

        prompt_type, _ = prompt_manager.select_and_build_prompt(context)

        assert prompt_type == PromptType.MODIFICATION

    def test_force_type_override(self, prompt_manager, strong_champion_context):
        """Force type should override automatic selection."""
        # Strong champion would normally select MODIFICATION
        # Force CREATION instead
        prompt_type, prompt = prompt_manager.select_and_build_prompt(
            strong_champion_context,
            force_type=PromptType.CREATION
        )

        assert prompt_type == PromptType.CREATION


class TestRetryBehavior:
    """Test retry logic with validation failures."""

    def test_provider_failure_returns_none(self, prompt_manager, failing_provider):
        """
        Test that failing provider returns None.

        Simulates API failure - provider should return None after retries.
        """
        context = PromptContext(
            champion_code="def strategy(data): pass",
            champion_metrics={"sharpe_ratio": 0.85}
        )

        prompt_type, prompt = prompt_manager.select_and_build_prompt(context)
        response = failing_provider.generate(prompt)

        assert response is None

    def test_retry_provider_succeeds_after_failures(
        self,
        prompt_manager,
        retry_provider
    ):
        """
        Test that provider succeeds after configured failures.

        Simulates transient failures (e.g., rate limits) followed by success.
        """
        context = PromptContext(
            champion_code="def strategy(data): pass",
            champion_metrics={"sharpe_ratio": 0.85}
        )

        prompt_type, prompt = prompt_manager.select_and_build_prompt(context)

        # First call fails
        response1 = retry_provider.generate(prompt)
        assert response1 is None

        # Second call fails
        response2 = retry_provider.generate(prompt)
        assert response2 is None

        # Third call succeeds (fail_count=2, so succeeds on 3rd call)
        response3 = retry_provider.generate(prompt)
        assert response3 is not None
        assert isinstance(response3, LLMResponse)

    def test_multiple_attempts_tracked(self, retry_provider):
        """Test that provider tracks call attempts correctly."""
        assert retry_provider._call_count == 0

        # Make 3 calls
        retry_provider.generate("test prompt")
        assert retry_provider._call_count == 1

        retry_provider.generate("test prompt")
        assert retry_provider._call_count == 2

        retry_provider.generate("test prompt")
        assert retry_provider._call_count == 3


class TestCustomResponseContent:
    """Test mock provider with custom response content."""

    def test_custom_response_content(self, prompt_manager):
        """Test that mock provider can return custom content."""
        custom_code = """
def strategy(data):
    '''Custom test strategy'''
    pe_ratio = data.get('fundamental_features:本益比')
    return pe_ratio < 12
"""

        mock_provider = MockLLMProvider(response_content=custom_code)

        context = PromptContext(
            champion_code="def strategy(data): pass",
            champion_metrics={"sharpe_ratio": 0.85}
        )

        prompt_type, prompt = prompt_manager.select_and_build_prompt(context)
        response = mock_provider.generate(prompt)

        assert response is not None
        assert 'Custom test strategy' in response.content
        assert 'pe_ratio' in response.content

    def test_yaml_response_content(self, prompt_manager):
        """Test mock provider with YAML response."""
        yaml_content = """
metadata:
  name: momentum_strategy
  category: momentum

entry_logic:
  type: combination
  conditions:
    - type: momentum
      window: 20
    - type: fundamental
      field: ROE
      threshold: 15
"""

        mock_provider = MockLLMProvider(response_content=yaml_content)

        context = PromptContext(
            champion_code="",
            champion_metrics={"sharpe_ratio": 0.85},
            generation_mode=GenerationMode.YAML
        )

        prompt_type, prompt = prompt_manager.select_and_build_prompt(context)
        response = mock_provider.generate(prompt)

        assert response is not None
        assert 'metadata' in response.content
        assert 'entry_logic' in response.content


class TestCostEstimation:
    """Test cost estimation with mock provider."""

    def test_token_counting(self, mock_provider):
        """Test that mock provider estimates tokens correctly."""
        test_prompt = "Generate a strategy" * 100  # ~400 chars

        response = mock_provider.generate(test_prompt)

        assert response is not None
        assert response.prompt_tokens > 0
        assert response.completion_tokens > 0

        # Rough estimate: 1 token ≈ 4 chars
        expected_prompt_tokens = len(test_prompt) // 4
        assert abs(response.prompt_tokens - expected_prompt_tokens) < 50

    def test_cost_estimation(self, mock_provider):
        """Test cost estimation method."""
        # Mock provider returns 0 cost (not in pricing table)
        cost = mock_provider.estimate_cost(
            prompt_tokens=1000,
            completion_tokens=500
        )

        assert cost == 0.0  # Mock provider has no pricing


class TestPromptQuality:
    """Test that generated prompts meet quality requirements."""

    def test_modification_prompt_includes_context(
        self,
        prompt_manager,
        strong_champion_context
    ):
        """Modification prompt should include champion context."""
        prompt_type, prompt = prompt_manager.select_and_build_prompt(
            strong_champion_context
        )

        assert prompt_type == PromptType.MODIFICATION

        # Should include champion metrics
        assert "0.95" in prompt or "sharpe" in prompt.lower()

        # Should include champion code
        assert "def strategy" in prompt or "ROE" in prompt

    def test_creation_prompt_includes_guidance(self, prompt_manager):
        """Creation prompt should include innovation guidance."""
        context = PromptContext(
            champion_approach="Momentum-based with ROE filter",
            innovation_directive="Explore value + quality combinations",
            failure_history=[
                {"description": "High turnover strategies failed", "error_type": "high_turnover"}
            ]
        )

        prompt_type, prompt = prompt_manager.select_and_build_prompt(context)

        assert prompt_type == PromptType.CREATION

        # Should mention innovation
        assert "novel" in prompt.lower() or "innovation" in prompt.lower()

        # Should include failure patterns
        assert "avoid" in prompt.lower() or "failure" in prompt.lower()

    def test_prompt_token_budget(self, prompt_manager, strong_champion_context):
        """Prompts should stay within token budget (<2000 tokens)."""
        prompt_type, prompt = prompt_manager.select_and_build_prompt(
            strong_champion_context
        )

        # Rough estimate: 1 token ≈ 4 characters
        estimated_tokens = len(prompt) // 4
        assert estimated_tokens < 2000, f"Prompt too long: ~{estimated_tokens} tokens"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_champion_code(self, prompt_manager, mock_provider):
        """Test handling of empty champion code."""
        context = PromptContext(
            champion_code="",
            champion_metrics={"sharpe_ratio": 0.85}
        )

        prompt_type, prompt = prompt_manager.select_and_build_prompt(context)
        response = mock_provider.generate(prompt)

        assert response is not None
        assert len(response.content) > 0

    def test_missing_champion_metrics(self, prompt_manager, mock_provider):
        """Test handling of missing champion metrics."""
        context = PromptContext(
            champion_code="def strategy(data): pass",
            champion_metrics=None
        )

        prompt_type, prompt = prompt_manager.select_and_build_prompt(context)
        response = mock_provider.generate(prompt)

        assert response is not None

    def test_none_failure_history(self, prompt_manager, mock_provider):
        """Test handling of None failure history."""
        context = PromptContext(
            champion_code="def strategy(data): pass",
            champion_metrics={"sharpe_ratio": 0.85},
            failure_history=None
        )

        prompt_type, prompt = prompt_manager.select_and_build_prompt(context)
        response = mock_provider.generate(prompt)

        assert response is not None


class TestEndToEndFlow:
    """Test complete end-to-end flows."""

    def test_complete_modification_flow(
        self,
        prompt_manager,
        mock_provider,
        strong_champion_context
    ):
        """
        Test complete modification flow from context to response.

        Flow:
        1. PromptManager selects MODIFICATION
        2. Builds prompt with champion context
        3. MockProvider generates response
        4. Response contains valid code
        5. Statistics are tracked
        """
        # Step 1: Select and build prompt
        prompt_type, prompt = prompt_manager.select_and_build_prompt(
            strong_champion_context
        )

        assert prompt_type == PromptType.MODIFICATION

        # Step 2: Verify prompt quality
        assert "champion" in prompt.lower() or "current" in prompt.lower()
        assert "0.95" in prompt or "sharpe" in prompt.lower()

        # Step 3: Generate with mock provider
        response = mock_provider.generate(prompt, max_tokens=2000)

        assert response is not None
        assert response.provider == 'mock'

        # Step 4: Verify response
        assert 'def strategy' in response.content or '```python' in response.content

        # Step 5: Check statistics
        stats = prompt_manager.get_statistics()
        assert stats['modification_prompts'] == 1
        assert stats['creation_prompts'] == 0

    def test_complete_creation_flow(
        self,
        prompt_manager,
        mock_provider,
        weak_champion_context
    ):
        """
        Test complete creation flow from context to response.

        Flow:
        1. PromptManager selects CREATION
        2. Builds prompt with innovation guidance
        3. MockProvider generates novel strategy
        4. Response contains valid code
        5. Statistics are tracked
        """
        # Step 1: Select and build prompt
        prompt_type, prompt = prompt_manager.select_and_build_prompt(
            weak_champion_context
        )

        assert prompt_type == PromptType.CREATION

        # Step 2: Verify prompt guides novelty
        assert "novel" in prompt.lower() or "create" in prompt.lower()

        # Step 3: Generate with mock provider
        response = mock_provider.generate(prompt)

        assert response is not None

        # Step 4: Verify response contains strategy
        assert 'def strategy' in response.content or '```python' in response.content

        # Step 5: Check statistics
        stats = prompt_manager.get_statistics()
        assert stats['creation_prompts'] == 1

    def test_fallback_on_provider_failure(
        self,
        prompt_manager,
        failing_provider,
        strong_champion_context
    ):
        """
        Test that system handles provider failures gracefully.

        When provider fails, system should:
        1. Return None
        2. Not crash
        3. Allow fallback to alternative generation method
        """
        # Generate prompt
        prompt_type, prompt = prompt_manager.select_and_build_prompt(
            strong_champion_context
        )

        # Try with failing provider
        response = failing_provider.generate(prompt, max_retries=3)

        # Should fail gracefully
        assert response is None

        # System should still be functional - statistics still work
        stats = prompt_manager.get_statistics()
        assert stats['modification_prompts'] == 1


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    """Run integration tests."""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-k", "test_"
    ])
