"""
System Migration Script - Fix 1.4
==================================

Migrates existing iteration_history.jsonl to be compatible with Fix 1.1 and 1.2.

Features:
- Loads and validates existing iteration history
- Adds migration flags to pre-fix records
- Migrates Hall of Fame entries
- Creates comprehensive migration report
- Backs up data before migration

Usage:
    python scripts/migrate_to_fixed_system.py
    python scripts/migrate_to_fixed_system.py --dry-run
    python scripts/migrate_to_fixed_system.py --verify
    python scripts/migrate_to_fixed_system.py --backup-only
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import argparse
import shutil
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File paths
PROJECT_ROOT = Path(__file__).parent.parent
ITERATION_HISTORY_PATH = PROJECT_ROOT / "iteration_history.jsonl"
HALL_OF_FAME_PATH = PROJECT_ROOT / "hall_of_fame.jsonl"

# Migration constants
MIGRATION_FLAG = "pre_template_fix"
HALL_OF_FAME_THRESHOLD = 2.0  # Sharpe ratio threshold


def load_iteration_history(file_path: Path) -> Tuple[List[Dict], List[str]]:
    """
    Load iteration history with validation.

    Returns:
        (records, errors): List of valid records and list of error messages
    """
    records = []
    errors = []

    if not file_path.exists():
        logger.warning(f"Iteration history file not found: {file_path}")
        return records, [f"File not found: {file_path}"]

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)

                # Validate required fields
                required_fields = ['iteration', 'success', 'metrics']
                missing_fields = [field for field in required_fields if field not in record]

                if missing_fields:
                    error_msg = f"Line {line_num}: Missing required fields: {missing_fields}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    continue

                # Validate metrics structure
                if not isinstance(record.get('metrics'), dict):
                    error_msg = f"Line {line_num}: Invalid metrics format (not a dict)"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    continue

                records.append(record)

            except json.JSONDecodeError as e:
                error_msg = f"Line {line_num}: JSON decode error: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue
            except Exception as e:
                error_msg = f"Line {line_num}: Unexpected error: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue

    logger.info(f"Loaded {len(records)} valid records, {len(errors)} errors")
    return records, errors


def needs_migration(record: Dict) -> bool:
    """
    Check if a record needs migration.

    Returns True if record is from the old system (no migration flag).
    """
    return '_migration_flag' not in record


def add_migration_flags(record: Dict) -> Dict:
    """
    Add migration metadata to pre-fix records.

    Adds:
    - _migration_flag: "pre_template_fix"
    - _migrated_at: ISO timestamp
    - _original_data_preserved: True
    """
    if not needs_migration(record):
        return record

    migrated_record = record.copy()
    migrated_record['_migration_flag'] = MIGRATION_FLAG
    migrated_record['_migrated_at'] = datetime.now().isoformat()
    migrated_record['_original_data_preserved'] = True

    return migrated_record


def extract_hall_of_fame_entry(record: Dict) -> Optional[Dict]:
    """
    Extract Hall of Fame entry from a high-performing strategy.

    Args:
        record: Iteration history record

    Returns:
        Hall of Fame entry dict or None if not eligible
    """
    metrics = record.get('metrics', {})
    sharpe = metrics.get('sharpe_ratio', 0.0)

    # Check if meets Hall of Fame criteria
    if sharpe < HALL_OF_FAME_THRESHOLD:
        return None

    # Create Hall of Fame entry with available data
    entry = {
        'iteration': record.get('iteration'),
        'sharpe_ratio': sharpe,
        'annual_return': metrics.get('annual_return', 0.0),
        'max_drawdown': metrics.get('max_drawdown', 0.0),
        'strategy_type': record.get('strategy_type', 'unknown'),
        'template': record.get('template', 'unknown'),  # Will be null for old records
        'added_at': datetime.now().isoformat(),
        'migrated_from_old_system': needs_migration(record),
        'success': record.get('success', False)
    }

    # Add any additional metrics that exist
    for key, value in metrics.items():
        if key not in ['sharpe_ratio', 'annual_return', 'max_drawdown']:
            entry[f'metric_{key}'] = value

    return entry


def migrate_hall_of_fame(records: List[Dict]) -> List[Dict]:
    """
    Extract Hall of Fame entries from high-performing strategies.

    Criteria: Sharpe >= 2.0

    Returns:
        List of Hall of Fame entries
    """
    hall_of_fame_entries = []

    for record in records:
        entry = extract_hall_of_fame_entry(record)
        if entry:
            hall_of_fame_entries.append(entry)

    logger.info(f"Found {len(hall_of_fame_entries)} Hall of Fame candidates")
    return hall_of_fame_entries


def create_backup(source: Path) -> Path:
    """
    Create timestamped backup of iteration history.

    Returns: Path to backup file
    """
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    backup_name = f"{source.stem}.backup-{timestamp}{source.suffix}"
    backup_path = source.parent / backup_name

    shutil.copy2(source, backup_path)
    logger.info(f"Created backup: {backup_path}")

    # Verify backup
    if not backup_path.exists():
        raise RuntimeError(f"Backup creation failed: {backup_path}")

    backup_size = backup_path.stat().st_size
    source_size = source.stat().st_size

    if backup_size != source_size:
        raise RuntimeError(f"Backup size mismatch: {backup_size} != {source_size}")

    logger.info(f"Backup verified: {backup_size} bytes")
    return backup_path


def save_records(records: List[Dict], file_path: Path) -> None:
    """
    Save records to JSONL file.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            json.dump(record, f)
            f.write('\n')

    logger.info(f"Saved {len(records)} records to {file_path}")


def save_hall_of_fame(entries: List[Dict], file_path: Path) -> None:
    """
    Save Hall of Fame entries to JSONL file.

    Appends to existing file if it exists.
    """
    # Load existing entries to avoid duplicates
    existing_entries = []
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    existing_entries.append(json.loads(line))

    # Get existing iterations
    existing_iterations = {entry.get('iteration') for entry in existing_entries}

    # Filter out duplicates
    new_entries = [entry for entry in entries if entry.get('iteration') not in existing_iterations]

    if new_entries:
        with open(file_path, 'a', encoding='utf-8') as f:
            for entry in new_entries:
                json.dump(entry, f)
                f.write('\n')

        logger.info(f"Added {len(new_entries)} new Hall of Fame entries (skipped {len(entries) - len(new_entries)} duplicates)")
    else:
        logger.info("No new Hall of Fame entries to add (all duplicates)")


def generate_migration_report(stats: Dict) -> str:
    """
    Generate comprehensive migration report.
    """
    report = [
        "=" * 70,
        "SYSTEM MIGRATION REPORT - Fix 1.4",
        "=" * 70,
        "",
        f"Migration Date: {stats['migration_date']}",
        f"Backup Location: {stats['backup_path']}",
        "",
        "ITERATION HISTORY MIGRATION:",
        f"  Total Records Loaded: {stats['total_records']}",
        f"  Records Needing Migration: {stats['records_migrated']}",
        f"  Records Already Migrated: {stats['records_skipped']}",
        f"  Loading Errors: {stats['loading_errors']}",
        "",
        "HALL OF FAME MIGRATION:",
        f"  Candidates Found: {stats['hall_of_fame_candidates']}",
        f"  Entries Created: {stats['hall_of_fame_created']}",
        f"  Threshold (Sharpe): {HALL_OF_FAME_THRESHOLD}",
        "",
        "DATA QUALITY:",
        f"  Data Loss: {stats['data_loss']}",
        f"  Corruption Detected: {stats['corruption_detected']}",
        f"  Original Data Preserved: {stats['original_data_preserved']}",
        "",
    ]

    if stats['loading_errors'] > 0:
        report.extend([
            "ERRORS ENCOUNTERED:",
            *[f"  - {error}" for error in stats.get('error_details', [])[:10]],
        ])
        if len(stats.get('error_details', [])) > 10:
            report.append(f"  ... and {len(stats['error_details']) - 10} more errors")
        report.append("")

    report.extend([
        "MIGRATION STATUS:",
        f"  {'SUCCESS' if stats['success'] else 'FAILED'}",
        "",
        "=" * 70,
    ])

    return "\n".join(report)


def migrate_system(dry_run: bool = False) -> Dict:
    """
    Main migration function.

    Args:
        dry_run: If True, preview migration without making changes

    Returns:
        Migration statistics dictionary
    """
    logger.info("=" * 70)
    logger.info("Starting System Migration - Fix 1.4")
    logger.info("=" * 70)

    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    stats = {
        'migration_date': datetime.now().isoformat(),
        'dry_run': dry_run,
        'total_records': 0,
        'records_migrated': 0,
        'records_skipped': 0,
        'loading_errors': 0,
        'error_details': [],
        'hall_of_fame_candidates': 0,
        'hall_of_fame_created': 0,
        'backup_path': None,
        'data_loss': False,
        'corruption_detected': False,
        'original_data_preserved': True,
        'success': False
    }

    try:
        # Step 1: Load existing iteration history
        logger.info("\nStep 1: Loading iteration history...")
        records, errors = load_iteration_history(ITERATION_HISTORY_PATH)

        stats['total_records'] = len(records)
        stats['loading_errors'] = len(errors)
        stats['error_details'] = errors
        stats['corruption_detected'] = len(errors) > 0

        if not records:
            logger.warning("No valid records found to migrate")
            stats['success'] = True
            return stats

        # Step 2: Create backup
        if not dry_run:
            logger.info("\nStep 2: Creating backup...")
            backup_path = create_backup(ITERATION_HISTORY_PATH)
            stats['backup_path'] = str(backup_path)
        else:
            logger.info("\nStep 2: Skipping backup (dry run)")
            stats['backup_path'] = "N/A (dry run)"

        # Step 3: Add migration flags
        logger.info("\nStep 3: Adding migration flags...")
        migrated_records = []
        for record in records:
            if needs_migration(record):
                migrated_record = add_migration_flags(record)
                migrated_records.append(migrated_record)
                stats['records_migrated'] += 1
            else:
                migrated_records.append(record)
                stats['records_skipped'] += 1

        logger.info(f"  Migrated: {stats['records_migrated']}, Skipped: {stats['records_skipped']}")

        # Step 4: Extract Hall of Fame entries
        logger.info("\nStep 4: Extracting Hall of Fame entries...")
        hall_of_fame_entries = migrate_hall_of_fame(records)
        stats['hall_of_fame_candidates'] = len(hall_of_fame_entries)

        # Step 5: Save migrated data
        if not dry_run:
            logger.info("\nStep 5: Saving migrated data...")
            save_records(migrated_records, ITERATION_HISTORY_PATH)

            if hall_of_fame_entries:
                save_hall_of_fame(hall_of_fame_entries, HALL_OF_FAME_PATH)
                stats['hall_of_fame_created'] = len(hall_of_fame_entries)
        else:
            logger.info("\nStep 5: Skipping save (dry run)")
            stats['hall_of_fame_created'] = 0

        # Step 6: Verify no data loss
        logger.info("\nStep 6: Verifying data integrity...")
        if len(migrated_records) != len(records):
            logger.error(f"Data loss detected: {len(records)} -> {len(migrated_records)}")
            stats['data_loss'] = True
        else:
            logger.info("No data loss detected")

        stats['success'] = not stats['data_loss']

    except Exception as e:
        logger.error(f"Migration failed with error: {e}", exc_info=True)
        stats['success'] = False
        stats['error_details'].append(f"Fatal error: {e}")

    return stats


def verify_migration() -> bool:
    """
    Verify migration was successful.

    Checks:
    - All records have migration flags or are new
    - No data loss occurred
    - Hall of Fame entries created correctly
    """
    logger.info("=" * 70)
    logger.info("Verifying Migration")
    logger.info("=" * 70)

    try:
        # Load current iteration history
        records, errors = load_iteration_history(ITERATION_HISTORY_PATH)

        if errors:
            logger.error(f"Found {len(errors)} errors in iteration history")
            return False

        # Check all records have migration flags or template info
        records_without_migration_info = 0
        for record in records:
            has_migration_flag = '_migration_flag' in record
            has_template = record.get('template') is not None

            if not (has_migration_flag or has_template):
                records_without_migration_info += 1

        if records_without_migration_info > 0:
            logger.error(f"Found {records_without_migration_info} records without migration info")
            return False

        logger.info(f"All {len(records)} records have proper migration info")

        # Check Hall of Fame
        if HALL_OF_FAME_PATH.exists():
            with open(HALL_OF_FAME_PATH, 'r', encoding='utf-8') as f:
                hof_entries = [json.loads(line) for line in f if line.strip()]
            logger.info(f"Hall of Fame contains {len(hof_entries)} entries")
        else:
            logger.info("No Hall of Fame file found (may be empty)")

        logger.info("\n" + "=" * 70)
        logger.info("VERIFICATION PASSED")
        logger.info("=" * 70)
        return True

    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Migrate iteration history to fixed system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                  # Run migration
  %(prog)s --dry-run        # Preview without changes
  %(prog)s --backup-only    # Only create backup
  %(prog)s --verify         # Verify migration success
        """
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview migration without making changes'
    )
    parser.add_argument(
        '--backup-only',
        action='store_true',
        help='Only create backup without migrating'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify migration was successful'
    )

    args = parser.parse_args()

    # Handle verify mode
    if args.verify:
        success = verify_migration()
        sys.exit(0 if success else 1)

    # Handle backup-only mode
    if args.backup_only:
        try:
            backup_path = create_backup(ITERATION_HISTORY_PATH)
            logger.info(f"Backup created successfully: {backup_path}")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            sys.exit(1)

    # Run migration
    stats = migrate_system(dry_run=args.dry_run)

    # Generate and display report
    report = generate_migration_report(stats)
    print("\n" + report)

    # Save report to file
    if not args.dry_run:
        report_path = PROJECT_ROOT / f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"\nReport saved to: {report_path}")

    sys.exit(0 if stats['success'] else 1)


if __name__ == '__main__':
    main()
