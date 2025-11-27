"""
Fix emoji characters in critical path files for Windows cp950 compatibility.

This script replaces emoji characters with ASCII alternatives in the 5 critical
files that cause JSON mode test failures.

Files fixed:
1. src/learning/llm_client.py
2. src/learning/iteration_executor.py
3. src/learning/learning_loop.py
4. src/innovation/llm_providers.py
5. src/innovation/structured_validator.py
"""

import re
from pathlib import Path

# Emoji to ASCII mapping
EMOJI_MAP = {
    '✓': '[OK]',
    '✅': '[PASS]',
    '❌': '[FAIL]',
    '⚠️': '[WARN]',
    '⚠': '[WARN]',  # Plain warning sign without variation selector
    '💡': '[INFO]',
    '🔧': '[CFG]',
    '📊': '[DATA]',
    '🚨': '[ALERT]',
    '🎯': '[TARGET]',
    '🔍': '[SEARCH]',
}

# Critical files to fix (in order of importance)
CRITICAL_FILES = [
    'src/innovation/llm_providers.py',          # Root cause: JSON validation warnings
    'src/innovation/structured_validator.py',   # Related: structured validation
    'src/learning/learning_loop.py',            # Loop completion logging
    'src/learning/iteration_executor.py',       # Iteration execution logging
    'src/learning/llm_client.py',               # LLM client initialization
]

def replace_emojis(text: str) -> tuple[str, int]:
    """Replace all emojis with ASCII alternatives.

    Returns:
        (modified_text, replacement_count)
    """
    count = 0
    for emoji, ascii_alt in EMOJI_MAP.items():
        if emoji in text:
            occurrences = text.count(emoji)
            text = text.replace(emoji, ascii_alt)
            count += occurrences
    return text, count

def fix_file(file_path: Path) -> tuple[bool, int]:
    """Fix emojis in a single file.

    Returns:
        (was_modified, replacement_count)
    """
    if not file_path.exists():
        print(f"[SKIP] File not found: {file_path}")
        return False, 0

    # Read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        print(f"[ERROR] Failed to read {file_path}: {e}")
        return False, 0

    # Replace emojis
    modified_content, count = replace_emojis(original_content)

    if count == 0:
        print(f"[SKIP] No emojis found in {file_path}")
        return False, 0

    # Write back
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f"[OK] Fixed {count} emojis in {file_path}")
        return True, count
    except Exception as e:
        print(f"[ERROR] Failed to write {file_path}: {e}")
        return False, 0

def main():
    """Fix emojis in all critical files."""
    print("=" * 80)
    print("Fixing Emoji Characters in Critical Path Files")
    print("=" * 80)
    print()

    base_path = Path(__file__).parent
    total_files_modified = 0
    total_replacements = 0

    for file_rel_path in CRITICAL_FILES:
        file_path = base_path / file_rel_path
        print(f"\nProcessing: {file_rel_path}")
        was_modified, count = fix_file(file_path)

        if was_modified:
            total_files_modified += 1
            total_replacements += count

    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Files modified: {total_files_modified}/{len(CRITICAL_FILES)}")
    print(f"Total replacements: {total_replacements}")
    print()

    if total_files_modified > 0:
        print("Next steps:")
        print("1. Review changes with: git diff")
        print("2. Test with: python test_json_config.py")
        print("3. Commit with: git add src/ && git commit -m 'fix: Replace emoji with ASCII in critical path files'")
        print("4. Run full test: python run_json_mode_test_20.py")
    else:
        print("[INFO] No changes made - emojis already fixed or files not found")

if __name__ == '__main__':
    main()
