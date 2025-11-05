# Exit Mutation Long-Running Validation Report

**Generated**: 2025-10-20T18:41:16.421134

## Executive Summary

**Decision**: ⚠️  OPTIMIZATION NEEDED - Address stability/success rate issues

### Phase 2a Readiness Criteria

- ❌ FAIL: Sharpe Target
- ✅ PASS: Diversity Target
- ❌ FAIL: Success Rate Target
- ✅ PASS: Stability Ok
- ❌ FAIL: Performance Maintained

## Performance Analysis

- **Initial Sharpe**: 1.7384
- **Final Sharpe**: 1.7384
- **Best Sharpe**: 1.7384
- **Improvement**: +0.0000
- **Avg Improvement Rate**: 0.0000/gen
- **Plateaued**: Yes ⚠️

### Sharpe Ratio Progression

```
Gen  0: 1.7384 ██████████████████████████████████
Gen  1: 1.7384 ██████████████████████████████████
Gen  2: 1.7384 ██████████████████████████████████
Gen  3: 1.7384 ██████████████████████████████████
Gen  4: 1.7384 ██████████████████████████████████
Gen  5: 1.7384 ██████████████████████████████████
Gen  6: 1.7384 ██████████████████████████████████
Gen  7: 1.7384 ██████████████████████████████████
Gen  8: 1.7384 ██████████████████████████████████
Gen  9: 1.7384 ██████████████████████████████████
Gen 10: 1.7384 ██████████████████████████████████
```

## Diversity Analysis

- **Unique Exit Patterns**: 3
- **Jaccard Diversity**: 0.304
- **Exit Patterns Found**:
  - stop_loss
  - basic
  - take_profit

## Exit Mutation Analysis

- **Total Attempts**: 51
- **Successes**: 0
- **Failures**: 51
- **Success Rate**: 0.00%

### Mutation Types Distribution

- Parametric: 0
- Structural: 0
- Relational: 0

## Stability Analysis

- **Total Issues**: 0

✅ No stability issues detected

## Generation Breakdown

| Gen | Best Sharpe | Mutations | Success Rate | Patterns | Time |
|-----|-------------|-----------|--------------|----------|------|
| 1 | 1.7384 | 5 | 0.00% | 3 | 0.0s |
| 2 | 1.7384 | 3 | 0.00% | 3 | 0.8s |
| 3 | 1.7384 | 6 | 0.00% | 3 | 0.3s |
| 4 | 1.7384 | 0 | 0.00% | 3 | 0.2s |
| 5 | 1.7384 | 4 | 0.00% | 3 | 0.1s |
| 6 | 1.7384 | 7 | 0.00% | 3 | 0.2s |
| 7 | 1.7384 | 7 | 0.00% | 3 | 0.2s |
| 8 | 1.7384 | 7 | 0.00% | 3 | 0.1s |
| 9 | 1.7384 | 6 | 0.00% | 3 | 0.2s |
| 10 | 1.7384 | 6 | 0.00% | 3 | 0.2s |

## Decision Recommendation

**Recommendation**: ⚠️  OPTIMIZATION NEEDED - Address stability/success rate issues

### Next Steps

1. Address exit mutation success rate issues
2. Fix stability problems before proceeding
3. Re-run validation after fixes
4. Consider parameter tuning for mutation operator

## Timing Summary

- **Total Time**: 0.0 minutes
- **Avg Generation Time**: 0.2s
- **Generations Completed**: 10/10
