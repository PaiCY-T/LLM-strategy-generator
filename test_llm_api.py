#!/usr/bin/env python3
"""
Quick LLM API Integration Test

Tests OpenRouter API connection without full system dependencies.
"""

import os
import sys
import json
import time

def test_openrouter_api():
    """Test OpenRouter API with simple request."""
    print("=" * 70)
    print("LLM API INTEGRATION TEST")
    print("=" * 70)
    print()

    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        return False

    masked_key = api_key[:8] + "..." + api_key[-4:]
    print(f"✓ API Key: {masked_key}")
    print()

    # Try to import required modules
    try:
        import httpx
        print("✓ httpx available")
    except ImportError:
        print("⚠️  httpx not installed, trying requests...")
        try:
            import requests
            httpx = None
            print("✓ requests available")
        except ImportError:
            print("❌ Neither httpx nor requests available")
            print("   Install: pip install requests")
            return False

    print()

    # Test API call
    print("Testing API connection...")
    print("-" * 70)

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [
            {
                "role": "user",
                "content": "Reply with exactly: 'API connection successful'"
            }
        ],
        "max_tokens": 50,
        "temperature": 0.0,
    }

    try:
        start_time = time.time()

        if httpx:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
        else:
            import requests
            response = requests.post(url, headers=headers, json=payload, timeout=30)

        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            message = data['choices'][0]['message']['content']

            print(f"✅ API call successful ({elapsed:.2f}s)")
            print(f"   Model: {data.get('model', 'N/A')}")
            print(f"   Response: {message}")
            print()
            return True
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            print()
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_generation():
    """Test LLM strategy generation."""
    print()
    print("=" * 70)
    print("STRATEGY GENERATION TEST")
    print("=" * 70)
    print()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        return False

    # Import http client
    try:
        import httpx
        http_module = httpx
    except ImportError:
        try:
            import requests
            http_module = requests
        except ImportError:
            print("❌ No HTTP client available")
            return False

    # Create strategy generation prompt
    prompt = """Generate a simple technical trading strategy for Taiwan stock market.

Requirements:
- Use finlab API
- Use one technical indicator (e.g., RSI, MA, MACD)
- Include entry and exit logic
- Keep it simple and concise

Format: Return only Python code, no explanation."""

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.7,
    }

    try:
        print("Generating strategy...")
        start_time = time.time()

        if hasattr(http_module, 'Client'):
            with http_module.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
        else:
            response = http_module.post(url, headers=headers, json=payload, timeout=60)

        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            code = data['choices'][0]['message']['content']

            print(f"✅ Strategy generated ({elapsed:.2f}s)")
            print()
            print("Generated Code Preview:")
            print("-" * 70)
            lines = code.split('\n')[:20]  # Show first 20 lines
            for line in lines:
                print(line)
            all_lines = code.split('\n')
            if len(all_lines) > 20:
                print("...")
                print(f"(Total: {len(all_lines)} lines)")
            print("-" * 70)
            print()

            # Check if code looks valid
            has_import = 'import' in code.lower()
            has_finlab = 'finlab' in code.lower()

            print("Code Analysis:")
            print(f"  Has imports: {has_import}")
            print(f"  Uses finlab: {has_finlab}")
            print(f"  Length: {len(code)} characters")
            print()

            return True
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    results = []

    # Test 1: Basic API connection
    test1_pass = test_openrouter_api()
    results.append(("API Connection", test1_pass))

    # Test 2: Strategy generation
    if test1_pass:
        test2_pass = test_strategy_generation()
        results.append(("Strategy Generation", test2_pass))
    else:
        print()
        print("⚠️  Skipping strategy generation test (API connection failed)")
        results.append(("Strategy Generation", None))

    # Summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()

    for name, result in results:
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIPPED"
        print(f"  {status:12} {name}")

    print()

    passed = sum(1 for _, r in results if r is True)
    total = len([r for _, r in results if r is not None])

    if passed == total:
        print(f"🎉 All tests passed ({passed}/{total})")
        return 0
    else:
        print(f"⚠️  Some tests failed ({passed}/{total} passed)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
