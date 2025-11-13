# Next Steps: Actionable Plan

**Date**: 2025-10-27
**Status**: Ready to Execute
**Priority**: Phase 0 Testing (SAFE, TODAY)

---

## 🎯 Immediate Action: Run Phase 0 Smoke Test (5 minutes)

### Why Phase 0 First?

根據您的經驗："yaml Normalizer 是在第一次 smoke testing 之後發現問題才新增的 spec"

Phase 0 可以：
- ✅ 安全地測試（零風險，dry-run only）
- ✅ 今天就能跑（不需要等 Docker 修好）
- ✅ 發現早期問題（就像發現 YAML Normalizer 問題一樣）
- ✅ 快速反饋（<5 分鐘）
- ✅ 低成本（<$0.10）

### Step-by-Step Execution

#### 1. 設定環境變數
```bash
cd /mnt/c/Users/jnpi/documents/finlab
export OPENROUTER_API_KEY="your_key_here"
```

#### 2. 檢查配置檔案
```bash
cat config/test_phase0_smoke.yaml
```

應該看到：
```yaml
docker:
  enabled: false              # ✅ Docker 已禁用
  fallback_to_direct: false   # ✅ 直接執行已禁用

execution:
  mode: "dry_run"             # ✅ 只驗證語法
```

#### 3. 運行 Phase 0 測試
```bash
# 選項 A: 使用測試框架（推薦）
python3 -m pytest tests/integration/test_phase0_smoke.py -v

# 選項 B: 如果測試文件尚未創建，使用配置直接運行
python3 -c "
from src.innovation.innovation_engine import InnovationEngine
import yaml

with open('config/test_phase0_smoke.yaml', 'r') as f:
    config = yaml.safe_load(f)

engine = InnovationEngine(config)
results = engine.run(max_iterations=10)

print('\\n=== Phase 0 Results ===')
print(f'Iterations Completed: {results[\"iterations_completed\"]}')
print(f'YAML Validation Rate: {results[\"yaml_validation_rate\"]:.0%}')
print(f'Code Generation Rate: {results[\"code_generation_rate\"]:.0%}')
print(f'Syntax Correctness: {results[\"syntax_correctness_rate\"]:.0%}')
print(f'Total Cost: \${results[\"llm_cost\"]:.2f}')
print(f'Strategies Executed: {results[\"strategies_executed\"]}')  # Should be 0
"
```

#### 4. 檢查結果
```bash
# 查看生成的 YAML specs
cat artifacts/phase0_yaml_specs.jsonl | jq .

# 查看生成的程式碼
cat artifacts/phase0_generated_code.jsonl | jq .

# 查看度量指標
cat artifacts/phase0_metrics.json | jq .
```

#### 5. 驗證成功標準
- ✅ **Iterations Completed**: 10/10
- ✅ **YAML Validation Rate**: ≥70%
- ✅ **Code Generation Rate**: 100%
- ✅ **Syntax Correctness**: 100%
- ✅ **Strategies Executed**: 0 (dry-run 模式)
- ✅ **Total Cost**: <$0.10

---

## 📋 如果 Phase 0 發現問題

### 問題類型 1: YAML 驗證率 <70%

**可能原因**:
- LLM 生成的 YAML 格式不正確
- Schema 過於嚴格
- Prompt 需要改進

**行動**:
1. 檢查 `artifacts/phase0_yaml_specs.jsonl` 中的錯誤
2. 創建新的 spec: `yaml-validation-improvement`
3. 更新 prompt template 或 schema

### 問題類型 2: 程式碼生成失敗

**可能原因**:
- Jinja2 template 錯誤
- YAML → Code mapping 問題
- 缺少必要的欄位

**行動**:
1. 檢查 `artifacts/phase0_generated_code.jsonl` 中的錯誤
2. 創建新的 spec: `code-generation-fix`
3. 更新 `yaml_to_code_generator.py`

### 問題類型 3: 語法錯誤

**可能原因**:
- 生成的程式碼有語法錯誤
- Import statements 不正確
- Indentation 問題

**行動**:
1. 檢查具體的 SyntaxError
2. 創建新的 spec: `code-syntax-fix`
3. 更新 code generation template

### 問題類型 4: 新的正規化問題

**可能原因**:
- 類似 YAML Normalizer 的新問題
- 其他命名規範問題

**行動**:
1. 分析具體案例
2. 創建新的 spec (就像 YAML Normalizer 一樣)
3. 實現修復並測試

---

## 📊 Phase 0 之後的計劃

### 如果 Phase 0 成功 ✅

**Week 1 (本週)**:
1. **Day 1-2**: Docker Security Tier 1 fixes (17 hours)
   - 移除 fallback_to_direct
   - 添加 runtime monitoring
   - 配置 non-root user
   - 使用 battle-tested seccomp
   - 添加 PID limits
   - Pin Docker version

2. **Day 3**: 完成 LLM Integration Task 13 (4 hours)
   - 寫 `docs/LLM_INTEGRATION.md`
   - 包括使用指南、provider 設置、troubleshooting

3. **Day 4-5**: Phase 1 Testing (30 minutes)
   - 使用 Docker 測試
   - 驗證安全控制
   - 檢查容器隔離

### 如果 Phase 0 發現問題 ⚠️

**立即行動**:
1. 分析並記錄所有問題
2. 為每個主要問題創建新的 spec
3. 優先修復阻塞問題
4. 重新運行 Phase 0
5. 成功後再進行 Week 1 計劃

---

## 🔄 Spec-Workflow 系統性完成

### 已完成的文檔結構

```
/mnt/c/Users/jnpi/documents/finlab/
├── .spec-workflow/
│   └── PROJECT_STATUS_REPORT.md          ✅ 綜合狀態報告
│
├── config/
│   └── test_phase0_smoke.yaml            ✅ Phase 0 配置
│
├── COMPREHENSIVE_SPEC_REVIEW_REPORT.md   ✅ 詳細審查報告
├── E2E_TESTING_STRATEGY.md               ✅ 測試策略（4階段）
├── SPEC_REVIEW_AND_TESTING_SUMMARY.md    ✅ 執行摘要
└── NEXT_STEPS_ACTION_PLAN.md             ✅ 可執行計劃（本檔案）
```

### Spec 狀態總覽

| Spec | Status | Tasks | Production Ready |
|------|--------|-------|------------------|
| Structured Innovation MVP | ✅ COMPLETE | 13/13 | 95% |
| YAML Normalizer (Phase 1+2) | ✅ COMPLETE | 6/6 | 90% |
| Exit Mutation Redesign | ✅ COMPLETE | 8/8 | 65% |
| Docker Sandbox Security | ⚠️ IMPLEMENTING | 13/15 | 40% |
| LLM Integration Activation | ⚠️ IMPLEMENTING | 13/14 | 90% |
| Resource Monitoring System | ⚠️ IMPLEMENTING | 13/15 | 85% |

**總進度**: 56/61 tasks (91.8%)

---

## 🚨 Critical Path（關鍵路徑）

```
Phase 0 Testing (TODAY, 5 min)
    ↓
[If Issues Found]
    ↓
Create New Specs → Fix Issues → Re-run Phase 0
    ↓
[When Phase 0 Success]
    ↓
Docker Security Tier 1 Fixes (17 hours)
    ↓
LLM Integration Task 13 (4 hours)
    ↓
Phase 1 Testing (30 min)
    ↓
Exit Mutation Improvements (6 hours)
    ↓
Phase 2 Testing (60 min)
    ↓
Resource Monitoring Completion (5 hours)
    ↓
Phase 3 Testing (120 min)
    ↓
PRODUCTION READY ✅
```

**預計時間**: 2 週（假設 Docker Security 優先處理）

---

## 💰 Cost Tracking

### Phase 0 (Today)
- **Estimated**: $0.04 (2 LLM calls × $0.02)
- **Budget**: $0.10
- **Risk**: ZERO (dry-run only)

### Full Testing Cycle
- Phase 0: $0.04
- Phase 1: $0.08
- Phase 2: $0.20
- Phase 3: $0.40
- **Total**: $0.72

### Production (Estimated)
- Per iteration: $0.02 (20% innovation rate)
- Per 100-generation run: $0.40
- Monthly (10 runs): $4.00

---

## ✅ Verification Checklist

在開始 Phase 0 之前，確認：

- [ ] OpenRouter API key 已設定
- [ ] 配置檔案 `config/test_phase0_smoke.yaml` 存在
- [ ] `docker.enabled = false` 確認
- [ ] `docker.fallback_to_direct = false` 確認
- [ ] `execution.mode = "dry_run"` 確認
- [ ] `artifacts/` 目錄存在或會自動創建

開始執行：

- [ ] 運行 Phase 0 測試
- [ ] 檢查結果是否符合成功標準
- [ ] 記錄發現的任何問題
- [ ] 如有問題，創建新的 specs
- [ ] 如果成功，繼續 Week 1 計劃

---

## 📞 Support & Documentation

### 主要文檔參考

1. **Comprehensive Spec Review** (`COMPREHENSIVE_SPEC_REVIEW_REPORT.md`)
   - 詳細的 spec 分析
   - 7 個 Docker Security 漏洞說明
   - 生產就緒度評估

2. **E2E Testing Strategy** (`E2E_TESTING_STRATEGY.md`)
   - 4 階段測試詳細設計
   - 36 個測試案例
   - 實現代碼範例

3. **Project Status Report** (`.spec-workflow/PROJECT_STATUS_REPORT.md`)
   - 全面的項目狀態
   - Spec-by-spec 詳細分析
   - 時間線和優先級

4. **This Document** (`NEXT_STEPS_ACTION_PLAN.md`)
   - 立即可執行的步驟
   - 問題處理指南
   - 驗證清單

### Spec-Workflow Dashboard

如果已啟動 spec-workflow dashboard:
```
URL: http://localhost:3456
```

可以在 dashboard 查看：
- 所有 specs 的實時狀態
- Tasks 進度追蹤
- Approval requests

---

## 🎯 Success Definition

**Phase 0 成功** =
- 10/10 iterations complete
- YAML validation ≥70%
- Code generation 100%
- Syntax correctness 100%
- Zero execution (dry-run only)
- Cost <$0.10

**Project 成功** =
- All critical specs complete
- Docker Security Tier 1 fixes done
- All 4 testing phases pass
- Production deployment ready
- Cost within budget

---

## 🚀 Ready to Start?

```bash
# 1. 設定環境
cd /mnt/c/Users/jnpi/documents/finlab
export OPENROUTER_API_KEY="your_key_here"

# 2. 運行 Phase 0
python3 -m pytest tests/integration/test_phase0_smoke.py -v

# 3. 檢查結果
cat artifacts/phase0_metrics.json | jq .

# That's it! 就是這麼簡單，安全，快速。
```

**預期時間**: 5 分鐘
**預期成本**: <$0.10
**風險等級**: ZERO

Let's discover what issues exist (just like YAML Normalizer was discovered) before investing in Docker Security fixes! 🔍

---

**Document Version**: 1.0
**Last Updated**: 2025-10-27
**Next Update**: After Phase 0 results
