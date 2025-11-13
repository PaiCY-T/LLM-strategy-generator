# Spec Status: Docker Sandbox Security

**Spec Name**: docker-sandbox-security
**Status**: 🔴 **DEPRECATED** (as of 2025-10-09)
**Progress**: Implementation exists but not used
**Created**: 2025-10-25
**Last Updated**: 2025-10-28

---

> **⚠️ ARCHITECTURAL NOTE: DEPRECATED**
>
> This sandbox feature was deprecated on **2025-10-09** due to critical performance bottlenecks with the multiprocessing `spawn` method on Windows.
>
> **Problem**: Windows multiprocessing caused persistent timeouts (120s+) even for simple operations due to full module re-import overhead with complex pandas calculations on Taiwan stock data (~10M data points).
>
> **Decision**: Skip Phase 3 sandbox validation entirely. The project pivoted to an **AST-only validation model** as the PRIMARY security defense.
>
> **Performance Impact**:
> - Before: 120s+ per iteration (0% success rate due to timeouts)
> - After: 13-26s per iteration (100% success rate)
> - **Improvement: 5-10x faster**
>
> **Current Architecture**: AST validation (`src/validation/validate_code.py`) now serves as the **PRIMARY and ONLY** defense layer, blocking dangerous operations (imports, exec, eval, open, negative shifts).
>
> **Reference**: See "Skip-Sandbox Optimization" section in main `STATUS.md` (lines 21-50)
>
> **Code Status**:
> - ✅ Implementation exists (~2,500 lines in `src/sandbox/`)
> - ❌ Not integrated into `autonomous_loop.py`
> - ❌ Config flag `sandbox.enabled: false` by default
> - Status: **Orphaned technical debt** - preserved for historical reference
>
> **Recommendation**: Do not attempt to re-enable without addressing the Windows multiprocessing performance issue.

---

## Overview

**Original Goal**: Implement secure Docker-based sandbox execution for autonomous strategy backtesting, isolating code execution to prevent system compromise and resource exhaustion.

**Current Reality**: Feature implemented but not used due to platform-specific performance constraints.

---

## Implementation Evidence

### Completed Code (Not Used)

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| SecurityValidator | `src/sandbox/security_validator.py` | 365 | ✅ Implemented |
| DockerConfig | `src/sandbox/docker_config.py` | 329 | ✅ Implemented |
| DockerExecutor | `src/sandbox/docker_executor.py` | 613 | ✅ Implemented |
| ContainerMonitor | `src/sandbox/container_monitor.py` | 619 | ✅ Implemented |
| RuntimeMonitor | `src/sandbox/runtime_monitor.py` | 584 | ✅ Implemented |
| **Total** | | **~2,510** | **Not Integrated** |

### Configuration

```yaml
# config/learning_system.yaml (lines 704+)
sandbox:
  enabled: false  # DEPRECATED - Do not enable
  # Docker sandbox skipped due to Windows performance issues
  # AST validation is now the primary security layer
```

---

## Architectural Decision Record

### Context (2025-10-09)

The autonomous iteration engine was hitting persistent timeouts with Docker sandbox execution on Windows:
- Every iteration timed out at 120+ seconds
- Success rate: 0%
- Caused by multiprocessing "spawn" method overhead
- Full module re-import for each container creation
- Taiwan stock data (~10M points) amplified the problem

### Decision

**Skip Docker sandbox validation entirely**

Rely on AST-only validation as the PRIMARY security defense.

### Consequences

**Positive**:
- ✅ 5-10x performance improvement
- ✅ 100% iteration success rate
- ✅ Enabled continuous learning (validated 125+ iterations)
- ✅ Simpler architecture (fewer moving parts)

**Negative**:
- ⚠️ Single layer of defense (AST validation only)
- ⚠️ Abandoned investment (~2,500 lines of code)
- ⚠️ Cannot execute truly untrusted code
- ⚠️ Limited to AST-detectable threats

**Risk Mitigation**:
- AST validator has 80-90% coverage of dangerous operations
- Generates trusted (but potentially buggy) strategies, not arbitrary user code
- 125 iterations validated with zero security breaches

---

## Original Phase Breakdown (For Reference)

### Phase 1: Core Security Components (Tasks 1-4) - 4/4 ✅ (Not Used)

| Task | Status | File | Notes |
|------|--------|------|-------|
| 1. SecurityValidator | ✅ Implemented | `src/sandbox/security_validator.py` | 365 lines |
| 2. DockerConfig | ✅ Implemented | `src/sandbox/docker_config.py` | 329 lines |
| 3. DockerExecutor | ✅ Implemented | `src/sandbox/docker_executor.py` | 613 lines |
| 4. ContainerMonitor | ✅ Implemented | `src/sandbox/container_monitor.py` | 619 lines |

### Phase 2: Configuration (Tasks 5-6) - 2/2 ✅ (Not Used)

| Task | Status | File | Notes |
|------|--------|------|-------|
| 5. Docker configuration | ✅ Exists | `config/docker_config.yaml` | Not used |
| 6. Seccomp profile | ✅ Exists | `config/seccomp_profile.json` | Not used |

### Phase 3: Integration (Tasks 7-8) - 0/2 ❌ **Never Completed**

| Task | Status | File | Notes |
|------|--------|------|-------|
| 7. Integrate into loop | ❌ Skipped | `autonomous_loop.py` | No Docker code present |
| 8. Fallback mechanism | ❌ Skipped | - | AST-only approach instead |

---

## Alternatives Considered

1. **Linux-only deployment**: Would solve multiprocessing issue but limits platform compatibility
2. **Thread-based isolation**: Insufficient security isolation
3. **Process pool pre-warming**: Doesn't address spawn overhead
4. **Selected: AST-only validation**: Pragmatic trade-off for this use case

---

## Lessons Learned

1. **Platform-specific constraints matter**: Windows multiprocessing "spawn" has significant overhead
2. **Pragmatism over purity**: 5-10x performance gain justified the architectural pivot
3. **Risk-appropriate security**: AST validation sufficient for trusted but potentially buggy code
4. **Document decisions**: This note prevents future attempts to "fix" by re-enabling sandbox

---

## Future Considerations

If Docker sandbox needs to be re-enabled:
1. **Solve the root cause**: Windows multiprocessing performance
2. **Or migrate to Linux**: Use "fork" method for better performance
3. **Or hybrid approach**: Sandbox only high-risk operations
4. **Test thoroughly**: 125+ iteration validation before production

---

**Status Summary**: Implementation complete but deprecated due to insurmountable platform constraints. AST-only validation is the current production architecture.
