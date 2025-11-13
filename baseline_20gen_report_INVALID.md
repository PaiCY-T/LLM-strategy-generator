# Population-Based Learning Validation Report

**Generated**: 2025-10-24 06:52:49
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
- **Actual**: 0.0000
- **Threshold**: <0.5

### P-value <0.05

- **Status**: ❌ FAIL
- **Actual**: 0.0586
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
- **Updates**: 0/20 generations
- **Interpretation**: Low update rate suggests premature convergence or insufficient diversity

### Rolling Variance

Rolling variance of final generation Sharpe ratios measures population diversity. Lower values indicate convergence to similar strategies.

- **Result**: 0.0000
- **Interpretation**: Healthy convergence with maintained diversity

### Statistical Significance

T-test comparing final population against random baseline (initial generation) validates that evolution produces superior strategies.

- **P-value**: 0.0586
- **Cohen's d**: 1.526
- **Effect Size**: Large
- **Interpretation**: No significant improvement over random baseline

### Pareto Front Size

Number of non-dominated strategies in the final generation. Larger fronts indicate successful multi-objective optimization.

- **Result**: 2 strategies
- **Interpretation**: Limited diversity in Pareto front

---

## Generation History

| Gen | Diversity | Pareto Size | Champion Updated | Best Sharpe | Time (s) |
|-----|-----------|-------------|------------------|-------------|----------|
|  1  | 0.189     |           2 |                  |       1.145 |     0.02 |
|  2  | 0.100     |           2 |                  |       1.145 |   173.51 |
|  3  | 0.100     |           2 |                  |       1.145 |   139.00 |
|  4  | 0.100     |           2 |                  |       1.145 |   141.33 |
|  5  | 0.100     |          20 |                  |       1.145 |   150.09 |
|  6  | 0.100     |          20 |                  |       1.145 |   149.63 |
|  7  | 0.100     |          20 |                  |       1.145 |   139.94 |
|  8  | 0.100     |          20 |                  |       1.145 |   123.88 |
|  9  | 0.100     |          20 |                  |       1.145 |   107.44 |
| 10  | 0.100     |          20 |                  |       1.145 |   108.67 |
| 11  | 0.100     |          20 |                  |       1.145 |   111.03 |
| 12  | 0.100     |          20 |                  |       1.145 |   106.54 |
| 13  | 0.100     |          20 |                  |       1.145 |   112.65 |
| 14  | 0.100     |          20 |                  |       1.145 |   117.50 |
| 15  | 0.100     |          20 |                  |       1.145 |   110.95 |
| 16  | 0.100     |          20 |                  |       1.145 |   120.23 |
| 17  | 0.100     |          20 |                  |       1.145 |   111.29 |
| 18  | 0.100     |          20 |                  |       1.145 |   111.62 |
| 19  | 0.100     |          20 |                  |       1.145 |   109.69 |
| 20  | 0.100     |           2 |                  |       1.145 |   108.34 |

---

## Diversity Trend Analysis

- **Average Diversity**: 0.104
- **Range**: [0.100, 0.189]
- **Trend**: Stable

---

## Performance Metrics

- **Total Runtime**: 2353.37 seconds (39.22 minutes)
- **Average Generation Time**: 117.67 seconds
- **Total Generations**: 20

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

- **Population Size**: 20
- **Generations**: 20
- **Elite Count**: 2 (default)
- **Tournament Size**: 3 (default)
- **Checkpoint Directory**: baseline_checkpoints

### Success Criteria Source

All success criteria are derived from the system requirements document:
- Champion update rate: Measures continuous learning (R9.1)
- Rolling variance: Validates convergence quality (R6.2)
- P-value: Statistical validation of improvement (R9.2)
- Pareto front size: Multi-objective diversity (R6.1)

---

**End of Report**
