# Requirements Document: Docker Sandbox Integration Testing

## Introduction

This specification defines the testing and integration plan for the Docker Sandbox security layer (91% complete, 2,529 lines of code). The Docker Sandbox was recently developed to provide **dual-layer security defense** (AST validation + Container isolation) but remains untested and disabled by default (`sandbox.enabled: false`).

**Purpose**: Validate Docker Sandbox functionality, integrate into autonomous evolution loop, and assess whether to enable by default based on performance metrics.

**Value**: Upgrade from single-layer defense (AST-only) to dual-layer defense (AST + Docker Sandbox), significantly improving security posture while maintaining acceptable performance.

**Timeline**: 2 weeks (10 working days)
**Priority**: HIGH - Critical path to production

## Alignment with Product Vision

This feature directly supports the product vision's emphasis on **security and safety**:

- **7-Layer Validation Framework**: Docker Sandbox represents Layer 2 (Container Isolation) between Layer 1 (AST Validation) and Layer 3 (Execution Monitoring)
- **Production-Ready System**: Current AST-only approach is acceptable for MVP but requires hardening for production with untrusted strategy generation
- **LLM Integration Enablement**: Dual-layer security is prerequisite for confidently enabling LLM-driven innovation (20% innovation rate target)

**Risk Mitigation**: Windows multiprocessing "spawn" overhead was previously identified as a potential blocker. This testing phase will empirically determine if the performance impact is acceptable (<50% overhead target).

## Requirements

### Requirement 1: Basic Docker Sandbox Functionality

**User Story:** As a system administrator, I want Docker containers to start, execute strategies, and stop reliably, so that the sandbox infrastructure is proven stable before integration.

#### Acceptance Criteria

1. WHEN a strategy code is submitted THEN the Docker container SHALL start within 10 seconds
2. WHEN a container is started THEN the system SHALL execute the strategy and collect results successfully
3. WHEN strategy execution completes THEN the container SHALL terminate cleanly within 5 seconds
4. WHEN a container fails THEN the system SHALL log the error and return a meaningful failure message
5. IF multiple strategies are submitted concurrently THEN each SHALL execute in isolated containers without interference

**Performance Target**: Container startup + execution + cleanup < 60 seconds per strategy (including Taiwan stock data load ~10M points)

### Requirement 2: Resource Limits Enforcement

**User Story:** As a security engineer, I want resource limits (CPU, Memory, Disk) enforced at the container level, so that malicious or buggy strategies cannot consume excessive system resources.

#### Acceptance Criteria

1. WHEN a strategy exceeds memory limit (2GB) THEN the container SHALL be terminated with OOMKilled status
2. WHEN a strategy exceeds CPU time limit (300 seconds) THEN the container SHALL be terminated with Timeout status
3. WHEN a strategy attempts excessive disk writes (>1GB) THEN the container SHALL be terminated or restricted
4. WHEN resource limits are enforced THEN the system SHALL log the violation type and return error metadata
5. IF a container is terminated due to resource limits THEN the autonomous loop SHALL skip this strategy and continue

**Validation Method**: Intentionally submit strategies that violate each limit and verify correct termination behavior.

### Requirement 3: Seccomp Security Profile

**User Story:** As a security engineer, I want dangerous system calls blocked at the kernel level, so that strategies cannot perform file I/O, network access, or process manipulation outside the container.

#### Acceptance Criteria

1. WHEN a strategy attempts file I/O (open, read, write) to host filesystem THEN the syscall SHALL be blocked with EPERM
2. WHEN a strategy attempts network access (socket, connect) THEN the syscall SHALL be blocked with EPERM
3. WHEN a strategy attempts process manipulation (fork, exec, kill) THEN the syscall SHALL be blocked with EPERM
4. WHEN a strategy attempts time manipulation (settimeofday, clock_settime) THEN the syscall SHALL be blocked with EPERM
5. IF a blocked syscall is attempted THEN the system SHALL log the violation with strategy ID and syscall name

**Security Test Cases**: Submit strategies that attempt each blocked operation and verify Seccomp enforcement.

### Requirement 4: Integration with Autonomous Loop

**User Story:** As a developer, I want Docker Sandbox integrated into `autonomous_loop.py` with automatic fallback to AST-only execution, so that the system gracefully handles sandbox failures without halting evolution.

#### Acceptance Criteria

1. WHEN `sandbox.enabled: true` in config THEN the autonomous loop SHALL route strategy execution through Docker Sandbox
2. WHEN a sandbox execution fails (timeout, error) THEN the system SHALL automatically fallback to AST-only execution
3. WHEN fallback occurs THEN the system SHALL log a WARNING with failure reason and continue the iteration
4. IF sandbox is disabled (`sandbox.enabled: false`) THEN the system SHALL use AST-only execution (current behavior)
5. WHEN an iteration completes THEN the system SHALL record whether sandbox or fallback was used in iteration metadata

**Backward Compatibility**: All existing tests must pass with `sandbox.enabled: false` (no regressions).

### Requirement 5: Performance Benchmarking

**User Story:** As a product owner, I want empirical performance data comparing Docker Sandbox vs. AST-only execution, so that I can make an informed decision on whether to enable by default.

#### Acceptance Criteria

1. WHEN running 5-iteration smoke test THEN the system SHALL record per-iteration timing with sandbox enabled
2. WHEN running 20-iteration validation test THEN the system SHALL record average iteration time and overhead percentage
3. WHEN performance data is collected THEN the system SHALL calculate: `overhead = (sandbox_time - ast_only_time) / ast_only_time * 100%`
4. IF overhead < 50% THEN recommend enabling sandbox by default
5. IF overhead >= 100% THEN document as optional feature with manual enable instructions

**Metrics to Track**:
- Iteration time (AST-only baseline): 13-26 seconds (from STATUS.md)
- Iteration time (Docker Sandbox): [To be measured]
- Overhead percentage: [To be calculated]
- Success rate (both modes): Target 100%

### Requirement 6: Decision Framework

**User Story:** As a product owner, I want a clear decision framework based on test results, so that the team knows whether to enable Docker Sandbox by default or keep it as an optional feature.

#### Acceptance Criteria

1. WHEN all functional tests pass (Req 1-3) AND overhead < 50% THEN recommend enabling by default (`sandbox.enabled: true`)
2. WHEN all functional tests pass AND overhead >= 50% AND < 100% THEN recommend optional feature with documentation
3. WHEN any functional test fails OR overhead >= 100% THEN document as experimental with known issues
4. WHEN decision is made THEN update `config/learning_system.yaml` and document rationale in STATUS.md
5. IF sandbox is not enabled by default THEN provide clear activation instructions in documentation

**Decision Matrix**:
```
| Functional Tests | Overhead | Decision |
|-----------------|----------|----------|
| ✅ PASS | < 50% | ✅ Enable by default |
| ✅ PASS | 50-100% | ⚠️ Optional feature |
| ✅ PASS | > 100% | ❌ Document only |
| ❌ FAIL | Any | ❌ Do not use |
```

## Non-Functional Requirements

### Code Architecture and Modularity
- **Single Responsibility**: Separate test modules for functional, integration, and performance tests
- **Reusable Test Utilities**: Shared fixtures for container lifecycle management
- **Clear Test Organization**: Group tests by phase (Basic → Integration → Performance → Decision)
- **Minimal Changes to Core**: Integration should require <50 lines of changes to `autonomous_loop.py`

### Performance
- **Container Startup**: < 10 seconds per container
- **Strategy Execution**: Comparable to AST-only (target: <50% overhead)
- **Total Iteration Time**: < 60 seconds (vs 13-26 seconds AST-only baseline)
- **Concurrent Execution**: Support 5 parallel containers without degradation

### Security
- **Defense in Depth**: AST validation must remain enabled (dual-layer, not replacement)
- **Isolation Guarantee**: Strategies cannot access host filesystem, network, or other containers
- **Audit Logging**: All security violations logged with strategy ID, timestamp, and violation type
- **Seccomp Enforcement**: 100% of dangerous syscalls blocked (verified by test suite)

### Reliability
- **Graceful Degradation**: Sandbox failures must not halt autonomous loop (fallback to AST-only)
- **Container Cleanup**: All containers must terminate within 10 seconds of completion/timeout
- **Error Recovery**: System must recover from Docker daemon errors, OOM conditions, and timeouts
- **Zero Data Loss**: Strategy execution results must be preserved even on sandbox failure (via fallback)

### Usability
- **Simple Configuration**: Single flag `sandbox.enabled: true/false` to control behavior
- **Clear Logging**: Distinguish sandbox vs. AST-only execution in logs
- **Performance Visibility**: Iteration metadata includes sandbox usage and timing
- **Documentation**: README and troubleshooting guide for common sandbox issues (Docker not running, Windows multiprocessing, resource limits)

### Maintainability
- **Test Coverage**: ≥90% coverage for Docker Sandbox integration code
- **Automated Testing**: All functional and integration tests run in CI/CD
- **Performance Baselines**: Established benchmarks for regression detection
- **Decision Documentation**: Clear rationale documented for enable/disable decision

## Success Criteria

**Phase 1 Success (Basic Functionality)**:
- ✅ All Requirement 1-3 tests pass (Container lifecycle, Resource limits, Seccomp)
- ✅ Zero security violations in positive test cases
- ✅ 100% security violation detection in negative test cases

**Phase 2 Success (Integration)**:
- ✅ Requirement 4 tests pass (Autonomous loop integration with fallback)
- ✅ 5-iteration smoke test completes successfully with sandbox enabled
- ✅ 20-iteration validation test maintains 100% success rate
- ✅ Zero regressions with `sandbox.enabled: false`

**Phase 3 Success (Decision)**:
- ✅ Performance benchmarks collected for both modes
- ✅ Overhead percentage calculated and documented
- ✅ Decision made per Requirement 6 framework
- ✅ Configuration and documentation updated accordingly

**Overall Success**: Docker Sandbox validated as production-ready (either enabled by default or documented as optional feature with clear activation path).

## Out of Scope

**Not in this specification**:
- Docker Sandbox implementation (already complete at 91%, 2,529 lines)
- AST validation improvements (separate concern, current defense)
- Multi-host orchestration (single-machine scope for MVP)
- GPU resource management (CPU/Memory only)
- Windows-specific optimizations (test on Windows first, optimize if needed)

**Future Enhancements** (separate specs if needed):
- Container image caching for faster startup
- Process pool pre-warming (if startup overhead is unacceptable)
- Linux-specific optimizations (fork vs spawn multiprocessing)
- Alternative isolation methods (thread-based, pyodide WASM)

## Dependencies

**Prerequisites**:
- Docker Sandbox implementation complete (91%, Task 1-20 from docker-sandbox-security spec)
- Docker Desktop installed and running on development/test machine
- Autonomous loop baseline established (13-26 seconds per iteration, 100% success rate with AST-only)
- Monitoring system operational (resource tracking, metrics collection)

**Blocks**:
- LLM Integration Activation (Week 3) - Requires dual-layer security confidence before enabling LLM innovation

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Windows multiprocessing overhead >100% | MEDIUM | HIGH | Fallback to AST-only, document as optional |
| Docker daemon crashes/errors | LOW | MEDIUM | Automatic fallback, retry logic |
| Seccomp profile too restrictive | LOW | LOW | Iterative refinement, test real strategies |
| Taiwan stock data load timeout | MEDIUM | HIGH | Increase timeout, optimize data loading |
| Integration breaks existing tests | LOW | HIGH | Backward compatibility requirement, feature flag |

**Critical Risk**: Windows multiprocessing "spawn" overhead was noted in STATUS.md as previously causing 120s+ timeouts. If this recurs, the decision framework (Requirement 6) provides clear guidance to document as optional feature rather than blocking.
