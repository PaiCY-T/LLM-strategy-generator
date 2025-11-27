#!/bin/bash
# Phase 3 & 4 Completion Verification Script

echo "=================================="
echo "Phase 3 & 4 Completion Verification"
echo "=================================="
echo ""

# Test execution
echo "1. Running critical component tests..."
python3 -m pytest tests/integration/test_tpe_template_integration.py \
                 tests/integration/test_runtime_ttpt_monitor.py \
                 tests/integration/test_experiment_tracker.py \
                 -v --tb=short -q 2>&1 | tail -10

echo ""
echo "2. Checking documentation..."
for doc in "docs/PHASE_3_4_COMPLETION_SUMMARY.md" \
           "PHASE_3_4_EXECUTIVE_SUMMARY.md" \
           "docs/QUICK_START_GUIDE_PHASE3_4.md"; do
    if [ -f "$doc" ]; then
        echo "✅ $doc exists ($(wc -l < "$doc") lines)"
    else
        echo "❌ $doc missing"
    fi
done

echo ""
echo "3. Verifying component implementations..."
for impl in "src/learning/optimizer.py" \
            "src/validation/ttpt_framework.py" \
            "src/validation/runtime_ttpt_monitor.py" \
            "src/tracking/experiment_tracker.py"; do
    if [ -f "$impl" ]; then
        echo "✅ $impl exists"
    else
        echo "❌ $impl missing"
    fi
done

echo ""
echo "4. README.md update check..."
if grep -q "Phase 3 & 4 Advanced Features Complete" README.md; then
    echo "✅ README.md updated with Phase 3 & 4 features"
else
    echo "❌ README.md not updated"
fi

echo ""
echo "=================================="
echo "Verification Complete"
echo "=================================="
