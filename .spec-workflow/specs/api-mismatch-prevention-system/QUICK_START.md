# Pre-commit Hooks - Quick Start Guide

## 2-Minute Setup

```bash
# 1. Install pre-commit (choose one)
pip install pre-commit              # Using pip
conda install -c conda-forge pre-commit  # Using conda
brew install pre-commit             # Using homebrew (macOS)

# 2. Navigate to project root
cd /path/to/LLM-strategy-generator

# 3. Install git hooks
pre-commit install

# 4. Test configuration
pre-commit run --all-files --verbose
```

**Expected output**:
```
pre-commit installed at .git/hooks/pre-commit
```

---

## Daily Usage

### Normal Workflow (Automatic)

```bash
# Write code with type hints
vim src/learning/my_module.py

# Stage changes
git add src/learning/my_module.py

# Commit (hooks run automatically)
git commit -m "Add new feature"
```

**If type errors found**:
```
❌ mypy type checking (src/ only)...Failed
src/learning/my_module.py:45: error: Incompatible types...
```

**Fix errors and commit again**:
```bash
vim src/learning/my_module.py  # Fix errors
git add src/learning/my_module.py
git commit -m "Add new feature"
✅ mypy type checking (src/ only)...Passed
```

---

## Common Commands

```bash
# Run hooks manually on all files
pre-commit run --all-files

# Run hooks on specific files
pre-commit run --files src/learning/interfaces.py

# Run only mypy hook
pre-commit run mypy --all-files

# Skip hooks (emergency only)
git commit -m "Emergency fix" --no-verify

# Update hooks to latest versions
pre-commit autoupdate

# Uninstall hooks (not recommended)
pre-commit uninstall
```

---

## Performance Expectations

| Scenario | Expected Time |
|----------|--------------|
| First commit (downloads dependencies) | 30-60s |
| Typical commit (warm cache) | <5s |
| Large refactor (100+ files) | 10-20s |

---

## Troubleshooting

### Problem: Hooks don't run
```bash
# Solution: Reinstall hooks
pre-commit uninstall
pre-commit install
```

### Problem: Import errors
```bash
# Solution: Install project dependencies
pip install -r requirements.txt
```

### Problem: Too slow
```bash
# Solution: Check cache and scope
ls -la .mypy_cache/
cat .pre-commit-config.yaml | grep "files:"
```

---

## Need More Help?

See comprehensive guide: `PRE_COMMIT_SETUP.md`

**Includes**:
- Detailed installation instructions
- Troubleshooting guide
- Performance optimization tips
- FAQ section
