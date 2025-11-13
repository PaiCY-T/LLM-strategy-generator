# Requirements - Autonomous Strategy Iteration Engine

## 1. Overview

### 1.1 Purpose
建立一個能夠自主運作的策略迭代引擎，讓Claude AI自動產生交易策略想法、執行回測、比較結果，並持續學習改進，無需人工干預。

### 1.2 Core Philosophy
- **迭代優於分析**: 跑100個策略比分析1個策略更有價值
- **MVP優於完整系統**: 先建立可運作的核心循環，再優化細節
- **量化優於主觀**: 使用IC/ICIR等量化指標指導策略改進

### 1.3 Success Criteria
- 能夠自動運行至少10次策略迭代循環
- 每次迭代產生可執行的Finlab策略代碼
- 自動記錄並比較所有迭代結果
- 基於量化指標（IC/ICIR）改進後續策略

---

## 2. Functional Requirements

### FR-1: 策略生成 (Strategy Generation)
**Priority**: P0 - Critical
**User Story**: 作為系統，我需要自動產生交易策略想法，即使策略不完美

**Acceptance Criteria**:
- AC-1.1: 使用Claude API生成完整的Finlab策略代碼
- AC-1.2: 代碼包含資料載入、因子計算、選股邏輯、回測執行
- AC-1.3: 支援從719個已發現的Finlab資料集中選擇
- AC-1.4: 能夠利用前次迭代結果改進策略
- AC-1.5: 生成失敗時有fallback機制（使用template）

**Technical Notes**:
- 使用Anthropic SDK (claude-sonnet-4-20250514)
- Prompt需包含: 可用資料集清單、前次結果、改進建議
- 返回格式: Python代碼字串

---

### FR-2: 策略執行與回測 (Strategy Execution & Backtesting)
**Priority**: P0 - Critical
**User Story**: 作為系統，我需要安全地執行策略代碼並獲取回測結果

**Acceptance Criteria**:
- AC-2.1: 在沙盒環境中執行策略代碼
- AC-2.2: 捕獲執行錯誤並記錄詳細訊息
- AC-2.3: 提取關鍵績效指標: 年化報酬、夏普比率、最大回撤、勝率
- AC-2.4: 執行超時保護 (120秒限制)
- AC-2.5: 記錄trade details和equity curve

**Technical Notes**:
- 使用finlab.backtest.sim()執行回測
- 沙盒: 限制imports、設置timeout、資源限制
- 錯誤處理: try-except包裹exec()

---

### FR-3: 結果比較與學習 (Result Comparison & Learning)
**Priority**: P0 - Critical
**User Story**: 作為系統，我需要比較所有迭代結果並識別成功模式

**Acceptance Criteria**:
- AC-3.1: 維護所有迭代的結果歷史
- AC-3.2: 自動識別最佳策略（基於夏普比率）
- AC-3.3: 提取成功模式（哪些因子、參數組合有效）
- AC-3.4: 提取失敗模式（哪些方向應該避免）
- AC-3.5: 將學習結果反饋到下次策略生成

**Technical Notes**:
- 結果儲存: JSON格式（簡單、可讀）
- 比較邏輯: 多維度排序（夏普>報酬>回撤）
- 模式識別: 初期使用規則，未來可擴展ML

---

### FR-4: 因子評估工具 (Factor Evaluation)
**Priority**: P1 - High
**User Story**: 作為系統，我需要量化評估每個因子的預測能力

**Acceptance Criteria**:
- AC-4.1: 計算每個因子的IC (Information Coefficient)
- AC-4.2: 計算每個因子的ICIR (IC Information Ratio)
- AC-4.3: 標記高質量因子 (IC>0.03, ICIR>0.5)
- AC-4.4: 標記低質量因子 (IC<0.01或ICIR<0.3)
- AC-4.5: 將因子評估結果反饋給策略生成

**Technical Notes**:
- IC計算: correlation(factor[t], returns[t+1])
- ICIR計算: mean(IC) / std(IC)
- 滾動窗口: 20日或60日
- 輸出: DataFrame with factor_name, IC, ICIR, quality_label

---

### FR-5: 自動迭代循環 (Autonomous Iteration Loop)
**Priority**: P0 - Critical
**User Story**: 作為用戶，我希望系統能自主運行多次迭代而無需人工干預

**Acceptance Criteria**:
- AC-5.1: 支援配置迭代次數 (預設10次)
- AC-5.2: 每次迭代自動執行: 生成→回測→評估→學習
- AC-5.3: 迭代間自動傳遞學習結果
- AC-5.4: 提供進度顯示（當前迭代/總迭代）
- AC-5.5: 支援中斷後恢復（checkpoint機制）

**Technical Notes**:
- 主循環: for loop with iteration tracking
- Checkpoint: 每次迭代後保存結果JSON
- 恢復: 讀取JSON並從最後一次迭代繼續

---

## 3. Non-Functional Requirements

### NFR-1: Performance
- **NFR-1.1**: 單次策略生成 < 30秒
- **NFR-1.2**: 單次回測執行 < 120秒
- **NFR-1.3**: 10次迭代總時間 < 30分鐘

### NFR-2: Reliability
- **NFR-2.1**: 策略生成失敗率 < 10%
- **NFR-2.2**: 回測執行失敗時有詳細錯誤訊息
- **NFR-2.3**: 系統崩潰後可從checkpoint恢復

### NFR-3: Usability
- **NFR-3.1**: 清晰的終端輸出（進度、結果、錯誤）
- **NFR-3.2**: 結果以人類可讀的格式保存（JSON + summary）
- **NFR-3.3**: 提供簡單的使用說明（README）

### NFR-4: Maintainability
- **NFR-4.1**: 單一Python腳本 < 500行
- **NFR-4.2**: 清晰的函數職責分離
- **NFR-4.3**: 關鍵邏輯有註解說明

### NFR-5: Scalability (Future)
- **NFR-5.1**: 設計允許未來擴展UI界面
- **NFR-5.2**: 設計允許未來切換資料庫儲存
- **NFR-5.3**: 設計允許未來並行執行多個迭代

---

## 4. Out of Scope (Not for MVP)

以下功能**不在此次MVP範圍內**，可能在未來版本實現：

- ❌ Streamlit UI界面
- ❌ SQLite資料庫儲存
- ❌ 多策略視覺化比較
- ❌ 雙語支援
- ❌ 自動部署到雲端
- ❌ 實盤交易整合
- ❌ 風險管理模組
- ❌ 完整的測試套件（單元測試、整合測試）

**理由**: 先驗證核心循環可行性，再考慮增強功能

---

## 5. Dependencies

### External APIs
- **Finlab API**: 資料下載與回測引擎
- **Anthropic Claude API**: 策略生成

### Python Libraries
```
finlab>=1.5.3
anthropic>=0.40.0
pandas>=2.0.0
numpy>=1.24.0
```

### Environment
- Python 3.10+
- 有效的Finlab API Token
- 有效的Claude API Key

---

## 6. Constraints

### Technical Constraints
- **TC-1**: 必須使用Finlab API，無法自行實現回測引擎
- **TC-2**: Claude API有rate limit (50 requests/min)
- **TC-3**: 策略代碼必須在120秒內執行完成

### Business Constraints
- **BC-1**: Finlab API有使用成本（每次data.get()消耗配額）
- **BC-2**: Claude API有使用成本（每次生成策略約$0.01-0.05）

### Resource Constraints
- **RC-1**: 單機執行，不使用雲端資源
- **RC-2**: 記憶體限制: 建議8GB+
- **RC-3**: 磁碟空間: 至少1GB用於緩存資料

---

## 7. Success Metrics

### Primary Metrics
1. **迭代完成率**: ≥ 90% (9/10次迭代成功完成)
2. **策略改進率**: 最後3次迭代的平均夏普比率 > 前3次迭代
3. **自動化程度**: 0次人工干預即可完成10次迭代

### Secondary Metrics
1. **因子識別準確度**: 高IC因子被重複使用的比例
2. **學習效果**: 相同錯誤不重複出現超過2次
3. **執行效率**: 單次迭代平均時間 < 3分鐘

---

## 8. Risks & Mitigation

### High Risk
1. **R-1**: Claude生成的策略代碼有語法錯誤
   - **Mitigation**: AST語法驗證、多次retry機制

2. **R-2**: 策略持續失敗（0交易、錯誤參數）
   - **Mitigation**: Template fallback、明確錯誤反饋給Claude

### Medium Risk
3. **R-3**: API費用超支
   - **Mitigation**: 設定迭代次數上限、本地緩存策略代碼

4. **R-4**: 資料下載失敗
   - **Mitigation**: 重試機制、使用cached data

### Low Risk
5. **R-5**: 結果JSON檔案損壞
   - **Mitigation**: 每次寫入前備份舊檔案

---

## 9. Glossary

| Term | Definition |
|------|------------|
| **Iteration** | 一次完整的策略生成→回測→評估循環 |
| **IC** | Information Coefficient，因子值與未來收益的相關性 |
| **ICIR** | IC Information Ratio，IC的均值/標準差 |
| **Factor** | 用於選股的量化指標（如RSI、外資買超） |
| **Backtest** | 歷史數據模擬交易，評估策略績效 |
| **Checkpoint** | 迭代進度保存點，用於斷點續傳 |

---

## 10. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2025-10-07 | Claude | Initial draft based on user feedback |

---

## 11. Approval

- [ ] User Review
- [ ] Technical Feasibility Check
- [ ] Resource Availability Confirmed
