#!/bin/bash
# Quick Test Script for Sandbox Deployment
# Runs a short evolution test (1-2 hours) to verify stability before full 1-week run

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/sandbox_output_test"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Sandbox Quick Test (1-2 hours)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test configuration
POPULATION_SIZE=50  # Smaller for faster testing
TEST_GENERATIONS=100  # Approximately 1-2 hours depending on hardware

echo "Test Configuration:"
echo "  Population: $POPULATION_SIZE individuals"
echo "  Generations: $TEST_GENERATIONS"
echo "  Output: $OUTPUT_DIR"
echo "  Estimated time: 1-2 hours"
echo ""

read -p "Start test run? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Test cancelled"
    exit 0
fi

echo ""
echo -e "${YELLOW}Starting test run...${NC}"
echo ""

# Run test
python3 "${SCRIPT_DIR}/sandbox_deployment.py" \
    --population-size "$POPULATION_SIZE" \
    --max-generations "$TEST_GENERATIONS" \
    --output-dir "$OUTPUT_DIR" \
    --test

TEST_RESULT=$?

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Test Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ Test completed successfully${NC}"
    echo ""

    # Show summary
    echo "Test Results Summary:"
    echo ""

    # Count metrics files
    METRICS_COUNT=$(ls "${OUTPUT_DIR}/metrics"/metrics_json_gen_*.json 2>/dev/null | wc -l)
    echo "  Metrics files: $METRICS_COUNT"

    # Count checkpoints
    CHECKPOINT_COUNT=$(ls "${OUTPUT_DIR}/checkpoints"/checkpoint_gen_*.json 2>/dev/null | wc -l)
    echo "  Checkpoints: $CHECKPOINT_COUNT"

    # Count alerts
    if [ -f "${OUTPUT_DIR}/alerts/alerts.json" ]; then
        ALERT_COUNT=$(python3 -c "import json; print(len(json.load(open('${OUTPUT_DIR}/alerts/alerts.json'))))" 2>/dev/null || echo "0")
        echo "  Total alerts: $ALERT_COUNT"

        # Critical alerts
        CRITICAL_COUNT=$(python3 -c "import json; print(sum(1 for a in json.load(open('${OUTPUT_DIR}/alerts/alerts.json')) if a.get('severity') == 'critical'))" 2>/dev/null || echo "0")
        if [ "$CRITICAL_COUNT" -gt 0 ]; then
            echo -e "  ${YELLOW}⚠ Critical alerts: $CRITICAL_COUNT${NC}"
        else
            echo "  Critical alerts: 0"
        fi
    fi

    echo ""

    # Get final metrics
    LATEST_METRICS=$(ls -t "${OUTPUT_DIR}/metrics"/metrics_json_gen_*.json 2>/dev/null | head -1)
    if [ -n "$LATEST_METRICS" ]; then
        echo "Final Generation Metrics:"
        python3 -c "
import json
with open('$LATEST_METRICS', 'r') as f:
    data = json.load(f)

summary = data.get('summary', {})
if summary:
    print(f\"  Generation: {summary.get('current_generation', 'N/A')}\")
    print(f\"  Best fitness: {summary.get('best_fitness', 'N/A'):.4f}\")
    print(f\"  Avg fitness: {summary.get('avg_fitness', 'N/A'):.4f}\")
    print(f\"  Diversity: {summary.get('diversity', 'N/A'):.4f}\")
    print(f\"  Champion template: {summary.get('champion_template', 'N/A')}\")
" 2>/dev/null || echo "  (Unable to parse metrics)"
    fi

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  System is ready for full deployment${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "To start 1-week run:"
    echo "  ./start_sandbox.sh"
    echo ""
    echo "Test output saved in: $OUTPUT_DIR"
    echo ""

else
    echo -e "${RED}✗ Test failed${NC}"
    echo ""
    echo "Check logs for errors:"
    echo "  ${OUTPUT_DIR}/sandbox_evolution.log"
    echo ""
    echo "Fix issues before attempting full deployment"
    echo ""
    exit 1
fi
