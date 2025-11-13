"""MVP with STRICT prompt template that explicitly forbids wrong keys.

Adds explicit prohibitions and examples to prevent LLM from using
'etl:monthly_revenue:revenue_yoy' (which doesn't exist).
"""

import os
import sys

# Set API credentials
os.environ['FINLAB_API_TOKEN'] = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m'
os.environ['OPENROUTER_API_KEY'] = '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'

print("="*60)
print("MVP STRICT - EXPLICIT KEY PROHIBITIONS")
print("="*60)
print()

# Initialize finlab
print("[1/2] Initializing finlab...")
try:
    import finlab
    finlab.login(os.environ['FINLAB_API_TOKEN'])
    from finlab import data
    print(f"✅ finlab {finlab.__version__} initialized")

    # Verify monthly revenue key
    print("   Testing correct monthly revenue key...")
    revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
    print(f"   ✅ Correct key works: {revenue_yoy.shape}")

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

# Run with strict template
print("\n[2/2] Running with STRICT prompt template...")
print("   Model: google/gemini-2.5-flash")
print("   Max iterations: 5")
print("   Timeout: 120s")
print("   Template: prompt_template_strict.txt (with explicit prohibitions)")
print()

try:
    from autonomous_loop import AutonomousLoop

    # Create loop
    loop = AutonomousLoop(
        model="google/gemini-2.5-flash",
        max_iterations=5,
        history_file="mvp_strict_history.json"
    )

    # Use strict template
    loop.prompt_builder.template_file = 'prompt_template_strict.txt'
    loop.prompt_builder.base_template = loop.prompt_builder._load_template()

    # Clear history
    loop.history.clear()

    # Run
    results = loop.run(data=finlab_data)

    print("\n" + "="*60)
    print("STRICT MVP RESULTS")
    print("="*60)

    print(f"\nExecution Summary:")
    print(f"  Total iterations: {results['total_iterations']}")
    print(f"  ✅ Successful: {results['successful_iterations']}")
    print(f"  ❌ Failed: {results['failed_iterations']}")
    print(f"  ⏱️  Total time: {results['elapsed_time']:.1f}s")

    if results['successful_iterations'] > 0:
        success_rate = results['successful_iterations'] / results['total_iterations'] * 100
        print(f"  📊 Success rate: {success_rate:.1f}%")

    # Show results
    successful = loop.history.get_successful_iterations()
    if successful:
        print(f"\n🎉 Success! {len(successful)} strategies worked!")

        for record in successful:
            print(f"\n📊 Iteration {record.iteration_num}:")
            if record.metrics:
                for key, value in sorted(record.metrics.items()):
                    if isinstance(value, float):
                        print(f"   {key}: {value:.4f}")
                    else:
                        print(f"   {key}: {value}")
    else:
        print("\n⚠️  No successful executions")
        print("\nDEBUG:")
        for i, record in enumerate(loop.history.records):
            print(f"  Iter {i}:")
            if record.execution_error:
                error = record.execution_error[:150]
                print(f"    Error: {error}")

                # Check what key was used
                if 'etl:monthly_revenue' in record.code:
                    print(f"    ❌ Still using wrong key 'etl:monthly_revenue:...'")
                elif 'monthly_revenue:去年同月增減' in record.code:
                    print(f"    ✅ Using correct key")
                    print(f"    💡 Error is NOT about missing dataset")

except Exception as e:
    print(f"\n❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
