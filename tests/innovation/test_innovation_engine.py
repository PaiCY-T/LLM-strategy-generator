"""
Unit tests for InnovationEngine - LLM-driven innovation with feedback loops

Tests all key functionality with mocked LLM API calls:
- Successful generation flow
- Retry logic on failures
- Validation integration
- Cost tracking
- Error handling

Coverage target: >85%
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Optional

from src.innovation.innovation_engine import (
    InnovationEngine,
    GenerationResult
)
from src.innovation.llm_providers import LLMResponse


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_response():
    """Create a mock successful LLM response."""
    return LLMResponse(
        content="""
Here's an improved strategy:

```python
def strategy(data):
    # Enhanced ROE filter with growth momentum
    roe = data.get('fundamental_features:ROE稅後')
    growth = data.get('fundamental_features:營收成長率')

    # Combine quality and growth
    quality_growth = (roe > 15) & (growth > 0.1)

    # Add liquidity filter
    volume = data.get('price:成交量')
    liquidity = volume.rolling(20).mean() > 150_000_000

    return quality_growth & liquidity
```

This modification adds growth momentum to improve returns while maintaining quality focus.
""",
        prompt_tokens=1500,
        completion_tokens=300,
        total_tokens=1800,
        model='gemini-2.0-flash-thinking-exp',
        provider='gemini'
    )


@pytest.fixture
def mock_failed_llm_response():
    """Create a mock LLM response with no extractable code."""
    return LLMResponse(
        content="I cannot help with that request.",
        prompt_tokens=1500,
        completion_tokens=20,
        total_tokens=1520,
        model='gemini-2.0-flash-thinking-exp',
        provider='gemini'
    )


@pytest.fixture
def mock_invalid_code_response():
    """Create a mock LLM response with dangerous code."""
    return LLMResponse(
        content="""
```python
import subprocess

def strategy(data):
    # Don't do this!
    subprocess.call(['ls', '-la'])
    return True
```
""",
        prompt_tokens=1500,
        completion_tokens=50,
        total_tokens=1550,
        model='gemini-2.0-flash-thinking-exp',
        provider='gemini'
    )


@pytest.fixture
def champion_code():
    """Sample champion code for testing."""
    return """
def strategy(data):
    roe = data.get('fundamental_features:ROE稅後')
    return roe > 15
"""


@pytest.fixture
def champion_metrics():
    """Sample champion metrics for testing."""
    return {
        'sharpe_ratio': 0.85,
        'max_drawdown': 0.15,
        'win_rate': 0.58,
        'calmar_ratio': 2.3
    }


# ============================================================================
# Test Initialization
# ============================================================================

def test_initialization_with_valid_provider():
    """Test InnovationEngine initialization with valid provider."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        mock_provider._get_provider_name.return_value = 'Gemini'
        mock_provider.model = 'gemini-2.0-flash-thinking-exp'
        mock_create.return_value = mock_provider

        engine = InnovationEngine(
            provider_name='gemini',
            max_retries=3,
            temperature=0.7
        )

        assert engine.provider_available is True
        assert engine.max_retries == 3
        assert engine.temperature == 0.7
        assert engine.total_attempts == 0
        assert engine.successful_generations == 0


def test_initialization_with_invalid_provider():
    """Test InnovationEngine initialization with invalid provider (no API key)."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_create.side_effect = ValueError("API key not found")

        engine = InnovationEngine(provider_name='openai')

        assert engine.provider_available is False
        assert engine.provider is None


def test_initialization_creates_components():
    """Test that initialization creates all required components."""
    with patch('src.innovation.innovation_engine.create_provider'):
        engine = InnovationEngine(provider_name='gemini')

        assert engine.prompt_builder is not None
        assert engine.validator is not None
        assert isinstance(engine.generation_history, list)


# ============================================================================
# Test Successful Generation Flow
# ============================================================================

def test_generate_innovation_success(
    mock_llm_response,
    champion_code,
    champion_metrics
):
    """Test successful code generation flow."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        # Mock provider
        mock_provider = Mock()
        mock_provider.generate.return_value = mock_llm_response
        mock_provider.estimate_cost.return_value = 0.0001
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini')

        # Generate innovation
        code = engine.generate_innovation(
            champion_code=champion_code,
            champion_metrics=champion_metrics,
            target_metric='sharpe_ratio'
        )

        # Verify success
        assert code is not None
        assert 'def strategy' in code
        assert 'roe' in code.lower()
        assert engine.successful_generations == 1
        assert engine.total_attempts == 1
        assert engine.failed_generations == 0


def test_generate_innovation_tracks_cost(
    mock_llm_response,
    champion_code,
    champion_metrics
):
    """Test that cost tracking works correctly."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        mock_provider.generate.return_value = mock_llm_response
        mock_provider.estimate_cost.return_value = 0.0005  # $0.0005 per call
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini')

        # Generate innovation
        engine.generate_innovation(
            champion_code=champion_code,
            champion_metrics=champion_metrics
        )

        # Verify cost tracking
        assert engine.total_cost_usd == 0.0005
        assert engine.total_tokens == 1800
        assert len(engine.generation_history) == 1
        assert engine.generation_history[0].cost_usd == 0.0005


def test_generate_innovation_with_failure_history(
    mock_llm_response,
    champion_code,
    champion_metrics
):
    """Test generation with failure history context."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        mock_provider.generate.return_value = mock_llm_response
        mock_provider.estimate_cost.return_value = 0.0001
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini')

        failure_history = [
            {
                'pattern_type': 'parameter_change',
                'description': 'Changing ROE threshold degraded performance',
                'performance_impact': -0.15
            }
        ]

        code = engine.generate_innovation(
            champion_code=champion_code,
            champion_metrics=champion_metrics,
            failure_history=failure_history
        )

        assert code is not None
        # Verify that prompt builder was called with failure history
        mock_provider.generate.assert_called_once()


# ============================================================================
# Test Retry Logic
# ============================================================================

def test_retry_on_code_extraction_failure(
    mock_failed_llm_response,
    mock_llm_response,
    champion_code,
    champion_metrics
):
    """Test retry logic when code extraction fails."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        # First call fails (no code), second succeeds
        mock_provider.generate.side_effect = [
            mock_failed_llm_response,
            mock_llm_response
        ]
        mock_provider.estimate_cost.return_value = 0.0001
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini', max_retries=3)

        code = engine.generate_innovation(
            champion_code=champion_code,
            champion_metrics=champion_metrics
        )

        # Should succeed on retry
        assert code is not None
        assert 'def strategy' in code
        assert mock_provider.generate.call_count == 2
        assert engine.successful_generations == 1


def test_retry_on_validation_failure(
    mock_invalid_code_response,
    mock_llm_response,
    champion_code,
    champion_metrics
):
    """Test retry logic when validation fails."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        # First call returns dangerous code, second returns valid code
        mock_provider.generate.side_effect = [
            mock_invalid_code_response,
            mock_llm_response
        ]
        mock_provider.estimate_cost.return_value = 0.0001
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini', max_retries=3)

        code = engine.generate_innovation(
            champion_code=champion_code,
            champion_metrics=champion_metrics
        )

        # Should succeed on retry with valid code
        assert code is not None
        assert 'subprocess' not in code
        assert mock_provider.generate.call_count == 2
        assert engine.validation_failures == 1


def test_max_retries_exhausted(
    mock_failed_llm_response,
    champion_code,
    champion_metrics
):
    """Test that generation fails after max retries."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        # All attempts fail
        mock_provider.generate.return_value = mock_failed_llm_response
        mock_provider.estimate_cost.return_value = 0.0001
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini', max_retries=2)

        code = engine.generate_innovation(
            champion_code=champion_code,
            champion_metrics=champion_metrics
        )

        # Should fail after retries
        assert code is None
        assert mock_provider.generate.call_count == 2
        assert engine.failed_generations == 1
        assert engine.successful_generations == 0


def test_api_call_failure_retry(champion_code, champion_metrics):
    """Test retry logic when API call fails."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        # First call returns None (API failure), second succeeds
        mock_provider.generate.side_effect = [
            None,
            LLMResponse(
                content='```python\ndef strategy(data): return data.get("price:收盤價") > 100\n```',
                prompt_tokens=1000,
                completion_tokens=50,
                total_tokens=1050,
                model='gemini-2.0-flash-thinking-exp',
                provider='gemini'
            )
        ]
        mock_provider.estimate_cost.return_value = 0.0001
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini', max_retries=3)

        with patch('time.sleep'):  # Mock sleep to speed up test
            code = engine.generate_innovation(
                champion_code=champion_code,
                champion_metrics=champion_metrics
            )

        # Should succeed on retry
        assert code is not None
        assert mock_provider.generate.call_count == 2


# ============================================================================
# Test Validation
# ============================================================================

def test_validate_generated_code_valid():
    """Test validation with valid code."""
    engine = InnovationEngine(provider_name='gemini')

    valid_code = """
def strategy(data):
    roe = data.get('fundamental_features:ROE稅後')
    return roe > 15
"""

    is_valid, errors = engine.validate_generated_code(valid_code)

    assert is_valid is True
    assert len(errors) == 0


def test_validate_generated_code_dangerous_import():
    """Test validation rejects dangerous imports."""
    engine = InnovationEngine(provider_name='gemini')

    dangerous_code = """
import subprocess

def strategy(data):
    subprocess.call(['ls'])
    return True
"""

    is_valid, errors = engine.validate_generated_code(dangerous_code)

    assert is_valid is False
    assert len(errors) > 0
    assert 'subprocess' in errors[0].lower()


def test_validate_generated_code_syntax_error():
    """Test validation detects syntax errors."""
    engine = InnovationEngine(provider_name='gemini')

    invalid_code = """
def strategy(data):
    return data.get('ROE' > 15  # Missing closing parenthesis
"""

    is_valid, errors = engine.validate_generated_code(invalid_code)

    assert is_valid is False
    assert len(errors) > 0
    assert 'syntax' in errors[0].lower()


# ============================================================================
# Test Retry with Feedback
# ============================================================================

def test_retry_with_feedback_success(champion_code, champion_metrics):
    """Test retry_with_feedback method."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        mock_provider.generate.return_value = LLMResponse(
            content='```python\ndef strategy(data): return data.get("price:收盤價") > 100\n```',
            prompt_tokens=1000,
            completion_tokens=50,
            total_tokens=1050,
            model='gemini-2.0-flash-thinking-exp',
            provider='gemini'
        )
        mock_provider.estimate_cost.return_value = 0.0001
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini')

        code = engine.retry_with_feedback(
            error_msg="Syntax error on line 5",
            previous_attempt="def strategy(data): return data.get('ROE' > 15",
            original_champion_code=champion_code,
            original_champion_metrics=champion_metrics
        )

        assert code is not None
        assert 'def strategy' in code


def test_retry_with_feedback_validation_fails(champion_code, champion_metrics):
    """Test retry_with_feedback when validation still fails."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        # Return code that fails validation
        mock_provider.generate.return_value = LLMResponse(
            content='```python\nimport os\ndef strategy(data): return os.system("ls")\n```',
            prompt_tokens=1000,
            completion_tokens=50,
            total_tokens=1050,
            model='gemini-2.0-flash-thinking-exp',
            provider='gemini'
        )
        mock_provider.estimate_cost.return_value = 0.0001
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini')

        code = engine.retry_with_feedback(
            error_msg="Previous validation failed",
            previous_attempt="bad code",
            original_champion_code=champion_code,
            original_champion_metrics=champion_metrics
        )

        assert code is None


# ============================================================================
# Test Statistics and Reporting
# ============================================================================

def test_get_statistics(mock_llm_response, champion_code, champion_metrics):
    """Test statistics reporting."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        mock_provider.generate.return_value = mock_llm_response
        mock_provider.estimate_cost.return_value = 0.0005
        mock_provider._get_provider_name.return_value = 'Gemini'
        mock_provider.model = 'gemini-2.0-flash-thinking-exp'
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini')

        # Generate 2 innovations
        engine.generate_innovation(champion_code, champion_metrics)
        engine.generate_innovation(champion_code, champion_metrics)

        stats = engine.get_statistics()

        assert stats['total_attempts'] == 2
        assert stats['successful_generations'] == 2
        assert stats['failed_generations'] == 0
        assert stats['success_rate'] == 1.0
        assert stats['total_cost_usd'] == 0.001
        assert stats['average_cost_usd'] == 0.0005
        assert stats['provider_name'] == 'Gemini'


def test_get_cost_report(mock_llm_response, champion_code, champion_metrics):
    """Test cost reporting."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        mock_provider.generate.return_value = mock_llm_response
        mock_provider.estimate_cost.return_value = 0.0005
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini')

        engine.generate_innovation(champion_code, champion_metrics)

        cost_report = engine.get_cost_report()

        assert cost_report['total_cost_usd'] == 0.0005
        assert cost_report['total_tokens'] == 1800
        assert cost_report['successful_generations'] == 1
        assert cost_report['average_cost_per_success'] == 0.0005
        assert len(cost_report['cost_breakdown']) == 1


def test_reset_statistics(mock_llm_response, champion_code, champion_metrics):
    """Test statistics reset."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        mock_provider.generate.return_value = mock_llm_response
        mock_provider.estimate_cost.return_value = 0.0005
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini')

        engine.generate_innovation(champion_code, champion_metrics)

        assert engine.total_attempts == 1

        engine.reset_statistics()

        assert engine.total_attempts == 0
        assert engine.successful_generations == 0
        assert engine.total_cost_usd == 0.0
        assert len(engine.generation_history) == 0


# ============================================================================
# Test Error Handling
# ============================================================================

def test_provider_unavailable(champion_code, champion_metrics):
    """Test generation when provider is unavailable."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_create.side_effect = ValueError("No API key")

        engine = InnovationEngine(provider_name='openai')

        code = engine.generate_innovation(
            champion_code=champion_code,
            champion_metrics=champion_metrics
        )

        assert code is None
        assert engine.failed_generations == 1
        assert engine.provider_available is False


def test_prompt_builder_error(champion_code, champion_metrics):
    """Test error handling when prompt building fails."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini')

        # Mock prompt builder to raise exception
        with patch.object(engine.prompt_builder, 'build_modification_prompt') as mock_build:
            mock_build.side_effect = Exception("Prompt build failed")

            code = engine.generate_innovation(
                champion_code=champion_code,
                champion_metrics=champion_metrics
            )

            assert code is None
            assert engine.failed_generations == 1


def test_unexpected_error_during_generation(champion_code, champion_metrics):
    """Test handling of unexpected errors."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        mock_provider.generate.side_effect = RuntimeError("Unexpected error")
        mock_create.return_value = mock_provider

        engine = InnovationEngine(provider_name='gemini', max_retries=2)

        with patch('time.sleep'):  # Speed up test
            code = engine.generate_innovation(
                champion_code=champion_code,
                champion_metrics=champion_metrics
            )

        assert code is None
        assert engine.failed_generations == 1


# ============================================================================
# Test Code Extraction
# ============================================================================

def test_extract_code_from_python_block():
    """Test code extraction from ```python block."""
    engine = InnovationEngine(provider_name='gemini')

    response = """
Here's the code:

```python
def strategy(data):
    return data.get('price:收盤價') > 100
```

This is a simple strategy.
"""

    code = engine._extract_code(response)

    assert code is not None
    assert 'def strategy' in code
    assert 'This is a simple strategy' not in code


def test_extract_code_from_generic_block():
    """Test code extraction from generic ``` block."""
    engine = InnovationEngine(provider_name='gemini')

    response = """
Here's the code:

```
def strategy(data):
    return data.get('price:收盤價') > 100
```
"""

    code = engine._extract_code(response)

    assert code is not None
    assert 'def strategy' in code


def test_extract_code_without_block():
    """Test code extraction when code is not in block."""
    engine = InnovationEngine(provider_name='gemini')

    response = """
def strategy(data):
    return data.get('price:收盤價') > 100

## Explanation
This strategy...
"""

    code = engine._extract_code(response)

    assert code is not None
    assert 'def strategy' in code
    assert 'Explanation' not in code


def test_extract_code_fails_no_code():
    """Test code extraction fails when no code present."""
    engine = InnovationEngine(provider_name='gemini')

    response = "I cannot provide code for that request."

    code = engine._extract_code(response)

    assert code is None


# ============================================================================
# Test Integration
# ============================================================================

def test_full_integration_success_flow(champion_code, champion_metrics):
    """Integration test: Full successful generation flow."""
    with patch('src.innovation.innovation_engine.create_provider') as mock_create:
        mock_provider = Mock()
        mock_provider.generate.return_value = LLMResponse(
            content="""
```python
def strategy(data):
    roe = data.get('fundamental_features:ROE稅後')
    growth = data.get('fundamental_features:營收成長率')
    return (roe > 15) & (growth > 0.1)
```
""",
            prompt_tokens=1500,
            completion_tokens=100,
            total_tokens=1600,
            model='gemini-2.0-flash-thinking-exp',
            provider='gemini'
        )
        mock_provider.estimate_cost.return_value = 0.0003
        mock_provider._get_provider_name.return_value = 'Gemini'
        mock_provider.model = 'gemini-2.0-flash-thinking-exp'
        mock_create.return_value = mock_provider

        engine = InnovationEngine(
            provider_name='gemini',
            max_retries=3,
            temperature=0.7
        )

        # Generate innovation
        code = engine.generate_innovation(
            champion_code=champion_code,
            champion_metrics=champion_metrics,
            failure_history=[
                {'description': 'Avoid overfitting', 'performance_impact': -0.1}
            ],
            target_metric='sharpe_ratio'
        )

        # Verify all aspects
        assert code is not None
        assert 'def strategy' in code
        assert engine.successful_generations == 1
        assert engine.total_attempts == 1
        assert engine.total_cost_usd > 0
        assert engine.total_tokens == 1600

        stats = engine.get_statistics()
        assert stats['success_rate'] == 1.0
        assert stats['provider_name'] == 'Gemini'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.innovation.innovation_engine", "--cov-report=term-missing"])
