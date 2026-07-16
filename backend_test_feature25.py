#!/usr/bin/env python3
"""
Feature 25 (Daily Meditation) Backend Smoke Validation
Test against: https://admin-policy-hub.preview.emergentagent.com
"""

import requests
import json
import sys

# Configuration
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
FREE_USER_EMAIL = "p1.free.1779113329@example.com"
FREE_USER_PASSWORD = "P1Free#2026!Aa"

# Test results
results = {
    "feature": "Feature 25 - Daily Meditation",
    "test_type": "Backend Smoke Validation",
    "base_url": BASE_URL,
    "user_tier": "free",
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0
    }
}

def log_test(name, status, details):
    """Log test result"""
    results["tests"].append({
        "name": name,
        "status": status,
        "details": details
    })
    results["summary"]["total"] += 1
    if status == "PASS":
        results["summary"]["passed"] += 1
    else:
        results["summary"]["failed"] += 1
    
    status_icon = "✅" if status == "PASS" else "❌"
    print(f"{status_icon} {name}: {status}")
    if details:
        print(f"   Details: {details}")

def test_login():
    """Test 1: Login with free user credentials"""
    print("\n=== Test 1: Login ===")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": FREE_USER_EMAIL,
                "password": FREE_USER_PASSWORD
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            cookies = response.cookies
            log_test(
                "Login with free user",
                "PASS",
                f"Status: {response.status_code}, User ID: {data.get('user_id', 'N/A')}"
            )
            return cookies, data.get('user_id')
        else:
            log_test(
                "Login with free user",
                "FAIL",
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
            return None, None
    except Exception as e:
        log_test("Login with free user", "FAIL", f"Exception: {str(e)}")
        return None, None

def test_auth_me(cookies):
    """Test 2: Verify /api/auth/me returns 200 and subscription_plan=free"""
    print("\n=== Test 2: /api/auth/me ===")
    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            cookies=cookies,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            subscription_plan = data.get('subscription_plan', 'N/A')
            
            if subscription_plan == 'free':
                log_test(
                    "/api/auth/me",
                    "PASS",
                    f"Status: 200, subscription_plan: {subscription_plan}"
                )
            else:
                log_test(
                    "/api/auth/me",
                    "FAIL",
                    f"Status: 200, but subscription_plan is '{subscription_plan}' (expected 'free')"
                )
        else:
            log_test(
                "/api/auth/me",
                "FAIL",
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
    except Exception as e:
        log_test("/api/auth/me", "FAIL", f"Exception: {str(e)}")

def test_daily_meditation_overview(cookies, user_id):
    """Test 3: GET /api/travel-visa/daily-meditation/overview/{user_id}"""
    print("\n=== Test 3: Daily Meditation Overview ===")
    try:
        response = requests.get(
            f"{BASE_URL}/api/travel-visa/daily-meditation/overview/{user_id}",
            cookies=cookies,
            timeout=30
        )
        
        if response.status_code == 200:
            log_test(
                "GET /api/travel-visa/daily-meditation/overview/{user_id}",
                "PASS",
                f"Status: 200"
            )
        elif 500 <= response.status_code < 600:
            log_test(
                "GET /api/travel-visa/daily-meditation/overview/{user_id}",
                "FAIL",
                f"5xx Error: Status {response.status_code}, Response: {response.text[:200]}"
            )
        else:
            log_test(
                "GET /api/travel-visa/daily-meditation/overview/{user_id}",
                "FAIL",
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
    except Exception as e:
        log_test(
            "GET /api/travel-visa/daily-meditation/overview/{user_id}",
            "FAIL",
            f"Exception: {str(e)}"
        )

def test_daily_meditation_feature_map(cookies, user_id):
    """Test 4: GET /api/travel-visa/daily-meditation/feature-map?user_id={user_id}"""
    print("\n=== Test 4: Daily Meditation Feature Map ===")
    try:
        response = requests.get(
            f"{BASE_URL}/api/travel-visa/daily-meditation/feature-map",
            params={"user_id": user_id},
            cookies=cookies,
            timeout=30
        )
        
        if response.status_code == 200:
            log_test(
                "GET /api/travel-visa/daily-meditation/feature-map?user_id={user_id}",
                "PASS",
                f"Status: 200"
            )
        elif 500 <= response.status_code < 600:
            log_test(
                "GET /api/travel-visa/daily-meditation/feature-map?user_id={user_id}",
                "FAIL",
                f"5xx Error: Status {response.status_code}, Response: {response.text[:200]}"
            )
        else:
            log_test(
                "GET /api/travel-visa/daily-meditation/feature-map?user_id={user_id}",
                "FAIL",
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
    except Exception as e:
        log_test(
            "GET /api/travel-visa/daily-meditation/feature-map?user_id={user_id}",
            "FAIL",
            f"Exception: {str(e)}"
        )

def test_daily_meditation_progress(cookies, user_id):
    """Test 5: GET /api/travel-visa/daily-meditation/progress/{user_id}"""
    print("\n=== Test 5: Daily Meditation Progress ===")
    try:
        response = requests.get(
            f"{BASE_URL}/api/travel-visa/daily-meditation/progress/{user_id}",
            cookies=cookies,
            timeout=30
        )
        
        if response.status_code == 200:
            log_test(
                "GET /api/travel-visa/daily-meditation/progress/{user_id}",
                "PASS",
                f"Status: 200"
            )
        elif 500 <= response.status_code < 600:
            log_test(
                "GET /api/travel-visa/daily-meditation/progress/{user_id}",
                "FAIL",
                f"5xx Error: Status {response.status_code}, Response: {response.text[:200]}"
            )
        else:
            log_test(
                "GET /api/travel-visa/daily-meditation/progress/{user_id}",
                "FAIL",
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
    except Exception as e:
        log_test(
            "GET /api/travel-visa/daily-meditation/progress/{user_id}",
            "FAIL",
            f"Exception: {str(e)}"
        )

def main():
    """Run all tests"""
    print("=" * 80)
    print("Feature 25 (Daily Meditation) Backend Smoke Validation")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"User: {FREE_USER_EMAIL} (free tier)")
    print("=" * 80)
    
    # Test 1: Login
    cookies, user_id = test_login()
    if not cookies or not user_id:
        print("\n❌ CRITICAL: Login failed. Cannot proceed with remaining tests.")
        print_summary()
        sys.exit(1)
    
    # Test 2: /api/auth/me
    test_auth_me(cookies)
    
    # Test 3: Daily Meditation Overview
    test_daily_meditation_overview(cookies, user_id)
    
    # Test 4: Daily Meditation Feature Map
    test_daily_meditation_feature_map(cookies, user_id)
    
    # Test 5: Daily Meditation Progress
    test_daily_meditation_progress(cookies, user_id)
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    if results["summary"]["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

def print_summary():
    """Print test summary"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']} ✅")
    print(f"Failed: {results['summary']['failed']} ❌")
    
    if results["summary"]["failed"] == 0:
        print("\n✅ ALL TESTS PASSED")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    print("=" * 80)
    
    # Print detailed results
    print("\nDETAILED RESULTS:")
    for test in results["tests"]:
        status_icon = "✅" if test["status"] == "PASS" else "❌"
        print(f"{status_icon} {test['name']}: {test['status']}")
        if test["details"]:
            print(f"   {test['details']}")

if __name__ == "__main__":
    main()
