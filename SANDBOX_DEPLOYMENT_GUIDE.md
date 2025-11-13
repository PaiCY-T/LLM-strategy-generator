# Sandbox Deployment Guide

Complete guide for Phase 6 sandbox deployment with 1-week runtime monitoring.

## Overview

This deployment system provides:
- ✅ Automated evolution execution with monitoring
- ✅ Health checks and automatic recovery
- ✅ Checkpoint saving and resume capability
- ✅ Comprehensive metrics collection
- ✅ Real-time alerting system
- ✅ Graceful shutdown handling

## Quick Start

### Step 1: Run Quick Test (1-2 hours)

**Recommended before full deployment** to verify system stability:

```bash
chmod +x test_sandbox.sh
./test_sandbox.sh
```

This will:
- Run 100 generations with 50 individuals
- Test all monitoring and checkpoint systems
- Generate health reports
- Verify no critical issues

**Expected output:**
- Metrics files: ~10 files
- Checkpoints: 2-3 files
- Test duration: 1-2 hours
- No critical alerts

### Step 2: Start Full Deployment (1 week)

After successful test:

```bash
chmod +x start_sandbox.sh
./start_sandbox.sh
```

**Full deployment configuration:**
- Population: 100 individuals
- Max generations: 1000
- Template distribution: 25% each (Momentum, Turtle, Factor, Mastiff)
- Runtime: Approximately 1 week

### Step 3: Monitor Progress

```bash
# Monitor evolution log
tail -f sandbox_output/logs/evolution.log

# Monitor health checks
tail -f sandbox_output/logs/monitor.log

# Run manual health check
chmod +x sandbox_monitor.sh
./sandbox_monitor.sh check

# Generate health report
./sandbox_monitor.sh report
```

### Step 4: Stop Deployment

```bash
chmod +x stop_sandbox.sh
./stop_sandbox.sh
```

This performs graceful shutdown with:
- Final checkpoint save
- Final metrics export
- Alert summary generation

## File Structure

```
sandbox_output/
├── checkpoints/           # Evolution checkpoints (every 50 generations)
│   ├── checkpoint_gen_50.json
│   ├── checkpoint_gen_100.json
│   └── ...
├── metrics/              # Metrics exports
│   ├── metrics_prometheus_gen_10.txt
│   ├── metrics_json_gen_10.json
│   └── ...
├── alerts/               # Alert logs
│   └── alerts.json
├── logs/                 # System logs
│   ├── evolution.log
│   ├── monitor.log
│   └── health_report_*.txt
├── evolution.pid         # Process ID
└── monitor.pid
```

## Scripts

### sandbox_deployment.py

Main deployment script with features:
- Environment validation (disk space, Python version, imports)
- Checkpoint loading and recovery
- Automated metrics export
- Health checks integration
- Graceful signal handling

**Usage:**
```bash
# Full deployment
python3 sandbox_deployment.py

# Custom configuration
python3 sandbox_deployment.py \
    --population-size 150 \
    --max-generations 2000 \
    --output-dir my_sandbox

# Test mode (100 generations only)
python3 sandbox_deployment.py --test
```

### start_sandbox.sh

Automated startup script:
- Starts evolution in background
- Starts monitoring process
- Verifies successful startup
- Creates log files

**Options:**
```bash
# Default (100 individuals, 1000 generations)
./start_sandbox.sh

# Test mode
./start_sandbox.sh --test

# Custom population
./start_sandbox.sh --population-size 150

# Custom max generations
./start_sandbox.sh --max-generations 2000
```

### sandbox_monitor.sh

Automated health monitoring:
- Process status checks (every 5 minutes)
- Disk space monitoring
- Memory usage tracking
- Metrics validation
- Alert analysis
- Hourly health reports

**Commands:**
```bash
# Start continuous monitoring
./sandbox_monitor.sh monitor

# Single health check
./sandbox_monitor.sh check

# Generate report
./sandbox_monitor.sh report
```

### stop_sandbox.sh

Graceful shutdown:
- Sends SIGTERM for graceful shutdown
- Waits up to 30 seconds
- Forces termination if needed
- Preserves all output data

### test_sandbox.sh

Quick validation test:
- Runs 100 generations (~1-2 hours)
- Smaller population (50)
- Verifies all systems working
- Generates test summary report

## Monitoring Metrics

### Real-time Metrics (Every 10 generations)

**Prometheus format** (`metrics_prometheus_gen_*.txt`):
- `evolution_generation`: Current generation
- `evolution_avg_fitness`: Average fitness
- `evolution_best_fitness`: Best fitness
- `evolution_diversity_unified`: Unified diversity score
- `evolution_template_count{template="X"}`: Population per template
- `evolution_mutations_total`: Total mutations
- `evolution_alerts_total`: Total alerts

**JSON format** (`metrics_json_gen_*.json`):
```json
{
  "metadata": {
    "export_timestamp": "2025-10-19T...",
    "runtime_hours": 24.5
  },
  "summary": {
    "current_generation": 500,
    "best_fitness": 2.45,
    "avg_fitness": 1.82,
    "diversity": 0.75,
    "champion_template": "Mastiff",
    "template_distribution": {...},
    "convergence_analysis": {...}
  }
}
```

### Health Checks (Every 5 minutes)

Monitors:
1. **Process Status**: Evolution process running
2. **Disk Space**: ≥1GB available
3. **Memory Usage**: Warning if >80%
4. **Metrics Age**: Updated within 10 minutes
5. **Critical Alerts**: Count in last hour

### Alerts

**Alert Severity Levels:**
- `LOW`: Informational (e.g., no improvement for 20 generations)
- `MEDIUM`: Attention needed (e.g., fitness drop 20-50%)
- `HIGH`: Serious issue (e.g., fitness drop >50%, diversity <0.1)
- `CRITICAL`: System error (e.g., crash, memory issue)

**Alert Types:**
- `fitness_drop`: Significant fitness decrease
- `diversity_collapse`: Diversity below threshold
- `no_improvement`: Stagnation detected
- `system_error`: Runtime errors

## Checkpoints

**Saved every 50 generations:**
- Generation number
- Recent metrics (last 10 generations)
- Event counters (mutations, crossovers)
- Best fitness ever

**Recovery:**
- Automatically loads latest checkpoint on restart
- Continues from last saved generation
- Preserves evolution history

## Troubleshooting

### Evolution Won't Start

**Check:**
```bash
# Environment validation
python3 sandbox_deployment.py --test

# Check logs
cat sandbox_output/logs/evolution.log
```

**Common issues:**
- Insufficient disk space (<1GB)
- Python version <3.8
- Missing dependencies

**Fix:**
```bash
# Free disk space
df -h

# Install dependencies
pip3 install -r requirements.txt
```

### Evolution Stuck

**Symptoms:**
- Metrics not updating
- Log file not growing
- High CPU but no progress

**Check:**
```bash
# Health check
./sandbox_monitor.sh check

# Check latest metrics age
ls -lth sandbox_output/metrics/
```

**Fix:**
```bash
# Stop and restart
./stop_sandbox.sh
./start_sandbox.sh
```

### High Memory Usage

**Monitor:**
```bash
# Check current usage
./sandbox_monitor.sh check | grep "Memory"

# Watch process
top -p $(cat sandbox_output/evolution.pid)
```

**Fix if >80%:**
- Reduce population size: `--population-size 50`
- Reduce metrics history window (edit `evolution_metrics.py`)
- Increase checkpoint frequency to free memory

### Too Many Alerts

**Check alert types:**
```bash
python3 -c "
import json
with open('sandbox_output/alerts/alerts.json', 'r') as f:
    alerts = json.load(f)

from collections import Counter
types = Counter(a['alert_type'] for a in alerts)
for alert_type, count in types.most_common():
    print(f'{alert_type}: {count}')
"
```

**Adjust thresholds:**
Edit `sandbox_deployment.py` alert thresholds:
```python
alert_thresholds = {
    'fitness_drop_percentage': 30.0,  # Increase from 20.0
    'diversity_floor': 0.05,          # Decrease from 0.1
    'no_improvement_generations': 50  # Increase from 20
}
```

## Expected Timeline

### Test Run (1-2 hours)
- ✅ **0-10 min**: Initialization and first 10 generations
- ✅ **10-60 min**: Steady evolution, metrics export every 10 gens
- ✅ **60-120 min**: Complete 100 generations, final export

### Full Deployment (1 week)
- ✅ **Day 1**: Generations 0-150, template distribution stabilizing
- ✅ **Day 2-3**: Generations 150-500, convergence patterns emerge
- ✅ **Day 4-6**: Generations 500-900, fine-tuning and optimization
- ✅ **Day 7**: Generations 900-1000, final convergence

## Success Criteria (Task 44)

After 1-week run, verify:

1. **Completion**: ≥1000 generations executed
2. **Stability**: <5 critical alerts total
3. **Data Quality**:
   - ≥100 metrics files
   - ≥20 checkpoints
   - Complete alert log
4. **Convergence**:
   - Fitness improvement visible
   - Template distribution evolution tracked
   - Diversity maintained >0.1
5. **System Health**:
   - No crashes or restarts required
   - Disk usage <10GB
   - Memory stable

## Next Steps

After successful 1-week run:

1. **Task 44**: Document findings
   - Analyze convergence patterns
   - Review alert history
   - Evaluate template evolution
   - Generate performance report

2. **Task 45-48**: Historical validation
   - Acquire real market data
   - Run backtests
   - Compare sandbox vs historical

3. **Task 49-52**: Production deployment
   - Shadow mode
   - Live trading preparation

## Contact & Support

For issues or questions:
- Check logs: `sandbox_output/logs/`
- Review alerts: `sandbox_output/alerts/alerts.json`
- Generate health report: `./sandbox_monitor.sh report`
- Check system status: `./sandbox_monitor.sh check`
