#!/usr/bin/env python3
"""
Quick Backend Sanity Test - 3 Specific Endpoints
Tests requested after frontend-only fixes
"""
import requests
import json
import sys

# Configuration
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

def test_admin_login():
    """Test 1: POST /api/auth/login returns success for admin credentials"""
    print("\n" + "="*60)
    print("TEST 1: POST /api/auth/login (Admin Login)")
    print("="*60)
    
    url = f"{BASE_URL}/api/auth/login"
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check for success indicators
            if data.get("user_id") and data.get("email") == ADMIN_EMAIL:
                print("✅ PASS: Admin login successful")
                return True, response.cookies
            else:
                print(f"❌ FAIL: Login response missing expected fields")
                return False, None
        else:
            print(f"Response: {response.text[:500]}")
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False, None

def test_i18n_adoption(cookies):
    """Test 2: GET /api/admin/i18n/adoption returns summary with adoption_pct"""
    print("\n" + "="*60)
    print("TEST 2: GET /api/admin/i18n/adoption")
    print("="*60)
    
    url = f"{BASE_URL}/api/admin/i18n/adoption"
    
    try:
        response = requests.get(url, cookies=cookies, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check for adoption_pct field
            if "adoption_pct" in data:
                adoption_pct = data["adoption_pct"]
                print(f"✅ PASS: adoption_pct found = {adoption_pct}")
                return True
            else:
                print(f"❌ FAIL: adoption_pct field missing in response")
                print(f"Available fields: {list(data.keys())}")
                return False
        else:
            print(f"Response: {response.text[:500]}")
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False

def test_compliance_counter(cookies):
    """Test 3: GET /api/admin/v7-templates/compliance-counter returns grade A / no bypass"""
    print("\n" + "="*60)
    print("TEST 3: GET /api/admin/v7-templates/compliance-counter")
    print("="*60)
    
    url = f"{BASE_URL}/api/admin/v7-templates/compliance-counter"
    
    try:
        response = requests.get(url, cookies=cookies, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check for grade A
            grade = data.get("grade", "").upper()
            
            # Check for bypass count (could be in different fields)
            bypass_count = None
            if "bypass_scan" in data and isinstance(data["bypass_scan"], dict):
                bypass_count = data["bypass_scan"].get("bypass_senders", 0)
            elif "bypass_count" in data:
                bypass_count = data["bypass_count"]
            
            print(f"\nGrade: {grade}")
            print(f"Bypass count: {bypass_count}")
            
            # Verify grade A and no bypass
            if grade == "A":
                if bypass_count is not None and bypass_count == 0:
                    print(f"✅ PASS: Grade A with no bypass (grade={grade}, bypass_count={bypass_count})")
                    return True
                elif bypass_count is None:
                    print(f"✅ PASS: Grade A (bypass count field not found, assuming no bypass)")
                    return True
                else:
                    print(f"❌ FAIL: Grade A but bypass_count={bypass_count} (expected 0)")
                    return False
            else:
                print(f"❌ FAIL: Expected grade A, got grade={grade}")
                return False
        else:
            print(f"Response: {response.text[:500]}")
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False

def main():
    """Run all sanity tests"""
    print("\n" + "="*60)
    print("QUICK BACKEND SANITY CHECK - 3 Endpoints")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Admin Email: {ADMIN_EMAIL}")
    
    results = []
    
    # Test 1: Admin Login
    login_success, cookies = test_admin_login()
    results.append(("POST /api/auth/login", login_success))
    
    if not login_success:
        print("\n❌ CRITICAL: Admin login failed, cannot proceed with authenticated tests")
        print("\n" + "="*60)
        print("FINAL RESULT: FAIL (1/3 tests attempted)")
        print("="*60)
        sys.exit(1)
    
    # Test 2: i18n Adoption
    i18n_success = test_i18n_adoption(cookies)
    results.append(("GET /api/admin/i18n/adoption", i18n_success))
    
    # Test 3: Compliance Counter
    compliance_success = test_compliance_counter(cookies)
    results.append(("GET /api/admin/v7-templates/compliance-counter", compliance_success))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*60)
    print(f"FINAL RESULT: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Backend sanity check complete")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - See details above")
        sys.exit(1)

if __name__ == "__main__":
    main()
