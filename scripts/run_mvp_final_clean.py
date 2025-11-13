"""Final MVP with CLEAN SLATE - no history contamination.

Completely removes history file and starts fresh with correct template.
"""

import os
import sys

# Set API credentials
os.environ['FINLAB_API_TOKEN'] = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m'
os.environ['OPENROUTER_API_KEY'] = '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'

print("="*60)
print("MVP FINAL CLEAN - FRESH START")
print("="*60)
print()

# Delete ALL old history files to prevent contamination
print("[0/3] Cleaning old history...")
import glob
old_histories = glob.glob('/mnt/c/Users/jnpi/Documents/finlab/*_history.json')
for f in old_histories:
    try:
        os.remove(f)
        print(f"   Deleted: {os.path.basename(f)}")
    except:
        pass
print("✅ Clean slate")

# Initialize finlab
print("\n[1/3] Initializing finlab...")
try:
    import finlab
    finlab.login(os.environ['FINLAB_API_TOKEN'])
    from finlab import data
    print(f"✅ finlab {finlab.__version__} initialized")

    # Verify alternative revenue growth dataset
    print("   Testing fundamental revenue growth...")
    revenue_growth = data.get('fundamental_features:營收成長率')
    print(f"   ✅ Revenue growth: {revenue_growth.shape}")

    class FinlabData:
        def __init__(self):
            self._data = data
        def get(self, key):
            return self._data.get(key)

    finlab_data = FinlabData()

except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Create ultra-simple template inline (bypass file loading issues)
print("\n[2/3] Creating inline template...")
template = """You are a Taiwan stock trading strategy developer.

**CRITICAL**: DO NOT use 'monthly_revenue' datasets. They cause errors.

**USE ONLY THESE**:
- price:收盤價, price:成交股數, price:成交金額
- fundamental_features:營收成長率 (revenue growth - USE THIS!)
- fundamental_features:ROE稅後, fundamental_features:本益比

**TEMPLATE**:
```python
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
trading_value = data.get('price:成交金額')
revenue_growth = data.get('fundamental_features:營收成長率')
roe = data.get('fundamental_features:ROE稅後')

momentum = close.pct_change(20).shift(1)
growth = revenue_growth.ffill().shift(1)
quality = roe.ffill().shift(1)

combined = momentum * 0.4 + growth * 0.3 + quality * 0.3

liquidity = trading_value.rolling(20).mean().shift(1) > 50_000_000
price_ok = close.shift(1) > 10

position = combined[liquidity & price_ok].is_largest(10)
report = sim(position, resample="Q", upload=False, stop_loss=0.08)
```

Create similar strategy. NO monthly_revenue! Return ONLY code.
"""

# Save inline template
with open('/mnt/c/Users/jnpi/Documents/finlab/prompt_template_inline.txt', 'w', encoding='utf-8') as f:
    f.write(template)
print("✅ Inline template created")

# Run with clean state
print("\n[3/3] Running with clean state...")
print("   Model: google/gemini-2.5-flash")
print("   Iterations: 3 (quick test)")
print("   NO HISTORY FEEDBACK")
print()

try:
    from autonomous_loop import AutonomousLoop

    loop = AutonomousLoop(
        model="google/gemini-2.5-flash",
        max_iterations=3,  # Fewer iterations for quick test
        history_file="mvp_final_clean_history.json"
    )

    # Use inline template
    loop.prompt_builder.template_file = 'prompt_template_inline.txt'
    loop.prompt_builder.base_template = loop.prompt_builder._load_template()

    # Clear to ensure no history
    loop.history.clear()

    # Run WITHOUT data parameter to force error early if wrong key used
    results = loop.run(data=finlab_data)

    print("\n" + "="*60)
    print("FINAL CLEAN RESULTS")
    print("="*60)

    print(f"\nExecution Summary:")
    print(f"  Total: {results['total_iterations']}")
    print(f"  ✅ Success: {results['successful_iterations']}")
    print(f"  ❌ Failed: {results['failed_iterations']}")
    print(f"  ⏱️  Time: {results['elapsed_time']:.1f}s")

    if results['successful_iterations'] > 0:
        rate = results['successful_iterations'] / results['total_iterations'] * 100
        print(f"  📊 Success rate: {rate:.1f}%")

        successful = loop.history.get_successful_iterations()
        print(f"\n🎉 {len(successful)} SUCCESSFUL STRATEGIES!")

        for record in successful:
            print(f"\n📊 Iteration {record.iteration_num}:")
            # Check what datasets were actually used
            if 'monthly_revenue' in record.code:
                print("   ⚠️  WARNING: Still used monthly_revenue somehow")
            else:
                print("   ✅ Used correct datasets")

            if record.metrics:
                print(f"   Sharpe: {record.metrics.get('sharpe_ratio', 0):.4f}")
                print(f"   Return: {record.metrics.get('total_return', 0):.4f}")

                with open(f'working_strategy_{record.iteration_num}.py', 'w') as f:
                    f.write(record.code)
                print(f"   💾 Saved: working_strategy_{record.iteration_num}.py")
    else:
        print("\n❌ All failed")
        for i, r in enumerate(loop.history.records):
            err = r.execution_error[:80] if r.execution_error else 'Unknown'
            print(f"  [{i}] {err}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
