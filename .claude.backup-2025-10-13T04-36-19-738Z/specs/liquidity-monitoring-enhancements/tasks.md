# Implementation Tasks: Liquidity Monitoring Enhancements

**Spec ID**: liquidity-monitoring-enhancements
**Total Tasks**: 4 atomic tasks
**Estimated Time**: 2.5-3.5 hours

## Task List

- [ ] 1. Implement liquidity compliance checker in analyze_metrics.py
  - Add AST-based threshold extraction
  - Validate ≥150M requirement
  - Log results to liquidity_compliance.json
  - Integrate with existing workflow
  - _Effort: 1 hour_
  - _Files: analyze_metrics.py, liquidity_compliance.json_

- [ ] 2. Create performance threshold comparison analyzer
  - Group strategies by liquidity threshold (50M/100M/150M/200M)
  - Calculate aggregate statistics per group
  - Perform statistical significance testing (t-test)
  - Generate LIQUIDITY_PERFORMANCE_REPORT.md
  - _Effort: 1-1.5 hours_
  - _Files: analyze_performance_by_threshold.py (new), LIQUIDITY_PERFORMANCE_REPORT.md_
  - _Requirements: Task 1_

- [ ] 3. Build market liquidity statistics analyzer
  - Query Finlab for Taiwan market trading value data
  - Count stocks meeting different threshold buckets
  - Categorize by market cap (large/mid/small)
  - Generate MARKET_LIQUIDITY_STATS.md
  - _Effort: 30-45 minutes_
  - _Files: analyze_market_liquidity.py (new), MARKET_LIQUIDITY_STATS.md, market_liquidity_stats.json_

- [ ] 4. Create dynamic liquidity calculator module
  - Implement calculate_min_liquidity() function
  - Add validation across stock count range (6-12)
  - Write comprehensive unit tests
  - Document for future prompt integration
  - _Effort: 30-45 minutes_
  - _Files: src/liquidity_calculator.py (new), tests/test_liquidity_calculator.py (new)_

## Task Dependencies

```
Task 1 (Compliance Checker)
    │
    ├─> Task 2 (Performance Analyzer) - needs compliance data
    │
    ├─> Task 3 (Market Analyzer) - independent
    │
    └─> Task 4 (Calculator) - independent, foundation for future
```

## Success Criteria

### Task 1: Compliance Checker
- ✅ AST parsing extracts threshold from 100% of valid strategies
- ✅ Correctly identifies compliant (≥150M) vs non-compliant strategies
- ✅ liquidity_compliance.json properly structured and updated
- ✅ Compliance statistics accurate (tested against known data)
- ✅ Integration with analyze_metrics.py maintains existing functionality

### Task 2: Performance Analyzer
- ✅ Correctly groups 125 historical strategies by threshold
- ✅ Statistical calculations accurate (validated manually for sample)
- ✅ T-test implementation correct (p-values reasonable)
- ✅ Report generated in proper markdown format
- ✅ Handles edge cases (insufficient data, missing metrics)

### Task 3: Market Analyzer
- ✅ Successfully queries Finlab price:成交金額 data
- ✅ Accurately counts stocks per threshold bucket
- ✅ Market cap categorization correct
- ✅ Report provides actionable insights
- ✅ Caching mechanism works (optional but recommended)

### Task 4: Calculator
- ✅ calculate_min_liquidity() returns correct values for all inputs
- ✅ Edge cases handled (6 stocks, 12 stocks, extreme values)
- ✅ Unit tests achieve ≥90% code coverage
- ✅ Validation function works across stock count ranges
- ✅ Documentation clear with examples

## Implementation Order

**Recommended**: Tasks 1 → 2 → (3 and 4 in parallel)

**Rationale**:
- Task 1 provides foundation for Task 2
- Task 3 and 4 are independent and can be done in any order
- If short on time, prioritize Tasks 1 and 2 (higher value)

## Testing Strategy

### Unit Tests
- Task 1: Test AST parsing with various code patterns
- Task 2: Test statistical calculations with known datasets
- Task 3: Mock Finlab API responses
- Task 4: Comprehensive edge case coverage

### Integration Tests
- Run Task 1 against existing iteration_history.json
- Verify Task 2 report accuracy with manual spot checks
- Test Task 3 with live Finlab connection
- Validate Task 4 against actual portfolio scenarios

### Acceptance Tests
- Execute full analyze_metrics.py workflow with all enhancements
- Generate all reports and verify correctness
- Confirm no performance regression (<5s overhead)
- Validate backward compatibility

## Notes

- All tasks maintain backward compatibility
- No changes to existing iteration_history.json format
- New features are opt-in (won't break existing workflows)
- Focus on code quality and documentation (future maintenance)
