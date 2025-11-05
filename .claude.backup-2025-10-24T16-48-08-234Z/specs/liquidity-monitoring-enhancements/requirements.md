# Requirements: Liquidity Monitoring Enhancements

**Spec ID**: liquidity-monitoring-enhancements
**Created**: 2025-10-10
**Status**: Draft
**Priority**: Medium
**Estimated Effort**: 2-3 hours

## Overview

Enhance the autonomous iteration engine with advanced liquidity monitoring, compliance checking, and performance analysis capabilities to ensure all generated strategies meet the 150M TWD liquidity standard across variable stock counts (6-12 stocks).

## Background

Recent analysis revealed that:
1. The system successfully updated to 150M TWD liquidity standard
2. Both prompt templates (v2 and v3) are now aligned
3. However, there's no automated compliance monitoring
4. Performance analysis under new constraints is needed
5. Dynamic liquidity calculation based on stock count would be beneficial

## Goals

### Primary Goals
1. **Compliance Monitoring**: Automatically verify all generated strategies use ≥150M liquidity filter
2. **Performance Analysis**: Compare strategy performance across different liquidity thresholds
3. **Market Availability**: Analyze Taiwan stock market for stocks meeting liquidity requirements
4. **Dynamic Optimization**: Enable future dynamic liquidity calculation based on actual stock count

### Success Criteria
- ✅ 100% of generated strategies comply with 150M standard
- ✅ Performance comparison report available for 50M/100M/150M/200M thresholds
- ✅ Market availability statistics documented
- ✅ Foundation for dynamic liquidity adjustment established

## Requirements

### R1: Liquidity Compliance Checker

**Priority**: High
**Effort**: 1 hour

**Description**: Add automated checking to `analyze_metrics.py` to verify liquidity filter compliance in all strategies.

**Acceptance Criteria**:
- [ ] Parses generated strategy code to extract liquidity threshold
- [ ] Validates threshold ≥ 150M TWD
- [ ] Reports compliance rate in monitoring output
- [ ] Flags non-compliant strategies with warnings
- [ ] Logs compliance history to JSON

**Technical Requirements**:
- Use AST parsing to extract filter thresholds reliably
- Handle multiple liquidity filter patterns (rolling mean, static filters)
- Store compliance data in `liquidity_compliance.json`
- Integrate with existing `analyze_metrics.py` workflow

### R2: Performance Threshold Comparison

**Priority**: Medium
**Effort**: 1-1.5 hours

**Description**: Analyze and compare strategy performance across different liquidity thresholds to validate the 150M choice.

**Acceptance Criteria**:
- [ ] Compares performance across 50M, 100M, 150M, 200M thresholds
- [ ] Metrics: Sharpe ratio, success rate, market impact estimation
- [ ] Statistical significance testing (t-test for Sharpe differences)
- [ ] Generates comparison report with visualizations
- [ ] Documents optimal threshold recommendation

**Technical Requirements**:
- Analyze existing iteration_history.json for strategies at different thresholds
- Calculate aggregate statistics per threshold bucket
- Use scipy.stats for significance testing
- Output markdown report with tables and charts

### R3: Market Liquidity Statistics

**Priority**: Low
**Effort**: 30-45 minutes

**Description**: Analyze Taiwan stock market to determine how many stocks meet different liquidity requirements.

**Acceptance Criteria**:
- [ ] Counts stocks meeting 50M, 100M, 150M, 200M thresholds
- [ ] Calculates percentage of total market
- [ ] Groups by market cap categories (large/mid/small cap)
- [ ] Documents findings in markdown report
- [ ] Updates at runtime or via scheduled analysis

**Technical Requirements**:
- Query Finlab data for trading value statistics
- Use existing data.get('price:成交金額') infrastructure
- Generate `market_liquidity_stats.json` and `MARKET_LIQUIDITY_REPORT.md`
- Optional: Cache results for performance

### R4: Dynamic Liquidity Calculator (Foundation)

**Priority**: Low
**Effort**: 30-45 minutes

**Description**: Create foundation for future dynamic liquidity calculation based on actual stock count in strategy.

**Acceptance Criteria**:
- [ ] Function to calculate minimum liquidity given stock count and portfolio size
- [ ] Validates against 2% market impact threshold (50x multiplier)
- [ ] Returns recommended threshold with safety margin
- [ ] Documented for future integration into prompt generation
- [ ] Unit tested with edge cases (6, 8, 10, 12 stocks)

**Technical Requirements**:
- Pure function: `calculate_min_liquidity(portfolio_value, stock_count, safety_multiplier=50)`
- Returns dict with: `{theoretical_min, recommended, market_impact_pct}`
- Located in new module: `src/liquidity_calculator.py`
- Full docstring with examples

## Non-Requirements

- ❌ Real-time market data integration (use historical data only)
- ❌ Automatic threshold adjustment during iteration (manual override only)
- ❌ GUI dashboard (command-line reports sufficient)
- ❌ Multi-currency support (TWD only)

## Constraints

- Must not break existing iteration_history.json structure
- Must maintain backward compatibility with v2/v3 templates
- Performance overhead <5 seconds per iteration
- All new code must pass existing AST validation

## Dependencies

- **Existing Systems**: iteration_engine.py, analyze_metrics.py, iteration_history.json
- **External Libraries**: scipy (for stats), matplotlib (optional for charts)
- **Data Sources**: Finlab API (price:成交金額)

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| AST parsing fails on edge cases | Low | Medium | Extensive test coverage, fallback to regex |
| Market data query slow | Medium | Low | Cache results, limit query frequency |
| Threshold comparison biased by small sample | Medium | Medium | Require minimum 10 strategies per threshold |
| Breaking changes to existing workflows | Low | High | Comprehensive integration testing |

## Timeline

- **R1 (Compliance Checker)**: Day 1 morning (1 hour)
- **R2 (Performance Comparison)**: Day 1 afternoon (1-1.5 hours)
- **R3 (Market Statistics)**: Day 2 morning (30-45 min)
- **R4 (Dynamic Calculator)**: Day 2 afternoon (30-45 min)

**Total Estimated Time**: 2.5-3.5 hours

## Validation Plan

1. **Unit Tests**: Test each component in isolation
2. **Integration Tests**: Run against existing iteration_history.json
3. **Smoke Test**: Execute one full iteration with monitoring enabled
4. **Regression Test**: Verify no performance degradation

## References

- Original conversation context (liquidity constraint evolution)
- `prompt_template_v2_with_datasets.txt` lines 128-136
- `prompt_template_v3_comprehensive.txt` lines 135-141
- `iteration_history.json` (125 iterations of production data)
- `LEARNING_CYCLE_MONITORING_REPORT.md` (baseline metrics)
