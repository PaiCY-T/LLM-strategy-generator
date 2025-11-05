#!/bin/bash
# Start Sandbox Evolution with Monitoring
# This script starts the evolution and monitoring processes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/sandbox_output"
PID_FILE="${OUTPUT_DIR}/evolution.pid"
LOG_FILE="${OUTPUT_DIR}/logs/evolution.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Sandbox Evolution Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Create necessary directories
mkdir -p "${OUTPUT_DIR}/logs"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}Evolution is already running (PID: $PID)${NC}"
        echo "Use './stop_sandbox.sh' to stop it first"
        exit 1
    else
        echo "Removing stale PID file..."
        rm -f "$PID_FILE"
    fi
fi

# Parse arguments
TEST_MODE=""
POPULATION_SIZE=100
MAX_GENERATIONS=1000

while [[ $# -gt 0 ]]; do
    case $1 in
        --test)
            TEST_MODE="--test"
            echo -e "${YELLOW}Running in TEST MODE (limited generations)${NC}"
            shift
            ;;
        --population-size)
            POPULATION_SIZE="$2"
            shift 2
            ;;
        --max-generations)
            MAX_GENERATIONS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--test] [--population-size N] [--max-generations N]"
            exit 1
            ;;
    esac
done

echo "Configuration:"
echo "  Population size: $POPULATION_SIZE"
echo "  Max generations: $MAX_GENERATIONS"
echo "  Test mode: ${TEST_MODE:-No}"
echo "  Output directory: $OUTPUT_DIR"
echo ""

# Start evolution in background
echo "Starting evolution process..."

cd "$SCRIPT_DIR"

nohup python3 sandbox_deployment.py \
    --population-size "$POPULATION_SIZE" \
    --max-generations "$MAX_GENERATIONS" \
    --output-dir "$OUTPUT_DIR" \
    $TEST_MODE \
    > "$LOG_FILE" 2>&1 &

EVOLUTION_PID=$!
echo $EVOLUTION_PID > "$PID_FILE"

echo -e "${GREEN}✓ Evolution started (PID: $EVOLUTION_PID)${NC}"
echo "  Log file: $LOG_FILE"
echo ""

# Wait a moment for process to initialize
sleep 3

# Check if still running
if ! ps -p "$EVOLUTION_PID" > /dev/null 2>&1; then
    echo -e "${RED}✗ Evolution process failed to start${NC}"
    echo "Check log file: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi

echo -e "${GREEN}✓ Evolution process is running${NC}"
echo ""

# Start monitoring in background
echo "Starting monitoring process..."

chmod +x "${SCRIPT_DIR}/sandbox_monitor.sh"

nohup "${SCRIPT_DIR}/sandbox_monitor.sh" monitor \
    > "${OUTPUT_DIR}/logs/monitor.log" 2>&1 &

MONITOR_PID=$!
echo $MONITOR_PID > "${OUTPUT_DIR}/monitor.pid"

echo -e "${GREEN}✓ Monitoring started (PID: $MONITOR_PID)${NC}"
echo "  Monitor log: ${OUTPUT_DIR}/logs/monitor.log"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Started Successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Evolution PID: $EVOLUTION_PID"
echo "Monitor PID: $MONITOR_PID"
echo ""
echo "To monitor progress:"
echo "  tail -f $LOG_FILE"
echo "  tail -f ${OUTPUT_DIR}/logs/monitor.log"
echo ""
echo "To check status:"
echo "  ./sandbox_monitor.sh check"
echo ""
echo "To stop:"
echo "  ./stop_sandbox.sh"
echo ""
