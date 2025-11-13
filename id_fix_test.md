# Population-Based Learning Validation Report

**Generated**: 2025-10-24 08:49:43
**Configuration**: N=6, Generations=3
**Status**: ❌ **FAILED**

---

## Executive Summary

This validation report evaluates the population-based learning system against production success criteria using a 3-generation test with population size N=6.

⚠️ **Some success criteria not met. Further tuning recommended.**

---

## Success Criteria Results

### Champion Update Rate ≥10%

- **Status**: ❌ FAIL
- **Actual**: 0.0%
- **Threshold**: ≥10%

### Rolling Variance <0.5

- **Status**: ✅ PASS
- **Actual**: 0.0000
- **Threshold**: <0.5

### P-value <0.05

- **Status**: ❌ FAIL
- **Actual**: 0.4774
- **Threshold**: <0.05

### Pareto Front Size ≥5

- **Status**: ❌ FAIL
- **Actual**: 2
- **Threshold**: ≥5

---

## Detailed Analysis

### Champion Update Rate

Champion update rate measures the percentage of generations where the global best strategy improved. This indicates continuous learning and adaptation.

- **Result**: 0.0%
- **Updates**: 0/3 generations
- **Interpretation**: Low update rate suggests premature convergence or insufficient diversity

### Rolling Variance

Rolling variance of final generation Sharpe ratios measures population diversity. Lower values indicate convergence to similar strategies.

- **Result**: 0.0000
- **Interpretation**: Healthy convergence with maintained diversity

### Statistical Significance

T-test comparing final population against random baseline (initial generation) validates that evolution produces superior strategies.

- **P-value**: 0.4774
- **Cohen's d**: 0.678
- **Effect Size**: Medium
- **Interpretation**: No significant improvement over random baseline

### Pareto Front Size

Number of non-dominated strategies in the final generation. Larger fronts indicate successful multi-objective optimization.

- **Result**: 2 strategies
- **Interpretation**: Limited diversity in Pareto front

---

## Generation History

| Gen | Diversity | Pareto Size | Champion Updated | Best Sharpe | Time (s) |
|-----|-----------|-------------|------------------|-------------|----------|
|  1  | 0.533     |           3 |                  |       0.889 |     0.00 |
|  2  | 0.333     |           6 |                  |       0.889 |    25.80 |
|  3  | 0.333     |           2 |                  |       0.889 |    27.61 |

---

## Diversity Trend Analysis

- **Average Diversity**: 0.400
- **Range**: [0.333, 0.533]
- **Trend**: Stable

---

## Performance Metrics

- **Total Runtime**: 53.41 seconds (0.89 minutes)
- **Average Generation Time**: 17.80 seconds
- **Total Generations**: 3

---

## Recommendations

⚠️ **Tuning Recommended**

- **Champion Update Rate**: Increase mutation rate or diversity mechanisms
- **Statistical Significance**: Run longer (more generations) or increase population size
- **Pareto Front Size**: Enhance diversity preservation or multi-objective selection

**Next Steps**:
1. Apply recommended tuning
2. Re-run validation test
3. Iterate until all criteria met

---

## Appendix

### Configuration Details

- **Population Size**: 6
- **Generations**: 3
- **Elite Count**: 2 (default)
- **Tournament Size**: 3 (default)
- **Checkpoint Directory**: id_fix_checkpoints

### Success Criteria Source

All success criteria are derived from the system requirements document:
- Champion update rate: Measures continuous learning (R9.1)
- Rolling variance: Validates convergence quality (R6.2)
- P-value: Statistical validation of improvement (R9.2)
- Pareto front size: Multi-objective diversity (R6.1)

---

**End of Report**
