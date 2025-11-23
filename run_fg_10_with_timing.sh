#!/bin/bash
# Factor Graph 10轮测试 - 计时脚本

echo "================================================================================"
echo "Factor Graph 10轮测试 - 详细计时"
echo "================================================================================"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 清理旧的结果文件
rm -rf experiments/llm_learning_validation/results/fg_only_10
mkdir -p experiments/llm_learning_validation/results/fg_only_10

# 记录总开始时间
TOTAL_START=$(date +%s)

# innovations文件路径
INNOVATIONS_FILE="experiments/llm_learning_validation/results/fg_only_10/innovations.jsonl"

# 创建临时文件记录每轮时间
TIMING_LOG="experiments/llm_learning_validation/results/fg_only_10/timing.log"
echo "轮次,开始时间,结束时间,耗时(秒),状态" > "$TIMING_LOG"

# 后台监控脚本
{
    LAST_COUNT=0
    ITER_START=$(date +%s)

    while true; do
        sleep 5  # 每5秒检查一次

        if [ -f "$INNOVATIONS_FILE" ]; then
            CURRENT_COUNT=$(wc -l < "$INNOVATIONS_FILE")

            if [ "$CURRENT_COUNT" -gt "$LAST_COUNT" ]; then
                # 新的迭代完成了
                ITER_END=$(date +%s)
                DURATION=$((ITER_END - ITER_START))

                echo "$CURRENT_COUNT,$(date -d @$ITER_START '+%H:%M:%S'),$(date -d @$ITER_END '+%H:%M:%S'),$DURATION,success" >> "$TIMING_LOG"
                echo "第 $CURRENT_COUNT/10 轮完成 - 耗时: ${DURATION}秒"

                LAST_COUNT=$CURRENT_COUNT
                ITER_START=$(date +%s)

                # 如果完成10轮，退出监控
                if [ "$CURRENT_COUNT" -ge 10 ]; then
                    break
                fi
            fi
        fi

        # 超时保护 (30分钟)
        ELAPSED=$(($(date +%s) - TOTAL_START))
        if [ "$ELAPSED" -gt 1800 ]; then
            echo "测试超时 (30分钟)"
            break
        fi
    done
} &
MONITOR_PID=$!

# 运行测试
echo "运行Factor Graph 10轮测试..."
echo "配置文件: experiments/llm_learning_validation/config_fg_only_10.yaml"
echo ""

cd experiments/llm_learning_validation
python3 << 'PYTHON_SCRIPT'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent.parent))

from src.learning.learning_loop import LearningLoop

try:
    loop = LearningLoop("config_fg_only_10.yaml")
    loop.run()
except Exception as e:
    print(f"测试出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

TEST_EXIT_CODE=$?
cd ../..

# 等待监控脚本完成
wait $MONITOR_PID 2>/dev/null

# 计算总耗时
TOTAL_END=$(date +%s)
TOTAL_DURATION=$((TOTAL_END - TOTAL_START))

# 打印结果
echo ""
echo "================================================================================"
echo "测试完成"
echo "================================================================================"
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "总耗时: ${TOTAL_DURATION}秒 ($((TOTAL_DURATION / 60))分$((TOTAL_DURATION % 60))秒)"
echo ""

# 打印详细统计
if [ -f "$TIMING_LOG" ]; then
    echo "每轮详细时间:"
    echo "----------------------------------------"
    cat "$TIMING_LOG"
    echo "----------------------------------------"

    # 计算统计数据
    SUCCESS_COUNT=$(grep -c "success" "$TIMING_LOG" || echo "0")
    if [ "$SUCCESS_COUNT" -gt 0 ]; then
        AVG_TIME=$(awk -F',' 'NR>1 && $5=="success" {sum+=$4; count++} END {if(count>0) print int(sum/count); else print 0}' "$TIMING_LOG")
        MIN_TIME=$(awk -F',' 'NR>1 && $5=="success" {if(min=="" || $4<min) min=$4} END {print min+0}' "$TIMING_LOG")
        MAX_TIME=$(awk -F',' 'NR>1 && $5=="success" {if($4>max) max=$4} END {print max+0}' "$TIMING_LOG")

        echo ""
        echo "统计汇总:"
        echo "  成功轮数: $SUCCESS_COUNT"
        echo "  平均耗时: ${AVG_TIME}秒"
        echo "  最快: ${MIN_TIME}秒"
        echo "  最慢: ${MAX_TIME}秒"
    fi
fi

echo "================================================================================"

exit $TEST_EXIT_CODE
