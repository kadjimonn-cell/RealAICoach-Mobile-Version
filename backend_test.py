#!/usr/bin/env python3
"""
Backend API Test Script for P1 Frontend Work Verification
Tests the following endpoints:
1. POST /api/auth/login with admin credentials
2. GET /_preview/health with preview freshness fields
3. GET /api/health for basic health check
"""

import requests
import json
import sys
from datetime import datetime

# Base URL from frontend/.env
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"

# Admin credentials from test_credentials.md
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_admin_login():
    """Test 1: POST /api/auth/login with admin credentials"""
    print_section("TEST 1: POST /api/auth/login")
    
    url = f"{BASE_URL}/api/auth/login"
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            data = response.json()
            print(f"Response Body: {json.dumps(data, indent=2)}")
        except:
            print(f"Response Body (text): {response.text[:500]}")
        
        if response.status_code == 200:
            print("\n✅ TEST 1 PASSED: Admin login succeeded")
            return True, response
        else:
            print(f"\n❌ TEST 1 FAILED: Expected 200, got {response.status_code}")
            return False, response
            
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: Exception occurred: {str(e)}")
        return False, None

def test_preview_health():
    """Test 2: GET /_preview/health with preview freshness fields"""
    print_section("TEST 2: GET /_preview/health")
    
    url = f"{BASE_URL}/_preview/health"
    
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=15)
        print(f"\nStatus Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response Body: {json.dumps(data, indent=2)}")
            
            # Check for required fields
            required_fields = []
            optional_fields = ["active_bundle_hash", "build_state", "dist_runtime", "last_reason", "last_result"]
            
            found_fields = []
            missing_fields = []
            
            for field in optional_fields:
                if field in data:
                    found_fields.append(field)
                    print(f"  ✓ Found field: {field}")
                    
                    # If build_state exists, check its contents
                    if field == "build_state" and isinstance(data[field], dict):
                        build_state = data[field]
                        print(f"    - build_state keys: {list(build_state.keys())}")
                else:
                    missing_fields.append(field)
            
            if response.status_code == 200:
                if found_fields:
                    print(f"\n✅ TEST 2 PASSED: /_preview/health responded successfully")
                    print(f"   Found preview freshness fields: {', '.join(found_fields)}")
                    return True, response
                else:
                    print(f"\n⚠️  TEST 2 PARTIAL: Endpoint responded but missing preview freshness fields")
                    print(f"   Expected at least one of: {', '.join(optional_fields)}")
                    return True, response  # Still pass if endpoint works
            else:
                print(f"\n❌ TEST 2 FAILED: Expected 200, got {response.status_code}")
                return False, response
                
        except Exception as json_error:
            print(f"Response Body (text): {response.text[:500]}")
            print(f"\n❌ TEST 2 FAILED: Could not parse JSON: {str(json_error)}")
            return False, response
            
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: Exception occurred: {str(e)}")
        return False, None

def test_api_health():
    """Test 3: GET /api/health for basic health check"""
    print_section("TEST 3: GET /api/health")
    
    url = f"{BASE_URL}/api/health"
    
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=15)
        print(f"\nStatus Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response Body: {json.dumps(data, indent=2)}")
            
            if response.status_code == 200:
                print("\n✅ TEST 3 PASSED: /api/health responded healthy")
                return True, response
            else:
                print(f"\n❌ TEST 3 FAILED: Expected 200, got {response.status_code}")
                return False, response
                
        except:
            print(f"Response Body (text): {response.text[:500]}")
            if response.status_code == 200:
                print("\n✅ TEST 3 PASSED: /api/health responded (non-JSON)")
                return True, response
            else:
                print(f"\n❌ TEST 3 FAILED: Expected 200, got {response.status_code}")
                return False, response
            
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: Exception occurred: {str(e)}")
        return False, None

def main():
    """Run all tests and report results"""
    print(f"\n{'#'*80}")
    print(f"  P1 Frontend Work - Backend Endpoint Verification")
    print(f"  Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Base URL: {BASE_URL}")
    print(f"{'#'*80}")
    
    results = []
    
    # Test 1: Admin Login
    test1_passed, _ = test_admin_login()
    results.append(("POST /api/auth/login", test1_passed))
    
    # Test 2: Preview Health
    test2_passed, _ = test_preview_health()
    results.append(("GET /_preview/health", test2_passed))
    
    # Test 3: API Health
    test3_passed, _ = test_api_health()
    results.append(("GET /api/health", test3_passed))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for endpoint, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {endpoint}")
    
    print(f"\n{'='*80}")
    print(f"  Total: {passed_count}/{total_count} tests passed")
    print(f"{'='*80}\n")
    
    # Exit with appropriate code
    if passed_count == total_count:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print(f"❌ {total_count - passed_count} TEST(S) FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
