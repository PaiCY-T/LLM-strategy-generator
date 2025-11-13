#!/bin/bash
# 1週測試進度檢查腳本

OUTPUT_DIR="sandbox_output"
LOG_FILE="sandbox_week_test.log"
PID_FILE="sandbox_week_test.pid"

echo "========================================"
echo "  1週測試進度檢查"
echo "========================================"
echo ""

# 檢查進程
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ 測試進程運行中 (PID: $PID)"
        ps aux | grep "$PID" | grep -v grep | awk '{printf "   CPU: %s%% | MEM: %.1fMB | Runtime: %s\n", $3, $6/1024, $10}'
    else
        echo "❌ 測試進程已停止 (PID: $PID)"
        exit 1
    fi
else
    echo "⚠️  找不到PID文件"
fi

echo ""

# 檢查最新代數
if [ -d "$OUTPUT_DIR/metrics" ]; then
    LATEST_METRICS=$(ls -t "$OUTPUT_DIR/metrics"/metrics_json_gen_*.json 2>/dev/null | head -1)
    if [ -n "$LATEST_METRICS" ]; then
        CURRENT_GEN=$(basename "$LATEST_METRICS" | sed 's/metrics_json_gen_//' | sed 's/.json//')
        PROGRESS=$((CURRENT_GEN * 100 / 1000))
        echo "📊 當前進度: Generation $CURRENT_GEN / 1000 (${PROGRESS}%)"

        # 顯示最新指標
        echo ""
        echo "最新指標 (Gen $CURRENT_GEN):"
        python3 -c "
import json
try:
    with open('$LATEST_METRICS') as f:
        data = json.load(f)
    history = data.get('generation_history', [])
    if history:
        latest = history[-1]
        print(f\"  平均適應度: {latest['avg_fitness']:.4f}\")
        print(f\"  最佳適應度: {latest['best_fitness']:.4f}\")
        print(f\"  多樣性: {latest['unified_diversity']:.4f}\")
        print(f\"  冠軍模板: {latest['champion_template']}\")

        # 模板分佈
        if 'template_distribution' in latest:
            print(f\"  模板分佈:\")
            for tmpl, pct in sorted(latest['template_distribution'].items(), key=lambda x: -x[1]):
                print(f\"    - {tmpl}: {pct*100:.1f}%\")
except Exception as e:
    print(f\"  無法解析指標: {e}\")
" 2>/dev/null || echo "  (解析失敗)"
    else
        echo "⏳ 等待第一個指標文件..."
    fi
else
    echo "⏳ 輸出目錄尚未創建"
fi

echo ""

# 檢查文件數量
if [ -d "$OUTPUT_DIR" ]; then
    METRICS_COUNT=$(ls "$OUTPUT_DIR/metrics"/*.json 2>/dev/null | wc -l)
    CHECKPOINT_COUNT=$(ls "$OUTPUT_DIR/checkpoints"/*.json 2>/dev/null | wc -l)

    echo "📁 輸出文件:"
    echo "   Metrics: $METRICS_COUNT"
    echo "   Checkpoints: $CHECKPOINT_COUNT"

    # 檢查警報
    if [ -f "$OUTPUT_DIR/alerts/alerts.json" ]; then
        ALERT_COUNT=$(python3 -c "import json; print(len(json.load(open('$OUTPUT_DIR/alerts/alerts.json'))))" 2>/dev/null || echo "0")
        if [ "$ALERT_COUNT" -gt 0 ]; then
            echo "   ⚠️  警報: $ALERT_COUNT"
        else
            echo "   警報: $ALERT_COUNT"
        fi
    fi
fi

echo ""

# 檢查最近錯誤
if [ -f "$LOG_FILE" ]; then
    ERROR_COUNT=$(grep -c "ERROR" "$LOG_FILE" 2>/dev/null || echo "0")
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "⚠️  日誌中發現 $ERROR_COUNT 個ERROR"
        echo "   最近錯誤:"
        grep "ERROR" "$LOG_FILE" | tail -3
    else
        echo "✅ 無錯誤記錄"
    fi
fi

echo ""

# 預估完成時間
if [ -n "$CURRENT_GEN" ] && [ "$CURRENT_GEN" -gt 0 ]; then
    if [ -f "$LOG_FILE" ]; then
        START_TIME=$(stat -c %Y "$LOG_FILE" 2>/dev/null || stat -f %B "$LOG_FILE" 2>/dev/null)
        CURRENT_TIME=$(date +%s)
        ELAPSED=$((CURRENT_TIME - START_TIME))

        if [ "$ELAPSED" -gt 0 ]; then
            TIME_PER_GEN=$((ELAPSED / CURRENT_GEN))
            REMAINING_GENS=$((1000 - CURRENT_GEN))
            REMAINING_TIME=$((REMAINING_GENS * TIME_PER_GEN))

            HOURS=$((REMAINING_TIME / 3600))
            MINUTES=$(((REMAINING_TIME % 3600) / 60))

            echo "⏱️  預估剩餘時間: ${HOURS}小時 ${MINUTES}分鐘"

            COMPLETION_DATE=$(date -d "+${REMAINING_TIME} seconds" "+%Y-%m-%d %H:%M" 2>/dev/null || date -v +${REMAINING_TIME}S "+%Y-%m-%d %H:%M" 2>/dev/null)
            echo "   預計完成: $COMPLETION_DATE"
        fi
    fi
fi

echo ""
echo "========================================"
