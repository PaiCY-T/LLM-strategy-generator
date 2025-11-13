# Phase 0: Template-Guided Parameter Generation - Integration Guide

**Version**: 1.0
**Last Updated**: 2025-10-19
**Status**: Ready for Testing

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Component Integration](#component-integration)
5. [Running Tests](#running-tests)
6. [Interpreting Results](#interpreting-results)
7. [Decision Matrix](#decision-matrix)
8. [Troubleshooting](#troubleshooting)
9. [API Reference](#api-reference)

---

## Overview

Phase 0 validates the hypothesis that **template-guided parameter generation** with LLM can achieve sufficient champion update rates (≥5%) to skip the more complex population-based learning system.

### Key Components

- **Phase0TestHarness**: Orchestrates 50-iteration test with template mode
- **ResultsAnalyzer**: Analyzes results and makes GO/NO-GO/PARTIAL decision
- **MomentumTemplate**: Domain-specific template for momentum strategies
- **AutonomousLoop**: Existing autonomous learning infrastructure

### Decision Framework

```
SUCCESS (≥5% update rate AND >1.0 Sharpe)
  → Skip population-based learning
  → Proceed with template mode optimization

PARTIAL (2-5% update rate OR 0.8-1.0 Sharpe)
  → Hybrid approach: template mode + small population (N=5-10)
  → Reduce complexity of Phase 1

FAILURE (<2% update rate OR <0.8 Sharpe)
  → Proceed to full population-based learning (N=20)
```

---

## Quick Start

### Prerequisites

```bash
# Ensure finlab is installed and configured
pip install finlab

# Set finlab API token
export FINLAB_API_TOKEN="your_token_here"

# Verify LLM access (Gemini API)
export GOOGLE_API_KEY="your_gemini_api_key"
```

### Running Phase 0 Tests

```bash
# Step 1: Smoke test (5 iterations, ~5-10 minutes)
python run_phase0_smoke_test.py

# Step 2: If smoke test passes, run full test (50 iterations, ~2-4 hours)
python run_phase0_full_test.py

# Step 3: Review decision report
cat PHASE0_RESULTS.md
```

---

## Architecture

### System Integration Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  Phase 0 Test Pipeline                  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Phase0TestHarness (Orchestrator)            │
│  - Manages 50-iteration test loop                       │
│  - Tracks champion updates                              │
│  - Records parameter combinations                        │
│  - Handles checkpointing                                │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              AutonomousLoop (Template Mode)              │
│  - Template: MomentumTemplate                           │
│  - Parameter generation: LLM (gemini-2.5-flash)         │
│  - Validation: StrategyValidator                        │
│  - History: HistoryManager                              │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│            ResultsAnalyzer (Decision Engine)             │
│  - Calculates primary metrics                           │
│  - Compares to baseline                                 │
│  - Analyzes parameter diversity                         │
│  - Makes GO/NO-GO/PARTIAL decision                      │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Phase0TestHarness initializes AutonomousLoop in template mode
2. For each iteration (0-49):
   a. AutonomousLoop generates strategy using MomentumTemplate + LLM
   b. Strategy validated with StrategyValidator
   c. Backtest executed, metrics calculated
   d. Champion comparison performed
   e. Results recorded in HistoryManager
   f. Checkpoint saved every 10 iterations
3. After 50 iterations:
   a. Results compiled by Phase0TestHarness
   b. ResultsAnalyzer processes results
   c. Decision made based on criteria
   d. Report generated (PHASE0_RESULTS.md)
```

---

## Component Integration

### 1. Phase0TestHarness

**Location**: `tests/integration/phase0_test_harness.py`

**Purpose**: Orchestrates the 50-iteration test with checkpointing and result tracking.

#### Key Methods

```python
from tests.integration.phase0_test_harness import Phase0TestHarness

# Initialize harness
harness = Phase0TestHarness(
    test_name="phase0_test",
    max_iterations=50,
    model="gemini-2.5-flash",
    checkpoint_interval=10
)

# Run full test
results = harness.run(data=finlab_data)

# Or run 5-iteration smoke test
results = harness.run_5_generation_test(data=finlab_data)
```

#### Tracked Metrics

- `champion_update_rate`: % of iterations with champion updates
- `avg_sharpe`: Average Sharpe ratio across successful iterations
- `best_sharpe`: Highest Sharpe ratio achieved
- `param_diversity`: Number of unique parameter combinations
- `validation_pass_rate`: % of validations passed

### 2. ResultsAnalyzer

**Location**: `tests/integration/phase0_results_analyzer.py`

**Purpose**: Analyzes test results and makes GO/NO-GO/PARTIAL decision.

#### Key Methods

```python
from tests.integration.phase0_results_analyzer import ResultsAnalyzer

# Initialize analyzer with results
analyzer = ResultsAnalyzer(results)

# Calculate primary metrics
metrics = analyzer.calculate_primary_metrics()

# Compare to baseline (200-iteration free-form test)
comparison = analyzer.compare_to_baseline()

# Analyze parameter diversity
diversity = analyzer.analyze_parameter_diversity()

# Make GO/NO-GO/PARTIAL decision
decision = analyzer.make_decision()

# Generate comprehensive report
report_path = analyzer.generate_report(output_file="PHASE0_RESULTS.md")
```

#### Decision Thresholds

```python
THRESHOLDS = {
    'success': {
        'champion_update_rate': 5.0,  # ≥5% for SUCCESS
        'avg_sharpe': 1.0               # >1.0 for SUCCESS
    },
    'partial': {
        'champion_update_rate': 2.0,  # 2-5% for PARTIAL
        'avg_sharpe': 0.8               # 0.8-1.0 for PARTIAL
    },
    'target': {
        'param_diversity': 30,          # ≥30 unique combinations
        'validation_pass_rate': 90.0    # ≥90% validation pass rate
    }
}
```

### 3. Template Mode Integration

Phase 0 uses `AutonomousLoop` in **template mode**:

```python
# AutonomousLoop initialization in Phase0TestHarness
self.loop = AutonomousLoop(
    template_mode=True,          # Enable template mode
    template_name="Momentum",     # Use MomentumTemplate
    model=self.model,             # LLM for parameter generation
    max_iterations=max_iterations,
    history_file=f'iteration_history_{test_name}.json'
)
```

**Template Mode Behavior**:
- Uses `MomentumTemplate` for strategy structure
- LLM generates parameter values within template constraints
- Template ensures valid strategy structure
- LLM explores parameter space for optimization

---

## Running Tests

### Smoke Test (5 iterations)

**Purpose**: Quick validation that infrastructure works correctly.

```bash
python run_phase0_smoke_test.py
```

**Expected Duration**: 5-10 minutes

**Validation Checks**:
- Template mode parameter generation works
- Champion update tracking works
- Metrics calculation works
- Checkpointing works
- Results compilation works

**Output**:
```
✅ SMOKE TEST PASSED - ALL SYSTEMS OPERATIONAL

Phase 0 template mode infrastructure is working correctly.

⚠️  IMPORTANT NOTES:
  - This was only a 5-iteration smoke test
  - Full 50-iteration test required for GO/NO-GO decision
  - Run 'python run_phase0_full_test.py' for full validation
```

### Full Test (50 iterations)

**Purpose**: Complete test for GO/NO-GO/PARTIAL decision.

```bash
python run_phase0_full_test.py
```

**Expected Duration**: 2-4 hours

**Checkpointing**: Automatically saves checkpoints every 10 iterations.

**Resume from Checkpoint**:
```python
# If test is interrupted, resume from checkpoint
harness = Phase0TestHarness(test_name="phase0_full_test")
results = harness.run(
    data=finlab_data,
    resume_from_checkpoint="checkpoints/checkpoint_phase0_full_test_iter_40.json"
)
```

---

## Interpreting Results

### Results Dictionary Structure

```python
results = {
    # Test completion
    'test_completed': True,
    'total_iterations': 50,

    # Primary decision metrics
    'champion_update_count': 3,
    'champion_update_rate': 6.0,  # % (3/50 * 100)
    'best_sharpe': 2.15,
    'avg_sharpe': 1.25,
    'sharpe_variance': 0.45,

    # Phase 0 specific metrics
    'param_diversity': 35,
    'param_diversity_rate': 70.0,  # % (35/50 * 100)
    'validation_pass_rate': 92.0,  # %

    # Success metrics
    'success_count': 46,
    'failure_count': 4,
    'success_rate': 92.0,  # %

    # Duration metrics
    'total_duration_seconds': 7200.0,  # 2 hours
    'avg_duration_per_iteration': 144.0,  # seconds

    # Champion state
    'final_champion': {
        'iteration': 42,
        'sharpe': 2.15,
        'metrics': {...},
        'parameters': {...}
    }
}
```

### Decision Analysis

```python
decision = analyzer.make_decision()

decision = {
    'decision': 'SUCCESS',  # or 'PARTIAL' or 'FAILURE'
    'confidence': 'HIGH',   # or 'MEDIUM' or 'LOW'
    'recommendation': "Template mode has proven effective...",
    'reasoning': [
        "✅ Champion update rate (6.00%) exceeds SUCCESS threshold (≥5.0%)",
        "✅ Average Sharpe ratio (1.25) exceeds SUCCESS threshold (>1.0)",
        "✅ Parameter diversity (35 unique) meets target (≥30)",
        "✅ Validation pass rate (92.0%) meets target (≥90.0%)"
    ],
    'primary_criteria_met': {
        'update_rate_success': True,
        'sharpe_success': True,
        'update_rate_partial': False,
        'sharpe_partial': False
    },
    'secondary_criteria_met': {
        'param_diversity_met': True,
        'validation_pass_rate_met': True
    },
    'key_metrics': {...}
}
```

---

## Decision Matrix

### SUCCESS Criteria

**Both must be met**:
- Champion update rate ≥ 5.0%
- Average Sharpe ratio > 1.0

**Recommendation**:
```
Template mode has proven effective. SKIP population-based learning (Phase 1)
and proceed directly to template mode optimization and out-of-sample validation.
```

**Next Steps**:
1. Document successful template mode configuration
2. Implement out-of-sample validation
3. Optimize template mode parameters
4. Deploy to production monitoring

### PARTIAL Criteria

**Either can trigger**:
- Champion update rate 2.0-5.0% OR
- Average Sharpe ratio 0.8-1.0

**Recommendation**:
```
Template mode shows improvement but below full SUCCESS criteria.
CONSIDER hybrid approach: use template mode as baseline for population-based
learning with reduced population size (N=5-10 instead of 20).
```

**Next Steps**:
1. Design hybrid system architecture
2. Implement small population variant
3. Test hybrid approach with 5-10 candidates
4. Compare hybrid vs. full population-based

### FAILURE Criteria

**Either can trigger**:
- Champion update rate < 2.0% OR
- Average Sharpe ratio < 0.8

**Recommendation**:
```
Template mode shows minimal improvement over baseline.
PROCEED to full population-based learning (Phase 1) with standard
population size (N=20).
```

**Next Steps**:
1. Implement full Phase 1 architecture
2. Design population management
3. Implement crossover and mutation
4. Run population-based validation

---

## Troubleshooting

### Common Issues

#### 1. Data Loading Fails

**Symptom**: `Failed to load finlab data`

**Solution**:
```bash
# Check API token
echo $FINLAB_API_TOKEN

# If empty, set it
export FINLAB_API_TOKEN="your_token_here"

# Verify finlab installation
pip show finlab
```

#### 2. LLM Generation Fails

**Symptom**: `LLM API error` or `Parameter generation failed`

**Solution**:
```bash
# Check Gemini API key
echo $GOOGLE_API_KEY

# If empty, set it
export GOOGLE_API_KEY="your_gemini_api_key"

# Test API access
python -c "import google.generativeai as genai; genai.configure(api_key='$GOOGLE_API_KEY'); print('OK')"
```

#### 3. Template Import Error

**Symptom**: `MomentumTemplate not available`

**Solution**:
```bash
# Verify template file exists
ls -l src/templates/momentum_template.py

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Add project root to PYTHONPATH if needed
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 4. Checkpoint Load Failure

**Symptom**: `Failed to load checkpoint: missing required fields`

**Solution**:
```python
# Check checkpoint file integrity
import json
with open('checkpoints/checkpoint_phase0_test_iter_40.json', 'r') as f:
    data = json.load(f)
    print("Required fields:",
          all(k in data for k in ['iteration_number', 'sharpes', 'durations']))
```

### Performance Issues

#### Slow Iteration Times

**Normal**: 2-3 minutes per iteration
**Slow**: >5 minutes per iteration

**Potential Causes**:
1. Network latency (LLM API calls)
2. Large data files
3. Complex backtests

**Solutions**:
- Use faster LLM model (gemini-2.5-flash vs. gemini-2.5-pro)
- Reduce data size for testing
- Enable result caching

---

## API Reference

### Phase0TestHarness

```python
class Phase0TestHarness:
    """Test harness for 50-iteration template mode validation."""

    def __init__(
        self,
        test_name: str = "phase0_template_test",
        max_iterations: int = 50,
        model: str = "gemini-2.5-flash",
        checkpoint_interval: int = 10,
        checkpoint_dir: str = "checkpoints"
    ):
        """Initialize test harness."""

    def run(
        self,
        data: Any,
        resume_from_checkpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute 50-iteration template mode test."""

    def run_5_generation_test(
        self,
        data: Any,
        resume_from_checkpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute 5-iteration smoke test."""
```

### ResultsAnalyzer

```python
class ResultsAnalyzer:
    """Analyzer for Phase 0 template mode test results."""

    def __init__(self, results: Dict[str, Any]):
        """Initialize analyzer with test results."""

    def calculate_primary_metrics(self) -> Dict[str, float]:
        """Calculate all primary decision metrics."""

    def compare_to_baseline(self) -> Dict[str, Any]:
        """Compare results to free-form baseline."""

    def analyze_parameter_diversity(self) -> Dict[str, Any]:
        """Analyze parameter diversity and exploration patterns."""

    def make_decision(self) -> Dict[str, Any]:
        """Make GO/NO-GO/PARTIAL decision."""

    def generate_report(self, output_file: str = "PHASE0_RESULTS.md") -> str:
        """Generate comprehensive markdown report."""
```

---

## Summary

Phase 0 provides a **systematic, data-driven approach** to determine whether template-guided parameter generation is sufficient or if population-based learning is needed.

**Key Benefits**:
- Evidence-based decision making
- Clear success criteria
- Comprehensive baseline comparison
- Detailed parameter diversity analysis
- Automated GO/NO-GO/PARTIAL recommendation

**Next Steps After Phase 0**:
1. Run smoke test to validate infrastructure
2. Run full 50-iteration test
3. Review decision report
4. Proceed based on recommendation (SUCCESS/PARTIAL/FAILURE)

For questions or issues, refer to:
- Design document: `.spec-workflow/specs/phase0-template-mode/design.md`
- Requirements: `.spec-workflow/specs/phase0-template-mode/requirements.md`
- Task tracking: `.spec-workflow/specs/phase0-template-mode/tasks.md`
