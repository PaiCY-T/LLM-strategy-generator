# Pilot Test Execution Guide - 20 Iterations

**Date**: 2025-11-13
**Purpose**: Run Phase 7 E2E validation after Phase 3.3 dict interface fix
**Expected Outcome**: 100% → 0% failure rate

## Test Configurations

### 📁 Configuration Files

Three pilot configurations located in `experiments/llm_learning_validation/`:

1. **`config_pilot_llm_only_20.yaml`**
   - **Group**: LLM-Only
   - **Innovation Rate**: 100% LLM, 0% Factor Graph
   - **Iterations**: 20
   - **Description**: Maximum LLM innovation test
   - **Results Dir**: `experiments/llm_learning_validation/results/pilot_llm_only_20/`

2. **`config_pilot_fg_only_20.yaml`**
   - **Group**: Factor Graph Only
   - **Innovation Rate**: 0% LLM, 100% Factor Graph
   - **Iterations**: 20
   - **Description**: Baseline control group
   - **Results Dir**: `experiments/llm_learning_validation/results/pilot_fg_only_20/`

3. **`config_pilot_hybrid_20.yaml`**
   - **Group**: Hybrid
   - **Innovation Rate**: 30% LLM, 70% Factor Graph
   - **Iterations**: 20
   - **Description**: Current production configuration
   - **Results Dir**: `experiments/llm_learning_validation/results/pilot_hybrid_20/`

## Quick Start

### Option 1: Python Script (Recommended for Windows)

```bash
# Run all three tests sequentially
python3 run_pilot_tests_20.py
```

### Option 2: Bash Script (Linux/Mac)

```bash
# Make executable
chmod +x run_pilot_tests_20.sh

# Run all three tests
./run_pilot_tests_20.sh
```

### Option 3: Manual Execution

Run each test individually:

```bash
# Test 1: LLM-Only
python3 experiments/llm_learning_validation/orchestrator.py \
    --config experiments/llm_learning_validation/config_pilot_llm_only_20.yaml \
    --phase pilot

# Test 2: Factor Graph Only
python3 experiments/llm_learning_validation/orchestrator.py \
    --config experiments/llm_learning_validation/config_pilot_fg_only_20.yaml \
    --phase pilot

# Test 3: Hybrid
python3 experiments/llm_learning_validation/orchestrator.py \
    --config experiments/llm_learning_validation/config_pilot_hybrid_20.yaml \
    --phase pilot
```

## What to Expect

### Before Phase 3.3 Fix
- **Status**: 100% failure rate
- **Error**: `AttributeError: 'StrategyMetrics' object has no attribute 'get'`
- **Impact**: All 3 pilot tests blocked

### After Phase 3.3 Fix
- **Expected**: 0% failure rate
- **Success Criteria**:
  - All 20 iterations complete successfully
  - No AttributeError exceptions
  - Champion metrics accessible via `.get()` method
  - JSONL results properly serialized

## Monitoring Execution

### Real-time Logs

The scripts display real-time output including:
- Iteration progress (1/20, 2/20, ...)
- Strategy generation status
- Backtest results
- Champion updates
- Novelty scores

### Log Files

All output is saved to timestamped log directory:
```
experiments/llm_learning_validation/results/pilot_run_YYYYMMDD_HHMMSS/
  ├── pilot_llm_only_20.log
  ├── pilot_fg_only_20.log
  └── pilot_hybrid_20.log
```

## Results Analysis

After successful execution, analyze results:

```bash
# Generate statistical analysis and reports
python3 experiments/llm_learning_validation/orchestrator.py --analyze pilot
```

This will generate:
- Learning curves per group
- Novelty comparison plots
- Statistical test results (Mann-Whitney U, Mann-Kendall)
- HTML summary report

## Expected Runtime

- **Per Test**: ~5-10 minutes (20 iterations × 15-30 seconds each)
- **Total**: ~15-30 minutes for all 3 tests

## Success Validation

### ✅ Test Pass Criteria

Each test should show:
1. **All 20 iterations complete**
2. **No fatal exceptions**
3. **Champion updates tracked**
4. **Results saved to JSONL**
5. **Exit code 0**

### ⚠️ Known Acceptable Warnings

These warnings are expected and acceptable:
- `WARNING: Strategy backtest had negative returns`
- `WARNING: Low Sharpe ratio < 0.5`
- `INFO: No champion update (Sharpe not improved)`

### ❌ Failure Indicators

These indicate the fix is not working:
- `AttributeError: 'StrategyMetrics' object has no attribute 'get'`
- `KeyError: 'sharpe_ratio'`
- Exit code non-zero
- < 20 iterations completed

## Troubleshooting

### Common Issues

**Issue**: Import errors
```
Solution: Ensure you're in project root and Python path is correct
cd /mnt/c/Users/jnpi/documents/finlab/LLM-strategy-generator
export PYTHONPATH=$PWD:$PYTHONPATH
```

**Issue**: Config file not found
```
Solution: Verify config paths are relative to project root
ls experiments/llm_learning_validation/config_pilot_*.yaml
```

**Issue**: Permission denied on bash script
```
Solution: Make script executable
chmod +x run_pilot_tests_20.sh
```

## Post-Execution Checklist

After all tests pass:

- [ ] Review logs for any unexpected errors
- [ ] Check results directories contain JSONL files
- [ ] Verify champion.json was updated
- [ ] Run analysis to generate reports
- [ ] Update IMPLEMENTATION_STATUS.md
- [ ] Mark Phase 7 as UNBLOCKED
- [ ] Commit changes with success report

## Configuration Details

### Common Settings (All 3 Configs)

```yaml
# Novelty System (3-Layer Weighted)
novelty:
  weights:
    factor_diversity: 0.30
    combination_patterns: 0.40
    logic_complexity: 0.30

# Statistical Testing
statistics:
  significance_level: 0.05
  tests:
    - mann_whitney_u
    - mann_kendall
    - sliding_window

# Execution
execution:
  timeout_seconds: 420
  continue_on_error: false
  max_parallel_groups: 1
```

### Differences Between Configs

| Setting | LLM-Only | FG-Only | Hybrid |
|---------|----------|---------|--------|
| innovation_rate | 1.00 (100%) | 0.00 (0%) | 0.30 (30%) |
| use_factor_graph | false | true | true |
| Group Name | "LLM-Only" | "FactorGraph-Only" | "Hybrid" |

## Next Steps

1. **If All Tests Pass**:
   - Run full statistical analysis
   - Generate HTML reports
   - Update project status
   - Plan full study (200 iterations × 5 runs)

2. **If Any Test Fails**:
   - Check logs for error details
   - Verify dict interface implementation
   - Run unit tests: `pytest tests/unit/test_strategy_metrics_dict_interface.py -v`
   - Re-run failed test individually

## Support Commands

```bash
# Quick verification of dict interface
python3 verify_dict_interface_fix.py

# Run unit tests only
pytest tests/unit/test_strategy_metrics_dict_interface.py -v

# Run integration tests
pytest tests/innovation/test_prompt_builder.py -v

# Check configuration is valid
python3 -c "from experiments.llm_learning_validation.config import ExperimentConfig; \
    ExperimentConfig.load('experiments/llm_learning_validation/config_pilot_llm_only_20.yaml')"
```

## Reference

- **Implementation Details**: `docs/PHASE3_DICT_INTERFACE_FIX_COMPLETE.md`
- **Verification Script**: `verify_dict_interface_fix.py`
- **Unit Tests**: `tests/unit/test_strategy_metrics_dict_interface.py`
- **Phase 7 Status**: `.spec-workflow/steering/IMPLEMENTATION_STATUS.md`
