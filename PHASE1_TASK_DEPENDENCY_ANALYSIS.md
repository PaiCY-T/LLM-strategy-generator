# Phase 1 Implementation - Task Dependency Analysis

**Date**: 2025-10-17
**Purpose**: Identify parallel execution opportunities for efficient implementation

---

## Task Breakdown & Dependencies

### Layer 1: Foundation (No Dependencies)

**Task 1.1: Individual Class**
- **File**: `src/population/individual.py`
- **Dependencies**: None (only stdlib: dataclasses, hashlib, json)
- **Estimated Time**: 30 minutes
- **Can Run in Parallel**: ✅ Yes (first task)
- **Description**:
  - Dataclass with parameters, fitness, metrics, generation, parent_ids, id
  - Hash-based ID generation
  - Validation methods

---

### Layer 2: Core Components (Depend on Individual)

These 4 tasks all depend on Individual but are **independent of each other** → Can run in **PARALLEL**

**Task 2.1: PopulationManager**
- **File**: `src/population/population_manager.py`
- **Dependencies**: Individual ✅ (Layer 1)
- **Estimated Time**: 90 minutes
- **Can Run in Parallel with**: 2.2, 2.3, 2.4 ✅
- **Description**:
  - Population initialization with diversity guarantee
  - Tournament selection (size=2)
  - Elitism (combine top N elites + offspring)
  - Diversity calculation
  - Convergence detection (window=10)

**Task 2.2: GeneticOperators**
- **File**: `src/population/genetic_operators.py`
- **Dependencies**: Individual ✅ (Layer 1)
- **Estimated Time**: 45 minutes
- **Can Run in Parallel with**: 2.1, 2.3, 2.4 ✅
- **Description**:
  - Mutation operator (adaptive rate 0.05-0.30)
  - Uniform crossover
  - Duplicate parent check
  - Adaptive mutation rate with decay

**Task 2.3: FitnessEvaluator**
- **File**: `src/population/fitness_evaluator.py`
- **Dependencies**: Individual ✅ (Layer 1), MomentumTemplate ✅ (exists)
- **Estimated Time**: 60 minutes
- **Can Run in Parallel with**: 2.1, 2.2, 2.4 ✅
- **Description**:
  - IS/OOS data split (2015-2020 vs 2021-2024)
  - Strategy evaluation with caching
  - Batch evaluation
  - Cache statistics tracking

**Task 2.4: EvolutionMonitor**
- **File**: `src/population/evolution_monitor.py`
- **Dependencies**: Individual ✅ (Layer 1)
- **Estimated Time**: 30 minutes
- **Can Run in Parallel with**: 2.1, 2.2, 2.3 ✅
- **Description**:
  - Generation statistics tracking
  - Champion history
  - Cache statistics integration
  - Summary report generation

---

### Layer 3: Integration (Depends on ALL Layer 2)

**Task 3.1: Phase1TestHarness**
- **File**: `tests/integration/phase1_test_harness.py`
- **Dependencies**: ALL Layer 2 components (2.1, 2.2, 2.3, 2.4) ❌
- **Estimated Time**: 120 minutes
- **Can Run in Parallel**: ❌ No (must wait for Layer 2)
- **Description**:
  - Extend Phase0TestHarness
  - Main evolution loop with convergence restart
  - IS/OOS data splitting
  - Checkpoint format extension
  - Population state management

**Task 3.2: Run Scripts**
- **File**: `run_phase1_smoke_test.py`, `run_phase1_full_test.py`
- **Dependencies**: Phase1TestHarness ✅ (Task 3.1)
- **Estimated Time**: 30 minutes
- **Can Run in Parallel with**: 3.1 (partially) ⚠️
- **Description**:
  - Smoke test runner (10 generations, pop=30)
  - Full test runner (50 generations, pop=50)
  - Logging setup
  - Results analysis integration

---

### Layer 4: Testing (Depends on Layer 3)

**Task 4.1: Unit Tests**
- **File**: `tests/population/*.py`
- **Dependencies**: Layer 2 components ✅
- **Estimated Time**: 60 minutes
- **Can Run in Parallel with**: 3.1, 3.2 ✅ (partially)
- **Description**:
  - Test Individual hashing
  - Test PopulationManager selection, diversity, elitism
  - Test GeneticOperators mutation, crossover
  - Test FitnessEvaluator caching, IS/OOS split
  - Test EvolutionMonitor statistics

---

## Parallel Execution Plan

### Wave 1: Foundation (Sequential, 30 min)
```
Task 1.1: Individual Class
  └─ Output: src/population/individual.py
```

### Wave 2: Core Components (PARALLEL, 90 min max)
```
Task 2.1: PopulationManager ─┐
Task 2.2: GeneticOperators   ├─ Run in parallel (4 agents)
Task 2.3: FitnessEvaluator   │
Task 2.4: EvolutionMonitor   ┘
  └─ Outputs: 4 component files
```

### Wave 3: Integration (Sequential, 120 min)
```
Task 3.1: Phase1TestHarness
  └─ Output: tests/integration/phase1_test_harness.py
```

### Wave 4: Scripts & Tests (PARALLEL, 60 min max)
```
Task 3.2: Run Scripts ─┬─ Run in parallel (2 agents)
Task 4.1: Unit Tests  ─┘
  └─ Outputs: run scripts + unit tests
```

---

## Total Time Estimate

### Sequential Execution (No Parallelization)
```
Wave 1: 30 min
Wave 2: 90 + 45 + 60 + 30 = 225 min (3h 45m)
Wave 3: 120 min (2h)
Wave 4: 30 + 60 = 90 min (1h 30m)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 465 minutes (7h 45m)
```

### Parallel Execution (With Task Tool)
```
Wave 1: 30 min (sequential)
Wave 2: 90 min (parallel, limited by slowest task 2.1)
Wave 3: 120 min (sequential)
Wave 4: 60 min (parallel, limited by slowest task 4.1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 300 minutes (5 hours)
```

**Time Saved**: ~2.75 hours (35% faster)

---

## Agent Assignment Strategy

### Wave 1 (1 agent)
- **Agent 1**: Task 1.1 (Individual)

### Wave 2 (4 agents in parallel)
- **Agent 1**: Task 2.1 (PopulationManager) - 90 min (critical path)
- **Agent 2**: Task 2.2 (GeneticOperators) - 45 min
- **Agent 3**: Task 2.3 (FitnessEvaluator) - 60 min
- **Agent 4**: Task 2.4 (EvolutionMonitor) - 30 min

### Wave 3 (1 agent)
- **Agent 1**: Task 3.1 (Phase1TestHarness) - 120 min

### Wave 4 (2 agents in parallel)
- **Agent 1**: Task 3.2 (Run Scripts) - 30 min
- **Agent 2**: Task 4.1 (Unit Tests) - 60 min

---

## Risk Analysis

### Risks with Parallel Execution

**Risk 1: Interface Mismatch**
- **Description**: Components may have incompatible interfaces if developed in parallel
- **Mitigation**:
  - Define clear interfaces in design document (already done ✅)
  - Individual class is well-defined (Layer 1 is sequential)
  - Code review after Wave 2 before proceeding to Wave 3
- **Severity**: Medium

**Risk 2: Agent Context Limitations**
- **Description**: Agents may not have full context of overall system
- **Mitigation**:
  - Provide comprehensive task descriptions
  - Reference design documents
  - Include relevant existing code (Phase0TestHarness, MomentumTemplate)
- **Severity**: Low

**Risk 3: Debugging Overhead**
- **Description**: Parallel bugs harder to trace than sequential
- **Mitigation**:
  - Wave 1 provides stable foundation
  - Wave 2 unit tests validate each component
  - Wave 3 integration testing catches interface issues
- **Severity**: Low

### Benefits Outweigh Risks

✅ **35% time reduction** (7.75h → 5h)
✅ **Clear dependency layers** minimize interface risk
✅ **Well-defined interfaces** in design documents
✅ **Smoke test validation** catches issues early

---

## Execution Recommendation

### Strategy: Hybrid Parallel Execution

1. **Wave 1 (Sequential)**: Implement Individual class
   - 30 minutes, single agent
   - Provides stable foundation for Wave 2

2. **Wave 2 (Full Parallel)**: Launch 4 agents simultaneously
   - PopulationManager, GeneticOperators, FitnessEvaluator, EvolutionMonitor
   - Wait for all 4 to complete (~90 min)
   - Quick code review before Wave 3

3. **Wave 3 (Sequential)**: Implement Phase1TestHarness
   - 120 minutes, single agent
   - Integration layer requires all Layer 2 components

4. **Wave 4 (Partial Parallel)**: Run scripts + unit tests
   - 2 agents in parallel
   - Final validation (~60 min)

**Total Duration**: ~5 hours (vs 7.75h sequential)

---

## Task Executor Configuration

### Wave 2 Task Specifications

**Task 2.1: PopulationManager**
```yaml
task_id: phase1-population-manager
description: Implement PopulationManager class
files:
  input:
    - src/population/individual.py
    - PHASE1_DESIGN_REVISION.md
  output:
    - src/population/population_manager.py
requirements:
  - Population initialization with diversity=1.0
  - Tournament selection (size=2)
  - Elitism strategy (combine elites + offspring)
  - Diversity calculation
  - Convergence detection (window=10, 2 criteria)
success_criteria:
  - All methods implemented
  - Type hints complete
  - Docstrings comprehensive
```

**Task 2.2: GeneticOperators**
```yaml
task_id: phase1-genetic-operators
description: Implement GeneticOperators class
files:
  input:
    - src/population/individual.py
    - src/templates/momentum_template.py (for PARAM_GRID)
    - PHASE1_DESIGN_REVISION.md
  output:
    - src/population/genetic_operators.py
requirements:
  - Mutation operator (adaptive 0.05-0.30)
  - Uniform crossover with duplicate check
  - Adaptive mutation rate with decay
success_criteria:
  - Mutated parameters always valid
  - Crossover produces valid offspring
  - Mutation rate adapts correctly
```

**Task 2.3: FitnessEvaluator**
```yaml
task_id: phase1-fitness-evaluator
description: Implement FitnessEvaluator with IS/OOS split
files:
  input:
    - src/population/individual.py
    - src/templates/momentum_template.py
    - PHASE1_DESIGN_REVISION.md
  output:
    - src/population/fitness_evaluator.py
requirements:
  - IS/OOS data split (2015-2020 vs 2021-2024)
  - Fitness caching with statistics
  - Batch evaluation support
success_criteria:
  - Cache hit/miss tracking works
  - IS/OOS evaluation separated
  - Thread-safe cache design (for future)
```

**Task 2.4: EvolutionMonitor**
```yaml
task_id: phase1-evolution-monitor
description: Implement EvolutionMonitor class
files:
  input:
    - src/population/individual.py
    - PHASE1_DESIGN_REVISION.md
  output:
    - src/population/evolution_monitor.py
requirements:
  - Generation statistics tracking
  - Champion history management
  - Cache statistics integration
  - Summary report generation
success_criteria:
  - All metrics tracked correctly
  - Champion updates detected
  - Summary provides actionable insights
```

---

## Execution Command

```bash
# Wave 1: Individual (Sequential)
# Implement manually or via single Task

# Wave 2: Launch 4 parallel tasks
# Use Task tool with subagent_type="spec-task-executor"
# Launch all 4 in a single message for true parallelization

# Wave 3: Phase1TestHarness (Sequential)
# After Wave 2 completes

# Wave 4: Scripts + Tests (Parallel)
# Launch 2 tasks in parallel
```

---

**Status**: ✅ DEPENDENCY ANALYSIS COMPLETE
**Recommendation**: Execute in 4 waves with Wave 2 fully parallelized
**Expected Time Savings**: 2.75 hours (35% faster)
