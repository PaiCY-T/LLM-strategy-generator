"""Unit tests for LLMConfig dataclass.

Tests configuration loading, validation, and environment variable substitution.

Requirements: 2.1 (LLM configuration)
Task: llm-integration-activation Task 4
"""

import os
import pytest
import tempfile
import yaml
from unittest import mock

from src.innovation.llm_config import LLMConfig


class TestLLMConfigValidation:
    """Test LLMConfig validation in __post_init__."""

    def test_valid_config_openrouter(self):
        """Test valid OpenRouter configuration."""
        config = LLMConfig(
            provider='openrouter',
            model='anthropic/claude-3.5-sonnet',
            api_key='sk-test-key-12345',
            innovation_rate=0.20,
            timeout=60,
            max_tokens=2000,
            temperature=0.7
        )
        assert config.provider == 'openrouter'
        assert config.model == 'anthropic/claude-3.5-sonnet'
        assert config.api_key == 'sk-test-key-12345'

    def test_valid_config_gemini(self):
        """Test valid Gemini configuration."""
        config = LLMConfig(
            provider='gemini',
            model='gemini-2.0-flash-thinking-exp',
            api_key='AIza-test-key',
            innovation_rate=0.15,
            timeout=90,
            max_tokens=4000,
            temperature=0.5
        )
        assert config.provider == 'gemini'
        assert config.innovation_rate == 0.15

    def test_valid_config_openai(self):
        """Test valid OpenAI configuration."""
        config = LLMConfig(
            provider='openai',
            model='gpt-4o',
            api_key='sk-openai-test',
            innovation_rate=0.30,
            timeout=120,
            max_tokens=3000,
            temperature=0.8
        )
        assert config.provider == 'openai'
        assert config.temperature == 0.8

    def test_invalid_provider(self):
        """Test invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Invalid provider 'invalid'"):
            LLMConfig(
                provider='invalid',
                model='some-model',
                api_key='test-key'
            )

    def test_innovation_rate_too_low(self):
        """Test innovation_rate below 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="innovation_rate must be between 0.0 and 1.0"):
            LLMConfig(
                provider='openrouter',
                model='claude',
                api_key='test-key',
                innovation_rate=-0.1
            )

    def test_innovation_rate_too_high(self):
        """Test innovation_rate above 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="innovation_rate must be between 0.0 and 1.0"):
            LLMConfig(
                provider='openrouter',
                model='claude',
                api_key='test-key',
                innovation_rate=1.5
            )

    def test_innovation_rate_boundary_zero(self):
        """Test innovation_rate=0.0 is valid."""
        config = LLMConfig(
            provider='openrouter',
            model='claude',
            api_key='test-key',
            innovation_rate=0.0
        )
        assert config.innovation_rate == 0.0

    def test_innovation_rate_boundary_one(self):
        """Test innovation_rate=1.0 is valid."""
        config = LLMConfig(
            provider='openrouter',
            model='claude',
            api_key='test-key',
            innovation_rate=1.0
        )
        assert config.innovation_rate == 1.0

    def test_innovation_rate_not_number(self):
        """Test innovation_rate as non-number raises ValueError."""
        with pytest.raises(ValueError, match="innovation_rate must be a number"):
            LLMConfig(
                provider='openrouter',
                model='claude',
                api_key='test-key',
                innovation_rate='not-a-number'  # type: ignore
            )

    def test_negative_timeout(self):
        """Test negative timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout must be a positive integer"):
            LLMConfig(
                provider='openrouter',
                model='claude',
                api_key='test-key',
                timeout=-10
            )

    def test_zero_timeout(self):
        """Test zero timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout must be a positive integer"):
            LLMConfig(
                provider='openrouter',
                model='claude',
                api_key='test-key',
                timeout=0
            )

    def test_negative_max_tokens(self):
        """Test negative max_tokens raises ValueError."""
        with pytest.raises(ValueError, match="max_tokens must be a positive integer"):
            LLMConfig(
                provider='openrouter',
                model='claude',
                api_key='test-key',
                max_tokens=-1000
            )

    def test_temperature_too_low(self):
        """Test temperature below 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="temperature must be between 0.0 and 2.0"):
            LLMConfig(
                provider='openrouter',
                model='claude',
                api_key='test-key',
                temperature=-0.5
            )

    def test_temperature_too_high(self):
        """Test temperature above 2.0 raises ValueError."""
        with pytest.raises(ValueError, match="temperature must be between 0.0 and 2.0"):
            LLMConfig(
                provider='openrouter',
                model='claude',
                api_key='test-key',
                temperature=3.0
            )

    def test_temperature_boundary_zero(self):
        """Test temperature=0.0 is valid."""
        config = LLMConfig(
            provider='openrouter',
            model='claude',
            api_key='test-key',
            temperature=0.0
        )
        assert config.temperature == 0.0

    def test_temperature_boundary_two(self):
        """Test temperature=2.0 is valid."""
        config = LLMConfig(
            provider='openrouter',
            model='claude',
            api_key='test-key',
            temperature=2.0
        )
        assert config.temperature == 2.0

    def test_empty_model(self):
        """Test empty model raises ValueError."""
        with pytest.raises(ValueError, match="model must be a non-empty string"):
            LLMConfig(
                provider='openrouter',
                model='',
                api_key='test-key'
            )

    def test_empty_api_key(self):
        """Test empty api_key raises ValueError."""
        with pytest.raises(ValueError, match="api_key must be a non-empty string"):
            LLMConfig(
                provider='openrouter',
                model='claude',
                api_key=''
            )


class TestLLMConfigFromYAML:
    """Test LLMConfig.from_yaml() configuration loading."""

    def test_load_from_yaml_openrouter(self):
        """Test loading OpenRouter config from YAML."""
        yaml_content = """
llm:
  provider: openrouter
  model: anthropic/claude-3.5-sonnet
  innovation_rate: 0.25
  timeout: 90
  max_tokens: 3000
  temperature: 0.8
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with mock.patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key-openrouter'}):
                config = LLMConfig.from_yaml(temp_path)
                assert config.provider == 'openrouter'
                assert config.model == 'anthropic/claude-3.5-sonnet'
                assert config.api_key == 'test-key-openrouter'
                assert config.innovation_rate == 0.25
                assert config.timeout == 90
                assert config.max_tokens == 3000
                assert config.temperature == 0.8
        finally:
            os.unlink(temp_path)

    def test_load_from_yaml_gemini(self):
        """Test loading Gemini config from YAML."""
        yaml_content = """
llm:
  provider: gemini
  model: gemini-2.0-flash-thinking-exp
  innovation_rate: 0.15
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with mock.patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key-google'}):
                config = LLMConfig.from_yaml(temp_path)
                assert config.provider == 'gemini'
                assert config.model == 'gemini-2.0-flash-thinking-exp'
                assert config.api_key == 'test-key-google'
                assert config.innovation_rate == 0.15
                # Defaults
                assert config.timeout == 60
                assert config.max_tokens == 2000
                assert config.temperature == 0.7
        finally:
            os.unlink(temp_path)

    def test_load_from_yaml_gemini_fallback_env(self):
        """Test Gemini uses GEMINI_API_KEY as fallback."""
        yaml_content = """
llm:
  provider: gemini
  model: gemini-2.0-flash-thinking-exp
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Only set GEMINI_API_KEY, not GOOGLE_API_KEY
            with mock.patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key-gemini'}, clear=True):
                config = LLMConfig.from_yaml(temp_path)
                assert config.api_key == 'test-key-gemini'
        finally:
            os.unlink(temp_path)

    def test_load_from_yaml_openai(self):
        """Test loading OpenAI config from YAML."""
        yaml_content = """
llm:
  provider: openai
  model: gpt-4o
  innovation_rate: 0.30
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with mock.patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-openai-test'}):
                config = LLMConfig.from_yaml(temp_path)
                assert config.provider == 'openai'
                assert config.model == 'gpt-4o'
                assert config.api_key == 'sk-openai-test'
        finally:
            os.unlink(temp_path)

    def test_load_from_yaml_default_model(self):
        """Test default model is used when not specified."""
        yaml_content = """
llm:
  provider: openrouter
  innovation_rate: 0.20
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with mock.patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
                config = LLMConfig.from_yaml(temp_path)
                # Should use default model for openrouter
                assert config.model == 'anthropic/claude-3.5-sonnet'
        finally:
            os.unlink(temp_path)

    def test_load_from_yaml_missing_file(self):
        """Test FileNotFoundError for missing config file."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            LLMConfig.from_yaml('/nonexistent/path/config.yaml')

    def test_load_from_yaml_missing_llm_section(self):
        """Test KeyError for missing llm section."""
        yaml_content = """
anti_churn:
  probation_period: 2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(KeyError, match="Missing 'llm' section"):
                LLMConfig.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_from_yaml_missing_provider(self):
        """Test KeyError for missing provider."""
        yaml_content = """
llm:
  model: some-model
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(KeyError, match="Missing 'provider' in llm configuration"):
                LLMConfig.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_from_yaml_invalid_yaml(self):
        """Test yaml.YAMLError for malformed YAML."""
        yaml_content = """
llm:
  provider: openrouter
    invalid: indentation
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(yaml.YAMLError):
                LLMConfig.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_from_yaml_missing_api_key(self):
        """Test ValueError when API key not in environment."""
        yaml_content = """
llm:
  provider: openrouter
  model: claude
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Clear environment variables
            with mock.patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError, match="API key not found for provider 'openrouter'"):
                    LLMConfig.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)


class TestLLMConfigEnvironmentVariables:
    """Test environment variable substitution for API keys."""

    def test_load_api_key_openrouter(self):
        """Test loading OpenRouter API key from environment."""
        with mock.patch.dict(os.environ, {'OPENROUTER_API_KEY': 'sk-or-test'}):
            api_key = LLMConfig._load_api_key('openrouter')
            assert api_key == 'sk-or-test'

    def test_load_api_key_gemini_google(self):
        """Test loading Gemini API key from GOOGLE_API_KEY."""
        with mock.patch.dict(os.environ, {'GOOGLE_API_KEY': 'AIza-google-test'}, clear=True):
            api_key = LLMConfig._load_api_key('gemini')
            assert api_key == 'AIza-google-test'

    def test_load_api_key_gemini_fallback(self):
        """Test loading Gemini API key from GEMINI_API_KEY fallback."""
        with mock.patch.dict(os.environ, {'GEMINI_API_KEY': 'AIza-gemini-test'}, clear=True):
            api_key = LLMConfig._load_api_key('gemini')
            assert api_key == 'AIza-gemini-test'

    def test_load_api_key_gemini_prefer_google(self):
        """Test Gemini prefers GOOGLE_API_KEY over GEMINI_API_KEY."""
        env = {
            'GOOGLE_API_KEY': 'google-key',
            'GEMINI_API_KEY': 'gemini-key'
        }
        with mock.patch.dict(os.environ, env, clear=True):
            api_key = LLMConfig._load_api_key('gemini')
            # Should get the first one in the list (GOOGLE_API_KEY)
            assert api_key == 'google-key'

    def test_load_api_key_openai(self):
        """Test loading OpenAI API key from environment."""
        with mock.patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-openai-test'}):
            api_key = LLMConfig._load_api_key('openai')
            assert api_key == 'sk-openai-test'

    def test_load_api_key_missing(self):
        """Test ValueError when API key not found."""
        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key not found for provider 'openrouter'"):
                LLMConfig._load_api_key('openrouter')

    def test_load_api_key_invalid_provider(self):
        """Test ValueError for invalid provider."""
        with pytest.raises(ValueError, match="Unknown provider 'invalid'"):
            LLMConfig._load_api_key('invalid')


class TestLLMConfigUtilityMethods:
    """Test utility methods (to_dict, __repr__)."""

    def test_to_dict_redacts_api_key(self):
        """Test to_dict() redacts API key."""
        config = LLMConfig(
            provider='openrouter',
            model='claude',
            api_key='super-secret-key',
            innovation_rate=0.25
        )
        config_dict = config.to_dict()
        assert config_dict['api_key'] == '***REDACTED***'
        assert config_dict['provider'] == 'openrouter'
        assert config_dict['model'] == 'claude'
        assert config_dict['innovation_rate'] == 0.25

    def test_repr_redacts_api_key(self):
        """Test __repr__() redacts API key."""
        config = LLMConfig(
            provider='openrouter',
            model='claude',
            api_key='super-secret-key'
        )
        repr_str = repr(config)
        assert 'api_key=\'***REDACTED***\'' in repr_str
        assert 'super-secret-key' not in repr_str
        assert 'provider=\'openrouter\'' in repr_str


class TestLLMConfigDefaults:
    """Test default values for optional parameters."""

    def test_default_innovation_rate(self):
        """Test default innovation_rate is 0.20."""
        config = LLMConfig(
            provider='openrouter',
            model='claude',
            api_key='test-key'
        )
        assert config.innovation_rate == 0.20

    def test_default_timeout(self):
        """Test default timeout is 60 seconds."""
        config = LLMConfig(
            provider='openrouter',
            model='claude',
            api_key='test-key'
        )
        assert config.timeout == 60

    def test_default_max_tokens(self):
        """Test default max_tokens is 2000."""
        config = LLMConfig(
            provider='openrouter',
            model='claude',
            api_key='test-key'
        )
        assert config.max_tokens == 2000

    def test_default_temperature(self):
        """Test default temperature is 0.7."""
        config = LLMConfig(
            provider='openrouter',
            model='claude',
            api_key='test-key'
        )
        assert config.temperature == 0.7


class TestLLMConfigEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_api_key(self):
        """Test API key with many characters is valid."""
        long_key = 'sk-' + 'a' * 500
        config = LLMConfig(
            provider='openrouter',
            model='claude',
            api_key=long_key
        )
        assert config.api_key == long_key

    def test_model_with_special_characters(self):
        """Test model name with slashes and dashes."""
        config = LLMConfig(
            provider='openrouter',
            model='anthropic/claude-3.5-sonnet-20241022',
            api_key='test-key'
        )
        assert config.model == 'anthropic/claude-3.5-sonnet-20241022'

    def test_very_large_timeout(self):
        """Test very large timeout value."""
        config = LLMConfig(
            provider='openrouter',
            model='claude',
            api_key='test-key',
            timeout=3600
        )
        assert config.timeout == 3600

    def test_very_large_max_tokens(self):
        """Test very large max_tokens value."""
        config = LLMConfig(
            provider='openrouter',
            model='claude',
            api_key='test-key',
            max_tokens=100000
        )
        assert config.max_tokens == 100000
