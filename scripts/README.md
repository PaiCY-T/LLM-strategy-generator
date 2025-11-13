# Scripts Directory

## Migration Scripts

### migrate_to_fixed_system.py

**Purpose**: Migrate existing iteration history to be compatible with Fix 1.1 and 1.2 (template system and accurate metric extraction).

**Quick Start**:
```bash
# Preview migration (no changes)
python3 scripts/migrate_to_fixed_system.py --dry-run

# Run migration
python3 scripts/migrate_to_fixed_system.py

# Verify success
python3 scripts/migrate_to_fixed_system.py --verify
```

**What It Does**:
1. Creates timestamped backup of iteration history
2. Adds migration flags to pre-fix records
3. Extracts Hall of Fame entries (Sharpe >= 2.0)
4. Generates comprehensive migration report
5. Verifies no data loss

**Safety**:
- Creates backup before ANY changes
- Idempotent (safe to run multiple times)
- Graceful error handling
- Comprehensive validation

**Full Documentation**: See [docs/MIGRATION_GUIDE.md](../docs/MIGRATION_GUIDE.md)

## Other Scripts

(Add other scripts here as they are created)
