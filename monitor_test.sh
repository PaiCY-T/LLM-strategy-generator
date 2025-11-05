#!/bin/bash
# Monitor 50-iteration test progress
LOG_FILE="logs/50iter_phase3_run.log"

while true; do
    if ps aux | grep -q "[r]un_50iteration_test.py"; then
        LINES=$(wc -l < "$LOG_FILE")
        LAST_ITER=$(grep -o "ITERATION [0-9]\+/49" "$LOG_FILE" | tail -1)
        echo "$(date +%H:%M:%S) - Test running: $LAST_ITER ($LINES lines in log)"
        sleep 60
    else
        echo "$(date +%H:%M:%S) - Test completed!"
        echo ""
        echo "Final results:"
        tail -50 "$LOG_FILE" | grep -E "(✅|❌|Champion|PASS|FAIL|Cohen|p-value|variance|frequency)"
        break
    fi
done
