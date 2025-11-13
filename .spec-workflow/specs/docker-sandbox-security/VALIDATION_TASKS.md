# Docker Sandbox Security - Validation Tasks

## Status: Pending Real Environment Validation

These validation tasks address gaps identified in critical review:
- Integration tests written but not executed (Docker unavailable in WSL)
- Production readiness claims need verification
- Real environment behavior needs validation

---

## Validation Task V1: Docker Environment Setup & Verification

**Priority**: Critical
**Estimated Time**: 30 minutes
**Prerequisites**: Access to environment with Docker daemon

### Objectives
1. Verify Docker daemon available and properly configured
2. Ensure python:3.10-slim base image available
3. Validate Docker SDK Python library installed
4. Test basic Docker operations work

### Steps
```bash
# 1. Check Docker daemon
docker info
docker version

# 2. Pull base image
docker pull python:3.10-slim

# 3. Verify Docker SDK
python3 -c "import docker; client = docker.from_env(); print(client.ping())"

# 4. Test basic container creation
docker run --rm python:3.10-slim python -c "print('Hello from Docker')"
```

### Success Criteria
- ✓ Docker daemon responds to commands
- ✓ Base image available (python:3.10-slim)
- ✓ Docker SDK can connect to daemon
- ✓ Test container executes successfully

### Deliverable
- Environment validation report documenting Docker setup

---

## Validation Task V2: Docker Integration Tests Execution

**Priority**: Critical
**Estimated Time**: 1-2 hours
**Prerequisites**: V1 complete, Docker daemon available

### Objectives
Execute all Docker integration tests that were skipped due to Docker unavailability:
1. test_docker_sandbox.py (13 tests) - **CRITICAL**
2. test_autonomous_loop_sandbox.py (3 tests) - **CRITICAL**
3. test_docker_overhead.py (9 tests) - **CRITICAL**

### Steps
```bash
# 1. Execute Docker sandbox integration tests (5 required scenarios)
pytest tests/integration/test_docker_sandbox.py -v -s

# 2. Execute autonomous loop integration tests (10 iterations)
pytest tests/integration/test_autonomous_loop_sandbox.py::TestTenIterationIntegration -v -s

# 3. Execute performance benchmark tests
pytest tests/performance/test_docker_overhead.py -v -s
```

### Expected Results

**test_docker_sandbox.py** (13 tests):
- ✓ Scenario 1: Valid strategy executes in real container
- ✓ Scenario 2: Dangerous code (os.system) rejected before container creation
- ✓ Scenario 3: Memory limit enforced, container killed at 512MB
- ✓ Scenario 4: Network isolation blocks socket operations
- ✓ Scenario 5: Filesystem read-only except /tmp
- ✓ 8 additional cleanup/edge case tests pass

**test_autonomous_loop_sandbox.py** (3 tests):
- ✓ 10 iterations complete with real Docker containers
- ✓ Container cleanup verified (0 orphaned containers)
- ✓ Metrics collected correctly

**test_docker_overhead.py** (9 tests):
- ✓ Container creation <3s average
- ✓ Parallel execution (5 containers) works
- ✓ Cleanup latency <1s average
- ⚠️ Execution overhead: Document actual % (may exceed 5% for single-use containers)

### Known Acceptable Failures
- **Execution overhead >5%**: Acceptable for single-use containers (see Task 13 notes)
  - Mitigation: Container pooling recommended for production
  - Target achievable with container reuse

### Success Criteria
- ✓ At least 20/25 integration tests pass (80% pass rate)
- ✓ All 5 critical security scenarios validated
- ✓ Container cleanup 100% successful
- ✓ No security bypasses discovered

### Deliverable
- Test execution report with screenshots
- Any discovered issues documented with severity
- Performance metrics documented

---

## Validation Task V3: Security Architecture Real Environment Verification

**Priority**: Critical
**Estimated Time**: 1-2 hours
**Prerequisites**: V1 & V2 complete

### Objectives
Validate 5-layer security architecture in real Docker environment:
1. **Layer 1**: AST Validation (SecurityValidator)
2. **Layer 2**: Network Isolation (network_mode: none)
3. **Layer 3**: Filesystem Isolation (read_only + tmpfs)
4. **Layer 4**: Syscall Filtering (seccomp profile)
5. **Layer 5**: Resource Limits (cgroup)

### Steps

#### Layer 1: AST Validation (Already Verified ✓)
- 100% coverage, 53 tests passing
- No additional validation needed

#### Layer 2: Network Isolation
```bash
# Test network isolation with real container
cat > test_network_isolation.py <<'EOF'
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("8.8.8.8", 53))
    print("FAIL: Network accessible")
except Exception as e:
    print(f"PASS: Network blocked - {e}")
EOF

docker run --rm --network none python:3.10-slim python test_network_isolation.py
```

**Expected**: "PASS: Network blocked"

#### Layer 3: Filesystem Isolation
```bash
# Test filesystem isolation
docker run --rm --read-only --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  python:3.10-slim sh -c "
    echo 'test' > /tmp/allowed.txt && cat /tmp/allowed.txt && \
    echo 'test' > /root/blocked.txt 2>&1 || echo 'PASS: Root FS read-only'
  "
```

**Expected**:
- /tmp write succeeds
- /root write fails with "Read-only file system"

#### Layer 4: Seccomp Profile
```bash
# Test seccomp profile blocks dangerous syscalls
docker run --rm --security-opt seccomp=config/seccomp_profile.json \
  python:3.10-slim python -c "
import os
try:
    os.fork()
    print('FAIL: fork() not blocked')
except Exception as e:
    print(f'PASS: fork() blocked - {e}')
"
```

**Expected**: "PASS: fork() blocked - Operation not permitted"

#### Layer 5: Resource Limits
```bash
# Test memory limit enforcement
docker run --rm -m 512m --memory-swap 512m \
  python:3.10-slim python -c "
import sys
try:
    data = bytearray(600 * 1024 * 1024)  # 600MB
    print('FAIL: Memory limit not enforced')
except MemoryError:
    print('PASS: Memory limit enforced')
"
```

**Expected**: Container killed or MemoryError

### Success Criteria
- ✓ Layer 2: Network operations blocked
- ✓ Layer 3: Root filesystem read-only, /tmp writable
- ✓ Layer 4: Dangerous syscalls blocked by seccomp
- ✓ Layer 5: Memory limits enforced
- ✓ All 5 layers working together without conflicts

### Deliverable
- Security validation report with test results
- Screenshots of each layer's verification
- Any discovered bypasses or weaknesses documented

---

## Validation Task V4: Prometheus Metrics Real Export Verification

**Priority**: High
**Estimated Time**: 1 hour
**Prerequisites**: None (can run without Docker)

### Objectives
Verify Prometheus metrics actually export correctly:
1. MetricsCollector exports all 22 metrics
2. Metrics accessible via /metrics endpoint
3. Prometheus format correct
4. All monitoring components integrate properly

### Steps

```bash
# 1. Start metrics collection
python3 <<'EOF'
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.resource_monitor import ResourceMonitor
from src.monitoring.diversity_monitor import DiversityMonitor
from src.monitoring.alert_manager import AlertManager
import time

# Initialize
collector = MetricsCollector()
resource_monitor = ResourceMonitor(metrics_collector=collector)
diversity_monitor = DiversityMonitor(metrics_collector=collector)
alert_manager = AlertManager(metrics_collector=collector)

# Start monitoring
resource_monitor.start_monitoring()
alert_manager.start_monitoring()

# Record some metrics
time.sleep(10)  # Let background threads collect
diversity_monitor.record_diversity(0.5, 10, 20, 5, False)

# Export metrics
print("=== Prometheus Metrics Export ===")
summary = collector.get_summary()
print(f"Resource metrics: {summary.get('resources', {})}")
print(f"Diversity metrics: {summary.get('diversity', {})}")
print(f"Alert metrics: {summary.get('alerts', {})}")

# Cleanup
resource_monitor.stop_monitoring()
alert_manager.stop_monitoring()
EOF

# 2. Check Prometheus format
python3 -c "
from prometheus_client import generate_latest, REGISTRY
print(generate_latest(REGISTRY).decode('utf-8'))
" | grep -E "resource_|diversity_|container_|alert_" | head -20
```

### Success Criteria
- ✓ All 22 metrics defined
- ✓ Metrics exported in Prometheus format
- ✓ HELP and TYPE lines present
- ✓ Values reasonable (not all zeros)
- ✓ Background threads collect data

### Deliverable
- Metrics export validation report
- Sample Prometheus output
- Any missing or incorrect metrics documented

---

## Summary of Validation Tasks

| Task | Priority | Time | Dependencies | Verifies |
|------|----------|------|--------------|----------|
| V1 | Critical | 30m | Docker access | Environment setup |
| V2 | Critical | 1-2h | V1 | Integration tests (25 tests) |
| V3 | Critical | 1-2h | V1, V2 | 5-layer security architecture |
| V4 | High | 1h | None | Prometheus metrics export |

**Total Estimated Time**: 4-6 hours

**Expected Outcomes**:
- ✓ Docker integration tests executed and validated
- ✓ Security architecture verified in real environment
- ✓ Prometheus metrics export confirmed
- ✓ Production readiness claim substantiated with evidence

**Risk Mitigation**:
- If V2-V3 reveal issues, document and fix before production
- Performance overhead >5% acceptable with container pooling
- Any security bypasses must be fixed immediately

---

## Post-Validation Actions

After successful validation:
1. Update STATUS.md with validation results
2. Document any issues found and resolutions
3. Update production readiness assessment
4. Proceed with Tasks 14-15 (documentation/deployment)

If validation fails:
1. Document all failures with severity
2. Create fix tasks for critical issues
3. Re-validate after fixes
4. Delay production deployment until validated
