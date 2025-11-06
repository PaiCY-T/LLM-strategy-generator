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

echo "🔍 Running type safety checks (Hybrid Approach)..."
echo

# Check if mypy is installed
if ! command -v mypy &> /dev/null; then
    echo "⚠️  mypy not installed, skipping type checks"
    echo "   Install with: pip install mypy"
    exit 0
fi

# Run mypy on 4 core modules only
mypy src/learning/iteration_history.py \
     src/learning/champion_tracker.py \
     src/learning/iteration_executor.py \
     src/backtest/executor.py \
     2>&1 | head -50

MYPY_EXIT=$?

# Check result
if [ $MYPY_EXIT -eq 0 ]; then
    echo "✅ Type checks passed!"
    exit 0
else
    echo
    echo "❌ Type check errors found (showing first 50 lines)"
    echo
    echo "Options:"
    echo "  1. Fix the type errors before committing"
    echo "  2. Bypass with: git commit --no-verify (emergencies only)"
    echo
    exit 1
fi
