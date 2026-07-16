"""Feature 27 (ID Checker) Backend API Verification Test

This test validates:
1. Auth login works for admin/free credentials
2. Free user can access /api/id-checker/kyc/status
3. Free user can access /api/id-checker/experience-summary
4. Free user gets 403 on /api/id-checker/admin/queue
5. Admin can access /api/id-checker/admin/queue
6. Admin can access /api/id-checker/admin/operations-kpis
7. Admin can access /api/id-checker/admin/conversion-funnel
"""

import requests
import json
import os
from datetime import datetime

# Backend URL from environment
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "https://admin-policy-hub.preview.emergentagent.com")
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"
FREE_USER_EMAIL = "p1.free.1779113329@example.com"
FREE_USER_PASSWORD = "P1Free#2026!Aa"

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name, details=""):
        self.passed.append({"test": test_name, "details": details})
        print(f"✅ PASS: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_fail(self, test_name, error):
        self.failed.append({"test": test_name, "error": str(error)})
        print(f"❌ FAIL: {test_name}")
        print(f"   Error: {error}")
    
    def add_warning(self, test_name, message):
        self.warnings.append({"test": test_name, "message": message})
        print(f"⚠️  WARNING: {test_name}")
        print(f"   {message}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        print("\n" + "="*80)
        print("TEST SUMMARY - FEATURE 27 (ID CHECKER)")
        print("="*80)
        print(f"Total Tests: {total}")
        print(f"Passed: {len(self.passed)} ({len(self.passed)*100//total if total > 0 else 0}%)")
        print(f"Failed: {len(self.failed)} ({len(self.failed)*100//total if total > 0 else 0}%)")
        print(f"Warnings: {len(self.warnings)}")
        print("="*80)
        
        if self.failed:
            print("\n❌ FAILED TESTS:")
            for item in self.failed:
                print(f"  - {item['test']}: {item['error']}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for item in self.warnings:
                print(f"  - {item['test']}: {item['message']}")
        
        return len(self.failed) == 0

results = TestResults()

def login(email, password):
    """Login and return session cookies"""
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": email, "password": password},
            timeout=30
        )
        if response.status_code == 200:
            return response.cookies
        else:
            raise Exception(f"Login failed with status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        raise Exception(f"Login request failed: {str(e)}")

def test_admin_login():
    """Test 1: Admin login"""
    print("\n" + "="*80)
    print("TEST 1: Admin Login")
    print("="*80)
    
    try:
        cookies = login(ADMIN_EMAIL, ADMIN_PASSWORD)
        
        # Verify session is valid by calling /api/auth/me
        response = requests.get(
            f"{API_BASE}/auth/me",
            cookies=cookies,
            timeout=30
        )
        
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data.get("user_id")
            email = user_data.get("email")
            is_admin = user_data.get("is_admin", False)
            
            if email == ADMIN_EMAIL:
                results.add_pass(
                    "Admin login",
                    f"User ID: {user_id}, Email: {email}, is_admin: {is_admin}"
                )
                return cookies
            else:
                results.add_fail(
                    "Admin login",
                    f"Email mismatch: expected {ADMIN_EMAIL}, got {email}"
                )
                return None
        else:
            results.add_fail(
                "Admin session validation",
                f"Status {response.status_code}: {response.text[:200]}"
            )
            return None
            
    except Exception as e:
        results.add_fail("Admin login", str(e))
        return None

def test_free_user_login():
    """Test 2: Free user login"""
    print("\n" + "="*80)
    print("TEST 2: Free User Login")
    print("="*80)
    
    try:
        cookies = login(FREE_USER_EMAIL, FREE_USER_PASSWORD)
        
        # Verify session is valid by calling /api/auth/me
        response = requests.get(
            f"{API_BASE}/auth/me",
            cookies=cookies,
            timeout=30
        )
        
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data.get("user_id")
            email = user_data.get("email")
            subscription_plan = user_data.get("subscription_plan", "unknown")
            
            if email == FREE_USER_EMAIL:
                results.add_pass(
                    "Free user login",
                    f"User ID: {user_id}, Email: {email}, Plan: {subscription_plan}"
                )
                return cookies
            else:
                results.add_fail(
                    "Free user login",
                    f"Email mismatch: expected {FREE_USER_EMAIL}, got {email}"
                )
                return None
        else:
            results.add_fail(
                "Free user session validation",
                f"Status {response.status_code}: {response.text[:200]}"
            )
            return None
            
    except Exception as e:
        results.add_fail("Free user login", str(e))
        return None

def test_free_user_kyc_status(cookies):
    """Test 3: Free user can access /api/id-checker/kyc/status"""
    print("\n" + "="*80)
    print("TEST 3: Free User - KYC Status Endpoint")
    print("="*80)
    
    if not cookies:
        results.add_fail("Free user KYC status", "No valid session cookies")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/id-checker/kyc/status",
            cookies=cookies,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields per test contract
            required_fields = ["kyc", "entitlements", "sla", "id_checker"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                results.add_fail(
                    "Free user KYC status contract",
                    f"Missing required fields: {missing_fields}. Got: {list(data.keys())}"
                )
            else:
                # Verify nested structures
                entitlements = data.get("entitlements", {})
                id_checker = data.get("id_checker", {})
                
                plan = entitlements.get("plan")
                workflow_state = id_checker.get("workflow_state")
                
                results.add_pass(
                    "Free user KYC status",
                    f"Plan: {plan}, Workflow State: {workflow_state}, All required fields present"
                )
        else:
            results.add_fail(
                "Free user KYC status endpoint",
                f"Status {response.status_code}: {response.text[:200]}"
            )
            
    except Exception as e:
        results.add_fail("Free user KYC status", str(e))

def test_free_user_experience_summary(cookies):
    """Test 4: Free user can access /api/id-checker/experience-summary"""
    print("\n" + "="*80)
    print("TEST 4: Free User - Experience Summary Endpoint")
    print("="*80)
    
    if not cookies:
        results.add_fail("Free user experience summary", "No valid session cookies")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/id-checker/experience-summary",
            cookies=cookies,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields per test contract
            required_fields = ["generated_at", "plan", "service_lane", "workflow_state", "progress", "sla", "trust_readiness_score", "nudges"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                results.add_fail(
                    "Free user experience summary contract",
                    f"Missing required fields: {missing_fields}. Got: {list(data.keys())}"
                )
            else:
                plan = data.get("plan")
                workflow_state = data.get("workflow_state")
                trust_score = data.get("trust_readiness_score")
                
                results.add_pass(
                    "Free user experience summary",
                    f"Plan: {plan}, Workflow State: {workflow_state}, Trust Score: {trust_score}"
                )
        else:
            results.add_fail(
                "Free user experience summary endpoint",
                f"Status {response.status_code}: {response.text[:200]}"
            )
            
    except Exception as e:
        results.add_fail("Free user experience summary", str(e))

def test_free_user_admin_queue_blocked(cookies):
    """Test 5: Free user gets 403 on /api/id-checker/admin/queue"""
    print("\n" + "="*80)
    print("TEST 5: Free User - Admin Queue Blocked (403)")
    print("="*80)
    
    if not cookies:
        results.add_fail("Free user admin queue blocked", "No valid session cookies")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/id-checker/admin/queue",
            params={"status": "ALL", "risk_level": "all", "country": "all", "limit": 20},
            cookies=cookies,
            timeout=30
        )
        
        if response.status_code == 403:
            results.add_pass(
                "Free user admin queue blocked",
                "Free user correctly blocked from admin queue (403)"
            )
        elif response.status_code == 401:
            results.add_pass(
                "Free user admin queue blocked",
                "Free user correctly blocked from admin queue (401)"
            )
        else:
            results.add_fail(
                "Free user admin queue access control",
                f"Expected 403 or 401, got status {response.status_code}: {response.text[:200]}"
            )
            
    except Exception as e:
        results.add_fail("Free user admin queue blocked", str(e))

def test_admin_queue(cookies):
    """Test 6: Admin can access /api/id-checker/admin/queue"""
    print("\n" + "="*80)
    print("TEST 6: Admin - Admin Queue Endpoint")
    print("="*80)
    
    if not cookies:
        results.add_fail("Admin queue", "No valid session cookies")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/id-checker/admin/queue",
            params={"status": "ALL", "risk_level": "all", "country": "all", "limit": 30},
            cookies=cookies,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "queue" not in data:
                results.add_fail(
                    "Admin queue response",
                    f"Missing 'queue' field. Got: {list(data.keys())}"
                )
            else:
                queue = data.get("queue", [])
                
                # Check if queue has items and verify enterprise fields
                if queue:
                    sample = queue[0]
                    enterprise_fields = ["service_lane", "subscription_plan", "sla_due_at", "sla_breached", "sla_hours_remaining"]
                    missing_fields = [f for f in enterprise_fields if f not in sample]
                    
                    if missing_fields:
                        results.add_warning(
                            "Admin queue enterprise fields",
                            f"Missing enterprise fields in queue item: {missing_fields}"
                        )
                    
                    results.add_pass(
                        "Admin queue",
                        f"Queue has {len(queue)} items, sample fields: {list(sample.keys())[:10]}"
                    )
                else:
                    results.add_pass(
                        "Admin queue",
                        "Queue is empty (no cases yet)"
                    )
        else:
            results.add_fail(
                "Admin queue endpoint",
                f"Status {response.status_code}: {response.text[:200]}"
            )
            
    except Exception as e:
        results.add_fail("Admin queue", str(e))

def test_admin_operations_kpis(cookies):
    """Test 7: Admin can access /api/id-checker/admin/operations-kpis"""
    print("\n" + "="*80)
    print("TEST 7: Admin - Operations KPIs Endpoint")
    print("="*80)
    
    if not cookies:
        results.add_fail("Admin operations KPIs", "No valid session cookies")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/id-checker/admin/operations-kpis",
            params={"lookback_days": 30},
            cookies=cookies,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields per test contract
            required_fields = [
                "lookback_days", "generated_at", "total_cases", "approval_rate_pct",
                "rejection_rate_pct", "pending_rate_pct", "document_completion_rate_pct",
                "sla_breach_cases", "state_counts", "service_lane_counts", "docs_missing_cases"
            ]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                results.add_fail(
                    "Admin operations KPIs contract",
                    f"Missing required fields: {missing_fields}. Got: {list(data.keys())}"
                )
            else:
                total_cases = data.get("total_cases")
                approval_rate = data.get("approval_rate_pct")
                sla_breaches = data.get("sla_breach_cases")
                
                results.add_pass(
                    "Admin operations KPIs",
                    f"Total Cases: {total_cases}, Approval Rate: {approval_rate}%, SLA Breaches: {sla_breaches}"
                )
        else:
            results.add_fail(
                "Admin operations KPIs endpoint",
                f"Status {response.status_code}: {response.text[:200]}"
            )
            
    except Exception as e:
        results.add_fail("Admin operations KPIs", str(e))

def test_admin_conversion_funnel(cookies):
    """Test 8: Admin can access /api/id-checker/admin/conversion-funnel"""
    print("\n" + "="*80)
    print("TEST 8: Admin - Conversion Funnel Endpoint")
    print("="*80)
    
    if not cookies:
        results.add_fail("Admin conversion funnel", "No valid session cookies")
        return
    
    try:
        response = requests.get(
            f"{API_BASE}/id-checker/admin/conversion-funnel",
            params={"lookback_days": 30},
            cookies=cookies,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields per test contract
            required_fields = ["funnel", "conversion_rates_pct", "dropoff", "insights"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                results.add_fail(
                    "Admin conversion funnel contract",
                    f"Missing required fields: {missing_fields}. Got: {list(data.keys())}"
                )
            else:
                insights = data.get("insights", [])
                conversion_rates = data.get("conversion_rates_pct", {})
                
                results.add_pass(
                    "Admin conversion funnel",
                    f"Insights count: {len(insights)}, Conversion rates: {list(conversion_rates.keys())[:5]}"
                )
        else:
            results.add_fail(
                "Admin conversion funnel endpoint",
                f"Status {response.status_code}: {response.text[:200]}"
            )
            
    except Exception as e:
        results.add_fail("Admin conversion funnel", str(e))

def main():
    print("\n" + "="*80)
    print("FEATURE 27 (ID CHECKER) BACKEND API VERIFICATION TEST")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print("="*80)
    
    # Test 1: Admin login
    admin_cookies = test_admin_login()
    
    # Test 2: Free user login
    free_user_cookies = test_free_user_login()
    
    # Test 3: Free user KYC status
    test_free_user_kyc_status(free_user_cookies)
    
    # Test 4: Free user experience summary
    test_free_user_experience_summary(free_user_cookies)
    
    # Test 5: Free user admin queue blocked
    test_free_user_admin_queue_blocked(free_user_cookies)
    
    # Test 6: Admin queue
    test_admin_queue(admin_cookies)
    
    # Test 7: Admin operations KPIs
    test_admin_operations_kpis(admin_cookies)
    
    # Test 8: Admin conversion funnel
    test_admin_conversion_funnel(admin_cookies)
    
    # Print summary
    success = results.summary()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
