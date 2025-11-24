#!/usr/bin/env python3
"""
10-Iteration Hybrid Mode Smoke Test
Validates innovation_rate=50.0 mode distribution
"""
import os
import sys
sys.path.insert(0, '/mnt/c/Users/jnpi/documents/finlab/LLM-strategy-generator')
os.environ['FINLAB_API_TOKEN'] = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyTXXRbvScfaO#vip_m'
os.chdir('/mnt/c/Users/jnpi/documents/finlab/LLM-strategy-generator')

# Set Phase 3 Feature Flags
os.environ['ENABLE_GENERATION_REFACTORING'] = 'true'
os.environ['PHASE3_STRATEGY_PATTERN'] = 'true'
os.environ['PHASE1_CONFIG_ENFORCEMENT'] = 'true'

from tests.integration.unified_test_harness import UnifiedTestHarness
import json
from datetime import datetime

print("=" * 80)
print("10-Iteration Hybrid Mode Smoke Test")
print("Expected: ~5 LLM iterations + ~5 FG iterations")
print("=" * 80)

# Clean up artifacts
import subprocess
subprocess.run(['rm', '-f', 'unified_iteration_history.jsonl'], check=False)
subprocess.run(['rm', '-f', 'unified_champion.json'], check=False)

# Initialize harness with Hybrid Mode
harness = UnifiedTestHarness(
    model='gemini-2.5-flash',
    target_iterations=10,
    template_mode=False,
    use_json_mode=False,
    innovation_rate=50.0,  # 50% LLM, 50% FG
    enable_learning=True,
    enable_monitoring=True,
    use_docker=False,
)

print(f"\n✓ Harness initialized (innovation_rate=50.0)")
print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Run test
result = harness.run_test()

# Analyze mode distribution from history file
print("\n" + "=" * 80)
print("MODE DISTRIBUTION ANALYSIS")
print("=" * 80)

import json
mode_counts = {'LLM': 0, 'FG': 0, 'UNKNOWN': 0}
try:
    with open('unified_iteration_history.jsonl', 'r') as f:
        for line in f:
            record = json.loads(line)
            gen_method = record.get('generation_method', 'unknown')
            if gen_method == 'llm':
                mode_counts['LLM'] += 1
            elif gen_method == 'factor_graph':
                mode_counts['FG'] += 1
            else:
                mode_counts['UNKNOWN'] += 1

    total = result['total_iterations']
    print(f"LLM iterations:          {mode_counts['LLM']}/{total} ({mode_counts['LLM']/total*100:.1f}%)")
    print(f"Factor Graph iterations: {mode_counts['FG']}/{total} ({mode_counts['FG']/total*100:.1f}%)")

    # Validation
    llm_pct = mode_counts['LLM'] / total * 100
    expected_llm = 50.0
    tolerance = 30.0  # ±30% for 10 iterations

    if abs(llm_pct - expected_llm) <= tolerance:
        print(f"\n✅ PASS: Mode distribution within expected range ({expected_llm}% ±{tolerance}%)")
        print(f"   Actual: {llm_pct:.1f}%, Expected: {expected_llm}% ±{tolerance}%")
    else:
        print(f"\n⚠️  WARNING: Mode distribution outside expected range")
        print(f"   Expected: {expected_llm}% ±{tolerance}%, Got: {llm_pct:.1f}%")
except FileNotFoundError:
    print("⚠️  Could not read unified_iteration_history.jsonl for mode distribution analysis")

print("\n" + "=" * 80)
print(f"Success Rate: {result['success_rate']:.1f}%")
print(f"Best Sharpe:  {result['best_sharpe']:.4f}")
print("=" * 80)
