# Deprecated Features - LLM Strategy Generator

**Date**: 2025-11-27
**Status**: Active deprecation list

## Overview

This document tracks features that have been deprecated and will be removed in future versions. All deprecated features have validated replacements with superior performance.

---

## Full Code Generation Mode (DEPRECATED)

### Status
- **Deprecated**: 2025-11-27
- **Replacement**: JSON mode with Template Library
- **Removal Target**: Version 2.0.0 (3-6 months)

### Why Deprecated

Full code generation mode (where LLM generates complete strategy code) has been superseded by JSON mode for the following reasons:

**Performance Comparison** (Phase 2 validation, 20 iterations each):

| Metric | JSON Mode | Full Code | Advantage |
|--------|-----------|-----------|-----------|
| Success Rate (LEVEL_3) | 100% | 25% | **4x better** |
| Avg Sharpe Ratio | 0.1724 | -0.1547 | **+211%** |
| Avg Total Return | 3.94% | -19.14% | **+23%** |
| Stability (std dev) | 0.31 | 1.52 | **5x more stable** |

**Technical Issues**:
1. ❌ High failure rate (75% weak performers - LEVEL_2)
2. ❌ Unstable code generation (high variance)
3. ❌ LLM weakness in code generation vs parameter tuning
4. ❌ No structural constraints (allows extreme configurations)
5. ❌ Slower execution (no template caching)

### Replacement

**JSON Mode** with **Template Library**:
- ✅ 100% success rate (LEVEL_3)
- ✅ 320x execution speedup (template caching)
- ✅ Pre-validated templates (zero syntax errors)
- ✅ Parameter constraints (prevents extreme configs)
- ✅ LLM focused on strength (parameter tuning)
- ✅ 5x more stable performance

### Configuration Changes

**Before** (Deprecated):
```python
config = UnifiedConfig(
    template_mode=False,  # ❌ DEPRECATED
    use_json_mode=False,  # ❌ DEPRECATED
)
```

**After** (Current Default):
```python
config = UnifiedConfig(
    template_mode=True,   # ✅ Now default
    use_json_mode=True,   # ✅ Now default
)
```

### Migration Path

**Automatic Migration** (No action required):
- New code automatically uses JSON mode (default)
- Existing code continues to work (backward compatible)

**Manual Migration** (For explicit full code users):
```python
# Old code (still works but deprecated)
loop = UnifiedLoop(
    template_mode=False,
    use_json_mode=False,
)

# New code (recommended)
loop = UnifiedLoop(
    template_mode=True,
    use_json_mode=True,
    template_name='Momentum',  # or other validated templates
)
```

### Deprecation Timeline

- **2025-11-27**: JSON mode promoted to default (Phase 3 complete)
- **2025-12 - 2026-02**: Deprecation period (3 months)
  - Full code mode still available via explicit config
  - Warning messages for explicit full code usage
  - Documentation updated to recommend JSON mode
- **2026-03**: Full code mode removal (Version 2.0.0)
  - Full code generation code removed
  - Only JSON mode + Template Library supported

### Impact Assessment

**Affected Components**:
- `src/learning/iteration_executor.py` - LLM code generation logic
- `src/innovation/innovation_engine.py` - Strategy code generation
- `src/innovation/prompt_builder.py` - Full code prompts
- Test files that explicitly use `template_mode=False`

**Estimated Effort**:
- Code cleanup: 2-3 days
- Test updates: 1-2 days
- Documentation: 1 day
- Total: ~1 week

**Risk Level**: **LOW**
- Replacement validated with 4x performance improvement
- Backward compatibility maintained during deprecation
- Clear migration path available

---

## LearningConfig (SUPERSEDED)

### Status
- **Superseded**: 2025-11-27
- **Replacement**: UnifiedConfig
- **Removal Target**: Version 2.0.0 (3-6 months)

### Why Superseded

`LearningConfig` doesn't support new features (template_mode, use_json_mode). `UnifiedConfig` is the superset that supports all features.

### Issue

When converting `UnifiedConfig → LearningConfig`, new parameters are lost:
```python
unified_config = UnifiedConfig(
    template_mode=True,
    use_json_mode=True,
)

learning_config = unified_config.to_learning_config()
# ❌ Lost: template_mode, use_json_mode
```

### Replacement

Use `UnifiedLoop` directly (it uses UnifiedConfig internally):
```python
# Old approach (parameters lost)
config = UnifiedConfig(...)
learning_config = config.to_learning_config()
loop = LearningLoop(config=learning_config)

# New approach (parameters preserved)
loop = UnifiedLoop(
    template_mode=True,
    use_json_mode=True,
    ...
)
```

### Migration Path

**Phase 1** (Current - 3 months):
- UnifiedLoop is recommended for new code
- LearningLoop still works but limited
- Warning: Using LearningLoop directly loses new features

**Phase 2** (3-6 months):
- LearningLoop becomes internal implementation detail
- All external code uses UnifiedLoop
- LearningConfig removed from public API

### Impact Assessment

**Affected Code**:
- Direct usage of `LearningConfig` class
- Direct usage of `LearningLoop` class
- Config conversion: `to_learning_config()` method

**Risk Level**: **LOW**
- UnifiedLoop already wraps LearningLoop internally
- No functional changes, only API simplification
- Clear upgrade path available

---

## Innovation Rate < 100% (PARTIALLY DEPRECATED)

### Status
- **Partially Deprecated**: 2025-11-27
- **Affected**: `innovation_rate < 100%` (hybrid with Factor Graph)
- **Reason**: Factor Graph mode not actively maintained

### Background

`innovation_rate` controls LLM vs Factor Graph split:
- 100% = Pure LLM (using JSON mode + templates)
- 50% = Hybrid (50% LLM, 50% Factor Graph)
- 0% = Pure Factor Graph

### Current Status

**Fully Supported**:
- ✅ `innovation_rate=100%` (Pure LLM with JSON mode)

**Deprecated/Unmaintained**:
- ⚠️ `innovation_rate < 100%` (Factor Graph hybrid)
- Factor Graph code exists but not actively tested
- No recent validation of hybrid mode

### Recommendation

**For Production**: Use `innovation_rate=100%` (Pure LLM)
- Validated with Phase 2 testing
- 100% LEVEL_3 success rate
- Fully supported and maintained

**For Research**: Factor Graph hybrid available but unsupported
- May work but no guarantees
- Not recommended for production
- Consider contributing if you need this feature

---

## Summary

### Actively Deprecated Features

| Feature | Deprecated Date | Replacement | Removal Target |
|---------|----------------|-------------|----------------|
| Full Code Generation | 2025-11-27 | JSON Mode | Version 2.0.0 |
| LearningConfig | 2025-11-27 | UnifiedConfig | Version 2.0.0 |
| Direct LearningLoop Usage | 2025-11-27 | UnifiedLoop | Version 2.0.0 |

### Migration Priority

1. **High Priority**: Switch from full code to JSON mode
   - Reason: 4x performance improvement
   - Effort: Minimal (change config defaults)

2. **Medium Priority**: Use UnifiedLoop instead of LearningLoop
   - Reason: Feature parity and future-proofing
   - Effort: Low (API mostly compatible)

3. **Low Priority**: Avoid innovation_rate < 100%
   - Reason: Unmaintained, not tested
   - Effort: None (default is already 100%)

### Questions?

For migration assistance or deprecation timeline questions, please:
1. Check migration examples above
2. Review Phase 2/3 documentation
3. Open an issue on GitHub (if applicable)

---

**Last Updated**: 2025-11-27
**Next Review**: 2026-02-27 (3 months)
