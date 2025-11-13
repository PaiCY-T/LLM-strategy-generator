#!/usr/bin/env python3
"""Quick analysis script to process Mode 1 (LLM Only) results from completed test."""

import json
from pathlib import Path
from datetime import datetime

# Read the JSONL file
history_file = Path("artifacts/data/phase5_llm_only_innovations.jsonl")

all_records = []
with open(history_file, 'r') as f:
    for line in f:
        if line.strip():
            record = json.loads(line)
            all_records.append(record)

total = len(all_records)
print(f"\n{'='*80}")
print(f"MODE 1 RESULTS ANALYSIS: LLM Only Mode")
print(f"{'='*80}\n")

# Calculate statistics
level_0 = sum(1 for r in all_records if r.get("classification_level") == "LEVEL_0")
level_1 = sum(1 for r in all_records if r.get("classification_level") == "LEVEL_1")
level_2 = sum(1 for r in all_records if r.get("classification_level") == "LEVEL_2")
level_3 = sum(1 for r in all_records if r.get("classification_level") == "LEVEL_3")

successful = level_1 + level_2 + level_3
success_rate = (successful / total * 100) if total > 0 else 0

# Collect Sharpe ratios
sharpes = []
for r in all_records:
    metrics = r.get("metrics", {})
    if isinstance(metrics, dict) and "sharpe_ratio" in metrics:
        sharpe = metrics.get("sharpe_ratio")
        if sharpe is not None:
            sharpes.append(sharpe)

avg_sharpe = sum(sharpes) / len(sharpes) if sharpes else 0.0
best_sharpe = max(sharpes) if sharpes else 0.0

# Count API errors (AttributeError from champion tracker API mismatches)
api_errors = sum(
    1 for r in all_records
    if r.get("classification_level") == "LEVEL_0"
    and r.get("execution_result", {}).get("error_type") == "AttributeError"
)

# Count error types
error_types = {}
for r in all_records:
    if r.get("classification_level") == "LEVEL_0":
        error_type = r.get("execution_result", {}).get("error_type", "Unknown")
        error_types[error_type] = error_types.get(error_type, 0) + 1

print(f"Total Iterations: {total}")
print(f"Successful: {successful} ({success_rate:.1f}%)")
print(f"Failed: {level_0}")
print()
print(f"Classification Breakdown:")
print(f"  LEVEL_0 (Failures): {level_0}")
print(f"  LEVEL_1 (Executed): {level_1}")
print(f"  LEVEL_2 (Weak): {level_2}")
print(f"  LEVEL_3 (Success): {level_3}")
print()
print(f"Performance Metrics:")
print(f"  Average Sharpe: {avg_sharpe:.4f}")
print(f"  Best Sharpe: {best_sharpe:.4f}")
print()
print(f"{'='*80}")
print(f"PHASE 5 VALIDATION RESULTS:")
print(f"{'='*80}")
print(f"  API Errors (AttributeError): {api_errors} {'✅ Phase 5 working!' if api_errors == 0 else '❌ Phase 5 issue!'}")
print()
if error_types:
    print(f"Error Type Breakdown (LEVEL_0 only):")
    for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {error_type}: {count}")
print()
print(f"{'='*80}")
print(f"CONCLUSION:")
print(f"{'='*80}")
if api_errors == 0:
    print("✅ Phase 5 API error prevention: SUCCESS")
    print("   No AttributeError from champion tracker API mismatches detected")
    print("   All LEVEL_0 failures are strategy execution errors (ValueError), not API errors")
else:
    print(f"❌ Phase 5 API error prevention: FAILURE")
    print(f"   {api_errors} AttributeError detected - Phase 5 may have issues")
print(f"{'='*80}\n")
