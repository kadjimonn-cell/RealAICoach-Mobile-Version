#!/usr/bin/env python3
"""
Backend Test - Admin Analytics/Insights Global Strict Lock
Verify ALL /api/admin/*analytics* and /api/admin/*insights* are strict admin-only
Target: https://admin-policy-hub.preview.emergentagent.com
Date: 2026-06-24
"""

import requests
import json
import sys

# Configuration
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"
NON_ADMIN_DELEGATED_EMAIL = "curation.1779076352@example.com"
NON_ADMIN_DELEGATED_PASSWORD = "NovaV2#2026!Aa"
FREE_USER_EMAIL = "p1.free.1779113329@example.com"
FREE_USER_PASSWORD = "P1Free#2026!Aa"

# Test endpoints - representative analytics/insights endpoints
ANALYTICS_INSIGHTS_ENDPOINTS = [
    "/api/admin/analytics",
    "/api/admin/subscription-analytics",
    "/api/admin/payment-analytics/provider-incidents/canary-status",
    "/api/admin/ai-insights/dashboard",
    "/api/admin/insights/dashboard",
    "/api/admin/executive/templates/analytics/summary",
]

# Non-analytics admin endpoints (should remain accessible to admin)
NON_ANALYTICS_ADMIN_ENDPOINTS = [
    "/api/admin/users",
    "/api/admin/system/health",
    "/api/admin/platform-health",
]

# Feature 34 endpoint (should not be affected by admin lock)
FEATURE_34_ENDPOINT = "/api/calendar/recommend-best-slot"

# Test results
results = {
    "admin_login": False,
    "non_admin_login": False,
    "free_user_login": False,
    "non_admin_403_on_analytics": {},
    "admin_allowed_on_analytics": {},
    "non_analytics_admin_unaffected": {},
    "feature_34_unaffected": False,
}

def login(email, password):
    """Login and return session"""
    session = requests.Session()
    login_url = f"{BASE_URL}/api/auth/login"
    
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = session.post(login_url, json=payload, timeout=30)
        if response.status_code == 200:
            print(f"✅ Login successful for {email}")
            return session
        else:
            print(f"❌ Login failed for {email}: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Login exception for {email}: {str(e)}")
        return None

def test_login():
    """Test login for all users"""
    print("\n" + "="*80)
    print("TEST: User Login")
    print("="*80)
    
    admin_session = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if admin_session:
        results["admin_login"] = True
    
    non_admin_session = login(NON_ADMIN_DELEGATED_EMAIL, NON_ADMIN_DELEGATED_PASSWORD)
    if non_admin_session:
        results["non_admin_login"] = True
    
    free_session = login(FREE_USER_EMAIL, FREE_USER_PASSWORD)
    if free_session:
        results["free_user_login"] = True
    
    return admin_session, non_admin_session, free_session

def test_non_admin_403_on_analytics(non_admin_session):
    """Test 1: Non-admin user gets strict 403 on analytics/insights endpoints"""
    print("\n" + "="*80)
    print("TEST 1: Non-Admin User Gets 403 on Analytics/Insights Endpoints")
    print("="*80)
    
    if not non_admin_session:
        print("❌ Non-admin session not available, skipping test")
        return
    
    for endpoint in ANALYTICS_INSIGHTS_ENDPOINTS:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = non_admin_session.get(url, timeout=30)
            status = response.status_code
            
            if status == 403:
                print(f"✅ {endpoint}: 403 (PASS)")
                results["non_admin_403_on_analytics"][endpoint] = True
            else:
                print(f"❌ {endpoint}: {status} (FAIL - Expected 403)")
                results["non_admin_403_on_analytics"][endpoint] = False
                if status == 200:
                    print(f"   ⚠️  CRITICAL: Non-admin user has access to analytics endpoint!")
        except Exception as e:
            print(f"❌ {endpoint}: Exception - {str(e)}")
            results["non_admin_403_on_analytics"][endpoint] = False

def test_admin_allowed_on_analytics(admin_session):
    """Test 2: Admin user remains allowed on analytics/insights endpoints"""
    print("\n" + "="*80)
    print("TEST 2: Admin User Allowed on Analytics/Insights Endpoints")
    print("="*80)
    
    if not admin_session:
        print("❌ Admin session not available, skipping test")
        return
    
    for endpoint in ANALYTICS_INSIGHTS_ENDPOINTS:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = admin_session.get(url, timeout=30)
            status = response.status_code
            
            # Admin should get 200 or 404 (if endpoint doesn't exist), but NOT 403
            if status in [200, 404]:
                print(f"✅ {endpoint}: {status} (PASS)")
                results["admin_allowed_on_analytics"][endpoint] = True
            elif status == 403:
                print(f"❌ {endpoint}: 403 (FAIL - Admin should have access)")
                results["admin_allowed_on_analytics"][endpoint] = False
            else:
                print(f"⚠️  {endpoint}: {status} (WARN - Unexpected status)")
                results["admin_allowed_on_analytics"][endpoint] = True  # Not a 403, so not blocked
        except Exception as e:
            print(f"❌ {endpoint}: Exception - {str(e)}")
            results["admin_allowed_on_analytics"][endpoint] = False

def test_non_analytics_admin_unaffected(admin_session):
    """Test 3: Non-analytics admin endpoints remain accessible to admin"""
    print("\n" + "="*80)
    print("TEST 3: Non-Analytics Admin Endpoints Unaffected")
    print("="*80)
    
    if not admin_session:
        print("❌ Admin session not available, skipping test")
        return
    
    for endpoint in NON_ANALYTICS_ADMIN_ENDPOINTS:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = admin_session.get(url, timeout=30)
            status = response.status_code
            
            # Admin should get 200 or 404, but NOT 403
            if status in [200, 404]:
                print(f"✅ {endpoint}: {status} (PASS)")
                results["non_analytics_admin_unaffected"][endpoint] = True
            elif status == 403:
                print(f"❌ {endpoint}: 403 (FAIL - Admin should have access)")
                results["non_analytics_admin_unaffected"][endpoint] = False
            else:
                print(f"⚠️  {endpoint}: {status} (WARN - Unexpected status)")
                results["non_analytics_admin_unaffected"][endpoint] = True
        except Exception as e:
            print(f"❌ {endpoint}: Exception - {str(e)}")
            results["non_analytics_admin_unaffected"][endpoint] = False

def test_feature_34_unaffected(free_session):
    """Test 4: Feature 34 endpoint unaffected by admin lock"""
    print("\n" + "="*80)
    print("TEST 4: Feature 34 Endpoint Unaffected by Admin Lock")
    print("="*80)
    
    if not free_session:
        print("❌ Free user session not available, skipping test")
        return
    
    url = f"{BASE_URL}{FEATURE_34_ENDPOINT}"
    try:
        # POST request with minimal payload
        payload = {
            "duration_minutes": 30,
            "timezone": "America/New_York"
        }
        response = free_session.post(url, json=payload, timeout=30)
        status = response.status_code
        
        # Should NOT get 403 due to admin lock (may get other errors like 400 for missing data)
        if status != 403:
            print(f"✅ {FEATURE_34_ENDPOINT}: {status} (PASS - Not blocked by admin lock)")
            results["feature_34_unaffected"] = True
        else:
            print(f"❌ {FEATURE_34_ENDPOINT}: 403 (FAIL - Should not be blocked by admin lock)")
            results["feature_34_unaffected"] = False
    except Exception as e:
        print(f"❌ {FEATURE_34_ENDPOINT}: Exception - {str(e)}")
        results["feature_34_unaffected"] = False

def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_tests = 0
    passed_tests = 0
    
    # Login tests
    print("\n📋 Login Tests:")
    for key in ["admin_login", "non_admin_login", "free_user_login"]:
        status = "✅ PASS" if results[key] else "❌ FAIL"
        print(f"  {key}: {status}")
        total_tests += 1
        if results[key]:
            passed_tests += 1
    
    # Non-admin 403 tests
    print("\n📋 Non-Admin 403 on Analytics/Insights:")
    for endpoint, passed in results["non_admin_403_on_analytics"].items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {endpoint}: {status}")
        total_tests += 1
        if passed:
            passed_tests += 1
    
    # Admin allowed tests
    print("\n📋 Admin Allowed on Analytics/Insights:")
    for endpoint, passed in results["admin_allowed_on_analytics"].items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {endpoint}: {status}")
        total_tests += 1
        if passed:
            passed_tests += 1
    
    # Non-analytics admin tests
    print("\n📋 Non-Analytics Admin Endpoints:")
    for endpoint, passed in results["non_analytics_admin_unaffected"].items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {endpoint}: {status}")
        total_tests += 1
        if passed:
            passed_tests += 1
    
    # Feature 34 test
    print("\n📋 Feature 34 Endpoint:")
    status = "✅ PASS" if results["feature_34_unaffected"] else "❌ FAIL"
    print(f"  {FEATURE_34_ENDPOINT}: {status}")
    total_tests += 1
    if results["feature_34_unaffected"]:
        passed_tests += 1
    
    # Overall summary
    print("\n" + "="*80)
    print(f"OVERALL: {passed_tests}/{total_tests} tests passed")
    print("="*80)
    
    # Critical failures
    critical_failures = []
    
    # Check if any non-admin user has access to analytics
    for endpoint, passed in results["non_admin_403_on_analytics"].items():
        if not passed:
            critical_failures.append(f"Non-admin has access to {endpoint}")
    
    # Check if admin is blocked from analytics
    for endpoint, passed in results["admin_allowed_on_analytics"].items():
        if not passed:
            critical_failures.append(f"Admin blocked from {endpoint}")
    
    if critical_failures:
        print("\n🚨 CRITICAL FAILURES:")
        for failure in critical_failures:
            print(f"  ❌ {failure}")
    else:
        print("\n✅ No critical failures detected")
    
    return passed_tests == total_tests

def main():
    """Main test execution"""
    print("="*80)
    print("Backend Test - Admin Analytics/Insights Global Strict Lock")
    print("="*80)
    print(f"Target: {BASE_URL}")
    print(f"Test Date: 2026-06-24")
    print("="*80)
    
    # Login
    admin_session, non_admin_session, free_session = test_login()
    
    # Run tests
    test_non_admin_403_on_analytics(non_admin_session)
    test_admin_allowed_on_analytics(admin_session)
    test_non_analytics_admin_unaffected(admin_session)
    test_feature_34_unaffected(free_session)
    
    # Print summary
    all_passed = print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
