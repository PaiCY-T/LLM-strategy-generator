# Population-Based Learning Validation Report

**Generated**: 2025-10-19 23:30:24
**Configuration**: N=20, Generations=20
**Status**: ❌ **FAILED**

---

## Executive Summary

This validation report evaluates the population-based learning system against production success criteria using a 20-generation test with population size N=20.

⚠️ **Some success criteria not met. Further tuning recommended.**

---

## Success Criteria Results

### Champion Update Rate ≥10%

- **Status**: ❌ FAIL
- **Actual**: 0.0%
- **Threshold**: ≥10%

### Rolling Variance <0.5

- **Status**: ✅ PASS
- **Actual**: 0.3359
- **Threshold**: <0.5

### P-value <0.05

- **Status**: ✅ PASS
- **Actual**: 0.0060
- **Threshold**: <0.05

### Pareto Front Size ≥5

- **Status**: ❌ FAIL
- **Actual**: 1
- **Threshold**: ≥5

---

## Detailed Analysis

### Champion Update Rate

Champion update rate measures the percentage of generations where the global best strategy improved. This indicates continuous learning and adaptation.

- **Result**: 0.0%
- **Updates**: 0/20 generations
- **Interpretation**: Low update rate suggests premature convergence or insufficient diversity

### Rolling Variance

Rolling variance of final generation Sharpe ratios measures population diversity. Lower values indicate convergence to similar strategies.

- **Result**: 0.3359
- **Interpretation**: Healthy convergence with maintained diversity

### Statistical Significance

T-test comparing final population against random baseline (initial generation) validates that evolution produces superior strategies.

- **P-value**: 0.0060
- **Cohen's d**: 2.341
- **Effect Size**: Large
- **Interpretation**: Evolution significantly outperforms random baseline

### Pareto Front Size

Number of non-dominated strategies in the final generation. Larger fronts indicate successful multi-objective optimization.

- **Result**: 1 strategies
- **Interpretation**: Limited diversity in Pareto front

---

## Generation History

| Gen | Diversity | Pareto Size | Champion Updated | Best Sharpe | Time (s) |
|-----|-----------|-------------|------------------|-------------|----------|
|  1  | 0.189     |           0 |                  |       4.884 |     0.01 |
|  2  | 0.100     |           1 |                  |       6.043 |     0.10 |
|  3  | 0.100     |           1 |                  |       6.043 |     0.18 |
|  4  | 0.100     |           1 |                  |       6.043 |     0.12 |
|  5  | 0.100     |           1 |                  |       6.043 |     0.11 |
|  6  | 0.100     |           1 |                  |       6.043 |     0.11 |
|  7  | 0.100     |           1 |                  |       6.043 |     0.15 |
|  8  | 0.100     |           1 |                  |       6.043 |     0.09 |
|  9  | 0.100     |           1 |                  |       6.043 |     0.09 |
| 10  | 0.100     |           1 |                  |       6.043 |     0.15 |
| 11  | 0.100     |           1 |                  |       6.043 |     0.19 |
| 12  | 0.100     |           1 |                  |       6.043 |     0.13 |
| 13  | 0.100     |           1 |                  |       6.043 |     0.13 |
| 14  | 0.100     |           1 |                  |       6.043 |     0.12 |
| 15  | 0.100     |           1 |                  |       6.043 |     0.18 |
| 16  | 0.100     |           1 |                  |       6.043 |     0.12 |
| 17  | 0.100     |           1 |                  |       6.043 |     0.11 |
| 18  | 0.100     |           1 |                  |       6.043 |     0.11 |
| 19  | 0.100     |           1 |                  |       6.043 |     0.14 |
| 20  | 0.100     |           1 |                  |       6.043 |     0.15 |

---

## Diversity Trend Analysis

- **Average Diversity**: 0.104
- **Range**: [0.100, 0.189]
- **Trend**: Stable

---

## Performance Metrics

- **Total Runtime**: 2.48 seconds (0.04 minutes)
- **Average Generation Time**: 0.12 seconds
- **Total Generations**: 20

---

## Recommendations

⚠️ **Tuning Recommended**

- **Champion Update Rate**: Increase mutation rate or diversity mechanisms
- **Pareto Front Size**: Enhance diversity preservation or multi-objective selection

**Next Steps**:
1. Apply recommended tuning
2. Re-run validation test
3. Iterate until all criteria met

---

## Appendix

### Configuration Details

- **Population Size**: 20
- **Generations**: 20
- **Elite Count**: 2 (default)
- **Tournament Size**: 3 (default)
- **Checkpoint Directory**: validation_checkpoints

### Success Criteria Source

All success criteria are derived from the system requirements document:
- Champion update rate: Measures continuous learning (R9.1)
- Rolling variance: Validates convergence quality (R6.2)
- P-value: Statistical validation of improvement (R9.2)
- Pareto front size: Multi-objective diversity (R6.1)

---

**End of Report**
