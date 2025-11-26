"""
Quick three-mode verification test to confirm the naming adapter fix works.

Tests all three modes with 1 iteration each:
1. Factor Graph Only
2. LLM Only
3. Hybrid

Expected outcome: Factor Graph should no longer fail with naming errors.
"""

import subprocess
import sys
import json
from pathlib import Path

def run_mode(mode_name, config_path):
    """Run a single iteration for a mode."""
    print(f"\n{'='*80}")
    print(f"Testing: {mode_name}")
    print(f"Config: {config_path}")
    print(f"{'='*80}\n")

    cmd = [
        "python3",
        "src/learning/iteration_executor.py",
        config_path
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120
    )

    if result.returncode == 0:
        print(f"✅ {mode_name}: EXECUTION COMPLETED")
    else:
        print(f"❌ {mode_name}: EXECUTION FAILED")
        print(f"Error: {result.stderr[:500]}")

    return result.returncode == 0

def main():
    print("\n" + "="*80)
    print("QUICK THREE-MODE VERIFICATION TEST")
    print("="*80)
    print("Purpose: Verify naming adapter fix enables Factor Graph mode")
    print("Test: 1 iteration per mode (3 total)")
    print("="*80)

    # Test configurations
    modes = [
        ("Factor Graph Only", "experiments/llm_learning_validation/config_pilot_fg_only_20.yaml"),
        ("LLM Only", "experiments/llm_learning_validation/config_pilot_llm_only_20.yaml"),
        ("Hybrid", "experiments/llm_learning_validation/config_pilot_hybrid_20.yaml"),
    ]

    results = {}

    for mode_name, config_path in modes:
        success = run_mode(mode_name, config_path)
        results[mode_name] = success

    # Summary
    print("\n" + "="*80)
    print("VERIFICATION RESULTS SUMMARY")
    print("="*80)

    for mode_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{mode_name:25} {status}")

    all_passed = all(results.values())

    print("="*80)
    if all_passed:
        print("🎉 ALL MODES VERIFIED SUCCESSFULLY!")
        print("The naming adapter fix is working correctly across all three modes.")
    else:
        failed = [name for name, success in results.items() if not success]
        print(f"⚠️  Some modes failed: {', '.join(failed)}")
    print("="*80 + "\n")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
