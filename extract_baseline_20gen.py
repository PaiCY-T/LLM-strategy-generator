#!/usr/bin/env python3
"""
Extract first 20 iterations from iteration_history.json as baseline.

This creates baseline_20gen.json for the LLM Innovation Capability baseline test.
"""

import json
import sys
from pathlib import Path

def extract_baseline_20gen():
    """Extract first 20 iterations as baseline."""

    # Load full iteration history (JSONL format)
    history_file = Path('iteration_history.json')
    if not history_file.exists():
        print(f"❌ Error: {history_file} not found")
        sys.exit(1)

    full_history = []
    with open(history_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    full_history.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    print(f"✅ Loaded {len(full_history)} iterations from {history_file}")

    # Extract first 20
    baseline_20 = full_history[:20]

    # Save as baseline
    baseline_file = Path('baseline_20gen.json')
    with open(baseline_file, 'w') as f:
        json.dump(baseline_20, f, indent=2)

    print(f"✅ Extracted first 20 iterations to {baseline_file}")

    # Print summary statistics
    print(f"\n📊 Baseline Summary (20 iterations):")

    sharpe_ratios = []
    calmar_ratios = []
    max_drawdowns = []

    for iteration in baseline_20:
        metrics = iteration.get('metrics', {})
        if metrics:
            sharpe_ratios.append(metrics.get('sharpe_ratio', 0))
            calmar_ratios.append(metrics.get('calmar_ratio', 0))
            max_drawdowns.append(metrics.get('max_drawdown', 0))

    if sharpe_ratios:
        import numpy as np
        print(f"  Sharpe Ratio:")
        print(f"    Mean:   {np.mean(sharpe_ratios):.3f}")
        print(f"    Median: {np.median(sharpe_ratios):.3f}")
        print(f"    Min:    {np.min(sharpe_ratios):.3f}")
        print(f"    Max:    {np.max(sharpe_ratios):.3f}")
        print(f"  Calmar Ratio:")
        print(f"    Mean:   {np.mean(calmar_ratios):.3f}")
        print(f"    Median: {np.median(calmar_ratios):.3f}")
        print(f"  Max Drawdown:")
        print(f"    Mean:   {np.mean(max_drawdowns):.1%}")
        print(f"    Median: {np.median(max_drawdowns):.1%}")

    return baseline_file

if __name__ == "__main__":
    baseline_file = extract_baseline_20gen()
    print(f"\n✅ Baseline ready: {baseline_file}")
