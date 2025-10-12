# System Migration Guide - Fix 1.4

## Overview

The migration system ensures backward compatibility when transitioning from the old iteration system (pre-Fix 1.1 and 1.2) to the new template-based system with accurate metric extraction.

## What Does Migration Do?

### 1. Iteration History Migration
- Loads existing `iteration_history.jsonl` records
- Adds migration metadata to pre-fix records:
  - `_migration_flag: "pre_template_fix"` - Identifies old system records
  - `_migrated_at: <timestamp>` - Tracks when migration occurred
  - `_original_data_preserved: true` - Confirms no data loss
- Preserves ALL original data (metrics, template info, etc.)

### 2. Hall of Fame Migration
- Identifies high-performing strategies (Sharpe >= 2.0)
- Extracts Hall of Fame entries with available data
- Handles missing template information gracefully
- Prevents duplicate entries

### 3. Data Safety
- Creates timestamped backup before ANY modifications
- Validates all records during loading
- Handles corrupt/incomplete records gracefully
- Verifies no data loss occurred
- Provides comprehensive migration report

## Usage

### Basic Migration
```bash
python3 scripts/migrate_to_fixed_system.py
```

This will:
1. Load iteration history
2. Create backup: `iteration_history.backup-<timestamp>.jsonl`
3. Add migration flags to old records
4. Extract Hall of Fame entries (if any)
5. Save migrated data
6. Generate migration report

### Preview Mode (Dry Run)
```bash
python3 scripts/migrate_to_fixed_system.py --dry-run
```

Preview what will happen without making any changes. Use this to:
- Check how many records need migration
- Verify Hall of Fame candidates
- Ensure no errors will occur

### Backup Only
```bash
python3 scripts/migrate_to_fixed_system.py --backup-only
```

Create a backup without performing migration. Useful for:
- Manual backup before testing
- Creating snapshots at specific points

### Verify Migration
```bash
python3 scripts/migrate_to_fixed_system.py --verify
```

Verify that migration was successful. Checks:
- All records have migration flags OR template info
- No data corruption detected
- Hall of Fame entries created correctly

## Migration Report

After migration, you'll receive a comprehensive report:

```
======================================================================
SYSTEM MIGRATION REPORT - Fix 1.4
======================================================================

Migration Date: 2025-10-11T15:46:35.592401
Backup Location: /mnt/c/.../iteration_history.backup-2025-10-11-15-46-35.jsonl

ITERATION HISTORY MIGRATION:
  Total Records Loaded: 20
  Records Needing Migration: 20
  Records Already Migrated: 0
  Loading Errors: 0

HALL OF FAME MIGRATION:
  Candidates Found: 0
  Entries Created: 0
  Threshold (Sharpe): 2.0

DATA QUALITY:
  Data Loss: False
  Corruption Detected: False
  Original Data Preserved: True

MIGRATION STATUS:
  SUCCESS

======================================================================
```

The report is also saved to: `migration_report_<timestamp>.txt`

## Idempotency

The migration script is **idempotent** - safe to run multiple times:

- Already-migrated records are automatically skipped
- No duplicate Hall of Fame entries created
- Backup created each time (with unique timestamp)

Example:
```bash
# First run: migrates 20 records
python3 scripts/migrate_to_fixed_system.py

# Second run: skips all 20 records (already migrated)
python3 scripts/migrate_to_fixed_system.py
```

## Error Handling

### Graceful Degradation

The migration system handles errors gracefully:

1. **Corrupt JSONL Lines**: Skipped with warning, migration continues
2. **Missing Required Fields**: Record skipped, error logged
3. **Invalid Metrics Format**: Record skipped, error logged
4. **File Not Found**: Handles missing files gracefully

All errors are:
- Logged with line numbers
- Included in migration report
- Do NOT stop the migration process

### Recovery

If migration fails:

1. **Backup Exists**: Your original data is safe in `iteration_history.backup-<timestamp>.jsonl`
2. **Restore Backup**:
   ```bash
   cp iteration_history.backup-<timestamp>.jsonl iteration_history.jsonl
   ```
3. **Investigate**: Check migration report for errors
4. **Retry**: Fix issues and re-run migration

## Data Structure

### Before Migration
```json
{
  "iteration": 0,
  "success": true,
  "metrics": {"sharpe_ratio": 0.5, "annual_return": 0.08, "max_drawdown": 0.15},
  "template": null,
  "strategy_type": "momentum_0d"
}
```

### After Migration
```json
{
  "iteration": 0,
  "success": true,
  "metrics": {"sharpe_ratio": 0.5, "annual_return": 0.08, "max_drawdown": 0.15},
  "template": null,
  "strategy_type": "momentum_0d",
  "_migration_flag": "pre_template_fix",
  "_migrated_at": "2025-10-11T15:46:35.605350",
  "_original_data_preserved": true
}
```

### Hall of Fame Entry
```json
{
  "iteration": 10,
  "sharpe_ratio": 2.5,
  "annual_return": 0.35,
  "max_drawdown": 0.08,
  "strategy_type": "momentum_10d",
  "template": "unknown",
  "added_at": "2025-10-11T15:46:35.605380",
  "migrated_from_old_system": true,
  "success": true
}
```

## Integration with New System

### Iteration Engine Compatibility

The new iteration engine (`iteration_engine.py`) handles both old and new records:

```python
# Load iteration history
records, errors = load_iteration_history("iteration_history.jsonl")

# Check if record is from old system
def is_pre_fix_record(record):
    return record.get('_migration_flag') == 'pre_template_fix'

# Handle appropriately
if is_pre_fix_record(record):
    # Old system record - may have missing/incorrect data
    # Use with caution for feedback
else:
    # New system record - has template info and accurate metrics
    # Safe to use for template feedback
```

### Template Feedback System

The template feedback system (`src/feedback/template_feedback.py`) excludes pre-fix records:

```python
def should_include_in_feedback(record):
    """Only include post-fix records in template feedback."""
    return record.get('_migration_flag') != 'pre_template_fix'
```

## Hall of Fame Criteria

Records are added to Hall of Fame if:
- Sharpe Ratio >= 2.0
- Successfully backtested (`success: true`)
- Not already in Hall of Fame (no duplicates)

For pre-fix records:
- Template will be marked as `"unknown"`
- `migrated_from_old_system: true` flag added
- All available metrics preserved

## Testing

### Test Migration
```bash
# 1. Preview migration
python3 scripts/migrate_to_fixed_system.py --dry-run

# 2. Run migration
python3 scripts/migrate_to_fixed_system.py

# 3. Verify success
python3 scripts/migrate_to_fixed_system.py --verify

# 4. Check records
head -5 iteration_history.jsonl
```

### Test Idempotency
```bash
# Run twice - second run should skip all records
python3 scripts/migrate_to_fixed_system.py
python3 scripts/migrate_to_fixed_system.py --dry-run  # Should show 0 migrations
```

### Test Error Handling
```bash
# Create corrupt record
echo "invalid json" >> iteration_history.jsonl

# Migration should handle gracefully
python3 scripts/migrate_to_fixed_system.py --dry-run

# Restore from backup
cp iteration_history.backup-<timestamp>.jsonl iteration_history.jsonl
```

## FAQ

### Q: Will I lose any data?
**A:** No. The script:
- Creates backup BEFORE any changes
- Preserves all original data
- Adds new fields without removing old ones
- Verifies no data loss occurred

### Q: What if migration fails?
**A:** Your data is safe:
- Original data backed up to `iteration_history.backup-<timestamp>.jsonl`
- Simply restore the backup and investigate the error
- All errors are logged with details

### Q: Can I run migration multiple times?
**A:** Yes! The script is idempotent:
- Already-migrated records are skipped
- No duplicate processing
- Safe to re-run at any time

### Q: What happens to old records?
**A:** They are preserved with migration flags:
- Original data unchanged
- Migration metadata added
- Can be identified and handled appropriately by new system

### Q: Will Hall of Fame include old strategies?
**A:** Yes, if they meet criteria (Sharpe >= 2.0):
- High-performing old strategies included
- Template marked as "unknown"
- `migrated_from_old_system` flag set

### Q: How do I know if migration was successful?
**A:** Multiple indicators:
- Migration report shows "SUCCESS"
- Verify command passes: `python3 scripts/migrate_to_fixed_system.py --verify`
- All records have migration flags: check `_migration_flag` field

## Troubleshooting

### Issue: "File not found" error
**Solution:** Ensure you're running from project root:
```bash
cd /mnt/c/Users/jnpi/Documents/finlab
python3 scripts/migrate_to_fixed_system.py
```

### Issue: Permission denied
**Solution:** Check file permissions:
```bash
chmod +x scripts/migrate_to_fixed_system.py
```

### Issue: JSON decode errors
**Cause:** Corrupt lines in iteration history
**Solution:**
- Check error details in migration report
- Manually fix or remove corrupt lines
- Re-run migration

### Issue: Backup already exists
**Info:** This is normal - multiple backups with different timestamps are created
**Action:** No action needed - each backup is unique

## Best Practices

1. **Always preview first**:
   ```bash
   python3 scripts/migrate_to_fixed_system.py --dry-run
   ```

2. **Verify after migration**:
   ```bash
   python3 scripts/migrate_to_fixed_system.py --verify
   ```

3. **Keep backups**: Don't delete backup files until confident migration succeeded

4. **Monitor errors**: Check migration report for any warnings or errors

5. **Test with sample data**: If possible, test on a copy of data first

## Related Documentation

- [Fix 1.1: Template System](./FIX_1.1_TEMPLATE_SYSTEM.md)
- [Fix 1.2: Metric Extraction](./FIX_1.2_METRIC_EXTRACTION.md)
- [Fix 1.3: Integration Testing](./FIX_1.3_INTEGRATION_TESTING.md)
- [Template Feedback System](./FEEDBACK_SYSTEM.md)

## Summary

The migration system ensures a smooth transition from the old iteration system to the new template-based system with:

- **Zero data loss** through automatic backups
- **Graceful error handling** for corrupt/incomplete records
- **Comprehensive reporting** of migration results
- **Idempotent operation** safe to run multiple times
- **Hall of Fame migration** for high-performing strategies
- **Full backward compatibility** with the new system

The migration is a one-time process that marks old records while preserving all data, allowing the new system to handle both old and new records appropriately.
