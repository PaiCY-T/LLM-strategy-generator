# Pre-Commit Hook Setup Guide

## Overview

This guide helps developers set up and use the pre-commit hooks for local type checking. The hooks automatically run mypy on staged files before each commit to catch API mismatches early in the development workflow.

**Performance Target**: <5 seconds for typical commits (src/ directory only)

---

## Installation

### 1. Install pre-commit (One-time setup)

```bash
# Option 1: Using pip
pip install pre-commit

# Option 2: Using conda
conda install -c conda-forge pre-commit

# Option 3: Using homebrew (macOS)
brew install pre-commit
```

### 2. Install Git Hooks (One-time per repository)

```bash
# Navigate to project root
cd /path/to/LLM-strategy-generator

# Install the pre-commit hooks
pre-commit install

# Expected output:
# pre-commit installed at .git/hooks/pre-commit
```

### 3. Verify Installation

```bash
# Check pre-commit version
pre-commit --version

# Expected output:
# pre-commit 3.x.x

# Test hook configuration
pre-commit run --all-files --verbose

# This will:
# - Download mypy and dependencies (first run only)
# - Run type checking on src/ directory
# - Report any type errors
```

---

## Daily Usage

### Normal Workflow (Automatic)

Pre-commit hooks run **automatically** when you commit:

```bash
# Stage your changes
git add src/learning/my_module.py

# Commit (hooks run automatically)
git commit -m "Add new feature"

# If type errors are found:
# ❌ mypy type checking (src/ only)...Failed
# - hook id: mypy
# - exit code: 1
#
# src/learning/my_module.py:45: error: ...
#
# Fix the errors, then commit again
```

### Skip Hooks (Emergency Use Only)

```bash
# Skip all hooks (NOT RECOMMENDED)
git commit -m "Emergency fix" --no-verify

# ⚠️ Warning: Only use --no-verify for:
# - Emergency hotfixes
# - Work-in-progress commits on feature branches
# - CI will still catch errors on PR
```

### Manual Hook Execution

```bash
# Run hooks on all files (useful for testing)
pre-commit run --all-files

# Run hooks on specific files
pre-commit run --files src/learning/interfaces.py

# Run only mypy hook
pre-commit run mypy --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

---

## Performance Optimization

### Current Configuration

- **Scope**: Only `src/` directory (not tests, docs, etc.)
- **Target**: <5 seconds for typical commits
- **Caching**: mypy uses `.mypy_cache/` for faster subsequent runs

### Performance Tips

1. **First run is slower** (downloads dependencies)
   - Expect 30-60 seconds for first commit
   - Subsequent commits: <5 seconds

2. **Large commits take longer**
   - Mypy checks entire module graph
   - Consider breaking large refactors into smaller commits

3. **Clean cache if needed**
   ```bash
   # Remove mypy cache (forces fresh check)
   rm -rf .mypy_cache

   # Clear pre-commit cache
   pre-commit clean
   ```

---

## Troubleshooting

### Problem: Hook execution fails with import errors

**Symptom**:
```
ModuleNotFoundError: No module named 'finlab'
```

**Solution**:
```bash
# Ensure project dependencies are installed
pip install -r requirements.txt

# Or install in editable mode
pip install -e .
```

---

### Problem: Hooks don't run automatically

**Symptom**:
Commits succeed without running mypy

**Solution**:
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Verify installation
ls -la .git/hooks/pre-commit
```

---

### Problem: Hook execution is too slow (>10s)

**Symptom**:
Every commit takes >10 seconds

**Solution**:
```bash
# 1. Check if mypy cache exists
ls -la .mypy_cache/

# 2. Verify scope is limited to src/
cat .pre-commit-config.yaml | grep "files:"
# Should show: files: ^src/

# 3. Consider increasing mypy cache size
export MYPY_CACHE_DIR=~/.mypy_cache
```

---

### Problem: Type errors in legacy code block commits

**Symptom**:
```
src/backtest/legacy_module.py:123: error: ...
```

**Solution**:
This should not happen (legacy modules are excluded from strict checks).
If it does:

```bash
# 1. Verify mypy.ini configuration
cat mypy.ini | grep -A5 "src.backtest"

# Should show:
# [mypy-src.backtest.*]
# strict = False
# check_untyped_defs = False

# 2. If configuration is correct but errors persist, report issue
```

---

## Configuration Reference

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
        args:
          - --strict          # Enforce strict type checking
          - --config-file=mypy.ini  # Use project-specific config
          - --show-error-codes      # Show error codes for debugging
        additional_dependencies:
          - types-requests    # Type stubs for requests library
          - types-PyYAML      # Type stubs for PyYAML library
        files: ^src/          # Only check src/ directory (PERFORMANCE)
```

### Key Settings

| Setting | Value | Reason |
|---------|-------|--------|
| `files: ^src/` | Scope to src/ only | Performance: Avoid checking tests, docs, config |
| `pass_filenames: false` | Don't pass filenames | Mypy handles incremental checks internally |
| `always_run: false` | Run only on staged files | Performance: Only check what changed |
| `verbose: true` | Detailed output | Debugging: See what mypy is doing |

---

## Integration with Development Workflow

### Recommended Workflow

1. **Write code** with type hints
2. **Stage changes**: `git add src/learning/my_module.py`
3. **Commit**: `git commit -m "Add feature"`
4. **Hook runs automatically**: Mypy checks staged files
5. **Fix errors if any**: Edit → stage → commit again
6. **Push**: `git push` (CI will run full validation)

### Best Practices

1. **Write type hints as you code** (easier than adding later)
2. **Fix type errors immediately** (don't accumulate tech debt)
3. **Use `--no-verify` sparingly** (only for emergencies)
4. **Run `pre-commit run --all-files` before major PRs** (catch all issues)

---

## CI/CD Integration

Pre-commit hooks provide **fast local feedback**. GitHub Actions CI provides **comprehensive validation**:

| Check | Local (Pre-commit) | CI (GitHub Actions) |
|-------|-------------------|---------------------|
| Scope | `src/` only | Entire codebase |
| Speed | <5s | <2min |
| Runs | On commit | On push/PR |
| Bypass | `--no-verify` | Cannot bypass |

**Strategy**: Local hooks catch 80% of errors, CI catches remaining 20%.

---

## FAQ

### Q: Can I disable hooks temporarily?

**A**: Yes, but not recommended:
```bash
# Disable hooks (NOT RECOMMENDED)
pre-commit uninstall

# Re-enable hooks
pre-commit install
```

### Q: Why does mypy run on all of src/ even if I changed one file?

**A**: Mypy checks the entire module graph to ensure type consistency. This is necessary for catching API mismatches between modules.

### Q: Can I configure different hooks for different branches?

**A**: No, `.pre-commit-config.yaml` is shared across all branches. Use branch-specific CI workflows instead.

### Q: What happens if I commit without installing hooks?

**A**: Commits succeed locally, but CI will catch errors on push/PR. Installing hooks is optional but strongly recommended.

---

## Performance Metrics

### Expected Performance (Local Pre-commit)

| Scenario | Expected Time | Notes |
|----------|--------------|-------|
| First commit (cold cache) | 30-60s | Downloads dependencies |
| Typical commit (warm cache) | <5s | Incremental type checking |
| Large refactor (100+ files) | 10-20s | Full module graph check |
| Clean cache commit | 15-30s | Rebuilds cache |

### Expected Performance (CI)

| Scenario | Expected Time | Notes |
|----------|--------------|-------|
| Full CI pipeline | <2min | Parallel jobs |
| Mypy check only | 20-30s | Entire codebase |
| Pytest suite | 60-90s | All tests |

---

## Support

### Getting Help

1. **Configuration issues**: Check `.pre-commit-config.yaml` and `mypy.ini`
2. **Type errors**: See mypy documentation: https://mypy.readthedocs.io/
3. **Performance issues**: Check cache, scope, and dependencies
4. **Hook failures**: Run `pre-commit run --verbose --all-files` for debugging

### Reporting Issues

When reporting issues, include:
1. Pre-commit version: `pre-commit --version`
2. Mypy version: `mypy --version`
3. Python version: `python --version`
4. Error output: `pre-commit run --verbose --all-files 2>&1 | tee error.log`

---

## References

- **Pre-commit Documentation**: https://pre-commit.com/
- **Mypy Documentation**: https://mypy.readthedocs.io/
- **Project Specification**: `.spec-workflow/specs/api-mismatch-prevention-system/`
- **Design Document**: `DESIGN_IMPROVEMENTS.md Section 5`
