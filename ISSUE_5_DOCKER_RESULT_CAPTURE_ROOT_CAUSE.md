# Issue #5: Docker Mock Data Initialization - Root Cause Analysis

**Date**: 2025-11-02
**Status**: ✅ ROOT CAUSE IDENTIFIED
**Severity**: Medium (blocks Docker execution >80% success criterion)

---

## Executive Summary

Issue #5 was reported as "Docker mock data initialization failure" with the error `AttributeError: 'NoneType' object has no attribute 'get'`. After systematic investigation, the root cause has been identified:

**The Docker container successfully executes the code and produces results, but DockerExecutor doesn't parse the output from the container logs.**

DockerExecutor returns `signal: None` (line 373 in docker_executor.py) instead of extracting the metrics from the container's stdout.

---

## Investigation Timeline

### Step 1: F-string Template Verification ✅
**Finding**: F-string escaping is working correctly
- `{{` properly evaluates to `{` in data_setup template
- Lines 221, 258, 323 all escape correctly
- No syntax errors in template

### Step 2: Code Assembly Verification ✅
**Finding**: Code assembly is correct
- `complete_code = data_setup + "\n" + code + "\n" + metrics_extraction` (line 354)
- `data = Data()` instantiation is included (line 294 of template)
- Complete code is 7,500+ characters
- No `{{}}` remains in assembled code

### Step 3: Local Execution Test ✅
**Finding**: Code executes successfully outside Docker
- Created `debug_docker_code_assembly.py` test script
- Executed complete_code with exec()
- **Result**: ✅ Success - signal extracted correctly
- Proves code is valid Python with no errors

### Step 4: Manual Docker Execution Test ✅ **BREAKTHROUGH**
**Finding**: Docker execution SUCCEEDS
- Created `test_docker_execution.py` to test DockerExecutor.execute()
- Executed same complete_code in Docker container
- **Container logs show**: `DOCKER_OUTPUT_SIGNAL: {'total_return': 0.236...}`
- **DockerExecutor returns**: `success: True, signal: None`

---

## Root Cause

**Location**: `src/sandbox/docker_executor.py:367-378`

```python
if exit_code == 0:
    # Success - try to read output file
    # Note: Since filesystem is read-only, output must be captured from logs
    # For now, we'll parse the signal from logs or code namespace
    return {
        'success': True,
        'signal': None,  # ← THE BUG: Would need to implement result capture
        'error': None,
        'execution_time': execution_time,
        'container_id': container_id,
        'logs': logs
    }
```

### The Issue

1. **Container execution**: Container successfully runs the code and prints `DOCKER_OUTPUT_SIGNAL: {...}` to stdout
2. **Log capture**: DockerExecutor captures the logs in the `logs` variable
3. **Result parsing**: **NOT IMPLEMENTED** - signal is hardcoded to `None`
4. **Return value**: Returns `signal: None` even though the actual signal is in the logs

### Impact Chain

1. DockerExecutor returns `signal: None`
2. autonomous_loop.py receives `result_dict['signal'] = None`
3. Code tries to access signal as a dict (somewhere downstream)
4. Results in `AttributeError: 'NoneType' object has no attribute 'get'`

---

## Evidence

### Manual Docker Test Result
```
================================================================================
DOCKER EXECUTION RESULT:
================================================================================
Success: True
Signal: None   ← Bug: Should be the parsed dict
Error: None
Execution time: 2.67s

================================================================================
CONTAINER LOGS:
================================================================================
DOCKER_OUTPUT_SIGNAL: {'total_return': 0.23612364029534139, 'annual_return': 0.19025513262179547, 'sharpe_ratio': 4.149915926847435, 'max_drawdown': -0.9998832510775599, 'win_rate': 0.26926915983160454, 'position_count': 252}
```

The signal is IN THE LOGS but not being extracted!

---

## Fix Strategy

### Option A: Parse Docker Logs (Recommended)
**Effort**: 1-2 hours
**Approach**: Parse container logs for `DOCKER_OUTPUT_SIGNAL:` pattern

```python
# In docker_executor.py:367-378
if exit_code == 0:
    # Parse signal from logs
    signal = None
    for line in logs.split('\n'):
        if 'DOCKER_OUTPUT_SIGNAL:' in line:
            import json
            signal_str = line.split('DOCKER_OUTPUT_SIGNAL:')[1].strip()
            signal = eval(signal_str)  # Or use json.loads() with proper formatting
            break

    return {
        'success': True,
        'signal': signal,  # ← Fixed: Parse from logs
        'error': None,
        'execution_time': execution_time,
        'container_id': container_id,
        'logs': logs
    }
```

**Pros**:
- Simple implementation
- No changes to autonomous_loop.py
- Works with existing infrastructure

**Cons**:
- Relies on string parsing (could be fragile)
- Using `eval()` has security implications

### Option B: Use JSON File Output
**Effort**: 2-3 hours
**Approach**: Write signal to `/tmp/output.json` in container, read after execution

**Pros**:
- More robust than log parsing
- Properly structured JSON output

**Cons**:
- Requires changes to metrics_extraction template
- More complex implementation
- File I/O overhead

---

## Recommended Fix

**Use Option A (Parse Docker Logs)** with these improvements:

1. Update `metrics_extraction` template to output JSON format:
   ```python
   print(f"__SIGNAL_JSON_START__{json.dumps(signal)}__SIGNAL_JSON_END__")
   ```

2. Parse logs in DockerExecutor:
   ```python
   import json
   import re

   signal_match = re.search(r'__SIGNAL_JSON_START__(.+?)__SIGNAL_JSON_END__', logs)
   if signal_match:
       signal = json.loads(signal_match.group(1))
   else:
       signal = None
   ```

**Advantages**:
- Uses JSON (safe parsing)
- Clear delimiters prevent false matches
- Backward compatible (gracefully handles missing output)

---

## Files to Modify

1. **src/sandbox/docker_executor.py** (lines 367-378)
   - Add signal parsing logic
   - Update return statement

2. **artifacts/working/modules/autonomous_loop.py** (lines 336-351)
   - Update metrics_extraction template to output JSON format
   - Add clear delimiters for parsing

---

## Testing Plan

1. **Unit test**: Test signal parsing with mock logs
2. **Integration test**: Run `test_docker_execution.py` and verify signal is extracted
3. **E2E test**: Run 5-iteration validation to verify Docker success rate improves
4. **Full validation**: Re-run 30-iteration test to verify >80% success rate

---

## Impact Assessment

**Before Fix**:
- Docker execution success rate: 0% (0/20 successful)
- Reason: Signal is None, causing AttributeError downstream

**After Fix** (Expected):
- Docker execution success rate: >95% (matches local execution success)
- All 4 original bugs verified as fixed
- Diversity activation remains at 66.7%

---

## Related Documentation

- Issue originally reported in: `DOCKER_INTEGRATION_TEST_FRAMEWORK_FINAL_SUMMARY.md`
- Validation results: `TASK_6.2_VALIDATION_REPORT.md`
- Debug scripts created:
  - `debug_docker_code_assembly.py` - Verifies code assembly
  - `test_docker_execution.py` - Tests Docker execution manually

---

## Conclusion

Issue #5 is NOT a "Docker mock data initialization failure" - it's a **result capture implementation gap** in DockerExecutor.

The data_setup template works correctly, the Data class is instantiated properly, and the strategy code executes successfully in Docker. The only missing piece is parsing the output from container logs.

**Estimated fix time**: 1-2 hours
**Expected outcome**: Docker execution success rate improves to >80%, meeting the final completion criterion for the spec.

---

*Root cause analysis completed: 2025-11-02*
