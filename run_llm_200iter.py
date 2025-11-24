#!/usr/bin/env python3
"""
200-Iteration LLM-Only Test - Innovation Rate Validation
Tests innovation_rate=100.0 (Pure LLM Mode)
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
from pathlib import Path
import time
from datetime import datetime

print("=" * 80)
print("200-Iteration LLM-Only Test (innovation_rate=100.0)")
print("Expected: 100% LLM iterations")
print("=" * 80)
print()

# Clean up old artifacts
print("Cleaning up old test artifacts...")
import subprocess
subprocess.run(['rm', '-f', 'unified_iteration_history.jsonl'], check=False)
subprocess.run(['rm', '-f', 'unified_champion.json'], check=False)
subprocess.run(['rm', '-rf', 'checkpoints'], check=False)
print("✓ Cleanup complete\n")

# Initialize test harness
print("Initializing UnifiedTestHarness (LLM-only mode)...")
harness = UnifiedTestHarness(
    model='gemini-2.5-flash',
    target_iterations=200,
    template_mode=False,  # LLM mode
    use_json_mode=False,  # Correct: template_mode=False incompatible with use_json_mode=True
    innovation_rate=100.0,  # Pure LLM mode (100% LLM)
    enable_learning=True,
    enable_monitoring=True,
    use_docker=False,
    checkpoint_dir='checkpoints',
    checkpoint_interval=20
)
print("✓ Harness initialized (innovation_rate=100.0 = Pure LLM)\n")

# Run test
print("Starting 200-iteration LLM-only test...")
print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Estimated duration: ~40-50 minutes")
print()

start_time = time.time()
result = harness.run_test()
duration = time.time() - start_time

# Analyze mode distribution from history file
print("\n" + "=" * 80)
print("MODE DISTRIBUTION ANALYSIS")
print("=" * 80)

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

    # Validation for Pure LLM mode
    llm_pct = mode_counts['LLM'] / total * 100
    expected_llm = 100.0
    tolerance = 5.0  # ±5% for 200 iterations

    if abs(llm_pct - expected_llm) <= tolerance:
        print(f"\n✅ PASS: Mode distribution within expected range ({expected_llm}% ±{tolerance}%)")
        print(f"   Actual: {llm_pct:.1f}%")
    else:
        print(f"\n⚠️  WARNING: Mode distribution outside expected range")
        print(f"   Expected: {expected_llm}% ±{tolerance}%, Got: {llm_pct:.1f}%")
except FileNotFoundError:
    print("⚠️  Could not read unified_iteration_history.jsonl for mode distribution analysis")

# Display results
print("\n" + "=" * 80)
print("RESULTS - LLM-ONLY 200 ITERATIONS")
print("=" * 80)
print(f"Total Iterations:        {result['total_iterations']}")
print(f"Duration:                {duration/60:.1f} minutes")
print(f"Success Rate:            {result['success_rate']:.1f}%")
print(f"Best Sharpe:             {result['best_sharpe']:.4f}")
print()

# Statistical analysis
if 'statistical_report' in result:
    print("Statistical Analysis:")
    print(f"  P-value:               {result['statistical_report']['p_value']:.4f}")
    print(f"  Statistically Significant: {result['statistical_report']['is_significant']}")
    print(f"  Production Ready:      {result['statistical_report']['production_ready']}")
    print()

# Save results
Path('results').mkdir(exist_ok=True)
output_file = f"results/llm_only_200iter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, 'w') as f:
    json.dump(result, f, indent=2, default=str)
print(f"Results saved to: {output_file}")
print("=" * 80)
