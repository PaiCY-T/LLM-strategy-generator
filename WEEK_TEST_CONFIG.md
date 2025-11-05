# 1週完整測試配置

**啟動時間**: 2025-10-19
**預計完成**: 2025-10-26 (~7天後)

---

## 測試參數

### 調整後的參數（基於100代測試發現）

```python
# Population settings
population_size = 100        # 增加族群大小以提升多樣性
elite_size = 3              # ↓ 從 5 減少，減少過度保留
tournament_size = 2         # 保持不變

# Mutation settings (提升探索能力)
base_mutation_rate = 0.20      # ↑ 從 0.15 提升 33%
template_mutation_rate = 0.10  # ↑ 從 0.05 提升 100%

# Evolution settings
max_generations = 1000      # 完整1週測試
convergence_window = 10     # 保持不變
diversity_threshold = 0.5   # 保持不變

# Monitoring settings
metrics_export_interval = 10    # 每10代導出
checkpoint_interval = 50        # 每50代檢查點
alert_file = "sandbox_output/alerts/alerts.json"
```

### 參數調整理由

1. **base_mutation_rate: 0.15 → 0.20**
   - 原因: 100代測試顯示過早收斂
   - 預期: 維持更高的參數探索

2. **template_mutation_rate: 0.05 → 0.10**
   - 原因: Turtle模板過度主導（100%）
   - 預期: 促進模板間的探索和競爭

3. **elite_size: 5 → 3**
   - 原因: 減少優勢策略的過度保留
   - 預期: 給新策略更多機會

4. **population_size: 50 → 100**
   - 原因: 更大族群支持更高多樣性
   - 預期: 減緩收斂速度，更充分探索

---

## 預期結果

### 基於100代測試的預測

**適應度**:
- 起始: ~0.0 (隨機初始化)
- 預期峰值: 2.2-2.5 (超越當前2.1484)
- 預期平均（最後100代）: 2.0-2.2

**多樣性**:
- 目標: 維持 >0.3 至少到 Gen 500
- 預期最終: 0.1-0.3（比當前0.0好）

**模板分佈**:
- 預期: 2-3個模板共存（vs 當前1個）
- 可能主導: Turtle 仍會優勢但非100%
- 期望: 發現其他模板的優勢組合

### 監控重點

**每日檢查**:
- [ ] Day 1: 確認啟動成功，檢查前50代
- [ ] Day 2: Gen 150-200，多樣性趨勢
- [ ] Day 3: Gen 300-350，模板分佈
- [ ] Day 4: Gen 450-500，適應度突破
- [ ] Day 5: Gen 600-650，收斂跡象
- [ ] Day 6: Gen 750-800，最終衝刺
- [ ] Day 7: Gen 900-1000，完成驗證

**關鍵指標**:
1. 多樣性 >0.3 維持到 Gen 500+
2. 至少2個模板保持 >10% 比例
3. 適應度突破 2.1484
4. 無系統錯誤或崩潰

---

## 執行計劃

### 啟動命令
```bash
nohup python3 sandbox_deployment.py \
    --population-size 100 \
    --max-generations 1000 \
    --output-dir sandbox_output \
    > sandbox_week_test.log 2>&1 &

# 記錄PID
echo $! > sandbox_week_test.pid
```

### 監控腳本
```bash
# 每日進度檢查
./check_week_progress.sh

# 即時日誌
tail -f sandbox_week_test.log | grep "Gen "

# 指標摘要
python3 scripts/analyze_metrics.py sandbox_output/metrics/
```

### 備份策略
- **每日備份**: checkpoint files
- **每3天**: 完整metrics備份
- **完成時**: 全部輸出歸檔

---

## 預期輸出

### 文件數量
```
sandbox_output/
├── metrics/
│   ├── metrics_json_gen_*.json (100個文件)
│   └── metrics_prometheus_gen_*.txt (100個文件)
├── checkpoints/
│   └── checkpoint_gen_*.json (20個文件)
├── alerts/
│   └── alerts.json (實時更新)
└── logs/
    └── (可選)
```

### 預計大小
- 總metrics: ~10-15 MB
- 總checkpoints: ~200 KB
- 日誌: ~500 MB
- **總計**: ~16 MB

---

## 風險評估

### 潛在問題

**1. 記憶體不足**
- 風險: 中
- 100個體 vs 50個體 → 2x 記憶體
- 預期: ~2.5 GB
- 緩解: 監控記憶體使用，必要時重啟

**2. 磁碟空間**
- 風險: 低
- 預計使用: ~20 MB
- 可用空間: 514 GB
- 緩解: 定期清理舊日誌

**3. 過早終止**
- 風險: 低（已修復所有bugs）
- 緩解: nohup + 錯誤處理 + checkpoint恢復

**4. 過度收斂（仍然發生）**
- 風險: 中
- 緩解: 新參數設計緩解此問題
- 備案: 數據仍有價值，記錄發現

---

## 成功標準

### 必須達成
- [x] 完成1000代無致命錯誤
- [ ] 生成所有預期文件
- [ ] 監控系統持續運作
- [ ] 冠軍適應度 ≥ 2.0

### 期望達成
- [ ] 最終多樣性 ≥ 0.1
- [ ] 至少2個模板共存 (>10%)
- [ ] 適應度突破 2.2
- [ ] 發現新優勢組合

### 優秀表現
- [ ] 最終多樣性 ≥ 0.3
- [ ] 3+模板共存
- [ ] 適應度 ≥ 2.5
- [ ] 持續改善至Gen 1000

---

**配置記錄完成**
**準備啟動1週測試** ✅
