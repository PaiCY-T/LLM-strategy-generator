# LLM Learning Validation - Technical Design

## 1. System Architecture

### 1.1 High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                   EXPERIMENT ORCHESTRATOR                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Configuration Manager                      │    │
│  │  - Load YAML config                                    │    │
│  │  - Validate experiment parameters                      │    │
│  └────────────────────────────────────────────────────────┘    │
│                              │                                   │
│              ┌───────────────┼───────────────┐                 │
│              ▼               ▼               ▼                 │
│    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│    │  Group A     │ │  Group B     │ │  Group C     │        │
│    │  Hybrid 30%  │ │  FG-Only 0%  │ │  LLM-Only    │        │
│    │              │ │              │ │  100%        │        │
│    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘        │
│           │                │                │                 │
│           └────────────────┼────────────────┘                 │
│                            ▼                                   │
│              ┌─────────────────────────────┐                  │
│              │  Novelty Quantification     │                  │
│              │  System (3 Layers)          │                  │
│              └─────────────┬───────────────┘                  │
│                            ▼                                   │
│              ┌─────────────────────────────┐                  │
│              │  Statistical Analysis       │                  │
│              │  Pipeline                   │                  │
│              └─────────────┬───────────────┘                  │
│                            ▼                                   │
│              ┌─────────────────────────────┐                  │
│              │  Results & Reports          │                  │
│              └─────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Overview

#### 1.2.1 Experiment Orchestrator
- **Responsibility**: Manage end-to-end experiment execution
- **Location**: `experiments/llm_learning_validation/orchestrator.py`
- **Key Functions**:
  - Load and validate configuration
  - Initialize LearningSystem instances per group
  - Execute iterations sequentially
  - Collect and aggregate results

#### 1.2.2 Novelty Quantification System
- **Responsibility**: Measure strategy innovation across 3 layers
- **Location**: `src/analysis/novelty/`
- **Key Components**:
  - Factor Diversity Analyzer
  - Combination Pattern Detector
  - Logic Complexity Analyzer
  - Novelty Scorer (aggregator)

#### 1.2.3 Statistical Analysis Pipeline
- **Responsibility**: Statistical testing and visualization
- **Location**: `src/analysis/`
- **Key Components**:
  - Statistical Tests Module
  - Visualization Engine
  - Report Generator

#### 1.2.4 Data Layer
- **Responsibility**: Persistence and data integrity
- **Location**: `src/learning/iteration_history.py` (extended)
- **Key Functions**:
  - Enhanced IterationRecord dataclass
  - JSON serialization/deserialization
  - Data validation

## 2. Detailed Component Design

### 2.1 Configuration System

#### 2.1.1 Config Schema
```yaml
# experiments/llm_learning_validation/config.yaml

experiment:
  name: "llm-learning-validation"
  version: "1.0.0"
  description: "A/B/C testing to validate LLM learning effectiveness"

phases:
  pilot:
    iterations_per_run: 50
    runs_per_group: 2
    total_iterations: 300  # 50 × 2 × 3

  full:
    iterations_per_run: 200
    runs_per_group: 5
    total_iterations: 3000  # 200 × 5 × 3

groups:
  - id: "hybrid"
    name: "Hybrid (30% LLM)"
    innovation_rate: 0.30
    output_dir: "artifacts/experiments/llm_validation/hybrid"

  - id: "fg_only"
    name: "Factor Graph Only (0% LLM)"
    innovation_rate: 0.00
    output_dir: "artifacts/experiments/llm_validation/fg_only"

  - id: "llm_only"
    name: "LLM Only (100% LLM)"
    innovation_rate: 1.00
    output_dir: "artifacts/experiments/llm_validation/llm_only"

novelty_weights:
  layer1_factor_diversity: 0.30
  layer2_combination_patterns: 0.40
  layer3_logic_complexity: 0.30

validation:
  max_failure_rate: 0.05  # 5%
  min_sharpe_threshold: 0.5
  statistical_significance: 0.05

go_no_go_criteria:
  min_criteria_met: 2
  statistical_signal_pvalue: 0.10
  novelty_advantage_threshold: 0.15  # 15%
  execution_time_buffer: 1.50  # 150%
```

#### 2.1.2 Config Loader
```python
from dataclasses import dataclass
from typing import List, Dict
import yaml

@dataclass
class GroupConfig:
    id: str
    name: str
    innovation_rate: float
    output_dir: str

@dataclass
class PhaseConfig:
    iterations_per_run: int
    runs_per_group: int
    total_iterations: int

@dataclass
class ExperimentConfig:
    name: str
    version: str
    description: str
    phases: Dict[str, PhaseConfig]
    groups: List[GroupConfig]
    novelty_weights: Dict[str, float]
    validation: Dict[str, float]
    go_no_go_criteria: Dict[str, float]

    @classmethod
    def load(cls, config_path: str) -> 'ExperimentConfig':
        """Load and validate experiment configuration"""
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)

        # Validation logic
        cls._validate_config(data)

        return cls(...)

    @staticmethod
    def _validate_config(data: dict) -> None:
        """Validate configuration schema and constraints"""
        # Check required fields
        # Validate innovation_rates in [0, 1]
        # Ensure output directories don't conflict
        # Validate novelty weights sum to 1.0
        pass
```

### 2.2 Orchestrator Design

#### 2.2.1 Class Structure
```python
from typing import List, Dict
from pathlib import Path
import logging

class ExperimentOrchestrator:
    """Manages A/B/C experiment execution and result aggregation"""

    def __init__(self, config_path: str):
        self.config = ExperimentConfig.load(config_path)
        self.groups: Dict[str, LearningSystem] = {}
        self.results: Dict[str, List[IterationRecord]] = {}
        self.logger = self._setup_logging()

    def initialize_groups(self) -> None:
        """Initialize LearningSystem instances for each experimental group"""
        for group_config in self.config.groups:
            learning_system = LearningSystem(
                config_path="config/learning_system.yaml",
                innovation_rate_override=group_config.innovation_rate
            )
            self.groups[group_config.id] = learning_system

            # Create output directory
            Path(group_config.output_dir).mkdir(parents=True, exist_ok=True)

    def run_phase(self, phase: str = "pilot", dry_run: bool = False) -> None:
        """Execute specified experiment phase"""
        phase_config = self.config.phases[phase]

        for group_id, learning_system in self.groups.items():
            self.logger.info(f"Starting {phase} for group: {group_id}")

            for run in range(phase_config.runs_per_group):
                self.logger.info(f"  Run {run + 1}/{phase_config.runs_per_group}")

                results = self._run_iterations(
                    learning_system=learning_system,
                    group_id=group_id,
                    num_iterations=phase_config.iterations_per_run,
                    run_id=run,
                    dry_run=dry_run
                )

                self.results.setdefault(group_id, []).extend(results)
                self._save_intermediate_results(group_id, results)

    def _run_iterations(
        self,
        learning_system: LearningSystem,
        group_id: str,
        num_iterations: int,
        run_id: int,
        dry_run: bool
    ) -> List[IterationRecord]:
        """Execute iterations for a single run"""
        results = []
        failure_count = 0

        for i in range(num_iterations):
            try:
                # Execute iteration
                strategy = learning_system.generate_strategy()
                metrics = learning_system.evaluate_strategy(strategy)

                # Calculate novelty scores
                novelty_scores = NoveltyScorer.score(strategy.code)

                # Create record
                record = IterationRecord(
                    iteration_num=i,
                    strategy_code=strategy.code,
                    metrics=metrics,
                    novelty_scores=novelty_scores.to_dict(),
                    experiment_group=group_id,
                    run_id=run_id
                )

                results.append(record)

                # Logging
                self.logger.info(
                    f"    Iteration {i}: Sharpe={metrics.sharpe_ratio:.4f}, "
                    f"Novelty={novelty_scores.total_score:.4f}"
                )

            except Exception as e:
                failure_count += 1
                self.logger.error(f"    Iteration {i} failed: {str(e)}")

                if failure_count / (i + 1) > self.config.validation.max_failure_rate:
                    raise RuntimeError(
                        f"Failure rate exceeded threshold: "
                        f"{failure_count}/{i+1} = {failure_count/(i+1):.2%}"
                    )

        return results

    def generate_report(self, phase: str) -> Path:
        """Generate comprehensive analysis report"""
        analyzer = ExperimentAnalyzer(
            results=self.results,
            config=self.config
        )

        report_path = analyzer.generate_html_report(phase=phase)
        self.logger.info(f"Report generated: {report_path}")

        return report_path

    def evaluate_go_no_go(self) -> Dict[str, any]:
        """Evaluate go/no-go criteria for Full Study"""
        analyzer = ExperimentAnalyzer(self.results, self.config)

        criteria = {
            "statistical_signal": analyzer.check_statistical_signal(),
            "novelty_signal": analyzer.check_novelty_signal(),
            "execution_stability": analyzer.check_execution_stability(),
            "champion_emergence": analyzer.check_champion_emergence()
        }

        criteria_met = sum(criteria.values())
        decision = "GO" if criteria_met >= self.config.go_no_go_criteria.min_criteria_met else "NO-GO"

        return {
            "decision": decision,
            "criteria_met": criteria_met,
            "criteria": criteria,
            "recommendation": self._generate_recommendation(criteria)
        }
```

### 2.3 Novelty Quantification System

#### 2.3.1 Layer 1: Factor Diversity Analyzer
```python
# src/analysis/novelty/factor_diversity.py

import re
from typing import Set, List
import numpy as np

class FactorDiversityAnalyzer:
    """Analyzes factor usage diversity and template deviation"""

    def __init__(self, template_library_path: str):
        self.templates = self._load_templates(template_library_path)
        self.factor_pattern = re.compile(r"df\['(\w+)'\]|df\.(\w+)")

    def analyze_factor_usage(self, strategy_code: str) -> Set[str]:
        """Extract unique factors from strategy code"""
        matches = self.factor_pattern.findall(strategy_code)
        factors = {m[0] or m[1] for m in matches}
        return factors

    def calculate_jaccard_distance(self, factors1: Set[str], factors2: Set[str]) -> float:
        """Calculate Jaccard distance between two factor sets"""
        if not factors1 and not factors2:
            return 0.0

        intersection = len(factors1 & factors2)
        union = len(factors1 | factors2)

        jaccard_similarity = intersection / union if union > 0 else 0
        return 1.0 - jaccard_similarity

    def score_template_deviation(self, factors: Set[str]) -> float:
        """Score how much factor set deviates from template library"""
        if not self.templates:
            return 0.5  # Neutral score if no templates

        # Calculate minimum Jaccard distance to any template
        min_distance = min(
            self.calculate_jaccard_distance(factors, template_factors)
            for template_factors in self.templates
        )

        # Normalize to [0, 1] where 1 = maximum deviation
        return np.clip(min_distance, 0.0, 1.0)

    def score(self, strategy_code: str) -> float:
        """Calculate Layer 1 novelty score"""
        factors = self.analyze_factor_usage(strategy_code)
        deviation_score = self.score_template_deviation(factors)

        # Bonus for using many unique factors
        factor_diversity_bonus = min(len(factors) / 10.0, 0.3)  # Cap at 30%

        return np.clip(deviation_score + factor_diversity_bonus, 0.0, 1.0)
```

#### 2.3.2 Layer 2: Combination Pattern Detector
```python
# src/analysis/novelty/combination_patterns.py

from dataclasses import dataclass
from typing import List, Set, Tuple
import re

@dataclass
class FactorCombo:
    factors: Set[str]
    weights: List[float]
    operation: str  # 'weighted_sum', 'ratio', 'product', 'custom'

class CombinationPatternDetector:
    """Detects and scores novel factor combination patterns"""

    def __init__(self, template_library_path: str):
        self.template_combos = self._load_template_combinations(template_library_path)

    def extract_combinations(self, strategy_code: str) -> List[FactorCombo]:
        """Identify factor combinations in strategy code"""
        combos = []

        # Pattern 1: Weighted sum (a*f1 + b*f2 + c*f3)
        weighted_sum_pattern = r"(\d+\.?\d*)\s*\*\s*df\['(\w+)'\]"
        matches = re.findall(weighted_sum_pattern, strategy_code)
        if matches:
            weights = [float(m[0]) for m in matches]
            factors = {m[1] for m in matches}
            combos.append(FactorCombo(factors, weights, 'weighted_sum'))

        # Pattern 2: Ratios (f1 / f2)
        ratio_pattern = r"df\['(\w+)'\]\s*/\s*df\['(\w+)'\]"
        matches = re.findall(ratio_pattern, strategy_code)
        for m in matches:
            combos.append(FactorCombo({m[0], m[1]}, [1.0, -1.0], 'ratio'))

        # Pattern 3: Products (f1 * f2)
        product_pattern = r"df\['(\w+)'\]\s*\*\s*df\['(\w+)'\]"
        matches = re.findall(product_pattern, strategy_code)
        for m in matches:
            combos.append(FactorCombo({m[0], m[1]}, [1.0, 1.0], 'product'))

        return combos

    def identify_novel_combinations(self, combo: FactorCombo) -> bool:
        """Check if combination is novel compared to templates"""
        for template_combo in self.template_combos:
            # Exact match on factors and operation
            if (combo.factors == template_combo.factors and
                combo.operation == template_combo.operation):
                return False

        return True

    def score_combination_complexity(self, combo: FactorCombo) -> float:
        """Score combination complexity"""
        # More factors = higher complexity
        factor_score = min(len(combo.factors) / 5.0, 0.5)

        # Non-linear operations score higher
        operation_scores = {
            'weighted_sum': 0.2,
            'ratio': 0.4,
            'product': 0.4,
            'custom': 0.6
        }
        operation_score = operation_scores.get(combo.operation, 0.3)

        return factor_score + operation_score

    def score(self, strategy_code: str) -> float:
        """Calculate Layer 2 novelty score"""
        combos = self.extract_combinations(strategy_code)

        if not combos:
            return 0.0

        # Score each combination
        combo_scores = []
        for combo in combos:
            novelty_bonus = 0.5 if self.identify_novel_combinations(combo) else 0.0
            complexity_score = self.score_combination_complexity(combo)
            combo_scores.append(novelty_bonus + complexity_score)

        # Average across all combinations
        return np.clip(np.mean(combo_scores), 0.0, 1.0)
```

#### 2.3.3 Layer 3: Logic Complexity Analyzer
```python
# src/analysis/novelty/logic_complexity.py

import ast
from typing import List, Set
import numpy as np

class LogicComplexityAnalyzer:
    """Analyzes code logic complexity via AST parsing"""

    def parse_strategy_ast(self, code: str) -> ast.Module:
        """Parse strategy code into AST"""
        try:
            # Wrap lambda in function for parsing
            wrapped_code = f"def strategy(df):\n    return {code}"
            tree = ast.parse(wrapped_code)
            return tree
        except SyntaxError as e:
            raise ValueError(f"Failed to parse strategy code: {str(e)}")

    def measure_cyclomatic_complexity(self, ast_node: ast.Module) -> int:
        """Calculate cyclomatic complexity (McCabe metric)"""
        complexity = 1  # Base complexity

        for node in ast.walk(ast_node):
            # Each decision point adds 1
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def detect_nonlinear_patterns(self, ast_node: ast.Module) -> List[str]:
        """Detect non-linear logic patterns"""
        patterns = []

        for node in ast.walk(ast_node):
            # np.where / pd.where (conditional logic)
            if isinstance(node, ast.Call):
                if hasattr(node.func, 'attr') and node.func.attr in ['where', 'select']:
                    patterns.append('conditional_where')

            # Custom function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    # Not a built-in or numpy/pandas function
                    if node.func.id not in ['min', 'max', 'abs', 'sum']:
                        patterns.append('custom_function')

            # Nested conditions
            if isinstance(node, ast.If):
                for child in ast.walk(node):
                    if isinstance(child, ast.If) and child != node:
                        patterns.append('nested_condition')
                        break

            # Lambda functions (higher-order)
            if isinstance(node, ast.Lambda):
                patterns.append('lambda_function')

        return list(set(patterns))

    def score_logic_deviation(self, ast_node: ast.Module, template_baseline: int = 1) -> float:
        """Score deviation from linear template baseline"""
        complexity = self.measure_cyclomatic_complexity(ast_node)
        patterns = self.detect_nonlinear_patterns(ast_node)

        # Complexity score (normalized)
        complexity_score = min((complexity - template_baseline) / 10.0, 0.5)

        # Pattern score
        pattern_score = min(len(patterns) * 0.2, 0.5)

        return np.clip(complexity_score + pattern_score, 0.0, 1.0)

    def score(self, strategy_code: str) -> float:
        """Calculate Layer 3 novelty score"""
        try:
            ast_tree = self.parse_strategy_ast(strategy_code)
            return self.score_logic_deviation(ast_tree)
        except Exception as e:
            # Fallback for unparseable code
            return 0.0
```

#### 2.3.4 Novelty Scorer (Aggregator)
```python
# src/analysis/novelty/novelty_scorer.py

from dataclasses import dataclass
import numpy as np

@dataclass
class NoveltyScores:
    layer1_factor_diversity: float
    layer2_combination_patterns: float
    layer3_logic_complexity: float
    total_score: float

    def to_dict(self) -> dict:
        return {
            'layer1': self.layer1_factor_diversity,
            'layer2': self.layer2_combination_patterns,
            'layer3': self.layer3_logic_complexity,
            'total': self.total_score
        }

class NoveltyScorer:
    """Aggregates 3-layer novelty scores"""

    def __init__(self, config: ExperimentConfig):
        self.weights = config.novelty_weights
        self.layer1 = FactorDiversityAnalyzer("artifacts/factor_graph/templates.json")
        self.layer2 = CombinationPatternDetector("artifacts/factor_graph/templates.json")
        self.layer3 = LogicComplexityAnalyzer()

    def score(self, strategy_code: str) -> NoveltyScores:
        """Calculate comprehensive novelty score"""
        # Individual layer scores
        layer1_score = self.layer1.score(strategy_code)
        layer2_score = self.layer2.score(strategy_code)
        layer3_score = self.layer3.score(strategy_code)

        # Weighted aggregation
        total_score = (
            layer1_score * self.weights['layer1_factor_diversity'] +
            layer2_score * self.weights['layer2_combination_patterns'] +
            layer3_score * self.weights['layer3_logic_complexity']
        )

        return NoveltyScores(
            layer1_factor_diversity=layer1_score,
            layer2_combination_patterns=layer2_score,
            layer3_logic_complexity=layer3_score,
            total_score=total_score
        )

    def validate_independence(self, scores_list: List[NoveltyScores]) -> dict:
        """Validate that layers measure different aspects (correlation < 0.7)"""
        layer1_scores = [s.layer1_factor_diversity for s in scores_list]
        layer2_scores = [s.layer2_combination_patterns for s in scores_list]
        layer3_scores = [s.layer3_logic_complexity for s in scores_list]

        correlations = {
            'layer1_layer2': np.corrcoef(layer1_scores, layer2_scores)[0, 1],
            'layer1_layer3': np.corrcoef(layer1_scores, layer3_scores)[0, 1],
            'layer2_layer3': np.corrcoef(layer2_scores, layer3_scores)[0, 1]
        }

        max_corr = max(abs(c) for c in correlations.values())

        return {
            'correlations': correlations,
            'max_correlation': max_corr,
            'independent': max_corr < 0.7
        }
```

### 2.4 Statistical Analysis Pipeline

#### 2.4.1 Statistical Tests Module
```python
# src/analysis/statistical_tests.py

from dataclasses import dataclass
from typing import List
import numpy as np
from scipy import stats
import pymannkendall as mk

@dataclass
class TestResult:
    statistic: float
    p_value: float
    effect_size: float
    significant: bool
    interpretation: str

def mann_whitney_u_test(
    group_a: List[float],
    group_b: List[float],
    alternative: str = 'two-sided',
    alpha: float = 0.05
) -> TestResult:
    """Mann-Whitney U test for comparing distributions"""
    statistic, p_value = stats.mannwhitneyu(
        group_a, group_b,
        alternative=alternative
    )

    # Calculate effect size (rank-biserial correlation)
    n1, n2 = len(group_a), len(group_b)
    effect_size = 1 - (2*statistic) / (n1 * n2)

    significant = p_value < alpha

    interpretation = (
        f"Group A (n={n1}) vs Group B (n={n2}): "
        f"U={statistic:.2f}, p={p_value:.4f}, r={effect_size:.3f}"
    )

    return TestResult(statistic, p_value, effect_size, significant, interpretation)

def mann_kendall_trend_test(
    time_series: List[float],
    alpha: float = 0.05
) -> TestResult:
    """Mann-Kendall trend test for time series"""
    result = mk.original_test(time_series, alpha=alpha)

    interpretation = (
        f"Trend: {result.trend}, "
        f"tau={result.tau:.3f}, p={result.p:.4f}"
    )

    return TestResult(
        statistic=result.tau,
        p_value=result.p,
        effect_size=abs(result.tau),
        significant=result.p < alpha,
        interpretation=interpretation
    )

def sliding_window_analysis(
    data: List[float],
    window: int = 20
) -> List[dict]:
    """Sliding window statistical analysis"""
    results = []

    for i in range(len(data) - window + 1):
        window_data = data[i:i+window]
        results.append({
            'window_start': i,
            'window_end': i + window,
            'mean': np.mean(window_data),
            'std': np.std(window_data),
            'min': np.min(window_data),
            'max': np.max(window_data),
            'median': np.median(window_data)
        })

    return results
```

## 3. Data Model

### 3.1 Extended IterationRecord
```python
# src/learning/iteration_history.py (extended)

from dataclasses import dataclass, asdict
from typing import Dict, Optional
import json

@dataclass
class IterationRecord:
    iteration_num: int
    strategy_code: str
    metrics: Dict[str, float]

    # NEW FIELDS
    novelty_scores: Dict[str, float]  # {'layer1': 0.5, 'layer2': 0.7, ...}
    experiment_group: str  # 'hybrid', 'fg_only', 'llm_only'
    run_id: Optional[int] = None

    # EXISTING FIELDS (preserved)
    classification_level: Optional[str] = None
    champion_updated: bool = False
    timestamp: Optional[str] = None

    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'IterationRecord':
        """Deserialize from JSON"""
        data = json.loads(json_str)
        return cls(**data)
```

## 4. Visualization Design

### 4.1 Learning Curves
```python
# src/analysis/visualization.py

import matplotlib.pyplot as plt
import seaborn as sns

def plot_learning_curves(results: Dict[str, List[IterationRecord]]) -> plt.Figure:
    """Plot Sharpe ratio learning curves for all groups"""
    fig, ax = plt.subplots(figsize=(12, 6))

    for group_id, records in results.items():
        sharpe_ratios = [r.metrics['sharpe_ratio'] for r in records]
        iterations = range(len(sharpe_ratios))

        ax.plot(iterations, sharpe_ratios, label=group_id, linewidth=2)

    ax.set_xlabel('Iteration', fontsize=12)
    ax.set_ylabel('Sharpe Ratio', fontsize=12)
    ax.set_title('Learning Curves: Sharpe Ratio Over Iterations', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig

def plot_novelty_comparison(results: Dict[str, List[IterationRecord]]) -> plt.Figure:
    """Box plot comparison of novelty scores across groups"""
    fig, ax = plt.subplots(figsize=(10, 6))

    data = []
    labels = []

    for group_id, records in results.items():
        novelty_scores = [r.novelty_scores['total'] for r in records]
        data.append(novelty_scores)
        labels.append(group_id)

    ax.boxplot(data, labels=labels)
    ax.set_ylabel('Novelty Score', fontsize=12)
    ax.set_title('Novelty Score Distribution by Group', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')

    return fig

def plot_sharpe_distributions(results: Dict[str, List[IterationRecord]]) -> plt.Figure:
    """KDE overlay of Sharpe distributions"""
    fig, ax = plt.subplots(figsize=(12, 6))

    for group_id, records in results.items():
        sharpe_ratios = [r.metrics['sharpe_ratio'] for r in records]
        sns.kdeplot(sharpe_ratios, label=group_id, ax=ax, linewidth=2)

    ax.set_xlabel('Sharpe Ratio', fontsize=12)
    ax.set_ylabel('Density', fontsize=12)
    ax.set_title('Sharpe Ratio Distribution Comparison', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig
```

## 5. Error Handling & Validation

### 5.1 Error Handling Strategy
- **Iteration Failures**: Log error, continue execution, track failure rate
- **Validation Errors**: Fail fast on configuration/schema errors
- **Resource Errors**: Graceful degradation, clear error messages
- **Statistical Errors**: Return NaN, log warning, continue analysis

### 5.2 Validation Checkpoints
1. **Pre-execution**: Config validation, dependency checks
2. **Post-infrastructure**: Unit tests for all components
3. **Post-novelty-system**: Validation against champion and templates
4. **Post-dry-run**: End-to-end validation with 15 iterations
5. **Post-pilot**: Go/no-go criteria evaluation

## 6. Performance Considerations

### 6.1 Optimization Strategies
- **Sequential Execution**: Avoid resource contention on single machine
- **Lazy Loading**: Load templates once, reuse across iterations
- **Caching**: Cache AST parsing results for identical code
- **Batch Processing**: Aggregate statistical tests for efficiency

### 6.2 Resource Management
- **Memory**: Stream large result sets, don't load all in memory
- **Storage**: Compress JSON outputs, cleanup intermediate files
- **Logging**: Rotate logs, limit verbosity in production

## 7. Security & Data Integrity

### 7.1 Data Protection
- Atomic file writes to prevent corruption
- JSON schema validation before saving
- Backup before Pilot and Full Study execution

### 7.2 Code Execution Safety
- AST parsing (no eval/exec)
- Sandboxed strategy execution in backtesting engine
- Input validation on all external data

## 8. Testing Strategy

### 8.1 Unit Tests
- All novelty layer analyzers (>80% coverage)
- Statistical test implementations
- Configuration loading and validation
- Data serialization/deserialization

### 8.2 Integration Tests
- End-to-end novelty scoring
- Orchestrator with mock learning system
- Statistical pipeline with synthetic data

### 8.3 Validation Tests
- Champion strategy baseline (novelty > 0.3)
- Template strategy baseline (novelty < 0.15)
- Layer independence (correlation < 0.7)
- Statistical test accuracy vs reference implementations

## 9. Deployment Plan

### 9.1 Pre-Deployment Checklist
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Validation tests passing
- [ ] Dry run successful (15 iterations)
- [ ] Configuration backed up
- [ ] Output directories created
- [ ] Dependencies installed

### 9.2 Execution Sequence
1. **Day 1-3**: Development and testing
2. **Day 4**: Dry run and final validation
3. **Day 5**: Pilot execution
4. **Day 5 evening**: Go/no-go decision
5. **Day 6-7**: Optional Full Study

### 9.3 Rollback Plan
- Restore learning_system.yaml from backup
- Delete experimental output directories
- Revert any code changes if needed
- Document lessons learned
