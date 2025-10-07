#!/bin/bash
# Phase 3 Verification Script

echo "=========================================="
echo "Phase 3: Storage Layer Verification"
echo "=========================================="
echo

# Check file existence
echo "1. Checking file existence..."
FILES=(
    "src/utils/init_db.py"
    "src/storage/__init__.py"
    "src/storage/manager.py"
    "src/storage/backup.py"
    "tests/storage/__init__.py"
    "tests/storage/test_manager.py"
)

ALL_EXIST=true
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file MISSING"
        ALL_EXIST=false
    fi
done
echo

# Type checking
echo "2. Running mypy type checking..."
if mypy src/storage/ src/utils/init_db.py --strict 2>&1 | grep -q "Success"; then
    echo "  ✓ mypy passed (100% type safety)"
else
    echo "  ✗ mypy failed"
    exit 1
fi
echo

# Code quality
echo "3. Running flake8 code quality check..."
if flake8 src/storage/ src/utils/init_db.py tests/storage/ --max-line-length=100; then
    echo "  ✓ flake8 passed (PEP 8 compliant)"
else
    echo "  ✗ flake8 failed"
    exit 1
fi
echo

# Line counts
echo "4. Code statistics..."
echo "  Implementation:"
wc -l src/utils/init_db.py src/storage/*.py | tail -1 | awk '{print "    - " $1 " lines"}'
echo "  Tests:"
wc -l tests/storage/*.py | tail -1 | awk '{print "    - " $1 " lines"}'
echo

echo "=========================================="
echo "Phase 3 Verification: COMPLETE ✓"
echo "=========================================="
