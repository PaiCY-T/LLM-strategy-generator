#!/usr/bin/env python3
"""
Diagnostic script to check Gemini API response structure.
"""

import os
import json
import requests

def test_gemini_api():
    """Test Gemini API to see actual response structure."""

    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not set")
        return

    print(f"✅ API Key found: {api_key[:10]}...")
    print()

    model = 'gemini-2.0-flash-thinking-exp'
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'

    print(f"Testing Gemini API:")
    print(f"  Model: {model}")
    print(f"  URL: {url}")
    print()

    headers = {
        'Content-Type': 'application/json',
    }

    payload = {
        'contents': [{
            'parts': [{'text': 'Say hello in JSON format'}]
        }],
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 100,
        }
    }

    params = {'key': api_key}

    try:
        print("Sending request...")
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            params=params,
            timeout=30
        )

        print(f"Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            print("✅ SUCCESS")
            print()
            print("Response JSON:")
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")

if __name__ == '__main__':
    test_gemini_api()
