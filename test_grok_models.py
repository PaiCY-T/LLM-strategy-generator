#!/usr/bin/env python3
"""Test different Grok model names on OpenRouter."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.innovation.llm_providers import create_provider

# Possible Grok model names based on OpenRouter documentation
models_to_try = [
    'x-ai/grok-beta',
    'x-ai/grok-vision-beta',
    'xai/grok-beta',
    'x-ai/grok-2-vision-1212',
    'x-ai/grok-2-1212',
    'anthropic/claude-3-5-sonnet-20241022',  # Fallback known working model
]

print("Testing Grok models on OpenRouter...")
print("="*70)

for model in models_to_try:
    print(f"\nTrying: {model}")
    try:
        provider = create_provider('openrouter', model=model)
        response = provider.generate('Say "test" only', max_tokens=10, max_retries=1)
        if response:
            print(f"  ✅ SUCCESS - Model works!")
            print(f"     Response: {response.content[:50]}")
            print(f"\n🎯 Found working model: {model}")
            break
        else:
            print(f"  ⚠️  No response received")
    except Exception as e:
        error_msg = str(e)
        if '404' in error_msg:
            print(f"  ❌ Model not found (404)")
        elif '429' in error_msg:
            print(f"  ⚠️  Rate limited (429) - model might exist")
        elif '400' in error_msg:
            print(f"  ❌ Bad request (400) - {error_msg[:80]}")
        else:
            print(f"  ❌ Error: {error_msg[:100]}")

print("\n" + "="*70)
