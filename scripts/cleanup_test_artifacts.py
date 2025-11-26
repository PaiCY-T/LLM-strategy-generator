#!/usr/bin/env python3
"""
cleanup_test_artifacts.py
Clean up temporary test files and artifacts

Usage:
    python scripts/cleanup_test_artifacts.py [--dry-run]

Options:
    --dry-run: Show what would be deleted without actually deleting
"""

import os
import sys
import glob
import shutil
from pathlib import Path
from typing import List, Tuple


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def delete_files(pattern: str, description: str, dry_run: bool = False) -> int:
    """Delete files matching the pattern.

    Args:
        pattern: Glob pattern to match files
        description: Human-readable description of files
        dry_run: If True, only show what would be deleted

    Returns:
        Number of files processed
    """
    print(f"{Colors.GREEN}Searching for: {description}{Colors.NC}")

    # Find all matching files recursively
    matches = list(Path('.').rglob(pattern))
    count = 0

    for file_path in matches:
        if file_path.is_file():
            if dry_run:
                print(f"  [DRY RUN] Would delete: {file_path}")
            else:
                try:
                    file_path.unlink()
                    print(f"  Deleted: {file_path}")
                    count += 1
                except Exception as e:
                    print(f"  {Colors.RED}Error deleting {file_path}: {e}{Colors.NC}")

    if count == 0 and not dry_run:
        print("  No files found")
    elif dry_run:
        print(f"  Found {len(matches)} file(s)")
    else:
        print(f"  Deleted {count} file(s)")

    print()
    return count


def delete_dirs(pattern: str, description: str, dry_run: bool = False) -> int:
    """Delete directories matching the pattern.

    Args:
        pattern: Glob pattern to match directories
        description: Human-readable description of directories
        dry_run: If True, only show what would be deleted

    Returns:
        Number of directories processed
    """
    print(f"{Colors.GREEN}Searching for: {description}{Colors.NC}")

    # Find all matching directories recursively
    matches = list(Path('.').rglob(pattern))
    count = 0

    for dir_path in matches:
        if dir_path.is_dir():
            if dry_run:
                print(f"  [DRY RUN] Would delete: {dir_path}")
            else:
                try:
                    shutil.rmtree(dir_path)
                    print(f"  Deleted: {dir_path}")
                    count += 1
                except Exception as e:
                    print(f"  {Colors.RED}Error deleting {dir_path}: {e}{Colors.NC}")

    if count == 0 and not dry_run:
        print("  No directories found")
    elif dry_run:
        print(f"  Found {len(matches)} director(ies)")
    else:
        print(f"  Deleted {count} director(ies)")

    print()
    return count


def main():
    """Main cleanup function"""
    # Parse arguments
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print(f"{Colors.YELLOW}DRY RUN MODE - No files will be deleted{Colors.NC}")
        print()

    print("=" * 40)
    print(" Test Artifacts Cleanup")
    print("=" * 40)
    print()

    # Clean up generated strategy files
    delete_files("generated_strategy_loop_iter*.py", "Generated strategy loop iteration files", dry_run)

    # Clean up iteration history files
    delete_files("iteration_history.json", "Iteration history JSON files", dry_run)

    # Clean up checkpoint directories
    delete_dirs("checkpoints_*", "Checkpoint directories", dry_run)

    # Clean up Python cache
    delete_dirs("__pycache__", "Python cache directories", dry_run)
    delete_dirs(".pytest_cache", "Pytest cache directories", dry_run)
    delete_dirs(".mypy_cache", "Mypy cache directories", dry_run)

    # Clean up log files (optional - ask for confirmation if not dry-run)
    if not dry_run:
        print(f"{Colors.YELLOW}Clean up log files? (y/N){Colors.NC}")
        response = input().strip().lower()
        if response in ['y', 'yes']:
            delete_files("*.log", "Log files", dry_run)

    # Clean up temporary files
    delete_files("*.tmp", "Temporary files", dry_run)
    delete_files("*.pkl", "Pickle files", dry_run)

    print("=" * 40)
    if dry_run:
        print(f"{Colors.YELLOW}DRY RUN COMPLETE{Colors.NC}")
        print("Run without --dry-run to actually delete files")
    else:
        print(f"{Colors.GREEN}CLEANUP COMPLETE{Colors.NC}")
    print("=" * 40)


if __name__ == "__main__":
    main()
