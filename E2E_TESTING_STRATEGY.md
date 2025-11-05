# E2E Testing Strategy: Phased Validation Approach

**Date**: 2025-10-27
**Status**: READY FOR PHASE 0
**Author**: Claude Code (Zen Thinkdeep Analysis)

---

## Executive Summary

This document outlines a **4-phase end-to-end testing strategy** that enables safe validation of the LLM integration and YAML pipeline **BEFORE Docker security issues are resolved**. This approach was designed in response to the observation that "YAML Normalizer was discovered after the first smoke test", demonstrating the value of early integration testing.

### Key Innovation: Phase 0 Dry-Run Mode

Phase 0 uses **dry-run mode** (syntax validation only, no code execution) to safely test:
- LLM API connectivity and YAML generation
- YAML schema validation and normalization
- Code generation from YAML
- AST parsing and import safety checks

**Critical Safety**: Docker disabled + fallback_to_direct disabled = NO EXECUTION

---

## Phase Overview

| Phase | Name | Prerequisites | Iterations | Execution | Cost | Risk |
|-------|------|---------------|------------|-----------|------|------|
| **0** | Pre-Docker Smoke Test | None | 10 | Dry-run only | $0.10 | ZERO |
| **1** | Post-Docker Week 1 Test | Docker Tier 1 fixes | 20 | Full (sandboxed) | $0.20 | LOW |
| **2** | Extended Integration | Phase 1 success | 50 | Full (sandboxed) | $0.50 | LOW |
| **3** | Production Simulation | Phase 2 success | 100 | Full (sandboxed) | $1.00 | LOW |

---

## Phase 0: Pre-Docker Smoke Test

### Objective

Validate LLM integration, YAML pipeline, and code generation **WITHOUT executing any generated code**. This phase can run **TODAY** on any developer laptop safely.

### Configuration

```yaml
# config/test_phase0_smoke.yaml

docker:
  enabled: false
  fallback_to_direct: false  # CRITICAL: No direct execution either

llm:
  enabled: true
  provider: "openrouter"
  model: "google/gemini-2.0-flash-lite"  # Fast, cheap model
  innovation_rate: 0.20  # 20% of iterations use LLM
  max_api_calls: 5  # Cost control: 5 calls × $0.02 = $0.10
  timeout: 30  # 30 seconds per API call

execution:
  mode: "dry_run"  # ONLY validate syntax, NO execution
  validate_ast: true
  validate_imports: true
  validate_schema: true

safety:
  allow_execution: false  # Hard block on execution
  allow_filesystem_write: false
  allow_network: false

test_params:
  max_iterations: 10
  checkpoint_interval: 2
  export_yaml_specs: true  # Save generated YAML for manual inspection
  export_code: true  # Save generated code for manual inspection
  log_level: "DEBUG"
```

### Test Cases (10 Total)

#### TC-P0-01: LLM Connectivity
```python
def test_llm_connectivity():
    """Verify LLM provider connection and authentication."""
    provider = OpenRouterProvider(api_key=os.getenv("OPENROUTER_API_KEY"))

    # Test with simple prompt
    response = provider.generate("Generate a momentum strategy in YAML format")

    assert response is not None, "No response from LLM"
    assert len(response) > 0, "Empty response from LLM"
    assert "metadata" in response.lower(), "Response missing strategy content"
```

**Expected Result**: Connection successful, valid response received
**Success Criteria**: No ConnectionError, response contains YAML-like content

---

#### TC-P0-02: YAML Generation
```python
def test_yaml_generation():
    """Generate 5 YAML specs via LLM and verify format."""
    engine = InnovationEngine(config_phase0)
    generated_yamls = []

    for i in range(5):
        yaml_spec = engine._generate_yaml_innovation(
            iteration=i,
            champion_metrics={"sharpe_ratio": 0.5}
        )
        if yaml_spec:
            generated_yamls.append(yaml_spec)

    success_rate = len(generated_yamls) / 5
    assert success_rate >= 0.80, f"Only {success_rate:.0%} success rate (target: ≥80%)"
```

**Expected Result**: ≥80% of LLM calls return valid YAML
**Success Criteria**: YAML blocks extracted successfully, basic structure present

---

#### TC-P0-03: YAML Schema Validation
```python
def test_yaml_schema_validation():
    """Validate generated YAML against strategy_schema_v1.json."""
    validator = YAMLSchemaValidator(schema_path="schemas/strategy_schema_v1.json")

    # Generate 5 YAML specs
    yamls = generate_test_yamls(count=5)

    valid_count = 0
    errors = []

    for yaml_spec in yamls:
        is_valid, error_msgs = validator.validate(yaml_spec)
        if is_valid:
            valid_count += 1
        else:
            errors.append(error_msgs)

    validation_rate = valid_count / len(yamls)
    assert validation_rate >= 0.70, f"Only {validation_rate:.0%} valid (target: ≥70%)"

    # Check error quality
    if errors:
        assert all("field" in str(e) for e in errors), "Error messages lack field paths"
```

**Expected Result**: ≥70% pass schema validation (accounting for LLM variability)
**Success Criteria**: Validation errors are clear and actionable

---

#### TC-P0-04: YAML Normalization
```python
def test_yaml_normalization():
    """Verify uppercase indicator names are normalized."""
    normalizer = YAMLNormalizer()

    # Test cases with uppercase names
    test_cases = [
        ("SMA_Fast", "sma_fast"),
        ("RSI_14", "rsi_14"),
        ("MACD_Signal", "macd_signal"),
        ("BB_Upper", "bb_upper"),
        ("ROE_Rank", "roe_rank"),
    ]

    for input_name, expected_output in test_cases:
        yaml_with_uppercase = create_yaml_with_indicator(input_name)
        normalized = normalizer.normalize(yaml_with_uppercase)

        assert expected_output in normalized, \
            f"Failed to normalize '{input_name}' → '{expected_output}'"
```

**Expected Result**: 100% normalization success
**Success Criteria**: No validation failures due to naming conventions

---

#### TC-P0-05: Code Generation
```python
def test_code_generation():
    """Generate Python code from validated YAML specs."""
    generator = YAMLToCodeGenerator(template_path="src/generators/yaml_to_code_template.py")

    # Load valid YAML specs
    valid_yamls = load_valid_yaml_specs(count=5)

    generation_times = []
    generated_codes = []

    for yaml_spec in valid_yamls:
        start = time.perf_counter()
        code = generator.generate(yaml_spec)
        elapsed = time.perf_counter() - start

        generation_times.append(elapsed)
        generated_codes.append(code)

    # Verify all generated successfully
    assert len(generated_codes) == 5, "Not all YAML specs generated code"

    # Verify performance
    avg_time = sum(generation_times) / len(generation_times)
    assert avg_time < 0.200, f"Avg generation time {avg_time:.3f}s (target: <200ms)"
```

**Expected Result**: 100% of valid YAML produces code in <200ms
**Success Criteria**: Code generation fast and reliable

---

#### TC-P0-06: AST Validation
```python
def test_ast_validation():
    """Parse generated code with ast.parse() to verify syntax."""
    codes = load_generated_codes(count=5)

    syntax_errors = []

    for i, code in enumerate(codes):
        try:
            tree = ast.parse(code)
            assert tree is not None, f"Code {i}: AST tree is None"
        except SyntaxError as e:
            syntax_errors.append((i, str(e)))

    assert len(syntax_errors) == 0, \
        f"Found {len(syntax_errors)} syntax errors: {syntax_errors}"
```

**Expected Result**: 100% syntax correctness
**Success Criteria**: Zero SyntaxError exceptions

---

#### TC-P0-07: Import Safety Check
```python
def test_import_safety():
    """Scan generated code for dangerous imports."""
    validator = SecurityValidator()
    codes = load_generated_codes(count=5)

    dangerous_imports = []

    for i, code in enumerate(codes):
        tree = ast.parse(code)
        violations = validator._check_dangerous_imports(tree)

        if violations:
            dangerous_imports.append((i, violations))

    assert len(dangerous_imports) == 0, \
        f"Found dangerous imports: {dangerous_imports}"
```

**Expected Result**: Zero dangerous imports (os, subprocess, eval, exec)
**Success Criteria**: SecurityValidator passes all generated code

---

#### TC-P0-08: Fallback Mechanism
```python
def test_fallback_mechanism():
    """Mock LLM timeout and verify graceful fallback."""
    engine = InnovationEngine(config_phase0)

    # Mock timeout
    with patch.object(engine.llm_provider, 'generate', side_effect=TimeoutError):
        result = engine.run_iteration(iteration=1)

    # Should fall back to Factor Graph mutation
    assert result["innovation_type"] == "factor_graph", \
        "Should fall back to Factor Graph on LLM timeout"
    assert result["status"] == "success", "Fallback should succeed"
```

**Expected Result**: Falls back to Factor Graph mutation without crash
**Success Criteria**: No exception, innovation continues

---

#### TC-P0-09: YAML Retry Logic
```python
def test_yaml_retry_logic():
    """Mock invalid YAML response and verify retry."""
    engine = InnovationEngine(config_phase0)

    # Mock responses: invalid, invalid, valid
    mock_responses = [
        "This is not YAML",  # Retry 1
        "metadata: missing sections",  # Retry 2
        create_valid_yaml_spec(),  # Success
    ]

    with patch.object(engine.llm_provider, 'generate', side_effect=mock_responses):
        result = engine._generate_yaml_innovation(iteration=1)

    assert result is not None, "Should eventually succeed after retries"
    assert result["retry_count"] <= 3, "Should succeed within 3 retries"
```

**Expected Result**: Retry up to 3 times with improved prompts
**Success Criteria**: Eventually succeeds or fails gracefully

---

#### TC-P0-10: End-to-End Flow
```python
def test_end_to_end_flow():
    """Run full 10-iteration loop in dry-run mode."""
    engine = InnovationEngine(config_phase0)

    results = engine.run(max_iterations=10)

    # Verify completion
    assert results["iterations_completed"] == 10, "Should complete 10 iterations"

    # Verify no execution
    assert results["strategies_executed"] == 0, "Dry-run: NO execution"

    # Verify metrics
    assert results["syntax_errors"] == 0, "All code syntactically valid"
    assert results["yaml_validation_rate"] >= 0.70, "≥70% YAML valid"

    # Verify exports
    assert os.path.exists("artifacts/phase0_yaml_specs.jsonl"), "YAML specs exported"
    assert os.path.exists("artifacts/phase0_generated_code.jsonl"), "Code exported"
```

**Expected Result**: 10 iterations complete without crashes
**Success Criteria**: All metrics healthy, no execution occurred

---

### Success Criteria Summary

- ✅ **10/10 test cases pass**
- ✅ **Zero code execution** (dry-run mode only)
- ✅ **YAML validation ≥70%** success rate
- ✅ **Code generation 100%** syntax correctness
- ✅ **Total test time <5 minutes**
- ✅ **Cost <$0.10**

### Safety Guarantees

1. **Docker disabled** → No container execution
2. **fallback_to_direct disabled** → No direct Python execution
3. **execution.mode = "dry_run"** → Only AST parsing
4. **No filesystem writes** outside test directory
5. **No network access** from generated code
6. **Can run on developer laptop** safely

### Phase 0 Implementation

```python
# tests/integration/test_phase0_smoke.py

import pytest
import os
from src.innovation.innovation_engine import InnovationEngine
from src.innovation.llm_providers import OpenRouterProvider
from src.generators.yaml_schema_validator import YAMLSchemaValidator
from src.generators.yaml_to_code_generator import YAMLToCodeGenerator

@pytest.fixture
def phase0_config():
    return {
        "docker": {
            "enabled": False,
            "fallback_to_direct": False
        },
        "llm": {
            "enabled": True,
            "provider": "openrouter",
            "model": "google/gemini-2.0-flash-lite",
            "innovation_rate": 0.20,
            "max_api_calls": 5,
            "timeout": 30
        },
        "execution": {
            "mode": "dry_run",
            "validate_ast": True,
            "validate_imports": True
        },
        "test_params": {
            "max_iterations": 10,
            "checkpoint_interval": 2,
            "export_yaml_specs": True,
            "export_code": True
        }
    }

def test_phase0_dry_run_smoke(phase0_config):
    """Phase 0: Pre-Docker smoke test with dry-run mode."""
    engine = InnovationEngine(phase0_config)
    results = engine.run(max_iterations=10)

    # Core assertions
    assert results["iterations_completed"] == 10
    assert results["strategies_executed"] == 0  # Dry-run
    assert results["syntax_errors"] == 0
    assert results["yaml_validation_rate"] >= 0.70

    # Safety assertions
    assert results["container_launches"] == 0
    assert results["direct_executions"] == 0

    print("\n✅ Phase 0 Complete:")
    print(f"   YAML Validation: {results['yaml_validation_rate']:.0%}")
    print(f"   Code Generation: {results['code_generation_rate']:.0%}")
    print(f"   Total Cost: ${results['llm_cost']:.2f}")
```

### Running Phase 0

```bash
# 1. Set environment variables
export OPENROUTER_API_KEY="your_key_here"

# 2. Run Phase 0 tests
python3 -m pytest tests/integration/test_phase0_smoke.py -v

# 3. Review generated artifacts
cat artifacts/phase0_yaml_specs.jsonl | jq .
cat artifacts/phase0_generated_code.jsonl | jq .

# 4. Check metrics
cat artifacts/phase0_metrics.json | jq .
```

**Expected Output:**
```
tests/integration/test_phase0_smoke.py::test_phase0_dry_run_smoke PASSED

✅ Phase 0 Complete:
   YAML Validation: 80%
   Code Generation: 100%
   Total Cost: $0.08
```

---

## Phase 1: Post-Docker Week 1 Test

### Prerequisites

**MUST complete before Phase 1:**

From Docker Security Tier 1 fixes (see COMPREHENSIVE_SPEC_REVIEW_REPORT.md):

1. ✅ Remove `fallback_to_direct` option entirely (not just set to false)
2. ✅ Add runtime monitoring IN ADDITION to static validation
3. ✅ Run containers as non-root (`--user 1000:1000`)
4. ✅ Use battle-tested seccomp profile (not custom)
5. ✅ Add PID limits (`--pids-limit 100`)
6. ✅ Pin Docker version in requirements

**Estimated Time**: 17 hours (Week 1 sprint)

### Objective

Validate **full execution pipeline** with Docker sandbox, testing container isolation, resource limits, and security controls.

### Configuration

```yaml
# config/test_phase1_docker.yaml

docker:
  enabled: true
  image: "finlab-sandbox:v1-secure"

  security:
    user: "1000:1000"  # Non-root
    network: "none"
    read_only: true
    seccomp_profile: "config/seccomp_profile.json"  # Battle-tested profile
    pids_limit: 100
    cap_drop: ["ALL"]
    no_new_privileges: true

  resources:
    memory: "2g"
    cpus: "0.5"
    timeout: 600  # 10 minutes

  monitoring:
    enabled: true
    export_metrics: true

llm:
  enabled: true
  provider: "openrouter"
  model: "google/gemini-2.0-flash-lite"
  innovation_rate: 0.20
  max_api_calls: 10  # 20 iterations × 20% = 4 expected, use 10 for safety

execution:
  mode: "full"  # Real execution in Docker
  validate_results: true
  timeout_per_strategy: 300  # 5 minutes

test_params:
  max_iterations: 20
  checkpoint_interval: 5
```

### Test Cases (12 Total)

#### TC-P1-01: Docker Container Launch
```python
def test_docker_container_launch():
    """Verify container starts with correct security settings."""
    executor = DockerExecutor(config_phase1)
    container_id = executor.start_container()

    # Inspect container
    inspect = executor.client.api.inspect_container(container_id)

    # Verify user
    assert inspect["Config"]["User"] == "1000:1000", "Container not running as non-root"

    # Verify network
    assert inspect["HostConfig"]["NetworkMode"] == "none", "Network not disabled"

    # Verify read-only
    assert inspect["HostConfig"]["ReadonlyRootfs"] == True, "Filesystem not read-only"

    # Verify seccomp
    assert "seccomp" in inspect["HostConfig"]["SecurityOpt"], "Seccomp not enabled"

    # Cleanup
    executor.stop_container(container_id)
```

**Expected Result**: Container launches with all security settings
**Success Criteria**: `docker inspect` confirms user=1000, network=none, read-only=true

---

#### TC-P1-02: Container Isolation
```python
def test_container_isolation():
    """Verify network access is blocked."""
    code = """
import requests
result = requests.get('https://google.com')
    """

    executor = DockerExecutor(config_phase1)
    result = executor.execute(code, timeout=30)

    # Should fail with network error
    assert result["status"] == "error", "Network request should fail"
    assert "network" in result["error"].lower() or "connection" in result["error"].lower()
```

**Expected Result**: Network requests fail (network=none)
**Success Criteria**: Connection refused, no external access

---

#### TC-P1-03: Filesystem Read-Only
```python
def test_filesystem_readonly():
    """Verify filesystem writes are blocked."""
    code = """
with open('/tmp/test.txt', 'w') as f:
    f.write('test')
    """

    executor = DockerExecutor(config_phase1)
    result = executor.execute(code, timeout=30)

    # Should fail with permission error
    assert result["status"] == "error"
    assert "permission" in result["error"].lower() or "readonly" in result["error"].lower()
```

**Expected Result**: Write operations fail (read-only filesystem)
**Success Criteria**: PermissionError raised, container remains healthy

---

#### TC-P1-04: Resource Limits
```python
def test_resource_limits():
    """Monitor memory/CPU usage during execution."""
    code = """
import numpy as np
# Allocate 1GB of memory
data = np.random.rand(125_000_000)  # 1GB float64
    """

    executor = DockerExecutor(config_phase1)

    # Start monitoring
    monitor = ResourceMonitor(executor.container_id)

    result = executor.execute(code, timeout=30)
    stats = monitor.get_stats()

    # Verify limits enforced
    assert stats["memory_max_mb"] <= 2048, f"Memory exceeded limit: {stats['memory_max_mb']}MB"
    assert stats["cpu_percent"] <= 55, f"CPU exceeded limit: {stats['cpu_percent']}%"  # 0.5 cores = 50%

    # Verify no OOM kill
    assert result["status"] != "oom_killed", "OOMKiller triggered unexpectedly"
```

**Expected Result**: Memory <2GB, CPU <0.5 cores
**Success Criteria**: Limits enforced, no OOMKiller

---

#### TC-P1-05: Timeout Enforcement
```python
def test_timeout_enforcement():
    """Verify container killed after timeout."""
    code = """
import time
time.sleep(1000)  # Sleep for 16+ minutes
    """

    executor = DockerExecutor(config_phase1)
    start = time.time()

    result = executor.execute(code, timeout=600)  # 10 minute timeout
    elapsed = time.time() - start

    # Should timeout around 10 minutes
    assert result["status"] == "timeout", "Should timeout"
    assert 590 <= elapsed <= 620, f"Timeout inaccurate: {elapsed}s"

    # Verify cleanup
    assert not executor.is_container_running(), "Container not stopped"
```

**Expected Result**: Container killed after 10 minutes
**Success Criteria**: Timeout enforced, resources cleaned up

---

#### TC-P1-06: Seccomp Profile
```python
def test_seccomp_profile():
    """Verify syscall filtering is active."""
    executor = DockerExecutor(config_phase1)
    container_id = executor.start_container()

    # Check logs for seccomp
    logs = executor.client.logs(container_id, stderr=True)
    logs_str = logs.decode('utf-8')

    # Should see seccomp enabled message
    # (This is container-dependent, may need adjustment)

    # Alternative: Check via inspect
    inspect = executor.client.api.inspect_container(container_id)
    security_opts = inspect["HostConfig"]["SecurityOpt"]

    assert any("seccomp" in opt for opt in security_opts), \
        "Seccomp profile not loaded"

    executor.stop_container(container_id)
```

**Expected Result**: Seccomp profile loaded
**Success Criteria**: Container logs or inspect show seccomp enabled

---

#### TC-P1-07: PID Bomb Protection
```python
def test_pid_bomb_protection():
    """Verify PID limit blocks fork bombs."""
    code = """
import os
for i in range(200):  # Try to create 200 processes (limit is 100)
    os.fork()
    """

    executor = DockerExecutor(config_phase1)
    result = executor.execute(code, timeout=30)

    # Should fail when hitting PID limit
    assert result["status"] == "error"
    # PIDs limited, cannot fork more

    # Verify container still responsive
    assert executor.is_container_running(), "Container should still be running"
```

**Expected Result**: Fork blocked at 100 PIDs
**Success Criteria**: PID limit enforced, container stable

---

#### TC-P1-08: LLM Innovation in Docker
```python
def test_llm_innovation_in_docker():
    """Generate YAML → code → execute in Docker (full pipeline)."""
    engine = InnovationEngine(config_phase1)

    # Run 1 iteration with LLM innovation
    result = engine.run_iteration(
        iteration=1,
        force_innovation=True,  # Force LLM use
        innovation_type="yaml"
    )

    # Verify full pipeline
    assert result["innovation_type"] == "yaml", "Should use YAML innovation"
    assert result["yaml_validated"] == True, "YAML should validate"
    assert result["code_generated"] == True, "Code should generate"
    assert result["execution_status"] == "success", "Strategy should execute"
    assert "sharpe_ratio" in result["metrics"], "Metrics should be calculated"
```

**Expected Result**: Full pipeline succeeds (YAML → code → Docker → metrics)
**Success Criteria**: Strategy executes successfully, metrics calculated

---

#### TC-P1-09: Runtime Monitoring
```python
def test_runtime_monitoring():
    """Verify container metrics exported to Prometheus."""
    engine = InnovationEngine(config_phase1)

    # Run 5 iterations
    engine.run(max_iterations=5)

    # Check Prometheus metrics
    metrics = fetch_prometheus_metrics()

    assert "container_memory_usage_bytes" in metrics
    assert "container_cpu_usage_seconds_total" in metrics
    assert "strategy_execution_time_seconds" in metrics

    # Verify Grafana dashboard accessible
    response = requests.get("http://localhost:3000/d/finlab-containers")
    assert response.status_code == 200, "Grafana dashboard not accessible"
```

**Expected Result**: Metrics exported to Prometheus
**Success Criteria**: Grafana shows container dashboard with data

---

#### TC-P1-10: Container Cleanup
```python
def test_container_cleanup():
    """Verify no orphaned containers after test."""
    engine = InnovationEngine(config_phase1)

    # Run test
    engine.run(max_iterations=5)

    # Check for orphaned containers
    client = docker.from_env()
    containers = client.containers.list(all=True, filters={"name": "finlab"})

    assert len(containers) == 0, f"Found {len(containers)} orphaned containers"
```

**Expected Result**: Zero containers remain after test
**Success Criteria**: `docker ps -a | grep finlab` returns nothing

---

#### TC-P1-11: Exit Mutation
```python
def test_exit_mutation():
    """Verify exit parameter mutations work in Docker."""
    mutator = ExitParameterMutator()

    # Run 20 mutations
    mutations = []
    for i in range(20):
        code = load_strategy_with_exit_params()
        mutated = mutator.mutate(code, param="stop_loss_pct")

        # Execute in Docker
        executor = DockerExecutor(config_phase1)
        result = executor.execute(mutated, timeout=300)

        mutations.append({
            "success": result["status"] == "success",
            "param_changed": extract_param(mutated, "stop_loss_pct") != extract_param(code, "stop_loss_pct")
        })

    success_rate = sum(m["success"] for m in mutations) / len(mutations)
    assert success_rate >= 0.70, f"Only {success_rate:.0%} success rate (target: ≥70%)"
```

**Expected Result**: ≥70% mutation success rate
**Success Criteria**: Mutations validate and execute successfully

---

#### TC-P1-12: End-to-End 20 Iterations
```python
def test_end_to_end_20_iterations():
    """Run full 20-iteration loop with Docker."""
    engine = InnovationEngine(config_phase1)

    results = engine.run(max_iterations=20)

    # Verify completion
    assert results["iterations_completed"] == 20

    # Verify security
    assert results["container_escapes"] == 0, "Container escape detected!"
    assert results["security_violations"] == 0, "Security violation detected!"

    # Verify execution
    assert results["strategies_executed"] > 0, "No strategies executed"

    # Verify metrics
    assert "sharpe_ratio_best" in results
    assert "population_diversity" in results

    print("\n✅ Phase 1 Complete:")
    print(f"   Container Escapes: {results['container_escapes']}")
    print(f"   Security Violations: {results['security_violations']}")
    print(f"   Strategies Executed: {results['strategies_executed']}")
    print(f"   Best Sharpe: {results['sharpe_ratio_best']:.2f}")
```

**Expected Result**: 20 iterations complete without security incidents
**Success Criteria**: Zero escapes, zero violations, metrics healthy

---

### Success Criteria Summary

- ✅ **12/12 test cases pass**
- ✅ **Zero container escapes**
- ✅ **Zero security incidents**
- ✅ **Resource limits enforced 100%**
- ✅ **Exit mutation ≥70%** success rate
- ✅ **Total test time <30 minutes**
- ✅ **Cost <$0.20**

### Running Phase 1

```bash
# 1. Verify Docker Security fixes complete
./scripts/verify_docker_security_tier1.sh

# 2. Build secure Docker image
docker build -t finlab-sandbox:v1-secure -f docker/Dockerfile.secure .

# 3. Start monitoring
docker-compose -f docker/monitoring-stack.yml up -d

# 4. Run Phase 1 tests
python3 -m pytest tests/integration/test_phase1_docker.py -v

# 5. Check Grafana dashboard
open http://localhost:3000/d/finlab-containers

# 6. Review results
cat artifacts/phase1_metrics.json | jq .
```

---

## Phase 2: Extended Integration (50 Iterations)

### Prerequisites

- ✅ Phase 1 complete (12/12 tests pass)
- ✅ No security incidents in Phase 1
- ✅ Container cleanup working

### Objective

Validate **system stability** over extended run, testing for memory leaks, container thrashing, and cost management.

### Configuration

```yaml
# config/test_phase2_extended.yaml

# Inherit from Phase 1, but:
test_params:
  max_iterations: 50
  checkpoint_interval: 10
  enable_population: true  # Population-based learning
  population_size: 10

monitoring:
  memory_leak_detection: true
  alert_on_anomalies: true
```

### Test Cases (8 Total)

#### TC-P2-01: Long-Run Stability
- **Action**: Run 50 iterations without interruption
- **Expected**: Complete successfully
- **Success**: No crashes, all 50 iterations logged

#### TC-P2-02: Memory Leak Detection
- **Action**: Monitor memory usage over time
- **Expected**: Stable (no growth >10% over baseline)
- **Success**: Memory growth <10%, no sustained increase

#### TC-P2-03: Container Thrashing
- **Action**: Measure container creation/cleanup overhead
- **Expected**: <1s overhead per iteration
- **Success**: Overhead <1s, no resource exhaustion

#### TC-P2-04: LLM Cost Management
- **Action**: Track total API costs
- **Expected**: <$0.50 (50 iter × 20% × $0.02 = $0.20 expected)
- **Success**: Actual cost within 2× budget

#### TC-P2-05: Population Evolution
- **Action**: Monitor population diversity over 50 iterations
- **Expected**: Diversity ≥0.1 throughout
- **Success**: No premature convergence, diversity maintained

#### TC-P2-06: Champion Staleness
- **Action**: Track iterations since last champion update
- **Expected**: Champion updated within 20 iterations
- **Success**: Staleness alert triggered correctly

#### TC-P2-07: Metrics Continuity
- **Action**: Verify all 50 iterations logged to Prometheus
- **Expected**: Zero gaps in metrics
- **Success**: Complete time series, no missing data

#### TC-P2-08: Checkpoint Recovery
- **Action**: Interrupt at iteration 25, resume from checkpoint
- **Expected**: Resumes at iteration 26
- **Success**: State restored, continues to iteration 50

### Success Criteria Summary

- ✅ **8/8 test cases pass**
- ✅ **System stability** over 50 iterations
- ✅ **Cost within budget** (<$0.50)
- ✅ **Performance metrics healthy**
- ✅ **Total test time <60 minutes**

---

## Phase 3: Full Production Simulation (100 Generations)

### Prerequisites

- ✅ Phase 2 complete (8/8 tests pass)
- ✅ No memory leaks detected
- ✅ Cost management validated

### Objective

**Production readiness validation** with full 100-generation run, testing all mutation types and hall of fame quality.

### Configuration

```yaml
# config/test_phase3_production.yaml

test_params:
  max_iterations: 100
  checkpoint_interval: 20
  enable_all_mutations: true  # All 5 mutation types
  enable_hall_of_fame: true

mutations:
  factor_mutation: 0.40
  exit_mutation: 0.20
  structural_mutation: 0.15
  ast_mutation: 0.15
  combination_mutation: 0.10
```

### Test Cases (6 Total)

#### TC-P3-01: Production Workload
- **Action**: Run 100 iterations with all features enabled
- **Expected**: Complete successfully
- **Success**: 100/100 iterations logged

#### TC-P3-02: Performance Benchmarks
- **Action**: Compare Sharpe ratio vs baseline
- **Expected**: Improvement over baseline
- **Success**: Sharpe ratio > baseline (statistical significance)

#### TC-P3-03: All Mutation Types
- **Action**: Verify all 5 mutation types active
- **Expected**: Distribution matches config (40/20/15/15/10)
- **Success**: Mutation distribution within ±10% of target

#### TC-P3-04: Hall of Fame Quality
- **Action**: Inspect top 10 strategies
- **Expected**: Diversity and performance
- **Success**: Top 10 show strategy diversity, Sharpe >0.5

#### TC-P3-05: Alert System
- **Action**: Verify alerts triggered correctly
- **Expected**: Memory >80%, diversity <0.1, staleness >20 trigger alerts
- **Success**: All alerts working, no false positives

#### TC-P3-06: End-to-End Production Simulation
- **Action**: Full system validation
- **Expected**: Ready for production deployment
- **Success**: All subsystems healthy, documentation complete

### Success Criteria Summary

- ✅ **6/6 test cases pass**
- ✅ **Performance improvement** demonstrated
- ✅ **System production-ready**
- ✅ **Documentation complete**
- ✅ **Total test time <120 minutes**
- ✅ **Cost <$1.00**

---

## Test Isolation Strategies

### Dry-Run Mode (Phase 0)

```python
class DryRunExecutor:
    """Executor that validates syntax without execution."""

    def execute(self, code: str, timeout: int = 30) -> dict:
        """Validate code without executing."""
        # 1. Parse as AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {"status": "error", "error": str(e)}

        # 2. Check for dangerous imports
        validator = SecurityValidator()
        violations = validator._check_dangerous_imports(tree)
        if violations:
            return {"status": "error", "error": f"Dangerous imports: {violations}"}

        # 3. Return success (no execution)
        return {"status": "success", "mode": "dry_run"}
```

### Docker-Disabled Mode (Phase 0)

```python
class SafeExecutor:
    """Executor for Phase 0 with Docker disabled."""

    def __init__(self, config):
        assert config["docker"]["enabled"] == False
        assert config["docker"]["fallback_to_direct"] == False
        self.dry_run = True

    def execute(self, code: str, timeout: int = 30) -> dict:
        """Only validate, never execute."""
        if self.dry_run:
            return DryRunExecutor().execute(code, timeout)
        else:
            raise RuntimeError("Execution not allowed in Phase 0")
```

---

## Test Execution Summary

### Timeline

| Phase | When | Duration | Prerequisites |
|-------|------|----------|---------------|
| **0** | **TODAY** | 5 min | None (safe to run now) |
| **1** | Week 1 Day 5 | 30 min | Docker Tier 1 fixes (17 hours) |
| **2** | Week 2 Day 1 | 60 min | Phase 1 success |
| **3** | Week 2 Day 5 | 120 min | Phase 2 success |

### Cost Breakdown

| Phase | Iterations | LLM Rate | Expected Calls | Cost per Call | Total Cost |
|-------|------------|----------|----------------|---------------|------------|
| 0 | 10 | 20% | 2 | $0.02 | **$0.04** |
| 1 | 20 | 20% | 4 | $0.02 | **$0.08** |
| 2 | 50 | 20% | 10 | $0.02 | **$0.20** |
| 3 | 100 | 20% | 20 | $0.02 | **$0.40** |
| **Total** | **180** | - | **36** | - | **$0.72** |

### Risk Assessment

| Phase | Execution Risk | Data Risk | Cost Risk | Overall Risk |
|-------|----------------|-----------|-----------|--------------|
| **0** | **ZERO** (dry-run only) | ZERO | MINIMAL | **ZERO** |
| **1** | LOW (Docker sandboxed) | LOW | LOW | **LOW** |
| **2** | LOW (proven in Phase 1) | LOW | MEDIUM | **LOW** |
| **3** | LOW (production-grade) | LOW | MEDIUM | **LOW** |

---

## Answering the User's Question

> "請考慮是否可以在docker未完善的情況下做smoke testing因為yaml Normalizer是在第一次smoke testing之後發現問題才新增的spec"

### Answer: YES, Phase 0 Enables Safe Testing Before Docker

**Key Design Decision:**

Phase 0 was specifically designed to address this exact scenario. By using **dry-run mode**:

1. **Docker disabled** → No Docker required
2. **fallback_to_direct disabled** → No direct execution either
3. **execution.mode = "dry_run"** → Only AST validation

This enables discovering issues like:
- LLM connectivity problems
- YAML generation failures
- **YAML normalization bugs** (uppercase names)
- Code generation errors
- Schema validation issues

**Without any execution risk**, just like how YAML Normalizer was discovered.

### Historical Validation

The user's observation confirms this approach works:

> "yaml Normalizer是在第一次smoke testing之後發現問題才新增的spec"

This means:
1. First smoke test ran (likely with execution)
2. Discovered YAML normalization issues (uppercase names)
3. Created YAML Normalizer spec to fix

**Phase 0 would have discovered this earlier and safer:**
- Dry-run mode shows YAML validation failures
- No execution required
- Safe to run immediately
- Fast feedback loop

---

## Conclusion

This phased e2e testing strategy balances:
- **Safety**: Phase 0 has ZERO execution risk
- **Velocity**: Can start testing TODAY
- **Thoroughness**: Progresses from syntax → isolation → stability → production
- **Cost-effectiveness**: Total cost <$1 for all 4 phases

The design directly addresses the user's need to "smoke test before Docker is complete", enabling rapid iteration and early issue discovery while maintaining safety.

**Recommendation**: Start Phase 0 immediately to validate LLM integration and YAML pipeline. This will likely discover additional issues (as YAML Normalizer was discovered) before investing time in Docker security fixes.
