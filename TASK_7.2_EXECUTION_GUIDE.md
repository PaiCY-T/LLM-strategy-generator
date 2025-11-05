# Task 7.2 Execution Guide

**Purpose**: 獨立執行 Task 7.2，避免消耗 Claude context

---

## 快速執行

### 選項 A：使用自動化腳本（推薦）

```bash
cd /mnt/c/Users/jnpi/documents/finlab
chmod +x execute_task_7.2.sh
./execute_task_7.2.sh
```

**時間**: ~90-150 分鐘（自動執行所有步驟）

---

### 選項 B：手動逐步執行

#### Step 1: Pre-flight 檢查 (1分鐘)

```bash
cd /mnt/c/Users/jnpi/documents/finlab

# 檢查 finlab 認證
python3 -c "from finlab import data; print('✅ Auth OK' if data.get('price:收盤價') is not None else '❌ Auth Failed')"

# 確認策略文件
ls generated_strategy_fixed_iter*.py | wc -l  # 應該輸出 20

# 檢查 validation framework
python3 -c "from src.validation import BonferroniIntegrator, DynamicThresholdCalculator; print('✅ OK')"
```

#### Step 2: Pilot Test (15分鐘)

```bash
python3 run_phase2_with_validation.py --limit 3 --timeout 420 2>&1 | tee phase2_pilot_with_validation.log
```

**監控進度**:
```bash
# 另一個終端視窗
tail -f phase2_pilot_with_validation.log
```

**驗證結果**:
```bash
# 檢查是否有報告生成
ls -lh phase2_validated_results_*.json
ls -lh phase2_validated_results_*.md
```

**如果 Pilot 失敗**: 停止並檢查錯誤，不要繼續執行 full test

#### Step 3: Full Execution (60-120分鐘)

```bash
python3 run_phase2_with_validation.py --timeout 420 2>&1 | tee phase2_full_with_validation.log
```

**監控進度**:
```bash
# 另一個終端視窗
tail -f phase2_full_with_validation.log

# 或每10分鐘檢查一次
watch -n 600 "tail -20 phase2_full_with_validation.log"
```

**進度指標**:
- 看到 "Processing strategy X/20..." 表示正常進行
- 每個策略約 3-6 分鐘
- 總共約 60-120 分鐘

#### Step 4: 查看結果 (5分鐘)

```bash
# 查看最新的 JSON 報告
REPORT=$(ls -t phase2_validated_results_*.json | head -1)
cat $REPORT | jq '.'

# 查看 Markdown 報告
REPORT_MD=$(ls -t phase2_validated_results_*.md | head -1)
less $REPORT_MD
```

**關鍵指標提取**:
```bash
python3 <<EOF
import json
with open('$(ls -t phase2_validated_results_*.json | head -1)', 'r') as f:
    report = json.load(f)

print(f"Total Strategies: {report['summary']['total']}")
print(f"Successful: {report['summary']['successful']}")
print(f"Level 3 Profitable: {report['summary']['level_3_profitable']}")
print(f"Validated (v1.1): {report['validation_statistics']['total_validated']}")
print(f"Avg Sharpe: {report['metrics']['avg_sharpe']:.2f}")
EOF
```

---

## 完成後通知 Claude

執行完成後，告訴 Claude：

```
Task 7.2 執行完成。結果：
- Total: X strategies
- Successful: Y (Z%)
- Level 3: A (B%)
- Validated: C (D%)
- Avg Sharpe: E
- 報告文件: phase2_validated_results_YYYYMMDD_HHMMSS.json

請分析結果並生成 Task 7.2 總結。
```

Claude 將：
1. 讀取報告文件
2. 分析統計數據
3. 與 targets 比較 (Level 1 ≥60%, Level 3 ≥40%, Validated ≥30%)
4. 生成 TASK_7.2_COMPLETION_SUMMARY.md
5. 提供 Phase 3 準備建議 (GO/NO-GO)

---

## 故障排除

### Pilot Test 失敗

**錯誤**: `ModuleNotFoundError: No module named 'src.validation'`
```bash
# 檢查當前目錄
pwd  # 應該是 /mnt/c/Users/jnpi/documents/finlab

# 檢查模組存在
ls -la src/validation/__init__.py
```

**錯誤**: `finlab authentication failed`
```bash
# 重新認證
python3 -c "from finlab import data; data.login('YOUR_API_TOKEN')"
```

**錯誤**: `Strategy execution timeout`
- 這是正常的（某些策略可能超時）
- 檢查有多少策略成功執行
- 如果全部超時，增加 --timeout 600

### Full Execution 卡住

**症狀**: 長時間沒有新輸出

```bash
# 檢查進程
ps aux | grep python3

# 檢查最後的日誌
tail -50 phase2_full_with_validation.log

# 如果確認卡住，可以重啟（從某個策略繼續）
# 但需要修改腳本支持 --start-from 參數
```

---

## 時間預估

- Pre-flight: 1 分鐘
- Pilot test (3): 15 分鐘
- Full test (20): 60-120 分鐘
- Analysis: 5 分鐘
- **Total**: ~90-150 分鐘

建議在有 2-3 小時空閒時間時執行。

---

## 輸出文件

執行完成後會生成：

1. `phase2_pilot_with_validation.log` - Pilot test 日誌
2. `phase2_full_with_validation.log` - Full execution 日誌
3. `phase2_validated_results_YYYYMMDD_HHMMSS.json` - JSON 報告
4. `phase2_validated_results_YYYYMMDD_HHMMSS.md` - Markdown 報告

這些文件可以提供給 Claude 進行分析。
