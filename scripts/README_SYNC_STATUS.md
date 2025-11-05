# Control Spec Status Synchronization

## Overview

`sync_control_spec_status.py` automatically synchronizes the completion status from all 4 individual priority specs into the control spec's "Current Status" section.

**Part of**: Control Spec Task 4 (priority-specs-parallel-execution)

## Features

1. **Automatic Status Aggregation**: Reads task completion from all 4 specs
2. **Anomaly Detection**: Identifies tasks completed out of expected order (dependency violations)
3. **Safe Updates**: Creates backup before editing, uses atomic writes
4. **Drift Detection**: Compares actual progress with expected timeline
5. **Dry-Run Mode**: Preview changes without modifying files

## Usage

### Basic Sync (Update Control Spec)

```bash
python scripts/sync_control_spec_status.py
```

**Output**:
```
Syncing control spec status...
  Reading 4 individual specs...

  Exit Mutation Redesign: 5/8 (62.5%)
  LLM Integration Activation: 5/14 (35.7%)
  Structured Innovation MVP: 3/13 (23.1%)
  YAML Normalizer Phase2: 0/34 (0.0%)

  Overall: 13/69 (18.8%)

  Creating backup: tasks.md.backup.20251027_125740
  ✓ Control spec synchronized

✓ Synchronization complete
```

### Preview Changes (Dry Run)

```bash
python scripts/sync_control_spec_status.py --dry-run
```

Shows the updated status table without modifying files.

### Run as Cron Job

```bash
# Daily at 9 AM
0 9 * * * cd /path/to/finlab && python3 scripts/sync_control_spec_status.py
```

## Architecture

### Status Parsing

Reuses logic from `check_priority_specs_status.py`:

```python
def parse_task_status(tasks_md_path: Path) -> Tuple[int, int, int]:
    """
    Returns: (completed, in_progress, pending)

    Task markers:
        - [x] = completed
        - [-] = in-progress
        - [ ] = pending
    """
```

### Anomaly Detection

Detects dependency violations by checking if higher-numbered tasks are completed before lower-numbered tasks:

```python
def detect_task_anomalies(tasks_md_path: Path) -> List[str]:
    """
    Example: Task 8 [x] but Task 7 [ ] → Anomaly

    Returns: List of anomaly descriptions
    """
```

**Example Output**:
```
⚠️ ANOMALY: Task 8 completed before Task 7
('Integration tests' done, 'Core implementation' pending)
```

### Safe Updates

1. **Find Section**: Parse control spec to locate "## Current Status" section
2. **Create Backup**: Copy to `tasks.md.backup.TIMESTAMP`
3. **Atomic Write**: Write to temp file, then rename (prevents corruption)
4. **Preserve Content**: Only updates Current Status section, keeps all other sections intact

```python
def update_control_spec(project_root: Path, results: List[Dict], dry_run: bool = False) -> bool:
    """
    1. Read control spec
    2. Find Current Status section
    3. Generate updated table
    4. Create backup
    5. Atomic write (temp file + rename)
    """
```

## Current Status Section Format

The script updates this section in the control spec:

```markdown
## Current Status (Updated: 2025-10-27)

**Overall Progress**: 13/69 tasks complete (18.8%)

| Spec | Completed | Total | Percentage | Track Status |
|------|-----------|-------|------------|--------------|
| Exit Mutation Redesign | 5/8 | 8 | 62.5% | 3 task(s) pending |
| LLM Integration Activation | 5/14 | 14 | 35.7% | 9 task(s) pending |
| Structured Innovation MVP | 3/13 | 13 | 23.1% | 10 task(s) pending |
| YAML Normalizer Phase2 | 0/34 | 34 | 0.0% | 34 task(s) pending |
| **Control Spec** | 2/5 | 5 | 40.0% | 3 task(s) pending |
| **TOTAL** | **15/74** | **74** | **20.3%** | **59 tasks remaining** |

**⚠️ Dependency Anomalies Detected:** (only if anomalies exist)

**Exit Mutation Redesign:**
- Task 8 completed before Task 7 ('Metrics' done, 'Documentation' pending)

**Next Steps**:
1. Complete remaining 59 tasks (147.5h estimated)
2. Follow 5-day timeline for parallel execution
3. Address any dependency anomalies above

**Critical Path**: Track 3 (Structured Innovation MVP) - 2 days from start of Day 1

**Token Savings**: This tasks.md provides complete context in ~10K tokens vs 40K+ for re-analysis (75% reduction)
```

## Backups

Backups are created before every update:

```
.spec-workflow/specs/priority-specs-parallel-execution/
├── tasks.md                     # Current version
├── tasks.md.backup.20251027_125740  # Backup from first run
└── tasks.md.backup.20251027_125756  # Backup from second run
```

**Backup Naming**: `tasks.md.backup.YYYYMMDD_HHMMSS`

To restore from backup:
```bash
cp tasks.md.backup.20251027_125740 tasks.md
```

## Integration with Other Scripts

### Check Status (Read-Only)

```bash
# View current status without modifying
python scripts/check_priority_specs_status.py
```

### Sync Status (Update Control Spec)

```bash
# Update control spec with latest status
python scripts/sync_control_spec_status.py
```

### Validate Dependencies

```bash
# Check for dependency violations
python scripts/validate_spec_dependencies.py
```

### Calculate Timeline

```bash
# Predict completion date based on dependencies
python scripts/calculate_parallel_timeline.py
```

## Error Handling

### Missing Spec Files

```
WARNING: YAML Normalizer Phase2: Tasks file not found: .spec-workflow/specs/...
```

Script continues with available specs.

### Corrupted Markdown

```
ERROR: Could not find '## Current Status' section in control spec
```

Script exits without modifying files.

### Concurrent Updates

Script uses atomic writes (temp file + rename) to prevent corruption from concurrent updates.

### Anomaly Warnings

```
⚠️ ANOMALY: Task 8 completed before Task 7
```

Detected anomalies are shown in output and added to control spec status table for manual review.

## Exit Codes

- `0`: Success (synchronization complete)
- `1`: Error (file not found, parse error, write failure)

## Requirements

- **Python**: 3.7+
- **Dependencies**: Python stdlib only (no external packages)
- **Permissions**: Write access to control spec directory

## Testing

### Dry Run Test

```bash
python scripts/sync_control_spec_status.py --dry-run
```

### Verify Backup Created

```bash
ls -lt .spec-workflow/specs/priority-specs-parallel-execution/tasks.md.backup.*
```

### Verify Status Updated

```bash
grep "## Current Status" .spec-workflow/specs/priority-specs-parallel-execution/tasks.md -A 20
```

### Test Anomaly Detection

```python
from scripts.sync_control_spec_status import detect_task_anomalies
from pathlib import Path

anomalies = detect_task_anomalies(Path('.spec-workflow/specs/exit-mutation-redesign/tasks.md'))
print(f"Anomalies: {anomalies}")
```

## Troubleshooting

### "Could not find project root"

**Cause**: Script not run from project directory or .spec-workflow/ missing

**Solution**:
```bash
cd /path/to/finlab
python scripts/sync_control_spec_status.py
```

### "Control spec not found"

**Cause**: Control spec missing or path incorrect

**Solution**: Verify path in `CONTROL_SPEC_PATH` variable

### "Failed to create backup"

**Cause**: No write permissions or disk full

**Solution**: Check permissions and disk space

### Changes Not Visible

**Cause**: Dry-run mode active or section not found

**Solution**: Run without `--dry-run` flag, verify "## Current Status" section exists

## Implementation Details

### Constants

```python
SPECS = [
    {
        "name": "Exit Mutation Redesign",
        "short": "exit-mutation",
        "path": ".spec-workflow/specs/exit-mutation-redesign/tasks.md",
        "expected_total": 8
    },
    # ... 3 more specs
]

CONTROL_SPEC_PATH = ".spec-workflow/specs/priority-specs-parallel-execution/tasks.md"
```

### Key Functions

| Function | Purpose |
|----------|---------|
| `parse_task_status()` | Count completed/in-progress/pending tasks |
| `detect_task_anomalies()` | Find tasks done out of order |
| `read_individual_specs()` | Aggregate status from all 4 specs |
| `parse_current_status_section()` | Find section boundaries in control spec |
| `generate_status_table()` | Create updated markdown table |
| `update_control_spec()` | Backup + atomic write |

## Success Criteria (Task 4)

- [x] Script accurately detects completion status from 4 specs
- [x] Updates control spec without corrupting Markdown
- [x] Detects dependency violations (anomaly detection)
- [x] Can run as daily cron job (exit codes, no user input)
- [x] Backup created before any edits
- [x] Python stdlib only (no external dependencies)
- [x] Atomic writes prevent corruption
- [x] Handles concurrent updates gracefully
- [x] Dry-run mode for testing

## Related Documentation

- **Control Spec**: `.spec-workflow/specs/priority-specs-parallel-execution/tasks.md`
- **Status Check Script**: `scripts/check_priority_specs_status.py`
- **Dependency Validation**: `scripts/validate_spec_dependencies.py`
- **Timeline Calculator**: `scripts/calculate_parallel_timeline.py`
