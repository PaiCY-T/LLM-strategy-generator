# Exit Mutation Performance Benchmark Report

**Generated:** 2025-10-26 13:13:25

## Executive Summary

- **Exit Mutation Success Rate:** 100.0%
- **Factor Mutation Success Rate:** 84.9%
- **Success Rate Improvement:** +15.1 percentage points
- **Speed:** Exit mutation 0.2× faster than factor mutation
- **Memory:** Exit mutation uses 50.19× memory vs factor mutation

## Detailed Metrics

### Exit Parameter Mutation

| Metric | Value |
|--------|-------|
| Success Rate | 100.0% (1000/1000) |
| Average Time | 2.65ms |
| Median Time | 0.97ms |
| P95 Time | 2.75ms |
| P99 Time | 10.92ms |
| Memory Overhead | 5.10MB |
| Syntax Correctness | 100.0% |

### Factor Mutation (Baseline)

| Metric | Value |
|--------|-------|
| Success Rate | 84.9% (849/1000) |
| Average Time | 0.57ms |
| Median Time | 0.56ms |
| P95 Time | 0.98ms |
| P99 Time | 1.48ms |
| Memory Overhead | 0.10MB |
| Syntax Correctness | 91.4% |

## Comparison Analysis

- **Success Rate:** Exit mutation has +15.1 percentage point improvement
- **Speed:** Exit mutation is 0.2× faster
- **Memory:** Exit mutation uses 50.19× memory

✅ **Significant improvement** in success rate (≥15 percentage points)
❌ **Minimal speedup** (<1.2× faster)

## Conclusion

✅ Exit mutation **meets success rate target** (≥95%)
✅ Exit mutation **meets speed target** (<10ms average)
✅ Exit mutation **meets memory target** (<10MB overhead)

---
*Report generated on 2025-10-26 13:13:25*