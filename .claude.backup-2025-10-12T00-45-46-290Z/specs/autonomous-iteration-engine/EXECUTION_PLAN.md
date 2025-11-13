# Execution Plan - Autonomous Iteration Engine

**Last Updated**: 2025-10-09
**Status**: Ready for execution
**Total Estimated Time**: 10.5-11.5 hours (optimized from 14-19 hours)

---

## Executive Summary

**Optimization Strategy**: Parallel workstreams with early risk validation

**Key Changes from Original Plan**:
1. Added Phase 0 (Setup & Validation) - 30 minutes
2. Parallel execution of independent tasks (saves ~65 minutes)
3. Increased time estimates for high-risk tasks (realistic buffers)
4. Added Integration debugging buffer (60 minutes)
5. Early GO/NO-GO decision point at ~4-5 hours

**Critical Path**: Phase 0 → Track A (Generation) → Integration → Polish

---

## Parallel Workstream Strategy

### Workstream A: Generation & Core Logic (CRITICAL PATH)
**Purpose**: Validate project viability - can LLM generate working strategies?
**Duration**: ~4.5-5 hours
**Risk Level**: HIGH (exploratory, uncertain)

```
Phase 0 (Setup) → Track A Tasks → Integration
```

### Workstream B: Execution Infrastructure (PARALLEL)
**Purpose**: Build safety machinery for code execution
**Duration**: ~2.5-3 hours
**Risk Level**: MEDIUM (technically complex but predictable)

```
Phase 0 (Setup) → Track B Tasks → Integration
```

### Workstream C: Main Structure (PARALLEL)
**Purpose**: Scaffold integration points early
**Duration**: ~20 minutes
**Risk Level**: LOW (structural only)

```
Phase 0 (Setup) → Track C Task → Integration
```

---

## Detailed Task Breakdown

### Phase 0: Setup & Validation (30 min) - SEQUENTIAL START

#### Task 0.1: Create requirements.txt (10 min)
**File**: `requirements.txt`
**Status**: Pending
**Dependencies**: None

**Description**:
- List all Python dependencies with version constraints
- Categories: AI/API, Data Processing, Backtesting, Testing, Environment
- Ensure compatibility with Python 3.8+

**Required Dependencies**:
```
# AI & API
openai>=1.0.0              # OpenRouter client for Claude
httpx>=0.24.0              # HTTP client

# Data Processing
pandas>=2.0.0              # Time series analysis
numpy>=1.24.0              # Numerical operations
duckdb>=0.8.0              # Local data warehouse

# Backtesting
finlab>=1.5.3              # Taiwan stock market backtesting

# Testing
pytest>=7.0.0              # Test framework
pytest-cov>=4.0.0          # Code coverage

# Environment
python-dotenv>=1.0.0       # API key management
```

**Success Criteria**:
- [x] File created with all dependencies
- [x] Version constraints specified
- [x] Organized by category with comments
- [x] Compatible with existing project

---

#### Task 0.2: Environment Validation Script (20 min)
**File**: `validate_environment.py`
**Status**: Pending
**Dependencies**: Task 0.1

**Description**:
- Check for required environment variables (FINLAB_API_TOKEN, OPENROUTER_API_KEY)
- Test Finlab API connectivity
- Verify Claude API access via OpenRouter
- Validate Python version (3.8+)

**Success Criteria**:
- [x] Script checks all environment variables
- [x] Tests API connectivity
- [x] Provides clear error messages
- [x] Returns exit code 0 on success

---

### Track A: Generation & Core Logic (CRITICAL PATH)

#### Task A1: Curate 50 Datasets (75 min)
**File**: `datasets_curated_50.json`
**Status**: Pending
**Dependencies**: Task 0.2
**Original Estimate**: 30 min → **Revised**: 75 min

**Why Revised**: Manual curation requires understanding dataset characteristics, not just selection. Includes documentation of rationale for debugging.

**Description**:
- Select 50 high-value datasets from 719 available Finlab datasets
- Categories: Price (10), Broker (5), Institutional (10), Fundamental (15), Technical (10)
- Include bilingual descriptions (Chinese + English)
- Document selection rationale for each

**Leverage Existing Knowledge**:
- Check `learning-system-enhancement` spec for previously validated datasets
- Review existing strategy files for commonly used data

**Success Criteria**:
- [x] JSON file with 50 entries
- [x] Each entry: id, name_zh, name_en, category, description, rationale
- [x] Well-distributed across categories
- [x] High-value datasets prioritized

---

#### Task A2: Design Baseline Prompt Template (20 min)
**File**: `prompt_template_v1.txt`
**Status**: Pending
**Dependencies**: Task A1

**Description**:
- Create system prompt with curated dataset list
- Define code requirements (position DataFrame, sim() call, report variable)
- Add constraints (shift(1+), no imports, etc.)
- Include placeholders for {datasets}, {history}

**Success Criteria**:
- [x] Clear instructions in English
- [x] Returns executable Python code only
- [x] Includes all safety constraints
- [x] Template tested with Claude API

---

#### Task A3: Implement Claude API Call Function (30 min)
**File**: `poc_claude_test.py`
**Status**: Pending
**Dependencies**: Task A2

**Description**:
- Load API key from environment (OPENROUTER_API_KEY)
- Call Claude API with baseline prompt
- Extract code from ```python blocks
- Handle API errors (timeout, rate limit)
- Implement retry with exponential backoff

**Success Criteria**:
- [x] Function `generate_strategy() -> str`
- [x] Successful API call with temperature=0.3
- [x] Code extraction works reliably
- [x] Error handling tested

---

#### Task A4: Manual Test 5 Iterations (120 min) - GO/NO-GO DECISION POINT
**File**: `poc_results.md`
**Status**: Pending
**Dependencies**: Task A3
**Original Estimate**: 60 min → **Revised**: 120 min

**Why Revised**: Exploratory testing with debugging requires realistic time allocation. Each iteration: generate → inspect → execute → debug → document.

**Description**:
- Generate 5 strategies using poc_claude_test.py
- Manually execute each in Python REPL
- Record: syntax errors, execution errors, trade count, metrics
- Calculate success rate
- Document failure patterns

**Success Criteria**:
- [x] >= 3/5 strategies execute successfully (60% minimum)
- [x] >= 2/5 strategies have >0 trades
- [x] Documented results with failure analysis
- [x] **GO/NO-GO DECISION**: If <60% success, pivot or abort

**Critical Decision Point**:
- **GO**: >= 60% success → Continue to Task A5
- **NO-GO**: <60% success → Re-evaluate approach or abort project

---

#### Task A5: Final Prompt Refinement (30 min, conditional)
**File**: `prompt_template_v1.txt` (update)
**Status**: Pending
**Dependencies**: Task A4
**Condition**: Skip if Task A4 achieves >=80% success

**Description**:
- Analyze failures from Task A4
- Refine prompt based on common error patterns
- Re-test with 3 additional generations
- Document improvements

**Success Criteria**:
- [x] Improved success rate (>= 80%)
- [x] Changes documented
- [x] Re-test validates improvements

---

### Track B: Execution Infrastructure (PARALLEL with Track A)

#### Task B1: AST Security Validator (45 min)
**File**: `validate_code.py`
**Status**: Pending
**Dependencies**: Task 0.2
**Can Start**: Immediately after Phase 0

**Description**:
- Create `SecurityValidator(ast.NodeVisitor)` class
- Block: Import, ImportFrom, Exec, Eval nodes
- Block: open(), __import__(), compile() function calls
- Check shift patterns: only allow .shift(positive_int)

**Success Criteria**:
- [x] Function `validate_code(code) -> (bool, List[str])`
- [x] Correctly rejects dangerous code
- [x] Returns detailed error messages
- [x] 80-90% coverage of common security issues

---

#### Task B2: AST Test Cases (20 min)
**File**: `test_validate_code.py`
**Status**: Pending
**Dependencies**: Task B1

**Description**:
- Test case 1: Valid finlab strategy (should pass)
- Test case 2: Code with `import os` (should fail)
- Test case 3: Code with `.shift(-1)` (should fail)
- Test case 4: Code with `eval()` (should fail)

**Success Criteria**:
- [x] All 4 test cases pass
- [x] False positive rate < 10%
- [x] Clear test documentation

---

#### Task B3: Multiprocessing Sandbox (60 min)
**File**: `sandbox_executor.py`
**Status**: Pending
**Dependencies**: Task 0.2
**Can Start**: Immediately after Phase 0

**Description**:
- Set `multiprocessing.start_method("spawn")` for cross-platform compatibility
- Define `safe_globals` with restricted builtins
- Implement `execute_strategy_wrapper(code, safe_globals, result_queue)`
- Implement `run_strategy_safe(code, timeout=120) -> Dict`

**Success Criteria**:
- [x] Process spawns correctly on Windows/Linux
- [x] Timeout terminates process (tested with infinite loop)
- [x] Returns result via Queue
- [x] Handles serialization correctly

---

#### Task B4: Metrics Extraction (30 min)
**File**: `extract_metrics.py`
**Status**: Pending
**Dependencies**: Task B3

**Description**:
- Test if finlab report is picklable
- Extract scalars immediately in worker process if not
- Return dict: annual_return, sharpe_ratio, max_drawdown, win_rate, total_trades

**Success Criteria**:
- [x] Function `extract_metrics(report) -> Dict`
- [x] All metrics are serializable (float/int)
- [x] Handles missing metrics gracefully
- [x] Error handling tested

---

### Track C: Main Structure (PARALLEL with Track A & B)

#### Task C1: Main Script Structure (20 min)
**File**: `iteration_engine.py`
**Status**: Pending
**Dependencies**: Task 0.2
**Can Start**: Immediately after Phase 0

**Description**:
- Create main script scaffold
- Setup section: load API keys, datasets, initialize logging
- Main loop structure: for i in range(10)
- Define interfaces for: validator, sandbox, generator, logger
- Final report section: select and export best strategy
- Error handling: try-except around main loop

**Success Criteria**:
- [x] Script runs without import errors
- [x] Main loop structure in place (placeholder functions OK)
- [x] Interfaces defined for all components
- [x] State management designed

---

## Integration Phase (After Tracks Complete)

### Integration 1: Engine Integration Test (45 min)
**File**: `test_execution_engine.py`
**Status**: Pending
**Dependencies**: Tasks B1, B2, B3, B4, A4
**Original Estimate**: 30 min → **Revised**: 45 min

**Description**:
- Use successful strategy from Track A
- Full pipeline: AST validate → Sandbox execute → Extract metrics
- Test timeout with deliberate infinite loop
- Test AST rejection with malicious code

**Success Criteria**:
- [x] Valid strategy executes and returns correct metrics
- [x] Timeout works (120s limit enforced)
- [x] Malicious code blocked by AST
- [x] Integration points verified

---

### Integration 2: Strategy Generation Function (40 min)
**File**: `iteration_engine.py` (update)
**Status**: Pending
**Dependencies**: Task A3, C1

**Description**:
- Integrate Claude API client into main loop
- Function `generate_strategy(iteration_num, history) -> str`
- Iteration 0: use baseline prompt only
- Iteration 1+: append history summary to prompt
- Retry logic: 3 attempts with exponential backoff

**Success Criteria**:
- [x] Generates code for iteration 0 successfully
- [x] Includes history in iterations 1+
- [x] Handles API errors gracefully
- [x] Integrated with main loop

---

### Integration 3: Template Fallback (15 min)
**File**: `iteration_engine.py` (update)
**Status**: Pending
**Dependencies**: Task B1, C1

**Description**:
- Define `TEMPLATE_FALLBACK` (simple RSI strategy)
- Trigger when AST validation fails
- Log when fallback is used

**Success Criteria**:
- [x] Template is valid Finlab code
- [x] Fallback triggers correctly
- [x] Logged appropriately

---

### Integration 4: Best Strategy Selection (20 min)
**File**: `iteration_engine.py` (update)
**Status**: Pending
**Dependencies**: Task B4, C1

**Description**:
- Function `select_best_strategy(history) -> Dict`
- Sort by sharpe_ratio (descending)
- Export code to `best_strategy.py`
- Print summary report to terminal

**Success Criteria**:
- [x] Correctly identifies best strategy
- [x] Exports executable code
- [x] Summary includes key metrics

---

### Integration 5: NL Summary Generator (30 min) - PARALLEL
**File**: `iteration_engine.py` (update)
**Status**: Pending
**Dependencies**: C1

**Description**:
- Function `create_nl_summary(iteration, result, metrics) -> str`
- Success format: metrics + analysis + improvement hint
- Failure format: error + diagnosis + fix suggestion
- Helper: `generate_improvement_hint(metrics)`

**Success Criteria**:
- [x] Returns structured NL summary
- [x] Clear, actionable feedback
- [x] Different formats for success/failure

---

### Integration 6: JSONL Logging (20 min) - PARALLEL
**File**: `iteration_engine.py` (update)
**Status**: Pending
**Dependencies**: C1

**Description**:
- Function `log_iteration(iteration, code, result, summary)`
- Append-only write to `iterations.jsonl`
- JSON format with all required fields
- Atomic write (open, write, close immediately)

**Success Criteria**:
- [x] Creates iterations.jsonl if not exists
- [x] Each line is valid JSON
- [x] File readable after multiple iterations

---

### Integration 7: E2E Test 3 Iterations (60 min)
**File**: None (run iteration_engine.py)
**Status**: Pending
**Dependencies**: All Integration 1-6
**Original Estimate**: 30 min → **Revised**: 60 min

**Why Revised**: First-time E2E test will expose integration issues. Realistic buffer needed.

**Description**:
- Run iteration_engine.py with 3 iterations
- No manual intervention
- Verify all components work together
- Check iterations.jsonl and best_strategy.py

**Success Criteria**:
- [x] >= 2/3 iterations complete successfully (67% minimum)
- [x] JSONL log has 3 entries
- [x] best_strategy.py created
- [x] No crashes

---

### Integration 8: Debugging Buffer (60 min) - NEW
**File**: Various
**Status**: Pending
**Dependencies**: Integration 7

**Why Added**: Integration issues are inevitable. Budget time for systematic debugging.

**Description**:
- Debug integration issues from Integration 7
- Fix data format mismatches
- Resolve unexpected sandbox behavior
- Correct error handling assumptions

**Success Criteria**:
- [x] All Integration 7 issues resolved
- [x] >= 90% success rate on re-test
- [x] Issues documented

---

## Polish Phase

### Polish 1: Logging & Progress Display (20 min)
**File**: `iteration_engine.py` (update)
**Status**: Pending
**Dependencies**: Integration 8

**Description**:
- Add terminal progress display
- Use logging module for errors
- Optional: Color output (colorama)

**Success Criteria**:
- [x] Clear progress indication
- [x] Errors logged to file
- [x] User-friendly output

---

### Polish 2: Error Recovery & Retries (45 min)
**File**: `iteration_engine.py` (update)
**Status**: Pending
**Dependencies**: Integration 8
**Original Estimate**: 30 min → **Revised**: 45 min

**Why Revised**: Comprehensive error recovery requires testing multiple failure scenarios.

**Description**:
- Claude API: retry 3 times with exponential backoff
- Execution timeout: log and continue to next iteration
- AST failure: use template, don't crash

**Success Criteria**:
- [x] API errors don't crash loop
- [x] Execution failures logged and skipped
- [x] >= 7/10 iterations complete in normal run

---

### Polish 3: README Documentation (30 min)
**File**: `README.md`
**Status**: Pending
**Dependencies**: Integration 8

**Description**:
- Project overview
- Installation steps (requirements.txt, API keys)
- Usage: `python iteration_engine.py`
- Output files explanation
- Limitations and known issues

**Success Criteria**:
- [x] User can follow without prior knowledge
- [x] All necessary information included
- [x] Clear and concise

---

### Polish 4: Full 10-Iteration Test (60 min) - FINAL VALIDATION
**File**: None (final validation)
**Status**: Pending
**Dependencies**: Polish 1, 2, 3
**Original Estimate**: 40 min → **Revised**: 60 min

**Why Revised**: Full 10-iteration run may expose rare issues. Buffer for validation.

**Description**:
- Run iteration_engine.py for full 10 iterations
- No manual intervention
- Measure total time
- Analyze success rate and quality

**Success Criteria**:
- [x] >= 7/10 iterations successful (70% MVP target)
- [x] Total time < 30 minutes (NFR-1.3)
- [x] Best strategy has positive Sharpe ratio
- [x] All output files generated correctly

---

## Execution Timeline

### Optimized Timeline (10.5-11.5 hours)

```
Hour 0-0.5: Phase 0 (Setup & Validation)
  ├─ 0.1: requirements.txt (10 min)
  └─ 0.2: validate_environment.py (20 min)

Hour 0.5-5.5: PARALLEL EXECUTION
  ├─ Track A (CRITICAL PATH): 4.5-5 hours
  │   ├─ A1: Curate datasets (75 min)
  │   ├─ A2: Prompt template (20 min)
  │   ├─ A3: API call function (30 min)
  │   ├─ A4: Manual test [GO/NO-GO] (120 min)
  │   └─ A5: Refinement (30 min, conditional)
  │
  ├─ Track B (PARALLEL): 2.5-3 hours
  │   ├─ B1: AST validator (45 min)
  │   ├─ B2: AST tests (20 min)
  │   ├─ B3: Sandbox (60 min)
  │   └─ B4: Metrics (30 min)
  │
  └─ Track C (PARALLEL): 20 min
      └─ C1: Main structure (20 min)

Hour 5.5-9.0: INTEGRATION (3-3.5 hours)
  ├─ Integration 1: Engine test (45 min)
  ├─ Integration 2: Strategy gen (40 min)
  ├─ Integration 3: Fallback (15 min)
  ├─ Integration 4: Selection (20 min)
  ├─ Integration 5: NL summary (30 min) - PARALLEL
  ├─ Integration 6: JSONL logging (20 min) - PARALLEL
  ├─ Integration 7: E2E test (60 min)
  └─ Integration 8: Debug buffer (60 min)

Hour 9.0-11.5: POLISH (2.5 hours)
  ├─ Polish 1: Logging display (20 min)
  ├─ Polish 2: Error recovery (45 min)
  ├─ Polish 3: README (30 min)
  └─ Polish 4: Full test (60 min)
```

### Critical Path Highlighted

```
0.1 → 0.2 → A1 → A2 → A3 → A4 [GO/NO-GO] → A5 → Integration → Polish
└─────────── 4-5 hours to decision point ──────────┘
```

---

## Risk Management

### High-Risk Tasks

1. **Task A4 (Manual Test - GO/NO-GO)**: 120 min
   - **Risk**: LLM may not generate viable strategies
   - **Mitigation**: Early decision point at 4-5 hours
   - **Fallback**: Pivot to manual strategy templates or abort

2. **Integration 7 (E2E Test)**: 60 min
   - **Risk**: Integration points may have subtle bugs
   - **Mitigation**: Added Integration 8 debugging buffer (60 min)
   - **Fallback**: Systematic component isolation

3. **Polish 4 (Full Test)**: 60 min
   - **Risk**: Rare issues may emerge at scale
   - **Mitigation**: Comprehensive error recovery (Polish 2)
   - **Fallback**: Reduce iteration count if needed

### Medium-Risk Tasks

1. **Task A1 (Dataset Curation)**: 75 min
   - **Risk**: Unfamiliarity with 719 datasets
   - **Mitigation**: Leverage existing project knowledge
   - **Fallback**: Start with familiar datasets

2. **Task B3 (Multiprocessing Sandbox)**: 60 min
   - **Risk**: Cross-platform compatibility issues
   - **Mitigation**: Use spawn mode (Windows compatible)
   - **Fallback**: Subprocess with timeout

### Success Metrics

**MVP Success Criteria**:
- [x] >= 70% iteration success rate (7/10)
- [x] Total execution time < 30 minutes
- [x] Best strategy Sharpe ratio > 0
- [x] All output files generated

**Quality Gates**:
1. Phase 0: Environment validated
2. Track A: >= 60% strategy generation success
3. Integration 7: >= 67% E2E success (2/3)
4. Polish 4: >= 70% full test success (7/10)

---

## Next Steps

1. **Begin Phase 0.1**: Create requirements.txt (10 min)
2. **Execute Phase 0.2**: Environment validation (20 min)
3. **Parallel Start**: Kick off Tracks A, B, C simultaneously
4. **Monitor Progress**: Track actual vs. estimated times
5. **Adjust Plan**: Update estimates based on actual performance

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-09 | Initial optimized plan with parallel workstreams | Claude + Gemini 2.5 Pro |
| 1.1 | 2025-10-09 | Added detailed task breakdowns and risk analysis | Claude |

---

## Appendix: Comparison with Original Plan

| Metric | Original | Optimized | Delta |
|--------|----------|-----------|-------|
| Total Time | 14-19 hours | 10.5-11.5 hours | -25% to -35% |
| Phase 0 | None | 30 min | +NEW |
| Task A1 | 30 min | 75 min | +150% (realistic) |
| Task A4 | 60 min | 120 min | +100% (realistic) |
| Integration 8 | None | 60 min | +NEW (buffer) |
| Parallelization | Limited | Extensive | +65 min savings |
| Risk Mitigation | Moderate | Comprehensive | +Multiple buffers |
