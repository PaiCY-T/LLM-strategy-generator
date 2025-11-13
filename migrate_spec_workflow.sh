#!/bin/bash
# Spec Workflow Migration Script
# Migrate .spec-workflow/specs → .spec-workflow/specs
# Date: 2025-10-28

set -e  # Exit on error

echo "=========================================="
echo "Spec Workflow Migration"
echo "=========================================="
echo "From: .spec-workflow/specs"
echo "To:   .spec-workflow/specs"
echo ""

OLD_DIR=".spec-workflow/specs"
NEW_DIR=".spec-workflow/specs"
BACKUP_DIR=".spec-workflow/specs.backup.$(date +%Y%m%d_%H%M%S)"
DEPRECATED_MARKER=".spec-workflow/specs/DEPRECATED.md"

# Step 1: Backup old directory
echo "[1/7] Creating backup..."
cp -r "$OLD_DIR" "$BACKUP_DIR"
echo "✅ Backup created: $BACKUP_DIR"
echo ""

# Step 2: Analyze directories
echo "[2/7] Analyzing directories..."
OLD_SPECS=$(ls -1 "$OLD_DIR" | grep -v "DEPRECATED" || true)
NEW_SPECS=$(ls -1 "$NEW_DIR" 2>/dev/null || true)

echo "Old specs count: $(echo "$OLD_SPECS" | wc -l)"
echo "New specs count: $(echo "$NEW_SPECS" | wc -l)"
echo ""

# Step 3: Identify duplicates and unique specs
echo "[3/7] Identifying duplicates..."
DUPLICATES=""
UNIQUE_TO_OLD=""

for spec in $OLD_SPECS; do
    if echo "$NEW_SPECS" | grep -q "^${spec}$"; then
        DUPLICATES="${DUPLICATES}${spec}\n"
    else
        UNIQUE_TO_OLD="${UNIQUE_TO_OLD}${spec}\n"
    fi
done

DUPLICATE_COUNT=$(echo -e "$DUPLICATES" | grep -v "^$" | wc -l)
UNIQUE_COUNT=$(echo -e "$UNIQUE_TO_OLD" | grep -v "^$" | wc -l)

echo "Duplicates: $DUPLICATE_COUNT"
echo "Unique to old: $UNIQUE_COUNT"
echo ""

# Step 4: Copy unique specs
echo "[4/7] Copying unique specs to new location..."
COPIED=0

for spec in $(echo -e "$UNIQUE_TO_OLD" | grep -v "^$"); do
    echo "  Copying: $spec"
    cp -r "$OLD_DIR/$spec" "$NEW_DIR/"
    COPIED=$((COPIED + 1))
done

echo "✅ Copied $COPIED unique specs"
echo ""

# Step 5: Handle duplicates
echo "[5/7] Handling duplicate specs..."
for spec in $(echo -e "$DUPLICATES" | grep -v "^$"); do
    # Check if there are differences
    DIFF_COUNT=$(diff -r "$OLD_DIR/$spec" "$NEW_DIR/$spec" 2>/dev/null | wc -l || echo "0")

    if [ "$DIFF_COUNT" -gt 0 ]; then
        echo "  ⚠️  Differences found in: $spec"
        echo "     Copying to: $NEW_DIR/${spec}.merged_$(date +%Y%m%d)"
        cp -r "$OLD_DIR/$spec" "$NEW_DIR/${spec}.merged_$(date +%Y%m%d)"
    else
        echo "  ✅ Identical: $spec (no action needed)"
    fi
done
echo ""

# Step 6: Create deprecation marker
echo "[6/7] Creating deprecation marker..."
cat > "$DEPRECATED_MARKER" << 'EOF'
# ⛔ DEPRECATED - DO NOT USE

**This directory is deprecated as of 2025-10-28**

## Migration Complete

All spec files have been migrated to: `.spec-workflow/specs/`

## Why Deprecated?

The old `.spec-workflow/specs` location conflicts with the new spec-workflow MCP server structure.
The new location provides:
- Better organization
- MCP server integration
- Approval workflow support
- Session management
- Steering document support

## What to Do?

1. **DO NOT** create new specs in `.spec-workflow/specs`
2. **DO** use `.spec-workflow/specs` for all new specs
3. **DO** use spec-workflow MCP tools:
   - `mcp__spec-workflow__spec-status`
   - `mcp__spec-workflow__approvals`
   - `mcp__spec-workflow__spec-workflow-guide`

## Migration Details

- **Migration Date**: 2025-10-28
- **Backup Location**: `.spec-workflow/specs.backup.*`
- **New Location**: `.spec-workflow/specs/`
- **Files Migrated**: See migration log below

## Migrated Specs

All specs have been copied to `.spec-workflow/specs/`:

$(ls -1 "$NEW_DIR" | sed 's/^/- /')

## Backup

Original files are backed up to: `$BACKUP_DIR`

## Cleanup (Future)

This directory will be removed in a future cleanup.
For now, it remains as read-only reference.

**Last Updated**: $(date '+%Y-%m-%d %H:%M:%S')
EOF

echo "✅ Deprecation marker created: $DEPRECATED_MARKER"
echo ""

# Step 7: Verify migration
echo "[7/7] Verifying migration..."
OLD_MD_COUNT=$(find "$OLD_DIR" -type f -name "*.md" -not -path "*/DEPRECATED.md" | wc -l)
NEW_MD_COUNT=$(find "$NEW_DIR" -type f -name "*.md" | wc -l)

echo "Old markdown files: $OLD_MD_COUNT"
echo "New markdown files: $NEW_MD_COUNT"

if [ "$NEW_MD_COUNT" -ge "$OLD_MD_COUNT" ]; then
    echo "✅ Migration verification passed"
else
    echo "⚠️  Warning: New location has fewer files"
fi
echo ""

# Summary
echo "=========================================="
echo "Migration Complete"
echo "=========================================="
echo "✅ Backup:     $BACKUP_DIR"
echo "✅ Deprecated: $DEPRECATED_MARKER"
echo "✅ New specs:  $NEW_DIR"
echo ""
echo "Specs in new location:"
ls -1 "$NEW_DIR" | head -20
echo ""
echo "Next steps:"
echo "1. Review: cat $DEPRECATED_MARKER"
echo "2. Verify: ls -la $NEW_DIR"
echo "3. Update any hardcoded paths in code"
echo ""
echo "=========================================="
