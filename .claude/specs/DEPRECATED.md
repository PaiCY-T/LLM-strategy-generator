# ⛔ DEPRECATED - DO NOT USE

**This directory is deprecated as of 2025-10-28**

## Migration Complete

All spec files have been migrated to: `.spec-workflow/specs/`

## Why Deprecated?

The old `.claude/specs` location conflicts with the new spec-workflow MCP server structure.
The new location provides:
- Better organization
- MCP server integration
- Approval workflow support
- Session management
- Steering document support

## What to Do?

1. **DO NOT** create new specs in `.claude/specs`
2. **DO** use `.spec-workflow/specs` for all new specs
3. **DO** use spec-workflow MCP tools:
   - `mcp__spec-workflow__spec-status`
   - `mcp__spec-workflow__approvals`
   - `mcp__spec-workflow__spec-workflow-guide`

## Migration Details

- **Migration Date**: 2025-10-28
- **Backup Location**: `.claude/specs.backup.*`
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
