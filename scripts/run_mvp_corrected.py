"""MVP test with CORRECTED monthly revenue dataset keys.

Based on finlab documentation, the correct keys are:
- monthly_revenue:去年同月增減(%) (YoY growth)
- monthly_revenue:上月比較增減(%) (MoM growth)

NOT etl:monthly_revenue:revenue_yoy (which doesn't exist).
"""

import os
import sys

# Set API credentials
os.environ['FINLAB_API_TOKEN'] = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m'
os.environ['OPENROUTER_API_KEY'] = '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'

print("="*60)
print("MVP CORRECTED - FIXED MONTHLY REVENUE KEYS")
print("="*60)
print()

# Initialize finlab
print("[1/3] Initializing finlab...")
try:
    import finlab
    finlab.login(os.environ['FINLAB_API_TOKEN'])
    from finlab import data
    print(f"✅ finlab {finlab.__version__} initialized")

    # Load confirmed available data
    print("   Loading data...")
    close = data.get('price:收盤價')
    volume = data.get('price:成交股數')
    print(f"   ✅ Price data loaded: {close.shape[1]} stocks, {close.shape[0]} days")

    # Test monthly revenue with CORRECT key
    print("   Testing monthly revenue (CORRECTED key)...")
    revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
    print(f"   ✅ Revenue YoY loaded: {revenue_yoy.shape}")

    # Create wrapper
    class FinlabData:
        """Wrapper providing data.get() interface."""
        def __init__(self):
            self._data = data

        def get(self, key):
            """Get dataset."""
            return self._data.get(key)

    finlab_data = FinlabData()

except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Update prompt builder to use corrected template
print("\n[2/3] Configuring prompt builder...")
try:
    from autonomous_loop import AutonomousLoop

    # Create loop with corrected template
    loop = AutonomousLoop(
        model="google/gemini-2.5-flash",
        max_iterations=5,
        history_file="mvp_corrected_history.json"
    )

    # Override template file
    loop.prompt_builder.template_file = 'prompt_template_v2_corrected.txt'
    loop.prompt_builder.base_template = loop.prompt_builder._load_template()

    print("✅ Using corrected prompt template with fixed dataset keys")

except Exception as e:
    print(f"❌ Template configuration failed: {e}")
    sys.exit(1)

# Run autonomous loop with corrected template and 120s timeout
print("\n[3/3] Running corrected loop...")
print("   Model: google/gemini-2.5-flash")
print("   Max iterations: 5")
print("   Timeout: 120s")
print("   Template: prompt_template_v2_corrected.txt (FIXED revenue keys)")
print()

try:
    # Clear history
    loop.history.clear()

    # Run with real data
    results = loop.run(data=finlab_data)

    print("\n" + "="*60)
    print("CORRECTED MVP RESULTS")
    print("="*60)

    print(f"\nExecution Summary:")
    print(f"  Total iterations: {results['total_iterations']}")
    print(f"  ✅ Successful: {results['successful_iterations']}")
    print(f"  ❌ Failed: {results['failed_iterations']}")
    print(f"  ⏱️  Total time: {results['elapsed_time']:.1f}s")

    # Show successful strategies
    successful = loop.history.get_successful_iterations()
    if successful:
        print(f"\n🎉 Success! Generated {len(successful)} working strategies!")

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
        print("\nDEBUG INFO:")
        for i, record in enumerate(loop.history.records):
            print(f"  Iter {i}: {record.execution_error[:100] if record.execution_error else 'Unknown'}")

except Exception as e:
    print(f"\n❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
