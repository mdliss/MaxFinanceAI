import json
import csv

# Read the JSON file
with open('evaluation_metrics.json', 'r') as f:
    data = json.load(f)

# Create CSV for recommendation quality metrics
with open('recommendation_quality_metrics.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Metric', 'Value'])
    quality = data['recommendation_quality']
    for key, value in quality.items():
        if key != 'content_type_distribution':
            writer.writerow([key, value])

    # Add content type distribution
    writer.writerow(['', ''])
    writer.writerow(['Content Type', 'Count'])
    for content_type, count in quality['content_type_distribution'].items():
        writer.writerow([content_type, count])

# Create CSV for system performance metrics
with open('system_performance_metrics.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Metric', 'Value'])
    for key, value in data['system_performance'].items():
        writer.writerow([key, value])

# Create CSV for user outcome metrics
with open('user_outcome_metrics.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Metric', 'Value'])
    outcomes = data['user_outcomes']
    for key, value in outcomes.items():
        if key != 'persona_distribution':
            writer.writerow([key, value])

    # Add persona distribution
    writer.writerow(['', ''])
    writer.writerow(['Persona Type', 'Count'])
    for persona, count in outcomes['persona_distribution'].items():
        writer.writerow([persona, count])

# Create CSV for guardrail effectiveness metrics
with open('guardrail_effectiveness_metrics.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Metric', 'Value'])
    guardrails = data['guardrail_effectiveness']

    # Basic metrics
    writer.writerow(['eligibility_rate', guardrails['eligibility_rate']])
    writer.writerow(['eligible_users', guardrails['eligible_users']])
    writer.writerow(['total_users_checked', guardrails['total_users_checked']])
    writer.writerow(['rate_limit_violations', guardrails['rate_limit_violations']])
    writer.writerow(['content_safety_enabled', guardrails['content_safety_enabled']])

    # Ineligibility reasons
    writer.writerow(['', ''])
    writer.writerow(['Ineligibility Reason', 'Count'])
    for reason, count in guardrails['ineligibility_reasons'].items():
        writer.writerow([reason, count])

    # Vulnerable populations
    writer.writerow(['', ''])
    writer.writerow(['Vulnerable Population', 'Count'])
    for population, count in guardrails['vulnerable_populations'].items():
        writer.writerow([population, count])

# Create comprehensive summary CSV
with open('evaluation_summary.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Category', 'Metric', 'Value', 'Target', 'Status'])

    # Recommendation Quality
    quality = data['recommendation_quality']
    writer.writerow(['Recommendation Quality', 'Relevance Score', quality['relevance_score'], '0.8+', 'Pass' if quality['relevance_score'] >= 0.8 else 'Fail'])
    writer.writerow(['Recommendation Quality', 'Diversity Score', quality['diversity_score'], '0.6+', 'Pass' if quality['diversity_score'] >= 0.6 else 'Fail'])
    writer.writerow(['Recommendation Quality', 'Coverage Rate', quality['coverage_rate'], '0.8+', 'Warning' if quality['coverage_rate'] < 0.8 else 'Pass'])
    writer.writerow(['Recommendation Quality', 'Personalization Score', quality['personalization_score'], '0.9+', 'Pass' if quality['personalization_score'] >= 0.9 else 'Fail'])

    # System Performance
    perf = data['system_performance']
    writer.writerow(['System Performance', 'Total Recommendations', perf['total_recommendations_generated'], '100+', 'Pass' if perf['total_recommendations_generated'] >= 100 else 'Fail'])
    writer.writerow(['System Performance', 'Unique Users Processed', perf['unique_users_processed'], '30+', 'Pass' if perf['unique_users_processed'] >= 30 else 'Fail'])

    # User Outcomes
    outcomes = data['user_outcomes']
    writer.writerow(['User Outcomes', 'Approval Rate', outcomes['approval_rate'], '0.7+', 'Pass' if outcomes['approval_rate'] >= 0.7 else 'Fail'])
    writer.writerow(['User Outcomes', 'Consent Rate', outcomes['consent_rate'], '0.6+', 'Pass' if outcomes['consent_rate'] >= 0.6 else 'Fail'])

    # Guardrail Effectiveness
    guardrails = data['guardrail_effectiveness']
    writer.writerow(['Guardrail Effectiveness', 'Eligibility Rate', guardrails['eligibility_rate'], 'N/A', 'Info'])
    writer.writerow(['Guardrail Effectiveness', 'Rate Limit Violations', guardrails['rate_limit_violations'], '0', 'Pass' if guardrails['rate_limit_violations'] == 0 else 'Fail'])

print("CSV files generated successfully!")
print("- recommendation_quality_metrics.csv")
print("- system_performance_metrics.csv")
print("- user_outcome_metrics.csv")
print("- guardrail_effectiveness_metrics.csv")
print("- evaluation_summary.csv")
