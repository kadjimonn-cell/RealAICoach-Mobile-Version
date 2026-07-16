#!/usr/bin/env python3
"""
Quick backend sanity check after frontend-only alias policy update.
Tests:
1) GET /api/health => expect 200
2) GET /api/auth/me without auth => expect 401
"""

import requests
import sys

BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"

def test_health_endpoint():
    """Test 1: GET /api/health => expect 200"""
    url = f"{BASE_URL}/api/health"
    try:
        response = requests.get(url, timeout=10)
        status = response.status_code
        if status == 200:
            return True, status, "PASS"
        else:
            return False, status, f"FAIL - Expected 200, got {status}"
    except Exception as e:
        return False, None, f"FAIL - Exception: {str(e)}"

def test_auth_me_unauthenticated():
    """Test 2: GET /api/auth/me without auth => expect 401"""
    url = f"{BASE_URL}/api/auth/me"
    try:
        # No cookies or auth headers
        response = requests.get(url, timeout=10)
        status = response.status_code
        if status == 401:
            return True, status, "PASS"
        else:
            return False, status, f"FAIL - Expected 401, got {status}"
    except Exception as e:
        return False, None, f"FAIL - Exception: {str(e)}"

def main():
    print("=" * 60)
    print("Backend Sanity Check - Frontend-Only Alias Policy Update")
    print(f"Base URL: {BASE_URL}")
    print("=" * 60)
    
    # Test 1: Health endpoint
    print("\n[Test 1] GET /api/health")
    success1, status1, result1 = test_health_endpoint()
    print(f"  Status Code: {status1}")
    print(f"  Result: {result1}")
    
    # Test 2: Auth me without auth
    print("\n[Test 2] GET /api/auth/me (unauthenticated)")
    success2, status2, result2 = test_auth_me_unauthenticated()
    print(f"  Status Code: {status2}")
    print(f"  Result: {result2}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Test 1 (Health): {'✅ PASS' if success1 else '❌ FAIL'} - Status {status1}")
    print(f"Test 2 (Auth Me): {'✅ PASS' if success2 else '❌ FAIL'} - Status {status2}")
    
    all_passed = success1 and success2
    print("\n" + "=" * 60)
    if all_passed:
        print("FINAL VERDICT: ✅ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("FINAL VERDICT: ❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
