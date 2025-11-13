"""MVP test with VALIDATED dataset keys from mapping file.

Uses dataset_mapping.json to ensure all dataset keys are correct.
Prevents "not exists" errors by using verified keys only.
"""

import os
import sys

# Set API credentials
os.environ['FINLAB_API_TOKEN'] = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m'
os.environ['OPENROUTER_API_KEY'] = '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'

print("="*60)
print("MVP VALIDATED - USING DATASET MAPPING")
print("="*60)
print()

# Initialize finlab
print("[1/4] Initializing finlab...")
try:
    import finlab
    finlab.login(os.environ['FINLAB_API_TOKEN'])
    from finlab import data
    print(f"✅ finlab {finlab.__version__} initialized")

    # Load test data to verify connection
    print("   Loading test data...")
    close = data.get('price:收盤價')
    print(f"   ✅ Data loaded: {close.shape[1]} stocks, {close.shape[0]} days")

    # Verify monthly revenue key
    print("   Testing monthly revenue key...")
    revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
    print(f"   ✅ Monthly revenue YoY loaded: {revenue_yoy.shape}")

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

# Verify dataset mapping exists
print("\n[2/4] Verifying dataset mapping...")
try:
    from dataset_lookup import DatasetLookup

    lookup = DatasetLookup()
    revenue_keys = lookup.get_monthly_revenue_keys()

    print("✅ Dataset mapping loaded")
    print(f"   Total datasets: {len(lookup.datasets)}")
    print(f"   Monthly revenue keys verified:")
    for name, key in list(revenue_keys.items())[:3]:
        valid = lookup.validate_key(key)
        status = "✅" if valid else "❌"
        print(f"     {status} {name}: {key}")

except Exception as e:
    print(f"❌ Dataset mapping failed: {e}")
    sys.exit(1)

# Generate validated prompt template
print("\n[3/4] Generating validated prompt template...")
try:
    from generate_prompt_with_lookup import generate_prompt_template

    template_content = generate_prompt_template()

    # Save template
    with open('prompt_template_validated.txt', 'w', encoding='utf-8') as f:
        f.write(template_content)

    print(f"✅ Validated template generated ({len(template_content)} chars)")
    print("   Contains verified keys for:")
    print("     - Price data")
    print("     - Monthly revenue (CORRECTED)")
    print("     - Fundamental features")
    print("     - Institutional investors")
    print("     - Margin trading")

except Exception as e:
    print(f"❌ Template generation failed: {e}")
    sys.exit(1)

# Run autonomous loop with validated template
print("\n[4/4] Running validated autonomous loop...")
print("   Model: google/gemini-2.5-flash")
print("   Max iterations: 5")
print("   Timeout: 120s")
print("   Template: prompt_template_validated.txt (from dataset mapping)")
print()

try:
    from autonomous_loop import AutonomousLoop

    # Create loop with validated template
    loop = AutonomousLoop(
        model="google/gemini-2.5-flash",
        max_iterations=5,
        history_file="mvp_validated_history.json"
    )

    # Override template file
    loop.prompt_builder.template_file = 'prompt_template_validated.txt'
    loop.prompt_builder.base_template = loop.prompt_builder._load_template()

    # Clear history
    loop.history.clear()

    # Run with real data
    results = loop.run(data=finlab_data)

    print("\n" + "="*60)
    print("VALIDATED MVP RESULTS")
    print("="*60)

    print(f"\nExecution Summary:")
    print(f"  Total iterations: {results['total_iterations']}")
    print(f"  ✅ Successful: {results['successful_iterations']}")
    print(f"  ❌ Failed: {results['failed_iterations']}")
    print(f"  ⏱️  Total time: {results['elapsed_time']:.1f}s")

    if results['successful_iterations'] > 0:
        success_rate = results['successful_iterations'] / results['total_iterations'] * 100
        print(f"  📊 Success rate: {success_rate:.1f}%")

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
            error_msg = record.execution_error[:100] if record.execution_error else 'Unknown'
            print(f"  Iter {i}: {error_msg}")

            # Check for dataset errors
            if record.execution_error and 'not exists' in record.execution_error:
                # Extract the bad key
                import re
                match = re.search(r'\*\*Error: (.*?) not exists', record.execution_error)
                if match:
                    bad_key = match.group(1)
                    print(f"    ⚠️  Invalid key used: {bad_key}")
                    print(f"    💡 Check dataset_mapping.json for correct key")

except Exception as e:
    print(f"\n❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
