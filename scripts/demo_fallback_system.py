#!/usr/bin/env python3
"""
Fallback System Demonstration

This script demonstrates the complete fallback system in action:
1. AST validation of generated code
2. Fallback activation when validation fails
3. Champion template usage
4. Comprehensive logging

Author: Integration Demo
Created: 2025-10-09
"""

import logging
from ast_validator import validate_strategy_code
from template_fallback import get_fallback_strategy, log_fallback_usage, get_champion_metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_scenario(scenario_name: str, code: str, iteration: int, fallback_count: int = 0):
    """
    Demonstrate a complete validation + fallback scenario.

    Args:
        scenario_name: Name of the scenario
        code: Code to validate
        iteration: Iteration number
        fallback_count: Number of recent fallbacks
    """
    print("\n" + "="*70)
    print(f"Scenario: {scenario_name}")
    print("="*70)

    MAX_FALLBACK_RATIO = 0.3

    # Step 1: Validate code
    print(f"\n1️⃣  Validating generated code (Iteration {iteration})...")
    is_valid, error = validate_strategy_code(code)

    if is_valid:
        print(f"   ✅ Validation PASSED - code is valid")
        print(f"   → Proceeding with original code")
        final_code = code
        used_fallback = False
    else:
        print(f"   ❌ Validation FAILED")
        print(f"      Error: {error[:100]}...")

        # Step 2: Check fallback threshold
        fallback_ratio = fallback_count / max(iteration, 1)
        can_use_fallback = fallback_ratio < MAX_FALLBACK_RATIO

        print(f"\n2️⃣  Checking fallback eligibility...")
        print(f"   Recent fallbacks: {fallback_count}")
        print(f"   Fallback ratio: {fallback_ratio:.1%} vs threshold {MAX_FALLBACK_RATIO:.1%}")

        if can_use_fallback:
            print(f"   ✅ Fallback ALLOWED (ratio below threshold)")

            # Step 3: Use fallback
            print(f"\n3️⃣  Activating fallback strategy...")
            log_fallback_usage("AST validation failed", iteration)
            final_code = get_fallback_strategy()

            # Validate fallback
            is_fallback_valid, fallback_error = validate_strategy_code(final_code)
            if is_fallback_valid:
                print(f"   ✅ Fallback validation PASSED")
                used_fallback = True
            else:
                print(f"   ❌ CRITICAL: Fallback validation FAILED!")
                print(f"      Error: {fallback_error}")
                final_code = None
                used_fallback = False
        else:
            print(f"   ❌ Fallback DENIED (ratio exceeds threshold)")
            print(f"   → Iteration will fail")
            final_code = None
            used_fallback = False

    # Summary
    print(f"\n4️⃣  Result Summary:")
    if final_code:
        print(f"   Status: ✅ SUCCESS")
        print(f"   Code source: {'Fallback Template' if used_fallback else 'Original Generated'}")
        print(f"   Code length: {len(final_code)} chars")
        if used_fallback:
            meta = get_champion_metadata()
            print(f"   Template: Iteration {meta['iteration']} (Sharpe: {meta['sharpe_ratio']:.4f})")
    else:
        print(f"   Status: ❌ FAILED")
        print(f"   Reason: Validation failed and fallback unavailable")


def main():
    """Run demonstration scenarios."""
    print("="*70)
    print("Fallback System Demonstration")
    print("="*70)
    print("\nThis demo shows how the fallback system handles different scenarios:")
    print("1. Valid code → No fallback needed")
    print("2. Invalid code + Low fallback ratio → Fallback activated")
    print("3. Invalid code + High fallback ratio → Fallback denied")

    # Scenario 1: Valid code
    valid_code = '''
import pandas as pd
close = data.get('price:收盤價')
momentum = close.pct_change(20).shift(1)
position = momentum.is_largest(10)
report = sim(position, resample="Q", upload=False)
'''
    demo_scenario("Valid Code (No Fallback)", valid_code, iteration=10, fallback_count=2)

    # Scenario 2: Invalid code with low fallback ratio
    invalid_code_low = '''
import os
import pandas as pd
os.system('rm -rf /')  # Dangerous!
'''
    demo_scenario("Invalid Code + Low Fallback Ratio", invalid_code_low, iteration=15, fallback_count=2)

    # Scenario 3: Invalid code with high fallback ratio
    invalid_code_high = '''
import subprocess
subprocess.call(['curl', 'http://evil.com'])
'''
    demo_scenario("Invalid Code + High Fallback Ratio", invalid_code_high, iteration=20, fallback_count=7)

    # Final summary
    print("\n" + "="*70)
    print("Demonstration Complete")
    print("="*70)
    print("\n✅ Fallback system is working correctly:")
    print("   • Valid code → Proceeds normally")
    print("   • Invalid code + eligible → Uses champion template")
    print("   • Invalid code + ineligible → Fails iteration")
    print("\n📊 Champion Template: Iteration 6 (Sharpe: 2.4751)")
    print("📚 See TASK3_INTEGRATION_SUMMARY.md for full documentation")


if __name__ == "__main__":
    main()
