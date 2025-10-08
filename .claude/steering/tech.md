# Technical Steering Document

## Technology Stack

### Core Technologies
- **Language**: Python 3.8+
- **AI Integration**: Claude API (google/gemini-2.5-flash via OpenRouter)
- **Data Warehouse**: DuckDB (local, high-performance)
- **Testing**: pytest, unittest.mock
- **Data Source**: Finlab API (Taiwan stock market)

### Key Libraries
```python
# AI & API
openai          # OpenRouter client for Claude access
httpx           # HTTP client for API calls

# Data Processing
pandas          # Time series analysis
numpy           # Numerical operations
duckdb          # Local data warehouse

# Backtesting
finlab          # Taiwan stock market backtesting library
backtesting     # Strategy backtesting engine

# Testing
pytest          # Test framework
pytest-cov      # Code coverage
```

## Architecture Decisions

### 1. **Local-First Data Architecture**
**Decision**: Use DuckDB for local data warehouse instead of cloud database

**Rationale**:
- Personal use system (個人使用) - no need for cloud complexity
- Sub-second query performance for backtest data
- Zero latency for data access
- No recurring cloud costs
- Full offline capability after initial data download

**Trade-offs**:
- No multi-user support
- Manual data backup required
- Limited to single machine

### 2. **Regex-Based Parameter Extraction (MVP)**
**Decision**: Use regex patterns for strategy parameter extraction instead of AST

**Rationale**:
- 80/20 solution: 80% accuracy with 20% effort
- Critical parameters (ROE smoothing, liquidity) extract reliably
- Fast implementation (30 min vs 2 hours for AST)
- Sufficient for MVP validation
- AST migration planned for v2.0

**Trade-offs**:
- 80% extraction success rate vs 95% with AST
- Brittle to unusual code formatting
- Manual regex pattern maintenance
- Limited to simple parameter types

### 3. **Atomic Write-Rename Pattern**
**Decision**: Use tempfile + os.replace() for champion and failure pattern persistence

**Rationale**:
- POSIX-guaranteed atomicity prevents data corruption
- Handles concurrent access and crashes safely
- No external dependencies (uses Python stdlib)
- Prevents race conditions in multi-process scenarios

**Implementation**:
```python
# Atomic write pattern
temp_fd, temp_path = tempfile.mkstemp(dir=dir_path, prefix='.champion_')
with os.fdopen(temp_fd, 'w') as f:
    json.dump(data, f)
os.replace(temp_path, target_path)  # Atomic on POSIX
```

### 4. **LLM Preservation Validation**
**Decision**: Post-generation validation with tolerance thresholds instead of constrained generation

**Rationale**:
- Claude API doesn't support hard constraints
- Validation faster than regeneration retry loops
- Allows ±20% variation for incremental improvements
- Enables learning from validation failures

**Validation Logic**:
```python
# Critical Check 1: ROE Type Preservation
if champion_params['roe_type'] == 'smoothed':
    if generated_params['roe_type'] != 'smoothed': return False

    # Allow ±20% variation in smoothing window
    window_deviation = abs(generated_window - champion_window) / champion_window
    if window_deviation > 0.2: return False

# Critical Check 2: Liquidity Threshold ≥80% of champion
if generated_liq < champion_liq * 0.8: return False
```

### 5. **Probation Period for Champion Updates**
**Decision**: 10% threshold for champions <2 iterations old, 5% threshold after

**Rationale**:
- Prevents champion churn from statistical noise
- Higher bar for new champions to prove stability
- Reduces false positives from lucky random variations
- Allows system to settle on stable champions

**Implementation**:
```python
if iteration_num - champion.iteration_num <= 2:
    required_improvement = 1.10  # 10% probation
else:
    required_improvement = 1.05  # 5% standard
```

### 6. **Failure Pattern Pruning**
**Decision**: Return only 20 most recent failure patterns instead of all patterns

**Rationale**:
- Prevents unbounded growth in prompt token consumption
- Prioritizes recent learnings (more relevant to current champion)
- Older patterns remain in storage for potential future analysis
- Keeps prompt size manageable (<2K tokens for patterns)

**Implementation**:
```python
def get_avoid_directives(self, max_patterns: int = 20) -> List[str]:
    sorted_patterns = sorted(
        self.patterns,
        key=lambda p: p.iteration_discovered,
        reverse=True
    )
    recent_patterns = sorted_patterns[:max_patterns]
    return [p.to_avoid_directive() for p in recent_patterns]
```

### 7. **Diversity Forcing Every 5th Iteration**
**Decision**: Force exploration mode every 5th iteration to prevent local optima

**Rationale**:
- Prevents system from over-fitting to single strategy family
- Empirically validated frequency (not yet A/B tested)
- Balances exploitation (incremental improvements) with exploration (new approaches)
- Mitigates LLM non-compliance risk

**Trade-offs**:
- Iteration 5, 10, 15 potentially waste champion knowledge
- Frequency not empirically optimized (future A/B test needed)
- May break winning streaks

### 8. **JSON for Persistence Instead of SQL**
**Decision**: Use JSON files for champion and failure pattern storage

**Rationale**:
- Simple schema (no complex relationships)
- Human-readable for debugging
- No database overhead
- Easy backup/restore
- Atomic write-rename pattern works well with files

**Trade-offs**:
- No ACID transactions
- No query optimization
- Manual schema versioning
- Concurrent access requires file locking

## Performance Constraints

### Target Performance
- **Attribution Analysis**: <100ms per iteration
- **Champion Persistence**: <50ms (save/load)
- **Pattern Extraction**: <200ms per strategy
- **Total Overhead**: <500ms per iteration
- **Backtest Execution**: 30-120s (Finlab library bottleneck)

### Memory Constraints
- **Champion Data**: ~10KB JSON per champion
- **Failure Patterns**: ~1KB per pattern × 20 max = 20KB
- **Iteration History**: ~5KB per iteration × 100 max = 500KB
- **Total Memory**: <1MB for learning system state

## Security Constraints

### Code Validation
- **Anti-lookahead**: Detect .shift() with negative values
- **Import Blocking**: No import statements allowed (data.get() provides all data)
- **Dangerous Functions**: Block exec(), eval(), compile()
- **Execution Sandbox**: Isolated process with timeout (120s)

### Data Security
- **API Tokens**: Environment variables only (never hardcoded)
- **Local Storage**: All data stored locally (no cloud uploads)
- **No PII**: System processes only public market data

## Testing Strategy

### Unit Tests (25 tests - ✅ Passing)
- **Champion Tracking**: 10 tests (initialization, update threshold, persistence, edge cases)
- **Attribution Integration**: 8 tests (comparison logic, first iteration, regression detection)
- **Evolutionary Prompts**: 7 tests (pattern extraction, 4-section structure, exploration mode)

### Integration Tests (5 scenarios - ✅ Passing)
1. Full learning loop (success case)
2. Regression prevention workflow
3. First iteration edge case
4. Champion update cascade
5. Premature convergence (diversity forcing)

### Pattern Extraction Tests (20 tests - ✅ Passing)
- Critical parameter extraction (ROE, liquidity)
- Moderate parameter extraction (revenue, value factor)
- Regex robustness (whitespace, scientific notation, underscores)

### Code Coverage
- **Target**: >80% for new code
- **Current**: ~85% (champion tracking, attribution, prompts)

## Development Workflow

### Dependency Management
```bash
# Development
pip install -r requirements.txt

# Testing
pytest tests/ -v --cov=src --cov=. --cov-report=term-missing

# Type Checking (not enforced)
mypy src/ autonomous_loop.py performance_attributor.py
```

### Testing Commands
```bash
# Unit tests only
pytest tests/test_*.py -v

# Integration tests
pytest tests/test_integration_scenarios.py -v

# Specific test file
pytest tests/test_evolutionary_prompts.py -v --tb=short

# With coverage
pytest tests/ -v --cov=src --cov-report=html
```

### Git Workflow
```bash
# Feature branch
git checkout -b feature/learning-system-enhancement

# Commit conventions
git commit -m "feat: Add champion tracking (Tasks 4-9)"
git commit -m "fix: Resolve atomic write race condition (P0)"
git commit -m "test: Add integration scenarios (Task 29)"

# Production hardening
git commit -m "hardening: Implement atomic persistence, LLM validation, pattern pruning"
```

## Environment Setup

### Required Environment Variables
```bash
# Finlab API (Taiwan stock data)
export FINLAB_API_TOKEN='your_finlab_token'

# OpenRouter API (Claude access)
export OPENROUTER_API_KEY='your_openrouter_key'
```

### Configuration Files
- **config/settings.py**: System configuration
- **.claude/specs/**: Specification documents (requirements, design, tasks)
- **.claude/steering/**: Steering documents (this directory)

## Migration Path

### Phase 2 → Phase 3 (AST Migration)
**Goal**: Improve parameter extraction from 80% → 95%

**Steps**:
1. Implement AST-based extraction in performance_attributor.py
2. Run A/B test: Regex vs AST extraction accuracy
3. Gradual migration with fallback to regex
4. Deprecate regex patterns after validation

**Estimated Effort**: 2 hours implementation + 1 hour testing

### Phase 3 → Phase 4 (Graphiti Integration)
**Goal**: Add knowledge graph for cross-strategy pattern recognition

**Steps**:
1. Install Graphiti library
2. Create entity extraction (strategies, parameters, patterns)
3. Build graph relationships (success→pattern, pattern→parameter)
4. Add temporal queries for historical analysis

**Estimated Effort**: 8 hours implementation + 4 hours testing

## Future Improvements

### Planned
- AST-based extraction (Phase 3)
- Preservation retry logic (30 min)
- TTL-based pattern storage pruning (1 hour)
- Empirical diversity forcing tuning (4 hours A/B test)

### Optional
- Multi-model ensemble (compare Claude, GPT-4, Gemini)
- Real-time data streaming (vs batch updates)
- Web UI for monitoring (Streamlit dashboard)
- Multi-market support (expand beyond Taiwan)
