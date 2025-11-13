#!/usr/bin/env python3
"""
Debug YAML Pipeline - Identify where "No code generated" error occurs.

Tests each step of the YAML pipeline with detailed logging.
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.innovation.innovation_engine import InnovationEngine

def test_yaml_pipeline():
    """Test YAML pipeline with detailed step-by-step logging."""

    print("\n" + "="*70)
    print("YAML Pipeline Debug Test")
    print("="*70)

    # Initialize engine
    print("\n[Step 1/6] Initializing InnovationEngine...")
    try:
        engine = InnovationEngine(
            provider_name='gemini',
            model='gemini-2.5-flash-lite',
            generation_mode='yaml',
            max_retries=3,
            temperature=0.7
        )
        print(f"✅ Engine initialized")
        print(f"   Provider: {engine.provider.__class__.__name__}")
        print(f"   Model: {engine.provider.model}")
        print(f"   Mode: {engine.generation_mode}")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test data
    champion_metrics = {
        'sharpe_ratio': 2.0,
        'annual_return': 0.20,
        'max_drawdown': 0.15
    }

    print("\n[Step 2/6] Calling generate_innovation()...")
    start_time = time.time()

    try:
        code = engine.generate_innovation(
            champion_code="",
            champion_metrics=champion_metrics,
            failure_history=None
        )

        elapsed = time.time() - start_time

        print(f"\n[Step 6/6] Result after {elapsed:.2f}s:")
        if code:
            print(f"✅ SUCCESS: Code generated")
            print(f"   Length: {len(code)} chars")
            print(f"   First 200 chars:\n{code[:200]}...")
        else:
            print(f"❌ FAILURE: No code generated (returned: {repr(code)})")

            # Try to get more info from engine
            stats = engine.get_statistics()
            print(f"\nEngine statistics:")
            for key, value in stats.items():
                print(f"   {key}: {value}")

    except Exception as e:
        print(f"❌ EXCEPTION during generation: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_yaml_pipeline()
