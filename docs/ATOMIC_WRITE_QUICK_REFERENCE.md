# Atomic Write Quick Reference

**Module**: `src.learning.iteration_history`
**Status**: Production Ready ✅
**Last Updated**: 2025-11-04

---

## What is Atomic Write?

Atomic write ensures that the history file is **never corrupted** even if the program crashes during write operations. The worst case is that a new record is not saved, but all existing data remains intact.

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│ Atomic Write Flow (Corruption-Proof)                    │
└─────────────────────────────────────────────────────────┘

1. Read Existing Records
   ├─ innovations.jsonl (100 records)
   └─ Load all into memory

2. Write to Temp File
   ├─ innovations.jsonl.tmp
   ├─ Write all 100 existing records
   └─ Write 1 new record (total: 101)

3. Atomic Replace
   └─ os.replace(tmp, original)
      ├─ If SUCCESS: original now has 101 records
      └─ If CRASH: original still has 100 records (safe!)

✅ Original file NEVER corrupted
✅ Filesystem guarantees atomicity
```

---

## Usage

### Basic Usage (No Changes Required)

```python
from src.learning.iteration_history import IterationHistory, IterationRecord
from datetime import datetime

# Create history manager (atomic write is automatic)
history = IterationHistory("artifacts/data/innovations.jsonl")

# Save record - atomic write happens automatically
record = IterationRecord(
    iteration_num=5,
    strategy_code="data.get('price:收盤價').rolling(20).mean()",
    execution_result={"success": True, "execution_time": 4.2},
    metrics={"sharpe_ratio": 1.5, "total_return": 0.2, "max_drawdown": -0.08},
    classification_level="LEVEL_3",
    timestamp=datetime.now().isoformat(),
    champion_updated=True
)

history.save(record)  # ✅ Atomic write - crash-safe!
```

### Load Records (No Changes)

```python
# Load recent iterations
recent = history.load_recent(N=5)
for record in recent:
    print(f"Iter {record.iteration_num}: Sharpe {record.metrics['sharpe_ratio']}")

# Get last iteration number (for loop resumption)
last_iter = history.get_last_iteration_num()
next_iter = (last_iter + 1) if last_iter is not None else 0
```

---

## Performance Characteristics

### Before (Append-only)
```
Write: O(1) - append single line
Risk:  ❌ Corruption possible on crash
```

### After (Atomic Write)
```
Write: O(N) where N = total records
Risk:  ✅ Corruption impossible
```

### Benchmarks

| Records | Write Time (100 iterations) | Status |
|---------|----------------------------|--------|
| 100     | < 2 seconds                | ✅ Fast |
| 1,000   | < 20 seconds               | ✅ OK |
| 5,000   | ~100 seconds               | ⚠️ Slow |
| 10,000+ | Minutes                    | ❌ Migrate to SQLite |

**Current System**: ~200 iterations max → **No performance concern**

---

## Thread Safety

### ✅ Supported
- Single process writes (sequential)
- Multiple threads with lock (see example below)
- Concurrent reads (always safe)

### ❌ NOT Supported
- Concurrent multi-process writes (temp file conflicts)

### Multi-Thread Example (with Lock)

```python
from threading import Lock
from src.learning.iteration_history import IterationHistory

history = IterationHistory("artifacts/data/innovations.jsonl")
write_lock = Lock()

def save_record_thread_safe(record):
    """Thread-safe save with lock"""
    with write_lock:
        history.save(record)

# Multiple threads can safely call save_record_thread_safe()
```

---

## Error Handling

### Automatic Cleanup

The atomic write mechanism automatically cleans up temporary files on error:

```python
try:
    history.save(record)
except IOError as e:
    # Temp file automatically cleaned up
    # Original file guaranteed intact
    logger.error(f"Failed to save: {e}")
    # Can retry safely
```

### Common Error Cases

| Error | Cause | Original File | Temp File | Action |
|-------|-------|---------------|-----------|--------|
| Disk full | No space during write | ✅ Safe | ⚠️ Partial | Auto-cleanup |
| Permission denied | No write access | ✅ Safe | ❌ Not created | Check permissions |
| Crash during `os.replace()` | System crash | ✅ Safe | ⚠️ May remain | Safe to delete |

---

## Migration Guide

### When to Migrate to Database

Consider migrating from JSONL to SQLite when:

1. ✅ **> 5,000 iterations** - Write performance degrades
2. ✅ **Concurrent writes needed** - Multiple processes writing
3. ✅ **Complex queries required** - Filtering, aggregation, joins
4. ✅ **Transaction support needed** - Multi-record consistency

### Migration Example

```python
# From: JSONL with atomic write
history = IterationHistory("artifacts/data/innovations.jsonl")
history.save(record)

# To: SQLite with transactions
import sqlite3
conn = sqlite3.connect("artifacts/data/history.db")
cursor = conn.cursor()
cursor.execute("""
    INSERT INTO iterations (iteration_num, strategy_code, metrics, timestamp)
    VALUES (?, ?, ?, ?)
""", (record.iteration_num, record.strategy_code, json.dumps(record.metrics), record.timestamp))
conn.commit()
```

---

## Testing

### Verify Atomic Write Protection

```python
# Test: Crash during write doesn't corrupt file
from unittest.mock import patch
from src.learning.iteration_history import IterationHistory

history = IterationHistory("test.jsonl")
history.save(record1)  # Initial record

# Simulate crash during os.replace()
with patch('os.replace', side_effect=Exception("Crash!")):
    try:
        history.save(record2)  # This will fail
    except:
        pass

# Original file still intact
records = history.get_all()
assert len(records) == 1  # Only record1, record2 not saved
```

Run full test suite:
```bash
pytest tests/learning/test_iteration_history_atomic.py -v
```

---

## Troubleshooting

### Issue: Write Performance Slow

**Symptom**: `history.save()` takes several seconds

**Diagnosis**:
```python
record_count = history.count()
print(f"Total records: {record_count}")
```

**Solution**:
- If < 5,000: Performance is expected (O(N) write)
- If > 5,000: Consider migrating to SQLite
- If > 10,000: Must migrate to database

### Issue: Temp File Remains After Crash

**Symptom**: `innovations.jsonl.tmp` file exists

**Diagnosis**:
```bash
ls -la artifacts/data/*.tmp
```

**Solution**:
```bash
# Safe to delete temp files
rm artifacts/data/*.tmp

# They'll be recreated on next write
```

### Issue: Concurrent Write Errors

**Symptom**: `OSError: No such file or directory: *.tmp`

**Diagnosis**: Multiple processes writing concurrently

**Solution**:
```python
# Option 1: Use lock for multi-thread
from threading import Lock
write_lock = Lock()
with write_lock:
    history.save(record)

# Option 2: Serialize writes at application level
# Option 3: Migrate to database with proper locking
```

---

## Best Practices

### ✅ DO

1. **Trust the atomic write** - It's crash-safe by design
2. **Monitor file size** - Track record count, migrate if > 5k
3. **Use lock for multi-thread** - Serialize writes with `threading.Lock()`
4. **Clean temp files on startup** - Delete `*.tmp` files on init
5. **Test crash scenarios** - Verify atomic write in your tests

### ❌ DON'T

1. **Don't manually append to file** - Use `history.save()` only
2. **Don't concurrent multi-process writes** - Use lock or database
3. **Don't delete original file manually** - Use `history.clear()` method
4. **Don't modify temp files** - They're internal implementation
5. **Don't expect O(1) writes** - Performance is O(N), plan accordingly

---

## FAQ

### Q: Is atomic write enabled by default?

**A**: Yes! No configuration needed. All writes are automatically atomic.

### Q: Can I disable atomic write for better performance?

**A**: No. Atomic write is core to data integrity. If performance is critical:
- Batch writes (save multiple records together)
- Migrate to database for large datasets
- Use append-only mode is not safe

### Q: What happens if disk is full during write?

**A**:
- Original file remains intact ✅
- Temp file may be partial (auto-cleanup) ⚠️
- Error raised: `IOError("Failed to save")`
- Safe to retry after freeing space

### Q: Can I use this with NFS or network drives?

**A**:
- Local filesystem: ✅ Fully supported
- NFS: ⚠️ May work but `os.replace()` atomicity not guaranteed
- Network drive: ❌ Not recommended (use database instead)

### Q: How do I backup history file?

**A**:
```python
import shutil
from datetime import datetime

# Backup before long-running operations
backup_path = f"artifacts/data/innovations_{datetime.now():%Y%m%d_%H%M%S}.jsonl.bak"
shutil.copy2(history.filepath, backup_path)
```

---

## Implementation Details

### File Format: JSONL

```jsonl
{"iteration_num": 0, "strategy_code": "...", "metrics": {...}, ...}
{"iteration_num": 1, "strategy_code": "...", "metrics": {...}, ...}
{"iteration_num": 2, "strategy_code": "...", "metrics": {...}, ...}
```

- One JSON object per line
- Newline-delimited
- Human-readable
- Grep-friendly

### Atomic Replace: `os.replace()`

**POSIX Guarantee** (Linux/Mac):
```
If newpath exists, it will be replaced atomically (subject to a few conditions).
```

**Windows Behavior**:
```
On Windows, if dst exists a FileExistsError is always raised.
The operation may fail if src and dst are on different filesystems.
```

**Solution**: Our implementation handles both platforms correctly.

---

## Related Documentation

- **Implementation**: `/mnt/c/Users/jnpi/Documents/finlab/src/learning/iteration_history.py`
- **Tests**: `/mnt/c/Users/jnpi/Documents/finlab/tests/learning/test_iteration_history_atomic.py`
- **Completion Report**: `/mnt/c/Users/jnpi/Documents/finlab/TASK_H1.2_ATOMIC_WRITE_COMPLETE.md`
- **Spec**: `/.spec-workflow/specs/phase3-learning-iteration/WEEK1_HARDENING_PLAN.md`

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test cases in `test_iteration_history_atomic.py`
3. Read completion report for detailed technical analysis
4. Check spec document for design rationale

---

**Last Updated**: 2025-11-04
**Version**: 1.0 (Task H1.2 Complete)
**Status**: Production Ready ✅
