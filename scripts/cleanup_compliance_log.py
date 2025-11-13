#!/usr/bin/env python3
"""Clean up duplicate entries in liquidity_compliance.json."""
import json
from datetime import datetime

def cleanup_compliance_log():
    """Remove duplicate entries, keeping first occurrence of each iteration."""
    log_file = 'liquidity_compliance.json'

    # Read corrupted log
    with open(log_file, 'r', encoding='utf-8') as f:
        log_data = json.load(f)

    print(f"Original log: {len(log_data['checks'])} total checks")

    # Deduplicate: keep first occurrence of each iteration
    seen = set()
    deduplicated_checks = []
    duplicates_removed = 0

    for check in log_data['checks']:
        iter_num = check['iteration']
        if iter_num not in seen:
            seen.add(iter_num)
            deduplicated_checks.append(check)
        else:
            duplicates_removed += 1

    print(f"Removed {duplicates_removed} duplicate entries")
    print(f"Deduplicated log: {len(deduplicated_checks)} unique iterations")

    # Update log with deduplicated data
    log_data['checks'] = deduplicated_checks

    # Update summary
    log_data['summary']['total_checks'] = len(log_data['checks'])
    log_data['summary']['compliant_count'] = sum(
        1 for c in log_data['checks'] if c.get('compliant', False)
    )
    log_data['summary']['compliance_rate'] = (
        log_data['summary']['compliant_count'] / log_data['summary']['total_checks']
        if log_data['summary']['total_checks'] > 0 else 0.0
    )
    log_data['summary']['last_updated'] = datetime.now().isoformat()

    # Atomic write
    temp_file = log_file + '.tmp'
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    import os
    os.replace(temp_file, log_file)

    print(f"✅ Cleanup complete!")
    print(f"   Total checks: {log_data['summary']['total_checks']}")
    print(f"   Compliant: {log_data['summary']['compliant_count']}")
    print(f"   Compliance rate: {log_data['summary']['compliance_rate']:.1%}")

if __name__ == '__main__':
    cleanup_compliance_log()
