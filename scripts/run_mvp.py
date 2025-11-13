"""Run complete MVP with real finlab data.

This is the final integration test that runs the autonomous learning loop
with real finlab data, enabling actual strategy execution and metrics extraction.
"""

import os
import sys

# Set API credentials
os.environ['FINLAB_API_TOKEN'] = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m'
os.environ['OPENROUTER_API_KEY'] = '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'

print("="*60)
print("MVP FINAL TEST - AUTONOMOUS LEARNING LOOP WITH REAL DATA")
print("="*60)
print()

# Initialize finlab
print("[1/4] Initializing finlab...")
try:
    import finlab
    finlab.login(os.environ['FINLAB_API_TOKEN'])
    from finlab import data
    print(f"✅ finlab {finlab.__version__} initialized")
except Exception as e:
    print(f"❌ Failed to initialize finlab: {e}")
    sys.exit(1)

# Load data
print("\n[2/4] Loading finlab data...")
try:
    # Create a simple data object that strategies can use
    print("   Loading price:收盤價...")
    close = data.get('price:收盤價')
    print(f"   ✅ Loaded {close.shape[1]} stocks, {close.shape[0]} days")

    # Wrap in a simple object that mimics the expected interface
    class FinlabData:
        """Wrapper for finlab data to provide consistent interface."""
        def __init__(self):
            self._data = data

        def get(self, key):
            """Get dataset by key."""
            return self._data.get(key)

    finlab_data = FinlabData()
    print("   ✅ Data wrapper created")

except Exception as e:
    print(f"❌ Failed to load data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Run autonomous loop
print("\n[3/4] Running autonomous learning loop...")
print("   Model: google/gemini-2.5-flash")
print("   Max iterations: 5")
print("   Data: Real finlab data")
print()

try:
    from autonomous_loop import AutonomousLoop

    loop = AutonomousLoop(
        model="google/gemini-2.5-flash",
        max_iterations=5,
        history_file="mvp_final_history.json"
    )

    # Clear previous history
    loop.history.clear()

    # Run with real data
    results = loop.run(data=finlab_data)

    print("\n[4/4] Analyzing results...")
    print("="*60)
    print("MVP RESULTS")
    print("="*60)

    print(f"\nExecution Summary:")
    print(f"  Total iterations: {results['total_iterations']}")
    print(f"  ✅ Successful: {results['successful_iterations']}")
    print(f"  ❌ Failed: {results['failed_iterations']}")
    print(f"     - Validation failures: {results['validation_failures']}")
    print(f"     - Execution failures: {results['execution_failures']}")
    print(f"  ⏱️  Total time: {results['elapsed_time']:.1f}s")
    print(f"  ⏱️  Avg per iteration: {results['elapsed_time']/results['total_iterations']:.1f}s")

    # Success rate
    if results['total_iterations'] > 0:
        success_rate = results['successful_iterations'] / results['total_iterations'] * 100
        print(f"\n  Success rate: {success_rate:.1f}%")

    # Show best strategies
    successful = loop.history.get_successful_iterations()
    if successful:
        print(f"\n🎉 Generated {len(successful)} successful strategies with real metrics!")

        # Find best by Sharpe ratio
        with_metrics = [s for s in successful if s.metrics and 'sharpe_ratio' in s.metrics]
        if with_metrics:
            best = max(with_metrics, key=lambda s: s.metrics['sharpe_ratio'])

            print(f"\n🏆 Best Strategy: Iteration {best.iteration_num}")
            print(f"   Model: {best.model}")
            print(f"   Timestamp: {best.timestamp}")
            print(f"\n   Metrics:")
            if best.metrics:
                for key, value in sorted(best.metrics.items()):
                    if isinstance(value, (int, float)):
                        print(f"     {key}: {value:.4f}" if isinstance(value, float) else f"     {key}: {value}")
                    else:
                        print(f"     {key}: {value}")

            print(f"\n   Code saved to: generated_strategy_loop_iter{best.iteration_num}.py")
    else:
        print("\n⚠️  No successful strategies generated")

    # Learning curve analysis
    print("\n" + "="*60)
    print("LEARNING CURVE ANALYSIS")
    print("="*60)

    all_records = loop.history.records
    for i, record in enumerate(all_records):
        status = "✅" if record.execution_success else "❌"
        sharpe = record.metrics.get('sharpe_ratio', 'N/A') if record.metrics else 'N/A'
        print(f"  Iter {i}: {status} Sharpe={sharpe}")

    print("\n✅ MVP TEST COMPLETE!")

except Exception as e:
    print(f"\n❌ Loop execution failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
