#!/bin/bash
# Monitor Phase 2 Re-Run Progress

LOG_FILE="phase2_fixed_run.log"

echo "=== Phase 2 Progress Monitor ==="
echo "Started: $(date)"
echo ""

# Extract latest iteration number
CURRENT_ITER=$(grep -o "Iteration [0-9]\+/20" "$LOG_FILE" 2>/dev/null | tail -1 | cut -d' ' -f2 | cut -d'/' -f1)
if [ -z "$CURRENT_ITER" ]; then
    CURRENT_ITER=0
fi

# Count successes
GENERATION_SUCCESS=$(grep -c "✅ Strategy generated" "$LOG_FILE" 2>/dev/null || echo 0)
VALIDATION_SUCCESS=$(grep -c "✅ Validation passed" "$LOG_FILE" 2>/dev/null || echo 0)
USES_ADJUSTED=$(grep -c "✅ Uses adjusted data" "$LOG_FILE" 2>/dev/null || echo 0)
VALIDATION_FAILED=$(grep -c "❌ Validation failed" "$LOG_FILE" 2>/dev/null || echo 0)

# Calculate rates
if [ "$CURRENT_ITER" -gt 0 ]; then
    GEN_RATE=$(echo "scale=1; $GENERATION_SUCCESS * 100 / $CURRENT_ITER" | bc)
    VAL_RATE=$(echo "scale=1; $VALIDATION_SUCCESS * 100 / $CURRENT_ITER" | bc)
    ADJ_RATE=$(echo "scale=1; $USES_ADJUSTED * 100 / $CURRENT_ITER" | bc)
else
    GEN_RATE=0.0
    VAL_RATE=0.0
    ADJ_RATE=0.0
fi

echo "Progress: Iteration $CURRENT_ITER/20"
echo ""
echo "Generation Success: $GENERATION_SUCCESS/$CURRENT_ITER ($GEN_RATE%)"
echo "Validation Success: $VALIDATION_SUCCESS/$CURRENT_ITER ($VAL_RATE%)"
echo "Uses Adjusted Data: $USES_ADJUSTED/$CURRENT_ITER ($ADJ_RATE%)"
echo "Validation Failed:  $VALIDATION_FAILED"
echo ""

# Show last few lines
echo "=== Latest Output ==="
tail -15 "$LOG_FILE" 2>/dev/null || echo "No output yet"
echo ""

# Completion estimate
if [ "$CURRENT_ITER" -gt 0 ]; then
    REMAINING=$((20 - CURRENT_ITER))
    echo "Remaining: $REMAINING iterations"
fi
