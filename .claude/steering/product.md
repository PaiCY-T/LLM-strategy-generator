# Product Steering Document

## Product Vision

Finlab is a **bilingual (中文/English) autonomous trading strategy optimization system** for weekly/monthly trading cycles. The system generates, validates, backtests, and learns from trading strategies using AI, targeting 60%+ success rate and consistent Sharpe ratio >1.2.

## Target Users

- **個人交易者 (Individual Traders)**: Weekly/monthly cycle traders seeking automated strategy development
- **量化研究員 (Quant Researchers)**: Professionals testing Taiwan stock market strategies
- **Python開發者 (Python Developers)**: Engineers building automated trading systems

## Core Features

### 1. Autonomous Strategy Generation (Phase 1 - Complete)
- **LLM Integration**: Claude API via OpenRouter for strategy code generation
- **Dataset Validation**: Real-time Finlab dataset key verification
- **Code Sandbox**: Secure execution environment with anti-lookahead validation
- **Bilingual Support**: 中文/English prompts and documentation

### 2. Learning System Enhancement (Current Phase)
- **Champion Tracking**: Persistence of best-performing strategies (Sharpe >0.5)
- **Performance Attribution**: Automated analysis identifying success factors and failure patterns
- **Evolutionary Prompts**: LLM constraints preserving proven elements while enabling incremental improvements
- **Failure Learning**: Dynamic tracking of failed parameter configurations

### 3. Backtest Engine
- **Metrics**: Sharpe ratio, annual return, max drawdown, win rate, total return
- **Validation**: Look-ahead bias detection, code quality checks
- **Visualization**: Performance plots, equity curves, drawdown analysis

### 4. Data Infrastructure
- **Finlab API Integration**: Taiwan stock market data (price, fundamentals, technical indicators)
- **DuckDB Storage**: High-performance local data warehouse
- **Auto-refresh**: Configurable data update scheduling
- **Caching**: Multi-layer caching for performance

## Product Principles

1. **Learning-Focused**: System learns from success and failure to improve over time
2. **Safety-First**: Comprehensive validation prevents look-ahead bias and unsafe code
3. **Bilingual**: Equal support for 中文 and English users
4. **Transparency**: Clear attribution of performance changes to specific parameters
5. **Autonomous**: Minimal human intervention after initial setup

## Success Metrics

### Current (MVP Phase)
- **Success Rate**: 33% → Target 60%+ (strategies with Sharpe >0.5)
- **Best Sharpe**: 0.97 → Target >1.2 after 10 iterations
- **Regression Prevention**: No >10% performance drops after establishing champion
- **Average Sharpe**: 0.33 → Target >0.5

### Long-term
- **Knowledge Accumulation**: Growing library of validated success patterns
- **Iteration Efficiency**: Achieve target performance in 5-7 iterations (vs random walk)
- **Strategy Diversity**: 10+ distinct high-performing strategy families

## Non-Goals

- **不做高頻交易 (No HFT)**: System targets weekly/monthly cycles only
- **No Real-time Trading**: Focus on backtest optimization, not live execution
- **No Multi-market**: Taiwan stock market only (TWS)
- **No Over-engineering**: Personal use system, not enterprise platform

## Roadmap

### Phase 1: MVP Foundation (✅ Complete)
- Autonomous loop with validation and sandbox
- Backtest engine with Finlab integration
- Basic storage and caching

### Phase 2: Learning System (🔄 Current - Production Hardening Complete)
- Champion tracking and persistence (✅)
- Performance attribution analysis (✅)
- Evolutionary prompts with preservation constraints (✅)
- Failure pattern learning (✅)
- Production hardening: Atomic persistence, LLM validation, pattern pruning (✅)
- **Status**: 88/100 production-ready, 40 tests passing

### Phase 3: Advanced Attribution (Planned)
- AST-based parameter extraction (90%+ accuracy vs 80% regex)
- Semantic code understanding
- Multi-factor interaction analysis

### Phase 4: Knowledge Graph (Future)
- Graphiti integration for strategy knowledge base
- Cross-strategy pattern recognition
- Long-term memory across sessions

## User Workflows

### Primary: Autonomous Optimization
```
1. Configure: Set max_iterations, model selection
2. Run: Execute autonomous loop
3. Monitor: Track champion updates, performance attribution
4. Learn: Review failure patterns, success factors
5. Iterate: System improves automatically with each cycle
```

### Secondary: Manual Analysis
```
1. Generate: Create single strategy via analysis engine
2. Backtest: Validate with sandbox and metrics
3. Compare: Analyze against existing strategies
4. Deploy: Export champion strategy for production
```

## Constraints

- **個人使用 (Personal Use)**: Not designed for enterprise scale
- **API Dependencies**: Requires Finlab API token and Claude API access
- **Taiwan Market**: Dataset limited to Taiwan stock market
- **Python 3.8+**: Minimum Python version requirement
- **LLM Compliance**: No guarantee AI follows preservation directives (mitigated by validation)
