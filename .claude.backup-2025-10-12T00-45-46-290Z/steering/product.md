# Product Steering Document

## Product Vision

**Finlab Autonomous Trading Strategy System** - An intelligent, self-improving platform that generates, validates, and optimizes quantitative trading strategies for the Taiwan stock market through machine learning and evolutionary algorithms.

> **⚠️ 個人使用專案 | Personal Use Project**
> 這是專為個人使用設計的交易系統，週/月交易週期，請勿過度工程化
> This is a personal-use trading system designed for weekly/monthly cycles - avoid over-engineering

## Core Purpose

Transform quantitative trading strategy development from manual trial-and-error into an autonomous learning system that:
- Generates profitable trading strategies automatically using LLM-powered code generation
- Learns from success and failure patterns across iterations
- Preserves high-performing elements while exploring improvements
- Achieves consistent performance through champion tracking and attribution analysis

## Target Users

**Primary**: Quantitative traders and strategy developers in Taiwan stock market
- Professional traders seeking systematic strategy optimization
- Algorithmic trading firms requiring reproducible strategy pipelines
- Individual quant developers exploring factor-based strategies

**Use Cases**:
- Autonomous strategy generation and backtesting
- Performance attribution and success pattern extraction
- Champion strategy tracking across iterations
- Risk-aware portfolio optimization with liquidity constraints

## Key Features

### 1. Autonomous Learning System (MVP - Production Ready)
**Status**: ✅ Complete (70% success rate, Sharpe 2.48, 100% validation success)

- **Champion Tracking**: Persistence of best-performing strategies
- **Performance Attribution**: Automated analysis of success factors and failure patterns
- **Evolutionary Prompts**: LLM constraints preserving proven elements
- **Diversity Forcing**: Periodic exploration to avoid local optima

**Value**: Increased success rate from 33% → 70%, consistent Sharpe >2.0

### 2. Hall of Fame Repository
**Status**: ✅ Production Ready (Post-Zen Debug Optimization)

- **Three-Tier Architecture**: Champions (Sharpe >1.5), Contenders (>1.0), Archive (historical)
- **Novelty Detection**: Vector-based duplicate detection with O(1) cached comparison
- **JSON Serialization**: 2-5x faster than YAML with unified persistence API
- **Factor Extraction**: Regex-based strategy fingerprinting for similarity analysis

**Value**: Prevents duplicate strategies, tracks portfolio of high performers

### 3. Data Management & Caching
**Status**: ✅ Production Ready (L1/L2 Architecture Validated)

- **L1 Memory Cache**: Runtime performance optimization, lazy loading, hit/miss statistics
- **L2 Disk Cache**: Persistent Finlab API downloads with timestamp management
- **Liquidity Calculator**: Market liquidity analysis (1-4 week smoothed turnover)
- **Data Wrapper**: Unified interface for Finlab data access

**Value**: Fast data access, API cost reduction, freshness management

### 4. Comprehensive Validation System
**Status**: ✅ Production Ready (Skip-Sandbox Optimization)

- **AST Validator**: Syntax and semantic validation without execution overhead
- **Data Validator**: Dataset key verification with 50 curated datasets
- **Code Validator**: Multi-stage validation (AST → Data → Backtest)
- **Sensitivity Tester**: Optional parameter stability testing (50-75 min per strategy)

**Value**: 100% validation success, <100ms validation time, production-grade quality

### 5. Feedback & Learning Infrastructure
**Status**: ✅ Production Ready

- **Failure Tracker**: Pattern recognition across failed iterations
- **Performance Attributor**: Identify critical parameter changes affecting Sharpe
- **Success Pattern Extraction**: Automated discovery of winning factors
- **NL Summary Generator**: Human-readable performance explanations

**Value**: Systematic learning from outcomes, reproducible insights

## Success Metrics

### Current Performance (Post-MVP)
- ✅ **Success Rate**: 70% (baseline: 33%)
- ✅ **Best Sharpe**: 2.4850 (baseline: 0.97)
- ✅ **Validation Success**: 100% (125/125 iterations)
- ✅ **Average Sharpe**: 0.52 (baseline: 0.33)

### Production Readiness
- ✅ **Skip-Sandbox Optimization**: 30-45s per iteration (75% time savings)
- ✅ **Champion Persistence**: <50ms save/load
- ✅ **Attribution Analysis**: <100ms overhead
- ✅ **Novelty Detection**: 1.6x-10x speedup with vector caching

## Product Objectives

### Near-Term (Complete)
1. ✅ Achieve >60% success rate in 10-iteration validation runs
2. ✅ Maintain Sharpe ratio >1.2 by iteration 10
3. ✅ Eliminate >10% performance regressions after champion establishment
4. ✅ Complete production optimization (skip-sandbox, vector caching)

### Mid-Term (Planned)
1. **AST Migration** (Phase 5): Replace regex parameter extraction with AST analysis
2. **Template Library**: Repository of proven strategy templates with Hall of Fame integration
3. **Multi-Factor Optimization**: Systematic grid search for optimal factor combinations
4. **Performance Monitoring**: Real-time tracking with alert system

### Long-Term Vision
1. **Production Deployment**: Live trading integration with risk management
2. **Portfolio Optimization**: Multi-strategy allocation and rebalancing
3. **User Interface**: Web dashboard for strategy monitoring and control

## Constraints and Assumptions

### Technical Constraints
- **Taiwan Market Focus**: Finlab API limited to Taiwan stock market data
- **Backtesting Only**: No live trading execution (safety-first design)
- **LLM Dependency**: Requires OpenAI/Claude API access via OpenRouter
- **Python 3.8+**: Modern Python features and type hints

### Business Constraints
- **API Costs**: OpenRouter/Gemini API usage costs for strategy generation
- **Data Costs**: Finlab API subscription for market data
- **⚠️ Personal Use Only**: 這是個人使用專案，不是企業級多租戶系統
  - Single-user design (not multi-tenant)
  - No team collaboration features required
  - Avoid over-engineering - keep it simple and practical
  - Focus on weekly/monthly trading cycles only

### Design Assumptions
- Weekly/monthly trading frequency (not high-frequency)
- Factor-based strategies (ROE, liquidity, fundamentals)
- Long-only positions (no shorting)
- Liquidity constraints (>100M TWD turnover)

## Competitive Advantages

1. **Autonomous Learning**: Self-improving system learning from iterations
2. **Production Ready**: 100% validation success, production-grade quality
3. **Taiwan Market**: Specialized for Taiwan stock market with Finlab integration
4. **Open Source Approach**: Transparent, reproducible, extensible

## Risk Management

### Market Risks
- **Backtesting Bias**: Historical performance ≠ future results
- **Overfitting**: Champion preservation may overfit to historical data
- **Market Regime Change**: Strategies may fail in different market conditions

**Mitigation**: Diversity forcing every 5th iteration, parameter sensitivity testing, conservative liquidity filters

### Technical Risks
- **LLM Non-Compliance**: LLM may ignore preservation directives
- **API Failures**: OpenRouter/Finlab API downtime
- **Data Quality**: Missing/incorrect market data

**Mitigation**: Prompt engineering validation, comprehensive error handling, data freshness checks

---

**Document Version**: 1.0
**Last Updated**: 2025-10-11
**Status**: Production Ready
**Next Review**: Post-AST Migration (Phase 5)
