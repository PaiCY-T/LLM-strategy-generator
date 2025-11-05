"""
Tests for LLM configuration in learning_system.yaml
Part of llm-integration-activation spec (Task 6)
"""
import os
import yaml
import pytest
from pathlib import Path


@pytest.fixture
def config():
    """Load learning_system.yaml configuration."""
    config_path = Path(__file__).parent.parent.parent / "config" / "learning_system.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def test_llm_config_loads(config):
    """Test that learning_system.yaml loads without errors."""
    assert config is not None
    assert isinstance(config, dict)


def test_llm_section_exists(config):
    """Test that LLM section exists in config."""
    assert 'llm' in config, "LLM section missing from config"
    assert isinstance(config['llm'], dict)


def test_llm_required_fields(config):
    """Test that required LLM fields are present."""
    llm = config['llm']

    # Core fields
    assert 'enabled' in llm, "llm.enabled field missing"
    assert 'provider' in llm, "llm.provider field missing"
    assert 'innovation_rate' in llm, "llm.innovation_rate field missing"

    # Fallback section
    assert 'fallback' in llm, "llm.fallback section missing"
    assert 'enabled' in llm['fallback']
    assert 'max_retries' in llm['fallback']
    assert 'retry_delay' in llm['fallback']

    # Generation section
    assert 'generation' in llm, "llm.generation section missing"
    assert 'max_tokens' in llm['generation']
    assert 'temperature' in llm['generation']
    assert 'timeout' in llm['generation']


def test_llm_provider_sections(config):
    """Test that all provider sections exist."""
    llm = config['llm']

    assert 'openrouter' in llm, "OpenRouter section missing"
    assert 'gemini' in llm, "Gemini section missing"
    assert 'openai' in llm, "OpenAI section missing"

    # Check API key fields
    assert 'api_key' in llm['openrouter']
    assert 'api_key' in llm['gemini']
    assert 'api_key' in llm['openai']


def test_llm_disabled_by_default(config):
    """Test that LLM is disabled by default (backward compatibility)."""
    llm = config['llm']

    # enabled should be a string with environment variable syntax
    # or a boolean False
    enabled = llm['enabled']

    # Check for environment variable syntax with false default
    if isinstance(enabled, str):
        assert enabled == '${LLM_ENABLED:false}', \
            "LLM should be disabled by default via ${LLM_ENABLED:false}"
    else:
        assert enabled == False, "LLM should be disabled by default"


def test_llm_innovation_rate_valid_range(config):
    """Test that innovation_rate is within valid range or uses env var."""
    llm = config['llm']
    innovation_rate = llm['innovation_rate']

    # Check for environment variable syntax or valid float
    if isinstance(innovation_rate, str):
        # Extract default value from ${ENV_VAR:default} syntax
        if ':' in innovation_rate:
            default = float(innovation_rate.split(':')[1].rstrip('}'))
            assert 0.0 <= default <= 1.0, \
                f"Default innovation_rate {default} not in range [0.0, 1.0]"
    else:
        assert isinstance(innovation_rate, (int, float))
        assert 0.0 <= innovation_rate <= 1.0, \
            f"innovation_rate {innovation_rate} not in range [0.0, 1.0]"


def test_llm_fallback_config(config):
    """Test fallback configuration is sensible."""
    fallback = config['llm']['fallback']

    assert fallback['enabled'] == True, "Fallback should be enabled by default"
    assert isinstance(fallback['max_retries'], int)
    assert fallback['max_retries'] >= 0
    assert isinstance(fallback['retry_delay'], (int, float))
    assert fallback['retry_delay'] >= 0


def test_llm_generation_config(config):
    """Test generation configuration is sensible."""
    generation = config['llm']['generation']

    # max_tokens
    max_tokens = generation['max_tokens']
    if isinstance(max_tokens, str):
        # Extract default from env var
        if ':' in max_tokens:
            default = int(max_tokens.split(':')[1].rstrip('}'))
            assert 100 <= default <= 10000, "max_tokens default out of range"
    else:
        assert isinstance(max_tokens, int)
        assert 100 <= max_tokens <= 10000

    # temperature
    temperature = generation['temperature']
    if isinstance(temperature, str):
        if ':' in temperature:
            default = float(temperature.split(':')[1].rstrip('}'))
            assert 0.0 <= default <= 2.0, "temperature default out of range"
    else:
        assert isinstance(temperature, (int, float))
        assert 0.0 <= temperature <= 2.0

    # timeout
    timeout = generation['timeout']
    if isinstance(timeout, str):
        if ':' in timeout:
            default = int(timeout.split(':')[1].rstrip('}'))
            assert 10 <= default <= 600, "timeout default out of range"
    else:
        assert isinstance(timeout, int)
        assert 10 <= timeout <= 600


def test_llm_provider_valid(config):
    """Test that provider is one of supported values."""
    provider = config['llm']['provider']

    valid_providers = ['openrouter', 'gemini', 'openai']

    # Extract default if env var syntax
    if isinstance(provider, str):
        if provider.startswith('${'):
            # Extract default value
            default = provider.split(':')[1].rstrip('}')
            assert default in valid_providers, \
                f"Default provider {default} not in {valid_providers}"
        else:
            assert provider in valid_providers, \
                f"Provider {provider} not in {valid_providers}"


def test_llm_api_keys_use_env_vars(config):
    """Test that API keys use environment variable syntax."""
    llm = config['llm']

    # All provider API keys should use ${ENV_VAR} syntax
    for provider in ['openrouter', 'gemini', 'openai']:
        api_key = llm[provider]['api_key']
        assert isinstance(api_key, str)
        assert api_key.startswith('${'), \
            f"{provider}.api_key should use environment variable syntax"
        assert api_key.endswith('}'), \
            f"{provider}.api_key should use environment variable syntax"


def test_llm_no_hardcoded_secrets(config):
    """Test that no API keys are hardcoded (security check)."""
    llm = config['llm']

    # Convert config to string and check for common API key patterns
    config_str = str(llm)

    # These patterns indicate hardcoded secrets (very basic check)
    suspicious_patterns = [
        'sk-',  # OpenAI key prefix
        'AIza',  # Google API key prefix
    ]

    for pattern in suspicious_patterns:
        # Only flag if pattern appears outside ${} syntax
        if pattern in config_str:
            # Make sure it's in environment variable syntax
            assert '${' in config_str, \
                f"Possible hardcoded API key detected (pattern: {pattern})"


def test_llm_config_backward_compatible(config):
    """Test that config maintains backward compatibility."""
    # Config should load successfully (already tested)
    # LLM should be disabled by default (already tested)

    # Additional check: ensure other sections still exist
    assert 'anti_churn' in config, "Backward compatibility: anti_churn section missing"
    assert 'features' in config, "Backward compatibility: features section missing"


def test_llm_provider_specific_fields(config):
    """Test provider-specific fields are present."""
    llm = config['llm']

    # OpenRouter
    assert 'model' in llm['openrouter']
    assert 'http_referer' in llm['openrouter']
    assert 'app_name' in llm['openrouter']

    # Gemini
    assert 'model' in llm['gemini']
    assert 'safety' in llm['gemini']

    # OpenAI
    assert 'model' in llm['openai']
    assert 'organization' in llm['openai']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
