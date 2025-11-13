#!/usr/bin/env python3
"""Debug script to investigate history retrieval issue."""

import os
import sys

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'artifacts', 'working', 'modules'))

from history import IterationHistory

def main():
    """Debug history retrieval."""
    print("=" * 70)
    print("DEBUGGING HISTORY RETRIEVAL")
    print("=" * 70)

    # Load history
    history_file = 'iteration_history_smoke_test.json'
    print(f"\nLoading history from: {history_file}")

    history = IterationHistory(history_file)

    print(f"Total records loaded: {len(history.records)}")
    print("")

    # Check each iteration
    for i in range(5):
        print(f"{'='*70}")
        print(f"ITERATION {i}")
        print(f"{'='*70}")

        record = history.get_record(i)

        if record:
            print(f"✅ Record found")
            print(f"   iteration_num: {record.iteration_num}")
            print(f"   model: {record.model}")
            print(f"   mode: {record.mode}")
            print(f"   execution_success: {record.execution_success}")
            print(f"   validation_passed: {record.validation_passed}")

            # Check metrics
            print(f"\n   Metrics attribute exists: {hasattr(record, 'metrics')}")
            if hasattr(record, 'metrics'):
                print(f"   Metrics value: {record.metrics}")
                print(f"   Metrics type: {type(record.metrics)}")
                if record.metrics:
                    print(f"   Sharpe ratio: {record.metrics.get('sharpe_ratio', 'N/A')}")
                else:
                    print(f"   Metrics is None or empty dict")

            # Check parameters
            print(f"\n   Parameters attribute exists: {hasattr(record, 'parameters')}")
            if hasattr(record, 'parameters'):
                print(f"   Parameters value: {record.parameters}")
                print(f"   Parameters type: {type(record.parameters)}")
                if record.parameters:
                    print(f"   Parameters keys: {list(record.parameters.keys())}")
                else:
                    print(f"   Parameters is None or empty dict")
        else:
            print(f"❌ Record NOT found!")

        print("")

    print("=" * 70)
    print("CHECKING RECORDS LIST DIRECTLY")
    print("=" * 70)
    for idx, record in enumerate(history.records):
        print(f"\nRecord {idx}:")
        print(f"  iteration_num: {record.iteration_num}")
        print(f"  Has metrics: {record.metrics is not None}")
        if record.metrics:
            print(f"  Sharpe: {record.metrics.get('sharpe_ratio', 'N/A')}")
        print(f"  Has parameters: {record.parameters is not None}")
        if record.parameters:
            print(f"  Param count: {len(record.parameters)}")

if __name__ == '__main__':
    main()
