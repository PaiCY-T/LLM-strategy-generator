# Technology Steering Document

## Technology Stack

### Core Technologies

**Language**: Python 3.8+
- Modern Python features: dataclasses, type hints, f-strings
- Async/await support for future enhancements
- Standard library: json, re, datetime, ast, pathlib

**Data Processing**:
- `pandas >= 2.0.0` - DataFrame operations, time series analysis
- `numpy >= 1.24.0` - Numerical computations, array operations
- `scipy >= 1.10.0` - Statistical analysis, optimization

**Finlab Integration**:
- `finlab >= 1.5.3` - Taiwan stock market data, backtesting engine
- Proprietary API for market data (price, revenue, fundamentals)
- Backtesting framework with Sharpe ratio calculation

**LLM Integration**:
- `openai >= 1.0.0` - OpenRouter client for Claude/GPT-4 access
- OpenRouter API for multi-model support (Claude, GPT-4, Gemini via OpenRouter)
- Direct Gemini API access via Google AI SDK (for Gemini-specific features)
- JSON-structured prompts for strategy generation

### Data Storage

**Local Storage**:
- JSON serialization for all persistent data (champion, history, patterns)
- Parquet format for cached market data (L2 disk cache)
- DuckDB for optional local data warehouse

**File Structure**:
```
/finlab/
├── champion_strategy.json          # Current champion
├── iteration_history.json          # All iteration results
├── failure_patterns.json           # Failure pattern tracking
├── datasets_curated_50.json        # Validated dataset registry
├── liquidity_compliance.json       # Liquidity analysis results
└── .finlab_cache/                  # L2 disk cache (Parquet)
```

### Testing & Quality

**Testing Framework**:
- `pytest >= 7.0.0` - Unit and integration testing
- `pytest-cov` - Code coverage reporting (target: >80%)
- `pytest-timeout` - Timeout enforcement for long-running tests

**Quality Tools**:
- `flake8` - PEP 8 compliance, code style enforcement
- `mypy` - Static type checking (optional)
- Python AST - Built-in syntax/semantic validation

### Development Tools

**Version Control**: Git
- Branch strategy: feature branches with descriptive names
- Commit messages: Conventional commits format
- No automated CI/CD (manual testing workflow)

**Documentation**: Markdown
- README.md: Quick start and usage
- STATUS.md: Current status and metrics
- Spec documents: .claude/specs/ directory

## Architecture Decisions

### 1. Skip-Sandbox Optimization (2025-10-10)

**Decision**: Replace sandboxed execution with AST-only validation

**Rationale**:
- Validation success rate: 100% (125/125 iterations)
- Time savings: 75% (120s → 30s per iteration)
- Risk assessment: Low (AST validation proven reliable)

**Trade-offs**:
- ✅ Massive performance improvement
- ✅ Simplified error handling
- ⚠️ No runtime validation (acceptable with 100% AST success)

**Status**: ✅ Production deployed

### 2. JSON Serialization (2025-10-11 Zen Debug H1)

**Decision**: Migrate from YAML to JSON for all persistence

**Rationale**:
- Performance: 2-5x faster parsing
- Reliability: Standard library (no external dependencies)
- Compatibility: Native Python support

**Trade-offs**:
- ✅ No external dependencies
- ✅ Better error handling
- ⚠️ Less human-readable (acceptable for automated system)

**Status**: ✅ Complete

### 3. L1/L2 Cache Architecture (2025-10-11 Zen Debug H2)

**Decision**: Maintain separate memory and disk caches

**Rationale**:
- L1 (Memory): Runtime performance, lazy loading, statistics
- L2 (Disk): Persistent storage, timestamp management
- Clear separation of concerns (performance vs persistence)

**Trade-offs**:
- ✅ Optimal performance characteristics
- ✅ Simple, focused interfaces
- ⚠️ Two implementations to maintain (validated as architectural pattern)

**Status**: ✅ Validated (no changes needed)

### 4. Vector Caching for Novelty Detection (2025-10-11 Zen Debug M1)

**Decision**: Pre-compute and cache factor vectors in Hall of Fame

**Rationale**:
- O(n) performance bottleneck from repeated vector extraction
- Minimal memory overhead (~160 KB per 1000 strategies)
- 1.6x-10x speedup measured

**Trade-offs**:
- ✅ Massive performance improvement
- ✅ Backward compatible API
- ⚠️ Memory usage scales with Hall of Fame size (acceptable)

**Status**: ✅ Complete

### 5. Regex-Based Parameter Extraction (MVP)

**Decision**: Use regex for parameter extraction (not AST)

**Rationale**:
- 80/20 solution: Handles 90% of critical parameters
- Simple implementation: <200 lines
- Fast development: MVP-ready in days

**Trade-offs**:
- ✅ Fast to implement and validate
- ✅ Sufficient for MVP success (70% success rate)
- ⚠️ Limited to pattern-based extraction
- 🔄 Planned migration: AST-based extraction (Phase 5)

**Status**: ✅ Production (AST migration planned)

### 6. OpenRouter for LLM Access

**Decision**: Use OpenRouter instead of direct API calls

**Rationale**:
- Multi-model support: Claude, GPT-4, Gemini
- Unified API: Single integration point
- Cost optimization: Model comparison and selection

**Trade-offs**:
- ✅ Flexibility to switch models
- ✅ Simplified integration
- ⚠️ Additional API layer (minimal latency impact)

**Status**: ✅ Production

## Performance Requirements

### Validation Performance
- **AST Validation**: <100ms per strategy
- **Data Validation**: <50ms dataset key verification
- **Code Validation**: <150ms end-to-end (AST + Data)

### Learning System Performance
- **Champion Persistence**: <50ms save/load
- **Attribution Analysis**: <100ms per comparison
- **Pattern Extraction**: <200ms per strategy
- **Novelty Detection**: <500ms per check (with caching)

### Iteration Performance
- **Total Iteration Time**: 30-45s (with skip-sandbox)
  - Strategy generation: 15-25s (LLM API call)
  - Validation: <1s (AST + Data)
  - Backtesting: 10-15s (Finlab engine)
  - Learning: <500ms (attribution + champion update)

### Memory Constraints
- **Vector Cache**: ~160 KB per 1000 strategies
- **L1 Memory Cache**: <100 MB for typical dataset set
- **Total Memory**: <500 MB for full system

## Security Considerations

### API Security
- **Environment Variables**: API keys stored in environment, not code
- **OpenRouter Key**: `OPENROUTER_API_KEY` environment variable
- **Gemini API Key**: `GOOGLE_API_KEY` environment variable (for direct Gemini access)
- **Finlab Token**: `FINLAB_API_TOKEN` environment variable
- **No Key Logging**: API keys never logged or exposed

### Code Execution Safety
- **AST Validation**: Syntax/semantic checks before execution
- **No eval()**: No arbitrary code execution
- **Sandboxed Backtesting**: Finlab engine isolated from system

### Data Security
- **Local Storage Only**: No external data transmission (except APIs)
- **No PII**: Market data only (no user personal information)
- **File Permissions**: Standard POSIX permissions on Linux/WSL

## Scalability Considerations

### Current Scale
- **Iterations**: 125+ validated iterations
- **Hall of Fame**: 60 strategies cached
- **Dataset Registry**: 50 curated datasets
- **Validation Success**: 100% (no failures)

### Scale Limits
- **Vector Cache**: Tested to 1000 strategies (~160 KB)
- **Iteration History**: No size limit (JSON append-only)
- **L1 Cache**: Limited by system memory (~100 datasets max)
- **L2 Cache**: Limited by disk space (Parquet compression efficient)

### Future Scaling
- **Multi-Strategy Portfolio**: 10-20 strategies in production
- **Parallel Backtesting**: Thread pool for concurrent validation
- **Distributed Cache**: Redis for shared L1 cache (if needed)
- **Database Migration**: PostgreSQL for structured queries (optional)

## Integration Points

### Finlab API Integration
- **Data Download**: `finlab.data.get()` for market data
- **Backtesting**: `finlab.backtest.sim()` for strategy evaluation
- **Performance Metrics**: Sharpe ratio, total return, max drawdown
- **Data Types**: price, monthly_revenue, fundamental_features, etl

### LLM API Integration

**OpenRouter API**:
- **Strategy Generation**: POST /v1/chat/completions
- **Model Selection**: claude-sonnet-4.5, gpt-4.1, gemini-2.5-pro (via OpenRouter)
- **Structured Output**: JSON code blocks extracted from LLM response
- **Error Handling**: Retry with exponential backoff

**Google Gemini API** (Direct):
- **Direct Access**: Google AI SDK for Gemini-specific features
- **Model Support**: gemini-2.5-pro, gemini-2.5-flash, gemini-2.0-flash
- **Use Cases**: Fallback, cost optimization, Gemini-native features
- **Authentication**: `GOOGLE_API_KEY` environment variable

### File System Integration
- **Working Directory**: `/mnt/c/Users/jnpi/Documents/finlab/`
- **Source Code**: `src/` organized by layer (data, validation, repository, templates)
- **Specs**: `.claude/specs/` for project specifications
- **Cache**: `.finlab_cache/` for persistent data

## Technical Constraints

### Platform Constraints
- **Operating System**: Linux (WSL2 on Windows)
- **Python Version**: 3.8+ (tested on 3.8, 3.9, 3.10)
- **⚠️ Personal Use Environment**: Single-user local development (not production server)
  - 個人使用專案，避免過度工程化
  - No enterprise features (multi-user, distributed systems, complex orchestration)
  - Keep architecture simple and maintainable for one developer

### API Constraints
- **Finlab Rate Limits**: Respect API rate limits (no aggressive polling)
- **OpenRouter Costs**: Monitor token usage and costs
- **Network Dependency**: Requires internet for API access

### Computational Constraints
- **CPU**: Single-threaded backtesting (Finlab engine limitation)
- **Memory**: <500 MB typical usage
- **Disk**: <10 GB for cache and history

## Maintenance and Monitoring

### Code Maintenance
- **Code Coverage**: >80% target for new code
- **Type Hints**: All new code uses type hints
- **Documentation**: Docstrings for all public APIs
- **Testing**: Unit tests for all critical paths

### Performance Monitoring
- **Iteration Metrics**: Track time per stage (generation, validation, backtesting)
- **Memory Usage**: Monitor L1 cache size and vector cache growth
- **API Costs**: Log OpenRouter token usage
- **Success Rate**: Track validation success and Sharpe ratio distribution

### Error Handling
- **Graceful Degradation**: Continue with simple feedback if attribution fails
- **Fallback Strategies**: Regex fallback if AST fails, L2 cache if L1 misses
- **Logging**: Comprehensive error logging with context
- **Recovery**: Automatic recovery from corrupted champion JSON

## Future Technology Roadmap

### Phase 5: AST Migration (Planned)
- Replace regex parameter extraction with AST analysis
- 100% coverage of all parameter types
- Improved accuracy and reliability
- Foundation for advanced code analysis

### Future Enhancements (Backlog)
- **Redis Integration**: Shared L1 cache for distributed systems (only if multi-process needed)
- **Web Dashboard**: Real-time monitoring and control interface
- **DuckDB**: In-memory analytical queries for complex historical analysis (lightweight alternative to PostgreSQL)
- **CI/CD**: Automated testing and deployment pipeline (when team collaboration starts)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-11
**Architecture Review**: Post-Zen Debug Optimization
**Next Review**: Post-AST Migration (Phase 5)
