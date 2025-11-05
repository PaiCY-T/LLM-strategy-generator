# Task 6.2 Execution Guide

## Overview
This guide explains how to execute Task 6.2 system validation test for the docker-integration-test-framework specification.

## Purpose
Verify Requirement 7 success criteria through actual system execution:
1. Docker execution success rate >80%
2. Diversity-aware prompting activates ≥30% of eligible iterations
3. No regression in direct-execution mode
4. Config snapshots saved successfully

## Prerequisites

### 1. Environment Setup
```bash
# Required API key
export OPENROUTER_API_KEY="your-openrouter-api-key-here"

# Optional: Adjust resource limits
export DOCKER_MEMORY_LIMIT="2g"
export DOCKER_CPU_LIMIT="0.5"
export DOCKER_TIMEOUT="600"
```

### 2. Docker Environment
Ensure Docker is installed and running:
```bash
docker --version  # Should show Docker 20.10+
docker ps         # Should connect successfully
```

### 3. Configuration Verification
The system will use configuration from:
- `/mnt/c/Users/jnpi/documents/finlab/config/learning_system.yaml`

Key settings verified:
- `sandbox.enabled: true` (Docker sandbox mode)
- `llm.enabled: true` (LLM innovation)
- `llm.provider: openrouter`
- `llm.model: google/gemini-2.5-flash`

## Execution

### Quick Start
```bash
cd /mnt/c/Users/jnpi/documents/finlab
python run_task_6_2_validation.py
```

### Expected Runtime
- **Duration**: 1-2 hours
- **Iterations**: 30
- **Average per iteration**: 2-4 minutes (including LLM API calls and backtest)

### What Happens During Execution
1. **Initialization** (10-30 seconds)
   - Load configuration
   - Initialize autonomous loop
   - Set up monitoring and logging

2. **Iteration Loop** (30 iterations × 2-4 min each)
   - Generate strategy via LLM
   - Validate code (AST security checks)
   - Execute in Docker sandbox
   - Extract metrics
   - Record results

3. **Analysis** (5-10 seconds)
   - Calculate success rates
   - Analyze diversity activation
   - Check for errors
   - Generate report

## Monitoring Progress

### Console Output
Watch for these indicators:
```
🚀 Starting Task 6.2 Validation - 30 Iterations
====================================================================

Iteration 0/30
====================================================================
  ✅ Docker execution: SUCCESS
  🎯 Diversity-aware prompting: ACTIVATED

Iteration 1/30
====================================================================
  ✅ Docker execution: SUCCESS
```

### Interim Checks
During execution, you can check:
```bash
# Watch iteration history (in separate terminal)
tail -f task_6_2_validation_history.json

# Check Docker containers
docker ps -a | grep finlab-sandbox
```

## Output Files

### 1. Raw Metrics (JSON)
**File**: `task_6_2_validation_results.json`

Contains:
- Total iterations and success counts
- Docker execution statistics
- Diversity activation data
- Error counts
- Iteration-by-iteration breakdown

**Example**:
```json
{
  "total_iterations": 30,
  "docker_successes": 27,
  "docker_failures": 3,
  "success_rate": 90.0,
  "diversity_activations": 12,
  "diversity_rate": 40.0,
  "import_errors": 0,
  "config_snapshot_errors": 0
}
```

### 2. Validation Report (Markdown)
**File**: `TASK_6.2_VALIDATION_REPORT.md`

Contains:
- Executive summary (pass/fail)
- Metrics table with success criteria comparison
- Iteration-by-iteration breakdown
- Success criteria verification
- Recommendations

### 3. Iteration History (JSON)
**File**: `task_6_2_validation_history.json`

Contains complete history of all iterations for debugging.

## Success Criteria

### Criterion 1: Docker Success Rate >80%
- **Target**: >24 successful Docker executions out of 30
- **Measurement**: `docker_successes / docker_iterations > 0.80`
- **Pass condition**: ✅ if ≥24 successes

### Criterion 2: Diversity Activation ≥30%
- **Target**: Diversity-aware prompting activates in ≥30% of iterations
- **Measurement**: `diversity_activations / total_iterations >= 0.30`
- **Pass condition**: ✅ if ≥9 activations (or N/A if no failures)

### Criterion 3: Zero Import Errors
- **Target**: No import errors for ExperimentConfig module
- **Measurement**: `import_errors == 0`
- **Pass condition**: ✅ if count is 0

### Criterion 4: Zero Config Snapshot Errors
- **Target**: All config snapshots saved successfully
- **Measurement**: `config_snapshot_errors == 0`
- **Pass condition**: ✅ if count is 0

## Troubleshooting

### Issue 1: API Key Not Set
**Error**: "WARNING: OPENROUTER_API_KEY not set in environment"

**Solution**:
```bash
export OPENROUTER_API_KEY="your-key-here"
```

### Issue 2: Docker Not Available
**Error**: "Docker daemon not available"

**Solution**:
```bash
# Start Docker daemon
sudo systemctl start docker  # Linux
# or
open -a Docker  # macOS

# Verify
docker ps
```

### Issue 3: Import Errors
**Error**: "ModuleNotFoundError: No module named 'X'"

**Solution**:
```bash
# Ensure you're in project root
cd /mnt/c/Users/jnpi/documents/finlab

# Check Python path
python -c "import sys; print(sys.path)"

# Install missing dependencies
pip install -r requirements.txt
```

### Issue 4: High Failure Rate
**Symptom**: Docker success rate <80%

**Investigation**:
1. Check Docker logs:
   ```bash
   docker logs <container-id>
   ```

2. Review iteration history:
   ```bash
   cat task_6_2_validation_history.json | jq '.[-1]'
   ```

3. Check resource limits:
   ```bash
   docker stats
   ```

## Next Steps

### If All Criteria Pass ✅
1. Review `TASK_6.2_VALIDATION_REPORT.md`
2. Archive validation results
3. Mark Task 6.2 as complete in tasks.md: `[x]`
4. Proceed to Phase 7 (if applicable)

### If Criteria Fail ❌
1. Review failure details in report
2. Check iteration breakdown for patterns
3. Investigate root causes
4. Apply fixes
5. Re-run validation

## Additional Notes

### Performance Optimization
To speed up testing (at cost of coverage):
```python
# Edit run_task_6_2_validation.py
max_iterations = 10  # Instead of 30
```

Note: Reduced iterations may not provide statistical confidence for criteria.

### Cost Estimation
- **LLM API costs**: ~$0.01-0.05 per strategy
- **30 iterations**: ~$0.30-$1.50 total
- Provider: OpenRouter (google/gemini-2.5-flash)

### Background Context
This validation confirms fixes for:
- **Bug #1**: F-string formatting (diagnostic logging)
- **Bug #2**: LLM API 404 errors (config fix)
- **Bug #3**: ExperimentConfig import (module created)
- **Bug #4**: Exception state (last_result=False fix)

## Support

For issues or questions:
1. Check `TASK_6.2_VALIDATION_REPORT.md` for detailed analysis
2. Review `task_6_2_validation_results.json` for raw data
3. Examine `task_6_2_validation_history.json` for iteration details
4. Check Docker logs for container issues

---
*Guide for Task 6.2 - Docker Integration Test Framework*
*Generated: 2025-11-02*
