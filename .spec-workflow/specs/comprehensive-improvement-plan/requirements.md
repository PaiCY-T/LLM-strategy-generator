# Requirements Document: Comprehensive Improvement Plan

## Introduction

本規格定義 LLM 策略生成器的綜合改善計畫，針對 5 個關鍵問題提出系統性解決方案。重點修正 40M TWD 資本規模的流動性成本計算，並採用 Finlab TA-Lib 整合簡化技術指標實現。本計畫採用 **TDD (Test-Driven Development)** 方法論，確保每個功能都有完整的測試覆蓋。

**資本規模**: 4 千萬新台幣 (40M TWD)
**優先級**: P0 (Critical) - 立即執行

## Alignment with Product Vision

本改善計畫直接支援 product.md 中的核心目標：
- **策略品質提升**: 修復 Metrics Bug 確保策略分類正確
- **因子多樣化**: 新增反轉型因子降低同質化風險
- **風險控制**: 流動性過濾器確保 40M TWD 資本可執行性
- **科學化評估**: 多目標評分公式取代單一 Sharpe ratio

## Requirements

### Requirement 1: P0 Metrics Contract Bug 修復

**User Story:** As a 策略開發者, I want Metrics 合約正確返回所有必要欄位, so that 策略分類能正確運作且學習循環不會失效

#### Acceptance Criteria (TDD)

1. WHEN `MomentumTemplate._extract_metrics()` 被調用 THEN 系統 SHALL 返回包含 `execution_success: True` 欄位的字典
2. WHEN `MomentumTemplate._extract_metrics()` 被調用 THEN 系統 SHALL 返回包含 `total_return` 欄位的字典
3. WHEN metrics 返回後經過 `StrategyMetrics.classify()` THEN 系統 SHALL 正確分類策略 (非全部歸為 LEVEL_0)
4. IF 回測成功執行 THEN 系統 SHALL 返回完整的 metrics 字典包含: `execution_success`, `annual_return`, `total_return`, `sharpe_ratio`, `max_drawdown`, `sortino_ratio`, `calmar_ratio`

**Test First (TDD)**:
```python
# tests/templates/test_momentum_template.py::test_metrics_contract
def test_metrics_contract_required_fields():
    """測試 metrics 合約包含所有必要欄位"""
    metrics = momentum_template._extract_metrics(mock_report)
    assert 'execution_success' in metrics
    assert 'total_return' in metrics
    assert metrics['execution_success'] == True

def test_strategy_classification_not_all_level_0():
    """測試策略不會全部被誤判為 LEVEL_0"""
    # 至少有一個策略應該被分類為非 LEVEL_0
```

---

### Requirement 2: P1 RSI 反轉因子

**User Story:** As a 策略開發者, I want RSI 反轉因子使用 TA-Lib 整合, so that 我可以利用超賣訊號進行反轉交易並降低因子同質化

#### Acceptance Criteria (TDD)

1. WHEN RSI factor 計算完成 THEN 系統 SHALL 返回 RSI 值在 [0, 100] 範圍內
2. WHEN RSI factor 生成訊號 THEN 系統 SHALL 返回 signal 值在 [-1.0, 1.0] 範圍內
3. WHEN RSI < oversold_threshold (30) THEN 系統 SHALL 生成正向訊號 (signal > 0)
4. WHEN RSI > overbought_threshold (70) THEN 系統 SHALL 生成負向訊號 (signal < 0)
5. **CRITICAL (Look-ahead)**: WHEN 修改 T+1 數據 THEN 系統 SHALL 保持 T 時刻訊號不變 (TTPT 測試)

**Test First (TDD)**:
```python
def test_rsi_range():
    """RSI 值應在 [0, 100]"""

def test_signal_range():
    """Signal 值應在 [-1, 1]"""

def test_rsi_no_lookahead_bias():
    """TTPT: 擾動 T+1 不影響 T 的訊號"""
```

---

### Requirement 3: P1 RVOL 成交量因子

**User Story:** As a 策略開發者, I want 相對成交量因子使用 Finlab 成交金額數據, so that 我可以確認量價關係並避免低流動性股票

#### Acceptance Criteria (TDD)

1. WHEN RVOL factor 計算完成 THEN 系統 SHALL 返回 rvol = 當日量/均量 比率
2. WHEN RVOL > volume_threshold (1.5) THEN 系統 SHALL 標記為放量確認
3. WHEN OBV 上升且價格上升 THEN 系統 SHALL 生成多頭確認訊號
4. IF Finlab 成交金額數據不可用 THEN 系統 SHALL 使用 fallback 數據源
5. **CRITICAL (Look-ahead)**: WHEN 修改 T+1 數據 THEN 系統 SHALL 保持 T 時刻訊號不變

**Test First (TDD)**:
```python
def test_rvol_calculation():
    """RVOL = 當日量/均量"""

def test_obv_confirmation():
    """OBV + 價格確認訊號"""

def test_rvol_no_lookahead_bias():
    """TTPT: 無 look-ahead bias"""
```

---

### Requirement 4: P1 流動性過濾器 (40M TWD)

**User Story:** As a 4 千萬資本規模的投資者, I want 流動性過濾器排除低 ADV 股票, so that 我的策略可以實際執行而不會有過大滑價

#### Acceptance Criteria (TDD)

1. WHEN ADV < 40 萬 TWD THEN 系統 SHALL 將股票分類為 Forbidden (完全排除)
2. WHEN 40 萬 <= ADV < 100 萬 THEN 系統 SHALL 將股票分類為 Warning (小倉位 1%)
3. WHEN 100 萬 <= ADV < 500 萬 THEN 系統 SHALL 將股票分類為 Safe (正常倉位 5%)
4. WHEN ADV >= 500 萬 THEN 系統 SHALL 將股票分類為 Premium (無限制 10%)
5. WHEN strict_mode=True THEN 系統 SHALL 僅保留 Safe/Premium 級別股票
6. IF 股票流動性不足 THEN 系統 SHALL 將其訊號歸零

**Test First (TDD)**:
```python
def test_liquidity_tier_forbidden():
    """ADV < 40萬 → Forbidden"""

def test_liquidity_tier_warning():
    """40萬 <= ADV < 100萬 → Warning"""

def test_liquidity_filter_strict_mode():
    """Strict mode 僅保留 Safe/Premium"""

def test_signal_zeroed_for_low_liquidity():
    """低流動性股票訊號歸零"""
```

---

### Requirement 5: P1 執行成本模型

**User Story:** As a 策略開發者, I want 基於 Square Root Law 的滑價模型, so that 我可以準確估算交易成本並懲罰低流動性策略

#### Acceptance Criteria (TDD)

1. WHEN 計算滑價 THEN 系統 SHALL 使用公式: Slippage = Base_Cost + α × sqrt(Trade_Size/ADV) × Volatility
2. WHEN 滑價計算完成 THEN 系統 SHALL 限制最大滑價為 500 bps (5%)
3. WHEN 滑價 < 20 bps THEN 系統 SHALL 不施加懲罰
4. WHEN 滑價在 20-50 bps THEN 系統 SHALL 施加線性懲罰
5. WHEN 滑價 > 50 bps THEN 系統 SHALL 施加二次懲罰

**Test First (TDD)**:
```python
def test_slippage_formula():
    """Square Root Law 滑價公式"""

def test_slippage_cap():
    """滑價最大 500 bps"""

def test_penalty_tiers():
    """懲罰分級: <20無, 20-50線性, >50二次"""
```

---

### Requirement 6: P1 綜合評分器

**User Story:** As a 策略開發者, I want 多目標評分公式整合 Calmar/Sortino/穩定性/週轉率/流動性, so that 我可以全面評估策略品質而非僅看 Sharpe ratio

#### Acceptance Criteria (TDD)

1. WHEN 計算評分 THEN 系統 SHALL 使用權重: Calmar 30%, Sortino 25%, Stability 20%, Turnover 15%, Liquidity 10%
2. WHEN 權重配置變更 THEN 系統 SHALL 驗證權重總和為 1.0
3. WHEN 計算穩定性 THEN 系統 SHALL 使用 1 - CV(monthly_returns) 公式
4. WHEN 計算週轉成本 THEN 系統 SHALL 使用 Annual_Turnover × Commission × 2
5. WHEN 返回評分 THEN 系統 SHALL 包含各分項分數及總分

**Test First (TDD)**:
```python
def test_weight_sum():
    """權重總和 = 1.0"""

def test_stability_calculation():
    """穩定性 = 1 - CV"""

def test_comprehensive_score_components():
    """評分包含 5 個分項"""
```

---

### Requirement 7: P2 Bollinger %B 因子

**User Story:** As a 策略開發者, I want Bollinger %B 因子用於波動率均值回歸, so that 我可以識別超買超賣狀態

#### Acceptance Criteria (TDD)

1. WHEN Bollinger %B 計算完成 THEN 系統 SHALL 使用 TA-Lib BBANDS 函數
2. WHEN %B < 0 THEN 系統 SHALL 標記為超賣
3. WHEN %B > 1 THEN 系統 SHALL 標記為超買
4. **CRITICAL (Look-ahead)**: WHEN 修改 T+1 數據 THEN 系統 SHALL 保持 T 時刻訊號不變

---

### Requirement 8: P2 Efficiency Ratio 市場狀態因子

**User Story:** As a 策略開發者, I want Efficiency Ratio 識別趨勢/震盪市場, so that 我可以動態選擇適合的策略類型

#### Acceptance Criteria (TDD)

1. WHEN ER 計算完成 THEN 系統 SHALL 返回值在 [0, 1] 範圍
2. WHEN ER > 0.5 THEN 系統 SHALL 標記為趨勢市場
3. WHEN ER < 0.3 THEN 系統 SHALL 標記為震盪市場
4. **CRITICAL (Look-ahead)**: WHEN 修改 T+1 數據 THEN 系統 SHALL 保持 T 時刻訊號不變

---

### Requirement 9: P2 Look-ahead Bias 驗證框架 (TTPT)

**User Story:** As a 策略開發者, I want Time Travel Perturbation Test 框架, so that 所有新因子都能自動驗證無 look-ahead bias

#### Acceptance Criteria (TDD)

1. WHEN 執行 TTPT 單次擾動測試 THEN 系統 SHALL 驗證 T-1 之前訊號不變
2. WHEN 執行 TTPT 100 次擾動測試 THEN 系統 SHALL 全部通過
3. WHEN 執行 TTPT 多日擾動測試 (T+1, T+2, T+3) THEN 系統 SHALL 全部通過
4. WHEN CI/CD 觸發 THEN 系統 SHALL 自動執行 TTPT 測試
5. WHEN Runtime 執行 THEN 系統 SHALL 以 1% 機率採樣執行 TTPT

---

## Non-Functional Requirements

### Code Architecture and Modularity
- **Single Responsibility Principle**: 每個因子函數只負責一種計算
- **Modular Design**: 因子、過濾器、評分器分離為獨立模組
- **Dependency Management**: TA-Lib 透過 Finlab 整合，減少直接依賴
- **Clear Interfaces**: Factor → Container → Signal 標準化介面

### Performance
- 單因子計算時間 < 100ms (1000 股 × 252 天)
- TTPT 100 次擾動測試 < 10 秒
- 流動性過濾 < 50ms

### Testing
- **TDD 覆蓋率**: ≥ 80% (unit + integration)
- **TTPT 覆蓋率**: 100% 新因子
- **CI/CD 整合**: 所有 PR 自動執行測試

### Security
- API keys 不得硬編碼
- 敏感數據不得記錄到日誌

### Reliability
- 因子計算失敗時提供 fallback
- 流動性數據缺失時使用預設門檻
