# Task 6.2 - Quick Reference Card

## One-Line Summary
Execute 30-iteration system validation to verify Docker execution (>80% success), diversity prompting (≥30% activation), and bug fixes.

## Quick Start

### 1. Setup (1 minute)
```bash
export OPENROUTER_API_KEY="your-key-here"
cd /mnt/c/Users/jnpi/documents/finlab
```

### 2. Quick Test (5-10 minutes)
```bash
python3 test_task_6_2_quick.py
```

### 3. Full Validation (1-2 hours)
```bash
python3 run_task_6_2_validation.py
```

### 4. Check Results
```bash
cat TASK_6.2_VALIDATION_REPORT.md
```

## Success Criteria
| Criterion | Target | Pass Threshold |
|-----------|--------|----------------|
| Docker Success Rate | >80% | ≥24/30 successes |
| Diversity Activation | ≥30% | ≥9/30 activations |
| Import Errors | 0 | No ExperimentConfig errors |
| Config Errors | 0 | No snapshot errors |

## Output Files
- `task_6_2_validation_results.json` - Raw metrics
- `TASK_6.2_VALIDATION_REPORT.md` - Analysis report
- `task_6_2_validation_history.json` - Iteration history

## Common Issues

### API Key Missing
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

### Docker Not Running
```bash
docker ps  # Verify Docker is running
# System will fall back to direct execution if Docker unavailable
```

### Import Errors
```bash
cd /mnt/c/Users/jnpi/documents/finlab  # Ensure in project root
pip install -r requirements.txt         # Install dependencies
```

## Documentation
- **Full Guide**: `TASK_6.2_EXECUTION_GUIDE.md`
- **Technical Details**: `TASK_6.2_IMPLEMENTATION_SUMMARY.md`
- **Completion Report**: `TASK_6.2_COMPLETION_REPORT.md`

## What This Validates
- ✅ Bug #1: F-string formatting fix
- ✅ Bug #2: LLM API routing (openrouter/gemini-2.5-flash)
- ✅ Bug #3: ExperimentConfig import
- ✅ Bug #4: Exception state (last_result=False)

## Timeline
- Quick Test: ~10 minutes (2 iterations)
- Full Validation: ~90 minutes (30 iterations)
- Report Review: ~5 minutes

## Next Steps After Validation
- ✅ All criteria pass → Mark Task 6.2 complete in tasks.md
- ❌ Any criteria fail → Review report, fix issues, re-run

---
*Quick Reference for Task 6.2*
