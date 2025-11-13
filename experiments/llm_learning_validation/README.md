# LLM Learning Validation Experiment

Scientifically validate whether LLM-driven learning can breakthrough Factor Graph template limitations.

## Quick Start

### 1. Execute Pilot (300 iterations, ~2 hours)

```bash
python experiments/llm_learning_validation/orchestrator.py --phase pilot
```

### 2. Analyze Results

```bash
python experiments/llm_learning_validation/orchestrator.py --analyze pilot
```

### 3. View Report

```bash
open experiments/llm_learning_validation/results/experiment_report.html
```

## Experiment Design

**3 Experimental Groups**:
- **Hybrid**: 30% LLM + 70% Factor Graph (current production setting)
- **FG-Only**: 0% LLM (baseline control)
- **LLM-Only**: 100% LLM (maximum innovation)

**Pilot Phase**: 300 iterations (50 iterations × 2 runs × 3 groups)

**Full Study**: 3000 iterations (200 iterations × 5 runs × 3 groups) - conditional on GO decision

## Output Files

```
results/
├── pilot_results.json          # Raw experiment data
├── hybrid_run1_history.jsonl   # Iteration history per run
├── hybrid_run1_champion.json   # Best strategy per run
├── experiment_report.html      # Comprehensive analysis report
├── learning_curves.png         # Visualizations
└── distribution_comparison.png
```

## Configuration

Edit `experiments/llm_learning_validation/config.yaml`:
- Adjust iterations per run
- Modify novelty weights
- Change innovation rates

## Dry Run Testing

Before running the full pilot, validate the pipeline with a quick dry run:

```bash
# Execute dry run (15 iterations total: 5 × 1 × 3 groups)
python experiments/llm_learning_validation/orchestrator.py \
  --phase pilot \
  --config experiments/llm_learning_validation/config_dry_run.yaml

# Analyze dry run results
python experiments/llm_learning_validation/orchestrator.py \
  --analyze pilot \
  --config experiments/llm_learning_validation/config_dry_run.yaml
```

The dry run should complete in ~10-15 minutes and validates:
- All 3 groups execute successfully
- Novelty scores are calculated
- Statistical tests run (may not be significant with small n)
- HTML report generates without errors

## Troubleshooting

**Issue**: Learning loop fails
**Solution**: Check `config/learning_system.yaml` is valid

**Issue**: No LLM calls in LLM-Only group
**Solution**: Verify `GEMINI_API_KEY` environment variable is set

**Issue**: Novelty scores all zero
**Solution**: Ensure Factor Graph templates exist in expected directory

**Issue**: Import errors
**Solution**: Ensure you're running from the project root directory

## Architecture

### Component Flow

```
Orchestrator
  ├─> ExperimentConfig (Track 1)
  ├─> LearningLoop per group
  │    ├─> IterationExecutor
  │    ├─> LLMClient (innovation_rate dependent)
  │    ├─> BacktestExecutor
  │    └─> ChampionTracker
  ├─> NoveltyScorer (Track 2)
  │    ├─> FactorDiversityAnalyzer
  │    ├─> CombinationPatternAnalyzer
  │    └─> LogicComplexityAnalyzer
  ├─> StatisticalPipeline (Track 3)
  │    ├─> MannWhitneyAnalyzer
  │    └─> MannKendallAnalyzer
  └─> ReportGeneration
       ├─> ExperimentVisualizer
       └─> HTMLReportGenerator
```

### Key Parameters

- **innovation_rate**: Controls LLM vs Factor Graph ratio
  - 0.0 = 100% Factor Graph (fg_only group)
  - 0.3 = 30% LLM, 70% Factor Graph (hybrid group)
  - 1.0 = 100% LLM (llm_only group)

- **novelty weights**: 3-layer weighted scoring
  - factor_diversity: 0.30
  - combination_patterns: 0.40
  - logic_complexity: 0.30

## Results Interpretation

### Statistical Significance

- **p < 0.05**: Strong evidence of difference (reject null hypothesis)
- **0.05 < p < 0.10**: Marginal evidence (exploratory phase acceptable)
- **p > 0.10**: Insufficient evidence

### Go/No-Go Decision Matrix

| Significant MW Tests | Significant Trends | Recommendation |
|---------------------|-------------------|----------------|
| ≥ 2/3              | ≥ 1/3             | GO             |
| 1/3                | Any               | CONDITIONAL GO |
| 0/3                | Any               | NO-GO          |

### Champion Quality Thresholds

- **Sharpe > 0.8**: Excellent (proceed with confidence)
- **0.5 < Sharpe < 0.8**: Good (proceed with caution)
- **Sharpe < 0.5**: Weak (refine before proceeding)

## Testing

Run the orchestrator test suite:

```bash
pytest tests/experiments/test_orchestrator.py -v
```

## Advanced Usage

### Custom Configuration

Create a custom config file:

```yaml
experiment:
  name: "custom-experiment"
  version: "1.0.0"

groups:
  custom_group:
    name: "Custom"
    innovation_rate: 0.50  # 50% LLM
    description: "Custom innovation rate"

phases:
  pilot:
    iterations_per_run: 20
    num_runs: 3
    total_iterations: 60  # 20 × 3 × 1 group
```

Run with custom config:

```bash
python experiments/llm_learning_validation/orchestrator.py \
  --phase pilot \
  --config path/to/custom_config.yaml
```

### Resumability

If an experiment is interrupted, results are saved incrementally. To resume:

1. Check which runs completed: `ls results/*_history.jsonl`
2. Manually edit `pilot_results.json` to remove incomplete runs
3. Re-run the experiment (it will skip completed runs automatically)

### Debugging

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python experiments/llm_learning_validation/orchestrator.py --phase pilot
```

Check orchestrator logs:

```bash
tail -f experiments/llm_learning_validation/results/orchestrator.log
```

## Performance Expectations

### Dry Run (15 iterations)
- Duration: ~10-15 minutes
- Output: ~3 MB
- Statistical power: Low (validation only)

### Pilot Phase (300 iterations)
- Duration: ~2-3 hours
- Output: ~50-100 MB
- Statistical power: Moderate (exploratory)

### Full Study (3000 iterations)
- Duration: ~20-30 hours
- Output: ~500 MB - 1 GB
- Statistical power: High (confirmatory)

## Citation

If you use this experiment framework in research, please cite:

```
LLM Learning Validation Framework
Finlab Autonomous Trading System
Track 4: Experiment Orchestrator
Version 1.0.0
```

## Support

For issues or questions:
1. Check this README
2. Review logs in `results/orchestrator.log`
3. Run dry run for quick validation
4. Check test suite results
