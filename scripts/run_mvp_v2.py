"""Run complete MVP with real finlab data - Version 2 with preloaded data.

This version preloads all commonly used datasets in the main process,
then passes them to the subprocess to avoid authentication issues.
"""

import os
import sys

# Set API credentials
os.environ['FINLAB_API_TOKEN'] = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m'
os.environ['OPENROUTER_API_KEY'] = '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'

print("="*60)
print("MVP V2 - AUTONOMOUS LOOP WITH PRELOADED DATA")
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

# Preload ALL commonly used datasets
print("\n[2/4] Preloading all common datasets...")
try:
    datasets = {}

    # Price data
    print("   Loading price data...")
    datasets['price:收盤價'] = data.get('price:收盤價')
    datasets['price:開盤價'] = data.get('price:開盤價')
    datasets['price:最高價'] = data.get('price:最高價')
    datasets['price:最低價'] = data.get('price:最低價')
    datasets['price:成交股數'] = data.get('price:成交股數')
    datasets['price:成交金額'] = data.get('price:成交金額')

    # Fundamental data
    print("   Loading fundamental data...")
    datasets['fundamental_features:ROE稅後'] = data.get('fundamental_features:ROE稅後')
    datasets['fundamental_features:股價淨值比'] = data.get('fundamental_features:股價淨值比')
    datasets['fundamental_features:本益比'] = data.get('fundamental_features:本益比')
    datasets['fundamental_features:稅後淨利率'] = data.get('fundamental_features:稅後淨利率')

    # Revenue data
    print("   Loading revenue data...")
    datasets['etl:monthly_revenue:revenue_yoy'] = data.get('etl:monthly_revenue:revenue_yoy')

    # Foreign data
    print("   Loading foreign investor data...")
    datasets['etl:foreign_main_force_buy_sell_summary:strength'] = data.get('etl:foreign_main_force_buy_sell_summary:strength')

    print(f"   ✅ Loaded {len(datasets)} datasets")

    # Create data wrapper with preloaded datasets
    class PreloadedData:
        """Wrapper for preloaded datasets that doesn't call finlab API."""
        def __init__(self, datasets_dict):
            self._datasets = datasets_dict

        def get(self, key):
            """Get dataset by key from preloaded data."""
            if key in self._datasets:
                return self._datasets[key]
            else:
                raise KeyError(f"Dataset '{key}' not preloaded. Available: {list(self._datasets.keys())}")

    finlab_data = PreloadedData(datasets)
    print("   ✅ Preloaded data wrapper created")

except Exception as e:
    print(f"❌ Failed to load data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Run autonomous loop
print("\n[3/4] Running autonomous learning loop...")
print("   Model: google/gemini-2.5-flash")
print("   Max iterations: 5")
print("   Data: Preloaded finlab datasets (no API calls in subprocess)")
print()

try:
    from autonomous_loop import AutonomousLoop

    loop = AutonomousLoop(
        model="google/gemini-2.5-flash",
        max_iterations=5,
        history_file="mvp_v2_history.json"
    )

    # Clear previous history
    loop.history.clear()

    # Run with preloaded data
    results = loop.run(data=finlab_data)

    print("\n[4/4] Analyzing results...")
    print("="*60)
    print("MVP V2 RESULTS")
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

    print("\n✅ MVP V2 TEST COMPLETE!")

except Exception as e:
    print(f"\n❌ Loop execution failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
