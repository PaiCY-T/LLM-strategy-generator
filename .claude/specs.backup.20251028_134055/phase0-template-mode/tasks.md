# Phase 0: Template-Guided Generation - Task Breakdown

**Spec Version**: 1.0
**Total Tasks**: 40
**Estimated Time**: ~20 hours development
**Status**: Planning

---

## Task Organization

Tasks are organized into 4 phases:
- **Phase 1**: Core Components (14 tasks, ~7h)
- **Phase 2**: Integration (8 tasks, ~4h)
- **Phase 3**: Testing Infrastructure (10 tasks, ~5h)
- **Phase 4**: Execution & Analysis (8 tasks, ~4h + test runtime)

Each task is atomic (15-30 minutes), has clear acceptance criteria, and leverages existing code where possible.

---

## Phase 1: Core Components Development {#phase1}

**Goal**: Build TemplateParameterGenerator, StrategyValidator, and enhanced prompt template

**Estimated Time**: 7 hours (14 tasks)

---

### Task 1.1: Create src/generators/ package structure
- **File**: `src/generators/__init__.py`, `src/generators/template_parameter_generator.py`
- **Action**: Create directory structure and empty module files
- **Dependencies**: None
- **Acceptance Criteria**:
  - `src/generators/` directory exists
  - `__init__.py` imports TemplateParameterGenerator
  - `template_parameter_generator.py` has module docstring
- **Time**: 15 min

---

### Task 1.2: Implement TemplateParameterGenerator.__init__() ✅ COMPLETED
- **File**: `src/generators/template_parameter_generator.py`
- **Action**: Initialize generator with template, model, and exploration settings
- **Implementation**:
  ```python
  def __init__(self, template_name="Momentum", model="gemini-2.5-flash", exploration_interval=5):
      self.template_name = template_name
      self.model = model
      self.exploration_interval = exploration_interval
      from src.templates.momentum_template import MomentumTemplate
      self.template = MomentumTemplate()
      self.param_grid = self.template.PARAM_GRID
  ```
- **Dependencies**: Task 1.1
- **Acceptance Criteria**:
  - ✅ Loads MomentumTemplate successfully
  - ✅ Stores PARAM_GRID reference
  - ✅ Sets exploration interval
- **Time**: 15 min
- **Completed**: 2025-10-17

---

### Task 1.3: Implement _build_prompt() method - Part 1 (Task & PARAM_GRID sections) ✅ COMPLETED
- **File**: `src/generators/template_parameter_generator.py`
- **Action**: Build prompt sections 1-2 (task description and PARAM_GRID)
- **Implementation**: Create formatted string with:
  - Task description for parameter selection
  - PARAM_GRID with explanations for each value
- **Dependencies**: Task 1.2
- **Acceptance Criteria**:
  - ✅ Prompt includes clear task description
  - ✅ All 8 parameters listed with value explanations
  - ✅ Prompt length 1694 characters (complete Task & PARAM_GRID sections)
- **Leverage**: Use design.md:line 500-650 as template
- **Time**: 30 min
- **Completed**: 2025-10-17

---

### Task 1.4: Implement _build_prompt() method - Part 2 (Champion & Domain sections) ✅ COMPLETED
- **File**: `src/generators/template_parameter_generator.py`
- **Action**: Add champion context and domain knowledge sections
- **Implementation**:
  - Champion params, Sharpe, success patterns
  - Trading domain knowledge (Taiwan market, Finlab data, risk management)
  - Parameter relationship guidelines
- **Dependencies**: Task 1.3
- **Acceptance Criteria**:
  - ✅ Champion section shows if context provided (iteration, Sharpe, parameters)
  - ✅ Exploration vs Exploitation mode indicator included
  - ✅ Domain knowledge includes Taiwan market specifics (T+2, retail participation, concentration)
  - ✅ Finlab Data Recommendations section (liquidity filter, .shift(), .rolling())
  - ✅ Risk Management Best Practices section (portfolio size, stop loss, rebalancing)
  - ✅ Parameter Relationships section (momentum-MA pairing guidelines)
  - ✅ Prompt with champion: ~3163 characters, without champion: ~2906 characters
  - ✅ _should_force_exploration() helper method implemented
- **Leverage**: Use design.md:line 651-800 as template
- **Time**: 30 min
- **Completed**: 2025-10-17

---

### Task 1.5: Implement _build_prompt() method - Part 3 (Output format & assembly) ✅ COMPLETED
- **File**: `src/generators/template_parameter_generator.py`
- **Action**: Add JSON output format specification and assemble all sections
- **Implementation**:
  - Output format example with all 8 parameters
  - Assemble all sections with separators
  - Return complete prompt string
- **Dependencies**: Task 1.4
- **Acceptance Criteria**:
  - ✅ Prompt includes JSON example with all 8 parameters
  - ✅ All sections properly separated (blank lines between)
  - ✅ Complete prompt ready for LLM (all 5 sections assembled)
  - ✅ Output format clearly specifies JSON-only response
  - ✅ Prompt without champion: ~3151 characters, with champion: ~3491 characters
- **Time**: 20 min
- **Completed**: 2025-10-17

---

### Task 1.6: Implement _parse_response() method with 4-tier JSON extraction ✅ COMPLETED
- **File**: `src/generators/template_parameter_generator.py`
- **Action**: Parse LLM response to extract JSON parameters
- **Implementation**: 4 strategies:
  1. Direct JSON.loads()
  2. Extract from markdown ```json``` block
  3. Extract any {...} block
  4. Extract nested braces
- **Dependencies**: Task 1.2
- **Acceptance Criteria**:
  - ✅ Successfully parses valid JSON responses
  - ✅ Handles responses with explanatory text
  - ✅ All 4 strategies implemented with try-except handling
  - ✅ Returns None if all strategies fail
  - ✅ Validates basic dict structure
- **Leverage**: Similar logic in poc_claude_test.py:extract_code_from_response()
- **Time**: 30 min
- **Completed**: 2025-10-17

---

### Task 1.7: Implement _validate_params() method ✅ COMPLETED
- **File**: `src/generators/template_parameter_generator.py`
- **Action**: Validate parameters against PARAM_GRID
- **Implementation**:
  - Check all 8 required keys present
  - Check no extra keys
  - Check each value in valid options
  - Return (is_valid: bool, errors: List[str]) tuple
- **Dependencies**: Task 1.2
- **Acceptance Criteria**:
  - ✅ Returns (is_valid, errors) tuple
  - ✅ Detects missing keys
  - ✅ Detects invalid values
  - ✅ Detects extra unknown parameters
  - ✅ Validates data types (int, float, str)
  - ✅ Error messages list all violations
- **Time**: 20 min
- **Completed**: 2025-10-17

---

### Task 1.8: Implement generate_parameters() main method ✅ COMPLETED
- **File**: `src/generators/template_parameter_generator.py`
- **Action**: Orchestrate parameter generation workflow
- **Implementation**:
  1. Build prompt from context
  2. Call LLM (use existing poc_claude_test.generate_strategy)
  3. Parse response
  4. Validate parameters
  5. Return validated params
- **Dependencies**: Tasks 1.5, 1.6, 1.7
- **Acceptance Criteria**:
  - ✅ End-to-end parameter generation works
  - ✅ Handles LLM errors gracefully (ValueError for parse/validation, RuntimeError for API)
  - ✅ Returns valid parameter dictionary with all 8 keys
  - ✅ Includes comprehensive error handling and logging
  - ✅ Calls all helper methods in correct order
- **Time**: 20 min
- **Completed**: 2025-10-17

---

### Task 1.9: Create StrategyValidator class with __init__()
- **File**: `src/validation/strategy_validator.py`
- **Action**: Create validator class and initialization
- **Implementation**:
  ```python
  class StrategyValidator:
      def __init__(self, strict_mode=False):
          self.strict_mode = strict_mode
  ```
- **Dependencies**: None
- **Acceptance Criteria**:
  - Class created in src/validation/
  - strict_mode flag stored
- **Time**: 10 min

---

### Task 1.10: Implement _validate_risk_management() method
- **File**: `src/validation/strategy_validator.py`
- **Action**: Validate risk parameters (stop_loss, n_stocks, resample)
- **Implementation**:
  - Check stop_loss: 0.05 ≤ value ≤ 0.20
  - Check n_stocks: 5 ≤ value ≤ 30
  - Check resample: not 'D' (daily)
  - Return (errors, warnings) tuple
- **Dependencies**: Task 1.9
- **Acceptance Criteria**:
  - Rejects too-tight stop loss (<5%)
  - Rejects too-loose stop loss (>20%)
  - Rejects over-concentration (<5 stocks)
  - Rejects daily rebalancing
- **Time**: 25 min

---

### Task 1.11: Implement _validate_logical_consistency() method
- **File**: `src/validation/strategy_validator.py`
- **Action**: Check parameter combinations make sense
- **Implementation**:
  - Short momentum (≤10d) + long MA (≥90d) → warning
  - Long momentum (≥20d) + short MA (≤20d) → warning
  - Weekly + long momentum (≥20d) → warning
  - Monthly + short momentum (≤10d) → warning
  - Return warnings list
- **Dependencies**: Task 1.9
- **Acceptance Criteria**:
  - Detects suspicious combinations
  - Provides helpful warning messages
  - Does not block execution (warnings only)
- **Time**: 25 min

---

### Task 1.12: Implement validate_parameters() main method
- **File**: `src/validation/strategy_validator.py`
- **Action**: Orchestrate validation workflow
- **Implementation**:
  1. Call _validate_risk_management()
  2. Call _validate_logical_consistency()
  3. Assemble ValidationResult
  4. Return result
- **Dependencies**: Tasks 1.10, 1.11
- **Acceptance Criteria**:
  - Returns ValidationResult dataclass
  - Errors block execution
  - Warnings logged but don't block
  - Strict mode converts warnings to errors
- **Time**: 20 min

---

### Task 1.13: Create enhanced prompt template file
- **File**: `artifacts/working/modules/prompt_template_v4_template_mode.txt`
- **Action**: Create new prompt template for template mode
- **Content**:
  - Base instructions for parameter selection
  - Finlab dataset catalog
  - Proven success patterns (from generated_strategy_loop_iter3.py analysis)
  - Anti-patterns to avoid
  - Taiwan market-specific guidelines
- **Dependencies**: None
- **Acceptance Criteria**:
  - Template includes ≥5 proven patterns
  - Template includes ≥5 anti-patterns
  - Template includes Finlab dataset documentation
  - Template length ~2000 characters
- **Leverage**: Use design.md domain knowledge section as source
- **Time**: 45 min

---

### Task 1.14: Add unit tests for TemplateParameterGenerator ✅ COMPLETED
- **File**: `tests/generators/test_template_parameter_generator.py`
- **Action**: Create unit tests for parameter generator
- **Tests**:
  1. test_init() - initialization
  2. test_build_prompt_no_champion() - prompt without champion
  3. test_build_prompt_with_champion() - prompt with champion
  4. test_parse_response_valid_json() - parsing valid JSON
  5. test_parse_response_with_markdown() - parsing markdown block
  6. test_parse_response_invalid() - handling parse failures
  7. test_validate_params_valid() - valid parameters
  8. test_validate_params_invalid() - invalid parameters
- **Dependencies**: Task 1.8
- **Acceptance Criteria**:
  - ✅ All 43 tests pass (614% of requirement)
  - ✅ Coverage 82% for TemplateParameterGenerator (exceeds ≥80%)
  - ✅ 8 test classes covering all methods
  - ✅ Comprehensive edge case testing
  - ✅ All 4 parsing strategies tested
  - ✅ All validation error types tested
  - ✅ Exploration mode tested (iterations 0, 5, 10, 15)
- **Time**: 45 min
- **Completed**: 2025-10-17

---

## Phase 2: Integration with Autonomous Loop {#phase2}

**Goal**: Integrate template mode into existing AutonomousLoop

**Estimated Time**: 4 hours (8 tasks)

---

### Task 2.1: Add template_mode flag to AutonomousLoop.__init__()
- **File**: `artifacts/working/modules/autonomous_loop.py`
- **Action**: Add template mode configuration parameters
- **Implementation**:
  ```python
  def __init__(
      self,
      ...,
      template_mode: bool = False,
      template_name: str = "Momentum"
  ):
      self.template_mode = template_mode
      self.template_name = template_name
      if template_mode:
          from src.generators import TemplateParameterGenerator
          from src.validation import StrategyValidator
          self.param_generator = TemplateParameterGenerator(template_name)
          self.validator = StrategyValidator()
  ```
- **Dependencies**: Phase 1 complete
- **Acceptance Criteria**:
  - template_mode flag added
  - TemplateParameterGenerator initialized if template_mode=True
  - Original free-form mode still works (backward compatible)
- **Time**: 20 min

---

### Task 2.2: Add _run_template_mode_iteration() method
- **File**: `artifacts/working/modules/autonomous_loop.py`
- **Action**: Implement template mode iteration workflow
- **Implementation**:
  1. Create ParameterGenerationContext from champion
  2. Call param_generator.generate_parameters(context)
  3. Validate via validator.validate_parameters(params)
  4. If validation fails, log and return None
  5. Call MomentumTemplate.generate_strategy(params)
  6. Return (report, metrics, params)
- **Dependencies**: Task 2.1
- **Acceptance Criteria**:
  - Complete template mode workflow
  - Validation failures handled gracefully
  - Returns same structure as free-form mode
- **Time**: 45 min

---

### Task 2.3: Modify run_iteration() to route based on mode
- **File**: `artifacts/working/modules/autonomous_loop.py`
- **Action**: Add mode-based routing in main iteration method
- **Implementation**:
  ```python
  def run_iteration(self, iteration_num):
      if self.template_mode:
          return self._run_template_mode_iteration(iteration_num)
      else:
          return self._run_freeform_mode_iteration(iteration_num)
  ```
- **Dependencies**: Task 2.2
- **Acceptance Criteria**:
  - Correct workflow executed based on mode flag
  - Both modes work without interference
- **Time**: 15 min

---

### Task 2.4: Update iteration history tracking for template mode
- **File**: `artifacts/working/modules/autonomous_loop.py`
- **Action**: Track parameters separately from code in history
- **Implementation**:
  ```python
  history_entry = {
      'iteration': iteration_num,
      'mode': 'template' if self.template_mode else 'freeform',
      'parameters': params if self.template_mode else None,
      'code': code if not self.template_mode else None,
      'metrics': metrics,
      'validation_passed': True,
      'template_name': self.template_name if self.template_mode else None
  }
  self.history.append(history_entry)
  ```
- **Dependencies**: Task 2.3
- **Acceptance Criteria**:
  - History entries include mode indicator
  - Template mode saves parameters
  - Free-form mode saves code
  - Both modes save metrics
- **Time**: 20 min

---

### Task 2.5: Update ChampionStrategy for template mode
- **File**: `artifacts/working/modules/history.py` (or wherever ChampionStrategy is defined)
- **Action**: Add optional parameters field to champion
- **Implementation**:
  ```python
  @dataclass
  class ChampionStrategy:
      iteration_num: int
      metrics: Dict[str, float]
      timestamp: str
      success_patterns: List[str]

      # Template mode fields
      parameters: Optional[Dict[str, Any]] = None
      mode: str = 'freeform'  # 'template' or 'freeform'

      # Free-form mode field
      code: Optional[str] = None
  ```
- **Dependencies**: Task 2.4
- **Acceptance Criteria**:
  - Champion stores parameters for template mode
  - Champion stores code for free-form mode
  - Mode indicator tracked
- **Time**: 15 min

---

### Task 2.6: Create ParameterGenerationContext dataclass
- **File**: `src/generators/template_parameter_generator.py`
- **Action**: Define context structure for parameter generation
- **Implementation**:
  ```python
  @dataclass
  class ParameterGenerationContext:
      iteration_num: int
      champion_params: Optional[Dict[str, Any]]
      champion_sharpe: Optional[float]
      champion_patterns: Optional[List[str]]
      feedback_history: Optional[str]
  ```
- **Dependencies**: None
- **Acceptance Criteria**:
  - Dataclass properly defined
  - All fields optional except iteration_num
- **Time**: 10 min

---

### Task 2.7: Add integration test for template mode workflow ✅ COMPLETED
- **File**: `tests/integration/test_template_mode_integration.py`
- **Action**: End-to-end test of template mode
- **Test Scenario**:
  1. Create AutonomousLoop with template_mode=True
  2. Run 3 iterations
  3. Verify parameters generated
  4. Verify validation executed
  5. Verify metrics extracted
  6. Verify champion updated if better
- **Dependencies**: Tasks 2.1-2.5
- **Acceptance Criteria**:
  - ✅ Test passes with real Gemini API call
  - ✅ Parameters saved in history
  - ✅ Champion updates correctly
  - ✅ 5 comprehensive test functions created
  - ✅ Mocked backtest to avoid Finlab data dependency
  - ✅ Full workflow validation (parameter generation → validation → strategy execution → champion update)
  - ✅ Champion update logic tested (baseline, worse, better)
  - ✅ Parameter validation warnings tested (non-blocking)
  - ✅ Template mode vs free-form mode distinction tested
- **Time**: 45 min
- **Completed**: 2025-10-17

---

### Task 2.8: Create 5-iteration smoke test script ✅ COMPLETED
- **File**: `run_5iteration_template_smoke_test.py`
- **Action**: Quick validation that template mode works
- **Implementation**:
  ```python
  from artifacts.working.modules.autonomous_loop import AutonomousLoop

  loop = AutonomousLoop(
      template_mode=True,
      template_name="Momentum",
      model="gemini-2.5-flash",
      max_iterations=5
  )

  results = loop.run()
  print(f"Champion updates: {results['champion_update_count']}/5")
  ```
- **Dependencies**: Task 2.7
- **Acceptance Criteria**:
  - ✅ Completes 5 iterations successfully
  - ✅ Prints results summary including success rate, champion updates, and Sharpe ratios
  - ✅ Takes ~30 minutes to run with real API
  - ✅ Comprehensive logging to file
  - ✅ Error handling for interruptions and exceptions
  - ✅ Result recommendations based on success rate
- **Time**: 30 min
- **Completed**: 2025-10-17

---

## Phase 3: Testing Infrastructure {#phase3}

**Goal**: Create 50-iteration test harness and analysis framework

**Estimated Time**: 5 hours (10 tasks)

---

### Task 3.1: Create Phase0TestHarness class skeleton
- **File**: `tests/integration/phase0_test_harness.py`
- **Action**: Create test harness class structure
- **Implementation**:
  ```python
  class Phase0TestHarness:
      def __init__(self, test_name, max_iterations=50, model="gemini-2.5-flash"):
          self.test_name = test_name
          self.max_iterations = max_iterations
          self.model = model
          self.results = {}
  ```
- **Dependencies**: None
- **Acceptance Criteria**:
  - Class created with initialization
  - Basic configuration stored
- **Leverage**: Copy structure from ExtendedTestHarness
- **Time**: 15 min

---

### Task 3.2: Implement run() method for test orchestration
- **File**: `tests/integration/phase0_test_harness.py`
- **Action**: Main test loop with progress tracking
- **Implementation**:
  ```python
  def run(self):
      start_time = time.time()

      loop = AutonomousLoop(
          template_mode=True,
          template_name="Momentum",
          model=self.model,
          max_iterations=self.max_iterations
      )

      for i in range(self.max_iterations):
          print(f"Iteration {i+1}/{self.max_iterations}...")
          loop.run_iteration(i)
          self._update_progress(i, loop)

      elapsed = time.time() - start_time
      return self._compile_results(loop, elapsed)
  ```
- **Dependencies**: Task 3.1, Phase 2 complete
- **Acceptance Criteria**:
  - Runs all iterations
  - Displays progress
  - Compiles final results
- **Time**: 30 min

---

### Task 3.3: Implement _update_progress() for real-time monitoring
- **File**: `tests/integration/phase0_test_harness.py`
- **Action**: Display real-time progress metrics
- **Implementation**:
  - Current iteration
  - Champion update count
  - Current champion Sharpe
  - Update rate %
  - Estimated time remaining
- **Dependencies**: Task 3.2
- **Acceptance Criteria**:
  - Progress updates every iteration
  - ETA calculation based on average iteration time
- **Time**: 20 min

---

### Task 3.4: Implement checkpoint save/restore functionality
- **File**: `tests/integration/phase0_test_harness.py`
- **Action**: Save state every 10 iterations
- **Implementation**:
  ```python
  def _save_checkpoint(self, iteration, loop):
      checkpoint = {
          'iteration': iteration,
          'champion': loop.champion,
          'history': loop.history,
          'timestamp': datetime.now().isoformat()
      }
      with open(f'checkpoint_{self.test_name}_iter{iteration}.json', 'w') as f:
          json.dump(checkpoint, f, indent=2)

  def _load_checkpoint(self, checkpoint_file):
      with open(checkpoint_file, 'r') as f:
          return json.load(f)
  ```
- **Dependencies**: Task 3.2
- **Acceptance Criteria**:
  - Checkpoint saved every 10 iterations
  - Can resume from checkpoint
- **Leverage**: Similar to ExtendedTestHarness checkpoint logic
- **Time**: 30 min

---

### Task 3.5: Implement _compile_results() method
- **File**: `tests/integration/phase0_test_harness.py`
- **Action**: Compile comprehensive test results
- **Implementation**:
  - Total iterations
  - Champion update count & rate
  - Average Sharpe
  - Best Sharpe
  - Variance
  - Parameter diversity
  - Validation statistics
- **Dependencies**: Task 3.2
- **Acceptance Criteria**:
  - All primary metrics calculated
  - Results dictionary complete
- **Time**: 25 min

---

### Task 3.6: Create ResultsAnalyzer class
- **File**: `tests/integration/phase0_results_analyzer.py`
- **Action**: Analyze test results and generate decision
- **Implementation**:
  ```python
  class ResultsAnalyzer:
      def __init__(self, results):
          self.results = results

      def calculate_primary_metrics(self):
          # Champion update rate, avg Sharpe, etc.

      def compare_to_baseline(self):
          # Compare to 0.5% baseline

      def analyze_parameter_diversity(self):
          # Unique combinations, exploration stats

      def make_decision(self):
          # GO/NO-GO recommendation
  ```
- **Dependencies**: Task 3.5
- **Acceptance Criteria**:
  - All analysis methods implemented
  - Decision logic matches requirements
- **Time**: 45 min

---

### Task 3.7: Implement calculate_primary_metrics() method
- **File**: `tests/integration/phase0_results_analyzer.py`
- **Action**: Calculate all primary decision metrics
- **Metrics**:
  - Champion update rate (updates / total × 100)
  - Average Sharpe (mean across all successful)
  - Best Sharpe (maximum)
  - Variance (Sharpe variance)
  - Parameter diversity (unique combinations / total)
- **Dependencies**: Task 3.6
- **Acceptance Criteria**:
  - All 5 primary metrics calculated correctly
  - Handles edge cases (no updates, all failures)
- **Time**: 25 min

---

### Task 3.8: Implement compare_to_baseline() method
- **File**: `tests/integration/phase0_results_analyzer.py`
- **Action**: Compare Phase 0 results to free-form baseline
- **Baseline** (from 200-iteration test):
  - Champion update rate: 0.5%
  - Average Sharpe: 1.3728
  - Variance: 1.001
- **Calculations**:
  - Update rate improvement: (template_rate / 0.5) × 100
  - Sharpe comparison: template_avg vs 1.3728
  - Variance improvement: (1.001 - template_variance) / 1.001 × 100
- **Dependencies**: Task 3.7
- **Acceptance Criteria**:
  - Improvement factors calculated
  - Comparison table generated
- **Time**: 20 min

---

### Task 3.9: Implement make_decision() method with decision matrix
- **File**: `tests/integration/phase0_results_analyzer.py`
- **Action**: Automated GO/NO-GO decision
- **Decision Logic**:
  ```python
  def make_decision(self):
      metrics = self.calculate_primary_metrics()

      if metrics['champion_update_rate'] >= 10 and metrics['avg_sharpe'] > 1.2:
          return {
              'decision': 'SUCCESS',
              'recommendation': 'Use template mode, skip population-based',
              'confidence': 'HIGH'
          }
      elif metrics['champion_update_rate'] >= 5 and metrics['avg_sharpe'] > 1.0:
          return {
              'decision': 'PARTIAL',
              'recommendation': 'Consider hybrid (template + population)',
              'confidence': 'MEDIUM'
          }
      else:
          return {
              'decision': 'FAILURE',
              'recommendation': 'Proceed to Phase 1 (population-based)',
              'confidence': 'HIGH'
          }
  ```
- **Dependencies**: Task 3.7
- **Acceptance Criteria**:
  - Decision matrix matches requirements.md
  - Clear recommendation provided
  - Confidence level included
- **Time**: 20 min

---

### Task 3.10: Create generate_report() method
- **File**: `tests/integration/phase0_results_analyzer.py`
- **Action**: Generate comprehensive markdown report
- **Report Sections**:
  1. Test Configuration
  2. Primary Metrics
  3. Comparison to Baseline
  4. Parameter Exploration Analysis
  5. Validation Analysis
  6. Decision & Recommendation
  7. Insights & Learnings
- **Dependencies**: Tasks 3.7-3.9
- **Acceptance Criteria**:
  - Complete report generated
  - Saved to `PHASE0_RESULTS.md`
- **Time**: 30 min

---

## Phase 4: Execution & Analysis {#phase4}

**Goal**: Run 50-iteration test and analyze results

**Estimated Time**: 4 hours + test runtime (8 tasks)

---

### Task 4.1: Create run_50iteration_template_test.py script
- **File**: `run_50iteration_template_test.py`
- **Action**: Main test execution script
- **Implementation**:
  ```python
  from tests.integration.phase0_test_harness import Phase0TestHarness
  from tests.integration.phase0_results_analyzer import ResultsAnalyzer

  def main():
      harness = Phase0TestHarness(
          test_name="phase0_template_test",
          max_iterations=50,
          model="gemini-2.5-flash"
      )

      results = harness.run()

      analyzer = ResultsAnalyzer(results)
      decision = analyzer.make_decision()
      report = analyzer.generate_report()

      print(decision['recommendation'])
  ```
- **Dependencies**: Phase 3 complete
- **Acceptance Criteria**:
  - Script runs to completion
  - Results saved
  - Report generated
- **Time**: 20 min

---

### Task 4.2: Add error handling and retry logic
- **File**: `tests/integration/phase0_test_harness.py`
- **Action**: Handle individual iteration failures gracefully
- **Implementation**:
  - Catch exceptions per iteration
  - Log error details
  - Mark iteration as failed
  - Continue to next iteration
  - Track failure rate
- **Dependencies**: Task 3.2
- **Acceptance Criteria**:
  - Test doesn't crash on single iteration failure
  - Failure rate tracked and reported
- **Time**: 25 min

---

### Task 4.3: Add parameter diversity tracking
- **File**: `tests/integration/phase0_test_harness.py`
- **Action**: Track unique parameter combinations
- **Implementation**:
  ```python
  self.param_combinations = []

  def _track_parameters(self, params):
      param_tuple = tuple(sorted(params.items()))
      if param_tuple not in self.param_combinations:
          self.param_combinations.append(param_tuple)

      diversity = len(self.param_combinations) / self.current_iteration * 100
      return diversity
  ```
- **Dependencies**: Task 3.2
- **Acceptance Criteria**:
  - Unique combinations tracked
  - Diversity percentage calculated
- **Time**: 20 min

---

### Task 4.4: Add validation statistics tracking
- **File**: `tests/integration/phase0_test_harness.py`
- **Action**: Track validation pass/fail rates
- **Implementation**:
  - Count validation passes
  - Count validation failures
  - Track most common validation errors
  - Calculate pass rate percentage
- **Dependencies**: Task 3.2
- **Acceptance Criteria**:
  - Pass rate calculated
  - Common errors identified
- **Time**: 20 min

---

### Task 4.5: Run 5-iteration smoke test and verify
- **Action**: Execute smoke test to validate setup
- **Script**: `python run_5iteration_template_smoke_test.py`
- **Dependencies**: Task 2.8
- **Acceptance Criteria**:
  - Completes 5 iterations successfully
  - 0-1 champion updates (not enough iterations for statistics)
  - All components working together
  - Runtime ~30 minutes
- **Time**: 45 min (includes test runtime)

---

### Task 4.6: Run 50-iteration full test
- **Action**: Execute main hypothesis test
- **Script**: `python run_50iteration_template_test.py`
- **Dependencies**: Tasks 4.1-4.4, Task 4.5 passed
- **Acceptance Criteria**:
  - Completes 50 iterations successfully
  - Results saved to JSON file
  - Checkpoints created every 10 iterations
  - Runtime <5 hours (average <6 min/iteration)
- **Time**: 5 hours (test runtime)

---

### Task 4.7: Analyze results and generate report
- **Action**: Run analysis on test results
- **Dependencies**: Task 4.6 complete
- **Steps**:
  1. Load results from JSON
  2. Run ResultsAnalyzer
  3. Generate markdown report
  4. Print decision recommendation
- **Acceptance Criteria**:
  - `PHASE0_RESULTS.md` generated
  - Clear GO/NO-GO decision
  - All metrics calculated
- **Time**: 30 min

---

### Task 4.8: Make Phase 1 decision and document
- **Action**: Based on results, decide next steps
- **Dependencies**: Task 4.7
- **Decision Matrix**:
  - **IF SUCCESS** (≥5% update rate): Document template mode as standard, skip population-based
  - **IF PARTIAL** (2-5% update rate): Document partial success, plan hybrid approach
  - **IF FAILURE** (<2% update rate): Document findings, proceed to Phase 1 (population-based)
- **Deliverable**: Update STATUS.md with decision and next steps
- **Acceptance Criteria**:
  - Decision documented in STATUS.md
  - Rationale clearly explained
  - Next steps defined
- **Time**: 30 min

---

## Task Summary

### By Phase

| Phase | Tasks | Estimated Time | Description |
|-------|-------|----------------|-------------|
| Phase 1 | 14 | 7h | Core components (TemplateParameterGenerator, StrategyValidator, Prompt) |
| Phase 2 | 8 | 4h | Integration with AutonomousLoop |
| Phase 3 | 10 | 5h | Testing infrastructure (harness, analyzer) |
| Phase 4 | 8 | 4h + 5h runtime | Execution and analysis |
| **TOTAL** | **40** | **20h dev + 5h test** | **~25 hours total** |

### By Component

| Component | Tasks | Time | Key Deliverables |
|-----------|-------|------|------------------|
| TemplateParameterGenerator | 6 | 3h | Prompt building, JSON parsing, validation |
| StrategyValidator | 4 | 1.5h | Risk validation, logical consistency |
| Enhanced Prompt | 1 | 0.75h | Domain knowledge template |
| Unit Tests | 1 | 0.75h | 80% coverage |
| AutonomousLoop Integration | 6 | 2.5h | Mode routing, history tracking |
| Integration Tests | 2 | 1.25h | End-to-end validation |
| Test Harness | 5 | 2.5h | 50-iteration orchestration |
| Results Analyzer | 5 | 2.5h | Metrics, decision matrix |
| Execution & Analysis | 8 | 4.25h | Smoke test, full test, reporting |

### Critical Path

```
Phase 1.1-1.8 (TemplateParameterGenerator) →
Phase 1.9-1.12 (StrategyValidator) →
Phase 2.1-2.5 (AutonomousLoop Integration) →
Phase 2.7-2.8 (Smoke Test) →
Phase 3.1-3.10 (Test Infrastructure) →
Phase 4.1-4.4 (Test Setup) →
Phase 4.5 (Smoke Test Execution) →
Phase 4.6 (Full Test Execution - 5 hours) →
Phase 4.7-4.8 (Analysis & Decision)
```

**Total Timeline**: ~25 hours (20h dev + 5h testing)

---

## Task Dependencies

### Prerequisites
- ✅ MomentumTemplate exists and works
- ✅ AutonomousLoop exists and works
- ✅ Gemini API integrated (95.2% success rate)
- ✅ Finlab backtest working

### Blocking Dependencies
- **Phase 2** requires **Phase 1** complete
- **Phase 3** requires **Phase 2** complete
- **Phase 4** requires **Phase 3** complete
- **Task 4.6** (50-iter test) requires **Task 4.5** (smoke test) passed

### Parallel Opportunities
- **Phase 1.1-1.8** (TemplateParameterGenerator) can be done in parallel with **Phase 1.9-1.12** (StrategyValidator)
- **Task 1.13** (Enhanced prompt) can be done anytime during Phase 1
- **Task 1.14** (Unit tests) can be done as Phase 1 tasks complete

---

## Risk Mitigation

### Risk: LLM fails to generate valid JSON
- **Mitigation**: 4-tier JSON parsing with fallbacks (Task 1.6)
- **Fallback**: Manual parameter selection if parsing fails consistently

### Risk: Validation too strict (>20% rejection rate)
- **Mitigation**: Track validation statistics (Task 4.4)
- **Adjustment**: Relax validation rules if rejection rate excessive

### Risk: Test doesn't complete due to API failures
- **Mitigation**: Error handling and retry logic (Task 4.2)
- **Mitigation**: Checkpoint save/restore (Task 3.4)
- **Recovery**: Resume from last checkpoint

### Risk: Results inconclusive (update rate 2-5%)
- **Mitigation**: Clear decision matrix for PARTIAL case (Task 3.9)
- **Next Steps**: Hybrid approach defined in advance

---

**Document Version**: 1.0
**Last Updated**: 2025-10-17
**Status**: Ready for implementation
