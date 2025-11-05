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
    """Unified LLM client supporting multiple providers."""

    def __init__(self, config: LLMConfig):
        """
        Initialize LLM client.

        Args:
            config: LLM provider configuration
        """
        self.config = config
        self.provider = config.provider.lower()

        # Provider-specific endpoints
        self.endpoints = {
            'openrouter': 'https://openrouter.ai/api/v1/chat/completions',
            'openai': 'https://api.openai.com/v1/chat/completions',
            'gemini': 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
        }

    def generate(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        Generate text from LLM.

        Args:
            prompt: Input prompt
            max_retries: Maximum retry attempts

        Returns:
            Generated text or None if failed
        """
        for attempt in range(max_retries):
            try:
                if self.provider == 'openrouter':
                    response = self._call_openrouter(prompt)
                elif self.provider == 'gemini':
                    response = self._call_gemini(prompt)
                elif self.provider == 'openai':
                    response = self._call_openai(prompt)
                else:
                    raise ValueError(f"Unsupported provider: {self.provider}")

                return response

            except requests.exceptions.RequestException as req_e:
                # Log generic error without exposing API keys or request details
                print(f"⚠️  LLM API call failed (attempt {attempt + 1}/{max_retries}): Network/API error ({type(req_e).__name__})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None
            except Exception as e:
                # Catch-all for unexpected errors, sanitize output
                print(f"⚠️  LLM API call failed (attempt {attempt + 1}/{max_retries}): Unexpected error ({type(e).__name__})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None

        return None

    def _call_openrouter(self, prompt: str) -> str:
        """Call OpenRouter API."""
        headers = {
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.config.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens
        }

        response = requests.post(
            self.endpoints['openrouter'],
            headers=headers,
            json=payload,
            timeout=self.config.timeout
        )
        response.raise_for_status()

        data = response.json()
        return data['choices'][0]['message']['content']

    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API."""
        url = self.endpoints['gemini'].format(model=self.config.model)

        headers = {
            'Content-Type': 'application/json'
        }

        payload = {
            'contents': [{
                'parts': [{'text': prompt}]
            }],
            'generationConfig': {
                'temperature': self.config.temperature,
                'maxOutputTokens': self.config.max_tokens
            }
        }

        params = {'key': self.config.api_key}

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            params=params,
            timeout=self.config.timeout
        )
        response.raise_for_status()

        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API (o3, GPT-4, etc.)."""
        headers = {
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.config.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens
        }

        response = requests.post(
            self.endpoints['openai'],
            headers=headers,
            json=payload,
            timeout=self.config.timeout
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
    Factory function to create LLM client.

    Args:
        use_mock: If True, return MockLLMClient for testing

    Returns:
        LLMClient or MockLLMClient instance
    """
    if use_mock:
        return MockLLMClient()

    # Try to get API key from environment
    # Priority: OPENROUTER > GOOGLE > OPENAI
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    google_key = os.getenv('GOOGLE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    if openrouter_key:
        config = LLMConfig(
            provider='openrouter',
            model='google/gemini-2.5-flash',  # Fast and capable
            api_key=openrouter_key,
            temperature=0.7,
            max_tokens=2000
        )
        return LLMClient(config)

    elif google_key:
        config = LLMConfig(
            provider='gemini',
            model='gemini-2.5-flash',
            api_key=google_key,
            temperature=0.7,
            max_tokens=2000
        )
        return LLMClient(config)

    elif openai_key:
        config = LLMConfig(
            provider='openai',
            model='o3-mini',
            api_key=openai_key,
            temperature=0.7,
            max_tokens=2000
        )
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
