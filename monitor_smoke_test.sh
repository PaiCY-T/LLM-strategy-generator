#!/bin/bash
# Phase 1 Smoke Test Monitor
# Real-time monitoring of 10-generation evolutionary test

LOG_FILE="phase1_smoke_test_output.log"
DETAIL_LOG="logs/phase1_smoke_test_20251028_133356.log"

echo "=========================================="
echo "Phase 1 Smoke Test Monitor"
echo "=========================================="
echo "Start Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check if test is running
if ! ps aux | grep -q "[p]ython3 run_phase1_smoke_test.py"; then
    echo "⚠️  Test process not found. Checking if completed..."
    if [ -f "$LOG_FILE" ]; then
        echo "📋 Log file exists, checking final status..."
    else
        echo "❌ No log file found"
        exit 1
    fi
fi

# Monitor loop
while true; do
    clear
    echo "=========================================="
    echo "Phase 1 Smoke Test - Live Monitor"
    echo "=========================================="
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Check progress
    if [ -f "$LOG_FILE" ]; then
        # Extract generation progress
        CURRENT_GEN=$(tail -100 "$LOG_FILE" | grep -oP "Generation \K\d+" | tail -1)
        if [ -z "$CURRENT_GEN" ]; then
            CURRENT_GEN="Initializing..."
        else
            echo "📊 Current Generation: $CURRENT_GEN / 10"
        fi

        # Extract latest metrics
        echo ""
        echo "📈 Latest Metrics:"
        tail -50 "$LOG_FILE" | grep -E "(Sharpe|Champion|Population|Success)" | tail -5

        # Check for errors
        ERROR_COUNT=$(grep -c "ERROR" "$LOG_FILE" 2>/dev/null || echo "0")
        WARNING_COUNT=$(grep -c "WARNING" "$LOG_FILE" 2>/dev/null || echo "0")

        echo ""
        echo "🔍 Status:"
        echo "  Errors: $ERROR_COUNT"
        echo "  Warnings: $WARNING_COUNT"

        # Check if completed
        if grep -q "SMOKE TEST COMPLETE" "$LOG_FILE" 2>/dev/null; then
            echo ""
            echo "✅ Test Completed!"
            echo ""
            echo "📊 Final Results:"
            tail -30 "$LOG_FILE" | grep -E "(Champion|Success|Sharpe)"
            break
        fi

        # Check if failed
        if grep -q "TEST FAILED" "$LOG_FILE" 2>/dev/null; then
            echo ""
            echo "❌ Test Failed"
            echo ""
            echo "🔍 Last 20 lines:"
            tail -20 "$LOG_FILE"
            break
        fi
    else
        echo "⏳ Waiting for log file..."
    fi

    echo ""
    echo "Press Ctrl+C to exit monitor (test continues in background)"
    echo "Next update in 30 seconds..."

    sleep 30
done

echo ""
echo "=========================================="
echo "Monitor session ended"
echo "=========================================="
echo "Full log: $LOG_FILE"
echo "Detailed log: $DETAIL_LOG"
