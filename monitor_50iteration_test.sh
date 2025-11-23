#!/bin/bash
count=0
while true; do
    sleep 120  # Check every 2 minutes
    echo "=== Progress Check $(date +%H:%M:%S) ==="
    
    # Check Factor Graph progress
    if [ -f experiments/llm_learning_validation/results/fg_only_50/innovations.jsonl ]; then
        fg_count=$(wc -l < experiments/llm_learning_validation/results/fg_only_50/innovations.jsonl 2>/dev/null || echo "0")
        echo "Factor Graph: $fg_count/50 iterations"
    else
        echo "Factor Graph: 0/50 iterations (not started)"
    fi
    
    # Check LLM Only progress  
    if [ -f experiments/llm_learning_validation/results/llm_only_50/innovations.jsonl ]; then
        llm_count=$(wc -l < experiments/llm_learning_validation/results/llm_only_50/innovations.jsonl 2>/dev/null || echo "0")
        echo "LLM Only: $llm_count/50 iterations"
    else
        echo "LLM Only: Not started yet"
    fi
    
    # Check Hybrid progress
    if [ -f experiments/llm_learning_validation/results/hybrid_50/innovations.jsonl ]; then
        hybrid_count=$(wc -l < experiments/llm_learning_validation/results/hybrid_50/innovations.jsonl 2>/dev/null || echo "0")
        echo "Hybrid: $hybrid_count/50 iterations"
    else
        echo "Hybrid: Not started yet"
    fi
    
    echo ""
    
    # Check if test completed
    result_files=$(ls experiments/llm_learning_validation/results/50iteration_three_mode/results_*.json 2>/dev/null | wc -l)
    if [ "$result_files" -gt 0 ]; then
        echo "✅ Test completed!"
        echo ""
        echo "Final Results:"
        cat experiments/llm_learning_validation/results/50iteration_three_mode/results_*.json
        break
    fi
    
    # Max 25 checks (50 minutes)
    count=$((count + 1))
    if [ $count -ge 25 ]; then
        echo "⚠️ Monitoring timeout (50 minutes reached)"
        break
    fi
done
