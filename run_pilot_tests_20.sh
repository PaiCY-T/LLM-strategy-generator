#!/bin/bash
# Pilot Test Execution Script - 20 Iterations Each
# Runs three experimental groups: LLM-Only, Factor Graph Only, Hybrid
# After Phase 3.3 dict interface fix

echo "========================================================================"
echo "Pilot Test Execution - 20 Iterations Per Group"
echo "========================================================================"
echo ""
echo "Experimental Groups:"
echo "  1. LLM-Only (100% LLM innovation)"
echo "  2. Factor Graph Only (0% LLM - baseline)"
echo "  3. Hybrid (30% LLM + 70% Factor Graph)"
echo ""
echo "Testing Phase 3.3 dict interface fix for Phase 7 E2E unblocking"
echo "========================================================================"
echo ""

# Navigate to project root
cd "$(dirname "$0")"

# Create results directory
mkdir -p experiments/llm_learning_validation/results

# Timestamp for this run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="experiments/llm_learning_validation/results/pilot_run_${TIMESTAMP}"
mkdir -p "$LOG_DIR"

echo "Log directory: $LOG_DIR"
echo ""

# Function to run a single pilot test
run_pilot() {
    local CONFIG_FILE=$1
    local TEST_NAME=$2
    local LOG_FILE="${LOG_DIR}/${TEST_NAME}.log"

    echo "========================================================================"
    echo "Running: $TEST_NAME"
    echo "Config: $CONFIG_FILE"
    echo "Log: $LOG_FILE"
    echo "========================================================================"

    # Run the test
    python3 experiments/llm_learning_validation/orchestrator.py \
        --config "$CONFIG_FILE" \
        --phase pilot \
        2>&1 | tee "$LOG_FILE"

    # Check exit status
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "✅ $TEST_NAME COMPLETED SUCCESSFULLY"
    else
        echo "❌ $TEST_NAME FAILED"
        return 1
    fi

    echo ""
    return 0
}

# Track overall success
TOTAL_TESTS=3
PASSED_TESTS=0

echo ""
echo "========================================================================"
echo "TEST 1/3: LLM-Only Mode"
echo "========================================================================"
if run_pilot "experiments/llm_learning_validation/config_pilot_llm_only_20.yaml" "pilot_llm_only_20"; then
    ((PASSED_TESTS++))
fi

echo ""
echo "========================================================================"
echo "TEST 2/3: Factor Graph Only Mode"
echo "========================================================================"
if run_pilot "experiments/llm_learning_validation/config_pilot_fg_only_20.yaml" "pilot_fg_only_20"; then
    ((PASSED_TESTS++))
fi

echo ""
echo "========================================================================"
echo "TEST 3/3: Hybrid Mode"
echo "========================================================================"
if run_pilot "experiments/llm_learning_validation/config_pilot_hybrid_20.yaml" "pilot_hybrid_20"; then
    ((PASSED_TESTS++))
fi

# Summary
echo ""
echo "========================================================================"
echo "Pilot Test Execution Summary"
echo "========================================================================"
echo "Tests Passed: $PASSED_TESTS / $TOTAL_TESTS"
echo "Logs saved to: $LOG_DIR"
echo ""

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo "✅ ALL PILOT TESTS PASSED!"
    echo ""
    echo "Next Steps:"
    echo "  1. Review results in: experiments/llm_learning_validation/results/"
    echo "  2. Check logs in: $LOG_DIR"
    echo "  3. Update IMPLEMENTATION_STATUS.md - Mark Phase 7 as UNBLOCKED"
    echo "  4. Run analysis: python3 experiments/llm_learning_validation/orchestrator.py --analyze pilot"
    exit 0
else
    echo "⚠️  Some tests failed: $((TOTAL_TESTS - PASSED_TESTS)) / $TOTAL_TESTS"
    echo ""
    echo "Check logs for details: $LOG_DIR"
    exit 1
fi
