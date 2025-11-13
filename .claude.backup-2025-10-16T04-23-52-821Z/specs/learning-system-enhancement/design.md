# Design Document: Learning System Enhancement

**Project**: Autonomous Trading Strategy Learning Loop Enhancement
**Version**: 1.1 (Post-Review)
**Date**: 2025-10-07
**Status**: Ready for Implementation
**Review**: ✅ Approved by Gemini 2.5 Pro - See DESIGN_REVIEW_IMPROVEMENTS.md

---

## Executive Summary

This design transforms the autonomous strategy generation loop from a random strategy generator (33% success rate) into an intelligent learning system through three integrated components:

1. **Champion Tracking**: Persistence of best-performing strategies
2. **Performance Attribution**: Automated analysis identifying success/failure factors
3. **Evolutionary Prompts**: LLM constraints preserving proven patterns

**Expected Impact**:
- Success rate: 33% → >60%
- Consistent Sharpe: Achieve >1.2 by iteration 10
- Regression prevention: <10% degradation after champion establishment

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Autonomous Loop System                        │
│                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Strategy   │      │   Backtest   │      │   Metrics    │  │
│  │  Generation  │ ───> │   Execution  │ ───> │  Extraction  │  │
│  │    (LLM)     │      │   (Finlab)   │      │              │  │
│  └──────────────┘      └──────────────┘      └──────┬───────┘  │
│         ▲                                            │           │
│         │                                            ▼           │
│  ┌──────┴───────┐      ┌──────────────┐      ┌──────────────┐  │
│  │ Evolutionary │ <─── │  Performance │ <─── │   Champion   │  │
│  │   Prompts    │      │  Attribution │      │   Tracking   │  │
│  │              │      │              │      │              │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                     │                      │           │
│         └─────────────────────┴──────────────────────┘           │
│                      Learning Feedback Loop                      │
└─────────────────────────────────────────────────────────────────┘
```

### Component Integration

```python
# Autonomous Loop Workflow (Enhanced)
def run_iteration(iteration_num, data):
    # 1. Generate Strategy
    prompt = build_prompt(iteration_num, champion, feedback)
    code = generate_strategy(prompt)

    # 2. Execute Backtest
    result = execute_backtest(code, data)
    metrics = extract_metrics(result)

    # 3. Performance Attribution (NEW)
    if champion:
        attribution = compare_with_champion(code, metrics)
        feedback = build_attributed_feedback(attribution, champion)
    else:
        feedback = build_simple_feedback(metrics)

    # 4. Update Champion (NEW)
    if metrics['sharpe'] >= champion.sharpe * 1.05:
        update_champion(iteration_num, code, metrics)

    # 5. Log Results
    log_iteration(iteration_num, code, metrics, feedback)

    return feedback
```

---

## Component 1: Champion Tracking

### Purpose
Maintain persistent record of best-performing strategy as baseline for comparison and learning.

### Data Structure

```python
@dataclass
class ChampionStrategy:
    """Best-performing strategy across all iterations."""

    iteration_num: int                  # Iteration that produced champion
    code: str                           # Complete strategy code
    parameters: Dict[str, Any]          # Extracted parameters (8 key params)
    metrics: Dict[str, float]           # Performance metrics
    success_patterns: List[str]         # Preservation directives
    timestamp: str                      # ISO 8601 timestamp

    def to_dict(self) -> Dict:
        """Serialize to JSON."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> 'ChampionStrategy':
        """Deserialize from JSON."""
        return ChampionStrategy(**data)
```

### Key Parameters Tracked

| Parameter | Type | Criticality | Example |
|-----------|------|-------------|---------|
| `roe_type` | str | CRITICAL | "smoothed" vs "raw" |
| `roe_smoothing_window` | int | CRITICAL | 4 quarters |
| `liquidity_threshold` | int | CRITICAL | 100,000,000 TWD |
| `revenue_handling` | str | MODERATE | "forward_filled" |
| `value_factor` | str | MODERATE | "inverse_pe" |
| `price_filter` | float | LOW | 10.0 TWD |
| `volume_filter` | int | LOW | 1000 shares |
| `strategy_type` | str | INFO | "momentum_value" |

### Update Logic

```python
def _update_champion(
    self,
    iteration_num: int,
    code: str,
    metrics: Dict[str, float]
) -> bool:
    """Update champion if new strategy exceeds threshold."""

    # First valid strategy becomes champion
    if self.champion is None and metrics['sharpe_ratio'] > 0.5:
        self._create_champion(iteration_num, code, metrics)
        return True

    # Update if 5% improvement
    if self.champion and metrics['sharpe_ratio'] >= self.champion.metrics['sharpe_ratio'] * 1.05:
        self._create_champion(iteration_num, code, metrics)
        return True

    return False

def _create_champion(self, iteration_num: int, code: str, metrics: Dict[str, float]):
    """Create new champion strategy."""
    parameters = extract_strategy_params(code)
    success_patterns = extract_success_patterns(code, parameters)

    self.champion = ChampionStrategy(
        iteration_num=iteration_num,
        code=code,
        parameters=parameters,
        metrics=metrics,
        success_patterns=success_patterns,
        timestamp=datetime.now().isoformat()
    )

    self._save_champion()
    logger.info(f"🏆 New champion: Iteration {iteration_num}, Sharpe {metrics['sharpe_ratio']:.4f}")
```

### Persistence

```python
def _save_champion(self):
    """Persist champion to JSON file."""
    with open('champion_strategy.json', 'w') as f:
        json.dump(self.champion.to_dict(), f, indent=2)

def _load_champion(self) -> Optional[ChampionStrategy]:
    """Load champion from JSON file."""
    if os.path.exists('champion_strategy.json'):
        with open('champion_strategy.json', 'r') as f:
            data = json.load(f)
            return ChampionStrategy.from_dict(data)
    return None
```

---

## Component 2: Performance Attribution

### Purpose
Identify specific code changes that caused performance improvements or regressions.

### Attribution Flow

```
Current Strategy
      │
      ▼
Extract Parameters ──────> 8 Key Parameters
      │
      ▼
Compare with Champion ──> Detect Changes
      │                   • Critical (ROE, liquidity)
      ▼                   • Moderate (revenue, value)
Classify Changes         • Low (price, volume)
      │
      ▼
Assess Performance ─────> Improved / Degraded / Similar
      │
      ▼
Generate Insights ──────> Learning Directives
      │
      ▼
Format Feedback ────────> Structured Text for LLM
```

### Parameter Extraction (Regex-Based MVP)

```python
def extract_strategy_params(code: str) -> Dict[str, Any]:
    """Extract 8 key parameters using regex patterns."""

    params = {}

    # Critical Parameter 1: ROE Smoothing
    roe_rolling_match = re.search(r'roe.*?rolling\(window=(\d+)', code)
    if roe_rolling_match:
        params['roe_type'] = 'smoothed'
        params['roe_smoothing_window'] = int(roe_rolling_match.group(1))
    else:
        params['roe_type'] = 'raw'
        params['roe_smoothing_window'] = 1

    # Critical Parameter 2: Liquidity Threshold
    liquidity_match = re.search(r'(?:trading_value|liquidity).*?>.*?(\d{8,})', code)
    if liquidity_match:
        params['liquidity_threshold'] = int(liquidity_match.group(1))
    else:
        params['liquidity_threshold'] = None

    # Moderate Parameter 3: Revenue Handling
    if 'revenue.*ffill' in code or 'revenue_yoy.*ffill' in code:
        params['revenue_handling'] = 'forward_filled'
    elif 'revenue.*bfill' in code:
        params['revenue_handling'] = 'backward_filled'
    else:
        params['revenue_handling'] = 'raw'

    # ... extract 5 more parameters ...

    return params
```

### Strategy Comparison

```python
def compare_strategies(
    prev_params: Dict[str, Any],
    curr_params: Dict[str, Any],
    prev_metrics: Dict[str, float],
    curr_metrics: Dict[str, float]
) -> Dict[str, Any]:
    """Compare current strategy against champion."""

    changes = []
    critical_changes = []

    # Parameter criticality mapping
    critical_params = ['roe_type', 'roe_smoothing_window', 'liquidity_threshold']
    moderate_params = ['revenue_handling', 'value_factor']

    # Detect changes
    for param, prev_value in prev_params.items():
        curr_value = curr_params.get(param)
        if prev_value != curr_value:
            change = {
                'parameter': param,
                'from': prev_value,
                'to': curr_value,
                'criticality': 'critical' if param in critical_params else 'moderate'
            }
            changes.append(change)

            if param in critical_params:
                critical_changes.append(change)

    # Performance assessment
    sharpe_delta = curr_metrics['sharpe_ratio'] - prev_metrics['sharpe_ratio']
    if sharpe_delta > 0.1:
        assessment = 'improved'
    elif sharpe_delta < -0.1:
        assessment = 'degraded'
    else:
        assessment = 'similar'

    return {
        'changes': changes,
        'critical_changes': critical_changes,
        'performance_delta': sharpe_delta,
        'assessment': assessment
    }
```

### Attribution Feedback Generation

```python
def generate_attribution_feedback(
    attribution: Dict[str, Any],
    current_iter: int,
    champion_iter: int
) -> str:
    """Generate structured feedback for LLM consumption."""

    sections = []

    # Section 1: Performance Summary
    assessment = attribution['assessment']
    delta = attribution['performance_delta']

    if assessment == 'degraded':
        sections.append(f"❌ REGRESSION: Performance degraded (Sharpe Δ: {delta:.4f})")
    elif assessment == 'improved':
        sections.append(f"✅ IMPROVEMENT: Performance improved (Sharpe Δ: {delta:.4f})")
    else:
        sections.append(f"➡️ SIMILAR: No significant change (Sharpe Δ: {delta:.4f})")

    # Section 2: Detected Changes
    critical_changes = attribution['critical_changes']
    if critical_changes:
        sections.append("\n🔥 CRITICAL CHANGES:")
        for change in critical_changes:
            sections.append(f"  • {change['parameter']}:")
            sections.append(f"      From: {change['from']}")
            sections.append(f"      To:   {change['to']}")

    # Section 3: Attribution Insights
    if assessment == 'degraded' and critical_changes:
        sections.append("\n💡 ATTRIBUTION INSIGHTS:")
        sections.append("⚠️ Performance degraded after critical changes:")

        # Link changes to impact
        for change in critical_changes:
            insight = _generate_change_insight(change)
            sections.append(f"  • {insight}")

    # Section 4: Learning Directive
    sections.append("\n🎯 LEARNING DIRECTIVE:")
    sections.append(f"  → Review iteration {champion_iter}'s successful patterns")
    sections.append("  → Preserve proven elements")
    sections.append("  → Make INCREMENTAL improvements, not revolutionary changes")

    return "\n".join(sections)

def _generate_change_insight(change: Dict) -> str:
    """Generate human-readable insight for specific change."""
    param = change['parameter']

    if param == 'roe_type' and change['to'] == 'raw':
        return "Removing ROE smoothing likely increased noise"
    elif param == 'liquidity_threshold' and change['to'] < change['from']:
        return "Relaxing liquidity filter likely reduced stock quality"
    elif param == 'roe_smoothing_window' and change['to'] < change['from']:
        return f"Reducing smoothing window ({change['from']} → {change['to']}) increases volatility"

    return f"{param} changed may have impacted stability"
```

---

## Component 3: Evolutionary Prompts

### Purpose
Constrain LLM to preserve successful strategy patterns while enabling incremental improvements.

### Prompt Structure

```
┌─────────────────────────────────────────────────────────┐
│                    SYSTEM PROMPT                        │
│                   (Base Instructions)                   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              LEARNING FROM SUCCESS                      │
│  • Current Champion: Iteration X, Sharpe Y              │
│  • Success Factors: [extracted patterns]                │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│            MANDATORY REQUIREMENTS                       │
│  1. PRESERVE proven elements:                           │
│     - roe.rolling(window=4).mean()                      │
│     - liquidity > 100,000,000                           │
│  2. Make ONLY incremental improvements                  │
│  3. Explain changes in comments                         │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│        AVOID (from failed iterations)                   │
│  • Removing data smoothing                              │
│  • Relaxing liquidity filters                           │
│  • Over-complicated calculations                        │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│      EXPLORE improvements (preserving above)            │
│  • Fine-tune factor weights                             │
│  • Add quality filters                                  │
│  • Optimize threshold values                            │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│            PREVIOUS ITERATION FEEDBACK                  │
│                (Attribution Analysis)                   │
└─────────────────────────────────────────────────────────┘
```

### Success Pattern Extraction

```python
def extract_success_patterns(
    code: str,
    parameters: Dict[str, Any]
) -> List[str]:
    """Extract preservation directives from champion strategy."""

    patterns = []

    # Pattern 1: ROE Smoothing (CRITICAL)
    if parameters['roe_type'] == 'smoothed':
        window = parameters['roe_smoothing_window']
        patterns.append(
            f"roe.rolling(window={window}).mean() - "
            f"4-quarter smoothing reduces quarterly noise"
        )

    # Pattern 2: Strict Liquidity Filter (CRITICAL)
    if parameters['liquidity_threshold'] and parameters['liquidity_threshold'] >= 100_000_000:
        threshold = parameters['liquidity_threshold']
        patterns.append(
            f"liquidity_filter > {threshold:,} TWD - "
            f"Selects stable, high-volume stocks"
        )

    # Pattern 3: Revenue Handling (MODERATE)
    if parameters['revenue_handling'] == 'forward_filled':
        patterns.append(
            "revenue_yoy.ffill() - "
            "Forward-filled revenue data handles missing values"
        )

    # Pattern 4: Value Factor (MODERATE)
    if parameters.get('value_factor') == 'inverse_pe':
        patterns.append(
            "1 / pe_ratio - "
            "Value factor using inverse P/E ratio"
        )

    # Sort by criticality
    return _prioritize_patterns(patterns)

def _prioritize_patterns(patterns: List[str]) -> List[str]:
    """Sort patterns by criticality."""
    critical_keywords = ['rolling', 'liquidity', 'smoothing']

    critical = [p for p in patterns if any(k in p for k in critical_keywords)]
    moderate = [p for p in patterns if p not in critical]

    return critical + moderate
```

### Evolutionary Prompt Builder

```python
def build_evolutionary_prompt(
    self,
    iteration_num: int,
    champion: Optional[ChampionStrategy],
    feedback_summary: str,
    base_prompt: str
) -> str:
    """Build prompt with champion preservation constraints."""

    # Exploration mode for early iterations or no champion
    if iteration_num < 3 or champion is None:
        return base_prompt + "\n\n" + feedback_summary

    # Diversity forcing every 5th iteration
    if self._should_force_exploration(iteration_num):
        logger.info(f"🎲 Forcing exploration mode (iteration {iteration_num})")
        return base_prompt + "\n\n[EXPLORATION MODE: Try new approaches]\n\n" + feedback_summary

    # Exploitation mode: Build evolutionary prompt
    sections = []

    # Section A: Champion Context
    sections.append("=" * 60)
    sections.append("LEARNING FROM SUCCESS")
    sections.append("=" * 60)
    sections.append(f"CURRENT CHAMPION: Iteration {champion.iteration_num}")
    sections.append(f"Achieved Sharpe: {champion.metrics['sharpe_ratio']:.4f}")
    sections.append("")

    # Section B: Mandatory Preservation
    sections.append("MANDATORY REQUIREMENTS:")
    sections.append("1. PRESERVE these proven success factors:")
    for i, pattern in enumerate(champion.success_patterns, 1):
        sections.append(f"   {i}. {pattern}")
    sections.append("")
    sections.append("2. Make ONLY INCREMENTAL improvements")
    sections.append("   - Adjust weights/thresholds by ±10-20%")
    sections.append("   - Add complementary factors WITHOUT removing proven ones")
    sections.append("   - Explain changes with inline comments")
    sections.append("")

    # Section C: Failure Avoidance
    if iteration_num > 3:
        sections.append("AVOID (from failed iterations):")
        sections.append("   - Removing data smoothing (increases noise)")
        sections.append("   - Relaxing liquidity filters (reduces stability)")
        sections.append("   - Over-complicated multi-factor combinations")
        sections.append("")

    # Section D: Improvement Focus
    sections.append("EXPLORE these improvements (while preserving above):")
    sections.append("   - Fine-tune factor weights (e.g., momentum vs value balance)")
    sections.append("   - Add quality filters (debt ratio, profit margin stability)")
    sections.append("   - Optimize threshold values (within ±20% of current)")
    sections.append("=" * 60)
    sections.append("")

    # Combine: Evolutionary constraints + Base prompt + Feedback
    evolutionary_prompt = "\n".join(sections)
    return evolutionary_prompt + base_prompt + "\n\n" + feedback_summary

def _should_force_exploration(self, iteration_num: int) -> bool:
    """Every 5th iteration: force exploration to prevent local optima."""
    return iteration_num > 0 and iteration_num % 5 == 0
```

---

## Integration Architecture

### Modified autonomous_loop.py

```python
class AutonomousLoop:
    """Enhanced autonomous strategy generation loop with learning."""

    def __init__(self, model: str, max_iterations: int = 10):
        self.model = model
        self.max_iterations = max_iterations
        self.history = IterationHistory()
        self.prompt_builder = PromptBuilder()

        # NEW: Champion tracking
        self.champion: Optional[ChampionStrategy] = self._load_champion()

    def run_iteration(self, iteration_num: int, data) -> Tuple[bool, str]:
        """Execute single iteration with learning enhancement."""

        # Step 1: Build enhanced prompt
        force_exploration = self.prompt_builder.should_force_exploration(iteration_num)
        champion_for_prompt = None if force_exploration else self.champion

        feedback_summary = self._get_previous_feedback(iteration_num)
        prompt = self.prompt_builder.build_prompt(
            iteration_num,
            feedback_summary,
            champion=champion_for_prompt
        )

        # Step 2: Generate strategy
        code = self._generate_strategy(prompt)

        # Step 3: Execute backtest
        success, result = self._execute_backtest(code, data)

        if not success:
            return False, result  # Error message

        # Step 4: Extract metrics
        metrics = self._extract_metrics(result)

        # Step 5: Enhanced feedback with attribution (NEW)
        if self.champion:
            attribution = self._compare_with_champion(code, metrics)
            feedback = self.prompt_builder.build_attributed_feedback(
                attribution,
                iteration_num,
                self.champion
            )
        else:
            feedback = self.prompt_builder.build_simple_feedback(metrics)

        # Step 6: Update champion if improved (NEW)
        champion_updated = self._update_champion(iteration_num, code, metrics)

        # Step 7: Log results
        self.history.log_iteration(iteration_num, code, metrics, feedback)

        return True, feedback

    def _compare_with_champion(
        self,
        current_code: str,
        current_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Compare current strategy with champion."""
        curr_params = extract_strategy_params(current_code)
        return compare_strategies(
            prev_params=self.champion.parameters,
            curr_params=curr_params,
            prev_metrics=self.champion.metrics,
            curr_metrics=current_metrics
        )

    def _update_champion(
        self,
        iteration_num: int,
        code: str,
        metrics: Dict[str, float]
    ) -> bool:
        """Update champion if new strategy exceeds threshold."""
        # First valid strategy becomes champion
        if self.champion is None and metrics['sharpe_ratio'] > 0.5:
            self._create_champion(iteration_num, code, metrics)
            return True

        # Update if 5% improvement
        if self.champion and metrics['sharpe_ratio'] >= self.champion.metrics['sharpe_ratio'] * 1.05:
            self._create_champion(iteration_num, code, metrics)
            return True

        return False

    def _create_champion(self, iteration_num: int, code: str, metrics: Dict[str, float]):
        """Create new champion strategy."""
        parameters = extract_strategy_params(code)
        success_patterns = extract_success_patterns(code, parameters)

        self.champion = ChampionStrategy(
            iteration_num=iteration_num,
            code=code,
            parameters=parameters,
            metrics=metrics,
            success_patterns=success_patterns,
            timestamp=datetime.now().isoformat()
        )

        self._save_champion()
        logger.info(f"🏆 New champion: Iteration {iteration_num}, Sharpe {metrics['sharpe_ratio']:.4f}")

    def _save_champion(self):
        """Persist champion to JSON."""
        with open('champion_strategy.json', 'w') as f:
            json.dump(self.champion.to_dict(), f, indent=2)

    def _load_champion(self) -> Optional[ChampionStrategy]:
        """Load champion from JSON."""
        if os.path.exists('champion_strategy.json'):
            with open('champion_strategy.json', 'r') as f:
                data = json.load(f)
                return ChampionStrategy.from_dict(data)
        return None
```

### Modified prompt_builder.py

```python
class PromptBuilder:
    """Enhanced prompt builder with evolutionary constraints."""

    def build_prompt(
        self,
        iteration_num: int,
        feedback_summary: str,
        champion: Optional[ChampionStrategy] = None
    ) -> str:
        """Build LLM prompt with optional evolutionary constraints."""

        base_prompt = self._get_base_prompt()

        if champion:
            return self.build_evolutionary_prompt(
                iteration_num,
                champion,
                feedback_summary,
                base_prompt
            )
        else:
            return base_prompt + "\n\n" + feedback_summary

    def build_attributed_feedback(
        self,
        attribution: Dict[str, Any],
        iteration_num: int,
        champion: ChampionStrategy
    ) -> str:
        """Generate feedback with performance attribution."""

        # Generate attribution analysis
        feedback = generate_attribution_feedback(
            attribution,
            iteration_num,
            champion.iteration_num
        )

        # Add champion context
        feedback += f"\n\nCURRENT CHAMPION: Iteration {champion.iteration_num}\n"
        feedback += f"Champion Sharpe: {champion.metrics['sharpe_ratio']:.4f}\n"
        feedback += "\nSUCCESS PATTERNS TO PRESERVE:\n"
        for pattern in champion.success_patterns:
            feedback += f"  - {pattern}\n"

        return feedback

    def build_simple_feedback(self, metrics: Dict[str, float]) -> str:
        """Simple feedback for first iteration (no champion)."""
        feedback = []
        feedback.append(f"PERFORMANCE SUMMARY:")
        feedback.append(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.4f}")
        feedback.append(f"  Annual Return: {metrics['annual_return']:.2%}")
        feedback.append(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
        feedback.append("")

        # Basic guidance
        if metrics['sharpe_ratio'] < 1.0:
            feedback.append("SUGGESTION: Aim for Sharpe ratio > 1.0")
            feedback.append("  - Consider risk management (stop loss, position sizing)")
            feedback.append("  - Validate factor quality with IC/ICIR")

        return "\n".join(feedback)

    def build_evolutionary_prompt(
        self,
        iteration_num: int,
        champion: ChampionStrategy,
        feedback_summary: str,
        base_prompt: str
    ) -> str:
        """Build prompt with champion preservation constraints."""
        # See implementation in Component 3 section above
        ...

    def should_force_exploration(self, iteration_num: int) -> bool:
        """Every 5th iteration: force exploration."""
        return iteration_num > 0 and iteration_num % 5 == 0
```

---

## Data Flow

### Complete Iteration Workflow

```
START Iteration N
      │
      ▼
┌─────────────────┐
│ Load Champion   │ ◄── champion_strategy.json
└────────┬────────┘
         │
         ▼
┌─────────────────┐       Champion exists?
│ Build Prompt    │ ───── YES ──> Evolutionary Prompt (with constraints)
└────────┬────────┘   └── NO ──> Base Prompt (exploration)
         │
         ▼
┌─────────────────┐
│ Generate Code   │ ◄── LLM (Claude API)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Execute Backtest│ ◄── Finlab API
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Extract Metrics │
└────────┬────────┘
         │
         ▼
    Champion exists?
         │
    YES  │  NO
     │   │   │
     │   │   └────> Simple Feedback
     │   │
     │   ▼
┌────┴────────────┐
│ Attribution     │ ◄── performance_attributor.py
│ Analysis        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Attributed      │
│ Feedback        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update Champion?│ ◄── Sharpe >= Champion * 1.05?
└────────┬────────┘
         │
    YES  │  NO
     │   │   │
     │   │   └────> Keep existing champion
     │   │
     │   ▼
┌────┴────────────┐
│ Create New      │ ───> champion_strategy.json
│ Champion        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Log Iteration   │ ───> mvp_final_clean_history.json
└────────┬────────┘
         │
         ▼
END Iteration N
```

---

## Performance Considerations

### Time Complexity

| Operation | Complexity | Expected Time |
|-----------|-----------|---------------|
| Champion load/save | O(1) | <50ms |
| Parameter extraction (regex) | O(n) where n=code length | <100ms |
| Strategy comparison | O(p) where p=parameter count | <50ms |
| Attribution feedback generation | O(c) where c=change count | <100ms |
| Pattern extraction | O(p) | <100ms |
| Evolutionary prompt building | O(s) where s=pattern count | <150ms |
| **Total Overhead** | - | **<500ms per iteration** |

### Memory Usage

- Champion strategy: ~10KB (code + metadata)
- Attribution result: ~5KB (temporary)
- Prompt enhancement: ~2KB additional tokens
- **Total Additional Memory**: ~20KB per iteration

### Scalability

- **Current Design**: Single-threaded, sequential iterations
- **Bottleneck**: LLM generation time (30-60s) >> attribution time (<500ms)
- **Overhead Impact**: <1% of total iteration time
- **Future Optimization**: Parallel attribution for multiple strategies (v2.0)

---

## Error Handling

### Failure Scenarios

| Scenario | Detection | Recovery Strategy |
|----------|-----------|-------------------|
| Regex extraction fails | Empty/partial params | Fallback to simple feedback |
| Champion JSON corrupted | JSON parse error | Log error, proceed with None champion |
| Attribution comparison fails | Exception during compare | Use simple feedback, log error |
| Pattern extraction empty | No patterns found | Use generic preservation directive |
| LLM ignores constraints | Detect removed critical params | Attribution flags regression in feedback |

### Error Handling Code

```python
def _compare_with_champion(self, code: str, metrics: Dict) -> Optional[Dict]:
    """Compare with champion, with fallback."""
    try:
        curr_params = extract_strategy_params(code)
        return compare_strategies(
            self.champion.parameters,
            curr_params,
            self.champion.metrics,
            metrics
        )
    except Exception as e:
        logger.error(f"Attribution failed: {e}")
        logger.info("Falling back to simple feedback")
        return None  # Triggers simple feedback path

def _load_champion(self) -> Optional[ChampionStrategy]:
    """Load champion with error handling."""
    try:
        if os.path.exists('champion_strategy.json'):
            with open('champion_strategy.json', 'r') as f:
                data = json.load(f)
                return ChampionStrategy.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(f"Champion load failed: {e}")
        logger.info("Starting with clean champion state")
    return None
```

---

## Testing Strategy

### Unit Tests (25 tests)

#### Champion Tracking (10 tests)
- `test_champion_initializes_as_none`
- `test_first_valid_strategy_becomes_champion`
- `test_champion_updates_when_5percent_improvement`
- `test_champion_doesnt_update_below_threshold`
- `test_champion_persists_to_json`
- `test_champion_loads_from_json`
- `test_champion_handles_negative_sharpe`
- `test_champion_includes_success_patterns`
- `test_champion_update_logs_correctly`
- `test_champion_json_corruption_handled`

#### Attribution Integration (8 tests)
- `test_attribution_detects_critical_changes`
- `test_attribution_detects_moderate_changes`
- `test_first_iteration_uses_simple_feedback`
- `test_regression_triggers_learning_directive`
- `test_improvement_reinforces_patterns`
- `test_similar_performance_neutral_feedback`
- `test_attribution_fallback_on_error`
- `test_multiple_parameter_changes_tracked`

#### Evolutionary Prompts (7 tests)
- `test_patterns_extracted_from_champion`
- `test_roe_smoothing_pattern_preserved`
- `test_liquidity_threshold_pattern_preserved`
- `test_prompt_has_4section_structure`
- `test_exploration_mode_before_iteration_3`
- `test_exploitation_mode_after_iteration_3`
- `test_diversity_forcing_every_5th_iteration`

### Integration Tests (5 scenarios)

#### Scenario 1: Full Learning Loop (Success Case)
```python
def test_full_learning_loop():
    """Test complete 5-iteration learning workflow."""
    loop = AutonomousLoop(model='google/gemini-2.5-flash', max_iterations=5)

    # Iteration 0: No champion
    assert loop.champion is None
    success, feedback = loop.run_iteration(0, data)
    assert success
    assert "PERFORMANCE SUMMARY" in feedback

    # Mock iteration 1 with high Sharpe
    loop.run_iteration(1, data)  # Assume Sharpe 0.97
    assert loop.champion is not None
    assert loop.champion.iteration_num == 1

    # Iteration 3: Should have preservation constraints
    success, feedback = loop.run_iteration(3, data)
    prompt = loop.last_prompt
    assert "PRESERVE these proven success factors" in prompt
    assert "roe.rolling(window=4)" in prompt
```

#### Scenario 2: Regression Prevention
```python
def test_regression_prevention():
    """Test attribution detects and flags regression."""
    loop = AutonomousLoop(...)

    # Establish champion
    loop.champion = create_mock_champion(sharpe=0.97, roe_window=4, liquidity=100_000_000)

    # Generate strategy with degraded parameters
    code_with_regression = "...roe.shift(1)..."  # No smoothing
    metrics_degraded = {'sharpe_ratio': 0.30}

    attribution = loop._compare_with_champion(code_with_regression, metrics_degraded)

    assert attribution['assessment'] == 'degraded'
    assert any(c['parameter'] == 'roe_type' for c in attribution['critical_changes'])

    feedback = loop.prompt_builder.build_attributed_feedback(attribution, 2, loop.champion)
    assert "Removing ROE smoothing likely increased noise" in feedback
```

#### Scenario 3: First Iteration Edge Case
```python
def test_first_iteration_no_champion():
    """Test first iteration handles missing champion gracefully."""
    loop = AutonomousLoop(...)
    assert loop.champion is None

    success, feedback = loop.run_iteration(0, data)
    assert success
    assert "PRESERVE" not in feedback  # No preservation directives
    assert "PERFORMANCE SUMMARY" in feedback
```

#### Scenario 4: Champion Update Cascade
```python
def test_champion_update_cascade():
    """Test champion updates propagate correctly."""
    loop = AutonomousLoop(...)

    # Establish first champion
    loop.run_iteration(1, data)  # Sharpe 0.60
    champion_v1 = loop.champion.iteration_num

    # Better strategy emerges
    loop.run_iteration(3, data)  # Sharpe 1.05
    champion_v2 = loop.champion.iteration_num

    assert champion_v2 == 3
    assert champion_v2 != champion_v1

    # Next iteration should reference new champion
    success, feedback = loop.run_iteration(4, data)
    assert f"Iteration {champion_v2}" in feedback
```

#### Scenario 5: Premature Convergence (Diversity Forcing)
```python
def test_diversity_forcing():
    """Test exploration mode activates every 5th iteration."""
    loop = AutonomousLoop(...)
    loop.champion = create_mock_champion(sharpe=1.00)

    # Iteration 5: Should force exploration
    prompt = loop.prompt_builder.build_prompt(5, "", champion=loop.champion)
    assert "EXPLORATION MODE" in prompt
    assert "PRESERVE" not in prompt  # Constraints removed

    # Iteration 6: Back to exploitation
    prompt = loop.prompt_builder.build_prompt(6, "", champion=loop.champion)
    assert "PRESERVE" in prompt
```

### Validation Test (10-iteration run)

```python
def run_10iteration_validation():
    """Validate against success criteria."""
    loop = AutonomousLoop(model='google/gemini-2.5-flash', max_iterations=10)

    sharpes = []
    for i in range(10):
        success, feedback = loop.run_iteration(i, data)
        metrics = loop.history.get_metrics(i)
        sharpes.append(metrics['sharpe_ratio'])

    # Success Criteria (need 3/4 to pass)
    best_sharpe = max(sharpes)
    success_rate = sum(1 for s in sharpes if s > 0.5) / len(sharpes)
    avg_sharpe = sum(sharpes) / len(sharpes)

    # Check regression after champion
    if loop.champion:
        champion_idx = loop.champion.iteration_num
        post_champion = sharpes[champion_idx+1:]
        if post_champion:
            worst_regression = min(post_champion) - loop.champion.metrics['sharpe_ratio']
            regression_pct = worst_regression / loop.champion.metrics['sharpe_ratio']
        else:
            regression_pct = 0.0

    # Report
    criteria = {
        '1. Best Sharpe >1.2': best_sharpe > 1.2,
        '2. Success rate >60%': success_rate > 0.6,
        '3. Avg Sharpe >0.5': avg_sharpe > 0.5,
        '4. No regression >10%': regression_pct > -0.10
    }

    passed = sum(criteria.values())
    print(f"\nValidation Results: {passed}/4 criteria passed")
    for criterion, result in criteria.items():
        print(f"  {'✅' if result else '❌'} {criterion}")

    return passed >= 3
```

---

## Security Considerations

### Input Validation
- **Champion JSON**: Validate schema on load, handle malformed data
- **Regex Extraction**: Sandboxed pattern matching, no code execution
- **File Operations**: Atomic writes, proper file permissions

### Code Execution Safety
- **No Change**: Attribution system doesn't execute user code
- **Existing Sandbox**: Backtest execution uses existing sandbox (unchanged)
- **LLM Output**: Already validated by existing AST checks

---

## Monitoring and Observability

### Logging Strategy

```python
import logging

logger = logging.getLogger('autonomous_loop.learning')

# Key Events to Log
logger.info(f"🏆 New champion: Iteration {iter}, Sharpe {sharpe:.4f}")
logger.info(f"📊 Attribution: {len(changes)} changes detected, {assessment}")
logger.warning(f"⚠️ Regression detected: Sharpe {prev:.4f} → {curr:.4f}")
logger.info(f"🎲 Forcing exploration mode (iteration {iter})")
logger.error(f"❌ Attribution failed: {error}")
```

### Metrics to Track

| Metric | Purpose | Target |
|--------|---------|--------|
| Champion update frequency | Learning progress | 2-3 updates per 10 iterations |
| Attribution accuracy | Validation quality | >90% critical param detection |
| Regression incidents | System robustness | <1 per 10 iterations |
| Pattern preservation rate | LLM compliance | >80% preservation |
| Average Sharpe improvement | Overall effectiveness | +50% vs baseline |

---

## Deployment Strategy

### Phase 2 Rollout (Week 1)

1. **Day 1-2**: Implement champion tracking
   - Modify `autonomous_loop.py`
   - Add unit tests
   - Validate with historical data

2. **Day 3-4**: Integrate attribution
   - Connect to `performance_attributor.py`
   - Build attributed feedback
   - Test comparison logic

3. **Day 5**: Enhanced feedback generation
   - Implement feedback methods in `prompt_builder.py`
   - Manual testing with real iterations

### Phase 3 Rollout (Week 2)

1. **Day 1-2**: Pattern extraction
   - Implement success pattern extraction
   - Test with iteration 1 code
   - Validate preservation directives

2. **Day 3-4**: Evolutionary prompts
   - Build 4-section prompt structure
   - Add diversity forcing
   - Test exploration vs exploitation modes

3. **Day 5**: Full integration
   - End-to-end 5-iteration test
   - Verify no regressions
   - Document any issues

### Phase 4 Validation (Week 3)

1. **Day 1-2**: Complete unit tests (25 total)
2. **Day 3**: Integration tests (5 scenarios)
3. **Day 4**: 10-iteration validation run
4. **Day 5**: Documentation and polish

---

## Future Enhancements (v2.0)

### Advanced Attribution (Phase 5)
- Migrate from regex to AST-based parameter extraction
- Factor interaction analysis (which combinations work)
- Incremental value attribution (quantify each factor's contribution)

### Evolution Manager (Phase 4)
- Dynamic exploit/explore balance
- Multi-objective optimization (Sharpe + drawdown + win rate)
- Adaptive constraint strength based on results

### Knowledge Graph Integration (Phase 7)
- Hybrid JSON (fast) + Graphiti MCP (deep reasoning)
- Long-term pattern accumulation across sessions
- Market regime adaptation insights
- Cross-strategy learning and transfer

---

## References

### Existing Components
- `performance_attributor.py`: Phase 1 (completed)
- `autonomous_loop.py`: Core loop implementation
- `prompt_builder.py`: Prompt generation logic
- `history.py`: Iteration history management
- `validate_code.py`: AST security validation
- `sandbox_simple.py`: Backtest execution sandbox

### External Dependencies
- **Python Standard Library**: json, re, typing, dataclasses, datetime, logging, os
- **Finlab API**: Data retrieval and backtesting
- **Anthropic Claude API**: Strategy code generation

### Documentation
- `SPEC_LEARNING_SYSTEM_ENHANCEMENT.md`: Detailed implementation plan
- `ARCHITECTURE.md`: System architecture overview
- `README.md`: User guide and quick start
- `API_REFERENCE.md`: API documentation

---

**Design Version**: 1.0
**Status**: Ready for Implementation
**Next Step**: Begin Phase 2.1 (Champion Tracking)
**Estimated Completion**: 3 weeks
