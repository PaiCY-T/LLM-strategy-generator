#!/bin/bash
# Monitor Task 0.1 Baseline Re-run Progress

echo "=========================================="
echo "Task 0.1 Baseline Re-run Monitor"
echo "=========================================="
echo ""

# Check if test is running
if pgrep -f "run_20generation_validation.py.*baseline_checkpoints" > /dev/null; then
    echo "✅ Test is RUNNING"
else
    echo "❌ Test is NOT running"
fi
echo ""

# Count checkpoints
checkpoint_count=$(ls -1 baseline_checkpoints/generation_*.json 2>/dev/null | wc -l)
echo "📁 Checkpoints created: $checkpoint_count / 21"
echo ""

# Show latest generation
if [ $checkpoint_count -gt 0 ]; then
    latest_gen=$((checkpoint_count - 1))
    echo "📊 Latest generation: $latest_gen"

    # Extract best Sharpe from latest checkpoint
    latest_file="baseline_checkpoints/generation_${latest_gen}.json"
    if [ -f "$latest_file" ]; then
        best_sharpe=$(python3 -c "
import json
try:
    with open('$latest_file') as f:
        data = json.load(f)
        pop = data.get('population', [])
        sharpes = [s.get('metrics', {}).get('sharpe_ratio', 0) for s in pop if s.get('metrics')]
        if sharpes:
            print(f'{max(sharpes):.3f}')
        else:
            print('N/A')
except:
    print('Error')
" 2>/dev/null)
        echo "📈 Best Sharpe (Gen $latest_gen): $best_sharpe"
    fi
fi
echo ""

# Show last 15 lines of log
echo "📝 Recent log output:"
echo "----------------------------------------"
tail -15 baseline_rerun.log 2>/dev/null || echo "No log file yet"
echo ""

# Estimated completion
if [ $checkpoint_count -gt 1 ]; then
    # Calculate ETA based on ~2 min per generation
    remaining=$((20 - latest_gen))
    eta_minutes=$((remaining * 2))
    echo "⏱️  Estimated time remaining: ~$eta_minutes minutes"
fi
