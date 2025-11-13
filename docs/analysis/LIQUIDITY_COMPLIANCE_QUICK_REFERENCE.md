# Liquidity Compliance Checker - Quick Reference

## Usage

### Run Compliance Check
```bash
python3 analyze_metrics.py
```

This will:
1. Analyze all iterations in iteration_history.json
2. Check liquidity compliance for each strategy file
3. Log results to liquidity_compliance.json
4. Display compliance summary

### View Compliance Statistics Only
```python
from analyze_metrics import get_compliance_statistics

stats = get_compliance_statistics()
print(f"Compliance rate: {stats['compliance_rate']:.1%}")
print(f"Non-compliant iterations: {stats['non_compliant_iterations']}")
```

### Check Single Strategy
```python
from analyze_metrics import check_liquidity_compliance

result = check_liquidity_compliance(
    iteration_num=0,
    strategy_file='generated_strategy_iter0.py',
    min_threshold=150_000_000  # 150M TWD
)

print(f"Threshold found: {result['threshold_found']}")
print(f"Compliant: {result['compliant']}")
```

### Extract Threshold from Code
```python
from analyze_metrics import extract_liquidity_threshold

with open('generated_strategy_iter0.py', 'r') as f:
    code = f.read()

threshold = extract_liquidity_threshold(code)
print(f"Threshold: {threshold:,} TWD" if threshold else "No threshold found")
```

## Output Format

### Console Output
```
💧 Liquidity Compliance Check:
============================================================
  ❌ Iter  0: Threshold = 100,000,000 TWD
  ✅ Iter  1: Threshold = 200,000,000 TWD
  ❌ Iter  2: Threshold = Not found

📊 Compliance Summary:
  Total checks: 30
  Compliant: 1
  Compliance rate: 3.3%
  Average threshold: 51,058,824 TWD
  Non-compliant iterations: [0, 2, 3, ...]
```

### JSON Log Structure
```json
{
  "checks": [
    {
      "iteration": 0,
      "threshold_found": 100000000,
      "compliant": false,
      "timestamp": "2025-10-10T08:14:45.054636",
      "strategy_file": "generated_strategy_loop_iter0.py",
      "min_threshold": 150000000
    }
  ],
  "summary": {
    "total_checks": 125,
    "compliant_count": 0,
    "compliance_rate": 0.0,
    "last_updated": "2025-10-10T08:14:56.726293"
  }
}
```

## Supported Threshold Patterns

The checker recognizes these patterns:

1. **Direct comparison**:
   ```python
   trading_value.rolling(20).mean() > 150_000_000
   ```

2. **With shift**:
   ```python
   trading_value.rolling(20).mean().shift(1) > 150_000_000
   ```

3. **Via variable**:
   ```python
   avg_trading_value = trading_value.rolling(20).mean().shift(1)
   liquidity_filter = avg_trading_value > 150_000_000
   ```

4. **In filter definition**:
   ```python
   liquidity_filter = trading_value.rolling(20).mean().shift(1) > 150_000_000
   ```

## Files

- **analyze_metrics.py**: Main implementation (458 lines)
- **liquidity_compliance.json**: Compliance log (auto-generated)
- **test_liquidity_compliance.py**: Unit tests (100 lines)
- **TASK1_LIQUIDITY_COMPLIANCE_SUMMARY.md**: Full documentation (176 lines)

## Default Settings

- **Minimum threshold**: 150,000,000 TWD (150 million)
- **Log file**: liquidity_compliance.json
- **Supported file patterns**:
  - generated_strategy_loop_iter{N}.py
  - generated_strategy_iter{N}.py

## Customization

### Change Minimum Threshold
```python
result = check_liquidity_compliance(
    iteration_num=0,
    strategy_file='strategy.py',
    min_threshold=200_000_000  # 200M TWD
)
```

### Use Custom Log File
```python
from analyze_metrics import log_compliance_result

log_compliance_result(result, log_file='custom_compliance.json')
```

## Error Handling

The checker handles:
- ✅ Missing strategy files (logs error, continues)
- ✅ Syntax errors in strategy code (uses regex fallback)
- ✅ Empty files (returns None threshold)
- ✅ Multiple threshold patterns (supports all common formats)
- ✅ Corrupted JSON log files (rebuilds automatically)

## Next Steps

See Task 2 implementation for:
- Automated liquidity violation reporting
- Integration with iteration engine
- Real-time compliance monitoring
