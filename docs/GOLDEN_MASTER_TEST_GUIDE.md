# Golden Master Test Guide

## Overview

Golden Master Testing (also known as Characterization Testing or Approval Testing) is a technique for verifying that code refactoring does not change system behavior. This guide explains how to use the Golden Master Test system in the FinLab autonomous learning pipeline.

**Purpose**: Ensure behavioral equivalence before and after refactoring - same inputs produce same outputs (within tolerance).

**Scope**: Tests the deterministic components of the autonomous learning loop:
- Data processing pipeline
- Backtesting calculations
- Iteration management
- Result metrics computation

**Non-deterministic components** (LLM output) are mocked to ensure reproducibility.

---

## What is a Golden Master Test?

A Golden Master Test captures the output of a system at a known-good state (the "golden master" or "baseline"), then compares future outputs against this baseline to detect unintended behavioral changes.

### Key Concepts

1. **Baseline**: A snapshot of system output from pre-refactor code (the "golden master")
2. **Comparison**: Running refactored code and comparing output to baseline
3. **Tolerance**: Acceptable differences due to floating-point precision
4. **Determinism**: Fixed inputs (seed, data, mocked randomness) ensure reproducibility

### When to Use Golden Master Tests

**Use Golden Master Tests when**:
- Refactoring infrastructure code (extracting classes, modularizing)
- Migrating to new architecture patterns
- Upgrading Python version or major dependencies
- Need to verify "behavioral equivalence" (not just unit test coverage)

**Do NOT use Golden Master Tests when**:
- Intentionally changing system behavior (feature development)
- Developing new features (no baseline exists)
- System has non-deterministic outputs that can't be mocked

---

## Test Structure

### Location
```
tests/learning/test_golden_master_deterministic.py
```

### Components

1. **Fixtures** (Test Infrastructure):
   - `fixed_dataset`: Deterministic market data (2020-2024)
   - `fixed_config`: Deterministic system configuration
   - `canned_strategy`: Pre-defined strategy code (not LLM-generated)
   - `mock_llm_client`: Mocked LLM that returns fixed strategies
   - `golden_master_baseline`: Baseline metrics from pre-refactor code

2. **Main Test** (`test_golden_master_deterministic_pipeline`):
   - Sets deterministic environment (seed=42)
   - Runs refactored learning pipeline
   - Compares output to golden master baseline
   - Validates key metrics within tolerance

3. **Structure Validation** (`test_golden_master_structure_validation`):
   - Validates baseline file has correct schema
   - Checks required fields exist
   - Verifies iteration outcomes structure

4. **Smoke Test** (`test_fixtures_are_available`):
   - Ensures all fixtures are correctly defined
   - Quick sanity check before running main test

---

## When to Run Golden Master Tests

### Mandatory Scenarios

1. **After Refactoring Infrastructure Code**
   - Extracting ConfigManager, LLMClient, IterationHistory (Week 1)
   - Modularizing autonomous_loop.py
   - Changing internal architecture

2. **After Upgrading Dependencies**
   - Python version upgrade (3.9 → 3.10)
   - pandas/numpy major version upgrade
   - finlab library update

3. **Before Merging Refactoring PRs**
   - CI/CD pipeline should run golden master tests
   - Ensure no behavioral regression

### Optional Scenarios

4. **When Suspicious of Behavioral Changes**
   - Backtest results look different
   - Metrics seem off
   - Debug unexpected system behavior

5. **Periodic Regression Testing**
   - Weekly CI runs (optional)
   - After large code merges

### Frequency Recommendations

| Scenario | Frequency | Required? |
|----------|-----------|-----------|
| Refactoring infrastructure | Every commit | Yes |
| Dependency upgrade | Every upgrade | Yes |
| Feature development | Never | No |
| Weekly CI | Once/week | Optional |
| Before release | Every release | Yes |

---

## Running the Tests

### Basic Usage

```bash
# Run all golden master tests
pytest tests/learning/test_golden_master_deterministic.py -v

# Run specific test
pytest tests/learning/test_golden_master_deterministic.py::test_golden_master_deterministic_pipeline -v

# Run with detailed output
pytest tests/learning/test_golden_master_deterministic.py -v -s
```

### Expected Output

**Current State** (with structural baseline):
```
test_golden_master_deterministic_pipeline SKIPPED  [33%]  ← Expected (baseline is structural)
test_golden_master_structure_validation   PASSED   [66%]  ← Success
test_fixtures_are_available              PASSED   [100%] ← Success

========================= 2 passed, 1 skipped =========================
```

**Future State** (with real baseline):
```
test_golden_master_deterministic_pipeline PASSED   [33%]  ← Success (all metrics match)
test_golden_master_structure_validation   PASSED   [66%]  ← Success
test_fixtures_are_available              PASSED   [100%] ← Success

========================= 3 passed in 45.2s =========================
```

### Interpreting Results

**All Passed**: Refactored code maintains behavioral equivalence - safe to merge!

**Main Test Skipped**: Baseline is structural placeholder - need to generate real baseline

**Main Test Failed**: Behavioral divergence detected - investigate before merging

---

## Baseline Management

### Current Baseline Status

The current baseline (`tests/fixtures/golden_master_baseline.json`) is a **structural placeholder**:
- Defines expected data schema
- Contains null/zero values
- Used for structure validation only
- Main test is skipped until real baseline is generated

### Generating Real Baseline

**When to Generate**:
- Before starting infrastructure refactoring
- From pre-refactor commit (known-good state)
- Only once per refactoring cycle

**How to Generate**:

```bash
# 1. Checkout pre-refactor commit (known-good state)
git checkout <pre-refactor-commit>

# 2. Run baseline generation script
python scripts/generate_golden_master.py \
  --iterations 5 \
  --seed 42 \
  --output tests/fixtures/golden_master_baseline.json

# 3. Verify baseline file
cat tests/fixtures/golden_master_baseline.json | jq '.'

# 4. Return to refactoring branch
git checkout feature/learning-system-enhancement

# 5. Commit baseline to version control
git add tests/fixtures/golden_master_baseline.json
git commit -m "Add golden master baseline for Week 1 refactoring validation"
```

**Important**: Generate baseline from **pre-refactor** code, not post-refactor code!

---

## Updating the Baseline

### When to Update

Update the baseline only when you have **intentional, verified behavioral changes**:

1. **Algorithm Optimization**
   - Example: Improved Sharpe ratio calculation
   - Verified: New algorithm is mathematically correct

2. **Strategy Generation Improvement**
   - Example: Better prompt engineering for LLM
   - Verified: New strategies perform better in backtesting

3. **Threshold Adjustment**
   - Example: Changed probation threshold from 0.10 to 0.15
   - Verified: New threshold matches business requirements

### How to Update

**Step 1: Verify Change is Correct**
```bash
# Review code changes
git diff

# Understand why output changed
# - Is this an intended improvement?
# - Is this a bug fix?
# - Do I have evidence the new behavior is correct?
```

**Step 2: Generate New Baseline**
```bash
# Run with updated code
python scripts/generate_golden_master.py \
  --iterations 5 \
  --seed 42 \
  --output tests/fixtures/golden_master_baseline.json
```

**Step 3: Validate New Baseline**
```bash
# Check format is correct
cat tests/fixtures/golden_master_baseline.json | jq '.'

# Verify metrics are reasonable
# - Sharpe ratio in [-2, 5] range
# - Max drawdown in [-1, 0] range
# - Total return in [-1, 10] range
```

**Step 4: Commit with Clear Message**
```bash
git add tests/fixtures/golden_master_baseline.json
git commit -m "Update golden master baseline: [REASON]

- Improved strategy generation prompt (Sharpe +0.15)
- Changed probation threshold: 0.10 → 0.15
- Updated baseline to reflect intended behavioral change
"
```

**Important Warnings**:
- Do NOT update baseline to make failing tests pass
- Do NOT update baseline without understanding why output changed
- Do NOT update baseline for bug fixes (output should match original behavior)

---

## Tolerance Configuration

### Why Tolerance is Needed

Due to floating-point arithmetic limitations, exact numeric equality is unreliable:
- Different platforms (x86 vs ARM) have slight calculation differences
- Different compiler optimizations affect rounding
- pandas/numpy version changes may reorder operations
- Random number generator implementations vary

### Current Tolerance Values

```python
TOLERANCE = 0.01  # 1% relative error

Metrics:
- Sharpe ratio:    ±0.01 (1% tolerance)
- Max drawdown:    ±0.01 (1% tolerance)
- Total return:    ±0.01 (1% tolerance)
- Annual return:   ±0.01 (1% tolerance)

Exact match (zero tolerance):
- Success count:     must match exactly
- Iteration sequence: must match exactly
- History entries:   must match exactly
```

### Adjusting Tolerance

**When to Adjust**:
- Platform-specific differences consistently exceed tolerance
- Dependency upgrade causes systematic small differences
- Statistical tests show differences are numerically insignificant

**How to Adjust**:

Edit `tests/learning/test_golden_master_deterministic.py`:
```python
# Line ~340
TOLERANCE = 0.01  # Change this value

# Example: Increase to 2% tolerance
TOLERANCE = 0.02
```

**Guidelines**:
- Keep tolerance as small as possible (tighter verification)
- Typical range: 0.005 - 0.05 (0.5% - 5%)
- If you need >5% tolerance, investigate why outputs differ so much

---

## Troubleshooting

### Problem 1: Test Fails - "Sharpe ratio mismatch"

**Symptom**:
```
AssertionError: Sharpe ratio mismatch:
  expected 1.2345, got 1.2500,
  diff 0.0155 exceeds tolerance 0.0100
```

**Possible Causes**:

1. **Refactoring introduced behavioral change (bug)**
   - Check recent commits: `git log --oneline -10`
   - Review diff: `git diff <pre-refactor-commit>`
   - Look for logic changes in backtest calculations

2. **Dependency upgrade changed calculations**
   - Check updated packages: `pip list --outdated`
   - Review pandas/numpy changelog
   - Consider increasing tolerance if difference is small and systematic

3. **Random seed not properly fixed**
   - Verify `np.random.seed(42)` is called
   - Check for uncontrolled randomness (datetime.now(), random.random())
   - Ensure mock_llm_client returns deterministic strategies

4. **Platform-specific floating-point differences**
   - Run on different OS (Windows vs Linux)
   - Check CPU architecture (x86 vs ARM)
   - Consider slightly increasing tolerance

**Diagnostic Steps**:

```bash
# 1. Check what changed recently
git log --oneline -10
git diff <last-passing-commit> -- src/backtest/

# 2. Verify dependencies match
pip freeze | grep -E "(pandas|numpy|finlab)"

# 3. Run test with debug output
pytest tests/learning/test_golden_master_deterministic.py -v -s

# 4. Compare actual vs expected metrics
cat tests/fixtures/golden_master_baseline.json | jq '.final_champion'
```

**Resolution**:

- **Small difference (<0.02)**: Likely numerical precision - increase tolerance
- **Medium difference (0.02-0.10)**: Investigate code changes
- **Large difference (>0.10)**: Real bug - do NOT merge until fixed

---

### Problem 2: Main Test is Skipped

**Symptom**:
```
test_golden_master_deterministic_pipeline SKIPPED
Reason: Golden master baseline is structural only - no actual data
```

**Cause**:
Baseline file exists but contains structural placeholder (null values) instead of real metrics.

**Check Baseline Status**:
```bash
# View baseline file
cat tests/fixtures/golden_master_baseline.json | jq '.final_champion'

# Structural placeholder looks like:
{
  "sharpe_ratio": 0.0,
  "max_drawdown": 0.0,
  "total_return": 0.0,
  "note": "Structural placeholder - refactored code should populate these fields"
}

# Real baseline looks like:
{
  "sharpe_ratio": 1.2345,
  "max_drawdown": -0.1523,
  "total_return": 0.4567
}
```

**Resolution**:

Generate real baseline from pre-refactor code:
```bash
# 1. Checkout known-good pre-refactor commit
git checkout <pre-refactor-commit>

# 2. Generate baseline
python scripts/generate_golden_master.py \
  --iterations 5 \
  --seed 42 \
  --output tests/fixtures/golden_master_baseline.json

# 3. Return to current branch
git checkout feature/learning-system-enhancement

# 4. Verify baseline has real data
cat tests/fixtures/golden_master_baseline.json | jq '.final_champion.sharpe_ratio'
# Should output a non-zero number like 1.2345

# 5. Run test again
pytest tests/learning/test_golden_master_deterministic.py -v
```

---

### Problem 3: "Fixture 'mock_llm_client' not found"

**Symptom**:
```
fixture 'mock_llm_client' not found
```

**Possible Causes**:

1. **pytest version too old**
   - Requires pytest >= 6.0 for fixture resolution

2. **pytest cache corrupted**
   - Old cache may contain stale fixture definitions

3. **Test file not in correct location**
   - Must be in `tests/learning/` directory

**Resolution**:

```bash
# 1. Check pytest version
pytest --version
# Require: pytest 6.0 or higher

# 2. Upgrade pytest if needed
pip install --upgrade pytest

# 3. Clear pytest cache
pytest --cache-clear

# 4. Verify test file location
ls -l tests/learning/test_golden_master_deterministic.py

# 5. Run test again
pytest tests/learning/test_golden_master_deterministic.py -v
```

---

### Problem 4: "AutonomousLoop not available - Week 1 refactoring incomplete"

**Symptom**:
```
test_golden_master_deterministic_pipeline SKIPPED
Reason: AutonomousLoop not available - Week 1 refactoring incomplete
```

**Cause**:
The test tries to import `AutonomousLoop` from refactored location but it doesn't exist yet.

**Expected Behavior**:
This is **normal during Week 1 development**. The test is designed to gracefully skip if refactoring is incomplete.

**Resolution**:

This is not an error - continue Week 1 refactoring:
1. Complete ConfigManager extraction
2. Complete LLMClient extraction
3. Complete IterationHistory extraction
4. Once all components are ready, AutonomousLoop can be assembled

**Note**: The test validates **individual components** (ConfigManager, LLMClient, IterationHistory) even if full AutonomousLoop integration is not ready yet.

---

### Problem 5: Test Runs Forever (Timeout)

**Symptom**:
Test runs for >5 minutes without completing.

**Possible Causes**:

1. **Mock LLM not working - making real API calls**
2. **Infinite loop in refactored code**
3. **Sandbox execution stuck**

**Diagnosis**:

```bash
# 1. Run with timeout
pytest tests/learning/test_golden_master_deterministic.py -v --timeout=120

# 2. Check for real LLM API calls (should be mocked)
# Look for network activity during test

# 3. Run with debug output
pytest tests/learning/test_golden_master_deterministic.py -v -s
```

**Resolution**:

- Ensure `mock_llm_client` fixture is properly injected
- Verify `llm.enabled = False` in `fixed_config`
- Add explicit timeouts to test functions

---

## Implementation Notes

### Current Implementation Status

**Task H1.1.1** (Complete): Test Infrastructure
- All fixtures implemented
- Smoke test validates fixtures work
- Ready for H1.1.3 (main test implementation)

**Task H1.1.2** (Complete): Baseline Generation
- Structural baseline created
- Schema validated
- Placeholder for real baseline values

**Task H1.1.3** (Complete): Main Test Implementation
- Golden master test implemented
- Component validation logic working
- Gracefully handles incomplete refactoring

**Task H1.1.4** (Current): Validation & Documentation
- This guide documents usage
- Test validation complete (2 passed, 1 skipped as expected)

### What's Tested (Current)

The test validates **refactored components individually**:
- ConfigManager singleton behavior
- ConfigManager get_config() method
- IterationHistory JSONL persistence
- LLMClient mock integration
- Deterministic mock behavior

### What's NOT Tested Yet

Full end-to-end integration requires:
- Real finlab.data mocking (not just fixture)
- Sandbox execution mocking
- Complete AutonomousLoop assembly
- Multi-iteration pipeline execution

**Future Enhancement** (Phase 2):
Once Week 1 refactoring is complete, extend test to validate full pipeline integration.

---

## Best Practices

### DO

1. **Generate baseline from known-good state**
   - Pre-refactor commit
   - Verified correct behavior
   - Committed to version control

2. **Keep tolerance tight**
   - Start with 0.01 (1%)
   - Only increase if platform differences require it
   - Document why you increased tolerance

3. **Run tests frequently during refactoring**
   - After every significant change
   - Before committing
   - In CI/CD pipeline

4. **Document baseline updates**
   - Clear commit message
   - Explain why behavior changed
   - Link to issue/PR with rationale

5. **Use golden master tests for refactoring only**
   - Not for feature development
   - Not for bug fixes (unless fixing behavior drift)

### DON'T

1. **Don't update baseline to make tests pass**
   - Understand why test failed first
   - Fix the bug, don't hide it

2. **Don't use for non-deterministic code**
   - LLM outputs must be mocked
   - Random data must be seeded
   - Time-dependent code must be controlled

3. **Don't set tolerance too high**
   - >5% tolerance defeats the purpose
   - If you need high tolerance, investigate why

4. **Don't skip failing tests**
   - Skipped test = unverified refactoring
   - Fix the issue or revert changes

5. **Don't generate baseline from refactored code**
   - Baseline must be from **pre-refactor** state
   - Otherwise you're testing nothing

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Golden Master Tests

on:
  pull_request:
    branches: [main]
  push:
    branches: [feature/learning-system-enhancement]

jobs:
  golden-master-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-timeout

      - name: Run Golden Master Tests
        run: |
          pytest tests/learning/test_golden_master_deterministic.py -v --timeout=120

      - name: Upload test results
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: pytest-results.xml
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run golden master tests before committing refactoring changes
if git diff --cached --name-only | grep -q 'src/learning/'; then
    echo "Running golden master tests..."
    pytest tests/learning/test_golden_master_deterministic.py -v

    if [ $? -ne 0 ]; then
        echo "Golden master tests failed - commit rejected"
        exit 1
    fi
fi
```

---

## FAQ

### Q1: How long should the test take?

**A**: With mock LLM and 5 iterations:
- Current (component validation): ~3 seconds
- Future (full pipeline): ~30-60 seconds

If test takes >2 minutes, something is wrong (timeout, real API calls).

### Q2: Can I use golden master tests for new features?

**A**: No. Golden master tests are for **refactoring only** (behavior preservation). For new features, write normal unit/integration tests.

### Q3: What if baseline is too old?

**A**: Baseline should be generated right before refactoring starts. If weeks old, regenerate from pre-refactor commit.

### Q4: How do I debug why metrics don't match?

**A**:
```python
# Add debug output to test
print(f"Expected: {expected_sharpe:.6f}")
print(f"Actual: {actual_sharpe:.6f}")
print(f"Diff: {abs(expected_sharpe - actual_sharpe):.6f}")

# Run with -s flag
pytest tests/learning/test_golden_master_deterministic.py::test_golden_master_deterministic_pipeline -v -s
```

### Q5: Can I have multiple baselines?

**A**: Yes, for different scenarios:
- `golden_master_baseline_5iter.json` (5 iterations)
- `golden_master_baseline_20iter.json` (20 iterations)
- `golden_master_baseline_python39.json` (Python 3.9)

Just update test to load appropriate baseline.

### Q6: What about backward compatibility?

**A**: Golden master tests verify **behavioral equivalence**, not API compatibility. Use separate API compatibility tests for public interfaces.

---

## References

### Related Documentation

- **Week 1 Hardening Plan**: `.spec-workflow/specs/phase3-learning-iteration/WEEK1_HARDENING_PLAN.md`
- **Test Implementation**: `tests/learning/test_golden_master_deterministic.py`
- **Baseline Schema**: `tests/fixtures/golden_master_baseline.json`

### External Resources

- [Golden Master Testing (Wikipedia)](https://en.wikipedia.org/wiki/Characterization_test)
- [Working Effectively with Legacy Code (Michael Feathers)](https://www.goodreads.com/book/show/44919.Working_Effectively_with_Legacy_Code)
- [Approval Testing](https://approvaltests.com/)

### Related Tests

- `tests/learning/test_config_manager.py` - ConfigManager unit tests
- `tests/learning/test_llm_client.py` - LLMClient unit tests
- `tests/learning/test_iteration_history.py` - IterationHistory unit tests

---

## Changelog

### 2025-11-04 - Task H1.1.4 Complete
- Created comprehensive Golden Master Test Guide
- Validated test suite (2 passed, 1 skipped as expected)
- Documented usage, troubleshooting, and best practices
- Baseline structure validated, ready for real baseline generation

---

## Contact & Support

For questions or issues:
1. Check this guide first (especially Troubleshooting section)
2. Review test implementation comments
3. Check Week 1 Hardening Plan for context
4. Consult with team lead if behavioral divergence is unclear

**Remember**: Golden master tests are a safety net for refactoring. If tests fail, investigate before updating baseline!
