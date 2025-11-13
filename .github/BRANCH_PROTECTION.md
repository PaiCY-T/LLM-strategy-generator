# GitHub Branch Protection Configuration

This document describes the required branch protection settings for the `main` branch to ensure quality gates are enforced for the Architecture Refactoring project.

## Required Branch Protection Rules

Navigate to **Settings → Branches → Branch protection rules → Add rule** for the `main` branch and configure the following:

### 1. Require Status Checks

✅ **Require status checks to pass before merging**

Required status checks (must pass before PR can be merged):
- `type-check` - mypy type checking for all refactored modules
- `unit-tests` - Phase 1-4 unit tests with >95% coverage
- `shadow-mode-tests` - Behavioral equivalence validation (PR only)
- `integration-tests` - Full integration test suite with all phases enabled

✅ **Require branches to be up to date before merging**
- Ensures the PR has the latest changes from `main` before merging

### 2. Require Pull Request Reviews

✅ **Require pull request reviews before merging**
- **Required approving reviews**: 1
- **Dismiss stale pull request approvals when new commits are pushed**: ✅ Enabled
- **Require review from Code Owners**: ✅ Enabled (see CODEOWNERS file)

### 3. Restrict Pushes

✅ **Restrict who can push to matching branches**
- Allow only administrators and code owners to push directly
- All other contributors must use pull requests

### 4. Include Administrators

❌ **Do not allow bypassing the above settings**
- Even administrators must follow the rules (enforces quality for everyone)

### 5. Additional Settings

✅ **Require linear history**
- Prevent merge commits, enforce rebase or squash merges
- Keeps commit history clean and linear

✅ **Require deployments to succeed before merging**
- Optional: Enable if you have staging deployment validation

✅ **Do not allow force pushes**
- Prevents rewriting history on `main` branch

✅ **Do not allow deletions**
- Prevents accidental branch deletion

## Verification

After configuring branch protection, verify the settings:

1. Create a test branch and make a small change
2. Open a pull request to `main`
3. Verify that all required status checks appear and must pass
4. Verify that at least 1 review is required before merging
5. Verify that you cannot merge without all checks passing

## CI/CD Quality Gates

The GitHub Actions workflow (`.github/workflows/architecture-refactoring.yml`) defines 4 parallel jobs that serve as quality gates:

### type-check (5 minutes timeout)
- Runs mypy on all refactored modules
- Validates type hints and catches type errors
- Must complete with 0 errors

### unit-tests (10 minutes timeout)
- Runs Phase 1-4 test suites sequentially
- Enforces >95% code coverage
- Checks cyclomatic complexity with radon
- Must have 100% test pass rate

### shadow-mode-tests (15 minutes timeout, PR only)
- Runs behavioral equivalence validation
- Compares Phase 1/2 vs Phase 3 Strategy Pattern outputs
- Uses `scripts/compare_shadow_outputs.py` with 0.95 threshold
- Must demonstrate >95% equivalence

### integration-tests (20 minutes timeout)
- Runs full learning test suite with all phases enabled
- Validates E2E workflows
- Must have 100% test pass rate

## Performance Target

**Total CI Runtime**: <5 minutes (target)
- Parallel execution of independent jobs
- Optimized mypy caching
- Focused test selection

## Emergency Rollback

If a critical issue is discovered after merge:

1. Set `ENABLE_GENERATION_REFACTORING=false` in environment (immediate rollback)
2. Or set specific phase flag to `false` (e.g., `PHASE3_STRATEGY_PATTERN=false`)
3. Restart service (no code deployment needed)
4. System reverts to previous stable implementation
5. Fix issue in development, re-enable after validation

## Contact

For questions about branch protection configuration:
- See `.github/CODEOWNERS` for module ownership
- Review `.github/workflows/architecture-refactoring.yml` for CI/CD details

---

**Last Updated**: 2025-11-11
**Related**: `.github/CODEOWNERS`, `.github/workflows/architecture-refactoring.yml`
