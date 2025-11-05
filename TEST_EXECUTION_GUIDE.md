# 測試執行指南 | Test Execution Guide

**版本**: 1.0
**日期**: 2025-10-17
**預估總時間**: 6-8 小時 (可在睡眠時執行)

---

## 📋 執行前檢查清單 | Pre-Execution Checklist

### 1. 環境變數設定 | Environment Variables

確認以下環境變數已設定:

```bash
# 檢查環境變數 | Check environment variables
echo $FINLAB_API_TOKEN
echo $OPENROUTER_API_KEY
echo $GOOGLE_API_KEY
```

**必需設定** (Required):
- `FINLAB_API_TOKEN` - Finlab API 認證 token
- `OPENROUTER_API_KEY` - OpenRouter API key (用於 LLM 調用)
- `GOOGLE_API_KEY` - Google API key (備用)

如未設定，使用以下指令:
```bash
export FINLAB_API_TOKEN='your_token_here'
export OPENROUTER_API_KEY='your_key_here'
export GOOGLE_API_KEY='your_key_here'
```

### 2. 確認所需檔案存在 | Verify Required Files

```bash
# 確認測試腳本 | Verify test scripts
ls -lh run_5iteration_test.py run_200iteration_test.py

# 確認測試框架 | Verify test harness
ls -lh tests/integration/extended_test_harness.py

# 確認 Phase 2 監控元件 | Verify Phase 2 monitoring components
ls -lh src/monitoring/variance_monitor.py
ls -lh src/validation/preservation_validator.py
ls -lh src/config/anti_churn_manager.py
ls -lh src/recovery/rollback_manager.py
```

全部檔案應該都存在。如有缺失，請勿執行測試。

---

## 🔬 第一步: 5圈煙霧測試 | Step 1: 5-Iteration Smoke Test

### 執行指令 | Run Command

```bash
python3 run_5iteration_test.py
```

### 預期執行時間 | Expected Duration
- **30-60 分鐘** (取決於網路速度和 API 回應時間)

### 監控重點 | What to Monitor

測試會自動產生 log 檔案於 `logs/` 目錄:
```
logs/5iteration_smoke_test_YYYYMMDD_HHMMSS.log
```

**即時監控** (如果您保持清醒):
```bash
# 監看最新的 log 檔案 | Monitor latest log file
tail -f logs/5iteration_smoke_test_*.log
```

### 解讀結果 | Interpreting Results

測試完成後，會顯示以下資訊:

#### ✅ 成功案例 | Success Case
```
✅ Smoke test completed successfully
   Success rate: 80.0%
   Best Sharpe: 1.8500
   Avg Sharpe: 1.4200
   Phase 2 features: ✅ All available
   Log file: logs/5iteration_smoke_test_YYYYMMDD_HHMMSS.log

📊 Next Steps:
   ✅ High success rate - proceed with 200-iteration test
```

#### ⚠️ 中等成功率 | Moderate Success
```
✅ Smoke test completed successfully
   Success rate: 60.0%
   Best Sharpe: 1.5200
   Avg Sharpe: 1.2100
   Phase 2 features: ✅ All available

📊 Next Steps:
   ⚠️  Moderate success rate - review logs before 200-iteration test
```

**建議動作**: 檢查 log 檔案中的錯誤訊息，但可以繼續執行 200 圈測試。

#### ❌ 低成功率 | Low Success Rate
```
✅ Smoke test completed successfully
   Success rate: 40.0%
   Best Sharpe: 1.1000
   Avg Sharpe: 0.8500

📊 Next Steps:
   ❌ Low success rate - investigate issues before proceeding
```

**建議動作**: 暫停，檢查 log 檔案找出問題根因。

#### ❌ 測試失敗 | Test Failure
```
❌ Smoke test failed: [error message]
   Log file: logs/5iteration_smoke_test_YYYYMMDD_HHMMSS.log
```

**建議動作**: 檢查錯誤訊息。常見問題:
- API token 過期或無效
- 網路連線問題
- 缺少必要的 Python 套件

---

## 決策樹 | Decision Tree

```
煙霧測試結果 Smoke Test Result
    │
    ├─ Success Rate ≥ 80% ──> ✅ 直接執行 200 圈測試 | Proceed to 200-iteration test
    │
    ├─ 60% ≤ Success Rate < 80% ──> ⚠️  檢查 log 後執行 | Review logs, then proceed
    │                                    (大部分情況仍可執行)
    │
    ├─ 40% ≤ Success Rate < 60% ──> ⚠️  深入檢查 log | Deep log review required
    │                                    (風險較高，但可嘗試)
    │
    └─ Success Rate < 40% ──> ❌ 暫停調查 | Stop and investigate
                                (不建議執行 200 圈)
```

---

## 🚀 第二步: 200圈生產驗證測試 | Step 2: 200-Iteration Production Test

### 執行指令 | Run Command

```bash
# 基本執行 | Basic execution
python3 run_200iteration_test.py

# 或指定 group ID (用於多組測試) | Or specify group ID for parallel tests
python3 run_200iteration_test.py 1
```

### 預期執行時間 | Expected Duration
- **6-8 小時** (約 120-145 秒/圈，包含 backtest 和 LLM 調用)
- **建議**: 在睡眠或長時間離開時執行

### 自動檢查點 | Automatic Checkpointing

測試會**每 20 圈自動儲存檢查點**:
```
checkpoints_group1/
├── checkpoint_iter_20.json
├── checkpoint_iter_40.json
├── checkpoint_iter_60.json
...
└── checkpoint_iter_200.json
```

### 中斷後恢復 | Resume After Interruption

如果測試中斷 (停電、當機、Ctrl+C):

```bash
# 從最後一個檢查點恢復 | Resume from last checkpoint
python3 run_200iteration_test.py 1 checkpoints_group1/checkpoint_iter_140.json
```

**注意**: 檢查點檔名中的數字 (如 `iter_140`) 表示已完成的圈數。

### 監控執行進度 | Monitoring Progress

#### 方法 1: 即時 log 監控 | Real-time Log Monitoring
```bash
# 監看最新的 200 圈測試 log | Monitor latest 200-iteration log
tail -f logs/200iteration_test_group1_*.log

# 只顯示重要訊息 | Show only important messages
tail -f logs/200iteration_test_group1_*.log | grep -E "(Iteration|Champion|Sharpe|Error|Warning)"
```

#### 方法 2: 檢查點檔案 | Checkpoint Files
```bash
# 查看最新檢查點 | Check latest checkpoint
ls -lt checkpoints_group1/ | head -5

# 讀取檢查點內容 (JSON) | Read checkpoint content
cat checkpoints_group1/checkpoint_iter_100.json | python3 -m json.tool | head -50
```

#### 方法 3: 迭代歷史檔案 | Iteration History File
```bash
# 查看 champion 更新歷史 | View champion update history
cat iteration_history.json | python3 -m json.tool | grep -A 10 "champion_history"

# 統計成功/失敗次數 | Count success/failure
cat iteration_history.json | grep -o '"status": "success"' | wc -l
cat iteration_history.json | grep -o '"status": "failed"' | wc -l
```

---

## 📊 解讀 200 圈測試結果 | Interpreting 200-Iteration Results

### 成功案例 | Success Case

```
✅ Test completed successfully (Group 1)
   Total iterations: 200
   Success rate: 85.0%
   Best Sharpe: 2.1500
   Avg Sharpe: 1.6800
   Total duration: 7.25 hours

🎉 PRODUCTION READY: All criteria met
   Log file: logs/200iteration_test_group1_YYYYMMDD_HHMMSS.log
   Final checkpoint: checkpoints_group1/checkpoint_iter_200.json
```

### 生產就緒報告 | Production Readiness Report

測試完成後會自動產生詳細報告，包含:

#### 1. 統計指標 | Statistical Metrics
```
STATISTICAL METRICS:
  Sample size: 170          # 成功的圈數 (總圈數 * 成功率)
  Mean Sharpe: 1.6800      # 平均 Sharpe ratio
  Std Sharpe: 0.3200       # 標準差
  Range: [0.8500, 2.1500]  # 最小值到最大值
```

#### 2. 學習效果分析 | Learning Effect Analysis
```
LEARNING EFFECT ANALYSIS:
  Cohen's d: 0.650 (medium effect)     # 效應量 (small: 0.2-0.5, medium: 0.5-0.8, large: ≥0.8)
  P-value: 0.0023 (significant)        # 統計顯著性 (p<0.05 為顯著)
  95% CI: [0.420, 0.880]               # 95% 信賴區間
```

**解讀**:
- **Cohen's d ≥ 0.4**: 學習系統有實際效果 ✅
- **P-value < 0.05**: 效果具統計顯著性 ✅
- **CI 不含 0**: 效果一致性高 ✅

#### 3. 收斂分析 | Convergence Analysis
```
CONVERGENCE ANALYSIS:
  Rolling variance: 0.420              # 滾動方差 (10 圈窗口)
  Convergence achieved (σ<0.5): True   # 是否收斂
```

**解讀**:
- **σ < 0.5**: 策略品質趨於穩定 ✅
- **σ ≥ 0.5**: 仍在探索，品質波動大 ⚠️

#### 4. Phase 1 + Phase 2 穩定性特徵 | Stability Features
```
PHASE 1 + PHASE 2 STABILITY FEATURES:
  Data integrity checks: 200           # 資料完整性檢查次數
  Config snapshots: 200                # 設定快照次數
  Champion updates: 28                 # Champion 更新次數
  Update frequency: 14.0% (target: 10-20%)  # 更新頻率
```

**解讀**:
- **Update frequency 10-20%**: 適當平衡探索與利用 ✅
- **Update frequency < 10%**: 可能過度保守 ⚠️
- **Update frequency > 20%**: 可能過度不穩定 ⚠️

#### 5. 生產就緒判定 | Production Readiness Criteria

**3 項必須全部滿足**:
1. ✅ **Statistical significance**: p-value < 0.05
2. ✅ **Meaningful effect size**: Cohen's d ≥ 0.4
3. ✅ **Convergence**: Rolling variance < 0.5

```
✅ STATUS: READY FOR PRODUCTION

READINESS REASONING:
  ✅ Statistical significance: p=0.0023 < 0.05
  ✅ Effect size medium: d=0.650 ≥ 0.4
  ✅ Convergence achieved: σ=0.420 < 0.5
```

### 不符合生產標準案例 | Not Production Ready Case

```
❌ STATUS: NOT READY FOR PRODUCTION

READINESS REASONING:
  ✅ Statistical significance: p=0.0180 < 0.05
  ❌ Effect size too small: d=0.320 < 0.4
  ✅ Convergence achieved: σ=0.450 < 0.5
```

**建議動作**:
- 如果只有 1 項未達標: 檢查該項指標，可能需要調整超參數或增加訓練圈數
- 如果 2 項以上未達標: 需要深入調查根因，可能有系統性問題

---

## ⚠️ 常見問題與排解 | Troubleshooting

### 問題 1: API Token 錯誤
```
❌ Data loading failed: FINLAB_API_TOKEN environment variable not set
```

**解決方法**:
```bash
export FINLAB_API_TOKEN='your_token_here'
python3 run_5iteration_test.py  # 重新執行
```

### 問題 2: 網路連線問題
```
❌ Failed to load Finlab data: ConnectionError
```

**解決方法**:
- 檢查網路連線
- 確認 Finlab API 服務正常
- 使用檢查點恢復 (如果已執行部分圈數)

### 問題 3: 記憶體不足
```
❌ Test execution failed: MemoryError
```

**解決方法**:
- 關閉其他大型程式
- 增加系統 swap space
- 考慮使用較小的 checkpoint_interval (如 10 圈)

### 問題 4: Phase 2 功能缺失
```
⚠️  Missing features: ['VarianceMonitor', 'PreservationValidator']
```

**解決方法**:
- 測試仍會繼續執行，但缺少部分監控功能
- 檢查是否所有 Phase 2 相關檔案都存在
- 如果只是警告，可以繼續執行

### 問題 5: Champion 更新頻率異常

**過高 (>30%)**:
```
  Update frequency: 42.5% (target: 10-20%)
```
- 可能: 學習系統過度激進，策略品質不穩定
- 檢查: VarianceMonitor 和 AntiChurnManager 是否正常運作

**過低 (<5%)**:
```
  Update frequency: 3.2% (target: 10-20%)
```
- 可能: 學習系統過度保守，陷入局部最優
- 檢查: novelty scoring 和 exploration 機制是否有效

---

## 📁 輸出檔案說明 | Output Files

### 測試執行期間 | During Test Execution

1. **Log 檔案** | Log Files
   - 位置: `logs/`
   - 格式: `5iteration_smoke_test_YYYYMMDD_HHMMSS.log`
   - 格式: `200iteration_test_group1_YYYYMMDD_HHMMSS.log`
   - 用途: 詳細執行記錄，包含所有 INFO/WARNING/ERROR 訊息

2. **檢查點檔案** | Checkpoint Files
   - 位置: `checkpoints_group1/`
   - 格式: `checkpoint_iter_N.json` (N = 20, 40, 60, ...)
   - 用途: 恢復中斷的測試

3. **迭代歷史** | Iteration History
   - 位置: `iteration_history.json`
   - 格式: JSON
   - 用途: 每圈的詳細記錄 (參數、metrics、champion 更新等)

4. **生成的策略檔案** | Generated Strategy Files
   - 位置: 專案根目錄
   - 格式: `generated_strategy_loop_iterN.py`
   - 用途: 每圈生成的策略程式碼

### 測試完成後 | After Test Completion

5. **Champion 策略** | Champion Strategy
   - 位置: `champion.json`
   - 格式: JSON
   - 用途: 最佳策略的參數和 metrics

6. **統計報告** | Statistical Report
   - 位置: 內嵌於 log 檔案
   - 格式: Markdown-style text
   - 用途: 生產就緒評估

---

## 🎯 成功標準總結 | Success Criteria Summary

### 5 圈煙霧測試 | 5-Iteration Smoke Test
- ✅ **Success rate ≥ 60%**: 基本功能正常
- ✅ **All Phase 2 features available**: 監控元件完整
- ✅ **No critical errors**: 無嚴重錯誤

### 200 圈生產驗證測試 | 200-Iteration Production Test
- ✅ **Success rate ≥ 70%**: 系統穩定性高
- ✅ **p-value < 0.05**: 統計顯著性
- ✅ **Cohen's d ≥ 0.4**: 實際效應量
- ✅ **Rolling variance < 0.5**: 收斂性
- ✅ **Champion update frequency 10-20%**: 適當平衡

---

## 📞 需要協助 | Need Help

如果測試失敗或結果異常:

1. **保留所有輸出檔案**:
   - Log 檔案
   - 檢查點檔案
   - iteration_history.json
   - champion.json

2. **提供以下資訊**:
   - 測試類型 (5 圈或 200 圈)
   - 錯誤訊息 (來自 log 檔案)
   - 執行到第幾圈失敗
   - Success rate 和 Sharpe ratio 統計

3. **檢查這些檔案**:
   - `TASK_53_PARTIAL_COMPLETION_SUMMARY.md` - 測試覆蓋率問題
   - `PROJECT_TODO.md` - 待辦事項和已知問題
   - `.spec-workflow/specs/learning-system-stability-fixes/tasks.md` - Phase 實作狀態

---

## ✅ 執行清單 | Execution Checklist

**睡前** (Before Sleep):
- [ ] 確認所有環境變數已設定
- [ ] 執行 5 圈煙霧測試
- [ ] 等待煙霧測試完成 (30-60 分鐘)
- [ ] 檢查煙霧測試結果
- [ ] 如果 success rate ≥ 60%，啟動 200 圈測試
- [ ] 確認 200 圈測試已開始執行

**起床後** (After Sleep):
- [ ] 檢查 200 圈測試是否完成
- [ ] 如果中斷，使用檢查點恢復
- [ ] 查看生產就緒報告
- [ ] 檢查 log 檔案是否有異常
- [ ] 驗證 champion.json 是否合理
- [ ] 根據結果決定下一步行動

---

**版本歷史** | Version History:
- v1.0 (2025-10-17): 初版，包含 Phase 2 監控元件驗證

**相關文件** | Related Documents:
- `run_5iteration_test.py` - 煙霧測試腳本
- `run_200iteration_test.py` - 生產驗證測試腳本
- `tests/integration/extended_test_harness.py` - 測試框架
- `PROJECT_TODO.md` - 專案待辦事項
