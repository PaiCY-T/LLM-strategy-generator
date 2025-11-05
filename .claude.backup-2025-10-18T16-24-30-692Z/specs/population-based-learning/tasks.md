# Implementation Plan: Population-based Learning System

## Task Overview

本實作計畫將 population-based evolutionary learning system 分解為 40+ 個原子化任務，每個任務聚焦於單一組件或功能，可在 15-30 分鐘內完成。

**實作策略**：
1. **由下而上**：先實作基礎工具（diversity metrics、multi-objective），再實作演化組件
2. **測試驅動**：每個組件實作完立即編寫單元測試
3. **整合優先**：早期整合 `autonomous_loop.py`，確保相容性
4. **增量驗證**：每 5 個任務完成後執行部分整合測試

---

## Steering Document Compliance

**遵循 structure.md 的專案結構**：
- 新增 `src/evolution/` 目錄存放所有演化相關程式碼
- 新增 `tests/evolution/` 目錄存放對應測試
- 重用 `src/backtest/metrics.py` 計算 Calmar ratio、Max Drawdown
- 整合現有 `autonomous_loop.py`，最小化變更

**遵循 tech.md 的技術標準**：
- Type hints 覆蓋率 100%
- 錯誤處理使用 try-except + logging
- 所有 LLM API 調用使用 exponential backoff
- 程式碼驗證重用 `validate_code.py`

---

## Atomic Task Requirements

**每個任務必須滿足**：
- ✅ **File Scope**: 涉及 1-3 個相關文件
- ✅ **Time Boxing**: 可在 15-30 分鐘內完成
- ✅ **Single Purpose**: 一個可測試的結果
- ✅ **Specific Files**: 指定確切的文件路徑
- ✅ **Agent-Friendly**: 清晰的輸入/輸出，最少的上下文切換

---

## Tasks

### Phase 1: Data Models & Foundation (Tasks 1-8)

- [ ] 1. Create evolution package structure
  - Files: `src/evolution/__init__.py`
  - Create empty `__init__.py` to establish package
  - Add module docstring explaining package purpose
  - Purpose: Establish foundation for evolution components
  - _Requirements: R8.1 (Integration)_

- [ ] 2. Define MultiObjectiveMetrics dataclass in src/evolution/types.py
  - File: `src/evolution/types.py`
  - Define `MultiObjectiveMetrics` with 7 fields (sharpe, calmar, max_drawdown, etc.)
  - Implement `dominates()` method for Pareto dominance check
  - Add type hints and docstrings
  - Purpose: Establish multi-objective fitness representation
  - _Leverage: Python dataclasses_
  - _Requirements: R6.1_

- [ ] 3. Define Strategy dataclass in src/evolution/types.py
  - File: `src/evolution/types.py` (continue from task 2)
  - Define `Strategy` dataclass with 12 fields (id, generation, parent_ids, etc.)
  - Implement `to_dict()` and `from_dict()` for JSON serialization
  - Add `dominates()` method delegating to metrics
  - Purpose: Core data structure for individual strategies
  - _Leverage: Python dataclasses, UUID_
  - _Requirements: R1.3_

- [ ] 4. Define Population dataclass in src/evolution/types.py
  - File: `src/evolution/types.py` (continue from task 3)
  - Define `Population` dataclass with 5 fields (generation, strategies, pareto_front, etc.)
  - Implement properties: `size`, `best_sharpe`, `avg_sharpe`
  - Add `to_dict()` for serialization
  - Purpose: Represent entire population state
  - _Leverage: Python dataclasses_
  - _Requirements: R1.2_

- [ ] 5. Define EvolutionResult dataclass in src/evolution/types.py
  - File: `src/evolution/types.py` (continue from task 4)
  - Define `EvolutionResult` with 13 fields (generation, population, timing metrics, etc.)
  - Implement `summary()` method for human-readable output
  - Purpose: Track evolution generation results
  - _Requirements: R11.2 (Logging)_

- [ ] 6. Create unit tests for data models in tests/evolution/test_types.py
  - File: `tests/evolution/test_types.py`
  - Test `MultiObjectiveMetrics.dominates()` with 3 scenarios
  - Test `Strategy` serialization/deserialization
  - Test `Population` property calculations
  - Purpose: Ensure data model correctness
  - _Leverage: pytest, tests/helpers/testUtils.ts_
  - _Requirements: R1.3, R6.1_

- [ ] 7. Add Calmar ratio calculation to src/backtest/metrics.py
  - File: `src/backtest/metrics.py` (modify existing)
  - Add `calculate_calmar_ratio(total_return, max_drawdown)` function
  - Handle edge case: max_drawdown = 0
  - Add docstring with formula explanation
  - Purpose: Support multi-objective optimization
  - _Leverage: existing Sharpe ratio calculation_
  - _Requirements: R6.1_

- [ ] 8. Add Max Drawdown calculation to src/backtest/metrics.py
  - File: `src/backtest/metrics.py` (continue from task 7)
  - Add `calculate_max_drawdown(equity_curve)` function
  - Return negative value (e.g., -0.25 for 25% drawdown)
  - Add unit test in `tests/backtest/test_metrics.py`
  - Purpose: Complete multi-objective metrics
  - _Leverage: NumPy for cumulative max_
  - _Requirements: R6.1_

---

### Phase 2: Multi-objective Optimization (Tasks 9-15)

- [ ] 9. Create multi_objective.py with pareto_dominates function
  - File: `src/evolution/multi_objective.py`
  - Implement `pareto_dominates(metrics_a, metrics_b)` function
  - Handle maximize objectives (sharpe, calmar) and minimize (max_drawdown)
  - Add comprehensive docstring with example
  - Purpose: Core Pareto dominance logic
  - _Leverage: src/evolution/types.MultiObjectiveMetrics_
  - _Requirements: R6.2_

- [ ] 10. Add calculate_pareto_front function to multi_objective.py
  - File: `src/evolution/multi_objective.py` (continue from task 9)
  - Implement `calculate_pareto_front(population)` using brute-force comparison
  - Return list of non-dominated strategies
  - Time complexity: O(n²) acceptable for n=20-50
  - Purpose: Identify Pareto optimal strategies
  - _Leverage: pareto_dominates()_
  - _Requirements: R6.2_

- [ ] 11. Add assign_pareto_ranks function to multi_objective.py
  - File: `src/evolution/multi_objective.py` (continue from task 10)
  - Implement fast non-dominated sorting (NSGA-II algorithm)
  - Return dict mapping strategy_id to Pareto rank (1, 2, 3, ...)
  - Add detailed comments explaining algorithm steps
  - Purpose: Rank strategies by dominance
  - _Leverage: calculate_pareto_front()_
  - _Requirements: R2.2_

- [ ] 12. Add calculate_crowding_distance function to multi_objective.py
  - File: `src/evolution/multi_objective.py` (continue from task 11)
  - Implement NSGA-II crowding distance for diversity
  - Calculate distance for each objective, sum across objectives
  - Assign infinite distance to boundary solutions
  - Purpose: Maintain diversity along Pareto front
  - _Requirements: R7.1_

- [ ] 13. Create unit tests for multi_objective.py
  - File: `tests/evolution/test_multi_objective.py`
  - Test `pareto_dominates()` with 5 scenarios (dominates, dominated, non-dominated, equal, single-objective)
  - Test `calculate_pareto_front()` with known population
  - Test `assign_pareto_ranks()` correctness
  - Test `calculate_crowding_distance()` boundary cases
  - Purpose: Ensure Pareto logic correctness
  - _Leverage: pytest_
  - _Requirements: R6.2_

- [ ] 14. Add visualization helper in src/evolution/visualization.py
  - File: `src/evolution/visualization.py`
  - Create `plot_pareto_front(population, save_path)` function
  - 2D scatter plot: Sharpe (x) vs Calmar (y)
  - Highlight Pareto front in red, others in blue
  - Purpose: Visualize multi-objective trade-offs
  - _Leverage: Matplotlib_
  - _Requirements: R6.3_

- [ ] 15. Add diversity plot to visualization.py
  - File: `src/evolution/visualization.py` (continue from task 14)
  - Create `plot_diversity_over_time(results, save_path)` function
  - Line plot: Generation (x) vs Diversity score (y)
  - Add threshold line at 0.3
  - Purpose: Monitor diversity collapse
  - _Leverage: Matplotlib_
  - _Requirements: R7.3, R11.1_

---

### Phase 3: Diversity Metrics (Tasks 16-21)

- [ ] 16. Create diversity.py with extract_feature_set function
  - File: `src/evolution/diversity.py`
  - Implement `extract_feature_set(code: str) -> Set[str]`
  - Use regex to find: data.get('feature_name'), data.indicator('indicator_name')
  - Return set of unique feature names (e.g., {'roe', 'momentum', 'liquidity'})
  - Purpose: Extract features for Jaccard distance
  - _Leverage: Python re module_
  - _Requirements: R7.1_

- [ ] 17. Add calculate_jaccard_distance to diversity.py
  - File: `src/evolution/diversity.py` (continue from task 16)
  - Implement `calculate_jaccard_distance(strategy1, strategy2) -> float`
  - Formula: 1 - (intersection / union)
  - Return 0.0 for identical, 1.0 for completely different
  - Purpose: Measure strategy similarity
  - _Leverage: extract_feature_set()_
  - _Requirements: R7.1_

- [ ] 18. Add calculate_population_diversity to diversity.py
  - File: `src/evolution/diversity.py` (continue from task 17)
  - Implement `calculate_population_diversity(population) -> float`
  - Calculate average pairwise Jaccard distance
  - Return value in [0, 1] range
  - Purpose: Aggregate diversity metric
  - _Leverage: calculate_jaccard_distance()_
  - _Requirements: R7.1_

- [ ] 19. Add adaptive mutation rate logic to diversity.py
  - File: `src/evolution/diversity.py` (continue from task 18)
  - Implement `should_increase_mutation_rate(diversity_score, threshold=0.3) -> bool`
  - Return True if diversity < threshold
  - Add logging when triggered
  - Purpose: Detect diversity collapse
  - _Leverage: logging module_
  - _Requirements: R7.2_

- [ ] 20. Create unit tests for diversity.py
  - File: `tests/evolution/test_diversity.py`
  - Test `extract_feature_set()` with various code samples
  - Test `calculate_jaccard_distance()` with identical/different strategies
  - Test `calculate_population_diversity()` with known population
  - Test `should_increase_mutation_rate()` threshold logic
  - Purpose: Ensure diversity metrics correctness
  - _Leverage: pytest_
  - _Requirements: R7.1_

- [ ] 21. Add novelty score calculation to diversity.py
  - File: `src/evolution/diversity.py` (continue from task 19)
  - Implement `calculate_novelty_score(strategy, population, k=5) -> float`
  - Find k-nearest neighbors by Jaccard distance
  - Return average distance to neighbors
  - Purpose: Measure individual novelty
  - _Leverage: calculate_jaccard_distance()_
  - _Requirements: R7.1_

---

### Phase 4: Selection Mechanism (Tasks 22-27)

- [ ] 22. Create selection.py with SelectionManager class
  - File: `src/evolution/selection.py`
  - Define `SelectionManager` class with `__init__` method
  - Store population, tournament_size, selection_pressure as instance variables
  - Add docstring explaining purpose
  - Purpose: Foundation for selection logic
  - _Requirements: R2.1_

- [ ] 23. Implement tournament_selection method
  - File: `src/evolution/selection.py` (continue from task 22)
  - Add `tournament_selection(population, tournament_size=3, selection_pressure=0.8)` method
  - Random sample tournament_size strategies
  - Sort by Pareto rank, then crowding distance
  - Stochastic selection (80% best, 20% random)
  - Purpose: Core parent selection logic
  - _Leverage: random module, src/evolution/multi_objective.py_
  - _Requirements: R2.1_

- [ ] 24. Implement select_parents method
  - File: `src/evolution/selection.py` (continue from task 23)
  - Add `select_parents(population, count) -> List[Tuple[Strategy, Strategy]]`
  - Call `tournament_selection()` twice per pair
  - Ensure unique parents in each pair (no self-pairing)
  - Return list of parent pairs
  - Purpose: Batch parent selection
  - _Leverage: tournament_selection()_
  - _Requirements: R2.1_

- [ ] 25. Add diversity-aware selection probability
  - File: `src/evolution/selection.py` (continue from task 24)
  - Add `calculate_selection_probability(strategy, population)` method
  - Combine fitness (Pareto rank) and novelty (Jaccard distance)
  - Formula: prob ∝ (1/pareto_rank) * (1 + novelty_score)
  - Purpose: Balance fitness and diversity
  - _Leverage: src/evolution/diversity.calculate_novelty_score_
  - _Requirements: R2.3_

- [ ] 26. Create unit tests for selection.py
  - File: `tests/evolution/test_selection.py`
  - Test `tournament_selection()` returns valid strategy
  - Test selection pressure affects outcome (mock random)
  - Test Pareto rank influences selection (non-dominated favored)
  - Test crowding distance breaks ties
  - Test `select_parents()` returns unique pairs
  - Purpose: Ensure selection correctness
  - _Leverage: pytest, unittest.mock_
  - _Requirements: R2.1_

- [ ] 27. Add elitism preservation to selection.py
  - File: `src/evolution/selection.py` (continue from task 25)
  - Add `get_elite_strategies(population, elite_count=2)` method
  - Sort by Sharpe ratio (primary), Calmar ratio (secondary)
  - Return top elite_count strategies
  - Purpose: Identify strategies to preserve
  - _Requirements: R5.1_

---

### Phase 5: Crossover Mechanism (Tasks 28-34)

- [ ] 28. Create crossover.py with CrossoverManager class
  - File: `src/evolution/crossover.py`
  - Define `CrossoverManager` class with `__init__` accepting `prompt_builder`, `code_validator`
  - Store dependencies as instance variables
  - Add docstring
  - Purpose: Foundation for crossover logic
  - _Requirements: R3.1_

- [ ] 29. Implement parameter_crossover function
  - File: `src/evolution/crossover.py` (continue from task 28)
  - Add `parameter_crossover(params1, params2) -> Dict[str, Any]` method
  - Uniform crossover: 50/50 probability per parameter
  - Handle missing keys (use None if key not in both)
  - Purpose: Parameter-level breeding
  - _Leverage: random module_
  - _Requirements: R3.1_

- [ ] 30. Add factor weight renormalization to parameter_crossover
  - File: `src/evolution/crossover.py` (continue from task 29)
  - Detect 'factor_weights' parameter
  - Renormalize to sum=1.0 after crossover
  - Handle edge case: all weights zero (fallback to equal weights)
  - Purpose: Maintain weight constraint
  - _Requirements: R3.1_

- [ ] 31. Implement generate_offspring_code method
  - File: `src/evolution/crossover.py` (continue from task 30)
  - Add `generate_offspring_code(parent1, parent2, crossover_params)` method
  - Build crossover prompt via `prompt_builder.build_crossover_prompt()`
  - Call LLM API to generate code
  - Validate code via `code_validator.validate()`
  - Purpose: Generate offspring code from parameters
  - _Leverage: src/prompt_builder.py, src/validate_code.py_
  - _Requirements: R3.2_

- [ ] 32. Add crossover method with retry logic
  - File: `src/evolution/crossover.py` (continue from task 31)
  - Add `crossover(parent1, parent2, crossover_rate=0.7, max_retries=3)` method
  - Try `generate_offspring_code()` up to max_retries times
  - Fallback to single-parent mutation if all retries fail
  - Log crossover failures
  - Purpose: Robust offspring generation
  - _Leverage: logging, generate_offspring_code()_
  - _Requirements: R3.2_

- [ ] 33. Create unit tests for crossover.py
  - File: `tests/evolution/test_crossover.py`
  - Test `parameter_crossover()` uniform distribution (statistical test with 100 samples)
  - Test factor weights renormalized (sum=1.0)
  - Test crossover generates valid code (mock LLM API)
  - Test crossover fallback on invalid code
  - Test crossover preserves parent features (Jaccard distance check)
  - Purpose: Ensure crossover correctness
  - _Leverage: pytest, unittest.mock_
  - _Requirements: R3.1, R3.2_

- [ ] 34. Add crossover compatibility rules
  - File: `src/evolution/crossover.py` (continue from task 32)
  - Add `check_compatibility(parent1, parent2) -> bool` method
  - Verify factor types match (both use momentum, or both use value, etc.)
  - Return False if incompatible, log warning
  - Purpose: Prevent invalid crossover combinations
  - _Requirements: R3.3_

---

### Phase 6: Mutation Mechanism (Tasks 35-40)

- [ ] 35. Create mutation.py with MutationManager class
  - File: `src/evolution/mutation.py`
  - Define `MutationManager` class with `__init__` accepting `code_validator`
  - Store mutation_rate, mutation_strength as instance variables (default 0.1, 0.1)
  - Add docstring
  - Purpose: Foundation for mutation logic
  - _Requirements: R4.1_

- [ ] 36. Implement gaussian_mutation function
  - File: `src/evolution/mutation.py` (continue from task 35)
  - Add `gaussian_mutation(value, sigma, bounds) -> float` function
  - Sample noise from N(0, sigma)
  - Apply relative mutation: mutated = value + noise * value
  - Clip to bounds
  - Purpose: Numeric parameter mutation
  - _Leverage: NumPy for Gaussian sampling_
  - _Requirements: R4.1_

- [ ] 37. Implement mutate_parameters method
  - File: `src/evolution/mutation.py` (continue from task 36)
  - Add `mutate_parameters(params, mutation_rate) -> Dict[str, Any]` method
  - For each parameter: mutate with probability mutation_rate
  - Handle int (±10% or ±1) and float (Gaussian) separately
  - Preserve parameter types
  - Purpose: Parameter-level mutation
  - _Leverage: gaussian_mutation()_
  - _Requirements: R4.1_

- [ ] 38. Add factor weight renormalization to mutation
  - File: `src/evolution/mutation.py` (continue from task 37)
  - Detect 'factor_weights' in mutated_params
  - Renormalize weights to sum=1.0
  - Handle all-zero edge case
  - Purpose: Maintain weight constraint after mutation
  - _Requirements: R4.2_

- [ ] 39. Implement mutate method with code regeneration
  - File: `src/evolution/mutation.py` (continue from task 38)
  - Add `mutate(strategy, mutation_rate=0.1, mutation_strength=0.1, max_retries=3)` method
  - Mutate parameters via `mutate_parameters()`
  - Regenerate code via LLM API with mutated parameters
  - Validate code, retry up to max_retries
  - Purpose: Complete mutation workflow
  - _Leverage: code_validator, prompt_builder_
  - _Requirements: R4.3_

- [ ] 40. Create unit tests for mutation.py
  - File: `tests/evolution/test_mutation.py`
  - Test `gaussian_mutation()` within bounds (100 samples)
  - Test mutation rate controls frequency (statistical test)
  - Test mutation strength controls magnitude
  - Test mutated weights sum to 1.0
  - Test mutation retries on invalid code
  - Purpose: Ensure mutation correctness
  - _Leverage: pytest, NumPy for statistical tests_
  - _Requirements: R4.1, R4.2, R4.3_

---

### Phase 7: Population Manager (Tasks 41-48)

- [ ] 41. Create population_manager.py with PopulationManager class
  - File: `src/evolution/population_manager.py`
  - Define `PopulationManager` class with `__init__` accepting autonomous_loop
  - Initialize population_size=20, elite_count=2, tournament_size=3
  - Create instances of SelectionManager, CrossoverManager, MutationManager
  - Purpose: Central evolution coordinator
  - _Leverage: src/evolution/selection.py, crossover.py, mutation.py_
  - _Requirements: R1.1, R8.1_

- [ ] 42. Implement initialize_population method
  - File: `src/evolution/population_manager.py` (continue from task 41)
  - Add `initialize_population() -> List[Strategy]` method
  - Generate population_size diverse strategies using different templates
  - Evaluate each via `autonomous_loop.run_iteration()`
  - Extract features, calculate novelty scores
  - Purpose: Create initial diverse population
  - _Leverage: autonomous_loop, diversity.extract_feature_set_
  - _Requirements: R1.1_

- [ ] 43. Implement evaluate_population method
  - File: `src/evolution/population_manager.py` (continue from task 42)
  - Add `evaluate_population(population) -> List[Strategy]` method
  - For each strategy: run backtest, extract multi-objective metrics
  - Calculate Pareto ranks and crowding distances
  - Update strategy objects with fitness data
  - Purpose: Fitness evaluation
  - _Leverage: autonomous_loop, multi_objective.assign_pareto_ranks_
  - _Requirements: R1.3, R6.1_

- [ ] 44. Implement evolve_generation method
  - File: `src/evolution/population_manager.py` (continue from task 43)
  - Add `evolve_generation(generation_num) -> EvolutionResult` method
  - Execute 6-step evolution workflow (evaluate → select → crossover → mutate → replace → log)
  - Track timing for each phase
  - Return EvolutionResult with complete statistics
  - Purpose: Core evolution loop
  - _Leverage: selection, crossover, mutation, multi_objective_
  - _Requirements: R2.1, R3.1, R4.1, R5.1_

- [ ] 45. Add elitism_replacement method
  - File: `src/evolution/population_manager.py` (continue from task 44)
  - Add `elitism_replacement(current_pop, offspring, elite_count) -> List[Strategy]` method
  - Preserve top elite_count strategies
  - Add valid offspring
  - Remove worst performers to maintain population_size
  - Purpose: Form next generation
  - _Leverage: selection.get_elite_strategies_
  - _Requirements: R5.1, R5.2_

- [ ] 46. Implement save_checkpoint and load_checkpoint methods
  - File: `src/evolution/population_manager.py` (continue from task 45)
  - Add `save_checkpoint(filepath)` method to serialize population state to JSON
  - Add `load_checkpoint(filepath)` method to deserialize and restore state
  - Include lineage tree, generation history
  - Purpose: Recovery and persistence
  - _Leverage: json module, Strategy.to_dict()_
  - _Requirements: R10.2_

- [ ] 47. Add diversity monitoring and adaptation
  - File: `src/evolution/population_manager.py` (continue from task 46)
  - Add `monitor_and_adapt_diversity(population)` method
  - Calculate diversity, check threshold
  - Increase mutation rate if diversity < 0.3
  - Inject 2 random strategies if severe collapse (<0.2)
  - Purpose: Prevent premature convergence
  - _Leverage: diversity.calculate_population_diversity_
  - _Requirements: R7.2_

- [ ] 48. Create integration tests for population_manager.py
  - File: `tests/evolution/test_population_manager.py`
  - Test `initialize_population()` creates N strategies
  - Test `evaluate_population()` assigns fitness
  - Test `evolve_generation()` maintains population size
  - Test `elitism_replacement()` preserves elites
  - Test `save_checkpoint()` and `load_checkpoint()` round-trip
  - Purpose: Ensure population manager correctness
  - _Leverage: pytest, mock autonomous_loop_
  - _Requirements: R1.1, R1.2, R5.1_

---

### Phase 8: Prompt Builder Integration (Tasks 49-52)

- [ ] 49. Create evolutionary_prompt_builder.py
  - File: `src/evolution/evolutionary_prompt_builder.py`
  - Create `EvolutionaryPromptBuilder` class extending `PromptBuilder`
  - Add `__init__` calling `super().__init__()`
  - Purpose: Extend existing prompt builder for evolution
  - _Leverage: src/prompt_builder.py_
  - _Requirements: R8.2_

- [ ] 50. Add build_crossover_prompt method
  - File: `src/evolution/evolutionary_prompt_builder.py` (continue from task 49)
  - Add `build_crossover_prompt(parent1, parent2, target_params)` method
  - Format parent code snippets (relevant features only)
  - Include target parameters to achieve
  - Emphasize combining strengths from both parents
  - Purpose: Guide LLM for crossover
  - _Leverage: base PromptBuilder.build_prompt_
  - _Requirements: R3.2, R8.2_

- [ ] 51. Add build_mutation_prompt method
  - File: `src/evolution/evolutionary_prompt_builder.py` (continue from task 50)
  - Add `build_mutation_prompt(strategy, mutated_params)` method
  - Include original strategy code
  - Highlight mutated parameters (before/after)
  - Emphasize incremental variation
  - Purpose: Guide LLM for mutation
  - _Leverage: base PromptBuilder.build_prompt_
  - _Requirements: R4.3, R8.2_

- [ ] 52. Add build_initialization_prompt method
  - File: `src/evolution/evolutionary_prompt_builder.py` (continue from task 51)
  - Add `build_initialization_prompt(strategy_type)` method
  - Support strategy_type: 'momentum', 'value', 'quality', 'mixed'
  - Generate diverse initial strategies
  - Purpose: Create initial population diversity
  - _Leverage: base PromptBuilder.build_prompt_
  - _Requirements: R1.1_

---

### Phase 9: End-to-End Integration (Tasks 53-57)

- [ ] 53. Create 5-generation pilot test script
  - File: `tests/integration/test_5generation_pilot.py`
  - Initialize PopulationManager with N=10
  - Run 5 generations
  - Assert population size maintained, Pareto front exists, diversity >0.2
  - Log results to `logs/5generation_pilot.log`
  - Purpose: Early validation of full workflow
  - _Leverage: pytest, PopulationManager_
  - _Requirements: All_

- [ ] 54. Add metrics extraction integration
  - File: `src/evolution/population_manager.py` (modify)
  - Update `evaluate_population()` to call `backtest/metrics.calculate_calmar_ratio()`
  - Extract all 7 multi-objective metrics from backtest results
  - Handle missing metrics gracefully (default to 0.0)
  - Purpose: Complete integration with backtest system
  - _Leverage: src/backtest/metrics.py_
  - _Requirements: R6.1, R8.3_

- [ ] 55. Add progress visualization during evolution
  - File: `src/evolution/population_manager.py` (modify)
  - After each generation, call `visualization.plot_pareto_front()` and `plot_diversity_over_time()`
  - Save plots to `plots/generation_{num}_pareto.png` and `plots/diversity.png`
  - Purpose: Real-time monitoring
  - _Leverage: src/evolution/visualization.py_
  - _Requirements: R11.1_

- [ ] 56. Create full integration test (5 generations, N=20)
  - File: `tests/integration/test_full_evolution.py`
  - Run complete evolution with production configuration
  - Test all 5 integration scenarios from design document
  - Assert success criteria from requirements
  - Purpose: Comprehensive validation
  - _Leverage: pytest, PopulationManager_
  - _Requirements: All_

- [ ] 57. Add command-line interface for running evolution
  - File: `run_population_evolution.py` (root directory)
  - Accept arguments: --population-size, --generations, --model, --checkpoint-dir
  - Initialize PopulationManager, run evolution, save results
  - Display progress and final statistics
  - Purpose: User-friendly execution
  - _Leverage: argparse, PopulationManager_
  - _Requirements: R11.1, R11.2_

---

### Phase 10: Validation & Documentation (Tasks 58-60)

- [ ] 58. Create 20-generation validation script
  - File: `run_20generation_validation.py` (root directory)
  - Run 20 generations with N=20 (production configuration)
  - Track all success criteria metrics
  - Generate validation report with pass/fail for each criterion
  - Save to `VALIDATION_REPORT.md`
  - Purpose: Final production readiness check
  - _Leverage: PopulationManager_
  - _Requirements: All_

- [ ] 59. Add statistical analysis to validation script
  - File: `run_20generation_validation.py` (modify)
  - Calculate champion update rate (% generations with champion update)
  - Calculate rolling variance of final 20 strategies
  - Perform t-test vs random baseline, report p-value and Cohen's d
  - Count Pareto front size in final generation
  - Purpose: Quantitative success evaluation
  - _Leverage: SciPy for statistical tests_
  - _Requirements: Success Criteria_

- [ ] 60. Create user documentation in docs/POPULATION_EVOLUTION_GUIDE.md
  - File: `docs/POPULATION_EVOLUTION_GUIDE.md`
  - Explain population-based learning concept
  - Provide quick start guide (how to run, interpret results)
  - Document configuration parameters
  - Include example outputs and visualizations
  - Purpose: User onboarding
  - _Requirements: R11.2_

---

## Task Dependencies

```
Phase 1 (Foundation)
  └─> Phase 2 (Multi-objective) + Phase 3 (Diversity)
      └─> Phase 4 (Selection) + Phase 5 (Crossover) + Phase 6 (Mutation)
          └─> Phase 7 (Population Manager)
              └─> Phase 8 (Prompt Integration)
                  └─> Phase 9 (Integration)
                      └─> Phase 10 (Validation)
```

---

## Estimated Timeline

- **Phase 1-3** (Foundation): 8 hours (Day 1-2)
- **Phase 4-6** (Evolution Components): 12 hours (Day 3-4)
- **Phase 7-8** (Population Manager): 8 hours (Day 5)
- **Phase 9** (Integration): 6 hours (Day 6)
- **Phase 10** (Validation): 10 hours (Day 7-8)

**Total**: ~44 hours (1.5 weeks with 6 hours/day)

---

## Checkpoints

After completing each phase:
1. Run all unit tests (`pytest tests/evolution/`)
2. Run phase-specific integration test
3. Commit progress with descriptive message
4. Update this document with actual vs. estimated time

---

**Document Status**: Tasks Defined - Ready for Implementation
**Version**: 1.0
**Date**: 2025-10-17
**Total Tasks**: 60 atomic tasks
