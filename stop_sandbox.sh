#!/bin/bash
# Stop Sandbox Evolution and Monitoring

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/sandbox_output"
EVOLUTION_PID_FILE="${OUTPUT_DIR}/evolution.pid"
MONITOR_PID_FILE="${OUTPUT_DIR}/monitor.pid"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Stopping Sandbox Evolution...${NC}"
echo ""

# Stop evolution process
if [ -f "$EVOLUTION_PID_FILE" ]; then
    EVOLUTION_PID=$(cat "$EVOLUTION_PID_FILE")

    if ps -p "$EVOLUTION_PID" > /dev/null 2>&1; then
        echo "Stopping evolution process (PID: $EVOLUTION_PID)..."

        # Send SIGTERM for graceful shutdown
        kill -TERM "$EVOLUTION_PID" 2>/dev/null

        # Wait up to 30 seconds for graceful shutdown
        for i in {1..30}; do
            if ! ps -p "$EVOLUTION_PID" > /dev/null 2>&1; then
                echo -e "${GREEN}✓ Evolution stopped gracefully${NC}"
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if ps -p "$EVOLUTION_PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}Process still running, forcing termination...${NC}"
            kill -9 "$EVOLUTION_PID" 2>/dev/null
            sleep 1

            if ps -p "$EVOLUTION_PID" > /dev/null 2>&1; then
                echo -e "${RED}✗ Failed to stop evolution process${NC}"
            else
                echo -e "${GREEN}✓ Evolution process terminated${NC}"
            fi
        fi

        rm -f "$EVOLUTION_PID_FILE"
    else
        echo "Evolution process not running (stale PID file)"
        rm -f "$EVOLUTION_PID_FILE"
    fi
else
    echo "No evolution PID file found"
fi

echo ""

# Stop monitor process
if [ -f "$MONITOR_PID_FILE" ]; then
    MONITOR_PID=$(cat "$MONITOR_PID_FILE")

    if ps -p "$MONITOR_PID" > /dev/null 2>&1; then
        echo "Stopping monitor process (PID: $MONITOR_PID)..."
        kill -TERM "$MONITOR_PID" 2>/dev/null
        sleep 1

        if ! ps -p "$MONITOR_PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Monitor stopped${NC}"
        else
            kill -9 "$MONITOR_PID" 2>/dev/null
            echo -e "${GREEN}✓ Monitor terminated${NC}"
        fi

        rm -f "$MONITOR_PID_FILE"
    else
        echo "Monitor process not running (stale PID file)"
        rm -f "$MONITOR_PID_FILE"
    fi
else
    echo "No monitor PID file found"
fi

echo ""
echo -e "${GREEN}Sandbox deployment stopped${NC}"
echo ""
echo "Output preserved in: $OUTPUT_DIR"
echo ""
