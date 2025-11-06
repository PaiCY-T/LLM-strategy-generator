# Technology Stack

## Project Type

**Command-Line Intelligent Trading System** with autonomous strategy generation and optimization capabilities.

Primary characteristics:
- Headless autonomous loop (no GUI required)
- Batch processing workflow (iteration-based)
- JSON/YAML-based configuration and persistence
- CLI tools for data management and monitoring
- Optional web dashboard for visualization (future)

## Core Technologies

### Primary Language(s)
- **Language**: Python 3.10+
- **Runtime**: CPython 3.10.0 or higher
- **Package Manager**: pip (requirements.txt-based)
- **Build Tools**:
  - wheel for distribution
  - build for packaging
  - setuptools (implicit)

**Version Policy**: Minimum Python 3.10 for modern type hints, structural pattern matching, and performance improvements.

### Key Dependencies/Libraries

#### Trading & Financial Data
- **finlab ≥1.5.3**: Core Taiwan market data API, backtesting engine, technical indicators
- **pandas ≥2.3.2**: DataFrame operations, time series analysis
- **numpy ≥2.2.0**: Numerical computations, array operations
- **scipy ≥1.15.0**: Statistical functions, optimization algorithms
- **scikit-learn ≥1.7.0**: Machine learning utilities, clustering
- **TA-Lib ≥0.6.7**: Technical analysis indicators (requires system library)
- **yfinance ≥0.2.60**: Alternative data source for validation
- **pandas-market-calendars ≥5.1.0**: Trading calendar support

#### AI/LLM Integration ⭐ **CORE TECHNOLOGY**
**LLM-driven innovation is the primary capability for Stage 2 (>80% success, >2.5 Sharpe)**

- **anthropic ≥0.69.0**: Claude API client (primary strategy generation via InnovationEngine)
- **google-generativeai ≥0.8.5**: Gemini API (fast YAML generation, structured innovation)
- **openai ≥2.2.0**: OpenAI API (o3, GPT-5, o4-mini for reasoning)
- **aiohttp ≥3.12.0**: Async HTTP for concurrent LLM API calls
- **httpx ≥0.28.0**: Alternative HTTP client with HTTP/2 support

**Current Status**: ✅ Fully implemented (Phase 2-3 complete), ⏳ Activation pending
- InnovationEngine: src/innovation/innovation_engine.py
- Structured YAML pipeline: YAMLSchemaValidator, YAMLToCodeGenerator
- 7-layer validation framework: Syntax → Semantic → Security → Backtestability → Metrics → Multi-Objective → Baseline
- Configuration: config/learning_system.yaml:708 (`llm.enabled: false` by default)

#### Strategy Optimization
- **deap ≥1.4.3**: Genetic algorithms (DEPRECATED: replaced by hybrid LLM + Factor Graph evolution)
- **statsmodels ≥0.14.5**: Statistical validation, time series analysis
- **networkx ≥3.4.0**: Factor graph representation, dependency analysis

**Hybrid Innovation Model** (Design: 20% LLM + 80% Factor Graph):
- LLM innovation: Structural creativity, novel factor combinations (every 5th iteration)
- Factor Graph: Safe fallback with 13 predefined factors (Momentum, Value, Quality, Risk, Entry, Exit)
- Auto-fallback: LLM failures → automatic Factor Graph mutation

#### Configuration & Validation
- **PyYAML ≥6.0.0**: YAML configuration files (learning_system.yaml)
- **pydantic ≥2.11.0**: Data validation, settings management
- **python-dotenv ≥1.1.0**: Environment variable management

#### Data Storage & Caching
- **SQLAlchemy ≥2.0.43**: ORM for metadata storage (future)
- **duckdb ≥1.4.0**: Analytical queries on iteration history (future)
- **redis ≥5.1.0**: Caching layer (future)
- **JSON**: Primary persistence format (iteration_history.jsonl, hall_of_fame/*.json)
- **fastparquet ≥2024.11.0**: Parquet format for large datasets
- **pyarrow ≥21.0.0**: Apache Arrow for columnar data

### Application Architecture

**Three-Layer Architecture** - LLM-Driven Autonomous Learning System:

```
┌───────────────────────────────────────────────────────────────────┐
│  ⚙️ LEARNING LOOP LAYER (EXECUTION ENGINE)                       │
│  src/learning/ - Phase 3-6 implementation (4,200 lines, 7 modules)│
│  ────────────────────────────────────────────────────────────────│
│  • learning_loop.py: Main orchestrator (10-step process)          │
│  • iteration_executor.py: Step-by-step execution                  │
│  • champion_tracker.py: Best strategy tracking                    │
│  • iteration_history.py: JSONL persistence                        │
│  • feedback_generator.py: Context generation for LLM              │
│  • llm_client.py: Multi-provider LLM abstraction                  │
│  • learning_config.py: 21-parameter configuration                 │
│  ────────────────────────────────────────────────────────────────│
│  Status: ✅ Complete (88% coverage, A grade, 86.7% complexity ↓)  │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                         │ Step 3: Decide innovation mode
                         │ (20% LLM / 80% Factor Graph)
                         ▼
┌───────────────────────────────────────────────────────────────────┐
│  🤖 LLM INNOVATION LAYER (CORE - Intelligence Source)            │
│  src/innovation/ - Phase 2-3 implementation (~5000+ lines)        │
│  ────────────────────────────────────────────────────────────────│
│  • innovation_engine.py: LLM-driven strategy generation           │
│  • llm_provider.py: OpenRouter/Gemini/OpenAI integration          │
│  • prompt_builder.py: Context-aware prompts                       │
│  • security_validator.py: Code safety checks                      │
│  • validators/: 7-layer validation framework                      │
│    - Syntax → Semantic → Security → Backtestability →            │
│      Metrics → Multi-Objective → Baseline                         │
│  ────────────────────────────────────────────────────────────────│
│  Structured YAML Mode: 90%+ success (vs 60% full code)           │
│  Status: ✅ Implemented, ⏳ Activation pending (llm.enabled=false)│
└────────────────────────┬──────────────────────────────────────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         20% LLM    80% Factor     Validation
              │       Graph         Pipeline
              ▼          ▼              │
       ┌──────────┐ ┌──────────┐       │
       │Templates │ │Evolution │       │
       │ System   │ │ System   │       │
       └────┬─────┘ └────┬─────┘       │
            │            │             │
            └──────┬─────┴────┬────────┘
                   │          │
                   ▼          ▼
┌───────────────────────────────────────────────────────────────────┐
│  📊 VALIDATION LAYER (QUALITY GATE - Safety Assurance)           │
│  src/validation/ - v1.2 Production Ready                          │
│  ────────────────────────────────────────────────────────────────│
│  • Bootstrap confidence intervals (Politis & Romano 1994)         │
│  • Walk-forward analysis (temporal stability)                     │
│  • Baseline comparison (0050 ETF, Equal Weight, Risk Parity)     │
│  • Bonferroni correction (multiple comparison adjustment)         │
│  • Out-of-sample validation (train/val/test 2018-2024)           │
│  ────────────────────────────────────────────────────────────────│
│  Status: ✅ Integrated with iteration_executor.py (Step 5-7)      │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                    ┌────▼──────────┐
                    │  Backtest      │
                    │  Engine        │
                    │  (finlab)      │
                    └────┬───────────┘
                         │
                    ┌────▼───────────┐
                    │ Data Layer     │
                    │ (Finlab API)   │
                    └────────────────┘
```

**Why This Architecture**:
- **Learning Loop** (⚙️): Orchestrates the entire autonomous iteration process, managing state and workflow
- **LLM Innovation** (🤖): Provides structural intelligence to break framework limitations (20% innovation rate)
- **Validation** (📊): Ensures statistical robustness and quality through multi-layer validation

**Without LLM (Stage 1)**: 70% success, 1.15 Sharpe, 19-day plateau → limited to 13 predefined factors
**With LLM (Stage 2 Target)**: >80% success, >2.5 Sharpe → continuous structural innovation

**Key Architectural Patterns**:
1. **Repository Pattern**: Hall of Fame, Iteration History
2. **Strategy Pattern**: Template system (Turtle, Mastiff, Factor, Momentum)
3. **Factory Pattern**: Factor creation, template instantiation
4. **Observer Pattern**: Monitoring, variance tracking
5. **Chain of Responsibility**: Metric extraction fallback (DIRECT → SIGNAL → DEFAULT)

### Integration Testing Framework (v1.0) 🧪 **Production Ready** (2025-11-02)

**Purpose**: Prevent integration failures through systematic boundary validation, ensuring components work correctly when integrated together.

**Architecture**: Three-tier testing strategy (Unit → Integration → E2E)

**Core Components**:

1. **Characterization Tests** (`tests/integration/`)
   - Purpose: Establish baseline behavior before changes
   - Coverage: Autonomous loop end-to-end execution
   - Validation: Complete iteration cycle with metrics extraction

2. **Unit Tests** (`tests/unit/`)
   - Purpose: Test components in isolation
   - Coverage: LLM config validation, Docker executor, metrics extraction
   - Mocking: External dependencies (Docker API, LLM APIs)

3. **Integration Tests** (`tests/integration/`)
   - Purpose: Verify data flows at integration boundaries
   - Key Boundaries:
     - LLM generation → Code assembly
     - Code assembly → Docker execution
     - Docker execution → Metrics extraction
     - Exception handling → State propagation

4. **Dataset Key Validation** (2025-11-02)
   - **Three-Layer Defense System**:
     - Layer 1: Prompt Templates (primary prevention) - All 4 templates corrected
     - Layer 2: Auto-Fixer (safety net) - Enhanced with 8 new mappings
     - Layer 3: Static Validation (final check) - Validates against 334 keys
   - **Dataset Key Auto-Fixer** (`artifacts/working/modules/fix_dataset_keys.py`):
     - Common mistakes: `price:收盤價 → etl:adj_close`, `price:本益比 → price_earning_ratio:本益比`
     - Performance: 100% correction rate for known patterns
   - **Available Datasets** (`available_datasets.txt`): 334 keys synchronized with finlab_database_cleaned.csv

5. **Diagnostic Instrumentation**
   - Purpose: Debug integration failures quickly
   - Coverage: LLM initialization, code assembly, Docker execution, metrics extraction
   - Format: Debug-level logs at all integration boundaries

**Status**:
- ✅ **Integration Testing Complete**: All 4 critical bugs fixed (2025-11-02)
- ✅ **Prompt Templates Fixed**: 100% dataset key correctness (30/30 generations)
- ✅ **Auto-Fixer Enhanced**: 8 new mappings for edge cases
- ✅ **Static Validation**: 100% validation success rate
- 📖 **Specification**: docker-integration-test-framework (archived)

**Critical Fixes Applied** (2025-11-02):
1. ✅ Prompt template dataset key mismatch (all 4 templates corrected)
2. ✅ F-string template evaluation before Docker execution
3. ✅ LLM API routing configuration validation
4. ✅ Exception handling state propagation
5. ✅ Configuration snapshot module creation

### Validation Framework (v1.2) 📊 **Production Ready** (2025-11-02)

**Purpose**: Ensure strategies meet statistical robustness requirements before production deployment, preventing overfitting and false positives from random market noise.

**Status**: ✅ **PHASE 2 INTEGRATION COMPLETE** (9/9 tasks, 2025-11-02)
- ✅ All validation frameworks integrated into backtest pipeline
- ✅ Out-of-sample validation (train/val/test splits)
- ✅ Walk-forward analysis (temporal stability)
- ✅ Baseline comparison (Taiwan market benchmarks)
- ✅ Bootstrap confidence intervals (statistical significance)
- ✅ Bonferroni correction (multiple comparison adjustment)
- ✅ Explicit date range configuration (2018-2024, 7-year validation)
- ✅ Transaction cost modeling (Taiwan market defaults)
- 📖 **Specification**: phase2-validation-framework-integration (archived)

**Core Components** (`src/validation/`):

1. **Stationary Bootstrap** (`stationary_bootstrap.py`)
   - Implementation: Politis & Romano (1994) method
   - Purpose: Generate confidence intervals preserving time-series autocorrelation
   - Key feature: Geometric block length (~22 days) maintains serial dependence
   - Metrics: Sharpe Ratio, CAGR, Max Drawdown, Total Return
   - Validation: scipy-compatible (7.1% difference), 100% empirical coverage

2. **Dynamic Threshold Calculator** (`dynamic_threshold.py`)
   - Implementation: Market benchmark-based adaptive thresholds
   - Benchmark: 0050.TW (Taiwan 50 ETF)
   - Formula: `threshold = max(benchmark_sharpe + margin, static_floor)`
   - Current: `0.8 = max(0.6 + 0.2, 0.0)` (v1.2 uses empirical constant)
   - Rationale: Active strategies must beat passive benchmark by 0.2 Sharpe

3. **Integration Layer** (`integration.py` - 1050 lines)
   - **ValidationIntegrator**: Out-of-sample and walk-forward analysis
     - Train/Val/Test splits: 2018-2020 / 2021-2022 / 2023-2024
     - Overfitting detection: Test Sharpe < 0.7 * Train Sharpe
     - Stability scoring: Sharpe variance across rolling windows
   - **BaselineIntegrator**: Benchmark comparison
     - Taiwan market baselines: 0050 ETF, Equal Weight, Risk Parity
     - Sharpe improvement metrics vs each baseline
   - **BootstrapIntegrator**: Statistical validation with confidence intervals
     - Block bootstrap preserving autocorrelation
     - 95% confidence level (configurable)
   - **BonferroniIntegrator**: Multiple comparison correction
     - Family-wise error rate control (5% alpha)
     - Adjusted alpha for multi-strategy validation (α/n)
     - Dynamic thresholds based on Taiwan market benchmark
   - **Backward compatible**: v1.0 mode via `use_dynamic_threshold=False`

4. **Reporting** (`validation_report.py` - 611 lines, `validation_report_generator.py` - 726 lines)
   - Comprehensive validation reports (JSON/HTML)
   - All validation results consolidated
   - Used by `run_phase2_with_validation.py`

5. **BacktestExecutor Enhancements** (`src/backtest/executor.py`)
   - Explicit date range: `start_date`, `end_date` parameters (default: 2018-2024)
   - Transaction costs: `fee_ratio` (0.001425), `tax_ratio` (0.003) Taiwan defaults
   - Position filtering: `position.loc[start_date:end_date]`

**Integration in Pipeline**:
```python
# Phase 2 Backtest Execution with Full Validation
BacktestExecutor(start_date="2018-01-01", end_date="2024-12-31", fee_ratio=0.001425)
  → ValidationIntegrator.validate_out_of_sample()
  → ValidationIntegrator.validate_walk_forward()
  → BaselineIntegrator.compare_with_baselines()
  → BootstrapIntegrator.validate_with_bootstrap()
  → BonferroniIntegrator.validate_single_strategy()
  → ValidationReportGenerator.generate_report()
```

**Validation Capabilities**:
1. **Out-of-Sample**: 3-period split, overfitting detection, consistency scoring
2. **Walk-Forward**: Rolling window analysis, stability metrics
3. **Baseline Comparison**: Beat 0050 ETF requirement, alpha metrics
4. **Bootstrap CI**: 95% confidence intervals for Sharpe/Return/Drawdown
5. **Bonferroni**: Multiple comparison correction, family-wise error control

**Design Rationale**:
- **Why Stationary Bootstrap**: Financial returns exhibit autocorrelation and volatility clustering, traditional bootstrap assumes i.i.d. (invalid)
- **Why Dynamic Thresholds**: Static 0.5 Sharpe ignores Taiwan market conditions, dynamic threshold adapts to market regime
- **Why Taiwan 0050.TW**: Representative passive benchmark for Taiwan market, active strategies must outperform to justify trading costs
- **Why 7-Year Range**: Sufficient data for train/val/test splits (3yr/2yr/2yr) with robust statistics

**Known Limitations**:
- v1.2 uses empirical constant (0.6) for benchmark Sharpe (real-time data fetching planned for v2.0)
- Block length auto-calculated, no manual override (sufficient for current use cases)
- Limited to 4 metrics (Sharpe, CAGR, Max DD, Total Return), Sortino/Calmar planned for v2.0

### Data Storage (if applicable)

#### Primary Storage
- **Format**: JSON/JSONL (human-readable, git-friendly)
- **Locations**:
  - `iteration_history.jsonl`: Sequential iteration log
  - `hall_of_fame/*.json`: Champion strategies
  - `template_analytics.json`: Usage statistics
  - `rollback_history.json`: Rollback audit trail
- **Rationale**: Simple, debuggable, no external DB dependencies

#### Caching
- **Type**: File-based cache (data/ directory)
- **Scope**: Finlab API responses (price, fundamental data)
- **Freshness**: 7-day default, configurable
- **Compression**: lz4, cramjam for large datasets

#### Data Formats
- **Configuration**: YAML (learning_system.yaml)
- **Metrics Export**: JSON (human/machine-readable), Prometheus text format
- **Code Persistence**: Python source code (generated_strategy_*.py)
- **Checkpoints**: JSON (baseline_checkpoints/, validation_checkpoints/)

### External Integrations (if applicable)

#### APIs
1. **Finlab API** (Primary)
   - **Purpose**: Taiwan stock market data, backtesting
   - **Protocol**: HTTPS/REST
   - **Authentication**: API token (FINLAB_API_TOKEN env var)
   - **Rate Limits**: Managed by finlab SDK
   - **Error Handling**: Exponential backoff (5s, 10s, 20s, 40s)

2. **Claude API** (Anthropic)
   - **Purpose**: Strategy code generation, parameter optimization
   - **Protocol**: HTTPS/REST
   - **Authentication**: API key (CLAUDE_API_KEY env var)
   - **Models Used**: claude-sonnet-4-5-20250929 (primary)
   - **Streaming**: Supported for real-time generation feedback

3. **Gemini API** (Google)
   - **Purpose**: Fast parameter generation, template recommendation
   - **Protocol**: HTTPS/REST + gRPC
   - **Authentication**: API key (GOOGLE_API_KEY env var)
   - **Models Used**: gemini-2.5-flash (fast), gemini-2.5-pro (deep reasoning)

4. **OpenRouter API** (Optional)
   - **Purpose**: Access to multiple LLM providers (GPT-5, o3, Grok)
   - **Protocol**: HTTPS/REST
   - **Authentication**: API key

#### Protocols
- **HTTP/REST**: Primary API communication
- **gRPC**: Google APIs (Protocol Buffers)
- **WebSocket**: Future dashboard real-time updates
- **JSON-RPC**: Internal module communication (future)

#### Authentication
- **API Keys**: Environment variables (.env file)
- **Token Storage**: Never committed to git (.gitignore enforced)
- **Key Masking**: Automatic in logs (logging.py)

### Monitoring & Dashboard Technologies (if applicable)

#### Current Implementation (CLI-based)
- **Output Format**: Rich terminal output (rich library)
- **Progress Tracking**: tqdm progress bars
- **Logging**: Structured JSON logging (logging.py)
- **Metrics Export**: JSON + Prometheus text format

#### Future Dashboard (Planned)
- **Dashboard Framework**: FastAPI + React (or Streamlit for rapid prototype)
- **Real-time Communication**: Server-Sent Events (SSE) or WebSocket
- **Visualization Libraries**:
  - Plotly (interactive charts)
  - Matplotlib + Seaborn (static reports)
  - Chart.js (web dashboard)
- **State Management**: File system as source of truth (iteration_history.jsonl)
- **Port Management**: Configurable (default: 8000 for API, 3000 for frontend)

## Development Environment

### Build & Development Tools
- **Build System**: pip + requirements.txt (simple, no complex build)
- **Package Management**: pip (virtual environment recommended)
- **Development Workflow**:
  - Edit code → Run tests → Execute iteration loop
  - No hot reload (batch processing nature)
  - Checkpoint/resume for long runs

**Recommended Setup**:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing/linting
```

### Code Quality Tools

#### Static Analysis
- **mypy ≥1.18.0**: Type checking (strict mode)
- **flake8 ≥7.3.0**: PEP 8 compliance, style checking
- **pylint ≥3.3.0**: Code quality, bug detection
- **vulture ≥2.14.0**: Dead code detection

**Configuration**:
- `.flake8`: Max line length 100, ignore specific rules
- `mypy.ini`: Strict mode, disallow untyped defs
- `pylintrc`: Custom rules aligned with project style

#### Formatting
- **isort ≥6.0.0**: Import sorting (PEP 8)
- **black** (optional): Auto-formatting (not currently enforced)

**Style Guidelines**:
- Line length: 100 characters
- Indentation: 4 spaces
- Naming: snake_case for functions/variables, PascalCase for classes
- Docstrings: Google-style

#### Testing Framework
- **pytest ≥8.4.0**: Primary test runner
- **pytest-cov ≥7.0.0**: Coverage reports (target: >80%)
- **pytest-asyncio ≥1.2.0**: Async test support
- **pytest-mock ≥3.15.0**: Mocking utilities
- **pytest-benchmark ≥5.1.0**: Performance benchmarking
- **approvaltests ≥15.3.0**: Snapshot testing (code generation)

**Test Organization**:
- `tests/`: 926 tests across all modules
- Unit tests: Component-level validation
- Integration tests: End-to-end workflows
- Performance tests: Benchmark critical paths

#### Documentation
- **Markdown**: README.md, docs/*.md (中英雙語)
- **Inline**: Google-style docstrings
- **API Docs**: Comprehensive in docs/architecture/
- **Specs**: .spec-workflow/specs/*/requirements.md, design.md, tasks.md

### Version Control & Collaboration

#### VCS
- **System**: Git
- **Remote**: GitHub (or equivalent)
- **Ignore**: .gitignore (excludes .env, data/, checkpoints/, logs/)

#### Branching Strategy
- **Model**: Feature branches + main
- **Pattern**: `feature/<spec-name>`, `bugfix/<issue>`, `docs/<update>`
- **Main Branch**: Stable, tested code only
- **Protection**: No direct commits to main (PR required)

#### Code Review Process
- **Tool**: GitHub Pull Requests
- **Requirements**:
  - All tests passing (926 tests)
  - Code coverage >80%
  - No mypy/flake8 errors
  - Spec completion (requirements → design → tasks)
- **Reviewers**: Self-review + AI validation (codereview, challenge MCP tools)

### Dashboard Development (if applicable)

**Current**: CLI-only (no dashboard)

**Future Plans**:
- **Live Reload**: watchdog for file monitoring
- **Port Management**: Configurable via .env (DASHBOARD_PORT=3456)
- **Multi-Instance**: Support multiple dashboard instances (different projects)
- **Tunnel**: ngrok or similar for remote access

## Deployment & Distribution (if applicable)

### Target Platform(s)
- **Primary**: Linux (Ubuntu 20.04+, WSL2)
- **Secondary**: macOS (Homebrew for TA-Lib)
- **Windows**: WSL2 recommended (native support limited by TA-Lib)
- **Cloud**: Not deployed (personal-use system)

### Distribution Method
- **Type**: Git clone + pip install
- **Package**: Not published to PyPI (internal project)
- **Installation**:
  ```bash
  git clone <repo>
  cd finlab
  pip install -r requirements.txt
  cp .env.example .env  # Configure tokens
  ```

### Installation Requirements
- **Python**: 3.10+ (CPython)
- **System Libraries**:
  - TA-Lib (macOS: `brew install ta-lib`, Ubuntu: `apt-get install ta-lib`)
  - Build tools: gcc, g++, python3-dev
- **RAM**: 8GB+ recommended (for large backtests)
- **Disk**: 10GB+ (data cache, checkpoints, logs)

### Update Mechanism
- **Method**: Git pull + pip install -r requirements.txt
- **Migration**: scripts/migrate_to_fixed_system.py (when schema changes)
- **Backward Compatibility**: Maintained across all phases (100% verified)

## Technical Requirements & Constraints

### Performance Requirements
- **Attribution Analysis**: <100ms per iteration (measured: ~50ms)
- **Metric Extraction**: <1s (DIRECT method), fallback <30s (SIGNAL method)
- **Strategy Validation**: <5s per template (TemplateValidator)
- **Iteration Throughput**: 20-30 iterations per hour (bottleneck: Finlab backtest)
- **Memory Usage**: <4GB per iteration (typical), <8GB peak (200-gen runs)

**Bottlenecks**:
1. Finlab backtest execution: 30-120s per iteration
2. LLM API calls: 5-30s per generation (network latency)
3. Data download: First run only (cached afterward)

### Compatibility Requirements

#### Platform Support
- **Linux**: Ubuntu 20.04+, Debian 11+, Fedora 35+ ✅ Primary
- **macOS**: 11.0+ (Big Sur), Intel/Apple Silicon ✅ Tested
- **Windows**: WSL2 recommended, native partial support ⚠️ TA-Lib dependency

#### Dependency Versions
- **Python**: 3.10.0 minimum (3.11+ recommended)
- **Finlab**: 1.5.3+ (API compatibility)
- **Pandas**: 2.3.2+ (modern API features)
- **Numpy**: 2.2.0+, <3.0.0 (major version constraint)

#### Standards Compliance
- **PEP 8**: Python style guide (enforced by flake8)
- **PEP 484**: Type hints (enforced by mypy strict mode)
- **PEP 517/518**: Modern packaging (pyproject.toml future)
- **JSON**: RFC 8259 compliant
- **YAML**: YAML 1.2 specification

### Security & Compliance

#### Security Requirements
- **API Key Protection**:
  - Environment variables only (.env file)
  - Never committed to git (.gitignore enforced)
  - Automatic masking in logs (logging.py redaction)
- **Code Execution**:
  - Sandboxed strategy execution (exec() with limited namespace)
  - No arbitrary file system access from generated code
  - Input validation on all LLM outputs
- **Data Protection**:
  - Local-only storage (no cloud sync)
  - No PII collection
  - Finlab data cached locally (encryption optional)

#### Compliance Standards
- **N/A**: Personal-use system (no GDPR, HIPAA, SOC2 requirements)
- **Best Practices**: Follow industry standards for API key management

#### Threat Model
- **Low Risk**: No internet-facing services, no user authentication
- **Medium Risk**: LLM code generation (mitigated by validation)
- **Mitigations**:
  - TemplateValidator: Syntax and semantic validation
  - Strategy sandbox: Limited exec() namespace
  - Metric validator: Numerical sanity checks

### Scalability & Reliability

#### Expected Load
- **Iterations**: 20-200 per run (typical batch)
- **Concurrent Users**: 1 (personal use)
- **Data Volume**:
  - Taiwan stock universe: ~1700 stocks
  - Historical data: 2018-2024 (7 years)
  - Cache size: ~500MB-2GB

#### Availability Requirements
- **Uptime**: Not applicable (batch processing)
- **Disaster Recovery**:
  - Manual backup (git commit)
  - Automatic checkpoints (every N iterations)
  - Rollback system (RollbackManager)
- **Data Persistence**:
  - Iteration history preserved (JSONL append-only)
  - Hall of Fame versioned (JSON snapshots)

#### Growth Projections
- **Iteration Count**: 100 → 1000+ (long-term learning)
- **Strategy Library**: 100 → 1000+ champions
- **Factor Library**: 13 → 50+ factors
- **Market Coverage**: Taiwan → Multi-market (US, HK, etc.)

**Scalability Plan**:
1. **Phase 1 (Current)**: JSON-based, single market
2. **Phase 2 (6 months)**: DuckDB for analytics, compressed storage
3. **Phase 3 (12 months)**: Distributed backtesting, multi-market support

## Technical Decisions & Rationale

### Decision Log

#### 1. **Python 3.10+ as Primary Language**
**Rationale**:
- Strong ecosystem for financial analysis (pandas, numpy, scipy)
- Finlab SDK native support (Python-only)
- Excellent LLM API client libraries (anthropic, google-generativeai)
- Personal expertise alignment

**Alternatives Considered**:
- Julia: Better performance, but weaker financial ecosystem
- R: Strong stats, but poor LLM integration
- C++: Maximum performance, but development velocity too slow

**Trade-offs Accepted**:
- GIL performance limits (acceptable for I/O-bound workload)
- Type safety weaker than Rust/Go (mitigated by mypy strict mode)

#### 2. **JSON/JSONL for Data Persistence**
**Rationale**:
- Human-readable for debugging
- Git-friendly (easy diff, version control)
- No external database dependencies
- Simple backup/restore (file copy)

**Alternatives Considered**:
- SQLite: Better querying, but overkill for current scale
- Parquet: Better compression, but not human-readable
- PostgreSQL: Production-grade, but excessive for personal use

**Trade-offs Accepted**:
- Query performance (sequential scan vs. indexed)
- Storage efficiency (text vs. binary)
- **When to Migrate**: >10,000 iterations or multi-user requirements

#### 3. **Regex-based Parameter Extraction (MVP)**
**Rationale**:
- 80/20 solution: Covers 90% of critical parameters
- Simple implementation (<200 lines)
- Fast execution (<100ms)
- AST migration planned for v2.0

**Alternatives Considered**:
- AST (Abstract Syntax Tree): More accurate, but 5x development time
- LLM-based extraction: Unreliable, adds API latency

**Trade-offs Accepted**:
- 10% extraction failure rate (fallback to simple feedback)
- Cannot handle complex expressions (acceptable for templates)
- **Migration Trigger**: Extraction failure rate >20%

#### 4. **Hybrid LLM + Factor Graph Innovation (20/80 Model)**
**Rationale**:
- Combines LLM structural creativity with Factor Graph safety
- 20% LLM innovation: Novel factor combinations beyond predefined patterns
- 80% Factor Graph: Safe fallback with 13 validated factors
- Auto-fallback mechanism: LLM failures don't stop evolution
- Validated approach: Structured YAML (90% success) vs full code (60%)

**Alternatives Considered**:
- Pure LLM: Maximum flexibility, but 60% success rate and safety concerns
- Pure Factor Graph: 100% safe, but limited to 13 predefined factors (diversity collapse)
- Pure Templates: 80% success (Stage 1 achieved), but cannot break through performance ceiling

**Trade-offs Accepted**:
- Additional complexity: LLM integration + validation framework
- API costs: OpenRouter/Gemini/OpenAI API calls
- **Benefit**: Stage 2 breakthrough potential (>80% success, >2.5 Sharpe)

**Current Status** (2025-10-28):
- Implementation: ✅ Complete (Phase 2-3, ~5000+ lines)
- Activation: ⏳ Pending (config: `llm.enabled: false` by default)
- Reason: Backward compatibility during Phase 1 development

#### 5. **Multi-Objective Validation (Sharpe + Calmar + Drawdown)**
**Rationale**:
- Prevent brittle strategy selection (high Sharpe, poor Calmar)
- Real-world trading viability (drawdown management)
- Alignment with risk-adjusted returns goal

**Alternatives Considered**:
- Sharpe-only: Simpler, but brittle strategies
- Sortino ratio: Better downside risk, but correlation with Sharpe

**Trade-offs Accepted**:
- Slower champion updates (stricter criteria)
- More complex validation logic
- **Benefit**: Robust strategies, fewer regressions

#### 6. **Hybrid Threshold System (Relative OR Absolute)**
**Rationale**:
- Fixed percentage fails at high Sharpe (2.4751 * 1.05 = 2.599 impossible)
- Absolute threshold enables continuous improvement
- Balanced update frequency (10-20%)

**Alternatives Considered**:
- Fixed percentage only: Stagnation at high Sharpe
- Absolute only: Excessive churn at low Sharpe
- Adaptive thresholds: Complex, premature optimization

**Trade-offs Accepted**:
- More complex logic (if/else branches)
- Two threshold parameters to tune
- **Validation**: Phase 1 testing confirmed effectiveness

## Known Limitations

### 1. **Regex Parameter Extraction (80% Accuracy)**
**Impact**:
- 10-20% of iterations may have failed attribution
- Fallback to simple feedback (no champion preservation)

**Mitigation**:
- Comprehensive test coverage (historical strategies)
- Graceful degradation (simple feedback fallback)

**Future Solution**:
- Phase 2.0: AST-based extraction (planned)
- Trigger: Extraction failure rate >20%

### 2. **Single-Market Focus (Taiwan Only)**
**Impact**:
- Cannot backtest US, HK, or other markets
- Taiwan-specific biases (retail participation, TAIEX correlation)

**Mitigation**:
- Market characteristics documented (70% retail, 0.6-0.7 US correlation)
- Validation criteria calibrated to Taiwan

**Future Solution**:
- Multi-market support (Phase 3)
- Market-specific configuration (learning_system_<market>.yaml)

### 3. **TA-Lib System Dependency**
**Impact**:
- Windows native support limited
- Installation complexity (requires build tools)

**Mitigation**:
- WSL2 recommended for Windows users
- Alternative: pandas-ta (pure Python, slower)

**Future Solution**:
- Migrate to pandas-ta for cross-platform compatibility
- Trigger: User complaints or Windows market share >30%

### 4. **LLM Innovation Disabled by Default**
**Impact**:
- System runs in Stage 1 mode (Factor Graph only) without LLM activation
- Limited to 13 predefined factors → diversity collapse (10.4% in Phase1 Smoke Test)
- Cannot achieve Stage 2 breakthrough (>80% success, >2.5 Sharpe)

**Mitigation**:
- ✅ Full implementation ready (InnovationEngine + 7-layer validation)
- ✅ Structured YAML mode (90% success rate, 80% hallucination reduction)
- ✅ Auto-fallback to Factor Graph (safety guaranteed)
- ⏳ Phased activation plan: dry-run (2-3h) → 5% (5-8h) → 20% (production)

**Activation Trigger**:
- Enable via config: `llm.enabled: true` (environment variable: `LLM_ENABLED=true`)
- Configuration: config/learning_system.yaml:708

### 5. **No Real-Time Data Integration**
**Impact**:
- Cannot trade live or paper-trade
- Backtesting only (historical simulation)

**Mitigation**:
- Weekly/monthly trading cycle (not time-critical)
- Manual execution based on backtest results

**Future Solution**:
- Real-time data streaming (Phase 3)
- Paper trading mode (Phase 4)
- Live trading integration (Phase 5+)

### 6. **926 Tests, But No Continuous Integration (CI)**
**Impact**:
- Manual test execution before commits
- Risk of broken tests slipping through

**Mitigation**:
- Pre-commit hook reminder (manual)
- QA workflow using MCP tools (codereview, challenge)

**Future Solution**:
- GitHub Actions CI/CD pipeline
- Automated testing on every PR
- Coverage reports on PRs

---

**Document Version**: 1.3
**Last Updated**: 2025-11-05
**Status**: Production
**Technical Reviewer**: N/A (personal project)
**Latest Changes**:
- Application Architecture updated to three-layer model (Learning Loop → LLM Innovation → Validation)
- Added src/learning/ module documentation (Phase 3-6 implementation complete)
- Clarified architectural roles: ENGINE (⚙️) orchestrates CORE (🤖) with GATE (📊) validation
- Updated status: Phase 1-6 100% complete, 88% test coverage, A grade quality
