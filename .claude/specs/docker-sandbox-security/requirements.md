# Requirements Document: Docker Sandbox Security

## Introduction

The system currently executes LLM-generated Python code directly in the host environment, creating critical security vulnerabilities including code injection, resource exhaustion, file system corruption, and potential sandbox escape attacks. This feature implements a **Docker-based isolated execution environment** to safely execute untrusted LLM-generated strategies.

**CRITICAL PRIORITY**: This is a security blocker that must be completed before LLM integration can be activated in production.

**Value Proposition**: Enable safe execution of LLM-generated code with resource limits, network isolation, and filesystem protection, eliminating 100% of host-level security risks from code injection attacks.

## Alignment with Product Vision

This feature is essential for the **LLM Innovation Critical Path** (5-week roadmap to Task 3.5) by:
- **Security foundation**: Enabling safe activation of InnovationEngine in production
- **Resource protection**: Preventing memory leaks and CPU exhaustion from halting iteration loops
- **Production readiness**: Meeting security requirements for 100-generation LLM testing
- **Risk mitigation**: Protecting host system from malicious or buggy generated code

## Requirements

### Requirement 1: Docker Container Isolation

**User Story:** As the autonomous loop system, I want to execute LLM-generated strategies in isolated Docker containers, so that malicious or buggy code cannot affect the host system.

#### Acceptance Criteria

1. WHEN a strategy needs execution THEN the system SHALL create a new Docker container with Python 3.10+ runtime
2. WHEN the container is created THEN it SHALL use network isolation (--network none) to prevent external communication
3. WHEN the container filesystem is mounted THEN it SHALL be read-only except for /tmp and output directories
4. WHEN the container starts THEN it SHALL apply seccomp security profiles to restrict system calls
5. WHEN execution completes or times out THEN the system SHALL automatically destroy the container within 5 seconds

### Requirement 2: Resource Limits

**User Story:** As the system operator, I want strict resource limits on executed strategies, so that resource exhaustion cannot crash the iteration loop or host system.

#### Acceptance Criteria

1. WHEN a container is created THEN it SHALL be limited to 2GB memory (--memory 2g --memory-swap 2g)
2. WHEN a container is created THEN it SHALL be limited to 0.5 CPU cores (--cpus 0.5)
3. WHEN a container runs for >10 minutes THEN the system SHALL terminate it and mark the strategy as failed
4. WHEN memory usage exceeds 1.8GB (90% of limit) THEN the system SHALL log a warning but allow completion
5. WHEN container is terminated THEN all child processes SHALL be cleaned up automatically

### Requirement 3: Secure Code Injection Prevention

**User Story:** As a security-conscious system, I want to validate and sanitize all code before execution, so that code injection attacks cannot compromise the sandbox or host.

#### Acceptance Criteria

1. WHEN strategy code is received THEN the system SHALL validate it is valid Python syntax using ast.parse()
2. WHEN code contains dangerous imports (os.system, subprocess, eval, exec) THEN the system SHALL reject it
3. WHEN code contains file operations outside /tmp THEN the system SHALL reject it
4. WHEN code attempts network operations THEN the container network isolation SHALL block them
5. WHEN validation fails THEN the system SHALL log the rejection reason and return clear error to caller

### Requirement 4: Filesystem Isolation

**User Story:** As the host system, I want the execution environment to have minimal filesystem access, so that strategies cannot corrupt or exfiltrate host data.

#### Acceptance Criteria

1. WHEN container is created THEN the root filesystem SHALL be mounted read-only (--read-only)
2. WHEN container needs scratch space THEN /tmp SHALL be writable with 1GB size limit (--tmpfs /tmp:rw,size=1g)
3. WHEN strategy outputs results THEN they SHALL be written to a bind-mounted output directory
4. WHEN strategy attempts to write outside /tmp or output dir THEN the operation SHALL fail with permission denied
5. WHEN execution completes THEN output directory SHALL contain only metrics.json and logs

### Requirement 5: Monitoring and Observability

**User Story:** As a system operator, I want visibility into sandbox resource usage and security events, so that I can detect attacks or resource issues early.

#### Acceptance Criteria

1. WHEN a container is created THEN the system SHALL log container ID, resource limits, and strategy ID
2. WHEN container is running THEN the system SHALL export Prometheus metrics: container_memory_usage, container_cpu_usage, container_status
3. WHEN container is terminated abnormally THEN the system SHALL log exit code, signal, and resource usage at termination
4. WHEN validation rejects code THEN the system SHALL increment security_rejections_total metric
5. WHEN container cleanup fails THEN the system SHALL log orphaned container ID and alert operators

## Non-Functional Requirements

### Performance
- Container creation latency: <3 seconds per strategy execution
- Container cleanup latency: <5 seconds after execution completes
- Zero performance degradation to iteration loop throughput (<2% overhead)

### Security
- No host filesystem access except designated output directory
- No network access from containers
- No privilege escalation possible from container
- All containers run as non-root user

### Reliability
- 100% container cleanup rate (no orphaned containers)
- Graceful handling of Docker daemon unavailability
- Automatic retry on transient Docker API errors (max 3 attempts)

### Observability
- All security rejections logged with code snippets
- All resource limit violations logged with metrics
- Container lifecycle events exported to Prometheus
- Grafana dashboard showing: active containers, rejection rate, resource usage

## Dependencies

- Docker Engine 24.0+ installed on host
- Python docker SDK: `pip install docker>=7.0.0`
- Prometheus client library: `pip install prometheus_client>=0.19.0`
- Existing execution engine: `artifacts/working/modules/autonomous_loop.py`

## Timeline

- **Total Effort**: 8-12 days
- **Priority**: CRITICAL (blocks LLM integration activation)
- **Week 1 Target**: Complete implementation and validation
- **Dependency Chain**: This → llm-integration-activation → structured-innovation-mvp → Task 3.5

## Success Metrics

1. **Security**: Zero successful code injection attacks in penetration testing
2. **Reliability**: 100% container cleanup rate over 100 consecutive executions
3. **Performance**: <3s container creation, <2% iteration loop overhead
4. **Observability**: All security events and resource metrics visible in Grafana
5. **Production Readiness**: Passes 20-generation LLM test without security incidents

## Out of Scope

- Kubernetes orchestration (Docker-only for MVP)
- GPU resource limits (CPU/memory only)
- Multi-container strategies (single container per execution)
- Persistent container reuse (disposable containers only)
- Windows container support (Linux containers only)
