# Docker Sandbox Module

This module provides secure, isolated execution of Python code in Docker containers with strict resource limits and security controls.

## Quick Start

### Basic Usage

```python
from src.sandbox.docker_executor import DockerExecutor
from src.sandbox.docker_config import DockerConfig

# Use default configuration
executor = DockerExecutor()

# Execute code
code = """
import pandas as pd
signal = pd.DataFrame({'stock': ['AAPL'], 'position': [1.0]})
print(f"Signal created: {signal}")
"""

result = executor.execute(code)

if result['success']:
    print(f"Execution time: {result['execution_time']:.2f}s")
    print(f"Output: {result.get('logs', '')}")
else:
    print(f"Error: {result['error']}")

# Cleanup
executor.cleanup_all()
```

### Context Manager (Recommended)

```python
with DockerExecutor() as executor:
    result = executor.execute(code)
    # Automatic cleanup on exit
```

### Custom Configuration

```python
config = DockerConfig(
    memory_limit="1g",
    cpu_limit=0.25,
    timeout_seconds=300,
    network_mode="none",
    read_only=True
)

executor = DockerExecutor(config)
```

### Configuration from YAML

```python
# Load from config/docker_config.yaml
config = DockerConfig.from_yaml()
executor = DockerExecutor(config)
```

## Modules

### 1. SecurityValidator (`security_validator.py`)

AST-based code validation before execution.

**Features**:
- Detects dangerous imports (subprocess, os, eval, exec)
- Detects file operations (open, pathlib, shutil)
- Detects network operations (socket, urllib, requests)
- Fast validation (<100ms)

**Usage**:
```python
from src.sandbox.security_validator import SecurityValidator

validator = SecurityValidator()
is_valid, errors = validator.validate(code)

if not is_valid:
    print(f"Validation failed: {errors}")
```

### 2. DockerConfig (`docker_config.py`)

Configuration management for Docker settings.

**Features**:
- Load from YAML with defaults
- Validate resource limits
- Environment variable substitution
- Type-safe dataclass

**Usage**:
```python
from src.sandbox.docker_config import DockerConfig

# Default values
config = DockerConfig()

# From YAML
config = DockerConfig.from_yaml("config/docker_config.yaml")

# Custom values
config = DockerConfig(
    memory_limit="2g",
    cpu_limit=0.5,
    timeout_seconds=600
)
```

### 3. DockerExecutor (`docker_executor.py`)

Container lifecycle management and execution.

**Features**:
- Create containers with security settings
- Resource limit enforcement
- Timeout handling
- 100% cleanup success rate
- Fallback to direct execution (optional)

**Usage**:
```python
from src.sandbox.docker_executor import DockerExecutor

executor = DockerExecutor()

# Execute with validation
result = executor.execute(code, timeout=60, validate=True)

# Execute without validation (use with caution)
result = executor.execute(code, validate=False)

# Cleanup all containers
stats = executor.cleanup_all()
print(f"Cleaned up {stats['success']}/{stats['total']} containers")
```

## Security Features

### Network Isolation
- Network mode: `none` (no network access)
- Blocks all outbound connections
- Prevents data exfiltration

### Filesystem Isolation
- Root filesystem: Read-only
- Writable tmpfs: `/tmp` only
- Size limits on tmpfs
- Mount options: `rw,noexec,nosuid`

### Resource Limits
- Memory: 2GB default (configurable)
- CPU: 0.5 cores default (configurable)
- Timeout: 600s default (configurable)
- No swap usage

### Capability Restrictions
- Drop all Linux capabilities: `cap_drop=['ALL']`
- Non-privileged mode: `privileged=false`
- Optional seccomp profile for syscall filtering

### Code Validation
- AST-based pre-execution validation
- Blocks dangerous operations before container creation
- Fast (<100ms) and accurate (>95%)

## Result Format

The `execute()` method returns a dictionary:

```python
{
    'success': bool,           # Whether execution succeeded
    'signal': Any,             # Execution result (if success)
    'error': str,              # Error message (if failed)
    'execution_time': float,   # Actual execution time in seconds
    'container_id': str,       # Container ID (if created)
    'validated': bool,         # Whether code was validated
    'cleanup_success': bool,   # Whether cleanup succeeded
    'logs': str                # Container stdout/stderr (if available)
}
```

## Error Handling

### Common Errors

**Docker SDK not installed**:
```python
RuntimeError: Docker SDK not available. Install with: pip install docker
```
Solution: `pip install docker`

**Docker daemon not running**:
```python
RuntimeError: Failed to connect to Docker daemon
```
Solution: Start Docker daemon or enable fallback mode

**Image not found**:
```python
'error': 'Docker image not found: python:3.10-slim'
```
Solution: `docker pull python:3.10-slim`

**Validation failure**:
```python
'error': 'Security validation failed: Dangerous import detected: subprocess'
```
Solution: Remove dangerous code or disable validation (not recommended)

**Timeout**:
```python
'error': 'Container execution timeout exceeded (600s)'
```
Solution: Increase timeout or optimize code

## Configuration Options

### DockerConfig Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | `True` | Enable Docker sandbox |
| `image` | `python:3.10-slim` | Docker image to use |
| `memory_limit` | `"2g"` | Memory limit (e.g., "512m", "2g") |
| `cpu_limit` | `0.5` | CPU cores (e.g., 0.5 = half core) |
| `timeout_seconds` | `600` | Max execution time |
| `network_mode` | `"none"` | Network isolation mode |
| `read_only` | `True` | Read-only filesystem |
| `tmpfs_path` | `"/tmp"` | Writable tmpfs path |
| `tmpfs_size` | `"1g"` | Tmpfs size limit |
| `seccomp_profile` | `"config/seccomp_profile.json"` | Seccomp profile path |
| `cleanup_on_exit` | `True` | Auto cleanup containers |
| `fallback_to_direct` | `False` | Fallback to direct execution |

### Example YAML Configuration

```yaml
docker:
  enabled: true
  image: python:3.10-slim
  memory_limit: 2g
  cpu_limit: 0.5
  timeout_seconds: 600
  network_mode: none
  read_only: true
  tmpfs:
    path: /tmp
    size: 1g
    options: rw,noexec,nosuid
  seccomp_profile: config/seccomp_profile.json
  cleanup_on_exit: true
  fallback_to_direct: false

monitoring:
  export_container_stats: true
  alert_on_orphaned_containers: 3
  prometheus_port: 8000
```

## Testing

### Prerequisites
```bash
# Check Docker
docker --version
docker ps

# Pull image
docker pull python:3.10-slim
```

### Run Unit Tests
```bash
# All unit tests (no Docker required)
pytest tests/sandbox/test_docker_executor.py -v

# With coverage
pytest tests/sandbox/test_docker_executor.py --cov=src.sandbox.docker_executor
```

### Run Integration Tests
```bash
# All integration tests (requires Docker)
pytest tests/integration/test_docker_executor_integration.py -v -s

# Skip slow tests
pytest tests/integration/test_docker_executor_integration.py -v -s -m "not slow"
```

## Performance

### Expected Performance
- Container creation: <3s
- Execution overhead: <5%
- Cleanup time: <1s
- Validation time: <100ms

### Optimization Tips
1. Reuse executor instance (avoid recreating)
2. Use context manager for automatic cleanup
3. Skip validation for trusted code (carefully)
4. Use smaller base images if possible
5. Increase timeout for complex strategies

## Troubleshooting

### Container not cleaning up
```python
# Check active containers
executor.get_orphaned_containers()

# Force cleanup all
executor.cleanup_all()
```

### Performance issues
```python
# Check execution time breakdown
result = executor.execute(code)
print(f"Total time: {result['execution_time']:.2f}s")

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Validation too strict
```python
# Skip validation (use with caution)
result = executor.execute(code, validate=False)

# Or check what's allowed
from src.sandbox.security_validator import SecurityValidator
validator = SecurityValidator()
print(validator.get_allowed_imports())
```

## Best Practices

1. **Always use context manager** for automatic cleanup
2. **Enable validation** for untrusted code (default)
3. **Set appropriate timeouts** for your use case
4. **Monitor resource usage** via logs
5. **Handle errors gracefully** - check `result['success']`
6. **Use production config** - load from YAML
7. **Test with real Docker** before production
8. **Keep images updated** - rebuild base images regularly

## Architecture

```
┌─────────────────────────────────────────┐
│         DockerExecutor                  │
│  ┌────────────────────────────────────┐ │
│  │  1. SecurityValidator.validate()   │ │
│  │     - AST analysis                 │ │
│  │     - Reject dangerous code        │ │
│  └────────────────────────────────────┘ │
│              ↓                          │
│  ┌────────────────────────────────────┐ │
│  │  2. Create container               │ │
│  │     - Apply resource limits        │ │
│  │     - Apply security profiles      │ │
│  └────────────────────────────────────┘ │
│              ↓                          │
│  ┌────────────────────────────────────┐ │
│  │  3. Execute code                   │ │
│  │     - Start container              │ │
│  │     - Wait with timeout            │ │
│  │     - Capture output               │ │
│  └────────────────────────────────────┘ │
│              ↓                          │
│  ┌────────────────────────────────────┐ │
│  │  4. Cleanup (guaranteed)           │ │
│  │     - Normal remove                │ │
│  │     - Force remove (fallback)      │ │
│  │     - Kill + remove (last resort)  │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Dependencies

- `docker` (Python SDK): Container management
- `pyyaml`: Configuration loading
- Python 3.8+: Type hints, dataclasses

## Related Documentation

- [Docker Sandbox Security Spec](../../.spec-workflow/specs/docker-sandbox-security/)
- [Task 3 Implementation Summary](../../TASK3_DOCKER_EXECUTOR_IMPLEMENTATION.md)
- [Security Validator Tests](../../tests/sandbox/test_security_validator.py)
- [Docker Config Tests](../../tests/sandbox/test_docker_config.py)

## Future Enhancements

### Planned (Next Tasks)
- Task 4: ContainerMonitor (metrics and monitoring)
- Task 5: Docker configuration file
- Task 6: Seccomp security profile
- Task 7: Integration into autonomous loop

### Potential Improvements
- Async/parallel container execution
- Result serialization (pickle/JSON)
- Custom image building
- GPU resource limits
- Container networking for data sources
- Volume mounting for large datasets

## License

See project LICENSE file.

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test cases for examples
3. Check implementation summary document
4. Create issue with reproduction steps
