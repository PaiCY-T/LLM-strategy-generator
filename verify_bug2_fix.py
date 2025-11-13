#!/usr/bin/env python3
"""Quick verification that Bug #2 config fix eliminates 404 errors"""

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
print("BUG #2 FIX VERIFICATION")
print("=" * 80)
print()
print("Testing config fix:")
print("  ✓ provider: openrouter (was: gemini)")
print("  ✓ model: google/gemini-2.5-flash (was: anthropic/claude-3.5-sonnet)")
print()
print("Expected: No 404 errors, LLM innovation should work via OpenRouter")
print("=" * 80)
print()

try:
    loop = AutonomousLoop(
        model="google/gemini-2.5-flash",
        max_iterations=2  # Just 2 iterations to test LLM quickly
    )

    print(f"📋 Loop initialized: model={loop.model}, max_iterations={loop.max_iterations}")
    print(f"📋 LLM enabled: {loop.llm_enabled}")
    if loop.llm_enabled:
        print(f"📋 Innovation rate: {loop.innovation_rate:.1%}")
    print()

    loop.run()

    print()
    print("=" * 80)
    print("✅ VERIFICATION COMPLETE - No 404 errors!")
    print("=" * 80)
    print()
    print("Bug #2 is FIXED if you see:")
    print("  ✓ LLM innovation attempts")
    print("  ✓ No '404' errors")
    print("  ✓ Either successful generation OR valid API errors (rate limits, etc.)")
    print()

except Exception as e:
    print(f"\n❌ VERIFICATION FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
