# 1週測試啟動狀態

**啟動時間**: 2025-10-19 13:40:41 UTC
**狀態**: ✅ 成功啟動

---

## 進程信息

- **PID**: 12055
- **啟動命令**: `python3 sandbox_deployment.py --population-size 100 --max-generations 1000 --output-dir sandbox_output`
- **日誌文件**: `sandbox_week_test.log`
- **PID文件**: `sandbox_week_test.pid`

## 初始狀態

### 資源使用
- **CPU**: 71.1% ✅ (初始化族群評估，正常)
- **記憶體**: 910MB ✅ (100個體，正常範圍)
- **磁碟空間**: 514.12GB 可用 ✅

### 配置驗證
- ✅ Python 3.10.12
- ✅ 所有模組導入成功
- ✅ 環境驗證通過
- ✅ MonitoredEvolution 初始化成功

## 測試配置

### 族群參數
```python
population_size = 100        # ↑ 從50增加
elite_size = 3              # ↓ 從5減少
tournament_size = 2         # 保持
```

### 突變參數
```python
base_mutation_rate = 0.20      # ↑ 從0.15提升
template_mutation_rate = 0.10  # ↑ 從0.05提升
```

### 演化參數
```python
max_generations = 1000      # 完整1週測試
convergence_window = 10     # 保持
diversity_threshold = 0.5   # 保持
```

### 模板分佈
```python
template_distribution = {
    'Momentum': 0.25,
    'Turtle': 0.25,
    'Factor': 0.25,
    'Mastiff': 0.25
}
```

## 監控配置

### 指標導出
- **導出間隔**: 每10代
- **檢查點間隔**: 每50代
- **輸出目錄**: `sandbox_output/`

### 預期產出
```
sandbox_output/
├── metrics/
│   ├── metrics_json_gen_*.json (100個文件)
│   └── metrics_prometheus_gen_*.txt (100個文件)
├── checkpoints/
│   └── checkpoint_gen_*.json (20個文件)
└── alerts/
    └── alerts.json
```

## 監控命令

### 檢查進度
```bash
./check_week_progress.sh
```

### 查看即時日誌
```bash
tail -f sandbox_week_test.log | grep "Gen "
```

### 查看進程狀態
```bash
ps aux | grep 12055 | grep -v grep
```

### 檢查最新指標
```bash
ls -lt sandbox_output/metrics/ | head -5
```

## 預計時間表

基於100代測試的1.73小時運行時間：

- **每代平均時間**: ~1.04分鐘
- **預計總時間**: ~1040分鐘 = 17.3小時 ≈ 0.7天
- **預計完成**: 2025-10-20 06:58 UTC (~17小時後)

**注意**: 100個體 vs 50個體可能影響時間，實際可能需要 1.5-2天

## 每日檢查計劃

基於WEEK_TEST_CONFIG.md的監控重點：

### Day 1 (今日)
- [x] 確認啟動成功 ✅
- [ ] 檢查前50代表現
- [ ] 驗證指標導出正常
- [ ] 確認無錯誤

### 後續檢查點
- **6小時後**: Gen ~350 - 檢查多樣性維持
- **12小時後**: Gen ~700 - 檢查模板分佈
- **完成時**: Gen 1000 - 完整分析

## 成功標準

### 必須達成
- [ ] 完成1000代無致命錯誤
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

## 參數調整記錄

相對於100代測試的變更：

| 參數 | 100代測試 | 1週測試 | 變化 | 理由 |
|------|----------|---------|------|------|
| population_size | 50 | 100 | +100% | 支持更高多樣性 |
| elite_size | 5 | 3 | -40% | 減少過度保留 |
| base_mutation_rate | 0.15 | 0.20 | +33% | 維持參數探索 |
| template_mutation_rate | 0.05 | 0.10 | +100% | 促進模板競爭 |
| max_generations | 100 | 1000 | +900% | 完整長期測試 |

## 備份資訊

- **100代測試備份**: `sandbox_output_test_100gen_backup/`
- **配置文件**: `WEEK_TEST_CONFIG.md`
- **監控腳本**: `check_week_progress.sh`
- **測試結果**: `SANDBOX_TEST_RESULTS.md`

---

**啟動記錄完成** ✅
**測試運行中** 🔄
**預計完成**: ~17-48小時

---

*自動生成於 2025-10-19 13:40*
*PID: 12055*
