#!/usr/bin/env python3
"""Quick 5-iteration smoke test to verify bug fixes before full validation"""

import sys
import os
from pathlib import Path

# Set up paths
project_root = Path(__file__).parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "artifacts" / "working" / "modules"))

from autonomous_loop import AutonomousLoop

print("=" * 80)
print("BUG FIX SMOKE TEST (5 iterations)")
print("=" * 80)
print("\nVerifying:")
print("  ✓ Bug #1: F-string evaluation")
print("  ✓ Bug #2: LLM API routing")
print("  ✓ Bug #3: ExperimentConfig import")
print("  ✓ Bug #4: Exception state propagation")
print("\n" + "=" * 80 + "\n")

try:
    loop = AutonomousLoop(
        model="gemini-2.5-flash",
        max_iterations=5
    )

    print("📋 Initializing autonomous loop...")
    print(f"   Model: {loop.model}")
    print(f"   Max iterations: {loop.max_iterations}")
    print()

    loop.run()

    print("\n" + "=" * 80)
    print("✅ SMOKE TEST COMPLETE")
    print("=" * 80)
    print("\nIf no errors above, bug fixes are working!")

except Exception as e:
    print(f"\n❌ SMOKE TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
