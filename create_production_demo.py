#!/usr/bin/env python3
"""
Create demo user in production via API calls.
Usage: python3 create_production_demo.py <PRODUCTION_API_URL>
Example: python3 create_production_demo.py https://your-app.railway.app/api/v1
"""
import requests
import sys
import json
from datetime import datetime, timedelta, timezone
import random

def create_demo_user(api_url):
    """Create comprehensive demo user via API"""

    # Remove trailing slash
    api_url = api_url.rstrip('/')

    print(f"Creating demo user at: {api_url}")

    # 1. Create user
    print("\n1. Creating user...")
    user_data = {
        "user_id": "demo",
        "name": "Demo User",
        "age": 35,
        "income_level": "medium"
    }

    response = requests.post(f"{api_url}/users/", json=user_data)
    if response.status_code == 201:
        print("✅ User created")
    elif response.status_code == 400 and "already exists" in response.text:
        print("⚠️  User already exists, continuing...")
    else:
        print(f"❌ Failed to create user: {response.status_code} - {response.text}")
        return False

    # 2. Grant consent
    print("\n2. Granting consent...")
    consent_data = {
        "user_id": "demo",
        "consent_status": True
    }

    response = requests.post(f"{api_url}/consent", json=consent_data)
    if response.status_code in [200, 201]:
        print("✅ Consent granted")
    else:
        print(f"⚠️  Consent response: {response.status_code}")

    # 3. Check current stats
    print("\n3. Checking production stats...")
    response = requests.get(f"{api_url}/operator/dashboard/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"  Total users: {stats['total_users']}")
        print(f"  Total signals: {stats['total_signals']}")
        print(f"  Total recommendations: {stats['total_recommendations']}")

    # 4. Check coverage
    print("\n4. Checking coverage...")
    response = requests.get(f"{api_url}/operator/evaluation/metrics")
    if response.status_code == 200:
        metrics = response.json()
        coverage = metrics['coverage']
        print(f"  Coverage: {coverage['coverage_percentage']}%")
        print(f"  Users with 3+ behaviors: {coverage['users_with_3plus_behaviors']}/{coverage['total_users']}")

        if coverage['coverage_percentage'] < 100:
            print(f"\n⚠️  Coverage is {coverage['coverage_percentage']}%, not 100%")
            print(f"  Missing: {coverage['total_users'] - coverage['users_with_3plus_behaviors']} users")

    print("\n✅ Demo user setup complete!")
    print("\nYou can now log in with user_id: demo")
    print(f"Login at: {api_url.replace('/api/v1', '')}/login")

    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 create_production_demo.py <PRODUCTION_API_URL>")
        print("Example: python3 create_production_demo.py https://your-app.railway.app/api/v1")
        sys.exit(1)

    api_url = sys.argv[1]
    create_demo_user(api_url)
