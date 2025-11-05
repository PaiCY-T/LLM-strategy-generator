# Template Integration Process

**Comprehensive guide to the template system integration with the autonomous learning loop**

Version: 1.0.0 | Status: Production | Last Updated: 2025-10-16

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Template System Components](#template-system-components)
- [Integration Flow](#integration-flow)
- [Exploration Mode](#exploration-mode)
- [Template Diversity Tracking](#template-diversity-tracking)
- [Fallback Mechanisms](#fallback-mechanisms)
- [Error Handling](#error-handling)
- [Code Examples](#code-examples)
- [Migration from Hardcoded Strategies](#migration-from-hardcoded-strategies)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The template integration system replaced the hardcoded Value_PE strategy generator with an intelligent, adaptive template recommendation system. This enables the autonomous loop to explore diverse strategy architectures while leveraging proven patterns from champion strategies.

### Key Features

- **Intelligent Recommendation**: Performance-based template selection using Sharpe ratio tiers
- **Champion Integration**: Leverages Hall of Fame strategies for parameter suggestions
- **Forced Exploration**: Every 5th iteration tests new templates for diversity
- **Diversity Tracking**: Monitors recent template usage to prevent repetition
- **Fallback System**: Graceful degradation with retry logic (max 3 attempts)
- **Template Match Scoring**: Analyzes strategy code to identify best-fit templates

### Success Metrics

- **Strategy Diversity**: 80%+ unique strategies (8/10 iterations)
- **Template Diversity**: 4+ unique templates in recent 20 iterations
- **Success Rate**: TurtleTemplate proven 80% success rate
- **Performance**: <100ms recommendation latency

---

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│               Autonomous Loop (iteration_engine.py)            │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Step 1: Generate Strategy                           │    │
│  │    └─→ generate_strategy(iteration, feedback)        │    │
│  │           └─→ claude_code_strategy_generator.py      │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│           Strategy Generator (claude_code_strategy_generator)  │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Iteration < 20: Momentum Testing Phase              │    │
│  │    └─→ _generate_momentum_strategy()                 │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Iteration >= 20: Template-Based Generation          │    │
│  │    ┌────────────────────────────────────────────┐    │    │
│  │    │  1. Initialize TemplateFeedbackIntegrator  │    │    │
│  │    │  2. Load iteration history                 │    │    │
│  │    │  3. Analyze template diversity             │    │    │
│  │    │  4. Get recommendation                     │    │    │
│  │    │  5. Verify exploration mode                │    │    │
│  │    │  6. Instantiate template                   │    │    │
│  │    │  7. Generate strategy code                 │    │    │
│  │    │  8. Retry on failure (max 3 attempts)      │    │    │
│  │    └────────────────────────────────────────────┘    │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│        TemplateFeedbackIntegrator (src.feedback)              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  recommend_template()                                │    │
│  │    ├─→ Check exploration mode (iteration % 5 == 0)   │    │
│  │    ├─→ Performance-based recommendation              │    │
│  │    ├─→ Champion parameter enhancement                │    │
│  │    ├─→ Validation feedback incorporation             │    │
│  │    ├─→ Template match scoring                        │    │
│  │    └─→ Track template usage                          │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Template Registry                                   │    │
│  │    ├─→ TurtleTemplate (80% success)                  │    │
│  │    ├─→ MastiffTemplate (65% success)                 │    │
│  │    ├─→ FactorTemplate (70% success)                  │    │
│  │    └─→ MomentumTemplate (60% success)                │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│          Hall of Fame Repository (champion strategies)         │
└───────────────────────────────────────────────────────────────┘
```

---

## Template System Components

### 1. TemplateFeedbackIntegrator

**Core recommendation engine** from `src.feedback.TemplateFeedbackIntegrator`

**Responsibilities:**
- Analyze current performance metrics
- Recommend optimal template based on Sharpe tier
- Suggest parameters from champion strategies
- Enforce exploration mode every 5th iteration
- Track template usage for diversity

**Key Methods:**
- `recommend_template()`: Main recommendation orchestrator
- `get_champion_template_params()`: Retrieve champion parameters
- `calculate_template_match_score()`: Score architecture similarity
- `_recommend_by_performance()`: Performance-based selection
- `_recommend_exploration_template()`: Diversity-driven selection

**Performance Thresholds:**
```python
HIGH_SHARPE_THRESHOLD = 2.0    # Champion tier
MEDIUM_SHARPE_THRESHOLD = 1.5  # Contender tier
LOW_SHARPE_THRESHOLD = 1.0     # Archive tier
```

**Template Success Rates:**
```python
TurtleTemplate: 80%   # 6-layer AND filtering, proven robust
MastiffTemplate: 65%  # Concentrated contrarian strategies
FactorTemplate: 70%   # Single-factor stable returns
MomentumTemplate: 60% # Fast iteration and testing
```

### 2. Template Classes

**Four core templates** providing different strategy architectures:

#### TurtleTemplate
- **Success Rate**: 80% (highest proven)
- **Architecture**: 6-layer AND filtering
- **Best For**: Sharpe 0.5-1.5, robust multi-factor strategies
- **Key Features**: Revenue growth + price strength + volume + risk management
- **Selection Method**: `.is_largest()` for top performers

#### MastiffTemplate
- **Success Rate**: 65%
- **Architecture**: 6 contrarian conditions
- **Best For**: Concentrated high-conviction positions
- **Key Features**: Contrarian volume selection, value focus
- **Selection Method**: `.is_smallest()` for undervalued stocks

#### FactorTemplate
- **Success Rate**: 70%
- **Architecture**: Single-factor cross-sectional ranking
- **Best For**: Stable low-volatility returns, Sharpe 0.8-1.3
- **Key Features**: Simple factor ranking, consistent performance
- **Selection Method**: `.rank()` for normalized scoring

#### MomentumTemplate
- **Success Rate**: 60%
- **Architecture**: Momentum + catalyst combination
- **Best For**: Rapid iteration, fast feedback cycles
- **Key Features**: Price momentum, volume confirmation
- **Selection Method**: `.is_largest()` for momentum leaders

### 3. Exploration Mode Controller

**Forced diversity mechanism** activates every 5th iteration.

**Configuration:**
```python
EXPLORATION_FREQUENCY = 5  # Every 5th iteration
EXPLORATION_INTERVAL = 5   # Same as frequency
```

**Logic:**
```python
is_exploration = (iteration % EXPLORATION_INTERVAL == 0)
```

**Behavior:**
- Selects template different from recent 3 iterations
- Uses least-recently-used (LRU) selection when all used recently
- Expands parameter ranges to ±30% for broader exploration
- Marks recommendation with `exploration_mode=True`

### 4. Diversity Tracking

**Monitors recent template usage** to prevent over-fitting to single architecture.

**Configuration:**
```python
RECENT_HISTORY_WINDOW = 5      # Track last 5 iterations
LOW_DIVERSITY_THRESHOLD = 0.4  # Warning threshold
```

**Metrics Tracked:**
- Recent template list (sliding window of 5)
- Unique template count
- Diversity score = unique / total
- Warning when diversity < 40%

**Implementation:**
```python
def _analyze_template_diversity(iteration_history: list) -> list:
    """Analyze template diversity from recent iterations."""
    recent_templates = []
    recent_entries = iteration_history[-RECENT_HISTORY_WINDOW:]

    for entry in recent_entries:
        template = entry.get('template')
        if template:
            recent_templates.append(template)

    unique_count = len(set(recent_templates))
    total_count = len(recent_templates)
    diversity_score = unique_count / total_count

    if diversity_score < LOW_DIVERSITY_THRESHOLD:
        logger.warning(f"Low diversity: {diversity_score:.1%}")

    return recent_templates
```

---

## Integration Flow

### Step-by-Step Process

#### Step 1: Momentum Testing Phase (Iterations 0-19)

**Purpose**: Establish baseline performance before template system activation.

```python
if iteration < TEMPLATE_GENERATION_START_ITERATION:  # 20
    code = _generate_momentum_strategy(iteration)
    return code.strip()
```

**Momentum Variations Tested:**
- Iterations 0-4: Different lookback periods (10d, 20d, 40d, 60d, 120d)
- Iterations 5-6: Moving average crossovers (SMA20/60, SMA5/20)
- Iterations 7-8: Rate of change momentum
- Iterations 9-10: Relative strength vs market
- Iterations 11-12: Multi-timeframe momentum
- Iterations 13-14: Volume confirmation momentum
- Iterations 15-16: Volatility-adjusted momentum
- Iterations 17-18: Acceleration/deceleration momentum
- Iteration 19: Residual momentum (vs sector)

#### Step 2: Template Initialization (Iteration >= 20)

**Initialize integrator and load history:**

```python
integrator = TemplateFeedbackIntegrator()
iteration_history = _load_iteration_history()
recent_templates = _analyze_template_diversity(iteration_history)
```

#### Step 3: Extract Current Metrics

**Get most recent successful iteration metrics:**

```python
feedback_data = {'current_metrics': None, 'iteration': iteration}

if iteration_history:
    for entry in reversed(iteration_history):
        if entry.get('success', False) and entry.get('metrics'):
            feedback_data['current_metrics'] = entry['metrics']
            logger.info(f"Using metrics from iteration {entry.get('iteration')}")
            break
```

#### Step 4: Get Template Recommendation

**Call recommendation engine:**

```python
recommendation = integrator.recommend_template(
    current_metrics=feedback_data['current_metrics'],
    iteration=iteration,
    validation_result=feedback_data.get('validation_result')
)

logger.info(
    f"Template selected: {recommendation.template_name} | "
    f"Exploration: {recommendation.exploration_mode} | "
    f"Match score: {recommendation.match_score:.2f}"
)
```

**Recommendation includes:**
- `template_name`: Selected template (e.g., 'Turtle', 'Mastiff')
- `rationale`: Human-readable explanation
- `match_score`: Confidence level (0.0-1.0)
- `suggested_params`: Parameter dictionary
- `exploration_mode`: Boolean exploration flag
- `champion_reference`: Optional champion genome ID

#### Step 5: Verify Exploration Mode

**Ensure exploration mode matches expectation:**

```python
is_exploration = (iteration % EXPLORATION_INTERVAL == 0)

if is_exploration and not recommendation.exploration_mode:
    logger.warning("Exploration mode mismatch")
elif not is_exploration and recommendation.exploration_mode:
    logger.warning("Unexpected exploration mode")
else:
    logger.info("Exploration mode verified")
```

#### Step 6: Verify Template Diversity

**In exploration mode, ensure template is different from recent:**

```python
if is_exploration and recent_templates:
    if recommendation.template_name in recent_templates:
        logger.warning(
            f"Diversity violation: {recommendation.template_name} "
            f"used in recent {len(recent_templates)} iterations"
        )
    else:
        logger.info("Template diversity verified")
```

#### Step 7: Instantiate Template

**Get template class and instantiate:**

```python
TEMPLATE_MAPPING = {
    'Turtle': TurtleTemplate,
    'Mastiff': MastiffTemplate,
    'Factor': FactorTemplate,
    'Momentum': MomentumTemplate
}

template_class = TEMPLATE_MAPPING[recommendation.template_name]
template_instance = template_class()
```

#### Step 8: Generate Strategy Code

**Call template's generate_strategy() with suggested parameters:**

```python
code = template_instance.generate_strategy(**recommendation.suggested_params)
logger.info(f"Strategy code generated: {len(code)} chars")
```

---

## Exploration Mode

### Activation Logic

**Exploration mode activates automatically every 5th iteration:**

```python
EXPLORATION_FREQUENCY = 5

def _should_force_exploration(iteration: int) -> bool:
    """Check if forced exploration should activate."""
    is_exploration = (iteration % EXPLORATION_FREQUENCY) == 0

    if is_exploration:
        logger.info(f"⚡ EXPLORATION MODE activated at iteration {iteration}")

    return is_exploration
```

**Examples:**
- Iteration 5: Exploration ✓
- Iteration 10: Exploration ✓
- Iteration 15: Exploration ✓
- Iteration 7: Standard mode
- Iteration 12: Standard mode

### Template Selection in Exploration

**Selects template different from recent 3 iterations:**

```python
def _recommend_exploration_template(iteration: int, exclude_recent: int = 3):
    """Recommend template for exploration mode."""
    # Get recent templates
    recent_templates = iteration_history[-exclude_recent:]

    # Get all available templates
    all_templates = ['TurtleTemplate', 'MastiffTemplate',
                     'FactorTemplate', 'MomentumTemplate']

    # Filter out recently used
    candidates = [t for t in all_templates if t not in recent_templates]

    # If all used recently, use all templates
    if not candidates:
        candidates = all_templates

    # Select least-used template
    template_usage = {t: recent_templates.count(t) for t in all_templates}
    selected = min(candidates, key=lambda t: template_usage.get(t, 0))

    return TemplateRecommendation(
        template_name=selected,
        rationale=f"⚡ EXPLORATION MODE: Testing {selected} for diversity",
        match_score=0.65,
        exploration_mode=True
    )
```

### Parameter Range Expansion

**Exploration mode uses broader parameter ranges (±30%):**

```python
# Standard mode: Use champion parameters directly
base_value = 10
suggested_params = {'n_stocks': base_value}

# Exploration mode: Expand range by ±30%
lower = int(base_value * 0.70)  # 7
upper = int(base_value * 1.30)  # 13
# Uses expanded range for broader exploration
```

---

## Template Diversity Tracking

### Recent History Window

**Tracks last 5 iterations to monitor diversity:**

```python
RECENT_HISTORY_WINDOW = 5

def _analyze_template_diversity(iteration_history: list) -> list:
    """Analyze template diversity from recent iterations."""
    recent_entries = iteration_history[-RECENT_HISTORY_WINDOW:]

    recent_templates = []
    for entry in recent_entries:
        template = entry.get('template')
        if template:
            recent_templates.append(template)

    return recent_templates
```

### Diversity Metrics

**Calculated metrics:**

```python
unique_templates = len(set(recent_templates))
total_templates = len(recent_templates)
diversity_score = unique_templates / total_templates

logger.info(
    f"Template diversity (last {total_templates} iterations): "
    f"{unique_templates}/{total_templates} unique = {diversity_score:.1%}"
)
```

**Example outputs:**
- `[Turtle, Mastiff, Factor, Turtle, Momentum]` → 4/5 = 80% diversity ✓
- `[Turtle, Turtle, Turtle, Turtle, Mastiff]` → 2/5 = 40% diversity ⚠
- `[Turtle, Turtle, Turtle, Turtle, Turtle]` → 1/5 = 20% diversity ⚠

### Low Diversity Warning

**Warning threshold configured at 40%:**

```python
LOW_DIVERSITY_THRESHOLD = 0.4

if diversity_score < LOW_DIVERSITY_THRESHOLD and total >= RECENT_HISTORY_WINDOW:
    logger.warning(
        f"Low template diversity ({diversity_score:.1%} < {LOW_DIVERSITY_THRESHOLD:.1%}). "
        f"Consider enabling exploration mode."
    )
```

---

## Fallback Mechanisms

### Three-Level Fallback System

#### Level 1: Normal Template Recommendation

**Primary path using TemplateFeedbackIntegrator:**

```python
try:
    integrator = TemplateFeedbackIntegrator()
    recommendation = integrator.recommend_template(
        current_metrics=metrics,
        iteration=iteration
    )
    code = _instantiate_and_generate(
        recommendation.template_name,
        recommendation.suggested_params
    )
except Exception as e:
    # Fall through to Level 2
```

#### Level 2: Random Template Selection

**Fallback when recommendation system fails:**

```python
def _select_fallback_template(recent_templates: list) -> str:
    """Select fallback template when recommendation fails."""
    all_templates = set(['Turtle', 'Mastiff', 'Factor', 'Momentum'])
    recent_set = set(recent_templates)

    # Strategy 1: LRU if all used recently
    if len(recent_set) == len(all_templates):
        template_positions = {}
        for template in all_templates:
            last_idx = len(recent_templates) - 1 - recent_templates[::-1].index(template)
            template_positions[template] = last_idx

        selected = min(template_positions.items(), key=lambda x: x[1])[0]
        logger.info(f"LRU selection: {selected}")
        return selected

    # Strategy 2: Random from unused
    available = list(all_templates - recent_set)
    selected = random.choice(available if available else list(all_templates))
    logger.info(f"Random selection: {selected}")
    return selected
```

#### Level 3: Retry Logic with Different Templates

**Max 3 retry attempts with template tracking:**

```python
MAX_RETRIES = 3
attempted_templates = []

for retry_attempt in range(1, MAX_RETRIES + 1):
    logger.info(f"Attempt {retry_attempt}/{MAX_RETRIES}")

    try:
        # Get recommendation (or fallback)
        recommended_template = get_template()

        # Track attempt
        if recommended_template not in attempted_templates:
            attempted_templates.append(recommended_template)

        # Try to generate
        code = _instantiate_and_generate(recommended_template, params)
        break  # Success

    except Exception as e:
        if retry_attempt < MAX_RETRIES:
            logger.warning(f"Retry {retry_attempt} failed: {e}")
            continue  # Next attempt
        else:
            logger.error(f"All {MAX_RETRIES} attempts failed")
            raise RuntimeError(
                f"Failed after {MAX_RETRIES} attempts. "
                f"Attempted: {attempted_templates}"
            )
```

---

## Error Handling

### Template Instantiation Errors

**Handle template class instantiation failures:**

```python
try:
    template_class = TEMPLATE_MAPPING[template_name]
    template_instance = template_class()
except KeyError:
    raise ValueError(f"Unknown template: {template_name}")
except Exception as e:
    logger.error(f"Instantiation failed: {e}")
    raise
```

### Code Generation Errors

**Handle strategy code generation failures:**

```python
try:
    code = template_instance.generate_strategy(**suggested_params)

    if not code or len(code.strip()) < 50:
        raise ValueError("Generated code too short or empty")

    if "position" not in code and "signal" not in code:
        logger.warning("Missing position/signal variable")

except Exception as e:
    logger.error(f"Generation failed: {e}")
    raise
```

### Validation Feedback Integration

**Adjust parameters based on validation errors:**

```python
def _adjust_params_for_validation(params: Dict, errors: List):
    """Adjust parameters to resolve validation errors."""
    adjusted = params.copy()

    for error in errors:
        msg = str(error.message).lower()

        # n_stocks range errors
        if 'n_stocks' in msg:
            if 'n_stocks' in adjusted:
                current = adjusted['n_stocks']
                if current < 10:
                    adjusted['n_stocks'] = 10
                elif current > 30:
                    adjusted['n_stocks'] = 30

        # stop_loss range errors
        if 'stop_loss' in msg:
            if 'stop_loss' in adjusted:
                current = adjusted['stop_loss']
                if current < 0.05:
                    adjusted['stop_loss'] = 0.06
                elif current > 0.15:
                    adjusted['stop_loss'] = 0.12

    return adjusted
```

---

## Code Examples

### Example 1: Basic Template Integration

```python
from src.feedback import TemplateFeedbackIntegrator
from src.templates.turtle_template import TurtleTemplate

# Initialize integrator
integrator = TemplateFeedbackIntegrator()

# Get recommendation
recommendation = integrator.recommend_template(
    current_metrics={'sharpe_ratio': 0.8},
    iteration=1
)

print(f"Template: {recommendation.template_name}")
# Output: TurtleTemplate

print(f"Rationale: {recommendation.rationale}")
# Output: Sharpe 0.80 in target range 0.5-1.0: TurtleTemplate proven 80% success rate...

# Instantiate template
template = TurtleTemplate()
code = template.generate_strategy(**recommendation.suggested_params)
```

### Example 2: Exploration Mode Detection

```python
# Check if exploration mode should activate
iteration = 10
is_exploration = (iteration % 5 == 0)

if is_exploration:
    print(f"⚡ EXPLORATION MODE at iteration {iteration}")
    # System will select diverse template
else:
    print(f"Standard recommendation at iteration {iteration}")
    # System will use performance-based selection
```

### Example 3: Champion Parameter Integration

```python
from src.repository import HallOfFameRepository

# Initialize with Hall of Fame
repository = HallOfFameRepository()
integrator = TemplateFeedbackIntegrator(repository=repository)

# Get recommendation (automatically enhanced with champion parameters)
recommendation = integrator.recommend_template(
    current_metrics={'sharpe_ratio': 1.8},
    iteration=3
)

if recommendation.champion_reference:
    print(f"Based on champion: {recommendation.champion_reference}")
    print(f"Champion parameters: {recommendation.suggested_params}")
```

### Example 4: Complete Integration in Learning Loop

```python
from src.feedback import TemplateFeedbackIntegrator
from artifacts.working.modules.claude_code_strategy_generator import TEMPLATE_MAPPING

def run_iteration(iteration: int, current_metrics: dict):
    """Run single iteration with template integration."""

    # Step 1: Get recommendation
    integrator = TemplateFeedbackIntegrator()
    recommendation = integrator.recommend_template(
        current_metrics=current_metrics,
        iteration=iteration
    )

    print(f"[Iteration {iteration}] Template: {recommendation.template_name}")
    print(f"Exploration mode: {recommendation.exploration_mode}")

    # Step 2: Instantiate template
    template_class = TEMPLATE_MAPPING[recommendation.template_name]
    template = template_class()

    # Step 3: Generate strategy
    code = template.generate_strategy(**recommendation.suggested_params)

    # Step 4: Execute and extract metrics
    success, metrics, error = execute_strategy(code)

    # Step 5: Return for next iteration
    return success, metrics, recommendation.template_name

# Run 10 iterations
current_metrics = {'sharpe_ratio': 0.0}
for i in range(1, 11):
    success, metrics, template = run_iteration(i, current_metrics)
    if success:
        current_metrics = metrics
```

---

## Migration from Hardcoded Strategies

### Before (Hardcoded Value_PE Strategy)

**Old approach in `claude_code_strategy_generator.py`:**

```python
# Lines 372-405 (REMOVED)
def generate_value_pe_strategy():
    """Generate hardcoded Value + PE strategy."""
    code = """
# Value + PE Strategy (Hardcoded)
from finlab import data
from finlab import backtest

# Always same strategy
pe_ratio = data.get('fundamental_features:pe_ratio')
price = data.get('price:收盤價')

cond1 = pe_ratio < 15
cond2 = price > 10

position = (cond1 & cond2).is_largest(10)
report = backtest.sim(position, resample="M")
"""
    return code
```

**Problems with old approach:**
- No strategy diversity
- No learning from previous iterations
- No adaptation based on performance
- Same template every iteration
- Limited exploration of strategy space

### After (Template-Based System)

**New approach with TemplateFeedbackIntegrator:**

```python
# Task 1: Import TemplateFeedbackIntegrator
from src.feedback import TemplateFeedbackIntegrator

# Task 2: Template recommendation call
integrator = TemplateFeedbackIntegrator()
recommendation = integrator.recommend_template(
    current_metrics=current_metrics,
    iteration=iteration
)

# Task 3: Instantiate recommended template
template_class = TEMPLATE_MAPPING[recommendation.template_name]
template = template_class()

# Task 4: Generate strategy with suggested parameters
code = template.generate_strategy(**recommendation.suggested_params)
```

**Benefits of new approach:**
- 4 diverse templates (Turtle, Mastiff, Factor, Momentum)
- Performance-based selection (7 Sharpe tiers)
- Champion parameter suggestions
- Forced exploration every 5th iteration
- Diversity tracking and warnings
- Retry logic with fallback system

### Migration Steps

#### Step 1: Remove Hardcoded Generator

```python
# REMOVED: Lines 372-405 in claude_code_strategy_generator.py
# def generate_value_pe_strategy():
#     ...
```

#### Step 2: Import Template System

```python
from src.feedback import TemplateFeedbackIntegrator
from src.templates.turtle_template import TurtleTemplate
from src.templates.mastiff_template import MastiffTemplate
from src.templates.factor_template import FactorTemplate
from src.templates.momentum_template import MomentumTemplate
```

#### Step 3: Create Template Registry

```python
TEMPLATE_MAPPING = {
    'Turtle': TurtleTemplate,
    'Mastiff': MastiffTemplate,
    'Factor': FactorTemplate,
    'Momentum': MomentumTemplate
}
```

#### Step 4: Implement Template Integration

See "Integration Flow" section above for complete implementation.

---

## Best Practices

### 1. Template Selection

**Use performance-based selection:**
- Sharpe 0.5-1.0 → TurtleTemplate (80% success)
- Sharpe 1.0-1.5 → TurtleTemplate or FactorTemplate
- Sharpe 1.5-2.0 → TurtleTemplate (contender tier)
- Sharpe > 2.0 → Champion-based selection

**Enable exploration mode:**
- Let system automatically trigger every 5th iteration
- Don't override exploration mode unless necessary
- Monitor diversity metrics in logs

### 2. Parameter Configuration

**Use champion parameters when available:**
```python
recommendation = integrator.recommend_template(
    current_metrics=metrics,
    iteration=iteration
)

# recommendation.suggested_params already includes champion parameters
# if available from Hall of Fame
```

**Validate parameter ranges:**
```python
# Ensure parameters are within safe ranges
if 'n_stocks' in params:
    params['n_stocks'] = max(5, min(30, params['n_stocks']))

if 'stop_loss' in params:
    params['stop_loss'] = max(0.05, min(0.15, params['stop_loss']))
```

### 3. Error Handling

**Always use retry logic:**
```python
MAX_RETRIES = 3

for attempt in range(1, MAX_RETRIES + 1):
    try:
        code = template.generate_strategy(**params)
        break
    except Exception as e:
        if attempt < MAX_RETRIES:
            logger.warning(f"Retry {attempt}/{MAX_RETRIES}: {e}")
            continue
        else:
            raise
```

**Log template selection details:**
```python
logger.info(
    f"Template selected: {recommendation.template_name} | "
    f"Exploration: {recommendation.exploration_mode} | "
    f"Match score: {recommendation.match_score:.2f} | "
    f"Iteration: {iteration}"
)
```

### 4. Diversity Monitoring

**Track template usage:**
```python
# System automatically tracks in TemplateFeedbackIntegrator
integrator.track_iteration(recommendation.template_name)

# Get usage statistics
stats = integrator.get_template_statistics()
print(f"Template usage: {stats['usage_distribution']}")
```

**Monitor diversity warnings:**
```python
recent_templates = _analyze_template_diversity(iteration_history)
unique = len(set(recent_templates))
diversity = unique / len(recent_templates)

if diversity < 0.4:
    logger.warning(f"Low diversity: {diversity:.1%}")
```

### 5. Champion Integration

**Initialize with Hall of Fame:**
```python
from src.repository import HallOfFameRepository

repository = HallOfFameRepository()
integrator = TemplateFeedbackIntegrator(repository=repository)

# Champion parameters automatically included in recommendations
```

**Check champion reference:**
```python
if recommendation.champion_reference:
    print(f"Based on champion: {recommendation.champion_reference}")
    print(f"Champion Sharpe: {recommendation.suggested_params.get('champion_sharpe')}")
```

---

## Troubleshooting

### Issue 1: Exploration Mode Not Activating

**Symptom:** Exploration mode never triggers despite iteration % 5 == 0

**Diagnosis:**
```python
iteration = 10
is_exploration = (iteration % 5 == 0)
print(f"Should be exploration: {is_exploration}")  # Should print True
```

**Solution:**
- Verify EXPLORATION_INTERVAL = 5 in configuration
- Check logs for "⚡ EXPLORATION MODE activated"
- Ensure recommendation.exploration_mode is checked

### Issue 2: Low Template Diversity

**Symptom:** Same template used repeatedly (diversity < 40%)

**Diagnosis:**
```python
recent_templates = _analyze_template_diversity(iteration_history)
unique = len(set(recent_templates))
print(f"Recent templates: {recent_templates}")
print(f"Unique: {unique}/{len(recent_templates)}")
```

**Solution:**
- Check exploration mode is activating every 5 iterations
- Verify fallback template selection uses LRU strategy
- Review logs for diversity warnings

### Issue 3: Template Instantiation Failures

**Symptom:** "Template instantiation failed" errors

**Diagnosis:**
```python
try:
    template_class = TEMPLATE_MAPPING['Turtle']
    template = template_class()
except Exception as e:
    print(f"Instantiation error: {e}")
```

**Solution:**
- Verify template imports are correct
- Check TEMPLATE_MAPPING dictionary is complete
- Ensure template classes have default constructors
- Review template dependencies (data imports, etc.)

### Issue 4: Parameter Range Violations

**Symptom:** Validation errors about parameter values

**Diagnosis:**
```python
params = recommendation.suggested_params
print(f"Parameters: {params}")

# Check ranges
if 'n_stocks' in params:
    print(f"n_stocks={params['n_stocks']} (valid: 5-30)")
```

**Solution:**
- Use _adjust_params_for_validation() for automatic adjustment
- Add parameter validation before template instantiation
- Review champion parameter ranges in Hall of Fame

### Issue 5: Missing Champion Parameters

**Symptom:** recommendation.champion_reference is None

**Diagnosis:**
```python
from src.repository import HallOfFameRepository

repository = HallOfFameRepository()
champions = repository.get_champions(min_sharpe=1.5)
print(f"Champions found: {len(champions)}")
```

**Solution:**
- Ensure Hall of Fame has champion strategies (Sharpe >= 1.5)
- Initialize integrator with repository parameter
- Check repository base_path is correct
- Verify champion strategies are properly saved

---

## Summary

The template integration system provides intelligent, adaptive strategy generation for the autonomous learning loop. Key benefits include:

- **Diversity**: 4 templates with different architectures
- **Intelligence**: Performance-based selection using Sharpe tiers
- **Exploration**: Automatic diversity enforcement every 5th iteration
- **Champion Integration**: Leverages proven parameter combinations
- **Robustness**: Three-level fallback system with retry logic
- **Transparency**: Comprehensive logging and rationale generation

**System Impact:**
- Strategy diversity: 80%+ (8/10 unique)
- Template diversity: 4+ templates in recent 20 iterations
- Success rate: TurtleTemplate 80% proven
- Performance: <100ms recommendation latency

**For more information, see:**
- `src/feedback/template_feedback.py`: Core recommendation engine
- `docs/architecture/FEEDBACK_SYSTEM.md`: Complete API reference
- `tests/feedback/test_template_feedback_integration.py`: Integration tests
- `.spec-workflow/specs/system-fix-validation-enhancement/tasks.md`: Implementation tasks
