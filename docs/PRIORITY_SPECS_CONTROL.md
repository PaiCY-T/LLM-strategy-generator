# Priority Specs Control System

## Overview

The Priority Specs Control System orchestrates parallel execution of **4 priority specs** with **28 remaining tasks** across **4 independent tracks**. This control spec provides automation scripts to:

- **Track Progress**: Aggregate completion status across all specs
- **Validate Dependencies**: Ensure tasks are executed in correct order
- **Calculate Timeline**: Predict completion dates and identify bottlenecks
- **Sync Status**: Keep control spec synchronized with actual progress

**Managed Specs**:
1. **Exit Mutation Redesign** - `.spec-workflow/specs/exit-mutation-redesign/tasks.md`
2. **LLM Integration Activation** - `.spec-workflow/specs/llm-integration-activation/tasks.md`
3. **Structured Innovation MVP** - `.spec-workflow/specs/structured-innovation-mvp/tasks.md`
4. **YAML Normalizer Phase2** - `.spec-workflow/specs/yaml-normalizer-phase2-complete-normalization/tasks.md`

**Total Effort**: 71.5h across 28 tasks
**Timeline**: 5 days via parallelization (2.04x parallelism factor)
**Tracks**: 4 independent tracks (no cross-track dependencies)

---

## Quick Start

### 1. Check Overall Status

View aggregated progress across all 4 specs:

```bash
python scripts/check_priority_specs_status.py
```

**Expected Output**:
```
================================================================================
Priority Specs - Parallel Execution Status
================================================================================

Spec Name                       | Done | In Progress | Pending | Total |      %
--------------------------------------------------------------------------------
Exit Mutation Redesign          |    5 |           0 |       3 |     8 |  62.5% →
LLM Integration Activation      |    5 |           1 |       8 |    14 |  35.7% →
Structured Innovation MVP       |    3 |           0 |      10 |    13 |  23.0%
YAML Normalizer Phase2          |    0 |           0 |       6 |     6 |   0.0%
--------------------------------------------------------------------------------
TOTAL                           |   13 |           1 |      27 |    41 |  31.7%
================================================================================

⚡ 1 task(s) currently in progress
🚀 Good progress - keep going!
```

**JSON Output** (for CI/CD integration):
```bash
python scripts/check_priority_specs_status.py --json
```

**Expected Output**:
```json
{
  "specs": [
    {
      "name": "Exit Mutation Redesign",
      "short": "exit-mutation",
      "completed": 5,
      "in_progress": 0,
      "pending": 3,
      "total": 8,
      "percentage": 62.5
    },
    ...
  ],
  "summary": {
    "completed": 13,
    "in_progress": 1,
    "pending": 27,
    "total": 41,
    "percentage": 31.7
  }
}
```

### 2. Validate Dependencies

Ensure no circular dependencies and validate prerequisite completion:

```bash
python scripts/validate_spec_dependencies.py
```

**Expected Output** (no errors):
```
Parsing dependency matrix from control spec...
Found 41 tasks with dependencies

Checking for circular dependencies...
✓ No circular dependencies found

✅ Dependency validation PASSED
```

**With Prerequisite Checking**:
```bash
python scripts/validate_spec_dependencies.py --check-prerequisites
```

**Expected Output**:
```
Parsing dependency matrix from control spec...
Found 41 tasks with dependencies

Checking for circular dependencies...
✓ No circular dependencies found

Validating task prerequisites...
✓ All in-progress tasks have prerequisites completed

✅ Dependency validation PASSED
```

### 3. Calculate Timeline

**Note**: This script is being implemented in parallel (Task 3). Once available:

```bash
python scripts/calculate_parallel_timeline.py
```

**Expected Output**:
```
Critical Path Analysis
======================
Critical Path: Track 3 (Structured Innovation MVP)
Duration: 2 days (33h effort)

Day-by-Day Schedule
===================
Day 1:
  - Track 1: Tasks 7, 8 (4h) → 100% COMPLETE
  - Track 2A: Tasks 6, 7 (5h)
  - Track 4: Tasks 1-4 (3.75h)

Day 2:
  - Track 2A: Tasks 8, 9 (5h) → 100% COMPLETE
  - Track 3A: Tasks 4, 5, 6 (10h) → 100% COMPLETE
  - Track 4: Tasks 5, 6 (1.75h) → 100% COMPLETE

...

Estimated Completion: 2025-11-01 (5 days from start)
```

### 4. Sync Control Spec Status

**Note**: This script is being implemented in parallel (Task 4). Once available:

```bash
python scripts/sync_control_spec_status.py
```

**Expected Output**:
```
Reading individual spec statuses...
  - Exit Mutation Redesign: 5/8 (62.5%)
  - LLM Integration Activation: 5/14 (35.7%)
  - Structured Innovation MVP: 3/13 (23%)
  - YAML Normalizer Phase2: 0/6 (0%)

Comparing with control spec timeline...
✓ No drift detected (all tasks on schedule)

Creating backup: .spec-workflow/specs/priority-specs-parallel-execution/tasks.md.bak
Updating control spec "Current Status" section...
✓ Control spec synchronized

✅ Sync complete
```

---

## Usage Examples

### Example 1: Daily Progress Check

Monitor daily progress across all specs:

```bash
#!/bin/bash
# daily_check.sh - Run this each morning

echo "=== Priority Specs Daily Status ==="
python scripts/check_priority_specs_status.py

echo ""
echo "=== Dependency Validation ==="
python scripts/validate_spec_dependencies.py --check-prerequisites

echo ""
echo "=== Timeline Update ==="
python scripts/calculate_parallel_timeline.py
```

### Example 2: CI/CD Integration

Use JSON output for automated checks:

```bash
#!/bin/bash
# ci_check.sh - Run in CI/CD pipeline

# Get status in JSON format
STATUS=$(python scripts/check_priority_specs_status.py --json)

# Extract overall percentage
PERCENTAGE=$(echo "$STATUS" | jq '.summary.percentage')

# Check if completion is above threshold
if (( $(echo "$PERCENTAGE < 30" | bc -l) )); then
    echo "WARNING: Progress below 30% ($PERCENTAGE%)"
    exit 1
fi

# Validate dependencies
python scripts/validate_spec_dependencies.py --check-prerequisites || {
    echo "ERROR: Dependency validation failed"
    exit 1
}

echo "✅ All checks passed ($PERCENTAGE% complete)"
```

### Example 3: Pre-Commit Hook

Validate dependencies before starting work on a task:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check if any spec tasks.md files were modified
SPEC_FILES=$(git diff --cached --name-only | grep "spec-workflow/specs/.*/tasks.md")

if [ -n "$SPEC_FILES" ]; then
    echo "Validating spec dependencies..."
    python scripts/validate_spec_dependencies.py --check-prerequisites || {
        echo "ERROR: Dependency validation failed"
        echo "Please ensure prerequisites are completed before marking task as in-progress"
        exit 1
    }
fi
```

---

## Troubleshooting

### Error: "Circular dependency detected"

**Symptom**:
```
❌ CIRCULAR DEPENDENCY DETECTED!
Cycle: track-2a-task-7 → track-2a-task-8 → track-2a-task-7
```

**Cause**: Task A depends on Task B, which depends on Task A (or a longer cycle).

**Solution**:
1. Review the dependency matrix in `.spec-workflow/specs/priority-specs-parallel-execution/tasks.md`
2. Identify which dependency is incorrect
3. Update the dependency matrix to break the cycle
4. Re-run validation: `python scripts/validate_spec_dependencies.py`

**Example Fix**:
```markdown
# BEFORE (circular)
Task 7 → Depends: Task 8
Task 8 → Depends: Task 7

# AFTER (fixed)
Task 7 → No dependencies
Task 8 → Depends: Task 7
```

### Error: "Prerequisite not completed"

**Symptom**:
```
❌ PREREQUISITE VALIDATION FAILED!
  ERROR: track-2a-task-8 is in-progress but prerequisite track-2a-task-7
  is pending (must be completed)
```

**Cause**: A task is marked as in-progress `[-]` but its prerequisite is not completed `[x]`.

**Solution**:
1. Complete the prerequisite task first (mark as `[x]`)
2. OR change the in-progress task back to pending `[ ]`
3. Re-run validation: `python scripts/validate_spec_dependencies.py --check-prerequisites`

**Recommended Workflow**:
```bash
# Step 1: Check prerequisites before starting task
python scripts/validate_spec_dependencies.py --check-prerequisites

# Step 2: Mark prerequisite as complete in its spec's tasks.md
# Example: .spec-workflow/specs/llm-integration-activation/tasks.md
# Change: - [ ] 7. Dynamic prompt selection
# To:     - [x] 7. Dynamic prompt selection

# Step 3: Mark current task as in-progress
# Change: - [ ] 8. Modification prompts
# To:     - [-] 8. Modification prompts

# Step 4: Validate again
python scripts/validate_spec_dependencies.py --check-prerequisites
```

### Error: "Status out of sync"

**Symptom**:
```
WARNING: Drift detected
  - Track 2A Task 9 completed before Task 8
  - Expected order: Task 8 → Task 9
```

**Cause**: Tasks completed out of expected dependency order.

**Solution**:
1. Verify the actual task completion is correct
2. If order is intentional (e.g., tasks could overlap), update dependency matrix
3. Run sync script to update control spec: `python scripts/sync_control_spec_status.py`
4. Review changes in backup file before accepting

**When to Accept Drift**:
- Tasks marked "Can overlap" in dependency matrix
- Prerequisites were actually satisfied at runtime
- Dependency matrix was overly conservative

**When to Reject Drift**:
- Actual code dependency was violated
- Task B genuinely required Task A output
- Could cause bugs or integration issues

### Error: "Missing spec file"

**Symptom**:
```
ERROR: Exit Mutation Redesign: [Errno 2] No such file or directory:
  '.spec-workflow/specs/exit-mutation-redesign/tasks.md'
```

**Cause**: Expected spec tasks.md file doesn't exist at configured path.

**Solution**:
1. Verify the file path in script configuration
2. Check if spec was renamed or moved
3. Update `SPECS` list in `scripts/check_priority_specs_status.py`:

```python
SPECS = [
    {
        "name": "Exit Mutation Redesign",
        "short": "exit-mutation",
        "path": ".spec-workflow/specs/exit-mutation-redesign/tasks.md"  # Update this
    },
    ...
]
```

4. For dependency validation, update `SPEC_PATHS` in `scripts/validate_spec_dependencies.py`

### Error: "Could not find project root"

**Symptom**:
```
ERROR: Could not find project root.
Please run from project directory containing .spec-workflow/
```

**Cause**: Scripts cannot locate the `.spec-workflow` directory.

**Solution**:
1. Ensure you're running from the project root directory
2. OR run from any subdirectory (scripts search upward)
3. Verify `.spec-workflow/` directory exists:

```bash
ls -la .spec-workflow/
```

4. If directory is missing, you may be in the wrong repository

### Error: "Could not find 'Dependency Matrix' section"

**Symptom**:
```
ERROR: Could not find '## Dependency Matrix' section in tasks.md
```

**Cause**: Control spec's tasks.md is missing the required dependency matrix section.

**Solution**:
1. Open `.spec-workflow/specs/priority-specs-parallel-execution/tasks.md`
2. Ensure it contains a section starting with `## Dependency Matrix`
3. Verify format matches expected structure:

```markdown
## Dependency Matrix

### Track 1: Exit Mutation Redesign
```
Task 7 (Exit Docs) → No dependencies
Task 8 (Prometheus Metrics) → No dependencies
```
```

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Control Spec System                       │
└─────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌─────────────────┐   ┌──────────────┐
│ Status Script │   │ Validation      │   │ Timeline     │
│ (Task 1)      │   │ Script (Task 2) │   │ Script       │
│               │   │                 │   │ (Task 3)     │
│ - Parse tasks │   │ - Parse deps    │   │              │
│ - Aggregate   │   │ - Detect cycles │   │ - Critical   │
│ - Format      │   │ - Validate      │   │   path       │
└───────────────┘   └─────────────────┘   │ - Schedule   │
                                           └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Sync Script     │
                    │ (Task 4)        │
                    │                 │
                    │ - Read status   │
                    │ - Detect drift  │
                    │ - Update control│
                    └─────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Control Spec    │
                    │ tasks.md        │
                    │                 │
                    │ - Timeline      │
                    │ - Dependencies  │
                    │ - Current Status│
                    └─────────────────┘
```

### Data Flow

1. **Status Aggregation** (check_priority_specs_status.py):
   - Reads all 4 specs' tasks.md files
   - Parses task markers: `[ ]` (pending), `[-]` (in-progress), `[x]` (completed)
   - Aggregates counts and percentages
   - Outputs formatted table or JSON

2. **Dependency Validation** (validate_spec_dependencies.py):
   - Parses dependency matrix from control spec
   - Builds dependency graph (task → prerequisites)
   - Uses `graphlib.TopologicalSorter` to detect cycles
   - Validates in-progress tasks have completed prerequisites

3. **Timeline Calculation** (calculate_parallel_timeline.py):
   - Reads dependency matrix and task estimates
   - Calculates critical path (longest dependency chain)
   - Generates day-by-day schedule accounting for parallelism
   - Identifies resource conflicts

4. **Status Synchronization** (sync_control_spec_status.py):
   - Reads actual completion from all specs
   - Compares with expected timeline
   - Detects anomalies (out-of-order completion)
   - Updates control spec's "Current Status" section

### File Structure

```
finlab/
├── .spec-workflow/
│   └── specs/
│       ├── priority-specs-parallel-execution/
│       │   └── tasks.md                    # Control spec
│       ├── exit-mutation-redesign/
│       │   └── tasks.md                    # Individual spec
│       ├── llm-integration-activation/
│       │   └── tasks.md                    # Individual spec
│       ├── structured-innovation-mvp/
│       │   └── tasks.md                    # Individual spec
│       └── yaml-normalizer-phase2-complete-normalization/
│           └── tasks.md                    # Individual spec
├── scripts/
│   ├── check_priority_specs_status.py      # Status aggregation
│   ├── validate_spec_dependencies.py       # Dependency validation
│   ├── calculate_parallel_timeline.py      # Timeline calculator
│   └── sync_control_spec_status.py         # Sync script
├── tests/
│   └── control_spec/
│       ├── test_priority_specs_orchestration.py  # Integration tests
│       └── fixtures/                       # Test fixtures
└── docs/
    └── PRIORITY_SPECS_CONTROL.md           # This document
```

### Task Status Format

Tasks use standard markdown checkbox format:

```markdown
- [ ] 1. Task name (pending)
- [-] 2. Task name (in-progress)
- [x] 3. Task name (completed)
```

Both numbered and unnumbered formats are supported:

```markdown
# Numbered (preferred for control specs)
- [x] 1. Create status script

# Unnumbered (acceptable for simple specs)
- [x] Setup environment
```

### Dependency Matrix Format

Dependencies are declared in code blocks within the Dependency Matrix section:

```markdown
## Dependency Matrix

### Track 1: Exit Mutation Redesign
```
Task 7 (Exit Docs) → No dependencies
Task 8 (Prometheus Metrics) → No dependencies
```

### Track 2: LLM Integration Activation
```
Sub-track 2A (Core):
  Task 6 (LLMConfig) → No dependencies
  Task 7 (Dynamic prompt) → Depends: Task 6
  Task 8 (Modification prompts) → Depends: Task 7
```
```

**Supported Patterns**:
- `Task X (...) → No dependencies` - No prerequisites
- `Task X (...) → Depends: Task Y` - Single prerequisite
- `Task X (...) → Depends: Task Y, Task Z` - Multiple prerequisites (NOTE: Current implementation supports single "Task X" reference in depends clause)
- `Task X (...) → Can overlap with Task Y` - Independent, can run in parallel

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Priority Specs Status Check

on:
  push:
    paths:
      - '.spec-workflow/specs/*/tasks.md'
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM

jobs:
  check-status:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Check Overall Status
        run: |
          python scripts/check_priority_specs_status.py

      - name: Validate Dependencies
        run: |
          python scripts/validate_spec_dependencies.py --check-prerequisites

      - name: Post Status to PR
        if: github.event_name == 'pull_request'
        run: |
          STATUS=$(python scripts/check_priority_specs_status.py --json)
          PERCENTAGE=$(echo "$STATUS" | jq '.summary.percentage')
          echo "## Priority Specs Status: ${PERCENTAGE}%" >> $GITHUB_STEP_SUMMARY
          echo "\`\`\`json" >> $GITHUB_STEP_SUMMARY
          echo "$STATUS" >> $GITHUB_STEP_SUMMARY
          echo "\`\`\`" >> $GITHUB_STEP_SUMMARY
```

### Cron Job for Daily Sync

```bash
#!/bin/bash
# /etc/cron.daily/sync-priority-specs

cd /path/to/finlab
python scripts/sync_control_spec_status.py

# Commit if changes
if ! git diff --quiet .spec-workflow/specs/priority-specs-parallel-execution/tasks.md; then
    git add .spec-workflow/specs/priority-specs-parallel-execution/tasks.md
    git commit -m "chore: sync control spec status (automated)"
    git push
fi
```

### Pre-Commit Hook

Install as `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Validate dependencies before committing spec changes

SPEC_FILES=$(git diff --cached --name-only | grep "spec-workflow/specs/.*/tasks.md")

if [ -n "$SPEC_FILES" ]; then
    echo "Validating spec dependencies..."
    python scripts/validate_spec_dependencies.py --check-prerequisites || exit 1
fi
```

---

## Best Practices

### 1. Daily Status Check

Run status check every morning to track progress:

```bash
python scripts/check_priority_specs_status.py
```

### 2. Validate Before Starting Tasks

Before marking a task as in-progress, verify prerequisites:

```bash
python scripts/validate_spec_dependencies.py --check-prerequisites
```

### 3. Update Control Spec Weekly

Sync control spec with actual progress weekly:

```bash
python scripts/sync_control_spec_status.py
```

### 4. Review Timeline on Blockers

When blocked, recalculate timeline to assess impact:

```bash
python scripts/calculate_parallel_timeline.py
```

### 5. Use JSON Output in Automation

For CI/CD, dashboards, or monitoring, use JSON format:

```bash
python scripts/check_priority_specs_status.py --json | jq '.summary.percentage'
```

---

## Exit Codes

All scripts use consistent exit codes for automation:

| Exit Code | Meaning | Scripts |
|-----------|---------|---------|
| 0 | Success / All complete | All scripts |
| 1 | Error / Validation failed | All scripts |
| 2 | In progress (not an error) | check_priority_specs_status.py |

**Example Usage**:

```bash
#!/bin/bash

python scripts/validate_spec_dependencies.py
EXIT_CODE=$?

case $EXIT_CODE in
    0) echo "✅ Validation passed" ;;
    1) echo "❌ Validation failed"; exit 1 ;;
    *) echo "⚠️  Unexpected exit code: $EXIT_CODE"; exit 1 ;;
esac
```

---

## Testing

Integration tests are located in `tests/control_spec/test_priority_specs_orchestration.py`.

**Run all tests**:
```bash
python3 -m pytest tests/control_spec/ -v
```

**Run with coverage**:
```bash
python3 -m pytest tests/control_spec/ --cov=scripts --cov-report=term-missing
```

**Test coverage**: >80% for all scripts (35 tests, 9 skipped placeholders)

---

## FAQ

### Q: What if I need to add a new spec to the control system?

**A**: Update the configuration in both status and validation scripts:

1. Add to `SPECS` list in `scripts/check_priority_specs_status.py`
2. Add to `SPEC_PATHS` dict in `scripts/validate_spec_dependencies.py`
3. Add dependency matrix section in control spec's tasks.md
4. Update documentation

### Q: Can I run these scripts from any directory?

**A**: Yes, all scripts automatically search for the project root by looking for `.spec-workflow/` directory upward from the current working directory.

### Q: How do I handle tasks that can run in parallel?

**A**: Use the "Can overlap" notation in the dependency matrix:

```markdown
Task 8 (Modification prompts) → Depends: Task 7
Task 9 (Creation prompts) → Can overlap with Task 8
```

### Q: What's the difference between "in-progress" and "pending"?

**A**:
- **Pending** `[ ]`: Task not started, may have unmet prerequisites
- **In-progress** `[-]`: Task actively being worked on, prerequisites must be complete
- **Completed** `[x]`: Task finished and validated

### Q: How often should I sync the control spec?

**A**:
- **Daily**: If working actively on multiple tracks
- **Weekly**: For slower-paced projects
- **On milestone**: When completing major tasks or sub-tracks
- **Before standup**: To have accurate status for team updates

---

## Related Documentation

- [Spec Workflow Guide](/.spec-workflow/README.md) - Overview of spec-based development
- [Exit Mutation Redesign Spec](/.spec-workflow/specs/exit-mutation-redesign/) - Individual spec example
- [Control Spec Tasks](/.spec-workflow/specs/priority-specs-parallel-execution/tasks.md) - Current control spec

---

**Document Version**: 1.0
**Created**: 2025-10-27
**Last Updated**: 2025-10-27
**Maintainer**: QA Engineering Team
