#!/usr/bin/env python3
"""
Feature 15 Route-Hardening Backend Smoke Validation
Test the following endpoints:
1. POST /api/auth/login - should return 200
2. GET /api/auth/me - should return authenticated user
3. GET /api/video-studio/bootstrap - should return 200
4. GET /api/video-studio/health - should return 200
"""

import requests
import json
import sys

# Configuration
BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"
TEST_EMAIL = "p1.free.1779113329@example.com"
TEST_PASSWORD = "P1Free#2026!Aa"

# Test results
results = {
    "total": 4,
    "passed": 0,
    "failed": 0,
    "tests": []
}

def log_test(name, passed, status_code=None, details=None):
    """Log test result"""
    result = {
        "name": name,
        "passed": passed,
        "status_code": status_code,
        "details": details
    }
    results["tests"].append(result)
    if passed:
        results["passed"] += 1
        print(f"✅ PASS: {name} (status: {status_code})")
    else:
        results["failed"] += 1
        print(f"❌ FAIL: {name} (status: {status_code}) - {details}")

def main():
    print("=" * 80)
    print("Feature 15 Route-Hardening Backend Smoke Validation")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_EMAIL}")
    print()

    # Create session to persist cookies
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    })

    # Test 1: POST /api/auth/login
    print("Test 1: POST /api/auth/login")
    print("-" * 80)
    try:
        login_url = f"{BASE_URL}/api/auth/login"
        login_payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = session.post(login_url, json=login_payload, timeout=30)
        
        if response.status_code == 200:
            log_test("POST /api/auth/login", True, response.status_code, "Login successful")
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print(f"   Response: {response.text[:200]}...")
        else:
            log_test("POST /api/auth/login", False, response.status_code, f"Expected 200, got {response.status_code}")
            print(f"   Response: {response.text[:500]}")
    except Exception as e:
        log_test("POST /api/auth/login", False, None, str(e))
        print(f"   Error: {e}")
    
    print()

    # Test 2: GET /api/auth/me (using session cookie)
    print("Test 2: GET /api/auth/me (with session cookie)")
    print("-" * 80)
    try:
        me_url = f"{BASE_URL}/api/auth/me"
        response = session.get(me_url, timeout=30)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if "email" in data or "user_id" in data or "id" in data:
                    log_test("GET /api/auth/me", True, response.status_code, "Authenticated user returned")
                    print(f"   User: {data.get('email', data.get('user_id', data.get('id', 'unknown')))}")
                    print(f"   Response keys: {list(data.keys())[:10]}")
                else:
                    log_test("GET /api/auth/me", False, response.status_code, "Response missing user data")
                    print(f"   Response: {json.dumps(data, indent=2)[:300]}")
            except:
                log_test("GET /api/auth/me", False, response.status_code, "Invalid JSON response")
                print(f"   Response: {response.text[:500]}")
        else:
            log_test("GET /api/auth/me", False, response.status_code, f"Expected 200, got {response.status_code}")
            print(f"   Response: {response.text[:500]}")
    except Exception as e:
        log_test("GET /api/auth/me", False, None, str(e))
        print(f"   Error: {e}")
    
    print()

    # Test 3: GET /api/video-studio/bootstrap (using session cookie)
    print("Test 3: GET /api/video-studio/bootstrap (with session cookie)")
    print("-" * 80)
    try:
        bootstrap_url = f"{BASE_URL}/api/video-studio/bootstrap"
        response = session.get(bootstrap_url, timeout=30)
        
        if response.status_code == 200:
            log_test("GET /api/video-studio/bootstrap", True, response.status_code, "Bootstrap data returned")
            try:
                data = response.json()
                print(f"   Response keys: {list(data.keys())[:10]}")
                print(f"   Response preview: {json.dumps(data, indent=2)[:300]}...")
            except:
                print(f"   Response: {response.text[:300]}...")
        else:
            log_test("GET /api/video-studio/bootstrap", False, response.status_code, f"Expected 200, got {response.status_code}")
            print(f"   Response: {response.text[:500]}")
    except Exception as e:
        log_test("GET /api/video-studio/bootstrap", False, None, str(e))
        print(f"   Error: {e}")
    
    print()

    # Test 4: GET /api/video-studio/health (no auth required)
    print("Test 4: GET /api/video-studio/health (public endpoint)")
    print("-" * 80)
    try:
        health_url = f"{BASE_URL}/api/video-studio/health"
        # Use a fresh session without auth to test public access
        response = requests.get(health_url, timeout=30)
        
        if response.status_code == 200:
            log_test("GET /api/video-studio/health", True, response.status_code, "Health check passed")
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            except:
                print(f"   Response: {response.text[:300]}")
        else:
            log_test("GET /api/video-studio/health", False, response.status_code, f"Expected 200, got {response.status_code}")
            print(f"   Response: {response.text[:500]}")
    except Exception as e:
        log_test("GET /api/video-studio/health", False, None, str(e))
        print(f"   Error: {e}")
    
    print()
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {(results['passed'] / results['total'] * 100):.1f}%")
    print()
    
    # Print detailed results
    print("Detailed Results:")
    print("-" * 80)
    for i, test in enumerate(results["tests"], 1):
        status = "✅ PASS" if test["passed"] else "❌ FAIL"
        print(f"{i}. {status}: {test['name']}")
        print(f"   Status Code: {test['status_code']}")
        print(f"   Details: {test['details']}")
        print()
    
    # Exit with appropriate code
    if results["failed"] > 0:
        print("❌ SMOKE VALIDATION FAILED")
        sys.exit(1)
    else:
        print("✅ SMOKE VALIDATION PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
