# Invalid Diversity Reports - Archived 2025-11-01

**Reason for Archival**: These diversity analysis reports are INVALID and must not be used.

## Issue

These reports were generated using the WRONG validation results file:
- **Used**: `phase2_validated_results_20251101_060315.json` (OLD, before threshold fix)
- **Should use**: `phase2_validated_results_20251101_132244.json` (CORRECT, after threshold fix)

## Impact

- Analyzed 8 strategies instead of correct 4 validated strategies
- Old file had threshold bug (bonferroni_threshold=0.8 instead of 0.5)
- Resulted in invalid diversity score: 27.6/100

## Corrected Reports

See `diversity_report_corrected.*` in project root for valid diversity analysis:
- Correct validation file used
- Analyzed 4 validated strategies (not 8)
- Diversity score: 19.17/100 (INSUFFICIENT)

## Discovery Date

2025-11-01 21:45 UTC - Identified by Gemini 2.5 Pro challenge analysis

## Related Tasks

- Task 3.4: Archive invalid reports (this action)
- Task 3.5: Re-run with correct file (completed - see corrected reports)
