"""Simplified MVP test with basic price data only.

Uses only confirmed available datasets (price data) and increased timeout.
"""

import os
import sys

# Set API credentials
os.environ['FINLAB_API_TOKEN'] = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m'
os.environ['OPENROUTER_API_KEY'] = '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'

print("="*60)
print("MVP SIMPLE - BASIC PRICE DATA ONLY")
print("="*60)
print()

# Initialize finlab
print("[1/3] Initializing finlab...")
try:
    import finlab
    finlab.login(os.environ['FINLAB_API_TOKEN'])
    from finlab import data
    print(f"✅ finlab {finlab.__version__} initialized")

    # Load only confirmed available data
    print("   Loading price data...")
    close = data.get('price:收盤價')
    volume = data.get('price:成交股數')
    print(f"   ✅ Data loaded: {close.shape[1]} stocks, {close.shape[0]} days")

    # Create wrapper
    class FinlabData:
        """Minimal wrapper with only price data."""
        def __init__(self):
            self._data = data

        def get(self, key):
            """Get dataset."""
            return self._data.get(key)

    finlab_data = FinlabData()

except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

# Update prompt template to use only price data
print("\n[2/3] Updating prompt template...")
try:
    with open('prompt_template_simple.txt', 'w', encoding='utf-8') as f:
        f.write("""You are an expert quantitative trading strategy developer for Taiwan stock market.

**CRITICAL CONSTRAINTS**:
1. NO import statements allowed - data.get() provides all data
2. Only use POSITIVE shift values: .shift(1), .shift(2), etc.
3. Available datasets (CONFIRMED):
   - price:收盤價 (close price)
   - price:成交股數 (volume)
   - price:成交金額 (trading value)
   - price:開盤價 (open price)
   - price:最高價 (high price)
   - price:最低價 (low price)

**TASK**: Create a simple but effective trading strategy using ONLY the confirmed price datasets above.

**CODE STRUCTURE**:
```python
# 1. Load data (ONLY use confirmed datasets above!)
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
trading_value = data.get('price:成交金額')

# 2. Calculate factors (use price-based factors only)
# Example: momentum, volatility, volume patterns

# 3. Combine factors
# Create a combined factor score

# 4. Apply filters
# Filter by liquidity and price

# 5. Select stocks
# position = combined_factor[filters].is_largest(10)

# 6. Run backtest
# report = sim(position, resample="Q", upload=False)
```

**REQUIREMENTS**:
- Keep it SIMPLE - only 2-3 factors
- Use .shift() properly to avoid look-ahead bias
- Filter for liquidity (trading_value > 50M TWD)
- Select top 10 stocks
- No stop_loss (simplify for speed)

Generate the complete strategy code:
""")
    print("✅ Simple prompt template created")
except Exception as e:
    print(f"❌ Template creation failed: {e}")
    sys.exit(1)

# Run autonomous loop with simple template and longer timeout
print("\n[3/3] Running simplified loop...")
print("   Model: google/gemini-2.5-flash")
print("   Max iterations: 3 (testing)")
print("   Timeout: 120s (increased)")
print("   Data: Price data only")
print()

try:
    from autonomous_loop import AutonomousLoop

    # Create custom loop with simple template
    loop = AutonomousLoop(
        model="google/gemini-2.5-flash",
        max_iterations=3,
        history_file="mvp_simple_history.json"
    )

    # Override template file
    loop.prompt_builder.template_file = 'prompt_template_simple.txt'
    loop.prompt_builder.base_template = loop.prompt_builder._load_template()

    # Clear history
    loop.history.clear()

    # Run with real data
    results = loop.run(data=finlab_data)

    print("\n" + "="*60)
    print("SIMPLE MVP RESULTS")
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
