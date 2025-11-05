# Changelog

All notable changes to the Finlab Backtesting Optimization System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2025-11-03

### Fixed

**Validation Framework - Critical Bug Fixes**
- **Bonferroni threshold bug**: Corrected threshold comparison logic (was 0.8, now correctly uses 0.5 for statistical significance testing)
  - Root cause: Used `max(bonferroni_threshold, dynamic_threshold)` incorrectly
  - Impact: Validation pass rate more accurate (20% → 15%)
  - Files: `src/analysis/decision_framework.py` (lines 764-781)
- **DecisionFramework JSON parsing**: Fixed JSON path errors causing false CRITICAL failures
  - `validation_fixed`: Now correctly reads from `validation_statistics.bonferroni_threshold`
  - `execution_success_rate`: Now reads from `metrics.execution_success_rate` with fallback logic
  - Impact: Phase 3 decision changed from NO-GO → CONDITIONAL_GO (2 criteria now passing)

### Added

**Diversity Analysis System**
- **DiversityAnalyzer**: Comprehensive diversity analysis across factors, correlation, and risk profiles
  - Factor Diversity: Jaccard similarity-based metric (target >0.5)
  - Correlation Analysis: Average pairwise correlation using Sharpe ratios (target <0.8)
  - Risk Diversity: Coefficient of variation of max drawdowns (target >0.3)
  - Overall Diversity Score: 0-100 scale with recommendations (SUFFICIENT ≥60, MARGINAL 40-60, INSUFFICIENT <40)
- **analyze_diversity.py**: CLI tool for diversity analysis with visualization support
  - JSON and Markdown reports
  - Correlation heatmap generation
  - Factor usage distribution charts

**Decision Framework**
- **DecisionFramework**: Automated GO/NO-GO evaluation for Phase 3 progression
  - Three-tier decision model: GO / CONDITIONAL_GO / NO-GO
  - Seven criteria with configurable weights (CRITICAL, HIGH, MEDIUM, LOW)
  - Risk assessment: LOW / MEDIUM / HIGH
  - Mitigation strategies for CONDITIONAL_GO cases
- **evaluate_phase3_decision.py**: CLI tool for decision evaluation
  - Comprehensive decision document generation (Markdown)
  - Exit codes: 0=GO, 1=CONDITIONAL_GO, 2=NO_GO, 3=ERROR
  - Verbose logging for troubleshooting

**Documentation**
- `docs/VALIDATION_FRAMEWORK.md`: Threshold bug fix details with before/after comparison
- `docs/DIVERSITY_ANALYSIS.md`: Complete diversity metrics reference
- `docs/PHASE3_GO_CRITERIA.md`: GO/NO-GO criteria and decision framework guide
- `CHANGELOG.md`: This file

### Changed

**Validation System**
- Validation pass rate: 20% → 15% (more accurate with fixed Bonferroni threshold)
- Phase 3 decision: NO-GO → CONDITIONAL_GO (after bug fix)
  - Unique Strategies: 4 ≥ 3 ✅
  - Diversity Score: 19.2/100 (target ≥40) ⚠️
  - Validation Framework: Fixed ✅
  - Execution Success: 100% ✅
- Risk Level: HIGH → MEDIUM (improved after critical bug fixes)

**Threshold Logic**
- Separated statistical threshold (0.5) from dynamic threshold (0.8)
- Removed incorrect `max()` comparison that mixed thresholds
- Validation now uses appropriate threshold based on context:
  - Multi-strategy testing: Bonferroni-corrected (0.5)
  - Single strategy validation: Market benchmark (0.8)

### Deprecated

None

### Removed

None

### Security

None

---

## [1.1.0] - 2025-10-31

### Added

**Validation System v1.1 (P0 Complete)**
- **Stationary Bootstrap**: Time-series aware confidence intervals (Politis & Romano 1994)
  - Preserves autocorrelation structure
  - Geometric block lengths (avg ~20-25 days)
  - More realistic CI for financial returns
- **Dynamic Threshold**: Taiwan market benchmark-based validation
  - Benchmark: 0050.TW ETF (TWSE Taiwan 50 Index)
  - Adaptive threshold: Benchmark Sharpe + 0.2 margin = 0.8
  - Floor: Minimum 0.0 (positive risk-adjusted returns required)
- **97 tests passing**: Comprehensive test suite with scipy validation
  - 7.1% difference from scipy bootstrap (acceptable tolerance)
  - Backward compatible with v1.0 behavior

**Documentation**
- `docs/VALIDATION_SYSTEM.md`: Statistical validation framework guide
- `docs/TAIWAN_MARKET_THRESHOLD_ANALYSIS.md`: Benchmark analysis

### Changed

- Validation confidence intervals: Standard bootstrap → Stationary bootstrap
- Threshold calculation: Static (0.5) → Dynamic (market-adaptive, 0.8)

---

## [1.0.0] - 2025-10-20

### Added

**Phase B: Factor Extraction & Registry (COMPLETE)**
- **Factor Library**: 13 reusable factors extracted from templates
  - Categories: MOMENTUM (3), VALUE (1), QUALITY (1), RISK (1), ENTRY (1), EXIT (6)
- **Factor Registry**: Centralized discovery, validation, and creation
  - FactorRegistry.get_instance(): Singleton pattern
  - list_by_category(): Filter by FactorCategory enum
  - create_factor(): Factory pattern with parameter validation
- **Strategy Composition**: 3 full strategies validated
  - Momentum, Turtle, Hybrid strategies
  - Pipeline-based execution model
  - Dependency management
- **Performance**: All targets exceeded
  - Factor discovery: 7-200x faster than targets
  - Strategy composition: Meets all performance goals
- **18 integration tests**: 100% pass rate

**Documentation**
- `docs/PHASE_B_MIGRATION_REPORT.md`: Complete Phase B report
- `docs/FACTOR_GRAPH_*.md`: Factor graph architecture guides

### Changed

- Refactored momentum and turtle templates into reusable factors
- Backward compatibility: 100% maintained

---

## [0.9.0] - 2025-10-15

### Added

**Learning System MVP**
- **Champion Tracking**: Success pattern preservation
- **Performance Attribution**: Root cause analysis
- **Evolutionary Prompts**: Failure avoidance
- **MVP Validation**: 3/4 criteria passed
  - Best Sharpe: 2.48 (+155% over baseline)
  - Champion update rate: Meets targets

**Documentation**
- `docs/LEARNING_SYSTEM_*.md`: Learning system guides

---

## [0.8.0] - 2025-10-10

### Added

**Basic Validation System v1.0**
- Statistical significance testing
- Out-of-sample validation
- Baseline comparison

---

## [0.1.0] - 2025-10-01

### Added

**Initial Release**
- Finlab API integration
- Basic backtesting
- Performance metrics (Sharpe, CAGR, Max Drawdown)
- Data caching
- Bilingual support (Chinese/English)

---

**Notes**:
- Dates are approximate for historical entries
- Version 1.2.0 marks the first formal CHANGELOG entry
- Previous versions documented retroactively

---

**Changelog Version**: 1.0.0
**Last Updated**: 2025-11-03
