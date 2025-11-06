#!/bin/bash
# Pre-commit hook for type safety checks (Hybrid Approach)
#
# Installation:
#   cp scripts/pre-commit-hook.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# This hook runs mypy on the 4 core modules to catch API mismatches
# before committing. Aligned with "避免過度工程化" principle.
#
# To bypass (for emergencies): git commit --no-verify

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Running type safety checks (Hybrid Approach)..."
echo

# ISSUE #8 FIX: Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Check if mypy is installed
if ! command -v mypy &> /dev/null; then
    echo -e "${YELLOW}⚠️  mypy not installed, skipping type checks${NC}"
    echo "   Install with: pip install mypy"
    exit 0
fi

# Check if mypy.ini exists
if [ ! -f "mypy.ini" ]; then
    echo -e "${YELLOW}⚠️  mypy.ini not found, skipping type checks${NC}"
    exit 0
fi

# ISSUE #7 FIX: Capture mypy output and exit code BEFORE piping
# This ensures we get mypy's exit code, not head's exit code
MYPY_OUTPUT=$(mypy --config-file=mypy.ini 2>&1)
MYPY_EXIT=$?

# Count errors
ERROR_COUNT=$(echo "$MYPY_OUTPUT" | grep -c "error:" || echo "0")

# Check result
if [ $MYPY_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ Type checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Type check errors found${NC}"
    echo
    echo "Found $ERROR_COUNT type error(s) (showing first 50 lines):"
    echo
    echo "$MYPY_OUTPUT" | head -50
    echo
    echo "Options:"
    echo "  1. Fix the type errors before committing"
    echo "  2. Bypass with: git commit --no-verify (emergencies only)"
    echo
    exit 1
fi
