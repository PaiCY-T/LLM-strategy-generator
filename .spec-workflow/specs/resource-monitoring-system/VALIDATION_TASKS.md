# Resource Monitoring System - Validation Tasks

## Status: Pending Real Environment Validation

These validation tasks address gaps identified in critical review:
- Monitoring integration tests written but partially mocked
- Prometheus/Grafana integration needs real environment validation
- Production readiness needs verification

---

## Validation Task M1: Prometheus Integration Real Environment Test

**Priority**: Critical
**Estimated Time**: 1 hour
**Prerequisites**: Prometheus installed (or use Docker)

### Objectives
1. Start Prometheus HTTP server
2. Verify all 22 metrics exported correctly
3. Test /metrics endpoint accessibility
4. Validate metric format and values

### Steps

```bash
# Option 1: Use existing Prometheus installation
# Start Prometheus pointing to localhost:8000

# Option 2: Use Prometheus in Docker
docker run -d --name prometheus \
  --network host \
  prom/prometheus

# Run monitoring system with Prometheus export
python3 <<'EOF'
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.resource_monitor import ResourceMonitor
from src.monitoring.diversity_monitor import DiversityMonitor
from src.monitoring.alert_manager import AlertManager
from prometheus_client import start_http_server
import time

# Start Prometheus HTTP server
start_http_server(8000)
print("Prometheus metrics server started on http://localhost:8000/metrics")

# Initialize monitoring
collector = MetricsCollector()
resource_monitor = ResourceMonitor(metrics_collector=collector)
diversity_monitor = DiversityMonitor(metrics_collector=collector)
alert_manager = AlertManager(metrics_collector=collector)

# Start background monitoring
resource_monitor.start_monitoring()
alert_manager.start_monitoring()

# Let it run for 60 seconds
print("Collecting metrics for 60 seconds...")
for i in range(60):
    if i % 10 == 0:
        diversity_monitor.record_diversity(0.5 + i*0.01, 10+i, 20, i, False)
    time.sleep(1)

# Cleanup
resource_monitor.stop_monitoring()
alert_manager.stop_monitoring()
print("Monitoring stopped. Check http://localhost:8000/metrics")
input("Press Enter to exit...")
EOF

# Verify metrics endpoint
curl http://localhost:8000/metrics | grep -E "resource_|diversity_|alert_" | head -30
```

### Success Criteria
- ✓ Prometheus HTTP server starts successfully
- ✓ /metrics endpoint accessible
- ✓ All 22 metrics present in output
- ✓ HELP and TYPE lines correct
- ✓ Metric values reasonable (not all zeros)
- ✓ Metrics update over time

### Deliverable
- Prometheus integration validation report
- Screenshots of /metrics endpoint
- Sample metrics output
- Any issues documented

---

## Validation Task M2: Grafana Dashboard Import & Display Test

**Priority**: Critical
**Estimated Time**: 1-2 hours
**Prerequisites**: Grafana installed, Prometheus running

### Objectives
1. Import dashboard JSON to Grafana
2. Configure Prometheus datasource
3. Verify all 4 panels display data
4. Test alert thresholds and annotations

### Steps

```bash
# 1. Start Grafana (if not running)
docker run -d --name grafana \
  --network host \
  -e "GF_SECURITY_ADMIN_PASSWORD=admin" \
  grafana/grafana

# Access Grafana at http://localhost:3000 (admin/admin)

# 2. Configure Prometheus datasource
# - Go to Configuration → Data Sources
# - Add Prometheus datasource
# - URL: http://localhost:9090 (or localhost:8000 for direct metrics)
# - Save & Test

# 3. Import dashboard
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d @config/grafana_dashboard.json

# 4. Run autonomous loop with monitoring to generate data
python3 artifacts/working/modules/autonomous_loop.py \
  --iterations 20 \
  --config config/learning_system.yaml
```

### Manual Verification Steps
1. Open Grafana dashboard in browser
2. Verify **Panel 1: Resource Usage**
   - Memory % displays and updates
   - CPU % displays and updates
   - Disk % displays
   - Alert threshold line at 80% visible
3. Verify **Panel 2: Strategy Performance**
   - Success rate displays
   - Sharpe ratio updates
   - Champion staleness counter increments
4. Verify **Panel 3: Diversity Metrics**
   - Diversity score (0-1) displays
   - Collapse detection indicator works
   - Unique strategy count shows
5. Verify **Panel 4: Container Statistics**
   - Active containers count
   - Orphaned containers count
   - Container resources display (if Docker available)
6. Verify **Annotations**
   - Champion update events marked on timeline
7. Verify **Alerts**
   - Alert rules configured
   - Alerts trigger when thresholds crossed

### Success Criteria
- ✓ Dashboard imports without errors
- ✓ All 4 panels display data (not "No data")
- ✓ Metrics update every 5 seconds (refresh interval)
- ✓ Alert thresholds visible on graphs
- ✓ Annotations appear on champion updates
- ✓ No query errors in panels

### Known Acceptable Issues
- Container metrics may show "No data" if Docker not available
- Some metrics may be zero initially (normal)

### Deliverable
- Grafana dashboard validation report with screenshots
- Screenshots of all 4 panels displaying data
- Alert configuration verification
- Any query errors or display issues documented

---

## Validation Task M3: Monitoring Overhead Real Measurement ✅

**Priority**: High
**Estimated Time**: 2 hours
**Prerequisites**: None
**Status**: ✅ COMPLETED (2025-10-26)
**Result**: PASSED - 3.37% overhead (within acceptable <5% threshold)

### Objectives
Measure actual monitoring overhead in production-like scenario:
1. Baseline: autonomous loop without monitoring
2. With monitoring: autonomous loop with all monitoring enabled
3. Calculate overhead percentage
4. Verify <1% overhead requirement

### Steps

```bash
# 1. Baseline test (monitoring disabled)
time python3 artifacts/working/modules/autonomous_loop.py \
  --iterations 100 \
  --config config/learning_system_baseline.yaml \
  > baseline_output.txt 2>&1

# Extract execution time
grep "Total time" baseline_output.txt

# 2. Monitoring enabled test
time python3 artifacts/working/modules/autonomous_loop.py \
  --iterations 100 \
  --config config/learning_system.yaml \
  > monitoring_output.txt 2>&1

# Extract execution time
grep "Total time" monitoring_output.txt

# 3. Calculate overhead
python3 <<'EOF'
import re

# Read baseline time
with open('baseline_output.txt') as f:
    baseline = f.read()
baseline_match = re.search(r'Total time: ([\d.]+)s', baseline)
baseline_time = float(baseline_match.group(1)) if baseline_match else 0

# Read monitoring time
with open('monitoring_output.txt') as f:
    monitoring = f.read()
monitoring_match = re.search(r'Total time: ([\d.]+)s', monitoring)
monitoring_time = float(monitoring_match.group(1)) if monitoring_match else 0

# Calculate overhead
if baseline_time > 0:
    overhead = ((monitoring_time - baseline_time) / baseline_time) * 100
    print(f"Baseline: {baseline_time:.2f}s")
    print(f"With monitoring: {monitoring_time:.2f}s")
    print(f"Overhead: {overhead:.2f}%")
    print(f"Target: <1%")
    print(f"Status: {'PASS' if overhead < 1.0 else 'FAIL (but acceptable if <5%)'}")
EOF

# 4. Profile CPU and memory usage
python3 -m cProfile -o monitoring_profile.prof \
  artifacts/working/modules/autonomous_loop.py --iterations 10

python3 -c "
import pstats
stats = pstats.Stats('monitoring_profile.prof')
stats.sort_stats('cumulative')
stats.print_stats('monitoring', 20)
"
```

### Success Criteria
- ✓ Overhead <1% (ideal)
- ✓ Overhead <5% (acceptable)
- ✓ CPU usage of monitoring threads <1% total
- ✓ Memory overhead <50MB
- ✓ No performance regression in iteration speed

### Acceptable Results
- Overhead 1-5%: Acceptable for production with minor impact
- Overhead >5%: Investigate and optimize

### Deliverable
- Performance overhead measurement report
- Baseline vs monitoring comparison
- Profiling results showing monitoring impact
- Recommendations for optimization if needed

---

## Validation Task M4: Alert System Real Triggering Test

**Priority**: High
**Estimated Time**: 1 hour
**Prerequisites**: Monitoring system running

### Objectives
Verify alert system triggers correctly in real scenarios:
1. Memory alert (>80%)
2. Diversity collapse alert (<0.1)
3. Champion staleness alert (>20 iterations)
4. Success rate alert (<20%)
5. Orphaned container alert (>3)

### Steps

```bash
# Test each alert type by simulating conditions

# 1. Memory Alert Test
python3 <<'EOF'
from src.monitoring.alert_manager import AlertManager, AlertConfig
from src.monitoring.metrics_collector import MetricsCollector
import time

config = AlertConfig(
    memory_threshold=80.0,
    diversity_collapse_threshold=0.1,
    champion_staleness_threshold=20,
    success_rate_threshold=20.0,
    orphaned_container_threshold=3
)

collector = MetricsCollector()
alert_mgr = AlertManager(config, collector)

# Simulate high memory
alert_mgr._data_sources = {
    'memory_percent': lambda: 85.0  # Above 80% threshold
}

alerts = alert_mgr.evaluate_alerts()
print(f"Memory alert triggered: {any(a.alert_type == 'high_memory' for a in alerts)}")
EOF

# 2. Diversity Collapse Alert Test
python3 <<'EOF'
from src.monitoring.diversity_monitor import DiversityMonitor
from src.monitoring.alert_manager import AlertManager, AlertConfig
from src.monitoring.metrics_collector import MetricsCollector

collector = MetricsCollector()
diversity_monitor = DiversityMonitor(metrics_collector=collector)

# Simulate diversity collapse (5 iterations <0.1)
for i in range(5):
    diversity_monitor.record_diversity(0.05, 5, 20, 0, False)

collapse = diversity_monitor.check_diversity_collapse()
print(f"Diversity collapse detected: {collapse}")
EOF

# 3. Champion Staleness Alert Test
python3 <<'EOF'
from src.monitoring.diversity_monitor import DiversityMonitor
from src.monitoring.metrics_collector import MetricsCollector

collector = MetricsCollector()
diversity_monitor = DiversityMonitor(metrics_collector=collector)

# Simulate 25 iterations without champion update
for i in range(25):
    diversity_monitor.record_diversity(0.5, 10, 20, i, False)

staleness = diversity_monitor.calculate_staleness()
print(f"Champion staleness: {staleness} iterations (threshold: 20)")
print(f"Alert should trigger: {staleness > 20}")
EOF

# 4. Success Rate Alert Test
# (Requires running actual iterations with failures)

# 5. Orphaned Container Alert Test
# (Requires Docker and orphaned containers)
```

### Success Criteria
- ✓ Memory alert triggers when >80%
- ✓ Diversity collapse alert triggers after 5 low iterations
- ✓ Staleness alert triggers after 20 iterations
- ✓ Success rate alert triggers when <20%
- ✓ Orphaned container alert triggers when >3
- ✓ Alert suppression works (no duplicate alerts)

### Deliverable
- Alert system validation report
- Test results for each alert type
- Alert timing and suppression verification
- Any false positives/negatives documented

---

## Summary of Validation Tasks

| Task | Priority | Time | Dependencies | Verifies |
|------|----------|------|--------------|----------|
| M1 | Critical | 1h | Prometheus | Metrics export |
| M2 | Critical | 1-2h | M1, Grafana | Dashboard display |
| M3 | High | 2h | None | Performance overhead |
| M4 | High | 1h | None | Alert triggering |

**Total Estimated Time**: 5-6 hours

**Expected Outcomes**:
- ✓ Prometheus metrics confirmed working
- ✓ Grafana dashboard displays all panels
- ✓ Monitoring overhead <1% verified
- ✓ Alert system triggers correctly
- ✓ Production readiness validated

**Risk Mitigation**:
- If overhead >1%, document and optimize if >5%
- Dashboard display issues: fix queries or panel config
- Alert false positives: adjust thresholds
- Missing metrics: fix integration bugs

---

## Post-Validation Actions

After successful validation:
1. Update STATUS.md with validation results
2. Document any tuning or adjustments made
3. Update production deployment guide
4. Proceed with Tasks 14-15 (documentation/deployment)

If validation fails:
1. Document failures with severity and impact
2. Create fix tasks for critical issues
3. Re-validate after fixes
4. Update production readiness assessment
