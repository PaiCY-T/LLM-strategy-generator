#!/usr/bin/env python3
"""
Debug LLM Response - Capture raw LLM output before validation.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Monkey patch InnovationEngine to log YAML before validation
original_file = Path(__file__).parent / 'src' / 'innovation' / 'innovation_engine.py'

# Read the InnovationEngine
from src.innovation.innovation_engine import InnovationEngine
import yaml as yaml_lib

# Patch the _generate_yaml_innovation method to log YAML
original_method = InnovationEngine._generate_yaml_innovation

def patched_generate_yaml_innovation(self, champion_code, champion_metrics, historical_failures):
    """Patched version that logs YAML before validation."""

    # Build prompt
    prompt = self.structured_prompt_builder.build_compact_prompt(
        champion_code=champion_code,
        champion_metrics=champion_metrics,
        failure_patterns=historical_failures or []
    )

    print("\n" + "="*70)
    print("PROMPT SENT TO LLM:")
    print("="*70)
    print(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
    print("="*70)

    # Call LLM
    response = self.provider.generate(
        prompt=prompt,
        max_tokens=2000,
        temperature=self.temperature
    )

    print("\n" + "="*70)
    print("RAW LLM RESPONSE:")
    print("="*70)
    print(response.content)
    print("="*70)

    # Extract YAML
    yaml_text = self._extract_yaml(response.content)

    print("\n" + "="*70)
    print("EXTRACTED YAML:")
    print("="*70)
    print(yaml_text if yaml_text else "(NONE EXTRACTED)")
    print("="*70)

    if yaml_text:
        try:
            parsed = yaml_lib.safe_load(yaml_text)
            print("\n" + "="*70)
            print("PARSED YAML STRUCTURE:")
            print("="*70)
            print(f"Top-level keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'NOT A DICT'}")
            if isinstance(parsed, dict):
                for key in parsed.keys():
                    print(f"  {key}: {type(parsed[key]).__name__}")
            print("="*70)
        except Exception as e:
            print(f"\nFailed to parse YAML: {e}")

    # Continue with original logic (will fail at validation)
    return original_method(self, champion_code, champion_metrics, historical_failures)

# Apply patch
InnovationEngine._generate_yaml_innovation = patched_generate_yaml_innovation

# Now run the test
print("\nTesting with patched InnovationEngine...")

engine = InnovationEngine(
    provider_name='gemini',
    model='gemini-2.5-flash-lite',
    generation_mode='yaml',
    max_retries=1,  # Only 1 retry to save time
    temperature=0.7
)

code = engine.generate_innovation(
    champion_code="",
    champion_metrics={'sharpe_ratio': 2.0},
    failure_history=None
)

print(f"\n\nFinal result: {'SUCCESS' if code else 'FAILURE'}")
