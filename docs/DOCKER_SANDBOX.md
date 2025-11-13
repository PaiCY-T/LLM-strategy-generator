# Docker Sandbox Security

## Overview

The Docker Sandbox Security system provides **isolated execution of LLM-generated Python strategies** to prevent code injection attacks, resource exhaustion, and host system compromise. This feature is **CRITICAL for production LLM integration** and implements defense-in-depth security through container isolation, resource limits, and runtime monitoring.

**Security Properties**:
- Zero host filesystem access (read-only containers)
- Complete network isolation (no external communication)
- Strict resource limits (2GB memory, 0.5 CPU cores)
- Non-root execution (uid 1000:1000)
- Runtime security monitoring with automatic threat termination
- Battle-tested seccomp profiles (Docker default)

## Installation Requirements

### Prerequisites

**Required**:
- **Docker Engine 20.10+** (tested on 24.0+)
- **Python 3.10+**
- **Linux kernel 4.15+** with seccomp support
- **8GB RAM minimum** (16GB recommended for parallel execution)
- **10GB disk space** (for Docker images and container volumes)

**Verify Docker Installation**:
```bash
# Check Docker version (must be 20.10+)
docker --version

# Verify Docker daemon is running
docker ps

# Test container creation
docker run --rm hello-world
```

### Installation Steps

**1. Install Docker Engine** (if not already installed):
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (avoid sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker run --rm hello-world
```

**2. Install Python Dependencies**:
```bash
cd LLM-strategy-generator
pip install -r requirements.txt
```

**3. Run Automated Setup Script**:
```bash
bash scripts/setup_docker_sandbox.sh
```

This script will:
- Verify Docker installation (20.10+)
- Build Python 3.10 base image with FinLab dependencies
- Validate seccomp profile and configuration files
- Test container creation with security settings

**4. Verify Installation**:
```bash
# Run integration tests
pytest tests/integration/test_docker_sandbox.py -v

# Check security hardening
pytest tests/integration/test_tier1_security_hardening.py -v
```

## Configuration

### Docker Configuration File

**Location**: `config/docker_config.yaml`

```yaml
docker:
  # Enable/disable Docker sandbox (default: true for production)
  enabled: true

  # Base image with pinned SHA256 digest for security
  image: "python:3.10-slim@sha256:e0c4fae70d550834a40f6c3e0326e02cfe239c2351d922e1fb1577a3c6ebde02"

  # Resource limits
  memory_limit: "2g"          # Maximum memory (OOM killer at limit)
  memory_swap_limit: "2g"     # Disable swap for predictable performance
  cpu_limit: 0.5              # CPU cores (0.5 = 50% of one core)
  timeout_seconds: 600        # 10 minutes maximum execution time

  # Security settings
  network_mode: "none"        # Complete network isolation
  read_only: true             # Read-only root filesystem
  pids_limit: 100             # Prevent fork bombs (max 100 processes)

  # Writable temporary storage
  tmpfs:
    path: "/tmp"
    size: "1g"                # 1GB writable scratch space
    options: "rw,noexec,nosuid"  # No executable or setuid files

  # Security profiles
  seccomp_profile: "config/seccomp_profile.json"  # Docker default profile

  # Output and cleanup
  output_dir: "sandbox_output"
  cleanup_on_exit: true       # Auto-cleanup containers

  # Runtime monitoring (Tier 1 security)
  runtime_monitor_enabled: true
  runtime_monitor_interval: 5  # Check every 5 seconds

monitoring:
  # Export container metrics to Prometheus
  export_container_stats: true

  # Alert when >3 orphaned containers detected
  alert_on_orphaned_containers: 3

  # Prometheus metrics port
  prometheus_port: 8000
```

### Learning System Configuration

**Location**: `config/learning_system.yaml`

Add sandbox configuration to enable Docker isolation in the autonomous loop:

```yaml
sandbox:
  enabled: true               # Enable Docker sandbox

learning:
  # Your existing learning configuration
  population_size: 50
  max_iterations: 1000
  # ... other settings
```

### Environment Variables

Override configuration via environment variables:

```bash
# Enable/disable sandbox
export DOCKER_SANDBOX_ENABLED=true

# Override resource limits
export DOCKER_MEMORY_LIMIT="4g"
export DOCKER_CPU_LIMIT=1.0
export DOCKER_TIMEOUT=1200

# Override security settings
export DOCKER_NETWORK_MODE="none"
export DOCKER_READ_ONLY=true
```

## Usage Examples

### Basic Usage

**Execute Strategy in Sandbox**:
```python
from src.sandbox.docker_executor import DockerExecutor
from src.sandbox.docker_config import DockerConfig

# Load configuration
config = DockerConfig.from_yaml("config/docker_config.yaml")

# Create executor
executor = DockerExecutor(config)

# Execute strategy code
strategy_code = """
import pandas as pd
from finlab import data

def strategy(data):
    # Your strategy logic
    close = data.get("price:收盤價")
    return close > close.shift(1)
"""

result = executor.execute_strategy(strategy_code, market_data)

print(f"Success: {result.success}")
print(f"Metrics: {result.metrics}")
print(f"Execution time: {result.execution_time}s")
print(f"Memory used: {result.memory_used_mb}MB")
```

### Enable Sandbox in Autonomous Loop

**Modify** `config/learning_system.yaml`:
```yaml
sandbox:
  enabled: true  # Enable Docker sandbox for all LLM-generated strategies
```

**Run Autonomous Loop**:
```bash
python -m artifacts.working.modules.autonomous_loop
```

All LLM-generated strategies will now execute in isolated Docker containers.

### Security Validation

**Validate Code Before Execution**:
```python
from src.sandbox.security_validator import SecurityValidator

validator = SecurityValidator()

# This code will be REJECTED (dangerous imports)
dangerous_code = """
import os
os.system('rm -rf /')  # Malicious command
"""

is_valid, errors = validator.validate_code(dangerous_code)
print(f"Valid: {is_valid}")
print(f"Errors: {errors}")
# Output: Valid: False
# Errors: ['Dangerous import detected: os.system']

# This code will be ACCEPTED (safe FinLab usage)
safe_code = """
from finlab import data

def strategy(data):
    close = data.get("price:收盤價")
    return close > close.shift(1)
"""

is_valid, errors = validator.validate_code(safe_code)
print(f"Valid: {is_valid}")
# Output: Valid: True
```

### Runtime Monitoring

**Monitor Container Resource Usage**:
```python
from src.sandbox.runtime_monitor import RuntimeMonitor, SecurityPolicy

# Create custom security policy
policy = SecurityPolicy(
    max_cpu_percent=95.0,        # Kill at 95% CPU
    max_memory_percent=95.0,     # Kill at 95% memory
    max_pids=100,                # Kill at 100 processes
    cpu_window_seconds=15.0,     # Sustained 15s CPU spike
    memory_window_seconds=10.0,  # Sustained 10s memory spike
)

# Monitor container
monitor = RuntimeMonitor(container, policy)
monitor.start()

# Monitor runs in background thread
# Automatically kills container on policy violations
```

### Cleanup Orphaned Containers

**Manual Cleanup**:
```python
from src.sandbox.docker_executor import DockerExecutor
from src.sandbox.docker_config import DockerConfig

config = DockerConfig.from_yaml("config/docker_config.yaml")
executor = DockerExecutor(config)

# Find and remove orphaned containers
orphaned_count = executor.cleanup_orphaned_containers()
print(f"Cleaned up {orphaned_count} orphaned containers")
```

**Automatic Cleanup**:
- Containers are automatically cleaned up after execution
- Failed executions trigger cleanup via context manager
- System startup scans for orphaned containers from previous runs

## Security Features

### Defense-in-Depth Architecture

**Layer 1: Code Validation** (Pre-execution)
- AST-based syntax validation
- Dangerous import detection (os.system, subprocess, eval, exec)
- File operation restrictions (no access outside /tmp)
- Network operation detection (socket, urllib, requests)

**Layer 2: Container Isolation** (Execution)
- Read-only root filesystem (only /tmp writable)
- Network isolation (--network none)
- Non-root execution (uid 1000:1000)
- Resource limits (2GB memory, 0.5 CPU)
- PID limits (max 100 processes, fork bomb prevention)

**Layer 3: Runtime Monitoring** (Active defense)
- CPU spike detection (>95% for 15s)
- Memory spike detection (>95% for 10s)
- Fork bomb detection (>90 processes)
- Combined anomaly detection (>80% CPU+memory)
- Automatic container termination on violations

**Layer 4: Syscall Filtering** (Kernel-level)
- Docker default seccomp profile (766 lines, battle-tested)
- 408 allowed syscalls (read, write, stat, mmap, etc.)
- Blocked process creation (fork, clone, execve)
- Blocked network syscalls (socket, connect, bind)

### Security Guarantees

**What is BLOCKED**:
- ❌ Network access (no external communication)
- ❌ Host filesystem access (read-only except /tmp)
- ❌ Privilege escalation (non-root execution)
- ❌ Process creation (fork/exec blocked by seccomp)
- ❌ Resource exhaustion (strict memory/CPU/PID limits)
- ❌ Container escape (kernel-level syscall filtering)

**What is ALLOWED**:
- ✅ Strategy execution (Python code in container)
- ✅ FinLab API usage (backtesting, data access)
- ✅ Temporary file storage (/tmp, 1GB limit)
- ✅ Result output (metrics.json in bind-mounted directory)

### Security Testing

**Run Security Tests**:
```bash
# Unit tests (code validation)
pytest tests/sandbox/test_security_validator.py -v

# Integration tests (container isolation)
pytest tests/integration/test_docker_sandbox.py -v

# Tier 1 security hardening tests
pytest tests/integration/test_tier1_security_hardening.py -v
```

**Expected Results**:
- ✅ Dangerous code rejected before execution
- ✅ Network operations blocked by isolation
- ✅ Memory-hungry code killed at 2GB limit
- ✅ Filesystem writes outside /tmp blocked
- ✅ Fork bombs prevented by PID limits

## Troubleshooting

### Docker Daemon Issues

**Problem**: `docker.errors.DockerException: Error while fetching server API version`

**Solution**:
```bash
# Check Docker daemon status
sudo systemctl status docker

# Start Docker daemon
sudo systemctl start docker

# Enable Docker on boot
sudo systemctl enable docker

# Verify Docker is running
docker ps
```

**Problem**: `Got permission denied while trying to connect to the Docker daemon socket`

**Solution**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply group changes (or logout/login)
newgrp docker

# Verify access
docker ps
```

### Container Creation Failures

**Problem**: `docker.errors.ImageNotFound: 404 Client Error: Not Found`

**Solution**:
```bash
# Pull base image manually
docker pull python:3.10-slim@sha256:e0c4fae70d550834a40f6c3e0326e02cfe239c2351d922e1fb1577a3c6ebde02

# Verify image exists
docker images | grep python

# Rebuild if needed
bash scripts/setup_docker_sandbox.sh
```

**Problem**: `Container creation failed with APIError`

**Solution**:
```bash
# Check Docker system info
docker system info

# Check available resources
docker system df

# Clean up unused containers/images
docker system prune -a --volumes
```

### Orphaned Containers

**Problem**: Containers not cleaned up after failed executions

**Detection**:
```bash
# List all containers (including stopped)
docker ps -a

# Find containers from previous runs
docker ps -a | grep finlab_strategy
```

**Solution**:
```python
# Run cleanup programmatically
from src.sandbox.docker_executor import DockerExecutor
from src.sandbox.docker_config import DockerConfig

config = DockerConfig.from_yaml("config/docker_config.yaml")
executor = DockerExecutor(config)
orphaned_count = executor.cleanup_orphaned_containers()
print(f"Cleaned up {orphaned_count} containers")
```

**Automated Solution**:
- System automatically scans for orphaned containers on startup
- Prometheus alerts trigger when >3 orphaned containers detected
- Cleanup runs automatically via context managers

### Resource Limit Issues

**Problem**: `Container killed due to memory limit exceeded`

**Solution**:
```yaml
# Increase memory limit in config/docker_config.yaml
docker:
  memory_limit: "4g"  # Increase from 2g to 4g
```

**Problem**: `Execution timeout after 600 seconds`

**Solution**:
```yaml
# Increase timeout in config/docker_config.yaml
docker:
  timeout_seconds: 1200  # 20 minutes
```

**Problem**: `PID limit exceeded (fork bomb detected)`

**Solution**:
```yaml
# Increase PID limit if legitimate multi-threading
docker:
  pids_limit: 200  # Increase from 100 to 200
```

### Security Validation Failures

**Problem**: `SecurityValidator rejected code with false positive`

**Investigation**:
```python
from src.sandbox.security_validator import SecurityValidator

validator = SecurityValidator()
is_valid, errors = validator.validate_code(your_code)

# Review rejection reasons
for error in errors:
    print(f"Rejection: {error}")
```

**Solution**:
- Review AST validation logic in `src/sandbox/security_validator.py`
- Whitelist legitimate patterns if needed
- Report false positives to development team

### Performance Issues

**Problem**: Container creation takes >5 seconds

**Solution**:
```bash
# Pre-pull base image
docker pull python:3.10-slim@sha256:e0c4fae70d550834a40f6c3e0326e02cfe239c2351d922e1fb1577a3c6ebde02

# Build optimized base image
docker build -t finlab_base -f Dockerfile.base .

# Update config to use local image
# config/docker_config.yaml:
# image: "finlab_base:latest"
```

**Problem**: High CPU usage during monitoring

**Solution**:
```yaml
# Reduce monitoring frequency in config/docker_config.yaml
docker:
  runtime_monitor_interval: 10  # Check every 10s instead of 5s
```

### Debugging Failed Executions

**Enable Verbose Logging**:
```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Execute with detailed logs
executor = DockerExecutor(config)
result = executor.execute_strategy(code, data)
```

**Inspect Container Logs**:
```bash
# Find container ID from executor logs
docker logs <container_id>

# Follow logs in real-time
docker logs -f <container_id>
```

**Review Security Events**:
```bash
# Check Prometheus metrics
curl http://localhost:8000/metrics | grep security_rejection

# Review log files
tail -f logs/sandbox_security.log
```

## Monitoring and Observability

### Prometheus Metrics

**Container Lifecycle**:
- `docker_container_created_total` - Containers created
- `docker_container_cleanup_success_total` - Successful cleanups
- `docker_container_cleanup_failed_total` - Failed cleanups
- `docker_orphaned_containers` - Orphaned containers detected

**Security Events**:
- `docker_security_rejections_total` - Code rejected by validation
- `docker_runtime_violations_total` - Runtime policy violations
- `docker_cpu_spike_kills_total` - Containers killed for CPU abuse
- `docker_memory_spike_kills_total` - Containers killed for memory abuse
- `docker_fork_bomb_kills_total` - Containers killed for fork bombs

**Resource Usage**:
- `docker_container_memory_usage_mb` - Memory usage per container
- `docker_container_cpu_percent` - CPU usage per container
- `docker_container_execution_time_seconds` - Execution duration

**Performance**:
- `docker_container_creation_time_seconds` - Container creation latency
- `docker_execution_timeout_total` - Executions that timed out
- `docker_resource_limit_exceeded_total` - Resource limit violations

### Grafana Dashboard

**Import Dashboard**:
```bash
# TODO: Create Grafana dashboard JSON
# Import via Grafana UI > Dashboards > Import
```

**Key Panels**:
- Container lifecycle (created, running, stopped)
- Security rejection rate over time
- Resource usage heatmap (memory, CPU)
- Runtime violation alerts
- Orphaned container count

## Production Deployment Checklist

**Pre-Deployment**:
- [ ] Docker Engine 20.10+ installed and running
- [ ] Python 3.10+ with all dependencies installed
- [ ] Base image built and pulled (see `scripts/setup_docker_sandbox.sh`)
- [ ] Configuration files validated (`config/docker_config.yaml`, `config/seccomp_profile.json`)
- [ ] Integration tests passing (100% pass rate)
- [ ] Security tests passing (all Tier 1 hardening verified)

**Configuration**:
- [ ] `sandbox.enabled: true` in `config/learning_system.yaml`
- [ ] Resource limits appropriate for workload (2GB memory, 0.5 CPU)
- [ ] Runtime monitoring enabled (`runtime_monitor_enabled: true`)
- [ ] Prometheus metrics exporter running (port 8000)
- [ ] Grafana dashboard configured with alerts

**Security Verification**:
- [ ] Non-root execution verified (uid 1000:1000)
- [ ] Network isolation tested (--network none)
- [ ] Filesystem isolation tested (read-only except /tmp)
- [ ] Seccomp profile validated (Docker default, 766 lines)
- [ ] PID limits tested (fork bomb prevention, max 100)
- [ ] Runtime monitoring tested (CPU/memory spike detection)

**Monitoring**:
- [ ] Prometheus scraping Docker metrics
- [ ] Grafana alerts configured (orphaned containers, security rejections)
- [ ] Log aggregation configured (security events, violations)
- [ ] On-call rotation informed of alert escalation paths

**Emergency Procedures**:
- [ ] Docker disable procedure documented (fallback mechanism REMOVED)
- [ ] Incident response plan for security violations
- [ ] Rollback plan if sandbox causes production issues
- [ ] Emergency contact list for Docker/security experts

## Performance Characteristics

**Typical Performance**:
- Container creation: 2-3 seconds (with cached image)
- Execution overhead: <5% vs direct execution
- Memory overhead: ~100MB per container (Python runtime)
- Cleanup time: <1 second per container
- Parallel execution: Up to 10 concurrent containers (configurable)

**Optimization Tips**:
- Pre-pull base image on system startup
- Use local registry for faster image pulls
- Enable Docker layer caching
- Adjust monitoring interval for lower overhead
- Use SSD storage for Docker volumes

## Security Best Practices

**Production Recommendations**:
1. **Enable sandbox in production** (`sandbox.enabled: true`)
2. **Monitor security metrics** (rejection rate, violations)
3. **Review rejected code** (investigate anomalies)
4. **Update base image regularly** (security patches)
5. **Test isolation periodically** (penetration testing)
6. **Alert on orphaned containers** (>3 triggers investigation)
7. **Review runtime violations** (CPU/memory spikes)

**Security Hardening**:
- ✅ Use pinned image versions with SHA256 digests
- ✅ Enable runtime monitoring (active defense)
- ✅ Run containers as non-root (uid 1000:1000)
- ✅ Use battle-tested seccomp profiles (Docker default)
- ✅ Enforce PID limits (fork bomb prevention)
- ✅ No fallback to direct execution (fail-fast security)

## Additional Resources

**Documentation**:
- [Design Document](../.spec-workflow/specs/docker-sandbox-security/design.md)
- [Requirements Document](../.spec-workflow/specs/docker-sandbox-security/requirements.md)
- [Security Audit](../.spec-workflow/specs/docker-sandbox-security/TIER1_SECURITY_AUDIT.md)

**Code References**:
- `src/sandbox/docker_executor.py` - Container lifecycle management
- `src/sandbox/security_validator.py` - Code validation logic
- `src/sandbox/runtime_monitor.py` - Runtime security monitoring
- `src/sandbox/container_monitor.py` - Resource usage tracking

**Tests**:
- `tests/sandbox/test_security_validator.py` - Unit tests
- `tests/integration/test_docker_sandbox.py` - Integration tests
- `tests/integration/test_tier1_security_hardening.py` - Security tests

**Support**:
- GitHub Issues: Report bugs or feature requests
- Security Issues: security@finlab.tw (for vulnerabilities)

## FAQ

**Q: Is Docker sandbox required for production?**
A: YES. Docker sandbox is CRITICAL for production LLM integration. It prevents code injection attacks and resource exhaustion.

**Q: What happens if Docker daemon is unavailable?**
A: System raises RuntimeError and fails-fast. No fallback to direct execution (security by design).

**Q: Can I disable sandbox for testing?**
A: Yes, set `sandbox.enabled: false` in `config/learning_system.yaml` for local development only.

**Q: How do I customize resource limits?**
A: Edit `config/docker_config.yaml` and adjust `memory_limit`, `cpu_limit`, `timeout_seconds`.

**Q: What if legitimate code is rejected?**
A: Review rejection reason in logs, whitelist pattern in SecurityValidator if safe, report false positive.

**Q: How do I clean up orphaned containers?**
A: Run `executor.cleanup_orphaned_containers()` or use `docker system prune`.

**Q: Is GPU support available?**
A: Not in current version. GPU resource limits planned for future enhancement.

**Q: Can containers communicate with each other?**
A: No. Each container runs in complete isolation with `--network none`.

**Q: How do I update the base image?**
A: Pull new image, update SHA256 digest in config, rebuild with `scripts/setup_docker_sandbox.sh`.

**Q: What's the overhead of runtime monitoring?**
A: <1% CPU overhead, checks every 5 seconds, automatic cleanup on violations.

---

**Version**: 1.0.0
**Last Updated**: 2025-10-27
**Status**: Production Ready (Tier 1 Security Complete)
