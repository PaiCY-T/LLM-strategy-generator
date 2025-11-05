# Exit Mutation Production Deployment Guide

**Version**: 1.0
**Date**: 2025-10-20
**Target Audience**: DevOps, ML Engineers, System Administrators

---

## Quick Start

```bash
# 1. Verify configuration
python3 -c "import yaml; yaml.safe_load(open('config/learning_system.yaml'))"

# 2. Run integration tests
pytest tests/generators/test_exit_mutation_integration.py -v

# 3. Run performance benchmark
python3 scripts/benchmark_exit_mutation.py --output baseline.json

# 4. Enable in production (set enabled: true in YAML)

# 5. Monitor statistics
# Check exit_mutation_attempts, exit_mutation_successes, exit_mutation_failures
```

---

## Configuration Reference

### File: `config/learning_system.yaml`

```yaml
exit_mutation:
  enabled: true                       # Enable/disable framework
  exit_mutation_probability: 0.3      # 30% probability vs parameter mutation

  mutation_config:
    tier1_weight: 0.5                 # Parametric (50%)
    tier2_weight: 0.3                 # Structural (30%)
    tier3_weight: 0.2                 # Relational (20%)

    parameter_ranges:
      stop_loss_range: [0.8, 1.2]    # ±20%
      take_profit_range: [0.9, 1.3]   # +30%
      trailing_range: [0.85, 1.25]    # ±25%

  validation:
    max_retries: 3                    # Validation retry attempts
    validation_timeout: 5             # Timeout in seconds

  monitoring:
    log_mutations: true               # Log all mutations
    track_mutation_types: true        # Track type distribution
    log_validation: true              # Log validation results
```

### Configuration Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `enabled` | bool | true | true/false | Master enable switch |
| `exit_mutation_probability` | float | 0.3 | 0.0-1.0 | Probability vs parameter mutations |
| `tier1_weight` | float | 0.5 | 0.0-1.0 | Parametric mutation weight |
| `tier2_weight` | float | 0.3 | 0.0-1.0 | Structural mutation weight |
| `tier3_weight` | float | 0.2 | 0.0-1.0 | Relational mutation weight |
| `stop_loss_range` | [float,float] | [0.8,1.2] | [0.5,2.0] | Stop-loss adjustment multiplier |
| `take_profit_range` | [float,float] | [0.9,1.3] | [0.5,2.0] | Take-profit adjustment multiplier |
| `trailing_range` | [float,float] | [0.85,1.25] | [0.5,2.0] | Trailing stop adjustment multiplier |
| `max_retries` | int | 3 | 1-10 | Max validation retry attempts |
| `validation_timeout` | int | 5 | 1-30 | Validation timeout (seconds) |

---

## Deployment Checklist

### Pre-Deployment

- [ ] Configuration file validated (`learning_system.yaml` syntax correct)
- [ ] Integration tests passing (8/8 tests)
- [ ] Performance baseline established (benchmark run complete)
- [ ] Monitoring infrastructure ready (logging, metrics collection)
- [ ] Rollback plan documented
- [ ] Team trained on new feature

### Deployment

1. **Backup Current Configuration**
   ```bash
   cp config/learning_system.yaml config/learning_system.yaml.backup
   ```

2. **Update Configuration**
   - Set `enabled: true` in `exit_mutation` section
   - Verify all parameters are within acceptable ranges
   - Commit configuration changes to version control

3. **Deploy Code**
   ```bash
   git pull origin main
   pytest tests/generators/test_exit_mutation_integration.py -v
   ```

4. **Restart Services** (if applicable)
   - Restart autonomous learning loop
   - Restart population evolution workers
   - Verify services started successfully

5. **Monitor Initial Performance**
   - Check logs for mutation attempts/successes
   - Verify statistics tracking working
   - Monitor for unexpected errors

### Post-Deployment

- [ ] Statistics tracking confirmed working
- [ ] Mutation success rate ≥80% verified
- [ ] No performance degradation observed
- [ ] Logs reviewed for errors
- [ ] Stakeholders notified of deployment

---

## Monitoring and Alerting

### Key Metrics

| Metric | Location | Target | Alert Threshold |
|--------|----------|--------|-----------------|
| `exit_mutation_attempts` | PopulationManager | N/A | N/A |
| `exit_mutation_successes` | PopulationManager | ≥80% of attempts | <70% |
| `exit_mutation_failures` | PopulationManager | <20% of attempts | >30% |
| `mutation_type_distribution` | PopulationManager | Tier1:50%, Tier2:30%, Tier3:20% | ±15% deviation |
| `avg_mutation_time` | Benchmark | <10ms | >100ms |
| `memory_usage` | System | <10MB | >50MB |

### Logging Configuration

**Log Level**: INFO (production), DEBUG (troubleshooting)

**Log Format**:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/exit_mutation.log'),
        logging.StreamHandler()
    ]
)
```

**Key Log Events**:
- Mutation attempts (INFO)
- Mutation successes/failures (INFO)
- Validation errors (WARNING)
- Configuration loading (INFO)
- Performance anomalies (WARNING)

---

## Troubleshooting

### Issue 1: Low Mutation Success Rate (<80%)

**Symptoms**: `exit_mutation_failures` > 20% of attempts

**Possible Causes**:
1. Strategies lack proper exit mechanisms
2. Validation too strict
3. AST parsing failures

**Resolution**:
1. Review failed mutation logs
2. Verify strategy code has exit patterns
3. Check validation error messages
4. Consider adjusting `max_retries` to 5

### Issue 2: High Memory Usage (>50MB)

**Symptoms**: Memory usage exceeds 50MB

**Possible Causes**:
1. Memory leaks in mutation operators
2. Large strategy code samples
3. Accumulated validation results

**Resolution**:
1. Run memory profiling benchmark
2. Check for circular references
3. Review operator cleanup logic
4. Restart services if memory doesn't stabilize

### Issue 3: Slow Mutation Performance (>100ms)

**Symptoms**: Mutations take >100ms on average

**Possible Causes**:
1. Complex strategy code
2. Validation timeout too high
3. Resource contention

**Resolution**:
1. Run performance benchmark
2. Profile slow mutations
3. Check system resource availability
4. Consider reducing `validation_timeout`

### Issue 4: Configuration Loading Errors

**Symptoms**: Errors loading `learning_system.yaml`

**Possible Causes**:
1. YAML syntax errors
2. Missing configuration file
3. Invalid parameter values

**Resolution**:
1. Validate YAML syntax:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('config/learning_system.yaml'))"
   ```
2. Check file permissions
3. Verify all required parameters present
4. Use fallback defaults if needed

---

## Performance Tuning

### Optimization Recommendations

**Current Performance** (already excellent):
- Single mutation: 1.11ms average
- Batch throughput: 56,718 mutations/minute
- Memory usage: 1.15MB peak
- No optimization needed

**If Performance Degrades**:

1. **Reduce Validation Overhead**
   ```yaml
   validation:
     validation_timeout: 3  # Reduce from 5s to 3s
   ```

2. **Adjust Retry Logic**
   ```yaml
   validation:
     max_retries: 2  # Reduce from 3 to 2
   ```

3. **Simplify Mutation Distribution**
   ```yaml
   mutation_config:
     tier1_weight: 0.7  # Increase parametric (faster)
     tier2_weight: 0.2  # Decrease structural
     tier3_weight: 0.1  # Decrease relational
   ```

4. **Cache Configuration**
   - Configuration already cached on first load
   - No additional caching needed

---

## Security Considerations

### Code Execution

**Current Security**:
- No external code execution
- AST-based mutations (safe)
- Validation pipeline prevents invalid code
- No file I/O or network calls in mutations

**Security Best Practices**:
1. Keep configuration file read-only (chmod 444)
2. Validate YAML before deployment
3. Review mutation logs for anomalies
4. Monitor for unexpected code patterns

### Access Control

**Recommended Permissions**:
- Configuration file: Read-only (444)
- Log directory: Write-only for services (755)
- Code directory: Read-only for services (755)

---

## Rollback Plan

### Rolling Back Exit Mutations

1. **Disable Feature**
   ```yaml
   exit_mutation:
     enabled: false
   ```

2. **Restart Services**
   ```bash
   # Restart autonomous loop or population workers
   ```

3. **Verify Rollback**
   ```bash
   # Check logs confirm mutations disabled
   grep "exit_mutation" logs/population_manager.log
   ```

4. **Restore Previous Configuration** (if needed)
   ```bash
   cp config/learning_system.yaml.backup config/learning_system.yaml
   ```

### Rollback Checklist

- [ ] Feature disabled in configuration
- [ ] Services restarted successfully
- [ ] Mutation attempts stop (verify in logs)
- [ ] System reverts to parameter mutations only
- [ ] Performance baseline restored
- [ ] Stakeholders notified

---

## Support and Escalation

### Support Tiers

**Tier 1: Self-Service**
- Review troubleshooting guide
- Check logs for error messages
- Run integration tests
- Run performance benchmark

**Tier 2: Team Support**
- Contact development team
- Provide logs and configuration
- Share benchmark results
- Review recent code changes

**Tier 3: Expert Escalation**
- Complex AST issues
- Performance degradation
- Security concerns
- Architecture questions

---

## Maintenance

### Regular Tasks

**Daily**:
- Review mutation success rate (≥80%)
- Check for error logs
- Verify statistics tracking

**Weekly**:
- Run performance benchmark
- Review mutation type distribution
- Check memory usage trends

**Monthly**:
- Configuration parameter review
- Performance tuning evaluation
- Security audit

---

## Additional Resources

### Documentation
- `PHASE1_6_INTEGRATION_COMPLETE.md` - Implementation summary
- `docs/EXIT_MUTATION_API_REFERENCE.md` - API documentation
- `TASK_1.7_E2E_VALIDATION_REPORT.md` - Validation results

### Code
- `src/mutation/exit_mutation_operator.py` - Main operator
- `src/mutation/exit_mutator.py` - Mutation engine
- `src/mutation/exit_validator.py` - Validation pipeline
- `tests/generators/test_exit_mutation_integration.py` - Integration tests

### Scripts
- `scripts/benchmark_exit_mutation.py` - Performance benchmarking
- `run_exit_mutation_smoke_test.py` - Smoke testing

---

**Last Updated**: 2025-10-20
**Version**: 1.0
**Maintainer**: Development Team
