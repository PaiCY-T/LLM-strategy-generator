#!/usr/bin/env python3
"""
Migration Script: Champion Strategy → Hall of Fame
====================================================

Migrates legacy champion_strategy.json to unified Hall of Fame repository.

C1 Fix: Resolves champion concept conflict by migrating Learning System's
single-champion JSON persistence to Template System's multi-tier Hall of Fame.

Usage:
    python3 migrate_champion_to_hall_of_fame.py [--backup] [--dry-run]

Flags:
    --backup    : Create backup of champion_strategy.json before migration
    --dry-run   : Show what would be migrated without making changes
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.repository.hall_of_fame import HallOfFameRepository, StrategyGenome
from src.constants import CHAMPION_FILE


def load_legacy_champion(champion_file: str) -> Optional[dict]:
    """Load champion from legacy JSON file.

    Args:
        champion_file: Path to champion_strategy.json

    Returns:
        Champion data dictionary, or None if file doesn't exist or is invalid
    """
    if not os.path.exists(champion_file):
        print(f"ℹ️  No legacy champion file found at: {champion_file}")
        return None

    try:
        with open(champion_file, 'r') as f:
            data = json.load(f)

        # Validate required fields
        required = ['iteration_num', 'code', 'parameters', 'metrics', 'success_patterns', 'timestamp']
        missing = [field for field in required if field not in data]

        if missing:
            print(f"❌ Invalid champion file - missing fields: {missing}")
            return None

        return data

    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Failed to load champion file: {e}")
        return None


def convert_to_genome(champion_data: dict) -> StrategyGenome:
    """Convert legacy champion data to StrategyGenome.

    Args:
        champion_data: Dictionary from champion_strategy.json

    Returns:
        StrategyGenome object for Hall of Fame
    """
    return StrategyGenome(
        template_name='autonomous_generated',  # Legacy autonomous loop strategies
        parameters=champion_data['parameters'],
        metrics=champion_data['metrics'],
        created_at=champion_data['timestamp'],
        strategy_code=champion_data['code'],
        success_patterns=champion_data['success_patterns'],
        genome_id=champion_data['iteration_num']  # Use iteration as genome ID
    )


def backup_legacy_file(champion_file: str) -> str:
    """Create timestamped backup of legacy champion file.

    Args:
        champion_file: Path to champion_strategy.json

    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{champion_file}.backup_{timestamp}"

    shutil.copy2(champion_file, backup_path)
    return backup_path


def print_champion_summary(champion_data: dict) -> None:
    """Print human-readable summary of champion being migrated.

    Args:
        champion_data: Champion data dictionary
    """
    print("\n📊 Champion Summary:")
    print(f"   Iteration: {champion_data['iteration_num']}")
    print(f"   Timestamp: {champion_data['timestamp']}")

    metrics = champion_data.get('metrics', {})
    print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}")
    print(f"   Annual Return: {metrics.get('annual_return', 'N/A')}")
    print(f"   Max Drawdown: {metrics.get('max_drawdown', 'N/A')}")

    success_patterns = champion_data.get('success_patterns', [])
    if success_patterns:
        print(f"   Success Patterns: {len(success_patterns)}")
        for i, pattern in enumerate(success_patterns[:3], 1):
            print(f"      {i}. {pattern}")
        if len(success_patterns) > 3:
            print(f"      ... and {len(success_patterns) - 3} more")


def determine_tier(metrics: dict) -> str:
    """Determine Hall of Fame tier based on Sharpe ratio.

    Args:
        metrics: Performance metrics dictionary

    Returns:
        Tier name (champions/contenders/archive)
    """
    sharpe = metrics.get('sharpe_ratio', 0)

    if sharpe >= 2.0:
        return "champions"
    elif sharpe >= 1.5:
        return "contenders"
    else:
        return "archive"


def migrate_champion(
    champion_file: str = CHAMPION_FILE,
    backup: bool = False,
    dry_run: bool = False
) -> bool:
    """Migrate legacy champion to Hall of Fame.

    Args:
        champion_file: Path to champion_strategy.json
        backup: Whether to create backup before migration
        dry_run: If True, show what would be migrated without making changes

    Returns:
        True if migration successful, False otherwise
    """
    print("="*70)
    print("Champion Migration: JSON → Hall of Fame")
    print("="*70)

    # Step 1: Load legacy champion
    print(f"\n[1/4] Loading legacy champion from {champion_file}...")
    champion_data = load_legacy_champion(champion_file)

    if not champion_data:
        return False

    print("✅ Champion loaded successfully")

    # Step 2: Show summary
    print_champion_summary(champion_data)

    # Step 3: Determine target tier
    tier = determine_tier(champion_data['metrics'])
    print(f"\n🎯 Target tier: {tier.upper()}")

    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made")
        print("\nWould migrate:")
        print(f"   From: {champion_file}")
        print(f"   To: hall_of_fame/{tier}/strategy_{champion_data['iteration_num']}.json")
        print("\n✅ Dry run complete - no changes made")
        return True

    # Step 4: Backup if requested
    if backup:
        print(f"\n[2/4] Creating backup...")
        backup_path = backup_legacy_file(champion_file)
        print(f"✅ Backup created: {backup_path}")
    else:
        print(f"\n[2/4] Skipping backup (use --backup to create)")

    # Step 5: Convert and save to Hall of Fame
    print(f"\n[3/4] Converting to StrategyGenome format...")
    genome = convert_to_genome(champion_data)
    print("✅ Conversion complete")

    print(f"\n[4/4] Saving to Hall of Fame...")
    hall_of_fame = HallOfFameRepository()

    try:
        hall_of_fame.add_strategy(
            template_name=genome.template_name,
            parameters=genome.parameters,
            metrics=genome.metrics,
            strategy_code=genome.strategy_code,
            success_patterns=genome.success_patterns
        )
        print(f"✅ Champion saved to Hall of Fame ({tier} tier)")
    except Exception as e:
        print(f"❌ Failed to save to Hall of Fame: {e}")
        return False

    # Step 6: Verification
    print(f"\n✅ Migration complete!")
    print(f"\n📍 Champion location: hall_of_fame/{tier}/strategy_{genome.genome_id}.json")

    # Optional: Suggest removing legacy file
    print(f"\n💡 Suggestion: You can now remove the legacy file:")
    print(f"   rm {champion_file}")
    if backup:
        print(f"   (Backup preserved at: {backup_path})")

    return True


def main():
    """Main migration script entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate legacy champion_strategy.json to Hall of Fame",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic migration
  python3 migrate_champion_to_hall_of_fame.py

  # With backup
  python3 migrate_champion_to_hall_of_fame.py --backup

  # Dry run (preview without changes)
  python3 migrate_champion_to_hall_of_fame.py --dry-run
        """
    )

    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create timestamped backup of champion_strategy.json before migration'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be migrated without making changes'
    )

    parser.add_argument(
        '--champion-file',
        default=CHAMPION_FILE,
        help=f'Path to champion file (default: {CHAMPION_FILE})'
    )

    args = parser.parse_args()

    # Run migration
    success = migrate_champion(
        champion_file=args.champion_file,
        backup=args.backup,
        dry_run=args.dry_run
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
