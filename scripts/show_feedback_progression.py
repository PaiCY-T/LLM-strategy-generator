#!/usr/bin/env python3
"""Show feedback progression across iterations."""
from iteration_engine import create_nl_summary
import json

# Load real data
with open('iteration_history.json') as f:
    data = json.load(f)
    records = data.get('records', [])

# Show feedback progression for iterations 0, 1, 5
for i in [0, 1, 5]:
    if i < len(records):
        print('\n' + '='*70)
        print(f'ITERATION {i} FEEDBACK')
        print('='*70)
        record = records[i]
        metrics = record.get('metrics', {})
        code = record.get('code', '')

        # Show key metrics
        sharpe = metrics.get('sharpe_ratio', 0)
        ret = metrics.get('total_return', 0)
        dd = metrics.get('max_drawdown', 0)
        print(f'\nMetrics: Sharpe={sharpe:.4f}, Return={ret:.2%}, DD={dd:.2%}')
        print('\nFeedback Preview (first 800 chars):')
        print('-'*70)
        feedback = create_nl_summary(metrics, code, i)
        print(feedback[:800] + '...\n')
