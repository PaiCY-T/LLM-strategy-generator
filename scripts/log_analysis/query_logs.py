#!/usr/bin/env python3
"""
Log Query Utility for JSON Structured Logs.

Provides command-line interface for querying and analyzing JSON logs.
Supports filtering by event type, time range, iteration number, and custom fields.

Usage:
    # Query all iteration events
    python query_logs.py --event-type iteration_start --log-file logs/iterations.json.log

    # Query champion updates in time range
    python query_logs.py --event-type champion_update --since "2025-10-15" --log-file logs/iterations.json.log

    # Query failures for specific iteration
    python query_logs.py --event-type iteration_failure --iteration 42 --log-file logs/iterations.json.log

    # Query validation failures
    python query_logs.py --level ERROR --validator MetricValidator --log-file logs/iterations.json.log
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import sys


class LogQueryEngine:
    """Engine for querying JSON structured logs."""

    def __init__(self, log_file: Path):
        """
        Initialize query engine.

        Args:
            log_file: Path to JSON log file
        """
        self.log_file = log_file

    def query(
        self,
        event_type: Optional[str] = None,
        level: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        iteration_num: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query log entries matching criteria.

        Args:
            event_type: Filter by event type (e.g., "iteration_start")
            level: Filter by log level (e.g., "ERROR")
            since: Filter by timestamp >= since
            until: Filter by timestamp <= until
            iteration_num: Filter by iteration number
            filters: Additional field filters (key-value pairs)
            limit: Maximum number of results

        Returns:
            List of matching log entries
        """
        results = []

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        entry = json.loads(line.strip())

                        # Apply filters
                        if event_type and entry.get('event_type') != event_type:
                            continue

                        if level and entry.get('level') != level:
                            continue

                        if iteration_num is not None and entry.get('iteration_num') != iteration_num:
                            continue

                        # Time range filter
                        if since or until:
                            entry_time = datetime.fromisoformat(entry.get('timestamp', ''))
                            if since and entry_time < since:
                                continue
                            if until and entry_time > until:
                                continue

                        # Custom filters
                        if filters:
                            match = True
                            for key, value in filters.items():
                                if entry.get(key) != value:
                                    match = False
                                    break
                            if not match:
                                continue

                        results.append(entry)

                        # Check limit
                        if limit and len(results) >= limit:
                            break

                    except json.JSONDecodeError:
                        print(f"Warning: Skipping invalid JSON at line {line_num}", file=sys.stderr)
                        continue

        except FileNotFoundError:
            print(f"Error: Log file not found: {self.log_file}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading log file: {e}", file=sys.stderr)
            sys.exit(1)

        return results

    def aggregate_by_field(self, results: List[Dict[str, Any]], field: str) -> Dict[Any, int]:
        """
        Aggregate results by field value.

        Args:
            results: Query results
            field: Field to aggregate by

        Returns:
            Dictionary mapping field values to counts
        """
        aggregation = {}
        for entry in results:
            value = entry.get(field, 'null')
            aggregation[value] = aggregation.get(value, 0) + 1
        return aggregation


def format_results(results: List[Dict[str, Any]], output_format: str = 'table') -> str:
    """
    Format query results for display.

    Args:
        results: Query results
        output_format: 'table', 'json', or 'compact'

    Returns:
        Formatted output string
    """
    if not results:
        return "No matching log entries found."

    if output_format == 'json':
        return json.dumps(results, indent=2, ensure_ascii=False)

    elif output_format == 'compact':
        lines = []
        for entry in results:
            timestamp = entry.get('timestamp', 'N/A')
            level = entry.get('level', 'N/A')
            event_type = entry.get('event_type', 'N/A')
            message = entry.get('message', 'N/A')
            lines.append(f"[{timestamp}] {level:8} {event_type:20} {message}")
        return '\n'.join(lines)

    else:  # table format
        lines = []
        lines.append("=" * 120)
        lines.append(f"Found {len(results)} matching entries")
        lines.append("=" * 120)

        for i, entry in enumerate(results, 1):
            lines.append(f"\nEntry #{i}:")
            lines.append("-" * 120)
            for key, value in sorted(entry.items()):
                if isinstance(value, dict):
                    lines.append(f"  {key}:")
                    for k, v in value.items():
                        lines.append(f"    {k}: {v}")
                elif isinstance(value, list):
                    lines.append(f"  {key}: [{', '.join(map(str, value))}]")
                else:
                    lines.append(f"  {key}: {value}")

        lines.append("=" * 120)
        return '\n'.join(lines)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Query JSON structured logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query all iteration start events
  %(prog)s --event-type iteration_start --log-file logs/iterations.json.log

  # Query champion updates since yesterday
  %(prog)s --event-type champion_update --since 2025-10-15 --log-file logs/iterations.json.log

  # Query errors for iteration 42
  %(prog)s --level ERROR --iteration 42 --log-file logs/iterations.json.log

  # Query validation failures
  %(prog)s --event-type validation_result --filter passed=false --log-file logs/iterations.json.log
        """
    )

    # Required arguments
    parser.add_argument('--log-file', type=Path, required=True,
                        help='Path to JSON log file')

    # Filter arguments
    parser.add_argument('--event-type', type=str,
                        help='Filter by event type')
    parser.add_argument('--level', type=str,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Filter by log level')
    parser.add_argument('--iteration', type=int,
                        help='Filter by iteration number')
    parser.add_argument('--since', type=str,
                        help='Filter by timestamp >= date (ISO format)')
    parser.add_argument('--until', type=str,
                        help='Filter by timestamp <= date (ISO format)')
    parser.add_argument('--filter', action='append',
                        help='Additional filter (key=value), can be specified multiple times')

    # Output arguments
    parser.add_argument('--format', type=str, default='table',
                        choices=['table', 'json', 'compact'],
                        help='Output format')
    parser.add_argument('--limit', type=int,
                        help='Maximum number of results')
    parser.add_argument('--aggregate-by', type=str,
                        help='Aggregate results by field')

    args = parser.parse_args()

    # Parse custom filters
    custom_filters = {}
    if args.filter:
        for filter_str in args.filter:
            try:
                key, value = filter_str.split('=', 1)
                # Try to parse as JSON for type conversion
                try:
                    custom_filters[key] = json.loads(value)
                except json.JSONDecodeError:
                    custom_filters[key] = value
            except ValueError:
                print(f"Warning: Invalid filter format: {filter_str}", file=sys.stderr)

    # Parse date arguments
    since = datetime.fromisoformat(args.since) if args.since else None
    until = datetime.fromisoformat(args.until) if args.until else None

    # Execute query
    engine = LogQueryEngine(args.log_file)
    results = engine.query(
        event_type=args.event_type,
        level=args.level,
        since=since,
        until=until,
        iteration_num=args.iteration,
        filters=custom_filters if custom_filters else None,
        limit=args.limit
    )

    # Aggregate if requested
    if args.aggregate_by:
        aggregation = engine.aggregate_by_field(results, args.aggregate_by)
        print(f"\nAggregation by '{args.aggregate_by}':")
        print("=" * 60)
        for value, count in sorted(aggregation.items(), key=lambda x: x[1], reverse=True):
            print(f"  {value}: {count}")
        print("=" * 60)
        print(f"\nTotal entries: {sum(aggregation.values())}")
    else:
        # Display results
        output = format_results(results, args.format)
        print(output)


if __name__ == '__main__':
    main()
