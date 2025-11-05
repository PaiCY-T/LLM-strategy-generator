#!/bin/bash
# Update Hardcoded Spec Paths
# Replace .claude/specs → .spec-workflow/specs
# Date: 2025-10-28

set -e

echo "=========================================="
echo "Updating Hardcoded Spec Paths"
echo "=========================================="
echo "From: .claude/specs"
echo "To:   .spec-workflow/specs"
echo ""

# Count total files to update
TOTAL_FILES=$(grep -r "\.claude/specs" /mnt/c/Users/jnpi/documents/finlab \
    --include="*.py" --include="*.sh" --include="*.md" --include="*.yaml" \
    --exclude-dir=".claude/specs.backup*" --exclude-dir=".claude.backup*" \
    --exclude-dir="node_modules" --exclude-dir=".git" \
    -l 2>/dev/null | grep -v "DEPRECATED.md" | grep -v "update_spec_paths.sh" | wc -l)

echo "Found $TOTAL_FILES files to update"
echo ""

# Categories of files to update
echo "[1/6] Updating .claude/commands files..."
COMMANDS_UPDATED=0
for file in .claude/commands/population-based-learning/task-*.md; do
    if [ -f "$file" ] && grep -q "\.claude/specs" "$file"; then
        sed -i 's|\.claude/specs|.spec-workflow/specs|g' "$file"
        COMMANDS_UPDATED=$((COMMANDS_UPDATED + 1))
    fi
done
echo "✅ Updated $COMMANDS_UPDATED command files"
echo ""

echo "[2/6] Updating documentation files in root..."
ROOT_UPDATED=0
for file in *.md; do
    if [ -f "$file" ] && [ "$file" != "update_spec_paths.sh" ] && grep -q "\.claude/specs" "$file" 2>/dev/null; then
        sed -i 's|\.claude/specs|.spec-workflow/specs|g' "$file"
        ROOT_UPDATED=$((ROOT_UPDATED + 1))
    fi
done
echo "✅ Updated $ROOT_UPDATED root documentation files"
echo ""

echo "[3/6] Updating docs/ directory files..."
DOCS_UPDATED=0
if [ -d "docs" ]; then
    find docs -type f \( -name "*.md" -o -name "*.py" \) -exec grep -l "\.claude/specs" {} \; 2>/dev/null | while read file; do
        sed -i 's|\.claude/specs|.spec-workflow/specs|g' "$file"
        DOCS_UPDATED=$((DOCS_UPDATED + 1))
    done
fi
DOCS_UPDATED=$(find docs -type f \( -name "*.md" -o -name "*.py" \) -exec grep -l "\.spec-workflow/specs" {} \; 2>/dev/null | wc -l)
echo "✅ Updated $DOCS_UPDATED docs files"
echo ""

echo "[4/6] Updating Python source files..."
SRC_UPDATED=0
if [ -d "src" ]; then
    find src -type f -name "*.py" -exec grep -l "\.claude/specs" {} \; 2>/dev/null | while read file; do
        sed -i 's|\.claude/specs|.spec-workflow/specs|g' "$file"
        SRC_UPDATED=$((SRC_UPDATED + 1))
    done
fi
SRC_UPDATED=$(find src -type f -name "*.py" -exec grep -l "\.spec-workflow/specs" {} \; 2>/dev/null | wc -l)
echo "✅ Updated $SRC_UPDATED source files"
echo ""

echo "[5/6] Updating test files..."
TEST_UPDATED=0
if [ -d "tests" ]; then
    find tests -type f -name "*.py" -exec grep -l "\.claude/specs" {} \; 2>/dev/null | while read file; do
        sed -i 's|\.claude/specs|.spec-workflow/specs|g' "$file"
        TEST_UPDATED=$((TEST_UPDATED + 1))
    done
fi
TEST_UPDATED=$(find tests -type f -name "*.py" -exec grep -l "\.spec-workflow/specs" {} \; 2>/dev/null | wc -l)
echo "✅ Updated $TEST_UPDATED test files"
echo ""

echo "[6/6] Updating script files..."
SCRIPT_UPDATED=0
find . -maxdepth 2 -type f \( -name "*.sh" -o -name "*.py" \) \
    ! -path "./.git/*" \
    ! -path "./.claude.backup*" \
    ! -path "./.claude/specs.backup*" \
    ! -name "update_spec_paths.sh" \
    -exec grep -l "\.claude/specs" {} \; 2>/dev/null | while read file; do
    sed -i 's|\.claude/specs|.spec-workflow/specs|g' "$file"
    SCRIPT_UPDATED=$((SCRIPT_UPDATED + 1))
done
SCRIPT_UPDATED=$(find . -maxdepth 2 -type f \( -name "*.sh" -o -name "*.py" \) \
    ! -path "./.git/*" \
    ! -path "./.claude.backup*" \
    ! -path "./.claude/specs.backup*" \
    ! -name "update_spec_paths.sh" \
    -exec grep -l "\.spec-workflow/specs" {} \; 2>/dev/null | wc -l)
echo "✅ Updated $SCRIPT_UPDATED script files"
echo ""

# Update .spec-workflow/specs internal references
echo "[Bonus] Updating internal references in .spec-workflow/specs..."
SPEC_INTERNAL_UPDATED=0
if [ -d ".spec-workflow/specs" ]; then
    find .spec-workflow/specs -type f -name "*.md" -exec grep -l "\.claude/specs" {} \; 2>/dev/null | while read file; do
        sed -i 's|\.claude/specs|.spec-workflow/specs|g' "$file"
        SPEC_INTERNAL_UPDATED=$((SPEC_INTERNAL_UPDATED + 1))
    done
fi
SPEC_INTERNAL_UPDATED=$(find .spec-workflow/specs -type f -name "*.md" -exec grep -l "\.spec-workflow/specs" {} \; 2>/dev/null | wc -l)
echo "✅ Updated $SPEC_INTERNAL_UPDATED spec internal files"
echo ""

# Update .spec-workflow/steering if exists
STEERING_UPDATED=0
if [ -d ".spec-workflow/steering" ]; then
    find .spec-workflow/steering -type f -name "*.md" -exec grep -l "\.claude/specs" {} \; 2>/dev/null | while read file; do
        sed -i 's|\.claude/specs|.spec-workflow/specs|g' "$file"
        STEERING_UPDATED=$((STEERING_UPDATED + 1))
    done
fi
STEERING_UPDATED=$(find .spec-workflow/steering -type f -name "*.md" -exec grep -l "\.spec-workflow/specs" {} \; 2>/dev/null | wc -l)
if [ "$STEERING_UPDATED" -gt 0 ]; then
    echo "✅ Updated $STEERING_UPDATED steering files"
    echo ""
fi

# Verification
echo "=========================================="
echo "Verification"
echo "=========================================="

REMAINING=$(grep -r "\.claude/specs" /mnt/c/Users/jnpi/documents/finlab \
    --include="*.py" --include="*.sh" --include="*.md" --include="*.yaml" \
    --exclude-dir=".claude/specs.backup*" --exclude-dir=".claude.backup*" \
    --exclude-dir=".claude/specs" --exclude-dir="node_modules" --exclude-dir=".git" \
    -l 2>/dev/null | grep -v "DEPRECATED.md" | grep -v "update_spec_paths.sh" | wc -l)

if [ "$REMAINING" -eq 0 ]; then
    echo "✅ All references updated successfully!"
    echo "   No remaining .claude/specs references found"
else
    echo "⚠️  Still found $REMAINING files with .claude/specs references"
    echo "   (excluding deprecated directory and backups)"
    echo ""
    echo "Files still containing old paths:"
    grep -r "\.claude/specs" /mnt/c/Users/jnpi/documents/finlab \
        --include="*.py" --include="*.sh" --include="*.md" --include="*.yaml" \
        --exclude-dir=".claude/specs.backup*" --exclude-dir=".claude.backup*" \
        --exclude-dir=".claude/specs" --exclude-dir="node_modules" --exclude-dir=".git" \
        -l 2>/dev/null | grep -v "DEPRECATED.md" | grep -v "update_spec_paths.sh" | head -10
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Commands:        $COMMANDS_UPDATED files"
echo "Root docs:       $ROOT_UPDATED files"
echo "Docs directory:  $DOCS_UPDATED files"
echo "Source files:    $SRC_UPDATED files"
echo "Test files:      $TEST_UPDATED files"
echo "Scripts:         $SCRIPT_UPDATED files"
echo "Spec internal:   $SPEC_INTERNAL_UPDATED files"
if [ "$STEERING_UPDATED" -gt 0 ]; then
    echo "Steering files:  $STEERING_UPDATED files"
fi
echo "=========================================="
echo ""
echo "Migration Path Updates Complete ✅"
echo ""
