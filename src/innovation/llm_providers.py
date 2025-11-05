"""
LLM Provider Interface - Abstract interface for multiple LLM API providers

This module provides a unified interface for interacting with different LLM providers
(OpenRouter, Gemini, OpenAI) with consistent error handling, retry logic, and cost estimation.

Task: LLM Integration Activation - Task 1
Requirements: 2.1, 2.2, 2.3, 2.4
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
import requests


# Provider-specific pricing (USD per 1M tokens)
# Updated as of 2025 - adjust based on actual provider pricing
PRICING = {
    'openrouter': {
        'anthropic/claude-3.5-sonnet': {'input': 3.0, 'output': 15.0},
        'google/gemini-2.5-flash': {'input': 0.075, 'output': 0.30},
        'openai/gpt-4o': {'input': 2.5, 'output': 10.0},
    },
    'gemini': {
        'gemini-2.0-flash-thinking-exp': {'input': 0.0, 'output': 0.0},  # Free tier
        'gemini-2.5-flash': {'input': 0.075, 'output': 0.30},
        'gemini-pro': {'input': 0.50, 'output': 1.50},
    },
    'openai': {
        'gpt-4o': {'input': 2.5, 'output': 10.0},
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'o3-mini': {'input': 1.1, 'output': 4.4},
    }
}


@dataclass
class LLMResponse:
    """Response from LLM API call."""
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    provider: str


class LLMProviderInterface(ABC):
    """
    Abstract base class for LLM API providers.

    All concrete implementations must provide:
    - generate(): Make API call and return response
    - estimate_cost(): Calculate estimated cost for token usage
    - Error handling with 60s timeout
    - Retry logic for rate limits (exponential backoff)
    - Environment variable support for API keys
    """

    def __init__(self, api_key: Optional[str] = None, model: str = None, timeout: int = 60):
        """
        Initialize LLM provider.

        Args:
            api_key: API key for provider (if None, reads from environment)
            model: Model name to use
            timeout: Request timeout in seconds (default 60s)
        """
        self.api_key = api_key or self._get_api_key_from_env()
        self.model = model or self._get_default_model()
        self.timeout = timeout
        self._validate_api_key()

    @abstractmethod
    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment variable. Provider-specific."""
        pass

    @abstractmethod
    def _get_default_model(self) -> str:
        """Get default model name. Provider-specific."""
        pass

    @abstractmethod
    def _get_provider_name(self) -> str:
        """Get provider name for identification."""
        pass

    def _validate_api_key(self):
        """Validate that API key is present."""
        if not self.api_key:
            raise ValueError(
                f"{self._get_provider_name()} API key not found. "
                f"Set via constructor or environment variable."
            )

    @abstractmethod
    def _make_api_call(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """
        Make the actual API call to the provider.

        Args:
            prompt: Input prompt text
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Raw API response as dictionary

        Raises:
            requests.RequestException: On API errors
        """
        pass

    @abstractmethod
    def _parse_response(self, response_data: Dict[str, Any]) -> LLMResponse:
        """
        Parse provider-specific response format into LLMResponse.

        Args:
            response_data: Raw API response

        Returns:
            Parsed LLMResponse object
        """
        pass

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> Optional[LLMResponse]:
        """
        Generate text from LLM with retry logic.

        Args:
            prompt: Input prompt text
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
            max_retries: Maximum retry attempts on rate limits

        Returns:
            LLMResponse object or None if all retries failed
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                # Make API call with timeout
                response_data = self._make_api_call(prompt, max_tokens, temperature)

                # Parse response
                return self._parse_response(response_data)

            except requests.exceptions.Timeout:
                last_exception = f"Request timeout after {self.timeout}s"
                print(f"⚠️  {self._get_provider_name()} API timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    self._exponential_backoff(attempt)

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None

                # Retry on rate limits (429) or server errors (5xx)
                if status_code in [429, 500, 502, 503, 504]:
                    last_exception = f"HTTP {status_code}: {str(e)}"
                    print(f"⚠️  {self._get_provider_name()} API error {status_code} (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        self._exponential_backoff(attempt)
                else:
                    # Don't retry on auth errors (401, 403) or bad requests (400)
                    print(f"❌ {self._get_provider_name()} API error {status_code}: {str(e)}")
                    return None

            except requests.exceptions.RequestException as e:
                last_exception = str(e)
                print(f"⚠️  {self._get_provider_name()} network error (attempt {attempt + 1}/{max_retries}): {type(e).__name__}")
                if attempt < max_retries - 1:
                    self._exponential_backoff(attempt)

            except Exception as e:
                # Unexpected errors - don't retry
                print(f"❌ {self._get_provider_name()} unexpected error: {type(e).__name__}: {str(e)}")
                return None

        # All retries exhausted
        print(f"❌ {self._get_provider_name()} failed after {max_retries} attempts: {last_exception}")
        return None

    def _exponential_backoff(self, attempt: int):
        """Sleep with exponential backoff."""
        sleep_time = 2 ** attempt  # 1s, 2s, 4s, 8s, ...
        time.sleep(sleep_time)

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate API cost for token usage.

        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        provider_name = self._get_provider_name().lower()

        # Get pricing for provider and model
        if provider_name not in PRICING:
            return 0.0

        model_pricing = PRICING[provider_name].get(self.model)
        if not model_pricing:
            # Unknown model - return 0 cost
            return 0.0

        # Calculate cost (pricing is per 1M tokens)
        input_cost = (prompt_tokens / 1_000_000) * model_pricing['input']
        output_cost = (completion_tokens / 1_000_000) * model_pricing['output']

        return input_cost + output_cost


class OpenRouterProvider(LLMProviderInterface):
    """
    OpenRouter API provider.

    Supports multiple models through OpenRouter's unified interface.
    Default model: anthropic/claude-3.5-sonnet
    Environment variable: OPENROUTER_API_KEY
    """

    API_ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'

    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from OPENROUTER_API_KEY environment variable."""
        return os.getenv('OPENROUTER_API_KEY')

    def _get_default_model(self) -> str:
        """Default to Claude 3.5 Sonnet via OpenRouter."""
        return 'anthropic/claude-3.5-sonnet'

    def _get_provider_name(self) -> str:
        """Provider name for identification."""
        return 'OpenRouter'

    def _make_api_call(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Make API call to OpenRouter."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/finlab',  # Optional but recommended
        }

        payload = {
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': temperature,
            'max_tokens': max_tokens,
        }

        response = requests.post(
            self.API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()

        return response.json()

    def _parse_response(self, response_data: Dict[str, Any]) -> LLMResponse:
        """Parse OpenRouter response format."""
        content = response_data['choices'][0]['message']['content']
        usage = response_data.get('usage', {})

        return LLMResponse(
            content=content,
            prompt_tokens=usage.get('prompt_tokens', 0),
            completion_tokens=usage.get('completion_tokens', 0),
            total_tokens=usage.get('total_tokens', 0),
            model=self.model,
            provider='openrouter'
        )


class GeminiProvider(LLMProviderInterface):
    """
    Google Gemini API provider.

    Supports Gemini models through Google's Generative AI API.
    Default model: gemini-2.0-flash-thinking-exp
    Environment variable: GOOGLE_API_KEY or GEMINI_API_KEY
    """

    API_ENDPOINT_TEMPLATE = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'

    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from GOOGLE_API_KEY or GEMINI_API_KEY."""
        return os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')

    def _get_default_model(self) -> str:
        """Default to Gemini 2.0 Flash (non-thinking variant for faster response)."""
        return 'gemini-2.0-flash-exp'

    def _get_provider_name(self) -> str:
        """Provider name for identification."""
        return 'Gemini'

    def _make_api_call(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Make API call to Gemini."""
        url = self.API_ENDPOINT_TEMPLATE.format(model=self.model)

        headers = {
            'Content-Type': 'application/json',
        }

        payload = {
            'contents': [{
                'parts': [{'text': prompt}]
            }],
            'generationConfig': {
                'temperature': temperature,
                'maxOutputTokens': max_tokens,
            }
        }

        params = {'key': self.api_key}

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()

        return response.json()

    def _parse_response(self, response_data: Dict[str, Any]) -> LLMResponse:
        """Parse Gemini response format."""
        # Gemini response structure
        candidates = response_data.get('candidates', [])
        if not candidates:
            raise ValueError("No candidates in Gemini response")

        # Safely extract content with defensive checks
        candidate = candidates[0]

        # Check for 'content' key
        if 'content' not in candidate:
            raise ValueError(f"Missing 'content' in Gemini candidate: {candidate}")

        content_obj = candidate['content']

        # Check for 'parts' key
        if 'parts' not in content_obj:
            raise ValueError(f"Missing 'parts' in Gemini content: {content_obj}")

        parts = content_obj['parts']
        if not parts:
            raise ValueError("Empty 'parts' array in Gemini response")

        # Check for 'text' key
        if 'text' not in parts[0]:
            raise ValueError(f"Missing 'text' in Gemini part: {parts[0]}")

        content = parts[0]['text']

        # Token usage metadata (if available)
        usage_metadata = response_data.get('usageMetadata', {})
        prompt_tokens = usage_metadata.get('promptTokenCount', 0)
        completion_tokens = usage_metadata.get('candidatesTokenCount', 0)
        total_tokens = usage_metadata.get('totalTokenCount', prompt_tokens + completion_tokens)

        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=self.model,
            provider='gemini'
        )


class OpenAIProvider(LLMProviderInterface):
    """
    OpenAI API provider.

    Supports GPT-4, GPT-4o, o3, and other OpenAI models.
    Default model: gpt-4o
    Environment variable: OPENAI_API_KEY
    """

    API_ENDPOINT = 'https://api.openai.com/v1/chat/completions'

    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from OPENAI_API_KEY environment variable."""
        return os.getenv('OPENAI_API_KEY')

    def _get_default_model(self) -> str:
        """Default to GPT-4o."""
        return 'gpt-4o'

    def _get_provider_name(self) -> str:
        """Provider name for identification."""
        return 'OpenAI'

    def _make_api_call(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Make API call to OpenAI."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        payload = {
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': temperature,
            'max_tokens': max_tokens,
        }

        response = requests.post(
            self.API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()

        return response.json()

    def _parse_response(self, response_data: Dict[str, Any]) -> LLMResponse:
        """Parse OpenAI response format."""
        content = response_data['choices'][0]['message']['content']
        usage = response_data.get('usage', {})

        return LLMResponse(
            content=content,
            prompt_tokens=usage.get('prompt_tokens', 0),
            completion_tokens=usage.get('completion_tokens', 0),
            total_tokens=usage.get('total_tokens', 0),
            model=self.model,
            provider='openai'
        )


# Factory function for convenience
def create_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout: int = 60
) -> LLMProviderInterface:
    """
    Factory function to create LLM provider.

    Args:
        provider_name: Provider name ('openrouter', 'gemini', 'openai')
        api_key: API key (if None, reads from environment)
        model: Model name (if None, uses provider default)
        timeout: Request timeout in seconds

    Returns:
        Concrete LLMProviderInterface implementation

    Raises:
        ValueError: If provider_name is not supported
    """
    provider_name = provider_name.lower()

    providers = {
        'openrouter': OpenRouterProvider,
        'gemini': GeminiProvider,
        'openai': OpenAIProvider,
    }

    if provider_name not in providers:
        raise ValueError(
            f"Unsupported provider: {provider_name}. "
            f"Supported providers: {', '.join(providers.keys())}"
        )

    provider_class = providers[provider_name]
    return provider_class(api_key=api_key, model=model, timeout=timeout)


if __name__ == "__main__":
    """Example usage and basic testing."""

    print("=" * 80)
    print("LLM PROVIDER INTERFACE - Example Usage")
    print("=" * 80)

    # Example 1: Create provider with explicit API key
    print("\nExample 1: Create OpenRouter provider")
    print("-" * 80)
    try:
        provider = create_provider('openrouter')
        print(f"✅ Created {provider._get_provider_name()} provider")
        print(f"   Model: {provider.model}")
        print(f"   Timeout: {provider.timeout}s")
    except ValueError as e:
        print(f"⚠️  {e}")

    # Example 2: Estimate cost
    print("\nExample 2: Estimate API cost")
    print("-" * 80)
    try:
        provider = create_provider('gemini')
        cost = provider.estimate_cost(prompt_tokens=1000, completion_tokens=500)
        print(f"✅ Estimated cost for 1000 input + 500 output tokens: ${cost:.4f}")
    except ValueError as e:
        print(f"⚠️  {e}")

    # Example 3: Make API call (only if API key is set)
    print("\nExample 3: Test API call (requires API key)")
    print("-" * 80)

    # Try each provider in order of preference
    for provider_name in ['gemini', 'openrouter', 'openai']:
        try:
            provider = create_provider(provider_name)
            print(f"Testing {provider._get_provider_name()}...")

            response = provider.generate(
                prompt="What is 2+2? Answer in one sentence.",
                max_tokens=50,
                temperature=0.0
            )

            if response:
                print(f"✅ {provider._get_provider_name()} API call successful")
                print(f"   Response: {response.content[:100]}...")
                print(f"   Tokens: {response.prompt_tokens} input, {response.completion_tokens} output")
                cost = provider.estimate_cost(response.prompt_tokens, response.completion_tokens)
                print(f"   Estimated cost: ${cost:.6f}")
                break
            else:
                print(f"❌ {provider._get_provider_name()} API call failed")

        except ValueError as e:
            print(f"⚠️  {provider_name}: {e}")

    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETE")
    print("=" * 80)
