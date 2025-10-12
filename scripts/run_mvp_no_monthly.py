"""MVP WITHOUT monthly_revenue datasets - use fundamentals instead.

Completely avoids problematic monthly_revenue datasets.
Uses fundamental_features:營收成長率 for revenue growth.
"""

import os
import sys

# Set API credentials
os.environ['FINLAB_API_TOKEN'] = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m'
os.environ['OPENROUTER_API_KEY'] = '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'

print("="*60)
print("MVP NO-MONTHLY-REVENUE - FUNDAMENTALS ONLY")
print("="*60)
print()

# Initialize finlab
print("[1/2] Initializing finlab...")
try:
    import finlab
    finlab.login(os.environ['FINLAB_API_TOKEN'])
    from finlab import data
    print(f"✅ finlab {finlab.__version__} initialized")

    # Test alternative datasets
    print("   Testing alternative datasets...")
    revenue_growth = data.get('fundamental_features:營收成長率')
    print(f"   ✅ Revenue growth rate: {revenue_growth.shape}")

    # Create wrapper
    class FinlabData:
        def __init__(self):
            self._data = data
        def get(self, key):
            return self._data.get(key)

    finlab_data = FinlabData()

except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Run with no-monthly template
print("\n[2/2] Running WITHOUT monthly_revenue...")
print("   Model: google/gemini-2.5-flash")
print("   Max iterations: 5")
print("   Timeout: 120s")
print("   Strategy: Use fundamental_features:營收成長率 instead")
print()

try:
    from autonomous_loop import AutonomousLoop

    loop = AutonomousLoop(
        model="google/gemini-2.5-flash",
        max_iterations=5,
        history_file="mvp_no_monthly_history.json"
    )

    # Use no-monthly template
    loop.prompt_builder.template_file = 'prompt_template_no_monthly.txt'
    loop.prompt_builder.base_template = loop.prompt_builder._load_template()

    loop.history.clear()

    results = loop.run(data=finlab_data)

    print("\n" + "="*60)
    print("NO-MONTHLY MVP RESULTS")
    print("="*60)

    print(f"\nExecution Summary:")
    print(f"  Total iterations: {results['total_iterations']}")
    print(f"  ✅ Successful: {results['successful_iterations']}")
    print(f"  ❌ Failed: {results['failed_iterations']}")
    print(f"  ⏱️  Total time: {results['elapsed_time']:.1f}s")

    if results['successful_iterations'] > 0:
        success_rate = results['successful_iterations'] / results['total_iterations'] * 100
        print(f"  📊 Success rate: {success_rate:.1f}%")

        successful = loop.history.get_successful_iterations()
        print(f"\n🎉 SUCCESS! {len(successful)} strategies worked!")

        for record in successful:
            print(f"\n📊 Iteration {record.iteration_num}:")
            if record.metrics:
                for key, value in sorted(record.metrics.items()):
                    if isinstance(value, float):
                        print(f"   {key}: {value:.4f}")
                    else:
                        print(f"   {key}: {value}")

                # Save best strategy
                if record.metrics.get('sharpe_ratio', 0) > 0.5:
                    with open(f'best_strategy_iter{record.iteration_num}.py', 'w') as f:
                        f.write(record.code)
                    print(f"   💾 Saved as best_strategy_iter{record.iteration_num}.py")
    else:
        print("\n⚠️  No successful executions")
        print("\nDEBUG:")
        for i, record in enumerate(loop.history.records):
            print(f"  Iter {i}:")
            if record.execution_error:
                error = record.execution_error[:100]
                print(f"    {error}")

except Exception as e:
    print(f"\n❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
