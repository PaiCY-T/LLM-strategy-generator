# Tasks: System Fix and Validation Enhancement

**Status**: ✅ DEVELOPMENT COMPLETE - Ready for Loop Testing (93% Complete)
**Phase**: Implementation Complete | Documentation Pending
**Priority**: High
**Last Updated**: 2025-10-13
**Dependencies**: src.feedback.TemplateFeedbackIntegrator (integrated)

---

## Phase 1: Emergency System Fixes (CRITICAL)

### Fix 1.1: Strategy Generator Integration
_Requirements: 1.1_

- [x] 1. Remove hardcoded Value_PE strategy generator (lines 372-405 in claude_code_strategy_generator.py)
- [x] 2. Import TemplateFeedbackIntegrator from src.feedback
- [x] 3. Implement template recommendation call in generation loop (iteration e 20)
- [x] 4. Add template instantiation with parameter mapping
- [x] 5. Implement exploration mode logic (every 5th iteration)
- [x] 6. Add template diversity tracking (recent 5 iterations)
- [x] 7. Implement fallback to random template selection (error handling)
- [x] 8. Add retry logic for template instantiation (max 3 retries)
- [x] 9. Add logging for template name and exploration mode status
- [x] 10. Test strategy diversity (e8 unique in 10 iterations)

### Fix 1.2: Metric Extraction Accuracy
_Requirements: 1.2_

- [x] 11. Add report capture wrapper in iteration_engine.py (capture from execution namespace)
- [x] 12. Implement direct metric extraction from captured report
- [x] 13. Add fallback to signal-based extraction (same backtest parameters)
- [x] 14. Fix API compatibility in metrics_extractor.py (handle dict and float return types)
- [x] 15. Add suspicious metric detection (trades > 0 but Sharpe = 0)
- [x] 16. Add extraction method logging (which method succeeded)
- [x] 17. Implement 3-method fallback chain (captured → signal → default)
- [x] 18. Add default metrics return with failure metadata
- [x] 19. Test metric accuracy (error < 0.01 vs actual backtest)
- [x] 20. Verify 50% time savings (eliminate double backtest)

### Fix 1.3: System Integration Testing
_Requirements: 1.3_

- [x] 21. Create tests/test_system_integration_fix.py
- [x] 22. Test 1: Strategy diversity (≥8 unique in 10 iterations)
- [x] 23. Test 2: Template name recording
- [x] 24. Test 3: Exploration mode activation (every 5 iterations)
- [x] 25. Test 4: Metric extraction accuracy (within 0.01)
- [x] 26. Test 5: Report capture success rate (≥90%)
- [x] 27. Test 6: DIRECT extraction usage (<100ms)
- [x] 28. Test 7: Fallback chain activation
- [x] 29. Test 8: End-to-end iteration flow
- [x] 30. Test 9: Template feedback integration
- [x] 31. Test 10: System completeness
- [x] 32. Verify all tests pass in <15 seconds (actual: 1.30s)

### Fix 1.4: System Migration and Backward Compatibility
_Requirements: 1.4_

- [x] 31. Create scripts/migrate_to_fixed_system.py
- [x] 32. Implement iteration_history.jsonl loader with validation
- [x] 33. Add migration_flag: "pre_template_fix" to old records
- [x] 34. Implement Hall of Fame migration logic
- [x] 35. Add graceful degradation for incompatible records
- [x] 36. Generate migration report (processed, migrated, skipped)
- [x] 37. Test migration with existing iteration_history.jsonl
- [x] 38. Verify no data loss in migration
- [x] 39. Create backup mechanism before migration
- [x] 40. Document migration process

---

## Phase 2: Validation Enhancements

### Enhancement 2.1: Train/Validation/Test Data Split
_Requirements: 2.1_

- [x] 41. Create src/validation/data_split.py
- [x] 42. Implement train period backtest (2018-01-01 to 2020-12-31)
- [x] 43. Implement validation period backtest (2021-01-01 to 2022-12-31)
- [x] 44. Implement test period backtest (2023-01-01 to 2024-12-31)
- [x] 45. Calculate consistency score (1 - std/mean of Sharpes)
- [x] 46. Implement validation pass criteria (Sharpe > 1.0, consistency > 0.6)
- [x] 47. Add error handling for insufficient data (<252 days)
- [x] 48. Add error handling for backtest execution failures
- [x] 49. Test data split validation (25 tests, all passing)
- [x] 50. Document Taiwan market considerations (60+ lines comprehensive documentation)

### Enhancement 2.2: Walk-Forward Analysis
_Requirements: 2.2_

- [x] 51. Create src/validation/walk_forward.py
- [x] 52. Implement rolling window configuration (252 days train, 63 days step)
- [x] 53. Implement train/test loop for each window
- [x] 54. Calculate aggregate metrics (avg Sharpe, std, win rate, worst)
- [x] 55. Implement validation pass criteria (avg > 0.5, win rate > 60%, worst > -0.5, std < 1.0)
- [x] 56. Add minimum 3 windows validation
- [x] 57. Test walk-forward analysis (29 tests, all passing)
- [x] 58. Verify performance < 30 seconds for 10 windows (achieved: <2s for 10+ windows)

### Enhancement 2.3: Bonferroni Multiple Comparison Correction
_Requirements: 2.3_

- [x] 59. Create src/validation/multiple_comparison.py
- [x] 60. Install scipy dependency
- [x] 61. Implement Bonferroni adjustment calculation (adjusted_alpha = α/N)
- [x] 62. Calculate Z-score from adjusted alpha
- [x] 63. Calculate Sharpe significance threshold (Z / sqrt(T))
- [x] 64. Implement conservative threshold (max(calculated, 0.5))
- [x] 65. Implement significance determination for single strategy
- [x] 66. Generate validation report (total tested, significant, FDR)
- [x] 67. Test Bonferroni correction (500 strategies)
- [x] 68. Verify FWER ≤ 0.05

### Enhancement 2.4: Bootstrap Confidence Intervals
_Requirements: 2.4_

- [x] 69. Create src/validation/bootstrap.py
- [x] 70. Implement block bootstrap method (block size = 21 days)
- [x] 71. Implement resampling loop (1000 iterations)
- [x] 72. Calculate CI bounds (2.5th and 97.5th percentiles)
- [x] 73. Implement validation pass criteria (CI excludes zero, lower > 0.5)
- [x] 74. Add error handling for insufficient data (<100 days)
- [x] 75. Add error handling for NaN values (require 900/1000 success)
- [x] 76. Test bootstrap validation (27 tests, all passing)
- [x] 77. Verify performance < 20 seconds per metric (achieved: <1s per metric)

### Enhancement 2.5: Baseline Comparison
_Requirements: 2.5_

- [x] 78. Create src/validation/baseline.py
- [x] 79. Implement Buy-and-Hold 0050 baseline
- [x] 80. Implement Equal-Weight Top 50 baseline
- [x] 81. Implement Risk Parity baseline
- [x] 82. Calculate baseline metrics (Sharpe, MDD, annual return)
- [x] 83. Implement Sharpe improvement calculation
- [x] 84. Implement validation pass criteria (beats one baseline by > 0.5)
- [x] 85. Generate comparison report
- [x] 86. Test baseline comparison (26 tests, all passing)
- [x] 87. Verify performance < 5 seconds (with caching: < 0.1s cached, 2.03s full test suite)

---

## Validation & Documentation

### System Validation
_Requirements: Success Criteria_

- [x] 88. Run 10-iteration test with template integration
- [x] 89. Verify strategy diversity ≥80% (8/10 unique)
- [x] 90. Verify Sharpe ratios are non-zero for valid strategies
- [x] 91. Verify Hall of Fame accumulation (Sharpe ≥ 2.0)
- [x] 92. Verify template diversity ≥4 in recent 20 iterations
- [x] 93. Run validation component tests (139 tests, all passing)
- [x] 94. Verify train/val/test consistency > 0.6
- [x] 95. Verify walk-forward avg Sharpe > 0.5
- [x] 96. Verify bootstrap CI excludes zero
- [x] 97. Verify strategy beats baseline by > 0.5

### Documentation & Monitoring
_Requirements: NFR Observability_

- [ ] 98. Add structured logging (JSON format) to all components
- [ ] 99. Implement monitoring dashboard metrics
- [ ] 100. Document template integration process
- [ ] 101. Document validation component usage
- [ ] 102. Create troubleshooting guide
- [ ] 103. Update README with fix details
- [ ] 104. Generate final validation report

---

## Progress Tracking

**Phase 1 (Emergency Fixes)**: 40/40 tasks ✅ COMPLETE
**Phase 2 (Validation Enhancements)**: 47/47 tasks ✅ COMPLETE
**System Validation**: 10/10 tasks ✅ COMPLETE (Tasks 88-97)
**Documentation & Monitoring**: 0/7 tasks (Tasks 98-104)

**Total**: 97/104 tasks (93% complete)

**Implementation Status**: ✅ ALL CODE COMPLETE
**Testing Status**: ✅ ALL TESTS PASSING
**Current Phase**: Loop Testing & Validation
**Next Action**:
1. Run full iteration loop test (100-200 iterations)
2. Monitor system performance and stability
3. Complete documentation tasks (98-104) in parallel

**Key Achievements**:
- ✅ Template system fully integrated
- ✅ Metric extraction accuracy fixed
- ✅ All 5 validation components implemented
- ✅ 139 tests passing across all modules
- ✅ Migration script ready
- ✅ System validated at component level

---

## Notes

- � **CRITICAL**: Phase 1 must be completed before Phase 2
- All Phase 1 tasks block normal system operation
- Estimated total effort: 8-10 hours
- Phase 1: 4-5 hours, Phase 2: 4-5 hours
- Each task should take 15-30 minutes
