#!/usr/bin/env python3
"""
Export evaluation metrics to CSV format
"""
import json
import csv
import sys
from pathlib import Path


def flatten_dict(d, parent_key='', sep='_'):
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def main():
    # Read JSON metrics
    json_path = Path(__file__).parent.parent / "evaluation_reports" / "evaluation_metrics.json"

    if not json_path.exists():
        print(f"Error: {json_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(json_path, 'r') as f:
        metrics = json.load(f)

    # Flatten the nested structure
    flat_metrics = flatten_dict(metrics)

    # Write to CSV
    csv_path = json_path.parent / "evaluation_metrics.csv"

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value'])
        for key, value in sorted(flat_metrics.items()):
            writer.writerow([key, value])

    print(f"CSV exported to: {csv_path}")

    # Also create a summary CSV with key metrics
    summary_path = json_path.parent / "evaluation_summary.csv"

    key_metrics = {
        'Timestamp': metrics.get('timestamp', 'N/A'),
        'Total Recommendations': metrics['recommendation_quality'].get('total_recommendations', 0),
        'Relevance Score': metrics['recommendation_quality'].get('relevance_score', 0),
        'Diversity Score': metrics['recommendation_quality'].get('diversity_score', 0),
        'Coverage Rate': metrics['recommendation_quality'].get('coverage_rate', 0),
        'Personalization Score': metrics['recommendation_quality'].get('personalization_score', 0),
        'Approval Rate': metrics['user_outcomes'].get('approval_rate', 0),
        'Rejection Rate': metrics['user_outcomes'].get('rejection_rate', 0),
        'Eligibility Rate': metrics['guardrail_effectiveness'].get('eligibility_rate', 0),
        'Total Users': metrics['user_outcomes'].get('total_users', 0),
        'Users with Signals': metrics['user_outcomes'].get('users_with_signals', 0),
        'Signal Detection Rate': metrics['user_outcomes'].get('signal_detection_rate', 0),
        'Consent Rate': metrics['user_outcomes'].get('consent_rate', 0),
    }

    with open(summary_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value'])
        for key, value in key_metrics.items():
            writer.writerow([key, value])

    print(f"Summary CSV exported to: {summary_path}")


if __name__ == '__main__':
    main()
