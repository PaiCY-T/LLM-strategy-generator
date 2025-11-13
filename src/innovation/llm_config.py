"""LLM Configuration Management for Innovation Engine.

Centralized configuration management for LLM API providers with YAML loading,
validation, and environment variable substitution for API keys.

Requirements: 2.1 (LLM configuration)
Task: llm-integration-activation Task 4
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, Optional, Any


@dataclass
class LLMConfig:
    """LLM configuration dataclass with validation.

    Loads configuration from config/learning_system.yaml and validates all
    parameters. Supports environment variable substitution for API keys.

    Attributes:
        provider: LLM provider name (openrouter/gemini/openai)
        model: Model name to use for the provider
        api_key: API key loaded from environment variable
        innovation_rate: Probability of using LLM vs Factor Graph (0.0-1.0)
        timeout: API call timeout in seconds
        max_tokens: Maximum tokens for LLM response
        temperature: Sampling temperature for LLM generation

    Environment Variables:
        - openrouter: OPENROUTER_API_KEY
        - gemini: GOOGLE_API_KEY or GEMINI_API_KEY
        - openai: OPENAI_API_KEY

    Example:
        >>> config = LLMConfig.from_yaml("config/learning_system.yaml")
        >>> print(f"Provider: {config.provider}, Model: {config.model}")
        Provider: openrouter, Model: anthropic/claude-3.5-sonnet
    """

    provider: str
    model: str
    api_key: str
    innovation_rate: float = 0.20
    timeout: int = 60
    max_tokens: int = 2000
    temperature: float = 0.7

    # Valid provider names
    VALID_PROVIDERS = ['openrouter', 'gemini', 'openai']

    # Environment variable mappings
    ENV_VAR_MAPPING = {
        'openrouter': 'OPENROUTER_API_KEY',
        'gemini': ['GOOGLE_API_KEY', 'GEMINI_API_KEY'],  # Try both
        'openai': 'OPENAI_API_KEY',
    }

    # Default models per provider
    DEFAULT_MODELS = {
        'openrouter': 'anthropic/claude-3.5-sonnet',
        'gemini': 'gemini-2.0-flash-thinking-exp',
        'openai': 'gpt-4o',
    }

    def __post_init__(self) -> None:
        """Validate configuration after initialization.

        Raises:
            ValueError: If any configuration parameter is invalid
        """
        # Validate provider
        if self.provider not in self.VALID_PROVIDERS:
            raise ValueError(
                f"Invalid provider '{self.provider}'. "
                f"Must be one of: {', '.join(self.VALID_PROVIDERS)}"
            )

        # Validate innovation_rate
        if not isinstance(self.innovation_rate, (int, float)):
            raise ValueError(
                f"innovation_rate must be a number, got {type(self.innovation_rate).__name__}"
            )

        if not (0.0 <= self.innovation_rate <= 1.0):
            raise ValueError(
                f"innovation_rate must be between 0.0 and 1.0, got {self.innovation_rate}"
            )

        # Validate timeout
        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise ValueError(
                f"timeout must be a positive integer, got {self.timeout}"
            )

        # Validate max_tokens
        if not isinstance(self.max_tokens, int) or self.max_tokens <= 0:
            raise ValueError(
                f"max_tokens must be a positive integer, got {self.max_tokens}"
            )

        # Validate temperature
        if not isinstance(self.temperature, (int, float)):
            raise ValueError(
                f"temperature must be a number, got {type(self.temperature).__name__}"
            )

        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError(
                f"temperature must be between 0.0 and 2.0, got {self.temperature}"
            )

        # Validate model is not empty
        if not self.model or not isinstance(self.model, str):
            raise ValueError(
                f"model must be a non-empty string, got {self.model}"
            )

        # Validate api_key is not empty
        if not self.api_key or not isinstance(self.api_key, str):
            raise ValueError(
                f"api_key must be a non-empty string. "
                f"Ensure environment variable is set for provider '{self.provider}'"
            )

    @classmethod
    def from_yaml(cls, config_path: str = "config/learning_system.yaml") -> 'LLMConfig':
        """Load LLM configuration from YAML file.

        Args:
            config_path: Path to learning_system.yaml configuration file.
                        Can be absolute or relative to project root.

        Returns:
            LLMConfig instance with validated configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is malformed
            ValueError: If configuration is missing or invalid
            KeyError: If required configuration keys are missing

        Example:
            >>> config = LLMConfig.from_yaml("config/learning_system.yaml")
            >>> assert config.provider in ['openrouter', 'gemini', 'openai']
        """
        # Handle both absolute and relative paths
        if not os.path.isabs(config_path):
            # Try relative to project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            config_path = os.path.join(project_root, config_path)

        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Expected location: config/learning_system.yaml"
            )

        # Load YAML configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            raise yaml.YAMLError(
                f"Invalid config format: expected dict, got {type(config).__name__}"
            )

        # Extract LLM configuration section
        if 'llm' not in config:
            raise KeyError(
                "Missing 'llm' section in configuration file. "
                "Add 'llm' section with provider, model, and innovation_rate."
            )

        llm_config = config['llm']

        # Extract provider
        if 'provider' not in llm_config:
            raise KeyError(
                "Missing 'provider' in llm configuration. "
                "Must specify one of: openrouter, gemini, openai"
            )

        provider = llm_config['provider']

        # Get model (use default if not specified)
        model = llm_config.get('model', cls.DEFAULT_MODELS.get(provider))
        if not model:
            raise ValueError(
                f"No model specified for provider '{provider}' and no default available"
            )

        # Load API key from environment variable
        api_key = cls._load_api_key(provider)

        # Extract optional parameters with defaults
        innovation_rate = llm_config.get('innovation_rate', 0.20)
        timeout = llm_config.get('timeout', 60)
        max_tokens = llm_config.get('max_tokens', 2000)
        temperature = llm_config.get('temperature', 0.7)

        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            innovation_rate=innovation_rate,
            timeout=timeout,
            max_tokens=max_tokens,
            temperature=temperature
        )

    @classmethod
    def _load_api_key(cls, provider: str) -> str:
        """Load API key from environment variable based on provider.

        Args:
            provider: LLM provider name (openrouter/gemini/openai)

        Returns:
            API key from environment variable

        Raises:
            ValueError: If provider is invalid or API key not found

        Example:
            >>> os.environ['OPENROUTER_API_KEY'] = 'test-key'
            >>> key = LLMConfig._load_api_key('openrouter')
            >>> assert key == 'test-key'
        """
        if provider not in cls.ENV_VAR_MAPPING:
            raise ValueError(
                f"Unknown provider '{provider}'. "
                f"Must be one of: {', '.join(cls.VALID_PROVIDERS)}"
            )

        env_vars = cls.ENV_VAR_MAPPING[provider]

        # Handle both single env var and list of env vars
        if isinstance(env_vars, str):
            env_vars = [env_vars]

        # Try each environment variable
        for env_var in env_vars:
            api_key = os.getenv(env_var)
            if api_key:
                return api_key

        # None found
        env_var_list = ' or '.join(env_vars)
        raise ValueError(
            f"API key not found for provider '{provider}'. "
            f"Set environment variable: {env_var_list}"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration (api_key redacted)

        Example:
            >>> config = LLMConfig(provider='openrouter', model='claude', api_key='secret')
            >>> d = config.to_dict()
            >>> assert d['api_key'] == '***REDACTED***'
        """
        return {
            'provider': self.provider,
            'model': self.model,
            'api_key': '***REDACTED***',  # Never expose API key
            'innovation_rate': self.innovation_rate,
            'timeout': self.timeout,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
        }

    def __repr__(self) -> str:
        """String representation with redacted API key.

        Returns:
            String representation

        Example:
            >>> config = LLMConfig(provider='openrouter', model='claude', api_key='secret')
            >>> 'api_key=***' in repr(config)
            True
        """
        return (
            f"LLMConfig("
            f"provider='{self.provider}', "
            f"model='{self.model}', "
            f"api_key='***REDACTED***', "
            f"innovation_rate={self.innovation_rate}, "
            f"timeout={self.timeout}, "
            f"max_tokens={self.max_tokens}, "
            f"temperature={self.temperature})"
        )
