# Validation Workflow - Quick Reference

Fast reference guide for using the master validation workflow script.

---

## Quick Start

```bash
# Full workflow with re-validation (~7 minutes)
./scripts/run_full_validation_workflow.sh

# Quick workflow using existing results (~7 seconds)
./scripts/run_full_validation_workflow.sh --skip-revalidation

# Use specific validation file
./scripts/run_full_validation_workflow.sh --skip-revalidation \
  --validation-file phase2_validated_results_20251101_132244.json
```

---

## Options

| Option | Description |
|--------|-------------|
| `--skip-revalidation` | Skip re-validation, use existing results |
| `--validation-file <path>` | Specify validation results file |
| `--help` | Show help message |

---

## Exit Codes

| Code | Decision | Action |
|------|----------|--------|
| 0 | GO | ✅ Proceed to Phase 3 |
| 1 | CONDITIONAL_GO | ⚠️ Review mitigation plan |
| 2 | NO-GO | ❌ Fix blocking issues |
| 3+ | ERROR | 🔧 Check logs for details |

---

## Output Files

| File | Description |
|------|-------------|
| `validation_workflow_TIMESTAMP.log` | Complete workflow log |
| `duplicate_report.json` | Duplicate detection results (JSON) |
| `duplicate_report.md` | Duplicate detection report (Markdown) |
| `diversity_report.json` | Diversity analysis results (JSON) |
| `diversity_report.md` | Diversity analysis report (Markdown) |
| `diversity_report_correlation_heatmap.png` | Correlation heatmap visualization |
| `diversity_report_factor_usage.png` | Factor usage chart |
| `phase3_decision_report.md` | Final GO/NO-GO decision document |

---

## Workflow Steps

1. **Re-validation** (optional, ~7 min)
   - Execute Phase 2 with statistical validation
   - Generates: `phase2_validated_results_TIMESTAMP.json`

2. **Duplicate Detection** (~1 sec)
   - Identify duplicate strategies
   - Analyzes all strategy files in project root

3. **Diversity Analysis** (~5 sec)
   - Calculate diversity metrics
   - Generate visualizations
   - Filter to validated strategies only

4. **Decision Evaluation** (~1 sec)
   - Evaluate GO/NO-GO criteria
   - Generate comprehensive decision document
   - Return appropriate exit code

---

## Common Use Cases

### 1. First-Time Validation

```bash
# Run full workflow including re-validation
./scripts/run_full_validation_workflow.sh
```

### 2. Quick Re-Check

```bash
# Skip re-validation to save time
./scripts/run_full_validation_workflow.sh --skip-revalidation
```

### 3. Validate Specific Results

```bash
# Use a specific validation file
./scripts/run_full_validation_workflow.sh --skip-revalidation \
  --validation-file my_validation_results.json
```

### 4. Automated Pipeline

```bash
# Capture exit code for CI/CD
./scripts/run_full_validation_workflow.sh --skip-revalidation
if [ $? -eq 0 ]; then
  echo "Ready for Phase 3!"
  # Proceed to next stage
elif [ $? -eq 1 ]; then
  echo "Conditional GO - review mitigation plan"
  # Review and decide
else
  echo "NO-GO - fix issues first"
  # Block progression
fi
```

---

## Troubleshooting

### Script Won't Run

```bash
# Make sure it's executable
chmod +x scripts/run_full_validation_workflow.sh

# Check Python is available
python3 --version
```

### Missing Validation File

```bash
# List available validation files
ls -lh phase2_validated_results_*.json

# Use latest automatically (default behavior)
./scripts/run_full_validation_workflow.sh --skip-revalidation
```

### Check Logs for Errors

```bash
# Find latest workflow log
ls -lt validation_workflow_*.log | head -1

# View log file
less validation_workflow_20251103_075557.log

# Search for errors in log
grep -i "error\|fail" validation_workflow_*.log
```

---

## Reading the Reports

### Duplicate Report

```bash
# Check for duplicates
cat duplicate_report.md

# JSON format for programmatic access
python3 -c "import json; print(json.load(open('duplicate_report.json')))"
```

### Diversity Report

```bash
# Read diversity analysis
cat diversity_report.md

# View visualizations
xdg-open diversity_report_correlation_heatmap.png  # Linux
open diversity_report_correlation_heatmap.png      # macOS
```

### Decision Report

```bash
# Read final decision
cat phase3_decision_report.md

# Extract key metrics
grep -E "Decision|Diversity Score|Correlation" phase3_decision_report.md
```

---

## Performance Tips

1. **Skip Re-validation When Possible**
   - Re-validation takes ~7 minutes
   - Use existing results for quick checks
   - Only re-validate when strategies change

2. **Monitor Log Files**
   - Logs are timestamped
   - Keep for audit trail
   - Clean up old logs periodically

3. **Parallel Execution**
   - Don't run multiple workflows simultaneously
   - They overwrite the same output files
   - Use different directories if needed

---

## Decision Criteria

### GO Criteria

- ✅ Minimum 3 unique strategies
- ✅ Diversity score ≥ 60
- ✅ Average correlation < 0.8
- ✅ Validation framework fixed
- ✅ 100% execution success rate

### CONDITIONAL GO Criteria

- ✅ Minimum 3 unique strategies
- ✅ Diversity score ≥ 40
- ✅ Average correlation < 0.8
- ✅ Validation framework fixed
- ✅ 100% execution success rate

### NO-GO

- ❌ Any critical criterion fails
- ❌ Diversity score < 40
- ❌ Average correlation ≥ 0.8
- ❌ Less than 3 unique strategies

---

## Integration with Other Tools

### Use in Scripts

```bash
#!/bin/bash
# Example automation script

cd /path/to/finlab
./scripts/run_full_validation_workflow.sh --skip-revalidation

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "GO decision - proceeding to Phase 3"
  # Run Phase 3 scripts here
elif [ $EXIT_CODE -eq 1 ]; then
  echo "CONDITIONAL GO - manual review required"
  # Notify team for review
else
  echo "NO-GO - blocking issues detected"
  # Alert team, block progression
fi
```

### Use with Make

```makefile
# Add to Makefile
validate:
	./scripts/run_full_validation_workflow.sh --skip-revalidation

validate-full:
	./scripts/run_full_validation_workflow.sh

phase3: validate
	@if [ $$? -eq 0 ]; then \
		echo "Starting Phase 3..."; \
		# Phase 3 commands here \
	else \
		echo "Validation failed - cannot proceed to Phase 3"; \
		exit 1; \
	fi
```

---

## Best Practices

1. **Always review the decision report** - Don't just rely on exit code
2. **Keep logs for audit trail** - Timestamped logs are valuable
3. **Check diversity visualizations** - Charts reveal patterns not obvious in metrics
4. **Use `--skip-revalidation` for iteration** - Speeds up development cycle
5. **Monitor correlation trends** - High correlation indicates strategy diversity issues

---

## Support

**Script Location**: `/mnt/c/Users/jnpi/Documents/finlab/scripts/run_full_validation_workflow.sh`
**Documentation**: See TASK_6.1_MASTER_WORKFLOW_COMPLETION_REPORT.md
**Help**: `./scripts/run_full_validation_workflow.sh --help`
