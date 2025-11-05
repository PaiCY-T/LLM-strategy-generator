# Test Generation Prompt Template

使用此模板為 `zen:testgen` 提供完整的上下文，生成高質量的測試計劃。

---

## 測試對象：[模組/功能名稱]

### 系統上下文
- **用途**：[這個模組做什麼，為什麼存在]
- **架構位置**：[在系統中的角色，依賴關係]
- **關鍵數據流**：[輸入 → 處理 → 輸出]
- **業務重要性**：[對系統整體的影響，失敗的後果]

### 被測代碼路徑
- 主要實現：`src/path/to/module.py`
- 依賴模組：`src/path/to/dependency1.py`, `src/path/to/dependency2.py`
- 配置文件：`config/system_config.yaml`
- 數據文件：`data/sample_data.json`（如適用）

### 測試目標

**主要行為驗證**（必須測試）：
1. [核心功能 1]：在 [條件 A] 下，應該 [行為 X]
2. [核心功能 2]：當 [輸入 Y] 時，返回 [結果 Z]
3. [集成點]：與 [依賴模組] 的交互應該 [如何工作]

**邊緣情況**（關鍵場景）：
1. [空輸入/缺失數據]：如何處理？預期行為是什麼？
2. [無效輸入]：如何驗證和報錯？錯誤訊息是否清晰？
3. [並發場景]：多線程訪問時的行為？需要測試 race condition 嗎？
4. [故障恢復]：當 [依賴失敗] 時如何降級？是否有 fallback？
5. [資源限制]：記憶體/磁盤/網路限制下的行為？

**性能要求**（如適用）：
- [操作 X] 應在 [時間 Y] 內完成
- [資源消耗] 應低於 [閾值 Z]
- [擴展性]：能否處理 [大量數據/高並發]？

### 失敗模式和風險

**已知風險**：
1. [風險 1]：[描述] → 測試應驗證 [緩解措施]
2. [風險 2]：[描述] → 測試應捕獲 [失敗信號]

**歷史 Bug**（如有）：
- [Bug ID/描述]：[何時發生] → 測試應確保不再發生

**回歸風險**：
- [脆弱邏輯 1]：[代碼段 X] 容易出錯，需要特別覆蓋
- [脆弱邏輯 2]：[變更歷史] 顯示此處經常出問題

### 測試環境和約定

**框架**：pytest / unittest / [其他]
**版本**：Python 3.10+

**Fixtures**（可用的測試輔助）：
- `fixture_name1`：[用途描述]
- `fixture_name2`：[用途描述]

**Mocking 策略**：
- Mock 外部 API（LLM、數據庫、網路請求）
- 不 Mock 核心業務邏輯
- 使用 `pytest-mock` / `unittest.mock` / `MagicMock`

**測試數據**：
- 固定測試數據集：`tests/fixtures/sample_data.json`
- Mock 數據生成器：[描述如何生成]

**覆蓋率目標**：≥[X]%（建議 85-95%）

### 特定測試場景（重要）

**場景 1：[場景名稱]**
- **前置條件**：[設置什麼環境/數據]
- **操作**：[執行什麼動作]
- **預期結果**：[應該看到什麼輸出/狀態變化]
- **驗證點**：[具體斷言什麼]

**場景 2：[場景名稱]**
- **前置條件**：
- **操作**：
- **預期結果**：
- **驗證點**：

[添加更多場景...]

### 現有測試（參考）
- `tests/test_existing_module.py`：可參考的測試模式
- `tests/conftest.py`：共享 fixtures
- 相關文檔：[鏈接]

### 非功能性需求（如適用）

**安全性**：
- [敏感數據處理]：確保不洩露密鑰/密碼
- [輸入驗證]：防止注入攻擊

**可觀察性**：
- [日誌]：關鍵操作應記錄什麼？
- [監控]：需要暴露哪些指標？

**相容性**：
- [向後相容]：與舊版本的行為一致性
- [跨平台]：Windows/Linux/macOS 差異

### 生成請求

請生成完整的測試計劃和實現，包括：

1. **測試套件結構**
   - 測試文件組織方式
   - 測試類/函數命名規範

2. **關鍵測試用例**
   - 每個場景的具體測試函數
   - 包含完整的 AAA 模式（Arrange, Act, Assert）

3. **Fixtures 設計**
   - 需要哪些測試輔助設施
   - Fixture 的作用域（function/class/module/session）

4. **斷言策略**
   - 如何驗證行為正確性
   - 錯誤訊息的清晰度

5. **邊緣情況覆蓋**
   - 確保所有失敗模式被捕獲
   - Parametrize 策略（測試多組輸入）

6. **性能基準**（如適用）
   - 如何測試性能要求
   - Benchmark fixtures

7. **Mock 實現**
   - 具體的 Mock 策略
   - Mock 對象的設置和驗證

---

## 使用範例

### 為 ConfigManager 生成測試計劃

```markdown
## 測試對象：ConfigManager（配置管理單例）

### 系統上下文
- **用途**：集中管理系統配置（YAML 文件加載、緩存、訪問）
- **架構位置**：基礎設施層，被 LLMClient、AutonomousLoop 等使用
- **關鍵數據流**：YAML 文件 → 解析 → 緩存 → 提供配置值
- **業務重要性**：配置錯誤會導致整個系統無法運行

### 被測代碼路徑
- 主要實現：`src/learning/config_manager.py`
- 配置文件：`config/learning_system.yaml`
- 使用者：`src/learning/llm_client.py`, `artifacts/working/modules/autonomous_loop.py`

### 測試目標

**主要行為驗證**：
1. **單例模式**：多次調用 `get_instance()` 返回同一實例
2. **配置加載**：成功解析 YAML 並緩存
3. **嵌套鍵訪問**：支持點符號（`llm.enabled`）
4. **默認值**：缺失鍵返回默認值
5. **熱重載**：`force_reload=True` 重新讀取文件

**邊緣情況**：
1. **文件不存在**：拋出 `FileNotFoundError` 並提供清晰訊息
2. **無效 YAML**：處理語法錯誤（yaml.YAMLError）
3. **類型不匹配**：配置值類型與預期不符時的行為
4. **並發加載**：多線程同時調用 `load_config()` 的安全性

**性能要求**：
- 配置加載（含緩存）：O(1) 時間複雜度
- 首次加載：<100ms（對於小型 YAML）

### 失敗模式和風險

**已知風險**：
1. **Race Condition**：多線程初始化單例時的競爭 → 需要測試雙重檢查鎖
2. **緩存失效**：`clear_cache()` 後未正確重載 → 需要驗證

**回歸風險**：
- 之前單例未正確實現導致多實例 → 測試應確保只有一個實例

### 測試環境和約定

**框架**：pytest
**Fixtures**：
```python
@pytest.fixture
def temp_config_file(tmp_path):
    config = {"llm": {"enabled": True}, "iteration": {"max": 100}}
    file = tmp_path / "test_config.yaml"
    file.write_text(yaml.dump(config))
    return str(file)

@pytest.fixture(autouse=True)
def reset_singleton():
    """每個測試後重置單例"""
    yield
    ConfigManager.reset_instance()
```

**Mocking 策略**：不 Mock（測試真實 YAML 解析）

**覆蓋率目標**：≥98%

### 特定測試場景

**場景 1：基本配置加載**
- 前置：YAML 文件存在，內容有效
- 操作：`manager.load_config(path)`
- 預期：返回配置字典，`manager.get('llm.enabled')` 返回 `True`

**場景 2：並發安全性**
- 前置：單例未初始化
- 操作：20 個線程同時調用 `ConfigManager.get_instance()`
- 預期：所有線程獲得同一實例，無 race condition

**場景 3：熱重載**
- 前置：配置已加載並緩存
- 操作：修改 YAML 文件，調用 `load_config(force_reload=True)`
- 預期：新配置值生效

### 生成請求

請生成 `tests/learning/test_config_manager.py`，包括：
1. 單例模式測試（2 個）
2. 配置加載測試（4 個）
3. 錯誤處理測試（2 個）
4. 鍵訪問測試（3 個）
5. 線程安全測試（2 個）
6. 真實配置文件測試（1 個）
```

---

## 提交給 zen:testgen 的方式

```python
# 使用 zen:testgen
mcp__zen__testgen(
    step="根據上述完整上下文，生成 ConfigManager 的測試計劃",
    step_number=1,
    total_steps=2,
    next_step_required=True,
    findings="已收集完整的測試需求和上下文",
    relevant_files=["src/learning/config_manager.py"],
    model="gemini-2.5-pro"
)
```

---

**Template Version**: 1.0
**Last Updated**: 2025-11-04
**Author**: Code Implementation Specialist
