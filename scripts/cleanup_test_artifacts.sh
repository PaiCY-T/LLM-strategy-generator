#!/bin/bash
# cleanup_test_artifacts.sh
# Clean up temporary test files and artifacts
#
# Usage:
#   ./scripts/cleanup_test_artifacts.sh [--dry-run]
#
# Options:
#   --dry-run: Show what would be deleted without actually deleting

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=1
    echo -e "${YELLOW}DRY RUN MODE - No files will be deleted${NC}"
    echo ""
fi

# Function to delete files
delete_files() {
    local pattern=$1
    local description=$2

    echo -e "${GREEN}Searching for: ${description}${NC}"

    if [[ $DRY_RUN -eq 1 ]]; then
        find . -name "$pattern" -type f 2>/dev/null | while read -r file; do
            echo "  [DRY RUN] Would delete: $file"
        done
    else
        local count=0
        find . -name "$pattern" -type f 2>/dev/null | while read -r file; do
            rm -f "$file"
            echo "  Deleted: $file"
            ((count++))
        done
        if [[ $count -eq 0 ]]; then
            echo "  No files found"
        else
            echo "  Deleted $count file(s)"
        fi
    fi
    echo ""
}

# Function to delete directories
delete_dirs() {
    local pattern=$1
    local description=$2

    echo -e "${GREEN}Searching for: ${description}${NC}"

    if [[ $DRY_RUN -eq 1 ]]; then
        find . -name "$pattern" -type d 2>/dev/null | while read -r dir; do
            echo "  [DRY RUN] Would delete: $dir"
        done
    else
        local count=0
        find . -name "$pattern" -type d 2>/dev/null | while read -r dir; do
            rm -rf "$dir"
            echo "  Deleted: $dir"
            ((count++))
        done
        if [[ $count -eq 0 ]]; then
            echo "  No directories found"
        else
            echo "  Deleted $count director(ies)"
        fi
    fi
    echo ""
}

echo "========================================="
echo " Test Artifacts Cleanup"
echo "========================================="
echo ""

# Clean up generated strategy files
delete_files "generated_strategy_loop_iter*.py" "Generated strategy loop iteration files"

# Clean up iteration history files
delete_files "iteration_history.json" "Iteration history JSON files"

# Clean up checkpoint directories
delete_dirs "checkpoints_*" "Checkpoint directories"

# Clean up Python cache
delete_dirs "__pycache__" "Python cache directories"
delete_dirs ".pytest_cache" "Pytest cache directories"
delete_dirs ".mypy_cache" "Mypy cache directories"

# Clean up log files (optional - ask for confirmation if not dry-run)
if [[ $DRY_RUN -eq 0 ]]; then
    echo -e "${YELLOW}Clean up log files? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        delete_files "*.log" "Log files"
    fi
fi

# Clean up temporary files
delete_files "*.tmp" "Temporary files"
delete_files "*.pkl" "Pickle files"

echo "========================================="
if [[ $DRY_RUN -eq 1 ]]; then
    echo -e "${YELLOW}DRY RUN COMPLETE${NC}"
    echo "Run without --dry-run to actually delete files"
else
    echo -e "${GREEN}CLEANUP COMPLETE${NC}"
fi
echo "========================================="
