# Phase 2.0+ Fusion Decision - Factor Graph Architecture

**Decision Date**: 2025-10-20
**Decision**: Adopt Phase 2.0+ (Unified Factor Graph System)
**Status**: ✅ **APPROVED** - Architecture融合方案

---

## 📋 決策背景

### Phase 1 驗證結果
- ✅ **技術成功**: Exit mutation framework 完成（detector, mutator, validator, operator）
- ⚠️ **驗證失敗**: 0% 成功率（測試設計問題，非框架問題）
- 📊 **系統穩定**: 框架運作正常，PopulationManager 整合成功

### 深度分析結果
經過 Gemini 2.5 Pro + 專家分析，發現關鍵架構洞察：

**當前限制**: Strategy = 參數字典 → 限制創新能力
**根本問題**: 策略本質是 Factor DAG（有向無環圖），而非參數列表
**突破方向**: Factor Graph System 統一 Phase 1/2a/2.0

---

## 🎯 Phase 2.0+ 核心設計

### 統一架構

```python
# 核心抽象：Factor Graph System
class Factor:
    """原子化的策略組件"""
    inputs: List[str]      # 需要的數據列
    outputs: List[str]     # 產生的數據列
    category: FactorCategory  # momentum, value, quality, risk, exit
    logic: Callable        # 執行邏輯
    parameters: dict       # 可調參數

class Strategy:
    """策略 = Factor 的有向無環圖"""
    factors: Dict[str, Factor]

    def validate(self) -> bool:
        """依賴關係檢查 + 拓撲排序"""

    def to_pipeline(self, data: pd.DataFrame) -> pd.DataFrame:
        """編譯為可執行管道"""
```

### 三層突變系統（自然融合）

```
Tier 1: Safe Configuration (Phase 2a 思想)
├── LLM → YAML/JSON config
├── Schema 驗證
└── Safe interpreter → Factor 實例

Tier 2: Factor Mutations (Phase 1 擴展)
├── add_factor()          # 添加新因子
├── remove_factor()       # 移除因子（檢查依賴）
├── replace_factor()      # 替換同類因子
└── mutate_parameters()   # 參數突變（Phase 1 已有）

Tier 3: Structural Mutations (Phase 2.0 核心)
├── modify_factor_logic()      # AST 級別邏輯修改
├── combine_signals()          # 創建複合信號
└── adaptive_parameters()      # 動態參數調整
```

---

## 💡 融合的優勢

### 1. 技術統一
- **Phase 2a** (YAML 配置) → Tier 1 安全入口
- **Phase 1** (Exit mutations) → Factor 的特例實現
- **Phase 2.0** (AST 突變) → Tier 3 高級能力

### 2. 漸進實施
```
Week 1-2:  Factor/Strategy 基礎類（核心）
Week 3-4:  現有模板 → Factor 庫（驗證）
Week 5-6:  Tier 2 突變操作（進化能力）
Week 7-8:  Tier 1 (YAML) + Tier 3 (AST)（完整能力）
```

### 3. 風險管理
- ✅ 每層都有明確的驗證邊界
- ✅ 根據風險承受度動態選擇 Tier
- ✅ 驗證前置（validate before backtest）節省資源

---

## 📊 成本效益分析

### 工作量對比

| 方案 | Phase 1 | Phase 2a | Phase 2.0 | 總計 |
|------|---------|----------|-----------|------|
| **分離實施** | ✅ 完成 | 2-3 週 | 6-8 週 | 8-11 週 |
| **Phase 2.0+** | ✅ 整合 | 融合 | 融合 | **8 週** |

### 額外價值
- **+2 週投入**
- **獲得**：
  - 統一架構（長期可維護性）
  - 更強創新能力（三層突變）
  - 組件重用（Phase 1 exit mutations）
  - 專家驗證的設計方向

---

## 🚀 實施路徑

### Phase A: Foundation (Week 1-2)
**目標**: 實現 Factor/Strategy 基礎類

**任務**:
1. 設計 Factor 接口（inputs, outputs, category, logic）
2. 實現 Strategy DAG 結構
3. 實現 validate() 方法（依賴檢查 + 拓撲排序）
4. 實現 to_pipeline() 方法

**驗證**: 手動組合策略模仿現有模板，成功回測

---

### Phase B: Migration (Week 3-4)
**目標**: 將現有模板轉換為 Factor 庫

**任務**:
1. 從 MomentumTemplate 提取 10-15 個 Factor
2. 從 TurtleTemplate 提取 Factor
3. 從 Phase 1 提取 Exit Strategy Factors
4. 建立 Factor Registry

**驗證**: EA 可用 Factor 組合運行 10 代，產生有效策略

---

### Phase C: Evolution (Week 5-6)
**目標**: 實現 Tier 2 突變操作

**任務**:
1. add_factor() + 依賴驗證
2. remove_factor() + 孤立檢測
3. replace_factor() + 同類因子庫
4. Smart mutation operators（category-aware）
5. Mutation rate scheduling

**驗證**: EA 運行 20 代，策略結構持續演化

---

### Phase D: Advanced Capabilities (Week 7-8)
**目標**: 添加 Tier 1 (YAML) 和 Tier 3 (AST)

**任務**:
1. YAML schema 設計 + 驗證器
2. YAML → Factor 解釋器
3. AST-based factor logic mutation
4. Adaptive mutation tier selection

**驗證**: 完整三層突變系統運行 50 代驗證

---

## 📝 與原方案差異

### 原 Phase 2.0 設計
- 直接 AST 突變現有策略代碼
- 5 個獨立的 Mutation Operators
- ExitStrategyMutationOperator 與 Phase 1 重疊

### Phase 2.0+ 設計
- Factor Graph 為核心抽象
- 三層統一突變系統
- Phase 1 exit mutations 自然融入 Factor 庫
- YAML 配置（2a）作為 Tier 1 安全模式

### 技術優勢
1. ✅ 解決 Phase 1 驗證發現的結構問題
2. ✅ 驗證前置（validate() before backtest）
3. ✅ 更好的依賴管理（DAG 拓撲排序）
4. ✅ 更強的可組合性（Factor 組合）
5. ✅ 與專家建議的 DAG 架構一致

---

## ✅ 決策確認

**選擇**: **Phase 2.0+ (Unified Factor Graph System)**

**理由**:
1. ✅ 專家驗證的架構方向（DAG > 參數字典）
2. ✅ 自然融合 Phase 1/2a/2.0（無冗餘）
3. ✅ 長期架構更優（可維護性 + 擴展性）
4. ✅ 額外 2 週換來更大價值

**時間線**: 8 週完成（vs 原 6-8 週 Phase 2.0）
**團隊**: 1-2 開發者
**風險**: 低（漸進式驗證 + 專家背書）

---

## 📚 參考文檔

- **深度分析**: Gemini 2.5 Pro thinkdeep workflow (2025-10-20)
- **專家分析**: Factor Graph System architectural insights
- **Phase 1 驗證**: EXIT_MUTATION_LONG_VALIDATION_REPORT.md
- **原設計**: structural-mutation-phase2/design.md (v1.0)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-20
**Status**: ✅ Approved
**Next Steps**: Update requirements.md, design.md, tasks.md
