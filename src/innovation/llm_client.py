"""
LLM API Client - Unified interface for multiple LLM providers

Supports OpenRouter, Google Gemini, OpenAI o3, and other providers.
Provides retry logic, error handling, and response parsing.
"""

import os
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import requests


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str  # 'openrouter', 'gemini', 'openai'
    model: str     # 'gpt-4', 'gemini-pro', 'o3-mini', etc.
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30


class LLMClient:
    """Unified LLM client supporting multiple providers with automatic fallback."""

    def __init__(self, config: LLMConfig, fallback_config: Optional[LLMConfig] = None):
        """
        Initialize LLM client with optional fallback.

        Args:
            config: Primary LLM provider configuration
            fallback_config: Optional fallback provider (e.g., OpenRouter when Gemini quota exceeded)
        """
        self.config = config
        self.provider = config.provider.lower()
        self.fallback_config = fallback_config
        self._quota_exhausted = False  # Track if primary API quota is exhausted

        # Provider-specific endpoints
        self.endpoints = {
            'openrouter': 'https://openrouter.ai/api/v1/chat/completions',
            'openai': 'https://api.openai.com/v1/chat/completions',
            'gemini': 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
        }

    def generate(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        Generate text from LLM with automatic fallback.

        Implements quota-aware switching:
        1. Try primary provider (e.g., Gemini)
        2. If quota exhausted (429/rate limit), switch to fallback (e.g., OpenRouter)
        3. Retry with exponential backoff for transient errors

        Args:
            prompt: Input prompt
            max_retries: Maximum retry attempts per provider

        Returns:
            Generated text or None if all providers failed
        """
        # Try primary provider (unless quota already exhausted)
        if not self._quota_exhausted:
            for attempt in range(max_retries):
                try:
                    response = self._call_provider(self.config, self.provider, prompt)
                    return response

                except Exception as e:
                    error_str = str(e)

                    # Check for quota/rate limit errors
                    if '429' in error_str or 'quota' in error_str.lower() or 'rate' in error_str.lower():
                        print(f"⚠️  {self.provider.upper()} quota exhausted: {e}")
                        self._quota_exhausted = True
                        break  # Don't retry, switch to fallback immediately

                    # Network/transient errors - retry with backoff
                    print(f"⚠️  {self.provider.upper()} API call failed (attempt {attempt + 1}/{max_retries}): {type(e).__name__}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        # No more retries for primary provider
                        if not self.fallback_config:
                            return None

        # Try fallback provider if available
        if self.fallback_config:
            fallback_provider = self.fallback_config.provider.lower()
            print(f"🔄 Switching to fallback provider: {fallback_provider.upper()}")

            for attempt in range(max_retries):
                try:
                    response = self._call_provider(self.fallback_config, fallback_provider, prompt)
                    return response

                except Exception as e:
                    print(f"⚠️  {fallback_provider.upper()} API call failed (attempt {attempt + 1}/{max_retries}): {type(e).__name__}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff

        # All providers failed
        return None

    def _call_provider(self, config: LLMConfig, provider: str, prompt: str) -> str:
        """Call specific LLM provider with given configuration."""
        if provider == 'openrouter':
            return self._call_openrouter(prompt, config)
        elif provider == 'gemini':
            return self._call_gemini(prompt, config)
        elif provider == 'openai':
            return self._call_openai(prompt, config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _call_openrouter(self, prompt: str, config: LLMConfig) -> str:
        """Call OpenRouter API."""
        headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': config.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': config.temperature,
            'max_tokens': config.max_tokens
        }

        response = requests.post(
            self.endpoints['openrouter'],
            headers=headers,
            json=payload,
            timeout=config.timeout
        )
        response.raise_for_status()

        data = response.json()
        return data['choices'][0]['message']['content']

    def _call_gemini(self, prompt: str, config: LLMConfig) -> str:
        """Call Google Gemini API with robust error handling."""
        url = self.endpoints['gemini'].format(model=config.model)

        headers = {
            'Content-Type': 'application/json'
        }

        payload = {
            'contents': [{
                'parts': [{'text': prompt}]
            }],
            'generationConfig': {
                'temperature': config.temperature,
                'maxOutputTokens': config.max_tokens
            }
        }

        params = {'key': config.api_key}

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            params=params,
            timeout=config.timeout
        )
        response.raise_for_status()

        data = response.json()

        # Robust response validation
        if not data.get('candidates'):
            raise ValueError("Gemini API returned empty candidates (rate limit or quota exceeded)")

        candidate = data['candidates'][0]

        # Check for safety filter blocking
        if 'content' not in candidate:
            finish_reason = candidate.get('finishReason', 'UNKNOWN')
            raise ValueError(f"Gemini API blocked response: {finish_reason}")

        content = candidate['content']
        if not content or 'parts' not in content or not content['parts']:
            raise ValueError("Gemini API returned empty content")

        text = content['parts'][0].get('text', '')
        if not text.strip():
            raise ValueError("Gemini API returned empty text")

        return text

    def _call_openai(self, prompt: str, config: LLMConfig) -> str:
        """Call OpenAI API (o3, GPT-4, etc.)."""
        headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': config.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': config.temperature,
            'max_tokens': config.max_tokens
        }

        response = requests.post(
            self.endpoints['openai'],
            headers=headers,
            json=payload,
            timeout=config.timeout
        )
        response.raise_for_status()

        data = response.json()
        return data['choices'][0]['message']['content']


class MockLLMClient:
    """Mock LLM client for testing without API calls."""

    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize mock client."""
        self.config = config
        self.call_count = 0

    def generate(self, prompt: str, max_retries: int = 3) -> str:
        """
        Generate mock response.

        Returns realistic factor code and rationale for testing.
        """
        self.call_count += 1

        # Generate different mock responses based on call count
        mock_responses = [
            """```python
# Factor Code
factor = data.get('fundamental_features:ROE稅後') / data.get('fundamental_features:淨值比').replace(0, np.nan)

# Rationale
# Quality-adjusted value factor identifying companies with high ROE relative to price-to-book ratio, indicating undervalued quality stocks with strong fundamentals.
```""",
            """```python
# Factor Code
factor = data.get('price:收盤價').rolling(20).mean() / data.get('price:收盤價').rolling(50).mean()

# Rationale
# Moving average crossover strategy capturing momentum when short-term trend exceeds long-term trend, indicating bullish market conditions.
```""",
            """```python
# Factor Code
factor = (data.get('fundamental_features:營收成長率') * data.get('fundamental_features:營業毛利率')) / data.get('fundamental_features:本益比').replace(0, np.nan)

# Rationale
# Growth-margin-value composite identifying companies with strong revenue growth and margins at reasonable valuations.
```"""
        ]

        # Cycle through responses
        return mock_responses[(self.call_count - 1) % len(mock_responses)]


def create_llm_client(use_mock: bool = False) -> LLMClient:
    """
    Factory function to create LLM client with automatic fallback.

    Args:
        use_mock: If True, return MockLLMClient for testing

    Returns:
        LLMClient or MockLLMClient instance with fallback configuration

    Notes:
        - If GOOGLE_API_KEY is set, uses Gemini with OpenRouter as fallback
        - If only OPENROUTER_API_KEY is set, uses OpenRouter directly
        - If only OPENAI_API_KEY is set, uses OpenAI directly
    """
    if use_mock:
        return MockLLMClient()

    # Try to get API key from environment
    # Priority: GOOGLE (with OpenRouter fallback) > OPENROUTER > OPENAI
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    google_key = os.getenv('GOOGLE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    # Strategy: Use Gemini (free) with OpenRouter (paid) as fallback
    if google_key:
        primary_config = LLMConfig(
            provider='gemini',
            model='gemini-2.5-flash',
            api_key=google_key,
            temperature=0.7,
            max_tokens=2000
        )

        # Set up OpenRouter as fallback if available
        fallback_config = None
        if openrouter_key:
            fallback_config = LLMConfig(
                provider='openrouter',
                model='google/gemini-2.5-flash',
                api_key=openrouter_key,
                temperature=0.7,
                max_tokens=2000
            )
            print("✅ Using Gemini (free) with OpenRouter fallback")
        else:
            print("✅ Using Gemini (free) without fallback")

        return LLMClient(primary_config, fallback_config=fallback_config)

    elif openrouter_key:
        config = LLMConfig(
            provider='openrouter',
            model='google/gemini-2.5-flash',  # Fast and capable
            api_key=openrouter_key,
            temperature=0.7,
            max_tokens=2000
        )
        print("✅ Using OpenRouter (paid)")
        return LLMClient(config)

    elif openai_key:
        config = LLMConfig(
            provider='openai',
            model='o3-mini',
            api_key=openai_key,
            temperature=0.7,
            max_tokens=2000
        )
        print("✅ Using OpenAI")
        return LLMClient(config)

    else:
        print("⚠️  No LLM API key found. Using mock client.")
        print("   Set OPENROUTER_API_KEY, GOOGLE_API_KEY, or OPENAI_API_KEY to use real LLM.")
        return MockLLMClient()


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("TESTING LLM CLIENT")
    print("=" * 70)

    # Test 1: Mock client
    print("\nTest 1: Mock LLM Client")
    print("-" * 70)

    mock_client = create_llm_client(use_mock=True)
    response = mock_client.generate("Generate a factor")

    print(f"✅ Mock response generated ({len(response)} chars)")
    print(f"Preview: {response[:100]}...")

    # Test 2: Real client (if API key available)
    print("\nTest 2: Real LLM Client (if API key available)")
    print("-" * 70)

    real_client = create_llm_client(use_mock=False)

    if isinstance(real_client, MockLLMClient):
        print("⚠️  No API key found - using mock client")
    else:
        print(f"✅ Using {real_client.provider} with model {real_client.config.model}")

        # Test simple prompt
        test_prompt = "What is 2+2? Answer in one sentence."
        test_response = real_client.generate(test_prompt)

        if test_response:
            print(f"✅ API call successful")
            print(f"Response: {test_response[:100]}...")
        else:
            print("❌ API call failed")

    print("\n" + "=" * 70)
    print("LLM CLIENT TEST COMPLETE")
    print("=" * 70)
