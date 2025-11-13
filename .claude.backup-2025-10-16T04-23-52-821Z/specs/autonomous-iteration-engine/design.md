# Design Document - Autonomous Strategy Iteration Engine

## 1. System Architecture

### 1.1 High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  iteration_engine.py (Main)                 │
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │  Strategy  │─>│ Validator  │─>│  Executor  │          │
│  │ Generator  │  │ (AST)      │  │(Sandbox)   │          │
│  └────────────┘  └────────────┘  └────────────┘          │
│         │               │                │                 │
│         v               v                v                 │
│  ┌────────────────────────────────────────────┐           │
│  │         Learning & Feedback Loop           │           │
│  └────────────────────────────────────────────┘           │
│                        │                                   │
│                        v                                   │
│                 iterations.jsonl                           │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Component Design

#### Component 1: Strategy Generator
**Responsibility**: Generate Finlab-compatible strategy code using Claude API

**Key Functions**:
- `generate_strategy(iteration_num, history) -> str`
- `build_prompt(datasets, history_summary) -> str`
- `extract_code_block(response) -> str`

**Design Decisions**:
- Temperature: 0.3 (balance between creativity and reliability)
- Model: claude-sonnet-4-20250514
- Curated datasets: 50 (not 719) to avoid prompt bloat
- Natural language summary feedback (not raw JSON)

**Error Handling**:
- API timeout: retry with exponential backoff (5s, 10s, 20s)
- Rate limit: queue with 1-minute delay
- Invalid response: fallback to template

---

#### Component 2: Code Validator (AST)
**Responsibility**: Security and correctness validation before execution

**Key Functions**:
- `validate_code(code) -> (bool, List[str])`
- `check_dangerous_imports(ast_tree) -> List[str]`
- `check_shift_patterns(ast_tree) -> List[str]`

**Design Decisions**:
- Use Python AST (not regex) for reliable parsing
- Block list: Import, ImportFrom, Exec, Eval, open(), compile()
- Shift validation: only allow `.shift(positive_number)`
- Return detailed error messages for debugging

**Security Rationale**:
- AST can't catch all exploits, but blocks 80-90% of common issues
- Multiprocessing provides process isolation as second defense layer
- Acceptable risk for personal research project (not production)

---

#### Component 3: Sandbox Executor
**Responsibility**: Isolated execution with timeout and resource limits

**Key Functions**:
- `run_strategy_safe(code, timeout=120) -> Dict`
- `execute_strategy_wrapper(code, safe_globals, result_queue)`
- `extract_metrics(report) -> Dict`

**Design Decisions**:
- **Multiprocessing** (Gemini suggestion):
  - Spawn mode (Windows compatible)
  - Process isolation (memory safety)
  - Reliable timeout (join + terminate + kill)
- **Safe Globals**:
  ```python
  {
    '__builtins__': {minimal whitelist},
    'pd': pandas, 'np': numpy,
    'data': finlab.data, 'sim': finlab.backtest.sim
  }
  ```
- **Metrics Extraction**:
  - Convert finlab report to plain dict (handle serialization)
  - Extract: annual_return, sharpe_ratio, max_drawdown, win_rate, total_trades

**Technical Constraints**:
- 120s timeout (NFR-1.2)
- finlab report may not be picklable → extract scalars immediately
- Queue communication between processes

---

#### Component 4: Learning & Feedback Loop
**Responsibility**: Generate actionable natural language summaries for next iteration

**Key Functions**:
- `create_nl_summary(result, code, metrics) -> str`
- `generate_improvement_hint(metrics) -> str`
- `suggest_fix(error_message) -> str`

**Design Decisions** (Based on Gemini feedback):
- **No programmatic pattern extraction** - let Claude infer patterns from NL summary
- **Structured summary format**:
  ```
  === Iteration N - SUCCESS/FAILED ===
  [Metrics or Error]

  Analysis: [What worked/didn't work]
  Next steps: [Specific improvement suggestions]
  ```
- **Feedback includes**:
  - Success: metrics + improvement hints
  - Failure: error + diagnosis + fix suggestion

**Rationale**:
- LLMs are better at reasoning over NL than structured data
- Avoids premature optimization of learning logic
- Simpler code (no complex pattern recognition needed)

---

#### Component 5: Logging System
**Responsibility**: Record all iterations for analysis and recovery

**Key Functions**:
- `log_iteration(iteration, code, result, summary)`
- `load_checkpoint() -> Dict` (future)

**Design Decisions** (Based on o3 suggestion):
- **JSONL format** (append-only, atomic writes)
- **One line per iteration**:
  ```json
  {
    "iteration": 1,
    "timestamp": "ISO8601",
    "code": "full strategy code",
    "execution_status": "success|failed",
    "metrics": {...},
    "summary": "NL summary",
    "error": "error message if failed",
    "prompt_tokens": 1500,
    "completion_tokens": 800
  }
  ```
- **No automatic checkpoint recovery** (MVP out-of-scope)
- **Equity curve**: omitted from log (too large, can be regenerated)

**File Management**:
- Append-only (no overwrites)
- Rotation: manual (future enhancement)
- Backup: none (MVP accepts data loss risk)

---

## 2. Data Flow

### 2.1 Main Iteration Loop

```
┌─────────────────────────────────────────────────────┐
│ START                                               │
└─────────────┬───────────────────────────────────────┘
              │
              v
┌─────────────────────────────────────────────────────┐
│ Load API Keys, Datasets, Initialize Log            │
└─────────────┬───────────────────────────────────────┘
              │
              v
       ┌──────────────┐
       │ i = 0 to 9   │ <──────────────────┐
       └──────┬───────┘                    │
              │                            │
              v                            │
┌─────────────────────────────────────────┐           │
│ Generate Strategy Code                  │           │
│ - build_prompt(datasets, history)       │           │
│ - claude_api_call()                     │           │
│ - extract_code()                        │           │
└─────────────┬───────────────────────────┘           │
              │                                        │
              v                                        │
┌─────────────────────────────────────────┐           │
│ Validate Code (AST)                     │           │
│ - check_imports()                       │           │
│ - check_shifts()                        │           │
│ - if invalid: code = TEMPLATE           │           │
└─────────────┬───────────────────────────┘           │
              │                                        │
              v                                        │
┌─────────────────────────────────────────┐           │
│ Execute Strategy (Sandbox)              │           │
│ - spawn process                         │           │
│ - run with timeout=120s                 │           │
│ - extract_metrics()                     │           │
└─────────────┬───────────────────────────┘           │
              │                                        │
              v                                        │
┌─────────────────────────────────────────┐           │
│ Create NL Summary                       │           │
│ - format success/failure message        │           │
│ - add improvement hints                 │           │
└─────────────┬───────────────────────────┘           │
              │                                        │
              v                                        │
┌─────────────────────────────────────────┐           │
│ Log to iterations.jsonl                 │           │
│ - append JSON line                      │           │
│ - history.append(summary)               │           │
└─────────────┬───────────────────────────┘           │
              │                                        │
              └────────────────────────────────────────┘
              │
              v
┌─────────────────────────────────────────┐
│ Select Best Strategy (by Sharpe)        │
│ Export to best_strategy.py              │
│ Print Summary Report                    │
└─────────────┬───────────────────────────┘
              │
              v
┌─────────────────────────────────────────┐
│ END                                     │
└─────────────────────────────────────────┘
```

---

## 3. Technical Decisions Summary

| Decision | Chosen Approach | Rationale | Source |
|----------|----------------|-----------|--------|
| **Execution Isolation** | Multiprocessing (spawn) | Process isolation, reliable timeout, cross-platform | Gemini |
| **Feedback Format** | Natural language summary | LLMs reason better on NL than structured data | Gemini |
| **Pattern Extraction** | None (let Claude infer) | Simpler, avoids premature optimization | Gemini |
| **Logging Format** | JSONL append-only | Atomic writes, easy streaming, no overwrites | o3 |
| **Metrics Storage** | Plain dict scalars | Handle finlab report serialization issues | o3 |
| **Dataset Curation** | 50 (not 719) | Avoid prompt bloat, focus on high-value data | o3 |
| **Temperature** | 0.3 (start) | High determinism for reliability, can raise later | o3 |
| **AST Validation** | Block imports/exec/shift(-) | Catches 80-90% of issues, simple implementation | o3 |
| **Fallback Strategy** | Simple RSI template | Guarantee at least one working strategy | o3 |
| **Checkpoint Recovery** | Out of scope | MVP runs in <30min, manual restart acceptable | User |
| **IC/ICIR Calculation** | Out of scope | Premature optimization, let Claude learn from results | Gemini |

---

## 4. File Structure

```
finlab/
├── iteration_engine.py          # Main script (~400 lines)
├── validate_code.py             # AST validator (~100 lines)
├── sandbox_executor.py          # Multiprocessing sandbox (~150 lines)
├── extract_metrics.py           # Result extraction (~50 lines)
├── datasets_curated_50.json     # Curated dataset list
├── prompt_template_v1.txt       # Baseline prompt
├── iterations.jsonl             # Runtime log (generated)
├── best_strategy.py             # Best result (generated)
└── .env                         # API keys (not in git)
```

**Total Complexity**: ~700 lines (within acceptable range for MVP)

---

## 5. Performance Targets (NFRs)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Single strategy generation** | < 30s | Claude API latency |
| **Single backtest execution** | < 120s | Enforced by timeout |
| **10 iterations total** | < 30min | End-to-end measurement |
| **Success rate** | >= 70% | 7/10 iterations complete successfully |
| **Code generation reliability** | >= 60% | 3/5 in PoC, improves with prompt tuning |

---

## 6. Security Model

**Threat Model**: Malicious/buggy Claude-generated code

**Defense Layers**:
1. **AST Validation** (80-90% coverage)
   - Blocks: imports, exec, eval, open, file I/O
   - Validates: shift patterns, function calls

2. **Multiprocessing Isolation** (99% coverage)
   - Separate memory space
   - Restricted builtins
   - Timeout enforcement

3. **Safe Globals** (99.9% coverage)
   - Whitelist-only approach
   - No access to os, sys, subprocess

**Residual Risk**: Accepted for personal research project

**Not Defended Against**:
- Advanced sandbox escapes (e.g., `().__class__.__base__.__subclasses__()`)
- Social engineering attacks on prompt
- Side-channel attacks

**Mitigation**: Run on isolated machine, no sensitive data

---

## 7. Future Enhancements (Out of MVP Scope)

**Phase 2 Candidates** (if MVP succeeds):
1. IC/ICIR factor evaluation tools
2. Dynamic temperature adjustment (start 0.3, raise to 0.7)
3. Automatic checkpoint recovery
4. Parallel iteration execution (3 strategies at once)
5. Web UI (Streamlit)
6. SQLite storage (replace JSONL)

**Never Implement** (confirmed out-of-scope):
- Real-time trading integration
- Cloud deployment
- Multi-user support
- Complete test suite (unit/integration/E2E)

---

## 8. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2025-10-07 | Claude + Gemini 2.5 Pro + o3 | Initial design based on multi-AI collaboration |

---

## 9. Approval & Sign-off

**Technical Review**:
- [x] Gemini 2.5 Pro: Architecture & Risk Analysis
- [x] OpenAI o3: Technical Implementation Details
- [ ] User: Final approval

**Next Steps**:
1. User approval of design
2. Begin Phase 1 (Prompt PoC)
3. Update requirements.md with approved design decisions
