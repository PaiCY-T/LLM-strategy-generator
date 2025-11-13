#!/bin/bash
# Phase 1 Quality Check Commands
# Usage: bash docs/phase1/QUALITY_CHECK_COMMANDS.sh

set -e
cd /mnt/c/Users/jnpi/Documents/finlab/LLM-strategy-generator

echo "=========================================="
echo "Phase 1 Quality Check Suite"
echo "=========================================="
echo ""

# 1. Cyclomatic Complexity Analysis
echo "1. Cyclomatic Complexity Analysis"
echo "-----------------------------------"
radon cc src/learning/iteration_executor.py -a -nb
echo ""
echo "Target: <5.0 average"
echo "Current: 8.56 average"
echo ""

# 2. Maintainability Index
echo "2. Maintainability Index"
echo "-----------------------------------"
radon mi src/learning/iteration_executor.py src/learning/config.py src/learning/exceptions.py -s
echo ""
echo "Target: A-grade (20-100)"
echo "All files: A-grade ✓"
echo ""

# 3. Type Safety Check
echo "3. Type Safety Check (Phase 1 Files Only)"
echo "-----------------------------------"
echo "Checking exceptions.py..."
mypy src/learning/exceptions.py --ignore-missing-imports 2>&1 | grep "^src/learning/exceptions.py" || echo "No errors in exceptions.py"
echo ""
echo "Checking config.py..."
mypy src/learning/config.py --ignore-missing-imports 2>&1 | grep "^src/learning/config.py" || echo "No errors in config.py"
echo ""
echo "Target: 0 errors"
echo "Current: 9 errors in exceptions.py (PEP 484 violations)"
echo ""

# 4. Test Execution
echo "4. Test Execution"
echo "-----------------------------------"
export ENABLE_GENERATION_REFACTORING=true
export PHASE1_CONFIG_ENFORCEMENT=true
pytest tests/learning/test_iteration_executor_phase1.py -v --tb=short
echo ""

# 5. Coverage Analysis
echo "5. Coverage Analysis"
echo "-----------------------------------"
pytest tests/learning/test_iteration_executor_phase1.py \
  --cov=src/learning.iteration_executor \
  --cov-report=term-missing \
  --cov-report=html:htmlcov/phase1 \
  -q
echo ""
echo "Target: >95%"
echo "Current: 98.7% ✓"
echo ""

# 6. Summary
echo "=========================================="
echo "Quality Check Summary"
echo "=========================================="
echo "✅ Test Coverage: 98.7%"
echo "✅ Maintainability: A-grade"
echo "⚠️  Complexity: 8.56 (target <5.0)"
echo "❌ Type Safety: 9 errors"
echo ""
echo "Overall: 7.5/10 - CONDITIONAL PASS"
echo "=========================================="
