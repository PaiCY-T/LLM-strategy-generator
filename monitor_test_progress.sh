#!/bin/bash
# Monitor sandbox test progress in real-time

OUTPUT_DIR="sandbox_output_test"
LOG_FILE="sandbox_evolution.log"

echo "==================================="
echo "  Sandbox Test Progress Monitor"
echo "==================================="
echo ""

# Check if process is running
PROCESS=$(ps aux | grep "sandbox_deployment.py" | grep -v grep | grep "9314")
if [ -z "$PROCESS" ]; then
    echo "❌ Test process not running!"
    exit 1
fi

echo "✅ Process Status:"
echo "$PROCESS" | awk '{printf "   PID: %s | CPU: %s | MEM: %.1fMB | Runtime: %s\n", $2, $3"%", $6/1024, $10}'
echo ""

# Check for latest metrics
echo "📊 Latest Metrics:"
LATEST_METRICS=$(ls -t ${OUTPUT_DIR}/metrics/metrics_json_gen_*.json 2>/dev/null | head -1)
if [ -n "$LATEST_METRICS" ]; then
    GEN=$(basename "$LATEST_METRICS" | sed 's/metrics_json_gen_//' | sed 's/.json//')
    echo "   Last exported: Generation $GEN"
else
    echo "   No metrics exported yet (waiting for gen 9...)"
fi

# Check checkpoints
CHECKPOINTS=$(ls ${OUTPUT_DIR}/checkpoints/checkpoint_gen_*.json 2>/dev/null | wc -l)
echo "   Checkpoints: $CHECKPOINTS"

# Check alerts
if [ -f "${OUTPUT_DIR}/alerts/alerts.json" ]; then
    ALERTS=$(python3 -c "import json; print(len(json.load(open('${OUTPUT_DIR}/alerts/alerts.json'))))" 2>/dev/null || echo "0")
    echo "   Alerts: $ALERTS"
fi

echo ""

# Show recent log entries
echo "📋 Recent Activity:"
tail -20 "$LOG_FILE" 2>/dev/null | grep -E "(Gen |generation |ERROR)" | tail -5 || echo "   Waiting for first generation to complete..."

echo ""
echo "==================================="
