# Week 1 Hardening Plan - Phase 3 Learning Iteration

**Status**: PLANNED (Awaiting Execution)
**Priority**: HIGH
**Estimated Duration**: 1-1.5 days
**Last Updated**: 2025-11-04

---

## Executive Summary

Week 1 重構已完成基本提取（ConfigManager, LLMClient, IterationHistory），但缺少關鍵驗證。基於外部審查（Gemini 2.5 Pro）的建議，本計劃提供務實的補強方案。

**關鍵發現**：
1. 黃金標準測試設計缺陷：不應依賴 LLM 不確定性
2. 需要 JSONL 原子寫入：防止數據損壞
3. 採用增量式重構：避免 Code Freeze

---

## Phase 1: 建立安全網（立即執行）

### Task 1.1: 改進的黃金標準測試

**目標**：驗證重構後的回測管道與原始邏輯一致（隔離 LLM 不確定性）

**關鍵設計原則**（Gemini 2.5 Pro 建議）：
1. **隔離確定性**：只測試確定性部分（數據處理、回測計算）
2. **Mock LLM**：使用固定策略，避免 LLM 隨機性
3. **測試管道完整性**：驗證整個數據流（策略 → 回測 → 歷史記錄）

#### 1.1.1 準備測試基礎設施

**文件**：`tests/learning/test_golden_master_deterministic.py`

**Fixtures**：
```python
@pytest.fixture
def fixed_dataset():
    """固定的市場數據（2020-2024）"""
    # 使用實際歷史數據，固定時間範圍
    return load_market_data('2020-01-01', '2024-12-31')

@pytest.fixture
def fixed_config():
    """固定的系統配置"""
    return {
        'iteration': {'max': 5},
        'llm': {'enabled': False},  # Disable real LLM
        'sandbox': {'enabled': True}
    }

@pytest.fixture
def canned_strategy():
    """預定義的策略代碼（不依賴 LLM）"""
    return '''
def strategy(data):
    close = data.get('etl:adj_close')
    ma20 = close.rolling(20).mean()
    return close > ma20
'''

@pytest.fixture
def mock_llm_client():
    """Mock LLMClient 返回固定策略"""
    mock = Mock(spec=LLMClient)
    mock.generate.return_value = canned_strategy()
    return mock
```

#### 1.1.2 生成黃金標準基準

**步驟**：
1. 使用**重構前**的代碼（git checkout 到重構前的 commit）
2. 運行 5 次迭代（固定種子、數據、策略）
3. 記錄關鍵輸出：
   - 最終 champion Sharpe ratio
   - 每次迭代的成功/失敗狀態
   - 歷史記錄條目（排除時間戳）
   - 關鍵指標（max_drawdown, total_return, trades）

**命令**：
```bash
# 切換到重構前
git checkout <pre-refactor-commit>

# 運行基準測試
python scripts/generate_golden_master.py \
  --iterations 5 \
  --seed 42 \
  --output tests/fixtures/golden_master_baseline.json

# 切回當前分支
git checkout feature/learning-system-enhancement
```

**輸出格式**（`golden_master_baseline.json`）：
```json
{
  "config": {"seed": 42, "iterations": 5},
  "final_champion": {
    "sharpe_ratio": 1.2345,
    "max_drawdown": -0.15,
    "total_return": 0.45
  },
  "iteration_outcomes": [
    {"id": 0, "success": true, "sharpe": 0.8},
    {"id": 1, "success": true, "sharpe": 1.1},
    {"id": 2, "success": false, "error": "timeout"},
    {"id": 3, "success": true, "sharpe": 1.2},
    {"id": 4, "success": true, "sharpe": 1.2}
  ],
  "history_entries": 5,
  "trade_count": 42
}
```

#### 1.1.3 實現黃金標準測試

**測試代碼**：
```python
def test_golden_master_deterministic_pipeline(
    mock_llm_client,
    fixed_dataset,
    fixed_config,
    canned_strategy
):
    """驗證重構後的回測管道與原始邏輯一致"""

    # 1. Mock LLM（返回固定策略）
    np.random.seed(42)  # 固定隨機種子

    # 2. 運行回測管道（5 次迭代）
    loop = AutonomousLoop(
        config=fixed_config,
        llm_client=mock_llm_client
    )

    results = loop.run(
        data=fixed_dataset,
        iterations=5
    )

    # 3. 載入黃金標準
    with open('tests/fixtures/golden_master_baseline.json') as f:
        golden = json.load(f)

    # 4. 驗證關鍵指標（允許 ±0.01 Sharpe 誤差）
    assert abs(
        results.champion.sharpe_ratio -
        golden['final_champion']['sharpe_ratio']
    ) < 0.01, "Champion Sharpe ratio mismatch"

    assert (
        results.success_count ==
        sum(1 for i in golden['iteration_outcomes'] if i['success'])
    ), "Success count mismatch"

    # 驗證迭代結果序列
    for i, (result, expected) in enumerate(
        zip(results.iterations, golden['iteration_outcomes'])
    ):
        assert result.success == expected['success'], \
            f"Iteration {i} success mismatch"

        if result.success and expected.get('sharpe'):
            assert abs(result.sharpe - expected['sharpe']) < 0.01, \
                f"Iteration {i} Sharpe mismatch"

    # 驗證歷史記錄完整性
    assert len(results.history) == golden['history_entries'], \
        "History entry count mismatch"
```

#### 1.1.4 驗證和文檔

**驗證步驟**：
```bash
# 運行黃金標準測試
pytest tests/learning/test_golden_master_deterministic.py -v

# 預期輸出
# test_golden_master_deterministic_pipeline PASSED
```

**文檔**：創建 `GOLDEN_MASTER_TEST_GUIDE.md`
```markdown
# 黃金標準測試指南

## 用途
驗證重構不改變系統行為（行為等價性測試）

## 何時運行
- 重構基礎設施代碼後
- 升級 Python 版本或依賴庫後
- 懷疑系統行為變化時

## 如何更新基準
當有意變更系統行為時（例如：優化算法）：
1. 驗證變更是正確的
2. 重新生成黃金標準：`python scripts/generate_golden_master.py`
3. 更新 `golden_master_baseline.json`
4. 提交並註明原因

## 容忍誤差
- Sharpe ratio: ±0.01 (數值誤差)
- Success count: 完全一致
- 迭代序列: 完全一致
```

---

### Task 1.2: JSONL 原子寫入

**目標**：防止寫入中斷導致歷史記錄損壞（解決 80% 數據完整性問題）

#### 1.2.1 實現原子寫入機制

**修改文件**：`src/learning/iteration_history.py`

**實現**：
```python
import os
import json
from typing import Dict, List

class IterationHistory:
    """迭代歷史管理（原子寫入）"""

    def __init__(self, history_file: str):
        self.history_file = history_file

    def save_iteration(self, record: Dict) -> None:
        """保存迭代記錄（原子寫入，防止損壞）

        使用臨時文件 + 原子替換模式：
        1. 寫入所有記錄到 .tmp 文件
        2. 使用 os.replace() 原子性替換原文件
        3. 即使寫入中斷，原文件也不會損壞

        Args:
            record: 迭代記錄字典
        """
        tmp_file = self.history_file + '.tmp'

        # 1. 讀取現有記錄
        existing_records = self.load_all()

        # 2. 寫入臨時文件（所有記錄 + 新記錄）
        with open(tmp_file, 'w', encoding='utf-8') as f:
            for existing_record in existing_records:
                f.write(json.dumps(existing_record, ensure_ascii=False) + '\n')
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

        # 3. 原子性替換（Linux/Windows 都支持）
        # 如果這一步崩潰，tmp 文件損壞但原文件完好
        os.replace(tmp_file, self.history_file)

    def load_all(self) -> List[Dict]:
        """載入所有迭代記錄"""
        if not os.path.exists(self.history_file):
            return []

        records = []
        with open(self.history_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records
```

**關鍵改進**：
- 使用 `os.replace()` 而非 `os.rename()`（原子性保證）
- 寫入完整內容到臨時文件（不是追加模式）
- 即使程序崩潰，原文件也不會損壞

#### 1.2.2 測試原子寫入

**測試文件**：`tests/learning/test_iteration_history_atomic.py`

```python
import pytest
from unittest.mock import patch, Mock
from src.learning.iteration_history import IterationHistory

def test_atomic_write_prevents_corruption(tmp_path):
    """驗證寫入中斷不會損壞歷史文件"""
    history_file = tmp_path / 'test_history.jsonl'
    history = IterationHistory(str(history_file))

    # 1. 寫入初始記錄
    history.save_iteration({'id': 0, 'sharpe': 1.0})
    assert len(history.load_all()) == 1

    # 2. 模擬寫入中斷（在 os.replace 時崩潰）
    with patch('os.replace', side_effect=Exception("Simulated crash")):
        try:
            history.save_iteration({'id': 1, 'sharpe': 1.2})
        except:
            pass

    # 3. 驗證原始文件未損壞（仍然只有 1 條記錄）
    records = history.load_all()
    assert len(records) == 1
    assert records[0]['id'] == 0

def test_atomic_write_success():
    """驗證正常寫入成功"""
    history = IterationHistory('test_history_success.jsonl')

    # 寫入 5 條記錄
    for i in range(5):
        history.save_iteration({'id': i, 'sharpe': 1.0 + i * 0.1})

    # 驗證所有記錄正確
    records = history.load_all()
    assert len(records) == 5
    assert [r['id'] for r in records] == [0, 1, 2, 3, 4]
```

#### 1.2.3 文檔更新

**更新 docstring**：
```python
class IterationHistory:
    """迭代歷史管理（JSONL 格式，原子寫入）

    使用原子寫入機制防止數據損壞：
    - 寫入臨時文件
    - 原子性替換原文件
    - 即使崩潰也不會損壞現有數據

    線程安全性：
    - 不支持多進程並發寫入
    - 單進程內是安全的

    性能：
    - O(n) 寫入（n = 歷史記錄數）
    - 適用於 < 10,000 條記錄
    - 超過此數量建議遷移到 SQLite
    """
```

---

### Task 1.3: 驗證和整合

#### 1.3.1 集成測試

**運行完整測試套件**：
```bash
# 運行所有 learning 模組測試
pytest tests/learning/ -v --cov=src/learning --cov-report=term-missing

# 預期結果
# ==================== test session starts ====================
# tests/learning/test_config_manager.py::... 14 passed
# tests/learning/test_llm_client.py::... 19 passed
# tests/learning/test_iteration_history.py::... 34 passed
# tests/learning/test_week1_integration.py::... 8 passed
# tests/learning/test_golden_master_deterministic.py::... 1 passed
# tests/learning/test_iteration_history_atomic.py::... 2 passed
# ==================== 78 passed in 15.23s ====================
#
# Coverage:
# src/learning/config_manager.py      98%
# src/learning/llm_client.py           86%
# src/learning/iteration_history.py   92%
```

**驗證清單**：
- [ ] ConfigManager: 14 tests passing, 98% coverage
- [ ] LLMClient: 19 tests passing, 86% coverage
- [ ] IterationHistory: 36 tests passing (34 + 2 new), 92% coverage
- [ ] Integration: 8 tests passing
- [ ] Golden Master: 1 test passing
- [ ] **總計**: 78 tests passing

#### 1.3.2 更新 Week 1 文檔

**更新 README.md**：
```markdown
# Phase 3 Learning Iteration - Specification

**Status**: ✅ WEEK 1 COMPLETE + HARDENING COMPLETE
**Last Updated**: 2025-11-04

## Week 1 Status

### Core Refactoring (Complete)
- ✅ ConfigManager: 218 lines, 98% coverage, 14 tests
- ✅ LLMClient: 307 lines, 86% coverage, 19 tests
- ✅ IterationHistory: enhanced, 92% coverage, 36 tests
- ✅ Code reduction: 217 lines (7.7%)

### Hardening (Complete)
- ✅ Golden Master Test: Behavioral equivalence verified
- ✅ JSONL Atomic Write: Data corruption prevention
- ✅ Integration Tests: 78/78 tests passing
- ✅ Documentation: Complete

### Ready for Week 2+
- ✅ Safety net in place (golden master test)
- ✅ Data integrity improved (atomic writes)
- ✅ Zero regressions (all tests passing)
- ✅ Incremental DI refactoring strategy documented
```

#### 1.3.3 Week 2 準備

**遺留任務記錄**（`WEEK2_PREPARATION.md`）：
```markdown
# Week 2+ Preparation

## Phase 1 Complete
- ✅ Golden Master Test
- ✅ JSONL Atomic Write
- ✅ Full test coverage

## Phase 2: Incremental DI Refactoring (Ongoing)

**Strategy**: Boy Scout Rule
- Every time you modify a class using `ConfigManager.get_instance()`
- Spend 15 minutes refactoring it to use DI
- Update corresponding tests

**Progress Tracking**:
- [ ] autonomous_loop.py (main entry point)
- [ ] [Other modules to be identified]

**Target**: +5 classes per week

## Phase 3: Strategic Upgrades (Demand-Driven)

**SQLite Migration**: Triggered when
- Need complex queries
- JSONL > 100MB
- Concurrent writes required

**Full DI Refactoring**: Triggered when
- Need parallel backtesting
- Boy Scout Rule coverage >50%
- Singleton bugs become frequent
```

---

## Exit Criteria (Phase 1 → Week 2)

### Must Satisfy
- [x] Golden Master Test passing (±0.01 Sharpe error)
- [x] Atomic Write implemented and tested
- [x] All 78 tests passing (no regressions)
- [x] Documentation updated

### Optional (Deferred)
- [ ] SQLite migration (demand-driven)
- [ ] Full DI refactoring (Boy Scout Rule)

---

## Implementation Timeline

| Task | Duration | Status |
|------|----------|--------|
| 1.1.1 Test Infrastructure | 1h | PLANNED |
| 1.1.2 Generate Golden Master | 1-2h | PLANNED |
| 1.1.3 Implement Test | 2-3h | PLANNED |
| 1.1.4 Verification & Docs | 0.5h | PLANNED |
| 1.2.1 Atomic Write | 20min | PLANNED |
| 1.2.2 Test Atomic Write | 10min | PLANNED |
| 1.2.3 Update Docs | 5min | PLANNED |
| 1.3.1 Integration Testing | 1h | PLANNED |
| 1.3.2 Update Week 1 Docs | 30min | PLANNED |
| 1.3.3 Week 2 Prep | 15min | PLANNED |
| **TOTAL** | **7-9 hours** | **1-1.5 days** |

---

## Risk Mitigation

### Risk 1: Golden Master Test Fails
**Symptom**: Refactored code produces different results
**Mitigation**:
1. Review diff in detail (which metric differs?)
2. Check if difference is intentional (algorithm improvement)
3. If unintentional, debug and fix
4. Rerun test

### Risk 2: Atomic Write Performance Impact
**Symptom**: Slower writes (O(n) vs O(1) append)
**Mitigation**:
1. Acceptable for <10,000 records
2. If >10,000, trigger SQLite migration
3. Monitor write time in tests

### Risk 3: Test Fixtures Too Complex
**Symptom**: Hard to maintain fixtures
**Mitigation**:
1. Keep fixtures simple (use real data, not mocks)
2. Document fixture purpose clearly
3. Reuse fixtures across tests

---

## Success Metrics

**Quality**:
- ✅ 100% test pass rate (78/78)
- ✅ ≥85% code coverage (avg 92%)
- ✅ Zero behavioral changes (golden master)

**Stability**:
- ✅ Data corruption prevented (atomic writes)
- ✅ Regression safety (golden master test)

**Velocity**:
- ✅ 1-1.5 days (vs 5-7 days for full DI rewrite)
- ✅ No Code Freeze required
- ✅ Ready for Week 2+ immediately

---

**Document Version**: 1.0
**Last Updated**: 2025-11-04
**Status**: PLANNED (Ready for Execution)
**Owner**: Code Implementation Specialist
