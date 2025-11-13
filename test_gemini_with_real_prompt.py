#!/usr/bin/env python3
"""
Test Gemini API with the actual prompt that InnovationEngine uses.
"""

import os
import json
import requests

def test_gemini_with_real_prompt():
    """Test Gemini API with actual InnovationEngine prompt."""

    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not set")
        return

    model = 'gemini-2.0-flash-thinking-exp'
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'

    # The actual prompt from InnovationEngine
    prompt = """Generate momentum YAML strategy to beat champion (Sharpe=1.50).

Avoid: overtrading, large drawdowns

Schema (required fields):
metadata: {name, description, strategy_type, rebalancing_frequency}
indicators: {technical_indicators OR fundamental_factors OR custom_calculations}
entry_conditions: {threshold_rules OR ranking_rules, logical_operator}
exit_conditions: {stop_loss_pct, take_profit_pct} (optional)
position_sizing: {method, max_positions}

Output ONLY valid YAML starting with 'metadata':"""

    print("="*70)
    print(f"Testing Gemini API with Real Prompt")
    print("="*70)
    print(f"Model: {model}")
    print(f"Prompt Length: {len(prompt)} chars")
    print()

    headers = {
        'Content-Type': 'application/json',
    }

    payload = {
        'contents': [{
            'parts': [{'text': prompt}]
        }],
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 2000,
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
            response_data = response.json()

            print("="*70)
            print("Response Structure:")
            print("="*70)
            print(json.dumps(response_data, indent=2))
            print("="*70)
            print()

            # Check if we have the expected structure
            candidates = response_data.get('candidates', [])
            if not candidates:
                print("❌ No candidates in response")
                return

            candidate = candidates[0]
            print(f"Candidate keys: {list(candidate.keys())}")

            if 'content' in candidate:
                content = candidate['content']
                print(f"Content keys: {list(content.keys())}")

                if 'parts' in content:
                    parts = content['parts']
                    print(f"Parts count: {len(parts)}")
                    if parts and 'text' in parts[0]:
                        text = parts[0]['text']
                        print(f"✅ SUCCESS - Generated {len(text)} chars")
                        print()
                        print("Generated YAML:")
                        print("="*70)
                        print(text[:500])  # First 500 chars
                        print("="*70)
                    else:
                        print(f"❌ No 'text' in parts[0]: {parts[0]}")
                else:
                    print(f"❌ No 'parts' in content: {content}")
            else:
                print(f"❌ No 'content' in candidate: {candidate}")

        else:
            print(f"❌ FAILED: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")

if __name__ == '__main__':
    test_gemini_with_real_prompt()
