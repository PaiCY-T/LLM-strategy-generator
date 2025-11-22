#!/bin/bash
# 实时监控 post-fix 验证测试进度

echo "================================================================================================"
echo "POST-FIX VALIDATION TEST - Real-time Monitor"
echo "================================================================================================"
echo "修复验证测试监控"
echo "预期改善: LLM Only 0% → 80%+, Hybrid 44% → 70%+"
echo "================================================================================================"
echo

count=0
while true; do
    clear
    echo "================================================================================================"
    echo "POST-FIX VALIDATION TEST - Progress Monitor"
    echo "================================================================================================"
    echo "检查时间: $(date '+%H:%M:%S')"
    echo

    # Factor Graph Only 进度
    if [ -f experiments/llm_learning_validation/results/fg_only_20/innovations.jsonl ]; then
        fg_count=$(wc -l < experiments/llm_learning_validation/results/fg_only_20/innovations.jsonl)
        fg_progress=$((fg_count * 100 / 20))
        echo "📊 Factor Graph Only: $fg_count/20 完成 (${fg_progress}%)"
        
        # 显示最后一轮结果
        if [ -f experiments/llm_learning_validation/results/fg_only_20/innovations.jsonl ]; then
            last_result=$(tail -1 experiments/llm_learning_validation/results/fg_only_20/innovations.jsonl | jq -r '.classification // "N/A"')
            echo "   最后一轮: $last_result"
        fi
    else
        echo "📊 Factor Graph Only: 尚未开始"
    fi
    
    echo

    # LLM Only 进度
    if [ -f experiments/llm_learning_validation/results/llm_only_20/innovations.jsonl ]; then
        llm_count=$(wc -l < experiments/llm_learning_validation/results/llm_only_20/innovations.jsonl)
        llm_progress=$((llm_count * 100 / 20))
        echo "🤖 LLM Only: $llm_count/20 完成 (${llm_progress}%)"
        
        # 显示成功/失败统计
        if [ -f experiments/llm_learning_validation/results/llm_only_20/innovations.jsonl ]; then
            success_count=$(grep -c "LEVEL_3" experiments/llm_learning_validation/results/llm_only_20/innovations.jsonl || echo "0")
            fail_count=$(grep -c "LEVEL_0" experiments/llm_learning_validation/results/llm_only_20/innovations.jsonl || echo "0")
            if [ $llm_count -gt 0 ]; then
                success_rate=$((success_count * 100 / llm_count))
                echo "   成功率: ${success_rate}% (成功: $success_count, 失败: $fail_count)"
            fi
        fi
    else
        echo "🤖 LLM Only: 尚未开始"
    fi
    
    echo

    # Hybrid 进度
    if [ -f experiments/llm_learning_validation/results/hybrid_20/innovations.jsonl ]; then
        hybrid_count=$(wc -l < experiments/llm_learning_validation/results/hybrid_20/innovations.jsonl)
        hybrid_progress=$((hybrid_count * 100 / 20))
        echo "🔀 Hybrid: $hybrid_count/20 完成 (${hybrid_progress}%)"
        
        # 显示成功/失败统计
        if [ -f experiments/llm_learning_validation/results/hybrid_20/innovations.jsonl ]; then
            success_count=$(grep -c "LEVEL_3" experiments/llm_learning_validation/results/hybrid_20/innovations.jsonl || echo "0")
            fail_count=$(grep -c "LEVEL_0" experiments/llm_learning_validation/results/hybrid_20/innovations.jsonl || echo "0")
            if [ $hybrid_count -gt 0 ]; then
                success_rate=$((success_count * 100 / hybrid_count))
                echo "   成功率: ${success_rate}% (成功: $success_count, 失败: $fail_count)"
            fi
        fi
    else
        echo "🔀 Hybrid: 尚未开始"
    fi

    echo
    echo "================================================================================================"
    
    # 检查是否完成
    result_files=$(ls experiments/llm_learning_validation/results/20iteration_three_mode/results_*.json 2>/dev/null | wc -l)
    if [ "$result_files" -gt 0 ]; then
        echo "✅ 测试已完成！"
        echo
        echo "结果文件:"
        ls -lth experiments/llm_learning_validation/results/20iteration_three_mode/results_*.json | head -1
        break
    fi
    
    # 每60秒更新一次
    sleep 60
    
    count=$((count + 1))
    if [ $count -ge 60 ]; then
        echo "⏰ 监控超时 (60分钟)"
        break
    fi
done

echo
echo "监控结束"
