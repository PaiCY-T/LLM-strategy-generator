#!/usr/bin/env python3
"""
Test to see what prompt InnovationEngine generates.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.innovation.innovation_engine import InnovationEngine

def test_prompt_generation():
    """Test what prompt is generated for YAML mode."""

    print("="*70)
    print("InnovationEngine Prompt Generation Test")
    print("="*70)
    print()

    # Initialize engine in YAML mode
    engine = InnovationEngine(
        provider_name='gemini',
        generation_mode='yaml',
        max_retries=1,
        temperature=0.7
    )

    print("✅ Engine initialized in YAML mode")
    print()

    # Test champion metrics
    champion_metrics = {
        'sharpe_ratio': 1.5,
        'annual_return': 0.25,
        'max_drawdown': 0.15,
        'win_rate': 0.55
    }

    print("Champion Metrics:")
    print(f"  Sharpe Ratio: {champion_metrics['sharpe_ratio']}")
    print(f"  Annual Return: {champion_metrics['annual_return']}")
    print(f"  Max Drawdown: {champion_metrics['max_drawdown']}")
    print(f"  Win Rate: {champion_metrics['win_rate']}")
    print()

    # Build prompt using StructuredPromptBuilder
    if engine.structured_prompt_builder:
        prompt = engine.structured_prompt_builder.build_compact_prompt(
            champion_metrics=champion_metrics,
            failure_patterns=[],
            target_strategy_type='momentum'
        )

        print("="*70)
        print("Generated Prompt:")
        print("="*70)
        print(prompt)
        print("="*70)
        print()
        print(f"Prompt Length: {len(prompt)} characters")
        print(f"Prompt Tokens (approx): {len(prompt.split())} words")
    else:
        print("❌ StructuredPromptBuilder not initialized")

if __name__ == '__main__':
    test_prompt_generation()
