#!/bin/bash
# Phase 2: Low Innovation Rate Test
# ==================================
# Enable LLM innovation with 5% rate for cautious testing
# 20 generations to validate Stage 2 breakthrough potential

set -e

echo "════════════════════════════════════════════════════════════════"
echo "PHASE 2: Flash Lite Low Innovation Rate Test"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Configuration:"
echo "  Model: gemini-2.5-flash-lite"
echo "  Innovation Rate: 5% (1/20 iterations)"
echo "  Generations: 20"
echo "  Champion Updates: ENABLED (real test)"
echo "  Current Champion: 2.4751 Sharpe"
echo ""
echo "Expected Results:"
echo "  - 1 LLM strategy (5% × 20 = 1)"
echo "  - 19 Factor Graph strategies"
echo "  - LLM success rate: 80%"
echo "  - Diversity: >40%"
echo "  - Champion: May improve beyond 2.4751"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check API key
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ ERROR: GOOGLE_API_KEY not set"
    echo ""
    echo "Set with:"
    echo "  export GOOGLE_API_KEY=your_api_key"
    exit 1
fi

echo "✅ GOOGLE_API_KEY is set"
echo ""

# Set LLM configuration via environment variables
export LLM_ENABLED=true
export LLM_PROVIDER=gemini
export INNOVATION_RATE=0.05  # 5% innovation rate

echo "🔧 Environment Configuration:"
echo "  LLM_ENABLED=$LLM_ENABLED"
echo "  LLM_PROVIDER=$LLM_PROVIDER"
echo "  INNOVATION_RATE=$INNOVATION_RATE"
echo ""

# Backup current Champion
echo "💾 Backing up current Champion..."
if [ -f "artifacts/data/champion_strategy.json" ]; then
    cp artifacts/data/champion_strategy.json \
       artifacts/data/champion_strategy_backup_phase2_$(date +%Y%m%d_%H%M%S).json
    echo "✅ Champion backed up"
else
    echo "⚠️  No existing Champion found"
fi
echo ""

# Run autonomous loop
echo "🚀 Starting Phase 2 Test..."
echo "════════════════════════════════════════════════════════════════"
echo ""

python3 artifacts/working/modules/autonomous_loop.py \
    --max-iterations 20 \
    --history-file artifacts/data/phase2_flashlite_history.jsonl

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "PHASE 2 COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Results saved to:"
echo "  - artifacts/data/phase2_flashlite_history.jsonl"
echo "  - artifacts/data/champion_strategy.json (updated)"
echo ""
echo "Next steps:"
echo "  1. Review Champion updates"
echo "  2. Analyze LLM strategy quality"
echo "  3. Check diversity metrics"
echo "  4. Decide on Phase 3 (20% rate, 50 gen)"
echo ""
