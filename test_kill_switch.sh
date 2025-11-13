#!/bin/bash
# Kill Switch Integration Test Script

echo "======================================================================"
echo "KILL SWITCH INTEGRATION TESTS"
echo "======================================================================"

cd /mnt/c/Users/jnpi/Documents/finlab/LLM-strategy-generator

# Test 1: Kill switch OFF (legacy behavior)
echo ""
echo "TEST 1: Kill switch OFF (legacy behavior)"
echo "----------------------------------------------------------------------"
export ENABLE_GENERATION_REFACTORING=false
export PHASE1_CONFIG_ENFORCEMENT=false

python3 - <<'EOF'
import sys
sys.path.insert(0, 'src')
from unittest.mock import MagicMock
from src.learning.iteration_executor import IterationExecutor
from src.learning.exceptions import ConfigurationConflictError

# Create executor
config = {"use_factor_graph": True, "innovation_rate": 100}
mock_llm = MagicMock()
mock_llm.is_enabled.return_value = True
mock_deps = {
    "llm_client": mock_llm,
    "feedback_generator": MagicMock(),
    "backtest_executor": MagicMock(),
    "champion_tracker": MagicMock(),
    "history": MagicMock(),
    "config": config,
    "data": MagicMock(),
    "sim": MagicMock(),
}
executor = IterationExecutor(**mock_deps)

# Test that conflicting config does NOT raise error (legacy behavior)
try:
    result = executor._decide_generation_method()
    print(f"✅ PASSED: Legacy behavior - no conflict error, returned {result}")
except ConfigurationConflictError:
    print("❌ FAILED: Legacy mode should NOT raise ConfigurationConflictError")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ Test 1 FAILED"
    exit 1
fi

# Test 2: Kill switch PARTIAL (Phase 1 disabled)
echo ""
echo "TEST 2: Kill switch PARTIAL (ENABLE_GENERATION_REFACTORING=true, PHASE1_CONFIG_ENFORCEMENT=false)"
echo "----------------------------------------------------------------------"
export ENABLE_GENERATION_REFACTORING=true
export PHASE1_CONFIG_ENFORCEMENT=false

python3 - <<'EOF'
import sys
sys.path.insert(0, 'src')
from unittest.mock import MagicMock
from src.learning.iteration_executor import IterationExecutor
from src.learning.exceptions import ConfigurationConflictError

# Create executor
config = {"use_factor_graph": True, "innovation_rate": 100}
mock_llm = MagicMock()
mock_llm.is_enabled.return_value = True
mock_deps = {
    "llm_client": mock_llm,
    "feedback_generator": MagicMock(),
    "backtest_executor": MagicMock(),
    "champion_tracker": MagicMock(),
    "history": MagicMock(),
    "config": config,
    "data": MagicMock(),
    "sim": MagicMock(),
}
executor = IterationExecutor(**mock_deps)

# Should use legacy behavior
try:
    result = executor._decide_generation_method()
    print(f"✅ PASSED: Legacy behavior active - no conflict error, returned {result}")
except ConfigurationConflictError:
    print("❌ FAILED: Should use legacy behavior when PHASE1_CONFIG_ENFORCEMENT=false")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ Test 2 FAILED"
    exit 1
fi

# Test 3: Kill switch ON (Phase 1 active)
echo ""
echo "TEST 3: Kill switch ON (Phase 1 active)"
echo "----------------------------------------------------------------------"
export ENABLE_GENERATION_REFACTORING=true
export PHASE1_CONFIG_ENFORCEMENT=true

python3 - <<'EOF'
import sys
sys.path.insert(0, 'src')
from unittest.mock import MagicMock
from src.learning.iteration_executor import IterationExecutor
from src.learning.exceptions import ConfigurationConflictError

# Create executor
config = {"use_factor_graph": True, "innovation_rate": 100}
mock_llm = MagicMock()
mock_llm.is_enabled.return_value = True
mock_deps = {
    "llm_client": mock_llm,
    "feedback_generator": MagicMock(),
    "backtest_executor": MagicMock(),
    "champion_tracker": MagicMock(),
    "history": MagicMock(),
    "config": config,
    "data": MagicMock(),
    "sim": MagicMock(),
}
executor = IterationExecutor(**mock_deps)

# Should detect conflicts
try:
    executor._decide_generation_method()
    print("❌ FAILED: Expected ConfigurationConflictError with Phase 1 active")
    sys.exit(1)
except ConfigurationConflictError as e:
    print(f"✅ PASSED: Phase 1 behavior active - conflict error raised: {e}")
EOF

if [ $? -ne 0 ]; then
    echo "❌ Test 3 FAILED"
    exit 1
fi

# Summary
echo ""
echo "======================================================================"
echo "KILL SWITCH TEST SUMMARY"
echo "======================================================================"
echo "✅ All 3 kill switch tests PASSED"
echo ""
echo "Tests:"
echo "  1. Kill switch OFF (legacy) - ✅ PASSED"
echo "  2. Kill switch PARTIAL (Phase 1 disabled) - ✅ PASSED"
echo "  3. Kill switch ON (Phase 1 active) - ✅ PASSED"
