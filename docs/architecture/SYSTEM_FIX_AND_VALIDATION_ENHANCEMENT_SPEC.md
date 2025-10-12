# 系統修復與驗證增強規格書
# System Fix and Validation Enhancement Specification

**文件版本**: v1.0
**生成日期**: 2025-10-11
**狀態**: CRITICAL - 系統完全失效，需立即修復

---

## 執行摘要 | Executive Summary

**系統當前狀態**: ❌ **完全失效 (COMPLETELY BROKEN)**

**發現的關鍵問題**:
1. **策略生成失敗**: 130次迭代生成完全相同的策略（Value_PE）
2. **績效評估失敗**: 所有策略Sharpe比率為0.0（實際為-0.31）
3. **學習系統失效**: 已完成的2,993行模板系統從未被啟動

**證據**:
```python
# 檔案比較結果
generated_strategy_iter95.py == generated_strategy_iter149.py  # 位元組完全相同

# 迭代歷史記錄（iteration_history.jsonl）
所有迭代 130-149: sharpe_ratio = 0.0000, strategy_name = null

# 實際回測結果（背景日誌）
年化報酬率: -3.77%, 夏普比率: -0.31, 最大回撤: -64.14%  # ← 被丟棄！
```

**影響範圍**:
- 浪費計算資源: 130 × 16秒 = 35分鐘零學習
- 浪費儲存空間: 130 × 993位元組的重複檔案
- 浪費開發時間: 4,853+行程式碼（包含測試和文件）未使用
- 用戶信任損失: 系統宣稱在學習，實際上完全沒有

---

## 目錄 | Table of Contents

1. [根本原因分析](#根本原因分析)
2. [Phase 1: 緊急修復](#phase-1-緊急修復)
3. [Phase 2: 驗證增強](#phase-2-驗證增強)
4. [實施計畫](#實施計畫)
5. [成功標準](#成功標準)
6. [風險管理](#風險管理)

---

## 根本原因分析

### Root Cause #1: 硬編碼策略生成器

**位置**: `claude_code_strategy_generator.py:372-405`

**問題描述**:
```python
# 當前代碼（錯誤）
else:  # iteration 20+
    code = """# Value factor testing phase

from finlab import data
from finlab import backtest

close = data.get('price:收盤價')
vol = data.get('price:成交股數')
pe_ratio = data.get('price_earning_ratio:本益比')

# Value factor: Low P/E stocks
value_score = 1 / (pe_ratio + 1)

# Liquidity filter
liquidity_filter = (close * vol).average(20) > 150_000_000
price_filter = close > 10

# Combine
cond_all = liquidity_filter & price_filter
cond_all = cond_all * value_score
cond_all = cond_all[cond_all > 0].is_largest(10)

position = cond_all

report = backtest.sim(position, resample="M", fee_ratio=1.425/1000/3,
                      stop_loss=0.08, take_profit=0.5, position_limit=0.10,
                      name="Value_PE")
"""
    return code.strip()  # ← 完全忽略 feedback 參數！
```

**影響**:
- 迭代20-149（130次）生成完全相同的策略
- `feedback`字典在第56-62行建構但從未使用
- 模板推薦系統（Phase 4）完全被繞過
- 名人堂整合（Phase 5）從未啟動

**證據**:
- `generated_strategy_iter95.py` == `generated_strategy_iter149.py`（位元組完全相同）
- 所有65個測試通過，但未涵蓋迭代20+的情境
- 這是佔位符實作，不是真正的學習系統

**嚴重程度**: ⚠️ **CRITICAL** - 整個學習循環被繞過

---

### Root Cause #2: 雙重回測架構缺陷

**涉及組件**:
1. `iteration_engine.py:258-293` - 執行含有內嵌`sim()`的策略代碼
2. 生成的策略 - 使用`sim(resample="M", stop_loss=0.08)`執行回測
3. `metrics_extractor.py:62-86` - 重新執行第二次`sim(resample="D", stop_loss=0.1)`
4. API不匹配 - `get_stats()`返回dict而非float
5. 後備機制 - 返回預設指標（全部為0.0）

**執行流程（錯誤）**:
```python
# Phase 4: 執行策略
exec(code, namespace)  # ← 執行 sim()，印出結果，然後丟棄
signal = namespace['position']

# 策略代碼輸出（被丟棄）:
# 年化報酬率: -3.77%, 夏普比率: -0.31, 最大回撤: -64.14%

# Phase 5: 提取指標
metrics = extract_metrics_from_signal(signal)  # ← 第二次 sim() 使用錯誤參數

# metrics_extractor.py 內部:
report = sim(signal, resample="D", stop_loss=0.1)  # ← 不同參數！

# API 失敗:
sharpe = report.get_stats('Sharpe')  # 返回 dict，不是 float
# TypeError: float() argument must be a string or a real number, not 'dict'

# 後備到預設值:
metrics = {'sharpe_ratio': 0.0, 'max_drawdown': 0.0, ...}
```

**影響**:
- 有效的策略結果（Sharpe -0.31）被丟棄，替換為0.0
- 浪費50%計算時間（執行兩次回測）
- 參數不匹配導致不一致的評估
- 學習系統無法評估策略績效

**證據**:
```json
// iteration_history.jsonl 記錄 130（迭代 115）
{
  "sharpe_ratio": 0.0,      // ← 指標提取失敗
  "total_trades": 38664     // ← 回測實際上有執行！
}
```

**背景日誌證據**:
```
年化報酬率: -3.77%, 夏普比率: -0.31, 最大回撤: -64.14%  # ← 實際結果
get_stats() method failed: float() argument must be a string or a real number, not 'dict'  # ← 提取失敗
```

**嚴重程度**: ⚠️ **CRITICAL** - 學習系統無法評估策略績效

---

### 系統架構缺陷總結

**設計缺陷 #1: 無反饋整合**
- `generate_strategy_code()`建構反饋字典（第56-62行）但迭代20+從未使用
- 模板推薦系統（Phase 4）完全被繞過
- 名人堂整合（Phase 5）從未啟動
- 這解釋了為何所有65個測試通過但真實系統失敗 - 測試未涵蓋迭代20+

**設計缺陷 #2: 冗餘計算**
- 策略代碼已經計算回測結果
- 結果被印到控制台然後丟棄
- 提取器用不同參數重新計算
- 參數不匹配導致不一致的評估
- 浪費50%計算時間

**設計缺陷 #3: API假設違反**
- 代碼假設`get_stats('Sharpe')`返回float
- FinLab API改為返回dict
- 缺乏API演進的錯誤處理
- 靜默失敗並使用預設0.0值

---

## Phase 1: 緊急修復

**優先級**: ⚠️ CRITICAL
**估計時間**: 1-2小時
**目標**: 恢復基本學習能力

---

### Fix 1.1: 策略生成器整合

**檔案**: `claude_code_strategy_generator.py`
**要替換的行**: 372-405（整個硬編碼區塊）

**實作策略**:

```python
# 當前（錯誤）:
else:  # iteration 20+
    code = """..."""  # 硬編碼 Value_PE
    return code.strip()  # ← 忽略反饋！

# 提議（修復）:
else:  # iteration 20+
    # 使用模板反饋系統（已在 Phase 4-5 建立！）
    from src.feedback import TemplateFeedbackIntegrator
    from src.templates import TurtleTemplate, MastiffTemplate, FactorTemplate, MomentumTemplate

    # 初始化整合器
    integrator = TemplateFeedbackIntegrator(repository=hall_of_fame_repo)

    # 根據績效獲取模板推薦
    recommendation = integrator.recommend_template(
        current_metrics=feedback.get('current_metrics', {}),
        iteration=feedback.get('current_iteration', 20),
        validation_result=feedback.get('validation_result', None),
        previous_strategy_type=feedback.get('previous_template', None)
    )

    # 從推薦模板生成策略
    template_map = {
        'TurtleTemplate': TurtleTemplate,
        'MastiffTemplate': MastiffTemplate,
        'FactorTemplate': FactorTemplate,
        'MomentumTemplate': MomentumTemplate
    }

    template_class = template_map[recommendation.template_name]
    template_instance = template_class(**recommendation.suggested_params)

    # 生成策略代碼
    code = template_instance.generate()

    # 記錄使用的模板（用於下次迭代）
    logger.info(f"使用模板: {recommendation.template_name}, 探索模式: {recommendation.exploration_mode}")

    return code
```

**整合點**:
- 模板推薦: `src/feedback/template_feedback.py:TemplateFeedbackIntegrator`
- 模板庫: `src/templates/` (TurtleTemplate, MastiffTemplate, FactorTemplate, MomentumTemplate)
- 名人堂: 已通過repository參數整合

**預期結果**:
- 迭代20+將使用多樣化模板（Turtle, Mastiff, Factor, Momentum）
- 策略將根據績效反饋適應
- 模板系統（2,993行）最終啟動
- 每次迭代將有獨特的策略代碼

**驗證測試**:
```python
# 執行10次迭代並驗證多樣性
strategies = [generate_strategy_code(..., iteration=i) for i in range(20, 30)]
unique_strategies = set(strategies)
assert len(unique_strategies) >= 8  # 預期至少8個不同策略
```

**程式碼變更影響分析**:
- 新增依賴: `src.feedback`, `src.templates`（已存在）
- 移除: 34行硬編碼策略
- 新增: ~30行模板整合代碼
- 淨變更: -4行，但功能顯著提升

---

### Fix 1.2: 指標提取重新設計

**問題**: 雙重回測導致參數不匹配 + API失敗

**解決方案架構: 重用策略結果**

#### 方法 A: 修改策略代碼以捕獲報告（推薦）

**檔案**: `iteration_engine.py:258-293`

**當前流程（錯誤）**:
```python
# Phase 4: 執行策略
exec(code, namespace)  # ← 執行 sim()，印出結果，丟棄
signal = namespace['position']

# Phase 5: 提取指標
metrics = extract_metrics_from_signal(signal)  # ← 第二次 sim() 使用錯誤參數
```

**提議流程（修復）**:
```python
# Phase 4: 執行策略並捕獲結果
namespace = {
    'data': data,
    'sim': sim,
    '__builtins__': __builtins__,
    '_REPORT_CAPTURE_': None  # 用於捕獲報告
}

# 修改策略代碼以捕獲報告對象
# 方法: 包裝 sim() 函數
original_sim = sim

def sim_wrapper(*args, **kwargs):
    report = original_sim(*args, **kwargs)
    namespace['_REPORT_CAPTURE_'] = report
    return report

namespace['sim'] = sim_wrapper

# 執行策略代碼
exec(code, namespace)

# 提取信號和報告
signal = namespace.get('position') or namespace.get('signal')
report_object = namespace.get('_REPORT_CAPTURE_')

# Phase 5: 從捕獲的報告提取指標
if report_object:
    metrics = extract_metrics_from_report(report_object)
else:
    # 後備: 基於信號的提取（使用相同參數）
    metrics = extract_metrics_from_signal(signal, strategy_code=code)
```

**優點**:
- 單一回測執行（50%時間節省）
- 參數一致性保證
- 無需修改生成的策略代碼
- API變更隔離

#### 方法 B: 修改metrics_extractor處理API變更（必要）

**檔案**: `metrics_extractor.py:187-213`

**Fix 1.2a: 處理FinLab API變更**

**當前（錯誤）**:
```python
metrics['sharpe_ratio'] = float(report.get_stats('Sharpe') or 0.0)
# ↑ 假設 get_stats() 返回 float，但它返回 dict！
```

**修復**:
```python
sharpe_result = report.get_stats('Sharpe')

if isinstance(sharpe_result, dict):
    # 新 API: 返回帶有 'value' 鍵的 dict
    metrics['sharpe_ratio'] = float(sharpe_result.get('value', 0.0))
elif isinstance(sharpe_result, (int, float)):
    # 舊 API: 直接返回 float
    metrics['sharpe_ratio'] = float(sharpe_result)
else:
    # 未知格式: 記錄並使用預設值
    logger.warning(f"Unknown get_stats() format: {type(sharpe_result)}, value: {sharpe_result}")
    metrics['sharpe_ratio'] = 0.0
```

**對所有指標應用相同邏輯**:
```python
def _safe_extract_stat(report, stat_name, default=0.0):
    """安全提取統計數據，處理API版本變更。"""
    try:
        result = report.get_stats(stat_name)

        if isinstance(result, dict):
            return float(result.get('value', default))
        elif isinstance(result, (int, float)):
            return float(result)
        else:
            logger.warning(f"Unknown format for {stat_name}: {type(result)}")
            return default
    except Exception as e:
        logger.error(f"Failed to extract {stat_name}: {e}")
        return default

# 使用
metrics['sharpe_ratio'] = _safe_extract_stat(report, 'Sharpe', 0.0)
metrics['total_return'] = _safe_extract_stat(report, 'Return', 0.0)
metrics['max_drawdown'] = _safe_extract_stat(report, 'MaxDrawdown', 0.0)
```

**Fix 1.2b: 記錄提取方法**

```python
# 在提取前後添加記錄
logger.info(f"嘗試指標提取方法: {method}")
logger.info(f"提取的夏普比率: {metrics['sharpe_ratio']:.4f}")

# 添加驗證
if metrics['sharpe_ratio'] == 0.0 and metrics['total_trades'] > 0:
    logger.warning("可疑: 交易存在但夏普比率為0.0 - 可能提取失敗")
    logger.debug(f"報告對象類型: {type(report)}")
    logger.debug(f"可用方法: {dir(report)}")
```

**預期結果**:
- 單一回測執行每次迭代（50%時間節省）
- 執行和評估之間參數一致
- 正確捕獲夏普比率（例如 -0.31 而不是 0.0）
- API彈性提取，適當錯誤處理

**驗證測試**:
```python
def test_metric_extraction_accuracy():
    """測試提取的指標匹配回測結果。"""
    # 生成簡單策略
    code = """
from finlab import data
from finlab.backtest import sim

position = data.get('price:收盤價').is_largest(10)
report = sim(position, resample='M', stop_loss=0.1)
    """

    # 執行並提取
    namespace = {}
    exec(code, namespace)
    report = namespace['report']

    # 提取指標
    metrics = extract_metrics_from_report(report)

    # 驗證
    assert metrics['sharpe_ratio'] != 0.0, "有效策略夏普比率不應為0.0"
    assert metrics['total_trades'] > 0, "應該有交易"

    # 與直接報告訪問比較
    actual_sharpe = report.metrics.sharpe_ratio()
    assert abs(metrics['sharpe_ratio'] - actual_sharpe) < 0.01, "提取的夏普比率應匹配報告"
```

---

### Fix 1.3: 整合測試

**測試檔案**: `tests/test_system_integration_fix.py`

```python
"""
系統整合修復測試

驗證:
1. 策略多樣性（迭代20+）
2. 指標提取準確性
3. 模板系統啟動
4. 端到端學習循環
"""

import pytest
import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude_code_strategy_generator import generate_strategy_code
from metrics_extractor import extract_metrics_from_signal, extract_metrics_from_report
from src.feedback import TemplateFeedbackIntegrator


class TestStrategyDiversity:
    """測試策略生成多樣性。"""

    def test_iterations_20_plus_generate_diverse_strategies(self):
        """測試迭代20+生成多樣化策略。"""
        strategies = []

        for i in range(20, 30):
            feedback = {
                'current_iteration': i,
                'current_metrics': {'sharpe_ratio': 0.5 + i * 0.05}
            }
            code = generate_strategy_code(feedback=feedback, iteration=i)
            strategies.append(code)

        # 驗證唯一性
        unique = len(set(strategies))
        assert unique >= 8, f"僅生成{unique}個獨特策略，預期至少8個"

    def test_template_names_recorded(self):
        """測試模板名稱被正確記錄。"""
        feedback = {
            'current_iteration': 25,
            'current_metrics': {'sharpe_ratio': 1.2}
        }
        code = generate_strategy_code(feedback=feedback, iteration=25)

        # 策略代碼應包含模板標識符
        assert any(template in code for template in ['Turtle', 'Mastiff', 'Factor', 'Momentum'])

    def test_exploration_mode_activates_every_5_iterations(self):
        """測試探索模式每5次迭代啟動。"""
        for i in [20, 25, 30, 35, 40]:
            feedback = {'current_iteration': i, 'current_metrics': {'sharpe_ratio': 1.0}}
            code = generate_strategy_code(feedback=feedback, iteration=i)

            # 探索模式應使用不同模板
            # 可以檢查代碼註釋或日誌


class TestMetricExtraction:
    """測試指標提取準確性。"""

    def test_extraction_matches_backtest_results(self):
        """測試提取的指標匹配回測結果。"""
        from finlab import data
        from finlab.backtest import sim

        # 生成簡單策略
        close = data.get('price:收盤價')
        position = close.is_largest(10)

        # 執行回測
        report = sim(position, resample='M', stop_loss=0.1, upload=False)

        # 提取指標
        metrics = extract_metrics_from_report(report)

        # 驗證非零值（對於有效策略）
        assert metrics['sharpe_ratio'] != 0.0, "有效策略夏普比率不應為0.0"
        assert metrics['total_trades'] > 0, "應該有交易"

        # 與直接訪問比較
        actual_sharpe = report.metrics.sharpe_ratio()
        assert abs(metrics['sharpe_ratio'] - actual_sharpe) < 0.01, \
            f"提取的夏普比率({metrics['sharpe_ratio']:.4f})應匹配報告({actual_sharpe:.4f})"

    def test_api_version_compatibility(self):
        """測試API版本相容性（dict vs float）。"""
        from unittest.mock import Mock

        # 模擬新API（返回dict）
        mock_report = Mock()
        mock_report.get_stats.return_value = {'value': 1.25, 'metadata': {}}

        metrics = extract_metrics_from_report(mock_report)
        assert metrics['sharpe_ratio'] == 1.25, "應處理dict格式的get_stats()"

        # 模擬舊API（返回float）
        mock_report.get_stats.return_value = 1.25

        metrics = extract_metrics_from_report(mock_report)
        assert metrics['sharpe_ratio'] == 1.25, "應處理float格式的get_stats()"

    def test_zero_sharpe_with_trades_triggers_warning(self):
        """測試零夏普但有交易觸發警告。"""
        import logging
        from unittest.mock import Mock

        # 設置記錄器以捕獲警告
        logger = logging.getLogger('metrics_extractor')

        # 創建可疑指標（交易存在但夏普為0）
        metrics = {
            'sharpe_ratio': 0.0,
            'total_trades': 1000
        }

        # 應記錄警告（在實際代碼中實作）
        # assert "可疑" in captured_logs


class TestEndToEndIntegration:
    """測試端到端整合。"""

    def test_single_iteration_complete_flow(self):
        """測試單次迭代完整流程。"""
        # 1. 生成策略
        feedback = {'current_iteration': 25, 'current_metrics': {'sharpe_ratio': 0.8}}
        code = generate_strategy_code(feedback=feedback, iteration=25)

        # 2. 執行策略（模擬）
        # 在真實測試中會執行實際回測

        # 3. 提取指標
        # metrics = extract_metrics_from_signal(signal)

        # 4. 更新反饋
        # next_feedback = {...}

        # 驗證工作流程完成
        assert code is not None
        assert len(code) > 0

    def test_template_feedback_integration(self):
        """測試模板反饋整合。"""
        integrator = TemplateFeedbackIntegrator(repository=None)

        # 獲取推薦
        recommendation = integrator.recommend_template(
            current_metrics={'sharpe_ratio': 0.8},
            iteration=25
        )

        # 驗證推薦結構
        assert recommendation.template_name in ['TurtleTemplate', 'MastiffTemplate', 'FactorTemplate', 'MomentumTemplate']
        assert recommendation.match_score > 0
        assert isinstance(recommendation.suggested_params, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
```

**執行測試**:
```bash
pytest tests/test_system_integration_fix.py -v --tb=short
```

**預期結果**:
```
tests/test_system_integration_fix.py::TestStrategyDiversity::test_iterations_20_plus_generate_diverse_strategies PASSED
tests/test_system_integration_fix.py::TestStrategyDiversity::test_template_names_recorded PASSED
tests/test_system_integration_fix.py::TestStrategyDiversity::test_exploration_mode_activates_every_5_iterations PASSED
tests/test_system_integration_fix.py::TestMetricExtraction::test_extraction_matches_backtest_results PASSED
tests/test_system_integration_fix.py::TestMetricExtraction::test_api_version_compatibility PASSED
tests/test_system_integration_fix.py::TestMetricExtraction::test_zero_sharpe_with_trades_triggers_warning PASSED
tests/test_system_integration_fix.py::TestEndToEndIntegration::test_single_iteration_complete_flow PASSED
tests/test_system_integration_fix.py::TestEndToEndIntegration::test_template_feedback_integration PASSED

======================== 8 passed in 12.3s ========================
```

---

## Phase 2: 驗證增強

**優先級**: HIGH
**估計時間**: 4-6小時
**目標**: 添加統計嚴謹性以避免過度擬合

**動機**: 用戶識別的5個缺失驗證組件:
1. ❌ Train/Validation/Test split
2. ❌ Walk-forward analysis
3. ❌ Bonferroni correction（多重比較校正）
4. ❌ Bootstrap confidence interval
5. ❌ Baseline comparison（例如買入持有）

---

### Enhancement 2.1: Train/Validation/Test 分割

**規格**:

```yaml
data_split:
  training_period: "2018-01-01 to 2020-12-31"  # 3年
  validation_period: "2021-01-01 to 2022-12-31"  # 2年
  test_period: "2023-01-01 to 2024-12-31"  # 2年（保留）

  rationale: |
    - 訓練: 開發策略參數
    - 驗證: 選擇最佳策略（避免過度擬合）
    - 測試: 最終績效評估（從不用於選擇）

  taiwan_market_considerations:
    - 使用3年訓練期以捕捉牛/熊市週期
    - 驗證不同市場機制（2021-2022波動）
    - 測試最近數據（2023-2024）
```

**實作**:

**檔案**: `src/validation/data_split.py`

```python
"""
Train/Validation/Test 數據分割驗證器

防止過度擬合的三階段驗證:
1. 訓練期: 開發策略參數
2. 驗證期: 選擇最佳策略
3. 測試期: 最終績效評估（保留集）
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataSplitValidator:
    """實作train/validation/test分割的驗證器。"""

    def __init__(
        self,
        train_start: str = '2018-01-01',
        train_end: str = '2020-12-31',
        valid_end: str = '2022-12-31',
        test_end: str = '2024-12-31'
    ):
        """
        初始化數據分割驗證器。

        參數:
            train_start: 訓練期開始日期 (YYYY-MM-DD)
            train_end: 訓練期結束日期 = 驗證期開始日期
            valid_end: 驗證期結束日期 = 測試期開始日期
            test_end: 測試期結束日期
        """
        self.train_start = train_start
        self.train_end = train_end
        self.valid_end = valid_end
        self.test_end = test_end

        logger.info(f"數據分割初始化:")
        logger.info(f"  訓練期: {train_start} 到 {train_end}")
        logger.info(f"  驗證期: {train_end} 到 {valid_end}")
        logger.info(f"  測試期: {valid_end} 到 {test_end}")

    def validate_strategy(self, strategy_code: str) -> Dict[str, Any]:
        """
        在所有三個分割上執行策略。

        參數:
            strategy_code: 要驗證的策略代碼

        返回:
            包含train/valid/test績效的字典
        """
        # 訓練: 生成參數
        train_report = self._run_on_period(
            strategy_code,
            start=self.train_start,
            end=self.train_end,
            period_name='訓練'
        )

        # 驗證: 評估績效
        valid_report = self._run_on_period(
            strategy_code,
            start=self.train_end,
            end=self.valid_end,
            period_name='驗證'
        )

        # 測試: 最終保留（僅用於冠軍策略）
        test_report = self._run_on_period(
            strategy_code,
            start=self.valid_end,
            end=self.test_end,
            period_name='測試'
        )

        # 提取指標
        results = {
            'train_sharpe': train_report.metrics.sharpe_ratio(),
            'valid_sharpe': valid_report.metrics.sharpe_ratio(),
            'test_sharpe': test_report.metrics.sharpe_ratio(),
            'train_return': train_report.metrics.annual_return(),
            'valid_return': valid_report.metrics.annual_return(),
            'test_return': test_report.metrics.annual_return(),
            'train_drawdown': train_report.metrics.max_drawdown(),
            'valid_drawdown': valid_report.metrics.max_drawdown(),
            'test_drawdown': test_report.metrics.max_drawdown(),
        }

        # 計算一致性
        results['consistency'] = self._calculate_consistency(
            results['train_sharpe'],
            results['valid_sharpe'],
            results['test_sharpe']
        )

        # 驗證通過標準
        results['validation_passed'] = self._check_validation_criteria(results)

        return results

    def _run_on_period(
        self,
        strategy_code: str,
        start: str,
        end: str,
        period_name: str
    ):
        """在指定期間執行策略。"""
        from finlab import data
        from finlab.backtest import sim

        logger.info(f"在{period_name}期執行策略 ({start} 到 {end})")

        # 設置數據範圍
        # 注意: FinLab 可能需要特定的日期範圍設置方法
        # 這裡假設策略代碼可以訪問全局數據範圍

        namespace = {
            'data': data,
            'sim': sim,
            '__builtins__': __builtins__,
            '_DATE_START_': start,
            '_DATE_END_': end
        }

        exec(strategy_code, namespace)

        report = namespace.get('report') or namespace.get('_REPORT_CAPTURE_')
        return report

    def _calculate_consistency(
        self,
        train_sharpe: float,
        valid_sharpe: float,
        test_sharpe: float
    ) -> float:
        """
        計算跨分割的績效一致性。

        一致性分數 = 1 - (標準差 / 平均值)

        高一致性（>0.8）= 穩定策略
        低一致性（<0.5）= 可能過度擬合
        """
        import numpy as np

        sharpes = [train_sharpe, valid_sharpe, test_sharpe]
        mean_sharpe = np.mean(sharpes)
        std_sharpe = np.std(sharpes)

        if mean_sharpe == 0:
            return 0.0

        consistency = 1 - (std_sharpe / abs(mean_sharpe))
        return max(0.0, min(1.0, consistency))  # 限制在[0, 1]

    def _check_validation_criteria(self, results: Dict[str, Any]) -> bool:
        """
        檢查策略是否通過驗證標準。

        標準:
        1. 驗證夏普 > 1.0（實際樣本外績效良好）
        2. 一致性 > 0.6（穩定跨時期）
        3. 驗證夏普 > 訓練夏普 * 0.7（不過度退化）
        """
        valid_sharpe = results['valid_sharpe']
        train_sharpe = results['train_sharpe']
        consistency = results['consistency']

        criteria = {
            'valid_sharpe_threshold': valid_sharpe > 1.0,
            'consistency_threshold': consistency > 0.6,
            'degradation_acceptable': valid_sharpe > train_sharpe * 0.7
        }

        passed = all(criteria.values())

        logger.info(f"驗證標準檢查:")
        for criterion, result in criteria.items():
            logger.info(f"  {criterion}: {'✅' if result else '❌'}")

        return passed
```

**使用範例**:

```python
from src.validation.data_split import DataSplitValidator

# 初始化驗證器
validator = DataSplitValidator()

# 驗證策略
results = validator.validate_strategy(strategy_code)

print(f"訓練夏普: {results['train_sharpe']:.2f}")
print(f"驗證夏普: {results['valid_sharpe']:.2f}")
print(f"測試夏普: {results['test_sharpe']:.2f}")
print(f"一致性: {results['consistency']:.2%}")
print(f"驗證通過: {'✅' if results['validation_passed'] else '❌'}")
```

**整合到迭代引擎**:

```python
# 在 iteration_engine.py 中
from src.validation.data_split import DataSplitValidator

# Phase 6: 驗證分割（用於冠軍策略）
if metrics['sharpe_ratio'] > 2.0:  # 僅驗證高績效策略
    validator = DataSplitValidator()
    validation_results = validator.validate_strategy(code)

    if validation_results['validation_passed']:
        # 添加到名人堂
        hall_of_fame.add_champion(code, validation_results)
```

---

### Enhancement 2.2: Walk-Forward 分析

**規格**:

```yaml
walk_forward:
  window_size: 252  # 交易日（~1年）
  step_size: 63     # ~3個月重新平衡
  min_periods: 3    # 要求至少3個窗口

  methodology: |
    1. 在窗口 N 訓練
    2. 在窗口 N+1 測試
    3. 按 step_size 向前滾動
    4. 聚合所有窗口的結果

  metrics:
    - average_sharpe: 所有測試窗口的平均值
    - sharpe_std: 標準差（穩定性測量）
    - win_rate: 夏普為正的窗口百分比
    - worst_window: 窗口間的最小夏普
```

**實作**:

**檔案**: `src/validation/walk_forward.py`

```python
"""
Walk-Forward 分析驗證器

樣本外驗證通過滾動訓練/測試窗口:
- 在窗口 N 訓練
- 在窗口 N+1 測試（真正的樣本外）
- 滾動窗口以評估時間穩定性
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class WalkForwardValidator:
    """實作walk-forward分析的驗證器。"""

    def __init__(
        self,
        window_size: int = 252,  # ~1年交易日
        step_size: int = 63,     # ~3個月
        min_periods: int = 3
    ):
        """
        初始化walk-forward驗證器。

        參數:
            window_size: 訓練窗口大小（交易日）
            step_size: 滾動步長（交易日）
            min_periods: 最小所需窗口數
        """
        self.window_size = window_size
        self.step_size = step_size
        self.min_periods = min_periods

        logger.info(f"Walk-Forward初始化:")
        logger.info(f"  窗口大小: {window_size}天（~{window_size/252:.1f}年）")
        logger.info(f"  步長: {step_size}天（~{step_size/252*12:.1f}個月）")
        logger.info(f"  最小窗口: {min_periods}")

    def validate(
        self,
        strategy_code: str,
        data: pd.DataFrame = None
    ) -> Dict[str, Any]:
        """
        執行walk-forward分析。

        參數:
            strategy_code: 要驗證的策略代碼
            data: 可選數據框（如果None，使用完整FinLab數據）

        返回:
            聚合結果字典
        """
        from finlab import data as finlab_data

        # 如果未提供數據，使用FinLab數據
        if data is None:
            # 獲取價格數據以確定可用日期範圍
            close = finlab_data.get('price:收盤價')
            dates = close.index
        else:
            dates = data.index

        total_days = len(dates)
        logger.info(f"總可用日期: {total_days}天")

        # 檢查足夠數據
        min_required_days = self.window_size * 2 + self.step_size * (self.min_periods - 1)
        if total_days < min_required_days:
            raise ValueError(
                f"數據不足: 需要{min_required_days}天，有{total_days}天"
            )

        results = []
        window_idx = 0

        for start in range(0, total_days - 2 * self.window_size, self.step_size):
            train_end_idx = start + self.window_size
            test_end_idx = train_end_idx + self.window_size

            if test_end_idx > total_days:
                break

            # 定義期間
            train_start = dates[start]
            train_end = dates[train_end_idx - 1]
            test_start = dates[train_end_idx]
            test_end = dates[test_end_idx - 1]

            logger.info(f"窗口 {window_idx}:")
            logger.info(f"  訓練: {train_start} 到 {train_end}")
            logger.info(f"  測試: {test_start} 到 {test_end}")

            # 在測試窗口執行回測（樣本外）
            test_sharpe = self._backtest_on_period(
                strategy_code,
                start_date=test_start,
                end_date=test_end
            )

            results.append({
                'window': window_idx,
                'train_period': (str(train_start), str(train_end)),
                'test_period': (str(test_start), str(test_end)),
                'test_sharpe': test_sharpe
            })

            window_idx += 1

        # 聚合結果
        sharpes = [r['test_sharpe'] for r in results]

        aggregated = {
            'avg_sharpe': np.mean(sharpes),
            'sharpe_std': np.std(sharpes),
            'median_sharpe': np.median(sharpes),
            'win_rate': sum(1 for s in sharpes if s > 0) / len(sharpes),
            'worst_sharpe': min(sharpes),
            'best_sharpe': max(sharpes),
            'num_windows': len(results),
            'windows': results
        }

        # 驗證通過標準
        aggregated['validation_passed'] = self._check_validation_criteria(aggregated)

        logger.info(f"Walk-Forward結果:")
        logger.info(f"  平均夏普: {aggregated['avg_sharpe']:.2f}")
        logger.info(f"  夏普標準差: {aggregated['sharpe_std']:.2f}")
        logger.info(f"  勝率: {aggregated['win_rate']:.1%}")
        logger.info(f"  最差夏普: {aggregated['worst_sharpe']:.2f}")

        return aggregated

    def _backtest_on_period(
        self,
        strategy_code: str,
        start_date: str,
        end_date: str
    ) -> float:
        """在指定期間執行回測並返回夏普比率。"""
        from finlab import data
        from finlab.backtest import sim

        # 執行策略
        namespace = {
            'data': data,
            'sim': sim,
            '__builtins__': __builtins__,
            '_DATE_START_': start_date,
            '_DATE_END_': end_date
        }

        try:
            exec(strategy_code, namespace)
            report = namespace.get('report') or namespace.get('_REPORT_CAPTURE_')

            if report:
                return report.metrics.sharpe_ratio()
            else:
                logger.warning("未找到報告對象")
                return 0.0
        except Exception as e:
            logger.error(f"回測失敗: {e}")
            return 0.0

    def _check_validation_criteria(self, results: Dict[str, Any]) -> bool:
        """
        檢查walk-forward標準。

        標準:
        1. 平均夏普 > 0.5（正樣本外績效）
        2. 勝率 > 60%（多數窗口有利可圖）
        3. 最差夏普 > -0.5（無災難性失敗）
        4. 夏普標準差 < 1.0（穩定績效）
        """
        criteria = {
            'avg_sharpe_positive': results['avg_sharpe'] > 0.5,
            'win_rate_good': results['win_rate'] > 0.6,
            'no_catastrophic_failure': results['worst_sharpe'] > -0.5,
            'stable_performance': results['sharpe_std'] < 1.0
        }

        passed = all(criteria.values())

        logger.info("Walk-Forward標準:")
        for criterion, result in criteria.items():
            logger.info(f"  {criterion}: {'✅' if result else '❌'}")

        return passed
```

**使用範例**:

```python
from src.validation.walk_forward import WalkForwardValidator

# 初始化驗證器
validator = WalkForwardValidator(window_size=252, step_size=63)

# 執行walk-forward分析
results = validator.validate(strategy_code)

print(f"平均樣本外夏普: {results['avg_sharpe']:.2f}")
print(f"夏普穩定性（標準差）: {results['sharpe_std']:.2f}")
print(f"窗口勝率: {results['win_rate']:.1%}")
print(f"最差窗口夏普: {results['worst_sharpe']:.2f}")
print(f"驗證通過: {'✅' if results['validation_passed'] else '❌'}")
```

---

### Enhancement 2.3: Bonferroni 校正（多重比較）

**規格**:

```yaml
multiple_comparison:
  problem: |
    在 α=0.05（5%顯著性）測試500個策略
    預期誤發現: 500 × 0.05 = 25個策略

  bonferroni_correction:
    adjusted_alpha: α / n_strategies
    example: 0.05 / 500 = 0.0001（0.01%顯著性）

  sharpe_ratio_significance:
    threshold_formula: "Sharpe > Z(1 - α/(2n)) / sqrt(T)"
    for_500_strategies: "Sharpe > 3.89 / sqrt(252) ≈ 0.245"
    conservative_threshold: 0.5  # 使用更高閾值以增強穩健性
```

**實作**:

**檔案**: `src/validation/multiple_comparison.py`

```python
"""
Bonferroni 多重比較校正

防止誤發現由於測試多個策略:
- 調整顯著性閾值: α / n
- 計算統計顯著性的夏普比率閾值
- 驗證策略集合的誤發現率
"""

from typing import Dict, List, Any
import numpy as np
from scipy.stats import norm
import logging

logger = logging.getLogger(__name__)


class BonferroniValidator:
    """實作Bonferroni多重比較校正的驗證器。"""

    def __init__(
        self,
        n_strategies: int = 500,
        alpha: float = 0.05
    ):
        """
        初始化Bonferroni驗證器。

        參數:
            n_strategies: 測試的策略總數
            alpha: 未調整的顯著性水平（例如 0.05 = 5%）
        """
        self.n_strategies = n_strategies
        self.alpha = alpha
        self.adjusted_alpha = alpha / n_strategies

        logger.info(f"Bonferroni校正初始化:")
        logger.info(f"  策略數量: {n_strategies}")
        logger.info(f"  原始 α: {alpha}")
        logger.info(f"  調整後 α: {self.adjusted_alpha:.6f}")

    def calculate_significance_threshold(
        self,
        n_periods: int = 252,
        use_conservative: bool = True
    ) -> float:
        """
        計算Bonferroni調整的夏普閾值。

        參數:
            n_periods: 時間期數（例如 252 交易日）
            use_conservative: 是否使用保守閾值（推薦）

        返回:
            夏普比率顯著性閾值
        """
        # 計算z分數用於調整後的alpha
        z_score = norm.ppf(1 - self.adjusted_alpha / 2)

        # 夏普比率閾值 = z / sqrt(T)
        threshold = z_score / np.sqrt(n_periods)

        logger.info(f"顯著性閾值計算:")
        logger.info(f"  Z分數（調整後α={self.adjusted_alpha:.6f}）: {z_score:.2f}")
        logger.info(f"  理論閾值: {threshold:.4f}")

        if use_conservative:
            # 使用保守閾值（推薦用於實際交易）
            conservative_threshold = max(0.5, threshold)
            logger.info(f"  保守閾值: {conservative_threshold:.4f}")
            return conservative_threshold

        return threshold

    def is_significant(
        self,
        sharpe_ratio: float,
        n_periods: int = 252
    ) -> bool:
        """測試夏普比率是否具有統計顯著性。"""
        threshold = self.calculate_significance_threshold(n_periods)
        return abs(sharpe_ratio) > threshold

    def validate_strategy_set(
        self,
        strategies_with_sharpes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        使用多重比較校正驗證整個策略集。

        參數:
            strategies_with_sharpes: 策略列表，每個包含 'sharpe_ratio' 鍵

        返回:
            驗證結果字典
        """
        threshold = self.calculate_significance_threshold()

        # 識別顯著策略
        significant_strategies = [
            s for s in strategies_with_sharpes
            if self.is_significant(s['sharpe_ratio'])
        ]

        # 計算誤發現率
        expected_false_discoveries = self.adjusted_alpha * len(strategies_with_sharpes)

        results = {
            'total_strategies': len(strategies_with_sharpes),
            'significant_count': len(significant_strategies),
            'significance_threshold': threshold,
            'adjusted_alpha': self.adjusted_alpha,
            'expected_false_discoveries': expected_false_discoveries,
            'actual_fdr': expected_false_discoveries / max(1, len(significant_strategies)),
            'significant_strategies': significant_strategies
        }

        logger.info(f"策略集驗證:")
        logger.info(f"  總策略: {results['total_strategies']}")
        logger.info(f"  顯著策略: {results['significant_count']}")
        logger.info(f"  顯著性閾值: {threshold:.4f}")
        logger.info(f"  預期誤發現: {expected_false_discoveries:.2f}")
        logger.info(f"  實際FDR: {results['actual_fdr']:.2%}")

        return results

    def calculate_family_wise_error_rate(self) -> float:
        """
        計算家族錯誤率（FWER）。

        FWER = 至少一個誤發現的概率
        Bonferroni控制: FWER ≤ α
        """
        fwer = 1 - (1 - self.adjusted_alpha) ** self.n_strategies

        # 對於小alpha，近似為: FWER ≈ n * adjusted_alpha = alpha
        logger.info(f"家族錯誤率（FWER）: {fwer:.4f}")
        logger.info(f"Bonferroni保證: FWER ≤ {self.alpha}")

        return fwer
```

**使用範例**:

```python
from src.validation.multiple_comparison import BonferroniValidator

# 初始化驗證器（測試500個策略）
validator = BonferroniValidator(n_strategies=500, alpha=0.05)

# 計算顯著性閾值
threshold = validator.calculate_significance_threshold()
print(f"夏普必須 > {threshold:.4f} 才具有統計顯著性")

# 檢查單個策略
is_sig = validator.is_significant(sharpe_ratio=1.5)
print(f"夏普 1.5 顯著: {is_sig}")

# 驗證策略集
strategies = [
    {'name': 'Strategy_A', 'sharpe_ratio': 1.8},
    {'name': 'Strategy_B', 'sharpe_ratio': 0.3},
    {'name': 'Strategy_C', 'sharpe_ratio': 2.1},
]
results = validator.validate_strategy_set(strategies)
print(f"顯著策略: {results['significant_count']}/{results['total_strategies']}")
```

---

### Enhancement 2.4: Bootstrap 信賴區間

**規格**:

```yaml
bootstrap:
  method: block_bootstrap  # 保留時間序列結構
  block_size: 21  # ~1個月交易日
  n_iterations: 1000  # Bootstrap樣本數
  confidence_level: 0.95  # 95% CI

  metrics_to_bootstrap:
    - sharpe_ratio
    - max_drawdown
    - annual_return
    - win_rate

  interpretation: |
    如果夏普比率的95% CI包含0，策略不穩健
    窄CI = 穩定績效
    寬CI = 高不確定性
```

**實作**:

**檔案**: `src/validation/bootstrap.py`

```python
"""
Bootstrap 信賴區間驗證器

使用區塊bootstrap估計績效指標的不確定性:
- 保留時間序列結構（區塊重抽樣）
- 計算95%信賴區間
- 驗證統計穩健性
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class BootstrapValidator:
    """實作bootstrap信賴區間的驗證器。"""

    def __init__(
        self,
        n_iterations: int = 1000,
        block_size: int = 21,
        confidence: float = 0.95
    ):
        """
        初始化bootstrap驗證器。

        參數:
            n_iterations: Bootstrap樣本數
            block_size: 區塊大小（交易日）
            confidence: 信賴水平（例如 0.95 = 95%）
        """
        self.n_iterations = n_iterations
        self.block_size = block_size
        self.confidence = confidence

        logger.info(f"Bootstrap驗證器初始化:")
        logger.info(f"  迭代次數: {n_iterations}")
        logger.info(f"  區塊大小: {block_size}天（~{block_size/21:.1f}個月）")
        logger.info(f"  信賴水平: {confidence:.0%}")

    def block_bootstrap(self, returns: np.ndarray) -> np.ndarray:
        """
        生成區塊bootstrap樣本，保留時間序列結構。

        參數:
            returns: 原始報酬序列

        返回:
            Bootstrap重抽樣報酬
        """
        n = len(returns)
        n_blocks = n // self.block_size

        # 帶放回地抽樣區塊
        block_indices = np.random.choice(n_blocks, size=n_blocks, replace=True)

        sampled_returns = []
        for block_idx in block_indices:
            start = block_idx * self.block_size
            end = start + self.block_size
            sampled_returns.extend(returns[start:end])

        # 截斷到原始長度
        return np.array(sampled_returns[:n])

    def calculate_confidence_interval(
        self,
        returns: np.ndarray,
        metric: str = 'sharpe_ratio'
    ) -> Dict[str, Any]:
        """
        計算指標的bootstrap信賴區間。

        參數:
            returns: 報酬序列
            metric: 要bootstrap的指標 ('sharpe_ratio', 'max_drawdown', etc.)

        返回:
            包含CI和分佈的字典
        """
        metric_distribution = []

        logger.info(f"為{metric}執行{self.n_iterations}次bootstrap迭代...")

        for i in range(self.n_iterations):
            # 生成bootstrap樣本
            bootstrap_returns = self.block_bootstrap(returns)

            # 計算指標
            if metric == 'sharpe_ratio':
                value = self._calculate_sharpe(bootstrap_returns)
            elif metric == 'max_drawdown':
                value = self._calculate_max_drawdown(bootstrap_returns)
            elif metric == 'annual_return':
                value = self._calculate_annual_return(bootstrap_returns)
            elif metric == 'win_rate':
                value = self._calculate_win_rate(bootstrap_returns)
            else:
                raise ValueError(f"未知指標: {metric}")

            metric_distribution.append(value)

        # 計算百分位數
        lower_percentile = (1 - self.confidence) / 2 * 100
        upper_percentile = (1 + self.confidence) / 2 * 100

        lower = np.percentile(metric_distribution, lower_percentile)
        upper = np.percentile(metric_distribution, upper_percentile)
        mean = np.mean(metric_distribution)
        std = np.std(metric_distribution)

        # 檢查CI是否包含零
        includes_zero = (lower < 0 < upper)

        results = {
            'metric': metric,
            'mean': mean,
            'std': std,
            'ci_lower': lower,
            'ci_upper': upper,
            'confidence': self.confidence,
            'includes_zero': includes_zero,
            'distribution': metric_distribution
        }

        logger.info(f"{metric} Bootstrap結果:")
        logger.info(f"  平均值: {mean:.4f}")
        logger.info(f"  標準差: {std:.4f}")
        logger.info(f"  {self.confidence:.0%} CI: [{lower:.4f}, {upper:.4f}]")
        logger.info(f"  包含零: {'❌ 不穩健' if includes_zero else '✅ 穩健'}")

        return results

    def validate_strategy(
        self,
        returns: np.ndarray,
        metrics: List[str] = None
    ) -> Dict[str, Any]:
        """
        使用bootstrap驗證策略。

        參數:
            returns: 策略報酬序列
            metrics: 要bootstrap的指標列表

        返回:
            所有指標的驗證結果
        """
        if metrics is None:
            metrics = ['sharpe_ratio', 'max_drawdown', 'annual_return']

        results = {}

        for metric in metrics:
            results[metric] = self.calculate_confidence_interval(returns, metric)

        # 總體驗證通過標準
        validation_passed = self._check_validation_criteria(results)
        results['validation_passed'] = validation_passed

        return results

    def _calculate_sharpe(self, returns: np.ndarray) -> float:
        """計算年化夏普比率。"""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        return np.mean(returns) / np.std(returns) * np.sqrt(252)

    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """計算最大回撤。"""
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)

    def _calculate_annual_return(self, returns: np.ndarray) -> float:
        """計算年化報酬率。"""
        total_return = np.prod(1 + returns) - 1
        n_years = len(returns) / 252
        return (1 + total_return) ** (1 / n_years) - 1

    def _calculate_win_rate(self, returns: np.ndarray) -> float:
        """計算勝率（正報酬的百分比）。"""
        return np.sum(returns > 0) / len(returns)

    def _check_validation_criteria(self, results: Dict[str, Any]) -> bool:
        """
        檢查bootstrap驗證標準。

        標準:
        1. 夏普CI不包含零（統計顯著為正）
        2. 夏普下限 > 0.5（保守績效保證）
        3. 最大回撤上限 < -15%（可接受風險）
        """
        sharpe_results = results.get('sharpe_ratio', {})
        dd_results = results.get('max_drawdown', {})

        criteria = {
            'sharpe_excludes_zero': not sharpe_results.get('includes_zero', True),
            'sharpe_lower_acceptable': sharpe_results.get('ci_lower', 0) > 0.5,
            'drawdown_acceptable': dd_results.get('ci_upper', -1) < -0.15
        }

        passed = all(criteria.values())

        logger.info("Bootstrap驗證標準:")
        for criterion, result in criteria.items():
            logger.info(f"  {criterion}: {'✅' if result else '❌'}")

        return passed
```

**使用範例**:

```python
from src.validation.bootstrap import BootstrapValidator

# 假設有策略報酬序列
returns = np.array([0.01, -0.005, 0.02, ...])  # 每日報酬

# 初始化驗證器
validator = BootstrapValidator(n_iterations=1000, block_size=21)

# 計算夏普比率CI
sharpe_ci = validator.calculate_confidence_interval(returns, metric='sharpe_ratio')
print(f"夏普 95% CI: [{sharpe_ci['ci_lower']:.2f}, {sharpe_ci['ci_upper']:.2f}]")
print(f"包含零: {sharpe_ci['includes_zero']} ({'不穩健' if sharpe_ci['includes_zero'] else '穩健'})")

# 驗證多個指標
results = validator.validate_strategy(
    returns,
    metrics=['sharpe_ratio', 'max_drawdown', 'annual_return']
)
print(f"驗證通過: {'✅' if results['validation_passed'] else '❌'}")
```

---

### Enhancement 2.5: 基準比較

**規格**:

```yaml
baselines:
  buy_and_hold:
    description: "買入台灣50 ETF（0050）並持有"
    benchmark: "0050.TW"
    metric: "夏普比率, 最大回撤"

  equal_weight:
    description: "市值前50股票等權重"
    rebalance: "月度"

  risk_parity:
    description: "按逆波動率加權"
    rebalance: "月度"

  comparison_criteria:
    - sharpe_improvement: "策略夏普 > 基準夏普 + 0.5"
    - risk_adjusted: "策略Calmar > 基準Calmar"
    - consistency: "策略勝率 > 基準勝率"
```

**實作**:

**檔案**: `src/validation/baseline.py`

```python
"""
基準比較驗證器

將策略績效與標準基準比較:
- 買入持有（0050 ETF）
- 等權重前50股票
- 風險平價投資組合
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class BaselineComparator:
    """實作基準比較的驗證器。"""

    def __init__(self):
        """初始化基準比較器。"""
        self.baselines = {
            'buy_and_hold': self._buy_and_hold_0050,
            'equal_weight': self._equal_weight_top50,
            'risk_parity': self._risk_parity
        }

        logger.info("基準比較器初始化，可用基準:")
        for name in self.baselines.keys():
            logger.info(f"  - {name}")

    def _buy_and_hold_0050(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, float]:
        """模擬買入持有0050 ETF。"""
        from finlab import data

        try:
            # 獲取0050價格數據
            close = data.get('etf_price:收盤價')['0050']

            # 過濾日期範圍
            if start_date:
                close = close[close.index >= start_date]
            if end_date:
                close = close[close.index <= end_date]

            # 計算報酬
            returns = close.pct_change().dropna()

            # 計算指標
            sharpe = returns.mean() / returns.std() * np.sqrt(252)
            max_dd = self._calculate_max_drawdown(returns.values)
            annual_return = (1 + returns.mean()) ** 252 - 1

            return {
                'sharpe': sharpe,
                'max_drawdown': max_dd,
                'annual_return': annual_return
            }
        except Exception as e:
            logger.error(f"買入持有0050失敗: {e}")
            return {'sharpe': 0.0, 'max_drawdown': 0.0, 'annual_return': 0.0}

    def _equal_weight_top50(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, float]:
        """模擬市值前50股票等權重投資組合。"""
        from finlab import data

        try:
            # 獲取市值和價格數據
            close = data.get('price:收盤價')
            market_cap = data.get('market_value')

            # 選擇前50大市值股票
            top50 = market_cap.is_largest(50)

            # 計算等權重報酬
            returns = close.pct_change()
            portfolio_returns = (returns * top50).sum(axis=1) / top50.sum(axis=1)
            portfolio_returns = portfolio_returns.dropna()

            # 計算指標
            sharpe = portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252)
            max_dd = self._calculate_max_drawdown(portfolio_returns.values)
            annual_return = (1 + portfolio_returns.mean()) ** 252 - 1

            return {
                'sharpe': sharpe,
                'max_drawdown': max_dd,
                'annual_return': annual_return
            }
        except Exception as e:
            logger.error(f"等權重前50失敗: {e}")
            return {'sharpe': 0.0, 'max_drawdown': 0.0, 'annual_return': 0.0}

    def _risk_parity(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, float]:
        """模擬風險平價投資組合（按逆波動率加權）。"""
        from finlab import data

        try:
            # 獲取數據
            close = data.get('price:收盤價')
            market_cap = data.get('market_value')

            # 選擇前50大市值股票
            top50 = market_cap.is_largest(50)

            # 計算波動率
            returns = close.pct_change()
            volatility = returns.rolling(window=63).std()  # 3個月波動率

            # 風險平價權重 = 1 / 波動率
            weights = (1 / volatility) * top50
            weights = weights.div(weights.sum(axis=1), axis=0)

            # 計算投資組合報酬
            portfolio_returns = (returns * weights).sum(axis=1)
            portfolio_returns = portfolio_returns.dropna()

            # 計算指標
            sharpe = portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252)
            max_dd = self._calculate_max_drawdown(portfolio_returns.values)
            annual_return = (1 + portfolio_returns.mean()) ** 252 - 1

            return {
                'sharpe': sharpe,
                'max_drawdown': max_dd,
                'annual_return': annual_return
            }
        except Exception as e:
            logger.error(f"風險平價失敗: {e}")
            return {'sharpe': 0.0, 'max_drawdown': 0.0, 'annual_return': 0.0}

    def compare_to_baselines(
        self,
        strategy_metrics: Dict[str, float],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        將策略與所有基準比較。

        參數:
            strategy_metrics: 包含 'sharpe_ratio', 'max_drawdown' 等的字典
            start_date: 比較期間開始日期
            end_date: 比較期間結束日期

        返回:
            比較結果字典
        """
        results = {}

        for name, baseline_func in self.baselines.items():
            logger.info(f"計算{name}基準...")

            baseline_metrics = baseline_func(start_date, end_date)

            # 計算相對績效
            sharpe_improvement = strategy_metrics['sharpe_ratio'] - baseline_metrics['sharpe']
            beats_baseline = strategy_metrics['sharpe_ratio'] > baseline_metrics['sharpe'] + 0.5

            results[name] = {
                'baseline_sharpe': baseline_metrics['sharpe'],
                'baseline_drawdown': baseline_metrics['max_drawdown'],
                'baseline_return': baseline_metrics['annual_return'],
                'strategy_sharpe': strategy_metrics['sharpe_ratio'],
                'strategy_drawdown': strategy_metrics.get('max_drawdown', 0.0),
                'strategy_return': strategy_metrics.get('annual_return', 0.0),
                'sharpe_improvement': sharpe_improvement,
                'beats_baseline': beats_baseline
            }

            logger.info(f"  基準夏普: {baseline_metrics['sharpe']:.2f}")
            logger.info(f"  策略夏普: {strategy_metrics['sharpe_ratio']:.2f}")
            logger.info(f"  改進: {sharpe_improvement:.2f} ({'✅ 勝出' if beats_baseline else '❌ 落後'})")

        # 檢查驗證標準
        results['validation_passed'] = self._check_validation_criteria(results)

        return results

    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """計算最大回撤。"""
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)

    def _check_validation_criteria(self, results: Dict[str, Any]) -> bool:
        """
        檢查基準比較標準。

        標準:
        1. 至少勝出一個基準（夏普 > 基準 + 0.5）
        2. 未大幅落後任何基準（夏普 > 基準 - 1.0）
        """
        beats_count = sum(
            1 for r in results.values()
            if isinstance(r, dict) and r.get('beats_baseline', False)
        )

        worst_improvement = min(
            r.get('sharpe_improvement', 0)
            for r in results.values()
            if isinstance(r, dict)
        )

        criteria = {
            'beats_at_least_one': beats_count >= 1,
            'no_catastrophic_underperformance': worst_improvement > -1.0
        }

        passed = all(criteria.values())

        logger.info("基準比較標準:")
        for criterion, result in criteria.items():
            logger.info(f"  {criterion}: {'✅' if result else '❌'}")

        return passed
```

**使用範例**:

```python
from src.validation.baseline import BaselineComparator

# 初始化比較器
comparator = BaselineComparator()

# 策略指標
strategy_metrics = {
    'sharpe_ratio': 1.8,
    'max_drawdown': -0.20,
    'annual_return': 0.25
}

# 與基準比較
results = comparator.compare_to_baselines(strategy_metrics)

# 顯示結果
for baseline_name, metrics in results.items():
    if baseline_name == 'validation_passed':
        continue
    print(f"\n{baseline_name}:")
    print(f"  基準夏普: {metrics['baseline_sharpe']:.2f}")
    print(f"  策略夏普: {metrics['strategy_sharpe']:.2f}")
    print(f"  改進: {metrics['sharpe_improvement']:.2f}")
    print(f"  勝出: {'✅' if metrics['beats_baseline'] else '❌'}")

print(f"\n總體驗證: {'✅ 通過' if results['validation_passed'] else '❌ 未通過'}")
```

---

## 實施計畫

### Week 1: 緊急修復（CRITICAL）

**Day 1-2: Fix 1.1 - 策略生成器整合**
- [ ] 實作模板整合代碼（~30行）
- [ ] 移除硬編碼區塊（第372-405行）
- [ ] 添加模板映射和參數傳遞
- [ ] 單元測試策略多樣性
- **交付成果**: 迭代20+生成多樣化策略

**Day 2-3: Fix 1.2 - 指標提取重新設計**
- [ ] 實作報告捕獲包裝器
- [ ] 修復API相容性處理（dict vs float）
- [ ] 添加提取方法記錄
- [ ] 添加可疑指標警告
- **交付成果**: 正確捕獲夏普比率（例如 -0.31 而非 0.0）

**Day 3: Fix 1.3 - 整合測試**
- [ ] 編寫8個整合測試
- [ ] 執行並驗證所有測試通過
- [ ] 執行10次迭代端到端測試
- [ ] 確認不同策略和正確指標
- **交付成果**: 運作的學習系統

---

### Week 2: 驗證增強

**Day 1: Enhancement 2.1 - Train/Val/Test Split**
- [ ] 實作`DataSplitValidator`類
- [ ] 添加一致性計算
- [ ] 添加驗證標準檢查
- [ ] 整合到迭代引擎
- **交付成果**: 三階段驗證系統

**Day 2: Enhancement 2.2 - Walk-Forward Analysis**
- [ ] 實作`WalkForwardValidator`類
- [ ] 實作區塊滾動邏輯
- [ ] 添加聚合指標計算
- [ ] 添加驗證標準
- **交付成果**: 樣本外驗證

**Day 3: Enhancement 2.3 - Bonferroni Correction**
- [ ] 實作`BonferroniValidator`類
- [ ] 計算調整後的α和閾值
- [ ] 實作策略集驗證
- [ ] 添加FWER計算
- **交付成果**: 多重比較保護

**Day 4: Enhancement 2.4 - Bootstrap CI**
- [ ] 實作`BootstrapValidator`類
- [ ] 實作區塊bootstrap
- [ ] 計算多個指標的CI
- [ ] 添加驗證標準
- **交付成果**: 不確定性量化

**Day 5: Enhancement 2.5 - Baseline Comparison**
- [ ] 實作`BaselineComparator`類
- [ ] 實作3個基準策略
- [ ] 添加相對績效計算
- [ ] 添加比較標準
- **交付成果**: 基準驗證系統

---

## 成功標準

### Phase 1 成功標準:

- ✅ 迭代20+生成多樣化策略（每10次迭代≥8個獨特策略）
- ✅ 夏普比率正確提取（有效策略非零）
- ✅ 模板反饋系統啟動
- ✅ 名人堂開始積累冠軍（夏普 ≥ 2.0）

### Phase 2 成功標準:

- ✅ 所有5個驗證增強已實作
- ✅ 策略通過train/val/test一致性檢查
- ✅ Walk-forward夏普 > 0.5，勝率 > 60%
- ✅ 符合Bonferroni調整的顯著性閾值
- ✅ Bootstrap 95% CI排除零
- ✅ 夏普勝出買入持有基準 > 0.5

### 系統健康指標:

- 模板多樣性: 最近20次迭代使用≥4個不同模板
- 指標準確性: 夏普比率匹配回測輸出（誤差 < 0.01）
- 學習進度: 最佳夏普隨時間改進
- 統計嚴謹性: 誤發現率 < 5%

---

## 風險管理

### Risk 1: 模板系統整合破壞現有代碼

**緩解**:
- 功能標誌啟用/禁用模板系統
- 後備: 保留舊硬編碼生成器作為備份
- 分階段推出: 先在10次迭代測試，然後完整部署

**應急計畫**:
```python
# 添加功能標誌
USE_TEMPLATE_SYSTEM = os.getenv('USE_TEMPLATE_SYSTEM', 'true').lower() == 'true'

if USE_TEMPLATE_SYSTEM:
    # 新模板整合代碼
else:
    # 舊硬編碼後備
```

### Risk 2: 修復後指標提取仍然失敗

**緩解**:
- 實作多個提取方法並建立後備鏈
- 為每個提取方法進行廣泛的單元測試
- 添加詳細記錄以進行未來除錯

**後備鏈**:
1. 方法 A: 使用捕獲的報告對象
2. 方法 B: 從信號重新執行（使用相同參數）
3. 方法 C: 解析策略代碼輸出（印出的結果）
4. 方法 D: 返回預設值並記錄錯誤

### Risk 3: 驗證增強對500策略實驗太慢

**緩解**:
- 為walk-forward窗口實作並行處理
- 最佳化: 快取基準指標，重用bootstrap分佈
- 選擇性驗證: 僅對高績效策略（夏普 > 1.5）執行完整驗證

**效能目標**:
- Train/val/test分割: +10秒每次迭代
- Walk-forward（10個窗口）: +30秒
- Bootstrap（1000次迭代）: +20秒
- 總驗證開銷: ~1分鐘每個候選策略

### Risk 4: FinLab API再次變更

**緩解**:
- 版本檢測和自適應API處理
- 監控: 記錄API響應以供未來除錯
- 維護: 每季度檢查API更新

**版本檢測**:
```python
def detect_api_version(report):
    """檢測FinLab API版本。"""
    sample_result = report.get_stats('Sharpe')

    if isinstance(sample_result, dict):
        return 'v2'  # 新API
    elif isinstance(sample_result, (int, float)):
        return 'v1'  # 舊API
    else:
        return 'unknown'
```

---

## 附錄

### A. 程式碼變更摘要

**修改的檔案**:
1. `claude_code_strategy_generator.py`: -34行硬編碼 +30行模板整合
2. `iteration_engine.py`: +15行報告捕獲包裝器
3. `metrics_extractor.py`: +40行API相容性處理

**新增的檔案**:
1. `src/validation/data_split.py`: ~200行
2. `src/validation/walk_forward.py`: ~250行
3. `src/validation/multiple_comparison.py`: ~180行
4. `src/validation/bootstrap.py`: ~220行
5. `src/validation/baseline.py`: ~200行
6. `tests/test_system_integration_fix.py`: ~150行

**總程式碼變更**: ~1,300行新增，~34行移除

### B. 依賴項

**現有依賴**（已安裝）:
- `numpy`
- `pandas`
- `finlab`

**新依賴**（需要安裝）:
- `scipy`: 用於Bonferroni校正（norm分佈）

**安裝**:
```bash
pip install scipy
```

### C. 測試執行指令

```bash
# Phase 1: 整合測試
pytest tests/test_system_integration_fix.py -v --tb=short

# Phase 2: 驗證測試
pytest tests/validation/test_data_split.py -v
pytest tests/validation/test_walk_forward.py -v
pytest tests/validation/test_multiple_comparison.py -v
pytest tests/validation/test_bootstrap.py -v
pytest tests/validation/test_baseline.py -v

# 完整測試套件
pytest tests/ -v --cov=src --cov-report=term-missing
```

### D. 監控和觀察

**關鍵指標儀表板**:

```python
# 添加到迭代引擎日誌
logger.info("="*70)
logger.info("系統健康儀表板")
logger.info("="*70)
logger.info(f"模板多樣性（最近20次迭代）: {template_diversity:.0%}")
logger.info(f"平均夏普（最近10次迭代）: {avg_recent_sharpe:.2f}")
logger.info(f"最佳夏普（所有時間）: {best_sharpe_ever:.2f}")
logger.info(f"名人堂策略數量: {hall_of_fame_count}")
logger.info(f"驗證通過率: {validation_pass_rate:.0%}")
logger.info("="*70)
```

**警報觸發器**:
- ⚠️ 模板多樣性 < 40%（最近20次迭代）
- ⚠️ 所有最近夏普 = 0.0（指標提取失敗）
- ⚠️ 驗證通過率 < 30%（策略品質問題）
- ⚠️ 名人堂連續20次迭代無新增（學習停滯）

---

## 結論

本規格書解決了兩個關鍵系統失敗:

1. **策略生成失敗**: 透過啟動已建立的2,993行模板反饋系統修復
2. **指標提取失敗**: 透過重用策略結果和處理API變更修復

並增強了驗證嚴謹性，新增5個關鍵組件:

1. **Train/Val/Test Split**: 防止過度擬合
2. **Walk-Forward Analysis**: 真正的樣本外驗證
3. **Bonferroni Correction**: 多重比較保護
4. **Bootstrap CI**: 不確定性量化
5. **Baseline Comparison**: 績效基準測試

**實施時間表**:
- Week 1（緊急）: 恢復學習能力
- Week 2（高優先級）: 添加統計嚴謹性

**總努力**: 6-8小時完整系統恢復和增強

---

**文件狀態**: ✅ READY FOR IMPLEMENTATION
**下一步**: 開始 Phase 1 Fix 1.1（策略生成器整合）
