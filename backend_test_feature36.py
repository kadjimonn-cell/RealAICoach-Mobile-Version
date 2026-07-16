"""
Feature 36 Backend API Testing - Referrals Admin Integrity & Fraud Endpoints
Testing the latest Feature 36 enhancements for admin endpoints.

Test Matrix:
1. POST /api/referrals/admin/integrity-alerts/evaluate - Admin can trigger evaluation
2. GET /api/referrals/admin/integrity-alerts - Admin can view alerts
3. GET /api/referrals/admin/integrity-trends?days=90 - Admin can view trends
4. GET /api/referrals/admin/fraud-policy/recommendation - Admin can get recommendations
5. POST /api/referrals/admin/fraud-policy/apply-recommendation - Admin can apply policy
6. POST /api/referrals/admin/fraud-scan/run - Admin can run fraud scan with integrity_alert payload
7. Non-admin receives 403 on all admin routes
"""

import requests
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://admin-policy-hub.preview.emergentagent.com")
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"
BASIC_USER_EMAIL = "f22.basic.20260613@example.com"
BASIC_USER_PASSWORD = "F22Basic#2026Aa"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def log_test(message, status="INFO"):
    color = Colors.BLUE
    if status == "PASS":
        color = Colors.GREEN
    elif status == "FAIL":
        color = Colors.RED
    elif status == "WARN":
        color = Colors.YELLOW
    elif status == "HEADER":
        color = Colors.CYAN + Colors.BOLD
    print(f"{color}[{status}]{Colors.RESET} {message}")

def login(email, password):
    """Login and return session cookies"""
    log_test(f"Logging in as {email}...", "INFO")
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            log_test(f"✓ Login successful for {email}", "PASS")
            return response.cookies
        else:
            log_test(f"✗ Login failed for {email}: {response.status_code} - {response.text[:200]}", "FAIL")
            return None
    except Exception as e:
        log_test(f"✗ Login exception for {email}: {str(e)}", "FAIL")
        return None

def test_integrity_alerts_evaluate():
    """Test 1: POST /api/referrals/admin/integrity-alerts/evaluate"""
    log_test("\n" + "="*80, "HEADER")
    log_test("Test 1: POST /api/referrals/admin/integrity-alerts/evaluate", "HEADER")
    log_test("="*80, "HEADER")
    
    admin_cookies = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not admin_cookies:
        log_test("✗ Cannot proceed - admin login failed", "FAIL")
        return False
    
    try:
        response = requests.post(
            f"{API_BASE}/referrals/admin/integrity-alerts/evaluate",
            cookies=admin_cookies,
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=15
        )
        
        log_test(f"Response status: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            log_test("✓ Admin can trigger integrity alert evaluation (200 OK)", "PASS")
            data = response.json()
            log_test(f"Response keys: {list(data.keys())}", "INFO")
            
            # Check for expected response structure
            if "new_alerts" in data or "evaluated_at" in data or "trigger" in data:
                log_test("✓ Response contains expected fields", "PASS")
            else:
                log_test(f"⚠ Response structure: {json.dumps(data, indent=2)[:500]}", "WARN")
            
            return True
        else:
            log_test(f"✗ Request failed: {response.status_code} - {response.text[:500]}", "FAIL")
            return False
            
    except Exception as e:
        log_test(f"✗ Exception during test: {str(e)}", "FAIL")
        return False

def test_integrity_alerts_get():
    """Test 2: GET /api/referrals/admin/integrity-alerts"""
    log_test("\n" + "="*80, "HEADER")
    log_test("Test 2: GET /api/referrals/admin/integrity-alerts", "HEADER")
    log_test("="*80, "HEADER")
    
    admin_cookies = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not admin_cookies:
        log_test("✗ Cannot proceed - admin login failed", "FAIL")
        return False
    
    try:
        response = requests.get(
            f"{API_BASE}/referrals/admin/integrity-alerts",
            cookies=admin_cookies,
            params={"status": "open", "page": 1, "page_size": 20},
            timeout=10
        )
        
        log_test(f"Response status: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            log_test("✓ Admin can view integrity alerts (200 OK)", "PASS")
            data = response.json()
            
            # Check for required keys
            required_keys = ["alerts", "total_count", "page", "page_size", "status"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                log_test(f"✗ Missing required keys: {missing_keys}", "FAIL")
                log_test(f"Available keys: {list(data.keys())}", "INFO")
                return False
            
            log_test(f"✓ All required keys present: {required_keys}", "PASS")
            log_test(f"  - Total alerts: {data.get('total_count', 0)}", "INFO")
            log_test(f"  - Status filter: {data.get('status', 'N/A')}", "INFO")
            log_test(f"  - Alerts returned: {len(data.get('alerts', []))}", "INFO")
            
            return True
        else:
            log_test(f"✗ Request failed: {response.status_code} - {response.text[:500]}", "FAIL")
            return False
            
    except Exception as e:
        log_test(f"✗ Exception during test: {str(e)}", "FAIL")
        return False

def test_integrity_trends():
    """Test 3: GET /api/referrals/admin/integrity-trends?days=90"""
    log_test("\n" + "="*80, "HEADER")
    log_test("Test 3: GET /api/referrals/admin/integrity-trends?days=90", "HEADER")
    log_test("="*80, "HEADER")
    
    admin_cookies = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not admin_cookies:
        log_test("✗ Cannot proceed - admin login failed", "FAIL")
        return False
    
    try:
        response = requests.get(
            f"{API_BASE}/referrals/admin/integrity-trends",
            cookies=admin_cookies,
            params={"days": 90},
            timeout=15
        )
        
        log_test(f"Response status: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            log_test("✓ Admin can view integrity trends (200 OK)", "PASS")
            data = response.json()
            
            # Check for required keys
            required_keys = ["days", "points", "windows", "generated_at"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                log_test(f"✗ Missing required keys: {missing_keys}", "FAIL")
                log_test(f"Available keys: {list(data.keys())}", "INFO")
                return False
            
            log_test(f"✓ All required keys present: {required_keys}", "PASS")
            log_test(f"  - Days requested: {data.get('days', 0)}", "INFO")
            log_test(f"  - Data points returned: {len(data.get('points', []))}", "INFO")
            log_test(f"  - Windows available: {list(data.get('windows', {}).keys())}", "INFO")
            
            return True
        else:
            log_test(f"✗ Request failed: {response.status_code} - {response.text[:500]}", "FAIL")
            return False
            
    except Exception as e:
        log_test(f"✗ Exception during test: {str(e)}", "FAIL")
        return False

def test_fraud_policy_recommendation():
    """Test 4: GET /api/referrals/admin/fraud-policy/recommendation"""
    log_test("\n" + "="*80, "HEADER")
    log_test("Test 4: GET /api/referrals/admin/fraud-policy/recommendation", "HEADER")
    log_test("="*80, "HEADER")
    
    admin_cookies = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not admin_cookies:
        log_test("✗ Cannot proceed - admin login failed", "FAIL")
        return False
    
    try:
        response = requests.get(
            f"{API_BASE}/referrals/admin/fraud-policy/recommendation",
            cookies=admin_cookies,
            timeout=10
        )
        
        log_test(f"Response status: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            log_test("✓ Admin can get fraud policy recommendation (200 OK)", "PASS")
            data = response.json()
            
            # Check for required keys
            required_keys = ["active_profile", "recommendation", "metrics", "is_change_required", "evaluated_at"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                log_test(f"✗ Missing required keys: {missing_keys}", "FAIL")
                log_test(f"Available keys: {list(data.keys())}", "INFO")
                return False
            
            log_test(f"✓ All required keys present: {required_keys}", "PASS")
            log_test(f"  - Active profile: {data.get('active_profile', 'N/A')}", "INFO")
            log_test(f"  - Change required: {data.get('is_change_required', False)}", "INFO")
            
            return True
        else:
            log_test(f"✗ Request failed: {response.status_code} - {response.text[:500]}", "FAIL")
            return False
            
    except Exception as e:
        log_test(f"✗ Exception during test: {str(e)}", "FAIL")
        return False

def test_fraud_policy_apply():
    """Test 5: POST /api/referrals/admin/fraud-policy/apply-recommendation"""
    log_test("\n" + "="*80, "HEADER")
    log_test("Test 5: POST /api/referrals/admin/fraud-policy/apply-recommendation", "HEADER")
    log_test("="*80, "HEADER")
    
    admin_cookies = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not admin_cookies:
        log_test("✗ Cannot proceed - admin login failed", "FAIL")
        return False
    
    try:
        # First get the current recommendation
        rec_response = requests.get(
            f"{API_BASE}/referrals/admin/fraud-policy/recommendation",
            cookies=admin_cookies,
            timeout=10
        )
        
        if rec_response.status_code != 200:
            log_test("⚠ Could not get recommendation, will try with default profile", "WARN")
            profile = "balanced"
        else:
            rec_data = rec_response.json()
            recommendation = rec_data.get("recommendation", {})
            profile = recommendation.get("recommended_profile", "balanced")
            log_test(f"Using recommended profile: {profile}", "INFO")
        
        # Apply the recommendation
        response = requests.post(
            f"{API_BASE}/referrals/admin/fraud-policy/apply-recommendation",
            cookies=admin_cookies,
            json={"profile": profile},
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=10
        )
        
        log_test(f"Response status: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            log_test("✓ Admin can apply fraud policy recommendation (200 OK)", "PASS")
            data = response.json()
            log_test(f"Response keys: {list(data.keys())}", "INFO")
            
            if "success" in data or "profile" in data:
                log_test("✓ Response contains expected fields", "PASS")
            
            return True
        else:
            log_test(f"✗ Request failed: {response.status_code} - {response.text[:500]}", "FAIL")
            return False
            
    except Exception as e:
        log_test(f"✗ Exception during test: {str(e)}", "FAIL")
        return False

def test_fraud_scan_run():
    """Test 6: POST /api/referrals/admin/fraud-scan/run (includes integrity_alert payload)"""
    log_test("\n" + "="*80, "HEADER")
    log_test("Test 6: POST /api/referrals/admin/fraud-scan/run", "HEADER")
    log_test("="*80, "HEADER")
    
    admin_cookies = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not admin_cookies:
        log_test("✗ Cannot proceed - admin login failed", "FAIL")
        return False
    
    try:
        response = requests.post(
            f"{API_BASE}/referrals/admin/fraud-scan/run",
            cookies=admin_cookies,
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=20
        )
        
        log_test(f"Response status: {response.status_code}", "INFO")
        
        if response.status_code == 200:
            log_test("✓ Admin can run fraud scan (200 OK)", "PASS")
            data = response.json()
            
            # Check for required keys including integrity_alert
            required_keys = ["success", "new_alerts", "scan_time", "integrity_alert"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                log_test(f"✗ Missing required keys: {missing_keys}", "FAIL")
                log_test(f"Available keys: {list(data.keys())}", "INFO")
                return False
            
            log_test(f"✓ All required keys present: {required_keys}", "PASS")
            log_test(f"  - Success: {data.get('success', False)}", "INFO")
            log_test(f"  - New alerts: {data.get('new_alerts', 0)}", "INFO")
            log_test(f"  - Integrity alert payload present: {bool(data.get('integrity_alert'))}", "INFO")
            
            # Verify integrity_alert payload structure
            integrity_alert = data.get("integrity_alert", {})
            if integrity_alert:
                log_test(f"✓ integrity_alert payload included in response", "PASS")
                log_test(f"  - Integrity alert keys: {list(integrity_alert.keys())}", "INFO")
            else:
                log_test("⚠ integrity_alert payload is empty (may be expected if no alerts)", "WARN")
            
            return True
        else:
            log_test(f"✗ Request failed: {response.status_code} - {response.text[:500]}", "FAIL")
            return False
            
    except Exception as e:
        log_test(f"✗ Exception during test: {str(e)}", "FAIL")
        return False

def test_non_admin_403():
    """Test 7: Non-admin receives 403 on all admin routes"""
    log_test("\n" + "="*80, "HEADER")
    log_test("Test 7: Non-admin receives 403 on admin routes", "HEADER")
    log_test("="*80, "HEADER")
    
    basic_cookies = login(BASIC_USER_EMAIL, BASIC_USER_PASSWORD)
    if not basic_cookies:
        log_test("✗ Cannot proceed - basic user login failed", "FAIL")
        return False
    
    endpoints = [
        ("POST", "/referrals/admin/integrity-alerts/evaluate"),
        ("GET", "/referrals/admin/integrity-alerts"),
        ("GET", "/referrals/admin/integrity-trends?days=90"),
        ("GET", "/referrals/admin/fraud-policy/recommendation"),
        ("POST", "/referrals/admin/fraud-policy/apply-recommendation"),
        ("POST", "/referrals/admin/fraud-scan/run"),
    ]
    
    all_blocked = True
    for method, endpoint in endpoints:
        try:
            if method == "GET":
                response = requests.get(
                    f"{API_BASE}{endpoint}",
                    cookies=basic_cookies,
                    timeout=10
                )
            else:  # POST
                response = requests.post(
                    f"{API_BASE}{endpoint}",
                    cookies=basic_cookies,
                    json={},
                    headers={"X-Requested-With": "XMLHttpRequest"},
                    timeout=10
                )
            
            if response.status_code == 403:
                log_test(f"✓ {method} {endpoint}: 403 Forbidden (correctly blocked)", "PASS")
            elif response.status_code == 401:
                log_test(f"✓ {method} {endpoint}: 401 Unauthorized (correctly blocked)", "PASS")
            else:
                log_test(f"✗ {method} {endpoint}: {response.status_code} (should be 403/401)", "FAIL")
                all_blocked = False
                
        except Exception as e:
            log_test(f"✗ Exception testing {method} {endpoint}: {str(e)}", "FAIL")
            all_blocked = False
    
    if all_blocked:
        log_test("✓ All admin endpoints correctly block non-admin access", "PASS")
    else:
        log_test("✗ Some admin endpoints did not block non-admin access", "FAIL")
    
    return all_blocked

def main():
    log_test("\n" + "="*80, "HEADER")
    log_test("Feature 36 Backend Verification - Referrals Admin Endpoints", "HEADER")
    log_test("Testing latest Feature 36 enhancements", "HEADER")
    log_test("="*80 + "\n", "HEADER")
    
    log_test(f"Backend URL: {BACKEND_URL}", "INFO")
    log_test(f"API Base: {API_BASE}", "INFO")
    log_test(f"Admin User: {ADMIN_EMAIL}", "INFO")
    log_test(f"Basic User: {BASIC_USER_EMAIL}\n", "INFO")
    
    results = {
        "Test 1: POST integrity-alerts/evaluate": test_integrity_alerts_evaluate(),
        "Test 2: GET integrity-alerts": test_integrity_alerts_get(),
        "Test 3: GET integrity-trends": test_integrity_trends(),
        "Test 4: GET fraud-policy/recommendation": test_fraud_policy_recommendation(),
        "Test 5: POST fraud-policy/apply-recommendation": test_fraud_policy_apply(),
        "Test 6: POST fraud-scan/run (with integrity_alert)": test_fraud_scan_run(),
        "Test 7: Non-admin 403 on admin routes": test_non_admin_403(),
    }
    
    log_test("\n" + "="*80, "HEADER")
    log_test("TEST SUMMARY", "HEADER")
    log_test("="*80, "HEADER")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        log_test(f"{test_name}: {status}", status)
    
    log_test(f"\nTotal: {passed}/{total} tests passed", "PASS" if passed == total else "FAIL")
    
    if passed == total:
        log_test("\n✓ All Feature 36 admin endpoints working correctly!", "PASS")
        log_test("✓ Admin access control verified", "PASS")
        log_test("✓ Non-admin blocking verified", "PASS")
        log_test("✓ integrity_alert payload confirmed in fraud-scan/run", "PASS")
        return 0
    else:
        log_test(f"\n✗ {total - passed} test(s) failed. Please review the failures above.", "FAIL")
        return 1

if __name__ == "__main__":
    exit(main())
