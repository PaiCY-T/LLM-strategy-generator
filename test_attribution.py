"""Test attribution system with real iteration data."""

from performance_attributor import (
    extract_strategy_params,
    compare_strategies,
    generate_attribution_feedback
)

# Load real iteration codes
with open('generated_strategy_loop_iter0.py') as f:
    code_iter0 = f.read()

with open('generated_strategy_loop_iter1.py') as f:
    code_iter1 = f.read()

with open('generated_strategy_loop_iter2.py') as f:
    code_iter2 = f.read()

# Extract parameters
print("Extracting parameters from iterations...\n")
params_0 = extract_strategy_params(code_iter0)
params_1 = extract_strategy_params(code_iter1)
params_2 = extract_strategy_params(code_iter2)

print("Iteration 0 parameters:")
for key, value in params_0.items():
    print(f"  {key}: {value}")

print("\nIteration 1 parameters:")
for key, value in params_1.items():
    print(f"  {key}: {value}")

print("\nIteration 2 parameters:")
for key, value in params_2.items():
    print(f"  {key}: {value}")

# Real metrics from history
metrics_0 = {
    'sharpe_ratio': 0.36,
    'total_return': 0.61,
    'max_drawdown': -0.14
}

metrics_1 = {
    'sharpe_ratio': 0.97,
    'total_return': 0.10,
    'max_drawdown': -0.46
}

metrics_2 = {
    'sharpe_ratio': -0.35,
    'total_return': 0.38,
    'max_drawdown': -0.41
}

# Compare 0 → 1 (improvement)
print("\n" + "="*70)
print("COMPARISON: Iteration 0 → 1 (The Success)")
print("="*70)
comparison_01 = compare_strategies(params_0, params_1, metrics_0, metrics_1)
feedback_01 = generate_attribution_feedback(comparison_01, 1, champion_iteration=1)
print(feedback_01)

# Compare 1 → 2 (regression)
print("\n" + "="*70)
print("COMPARISON: Iteration 1 → 2 (The Regression)")
print("="*70)
comparison_12 = compare_strategies(params_1, params_2, metrics_1, metrics_2)
feedback_12 = generate_attribution_feedback(comparison_12, 2, champion_iteration=1)
print(feedback_12)
