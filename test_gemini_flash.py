#!/usr/bin/env python3
"""Test Gemini Flash (non-thinking) model."""

import os
import json
import requests

api_key = os.getenv('GOOGLE_API_KEY')
model = 'gemini-2.0-flash-exp'  # Non-thinking variant
url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'

prompt = """Generate momentum YAML strategy to beat champion (Sharpe=1.50).

Output ONLY valid YAML starting with 'metadata':"""

payload = {
    'contents': [{'parts': [{'text': prompt}]}],
    'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 2000}
}

response = requests.post(url, headers={'Content-Type': 'application/json'},
                        json=payload, params={'key': api_key}, timeout=30)

print(f"Status: {response.status_code}")
data = response.json()
print(f"Finish Reason: {data['candidates'][0].get('finishReason', 'N/A')}")

candidate = data['candidates'][0]
if 'content' in candidate and 'parts' in candidate['content']:
    text = candidate['content']['parts'][0]['text']
    print(f"✅ SUCCESS - Generated {len(text)} chars")
    print(f"\nFirst 300 chars:\n{text[:300]}")
else:
    print(f"❌ FAILED - {candidate}")
