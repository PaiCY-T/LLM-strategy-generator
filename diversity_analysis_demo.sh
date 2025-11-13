#!/bin/bash
# Diversity Analysis Demonstration Script
# Task 3.2 - validation-framework-critical-fixes

echo "================================================================================"
echo "Diversity Analysis Script Demonstration (Task 3.2)"
echo "================================================================================"
echo ""

echo "Step 1: Display help information"
echo "--------------------------------"
python3 scripts/analyze_diversity.py --help
echo ""

echo "Step 2: Run basic diversity analysis"
echo "------------------------------------"
python3 scripts/analyze_diversity.py \
  --validation-results phase2_validated_results_20251101_060315.json \
  --output demo_diversity_report.md
echo ""

echo "Step 3: Display results summary"
echo "------------------------------"
if [ -f demo_diversity_report.json ]; then
    echo "JSON Report Contents:"
    python3 -c "
import json
with open('demo_diversity_report.json', 'r') as f:
    data = json.load(f)
    print(f\"  Total Strategies: {data['total_strategies']}\")
    print(f\"  Diversity Score: {data['diversity_score']:.1f}/100\")
    print(f\"  Recommendation: {data['recommendation']}\")
    print(f\"  Factor Diversity: {data['metrics']['factor_diversity']:.3f}\")
    print(f\"  Avg Correlation: {data['metrics']['avg_correlation']:.3f}\")
    print(f\"  Risk Diversity: {data['metrics']['risk_diversity']:.3f}\")
"
    echo ""
fi

echo "Step 4: List generated files"
echo "---------------------------"
ls -lh demo_diversity_report* 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""

echo "Step 5: Cleanup demo files"
echo "-------------------------"
rm -f demo_diversity_report*
echo "  Demo files cleaned up"
echo ""

echo "================================================================================"
echo "Demonstration Complete!"
echo "================================================================================"
