#!/usr/bin/env python3
"""Extract available Finlab datasets from CSV for prompt template."""

import csv
from pathlib import Path


def extract_datasets(csv_path: str) -> list[str]:
    """Extract dataset keys from CSV file.

    Args:
        csv_path: Path to finlab_database_cleaned.csv

    Returns:
        List of dataset keys (second column)
    """
    datasets = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header

        for row in reader:
            if len(row) >= 2:
                dataset_key = row[1].strip()
                if dataset_key:
                    datasets.append(dataset_key)

    return sorted(datasets)


def format_for_prompt(datasets: list[str]) -> str:
    """Format datasets for prompt template.

    Args:
        datasets: List of dataset keys

    Returns:
        Formatted string for prompt
    """
    # Group by category for better readability
    categories = {}

    for key in datasets:
        category = key.split(':')[0] if ':' in key else 'other'
        if category not in categories:
            categories[category] = []
        categories[category].append(key)

    # Format output
    lines = ["Available Finlab datasets (use data.get('key')):"]
    lines.append("")

    for category in sorted(categories.keys()):
        lines.append(f"## {category}")
        for key in sorted(categories[category]):
            lines.append(f"- {key}")
        lines.append("")

    return '\n'.join(lines)


def main():
    """Main function."""
    csv_path = '/mnt/c/Users/jnpi/ML4T/epic-finlab-data-downloader/example/finlab_database_cleaned.csv'

    # Extract datasets
    datasets = extract_datasets(csv_path)

    print(f"Total datasets: {len(datasets)}")
    print()
    print(format_for_prompt(datasets))

    # Also save to file for reference
    output_path = Path(__file__).parent / 'available_datasets.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(format_for_prompt(datasets))

    print(f"\n✅ Saved to {output_path}")


if __name__ == '__main__':
    main()
