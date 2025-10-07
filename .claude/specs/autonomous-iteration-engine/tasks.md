# Implementation Tasks - Autonomous Strategy Iteration Engine

## Task Structure

Tasks are organized into **4 phases** following a bottom-up approach:
1. **Phase 1**: Prompt Engineering PoC (概念驗證)
2. **Phase 2**: Execution Engine (執行引擎)
3. **Phase 3**: Main Loop Integration (主循環整合)
4. **Phase 4**: Polish & Documentation (優化與文檔)

Each task is **atomic** (15-30 min), touches 1-3 files, and has clear success criteria.

---

## Phase 1: Prompt Engineering PoC

### Task 1.1: Create Curated Dataset List
- **File**: `datasets_curated_50.json`
- **Description**:
  - Select 50 high-value datasets from 719 discovered datasets
  - Categories: Price (10), Broker (5), Institutional (10), Fundamental (15), Technical (10)
  - Include brief description for each (Chinese + English)
- **Success Criteria**:
  - JSON file with 50 entries
  - Each entry has: `id`, `name_zh`, `name_en`, `category`, `description`
- **Estimated Time**: 30 min

### Task 1.2: Design Baseline Prompt Template
- **File**: `prompt_template_v1.txt`
- **Description**:
  - Create system prompt with curated dataset list
  - Define code requirements (position DataFrame, sim() call, report variable)
  - Add constraints (shift(1+), no imports, etc.)
- **Success Criteria**:
  - Prompt template with placeholders for {datasets}, {history}
  - Clear instructions in English
  - Returns executable Python code only
- **Estimated Time**: 20 min

### Task 1.3: Implement Claude API Call Function
- **File**: `poc_claude_test.py`
- **Description**:
  - Load API key from environment
  - Call Claude API with baseline prompt
  - Extract code from ```python blocks
  - Handle API errors (timeout, rate limit)
- **Success Criteria**:
  - Function `generate_strategy() -> str`
  - Successful API call with temperature=0.3
  - Code extraction works
- **Estimated Time**: 30 min

### Task 1.4: Manual Execution Test (5 iterations)
- **File**: `poc_results.md`
- **Description**:
  - Generate 5 strategies using poc_claude_test.py
  - Manually execute each in Python REPL
  - Record: syntax errors, execution errors, trade count
  - Calculate success rate
- **Success Criteria**:
  - >= 3/5 strategies execute successfully
  - >= 2/5 strategies have >0 trades
  - Documented results in poc_results.md
- **Estimated Time**: 60 min (includes debugging)

### Task 1.5: Prompt Refinement (if needed)
- **File**: `prompt_template_v1.txt` (update)
- **Description**:
  - Analyze failures from Task 1.4
  - Refine prompt based on common errors
  - Re-test with 3 additional generations
- **Success Criteria**:
  - Improved success rate (>= 4/5)
  - Documented changes in poc_results.md
- **Estimated Time**: 30 min
- **Skip if**: Task 1.4 already achieves >= 4/5 success

---

## Phase 2: Execution Engine

### Task 2.1: Implement AST Security Validator
- **File**: `validate_code.py`
- **Description**:
  - Create `SecurityValidator(ast.NodeVisitor)` class
  - Block: Import, ImportFrom, Exec, Eval nodes
  - Block: open(), __import__(), compile() function calls
  - Check shift patterns: only allow .shift(positive_int)
- **Success Criteria**:
  - Function `validate_code(code) -> (bool, List[str])`
  - Correctly rejects: `import os`, `exec()`, `.shift(-1)`
  - Returns detailed error messages
- **Estimated Time**: 45 min

### Task 2.2: Create Test Cases for AST Validator
- **File**: `test_validate_code.py`
- **Description**:
  - Test case 1: Valid finlab strategy (should pass)
  - Test case 2: Code with `import os` (should fail)
  - Test case 3: Code with `.shift(-1)` (should fail)
  - Test case 4: Code with `eval()` (should fail)
- **Success Criteria**:
  - All 4 test cases pass
  - False positive rate < 10%
- **Estimated Time**: 20 min

### Task 2.3: Implement Multiprocessing Sandbox
- **File**: `sandbox_executor.py`
- **Description**:
  - Set `multiprocessing.start_method("spawn")`
  - Define `safe_globals` with restricted builtins
  - Implement `execute_strategy_wrapper(code, safe_globals, result_queue)`
  - Implement `run_strategy_safe(code, timeout=120) -> Dict`
- **Success Criteria**:
  - Process spawns correctly on Windows/Linux
  - Timeout terminates process (test with infinite loop)
  - Returns result via Queue
- **Estimated Time**: 60 min

### Task 2.4: Implement Metrics Extraction
- **File**: `extract_metrics.py`
- **Description**:
  - Test if finlab report is picklable
  - If not, extract scalars immediately in worker process
  - Return dict: annual_return, sharpe_ratio, max_drawdown, win_rate, total_trades
- **Success Criteria**:
  - Function `extract_metrics(report) -> Dict`
  - All metrics are float/int (serializable)
  - Handles missing metrics gracefully
- **Estimated Time**: 30 min

### Task 2.5: Integration Test for Execution Engine
- **File**: `test_execution_engine.py`
- **Description**:
  - Use successful strategy from Phase 1
  - Full pipeline: AST validate → Sandbox execute → Extract metrics
  - Test timeout with deliberate infinite loop
  - Test AST rejection with malicious code
- **Success Criteria**:
  - Valid strategy executes and returns correct metrics
  - Timeout works (120s limit enforced)
  - Malicious code is blocked by AST
- **Estimated Time**: 30 min

---

## Phase 3: Main Loop Integration

### Task 3.1: Create Main Script Structure
- **File**: `iteration_engine.py`
- **Description**:
  - Setup section: load API keys, datasets, initialize logging
  - Main loop: for i in range(10)
  - Final report: select and export best strategy
  - Error handling: try-except around main loop
- **Success Criteria**:
  - Script runs without imports errors
  - Main loop structure in place (empty functions OK)
- **Estimated Time**: 20 min

### Task 3.2: Implement Strategy Generation Function
- **File**: `iteration_engine.py` (update)
- **Description**:
  - Function `generate_strategy(iteration_num, history) -> str`
  - Iteration 0: use baseline prompt only
  - Iteration 1+: append history summary to prompt
  - Call Claude API, extract code block
  - Retry logic: 3 attempts with exponential backoff
- **Success Criteria**:
  - Generates code for iteration 0 successfully
  - Includes history in iterations 1+
  - Handles API errors gracefully
- **Estimated Time**: 40 min

### Task 3.3: Implement NL Summary Generator
- **File**: `iteration_engine.py` (update)
- **Description**:
  - Function `create_nl_summary(iteration, result, metrics) -> str`
  - Success format: metrics + analysis + improvement hint
  - Failure format: error + diagnosis + fix suggestion
  - Helper: `generate_improvement_hint(metrics)` (simple rules)
- **Success Criteria**:
  - Returns structured NL summary
  - Clear, actionable feedback
  - Success and failure formats different
- **Estimated Time**: 30 min

### Task 3.4: Implement JSONL Logging System
- **File**: `iteration_engine.py` (update)
- **Description**:
  - Function `log_iteration(iteration, code, result, summary)`
  - Append-only write to `iterations.jsonl`
  - Log format: JSON with all required fields
  - Atomic write (open, write, close immediately)
- **Success Criteria**:
  - Creates iterations.jsonl if not exists
  - Each line is valid JSON
  - File readable after multiple iterations
- **Estimated Time**: 20 min

### Task 3.5: Add Template Fallback
- **File**: `iteration_engine.py` (update)
- **Description**:
  - Define `TEMPLATE_FALLBACK` (simple RSI strategy)
  - Trigger when AST validation fails
  - Log when fallback is used
- **Success Criteria**:
  - Template is valid Finlab code
  - Fallback triggers correctly
  - Logged in iterations.jsonl
- **Estimated Time**: 15 min

### Task 3.6: Implement Best Strategy Selection
- **File**: `iteration_engine.py` (update)
- **Description**:
  - Function `select_best_strategy(history) -> Dict`
  - Sort by sharpe_ratio (descending)
  - Export code to `best_strategy.py`
  - Print summary report to terminal
- **Success Criteria**:
  - Correctly identifies best strategy
  - Exports executable code
  - Summary includes key metrics
- **Estimated Time**: 20 min

### Task 3.7: End-to-End Test (3 iterations)
- **File**: None (run iteration_engine.py)
- **Description**:
  - Run iteration_engine.py with 3 iterations
  - No manual intervention
  - Verify all components work together
  - Check iterations.jsonl and best_strategy.py
- **Success Criteria**:
  - >= 2/3 iterations complete successfully
  - JSONL log has 3 entries
  - best_strategy.py created
  - No crashes
- **Estimated Time**: 30 min (includes debugging)

---

## Phase 4: Polish & Documentation

### Task 4.1: Add Logging and Progress Display
- **File**: `iteration_engine.py` (update)
- **Description**:
  - Add terminal progress display:
    ```
    ==========================================
    Iteration 3/10
    ==========================================
    Generating strategy...
    Validating code...
    Executing backtest...
    ```
  - Use logging module for errors
  - Color output (optional, using colorama)
- **Success Criteria**:
  - Clear progress indication
  - Errors logged to file
- **Estimated Time**: 20 min

### Task 4.2: Add Error Recovery and Retries
- **File**: `iteration_engine.py` (update)
- **Description**:
  - Claude API: retry 3 times with exponential backoff
  - Execution timeout: log and continue to next iteration
  - AST failure: use template, don't crash
- **Success Criteria**:
  - API errors don't crash loop
  - Execution failures logged and skipped
  - >= 7/10 iterations complete in normal run
- **Estimated Time**: 30 min

### Task 4.3: Create README.md
- **File**: `README.md`
- **Description**:
  - Project overview
  - Installation steps (requirements.txt, API keys)
  - Usage: `python iteration_engine.py`
  - Output files explanation
  - Limitations and known issues
- **Success Criteria**:
  - User can follow instructions without prior knowledge
  - All necessary information included
- **Estimated Time**: 30 min

### Task 4.4: Create requirements.txt
- **File**: `requirements.txt`
- **Description**:
  - List all dependencies with versions:
    ```
    finlab>=1.5.3
    anthropic>=0.40.0
    pandas>=2.0.0
    numpy>=1.24.0
    python-dotenv>=1.0.0
    ```
- **Success Criteria**:
  - `pip install -r requirements.txt` works
  - All imports successful
- **Estimated Time**: 10 min

### Task 4.5: Full 10-Iteration Test Run
- **File**: None (final validation)
- **Description**:
  - Run iteration_engine.py for full 10 iterations
  - No manual intervention
  - Measure total time
  - Analyze success rate and quality
- **Success Criteria**:
  - >= 7/10 iterations successful
  - Total time < 30 minutes
  - Best strategy has positive Sharpe ratio
  - All output files generated correctly
- **Estimated Time**: 40 min

---

## Task Summary

| Phase | Tasks | Estimated Total Time |
|-------|-------|---------------------|
| Phase 1: Prompt PoC | 5 tasks | 2.5-3 hours |
| Phase 2: Execution Engine | 5 tasks | 3-4 hours |
| Phase 3: Main Loop | 7 tasks | 3-4 hours |
| Phase 4: Polish | 5 tasks | 2-3 hours |
| **TOTAL** | **22 tasks** | **10-14 hours** |

## Task Dependencies

```
Phase 1 (PoC)
  │
  ├─ 1.1 --> 1.2 --> 1.3 --> 1.4 -------> 1.5 (optional)
  │                                        │
  v                                        v
Phase 2 (Engine)                     Phase 3 (Loop)
  │                                        │
  ├─ 2.1 --> 2.2                          │
  ├─ 2.3 --> 2.4 ---------> 2.5           │
  │                          │             │
  v                          v             v
                        (Integration)     3.1 --> 3.2 --> 3.3
                                           │       │       │
                                           └───────┴───────┴--> 3.4 --> 3.5 --> 3.6 --> 3.7
                                                                                         │
                                                                                         v
                                                                                    Phase 4 (Polish)
                                                                                         │
                                                                                         ├─ 4.1
                                                                                         ├─ 4.2
                                                                                         ├─ 4.3
                                                                                         ├─ 4.4
                                                                                         v
                                                                                        4.5 (Final Test)
```

## Success Criteria (MVP)

- [ ] All 22 tasks completed
- [ ] Full 10-iteration run completes successfully
- [ ] Success rate >= 70% (7/10 iterations)
- [ ] Best strategy exported with Sharpe > 0
- [ ] All output files generated correctly
- [ ] README allows user to run without help

## Next Steps After MVP

If MVP succeeds (all criteria met):
1. Implement IC/ICIR factor evaluation (future enhancement)
2. Dynamic temperature adjustment (0.3 → 0.7)
3. Parallel iteration execution
4. Web UI (Streamlit)

If MVP partially succeeds (50-69% success rate):
1. Analyze failure patterns
2. Refine prompt template
3. Adjust AST validation rules
4. Re-test

If MVP fails (<50% success rate):
1. Review fundamental assumptions
2. Consider alternative approaches
3. Potentially pivot or abort project
