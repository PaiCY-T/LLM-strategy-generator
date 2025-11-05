#!/bin/bash
# Sandbox Evolution Monitor
# Monitors running evolution and performs health checks

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/sandbox_output"
LOG_FILE="${OUTPUT_DIR}/logs/monitor.log"
PID_FILE="${OUTPUT_DIR}/evolution.pid"
CHECK_INTERVAL=300  # 5 minutes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

# Create output directory if needed
mkdir -p "${OUTPUT_DIR}/logs"

# Check if evolution process is running
check_process() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # Running
        else
            log_warning "PID file exists but process not running"
            rm -f "$PID_FILE"
            return 1  # Not running
        fi
    fi
    return 1  # Not running
}

# Check disk space
check_disk_space() {
    AVAILABLE=$(df -BG "$OUTPUT_DIR" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$AVAILABLE" -lt 1 ]; then
        log_error "Low disk space: ${AVAILABLE}GB remaining"
        return 1
    fi
    log "Disk space: ${AVAILABLE}GB available"
    return 0
}

# Check memory usage
check_memory() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            MEM_USAGE=$(ps -p "$PID" -o %mem= | tr -d ' ')
            log "Memory usage: ${MEM_USAGE}%"

            # Warning if > 80%
            if (( $(echo "$MEM_USAGE > 80" | bc -l) )); then
                log_warning "High memory usage: ${MEM_USAGE}%"
            fi
        fi
    fi
}

# Check latest metrics
check_metrics() {
    LATEST_METRICS=$(ls -t "${OUTPUT_DIR}/metrics"/metrics_json_gen_*.json 2>/dev/null | head -1)

    if [ -z "$LATEST_METRICS" ]; then
        log_warning "No metrics files found"
        return 1
    fi

    # Extract generation from filename
    GEN=$(basename "$LATEST_METRICS" | grep -oP 'gen_\K[0-9]+')

    # Check file age (should be updated within last 10 minutes)
    FILE_AGE=$(($(date +%s) - $(stat -c %Y "$LATEST_METRICS")))

    if [ "$FILE_AGE" -gt 600 ]; then
        log_warning "Metrics file is old (${FILE_AGE}s), evolution may be stuck at generation $GEN"
        return 1
    fi

    log_success "Latest metrics: generation $GEN (${FILE_AGE}s ago)"
    return 0
}

# Check for critical alerts
check_alerts() {
    ALERT_FILE="${OUTPUT_DIR}/alerts/alerts.json"

    if [ ! -f "$ALERT_FILE" ]; then
        log "No alert file found (OK for early run)"
        return 0
    fi

    # Count critical alerts in last hour
    RECENT_CRITICAL=$(python3 -c "
import json
import time
try:
    with open('$ALERT_FILE', 'r') as f:
        alerts = json.load(f)

    one_hour_ago = time.time() - 3600
    critical_count = sum(1 for a in alerts if a.get('timestamp', 0) > one_hour_ago and a.get('severity') == 'critical')
    print(critical_count)
except:
    print(0)
" 2>/dev/null)

    if [ "$RECENT_CRITICAL" -gt 0 ]; then
        log_warning "Found $RECENT_CRITICAL critical alerts in last hour"
        return 1
    fi

    log "Alert check: No critical alerts in last hour"
    return 0
}

# Generate status report
generate_report() {
    REPORT_FILE="${OUTPUT_DIR}/logs/health_report_$(date +%Y%m%d_%H%M%S).txt"

    {
        echo "=== Sandbox Evolution Health Report ==="
        echo "Generated: $(date)"
        echo ""

        echo "Process Status:"
        if check_process; then
            echo "  ✓ Evolution process running (PID: $(cat $PID_FILE))"
        else
            echo "  ✗ Evolution process NOT running"
        fi
        echo ""

        echo "Resource Status:"
        check_disk_space
        check_memory
        echo ""

        echo "Metrics Status:"
        check_metrics
        echo ""

        echo "Alert Status:"
        check_alerts
        echo ""

        # Latest checkpoint
        LATEST_CHECKPOINT=$(ls -t "${OUTPUT_DIR}/checkpoints"/checkpoint_gen_*.json 2>/dev/null | head -1)
        if [ -n "$LATEST_CHECKPOINT" ]; then
            echo "Latest Checkpoint:"
            echo "  File: $(basename $LATEST_CHECKPOINT)"
            echo "  Age: $(($(date +%s) - $(stat -c %Y "$LATEST_CHECKPOINT")))s"
        fi

    } | tee "$REPORT_FILE"

    log "Health report saved: $REPORT_FILE"
}

# Main monitoring loop
monitor_loop() {
    log "Starting monitoring loop (interval: ${CHECK_INTERVAL}s)"

    while true; do
        log "--- Health Check Cycle ---"

        # Run checks
        check_process
        PROCESS_OK=$?

        check_disk_space
        DISK_OK=$?

        check_memory
        check_metrics
        METRICS_OK=$?

        check_alerts
        ALERTS_OK=$?

        # Overall status
        if [ $PROCESS_OK -eq 0 ] && [ $DISK_OK -eq 0 ] && [ $METRICS_OK -eq 0 ] && [ $ALERTS_OK -eq 0 ]; then
            log_success "All checks passed"
        else
            log_warning "Some checks failed"
        fi

        # Generate hourly report
        CURRENT_HOUR=$(date +%H)
        if [ "$CURRENT_HOUR" != "$LAST_REPORT_HOUR" ]; then
            generate_report
            LAST_REPORT_HOUR=$CURRENT_HOUR
        fi

        # Sleep until next check
        sleep "$CHECK_INTERVAL"
    done
}

# Command handling
case "${1:-monitor}" in
    monitor)
        monitor_loop
        ;;
    check)
        log "Running single health check..."
        check_process
        check_disk_space
        check_memory
        check_metrics
        check_alerts
        ;;
    report)
        generate_report
        ;;
    *)
        echo "Usage: $0 {monitor|check|report}"
        echo "  monitor - Start continuous monitoring loop"
        echo "  check   - Run single health check"
        echo "  report  - Generate health report"
        exit 1
        ;;
esac
