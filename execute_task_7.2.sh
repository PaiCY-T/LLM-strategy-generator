#!/bin/bash
# Phase 2 Task 7.2: Automated Execution Script
# Run this in a separate terminal to avoid context consumption

set -e  # Exit on error

WORK_DIR="/mnt/c/Users/jnpi/documents/finlab"
cd "$WORK_DIR"

echo "=============================================="
echo "Phase 2 Task 7.2: Full 20-Strategy Validation"
echo "=============================================="
echo ""

# Step 1: Pre-flight checks
echo "[Step 1/5] Pre-flight verification..."
python3 -c "from finlab import data; assert data.get('price:收盤價') is not None, 'Auth failed'" && echo "✅ Finlab auth OK"
[ $(ls generated_strategy_fixed_iter*.py | wc -l) -eq 20 ] && echo "✅ 20 strategy files confirmed"
python3 -c "from src.validation import BonferroniIntegrator, DynamicThresholdCalculator" && echo "✅ Validation framework OK"
echo ""

# Step 2: Pilot test (3 strategies)
echo "[Step 2/5] Running pilot test (3 strategies)..."
echo "Start time: $(date)"
python3 run_phase2_with_validation.py --limit 3 --timeout 420 2>&1 | tee phase2_pilot_with_validation.log
echo "Pilot test complete: $(date)"
echo ""

# Check pilot test results
if [ $? -ne 0 ]; then
    echo "❌ Pilot test FAILED. Check phase2_pilot_with_validation.log for errors."
    exit 1
fi

# Verify pilot reports generated
PILOT_JSON=$(ls -t phase2_validated_results_*.json 2>/dev/null | head -1)
if [ -z "$PILOT_JSON" ]; then
    echo "❌ Pilot test reports not generated. Aborting."
    exit 1
fi

echo "✅ Pilot test PASSED. Reports generated:"
echo "   - JSON: $PILOT_JSON"
ls -lh phase2_validated_results_*.md | head -1
echo ""

# Step 3: Full execution (20 strategies)
echo "[Step 3/5] Running full execution (20 strategies)..."
echo "This will take 60-120 minutes. Start time: $(date)"
echo "You can monitor progress with: tail -f phase2_full_with_validation.log"
echo ""

python3 run_phase2_with_validation.py --timeout 420 2>&1 | tee phase2_full_with_validation.log
echo "Full execution complete: $(date)"
echo ""

# Check execution results
if [ $? -ne 0 ]; then
    echo "❌ Full execution FAILED. Check phase2_full_with_validation.log for errors."
    exit 1
fi

# Step 4: Results analysis
echo "[Step 4/5] Analyzing results..."
FULL_JSON=$(ls -t phase2_validated_results_*.json 2>/dev/null | head -1)

if [ -z "$FULL_JSON" ]; then
    echo "❌ Full execution reports not generated."
    exit 1
fi

echo "✅ Full execution PASSED. Reports generated:"
echo "   - JSON: $FULL_JSON"
ls -lh phase2_validated_results_*.md | head -1
echo ""

# Extract key metrics using jq (if available) or Python
echo "Extracting key metrics..."
python3 <<EOF
import json

with open('$FULL_JSON', 'r') as f:
    report = json.load(f)

print("=" * 60)
print("EXECUTION SUMMARY")
print("=" * 60)
print(f"Total Strategies:      {report.get('summary', {}).get('total', 'N/A')}")
print(f"Successfully Executed: {report.get('summary', {}).get('successful', 'N/A')}")
print(f"Level 3 (Profitable):  {report.get('summary', {}).get('level_3_profitable', 'N/A')}")

if 'validation_statistics' in report:
    val_stats = report['validation_statistics']
    print(f"\nVALIDATION STATISTICS (v1.1)")
    print(f"Total Validated:       {val_stats.get('total_validated', 'N/A')}")
    print(f"Validation Rate:       {val_stats.get('validation_rate', 0) * 100:.1f}%")
    print(f"Dynamic Threshold:     {report.get('dynamic_threshold', 'N/A')}")

if 'metrics' in report:
    metrics = report['metrics']
    print(f"\nPERFORMANCE METRICS")
    print(f"Avg Sharpe Ratio:      {metrics.get('avg_sharpe', 'N/A')}")
    print(f"Avg Return:            {metrics.get('avg_return', 'N/A')}")
    print(f"Avg Max Drawdown:      {metrics.get('avg_max_drawdown', 'N/A')}")

print("=" * 60)
EOF

echo ""

# Step 5: Generate summary report
echo "[Step 5/5] Generating summary report..."
echo "See: TASK_7.2_COMPLETION_SUMMARY.md"
echo ""

echo "=============================================="
echo "Task 7.2 Execution Complete!"
echo "Completion time: $(date)"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Review phase2_full_with_validation.log for details"
echo "2. Check $FULL_JSON for full results"
echo "3. Analyze TASK_7.2_COMPLETION_SUMMARY.md"
echo "4. Decide on Phase 3 readiness"
echo ""
