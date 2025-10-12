# JSONL Logging System Documentation

## Overview

The JSONL (JSON Lines) logging system provides robust, crash-resilient iteration tracking for the autonomous learning loop. Each iteration's complete state is saved to `iteration_history.jsonl` for analysis, resume capability, and historical context.

## Features

### 1. Append-Only JSONL Format
- One JSON record per line
- Each line is independently parseable
- Crash recovery: resume from last valid record
- No data loss on process interruption

### 2. Atomic Writes
- Write to temporary file, then atomic rename
- Prevents file corruption if process is killed mid-write
- Transaction-like behavior for data safety

### 3. Code Hashing (SHA256)
- Detect duplicate strategies across iterations
- Track code evolution over time
- Enable deduplication analysis

### 4. ISO 8601 Timestamps
- Precise time tracking for each iteration
- Timezone-aware datetime format
- Enables temporal analysis and debugging

### 5. Graceful Error Handling
- I/O failures don't crash the iteration loop
- Detailed logging for debugging
- Fallback mechanisms for corrupted data

## JSONL Record Format

```json
{
  "iteration": 0,
  "timestamp": "2025-01-09T12:34:56.789012",
  "code": "<full strategy code>",
  "code_hash": "abc123...",
  "metrics": {
    "sharpe_ratio": 1.24,
    "total_return": 0.265,
    "max_drawdown": -0.28,
    "win_rate": 0.58,
    "total_trades": 124,
    "avg_holding_period": 45.2
  },
  "feedback": "<natural language summary for next iteration>",
  "used_fallback": false,
  "success": true,
  "error": null
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `iteration` | int | 0-indexed iteration number |
| `timestamp` | str | ISO 8601 timestamp (e.g., "2025-01-09T12:34:56.789012") |
| `code` | str | Full Python strategy code |
| `code_hash` | str | SHA256 hash of code for deduplication |
| `metrics` | dict | Performance metrics from backtest |
| `feedback` | str | Natural language summary for next iteration |
| `used_fallback` | bool | Whether fallback strategy was used |
| `success` | bool | Whether execution succeeded |
| `error` | str\|null | Error message if failed, null otherwise |

## API Functions

### `save_iteration_result()`

Save iteration results to JSONL file with atomic writes.

```python
def save_iteration_result(
    iteration: int,
    code: str,
    metrics: Dict[str, Any],
    feedback: str,
    used_fallback: bool = False,
    success: bool = True,
    error: Optional[str] = None
) -> None
```

**Arguments:**
- `iteration`: Iteration number (0-indexed)
- `code`: Generated strategy code
- `metrics`: Performance metrics dictionary
- `feedback`: Natural language feedback for next iteration
- `used_fallback`: Whether fallback strategy was used (default: False)
- `success`: Whether execution succeeded (default: True)
- `error`: Error message if failed (default: None)

**Example:**
```python
save_iteration_result(
    iteration=0,
    code=strategy_code,
    metrics={
        "sharpe_ratio": 1.24,
        "total_return": 0.265,
        "max_drawdown": -0.28
    },
    feedback="Strong performance. Consider adding volume filter.",
    used_fallback=False,
    success=True,
    error=None
)
```

### `load_previous_feedback()`

Load feedback from last successful iteration for continuity.

```python
def load_previous_feedback() -> str
```

**Returns:**
- Feedback string from last iteration
- Empty string if no history exists

**Example:**
```python
feedback = load_previous_feedback()
if feedback:
    print(f"Resuming with feedback: {feedback[:50]}...")
else:
    print("Starting fresh - no previous history")
```

### `get_last_iteration_number()`

Get the last completed iteration number for crash recovery.

```python
def get_last_iteration_number() -> int
```

**Returns:**
- Last iteration number (0-indexed)
- -1 if no history exists

**Example:**
```python
last_iter = get_last_iteration_number()
if last_iter >= 0:
    print(f"Resuming from iteration {last_iter + 1}")
    start_iteration = last_iter + 1
else:
    print("Starting from scratch")
    start_iteration = 0
```

## Usage Patterns

### Pattern 1: Normal Iteration Loop

```python
for iteration in range(num_iterations):
    # Generate strategy
    code = generate_strategy(iteration, feedback)

    # Execute and get metrics
    result = validate_and_execute(code, iteration)

    # Create feedback for next iteration
    feedback = create_nl_summary(result["metrics"], code, iteration)

    # Save iteration results
    save_iteration_result(
        iteration=iteration,
        code=code,
        metrics=result["metrics"],
        feedback=feedback,
        used_fallback=result.get("used_fallback", False),
        success=result["success"],
        error=result.get("error")
    )
```

### Pattern 2: Crash Recovery and Resume

```python
# Detect last completed iteration
last_iter = get_last_iteration_number()

if last_iter >= 0:
    print(f"Crash detected! Resuming from iteration {last_iter + 1}")
    start_iteration = last_iter + 1

    # Load previous feedback for continuity
    feedback = load_previous_feedback()
else:
    print("Starting fresh")
    start_iteration = 0
    feedback = ""

# Resume from crash point
for iteration in range(start_iteration, num_iterations):
    # Continue loop...
```

### Pattern 3: Error Handling with Fallback

```python
try:
    code = generate_strategy(iteration, feedback)
    result = validate_and_execute(code, iteration)

    save_iteration_result(
        iteration=iteration,
        code=code,
        metrics=result["metrics"],
        feedback=feedback,
        used_fallback=result.get("used_fallback", False),
        success=True,
        error=None
    )

except Exception as e:
    logger.error(f"Iteration {iteration} failed: {e}")

    # Save failed iteration
    save_iteration_result(
        iteration=iteration,
        code=code if 'code' in locals() else "",
        metrics={},
        feedback=f"Previous iteration failed: {str(e)}",
        used_fallback=False,
        success=False,
        error=str(e)
    )
```

### Pattern 4: Historical Analysis

```python
def analyze_iteration_history():
    """Analyze historical performance trends."""
    if not os.path.exists(HISTORY_FILE):
        return None

    history = []
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line)
            history.append(record)

    # Extract metrics
    sharpe_ratios = [r["metrics"].get("sharpe_ratio", 0) for r in history if r["success"]]

    # Find best iteration
    best_idx = sharpe_ratios.index(max(sharpe_ratios))
    best_record = history[best_idx]

    print(f"Best iteration: {best_record['iteration']}")
    print(f"Best Sharpe: {best_record['metrics']['sharpe_ratio']:.4f}")

    return history
```

## File Format Specification

### File Name
- Default: `iteration_history.jsonl`
- Configurable via `HISTORY_FILE` constant

### Encoding
- UTF-8 encoding for international character support
- BOM-less for POSIX compatibility

### Line Format
- One JSON object per line
- No trailing commas
- LF line endings (Unix-style)
- Each line is independently parseable

### Example File Content
```jsonl
{"iteration": 0, "timestamp": "2025-01-09T12:00:00", "code": "...", "metrics": {...}, ...}
{"iteration": 1, "timestamp": "2025-01-09T12:15:00", "code": "...", "metrics": {...}, ...}
{"iteration": 2, "timestamp": "2025-01-09T12:30:00", "code": "...", "metrics": {...}, ...}
```

## Data Safety and Integrity

### Atomic Writes
1. Create temporary file: `.iteration_history_XXXXX.tmp`
2. Write all existing records to temp file
3. Append new record to temp file
4. Atomic rename: `os.replace(temp_path, HISTORY_FILE)`
5. Clean up temp file on error

### Corruption Recovery
- Last line corrupted → Try second-to-last line
- Multiple corrupted lines → Load all valid records
- Complete file corruption → Start fresh with warning

### Data Validation
- JSON parsing validation per record
- Type checking for required fields
- Timestamp format validation (ISO 8601)
- Code hash verification (SHA256)

## Performance Considerations

### Disk I/O
- Append-only writes (efficient)
- Atomic renames (fast operation)
- No in-memory caching (minimal RAM usage)

### File Size
- ~5-10 KB per iteration (typical)
- 100 iterations ≈ 500 KB - 1 MB
- 1000 iterations ≈ 5-10 MB
- Compression recommended for large histories

### Scalability
- Linear time complexity: O(n) for n iterations
- Constant space complexity: O(1) for writes
- Reading entire history: O(n) but rare operation

## Testing

Run the comprehensive test suite:

```bash
python3 test_jsonl_logging.py
```

**Test Coverage:**
1. ✅ Basic save functionality
2. ✅ Error save functionality
3. ✅ Multiple iterations
4. ✅ Load previous feedback
5. ✅ Get last iteration number
6. ✅ Code hash deduplication
7. ✅ JSONL format validation
8. ✅ Crash recovery and resume

## Troubleshooting

### Issue: "Permission denied" error
**Solution:** Check file permissions and ensure directory is writable

### Issue: Corrupted JSONL file
**Solution:** Use `load_previous_feedback()` which handles corruption gracefully

### Issue: Large file size
**Solution:**
- Archive old iterations: `mv iteration_history.jsonl iteration_history_archive.jsonl`
- Compress archived files: `gzip iteration_history_archive.jsonl`

### Issue: Slow performance
**Solution:** JSONL format is already optimized for append operations. If needed:
- Reduce code length in records (use code hash for deduplication)
- Implement record rotation after N iterations
- Use SSD storage for better I/O performance

## Best Practices

1. **Always use `save_iteration_result()` after each iteration**
   - Even if execution fails
   - Helps with debugging and continuity

2. **Check for previous history before starting**
   ```python
   last_iter = get_last_iteration_number()
   if last_iter >= 0:
       # Resume logic
   ```

3. **Handle errors gracefully**
   - Save error details to JSONL
   - Continue to next iteration
   - Don't crash the entire loop

4. **Monitor file size**
   - Archive or compress old histories
   - Set up rotation policies for production

5. **Validate data integrity periodically**
   - Check JSONL format with `json.loads()` per line
   - Verify code hashes match actual code

## Integration with Main Loop

The JSONL logging system integrates seamlessly with the iteration loop:

```python
# iteration_engine.py main loop
for iteration in range(start_iteration, num_iterations):
    try:
        # Generate strategy
        code = generate_strategy(iteration, feedback)

        # Validate and execute
        result = validate_and_execute(code, iteration, fallback_count)

        # Create feedback
        feedback = create_nl_summary(result["metrics"], code, iteration)

        # JSONL logging (critical step)
        save_iteration_result(
            iteration=iteration,
            code=code,
            metrics=result["metrics"],
            feedback=feedback,
            used_fallback=result.get("used_fallback", False),
            success=result["success"],
            error=result.get("error")
        )

    except Exception as e:
        # Error handling with JSONL logging
        save_iteration_result(
            iteration=iteration,
            code="",
            metrics={},
            feedback=f"Error: {str(e)}",
            used_fallback=False,
            success=False,
            error=str(e)
        )
```

## Future Enhancements

Potential improvements for future versions:

1. **Compression**: Built-in gzip compression for large histories
2. **Rotation**: Automatic file rotation after N iterations
3. **Cloud Backup**: Sync to S3/GCS for disaster recovery
4. **Metrics Database**: Export metrics to TimescaleDB for analysis
5. **Web Dashboard**: Visualize iteration history in real-time
6. **Diff Tracking**: Track code changes between iterations
7. **Performance Indexing**: Create index for fast metric lookups

## References

- [JSON Lines Format](http://jsonlines.org/)
- [ISO 8601 Timestamp Standard](https://en.wikipedia.org/wiki/ISO_8601)
- [SHA256 Hashing](https://en.wikipedia.org/wiki/SHA-2)
- [Atomic File Operations](https://en.wikipedia.org/wiki/Atomicity_(database_systems))

---

**Last Updated:** 2025-10-09
**Version:** 1.0
**Author:** Claude Code Task Implementation Specialist
