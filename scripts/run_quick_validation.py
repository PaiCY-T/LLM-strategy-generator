#!/usr/bin/env python3
"""Quick 5-iteration validation to verify P0 fixes."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autonomous_loop import AutonomousLoop
import finlab
from finlab import data

def main():
    print("="*60)
    print("QUICK VALIDATION - 5 ITERATIONS WITH P0 FIXES")
    print("="*60)
    print("Testing:")
    print("  1. Critical bug fix (unconditional code update)")
    print("  2. Hash logging for code delivery verification")
    print("  3. Static validator for pre-execution checking")
    print("="*60)

    # Initialize Finlab
    print("\n[1/3] Loading Finlab data...")
    finlab.login(os.environ['FINLAB_API_TOKEN'])
    data.get('price:收盤價')
    print("✅ Finlab data loaded")

    # Run validation
    print("\n[2/3] Running 5-iteration autonomous loop...")
    loop = AutonomousLoop(
        model='google/gemini-2.5-flash',
        max_iterations=5
    )

    try:
        loop.run(data=data)
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    # Check results
    print("\n[3/3] Analyzing results...")
    records = loop.history.records

    successful = sum(1 for r in records if r.execution_success and r.metrics)
    total = len(records)
    success_rate = (successful / total * 100) if total > 0 else 0

    print(f"\n{'='*60}")
    print(f"RESULTS: {successful}/{total} successful ({success_rate:.1f}%)")
    print(f"{'='*60}")

    for i, record in enumerate(records):
        status = "✅" if (record.execution_success and record.metrics) else "❌"
        sharpe = record.metrics.get('sharpe_ratio', 0) if record.metrics else 0
        print(f"{status} Iteration {i}: Sharpe {sharpe:.4f}")

    print()
    if success_rate >= 60:
        print("✅ VALIDATION PASSED - Target >60% achieved!")
        return 0
    else:
        print(f"⚠️  Target not met (need 60%, got {success_rate:.1f}%)")
        print("   Reviewing failures for patterns...")
        for i, record in enumerate(records):
            if not (record.execution_success and record.metrics):
                print(f"   - Iteration {i}: {record.execution_error or 'Unknown error'}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
