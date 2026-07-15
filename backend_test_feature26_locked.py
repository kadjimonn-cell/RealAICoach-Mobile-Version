"""Feature 26 Final Closure Locked Protocol Backend Validation

This test validates Feature 26 under locked protocol:
1. Locked metadata (health endpoint)
2. Free tier checks (dashboard, jobs search, admin block, boost profile block)
3. Basic tier checks (dashboard, jobs search, admin block, boost profile access)
4. Premium/Admin checks (dashboard, admin endpoints, employer conversion funnel)
5. Approved employer checks (dashboard, admin block)

Test credentials from review request:
- Free: p1.free.1779113329@example.com / P1Free#2026!Aa
- Basic: f21.basic.1781338672@example.com / F21Basic#2026Aa
- Admin/Premium: admin@realaicoach.app / NewAdminPass2026!
- Approved employer: feature26.approved.employer.e2e@realaicoach.app / Feature26Approved#2026!
"""

import requests
import json
import os
from datetime import datetime

# Backend URL from environment
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "https://visa-polish-v2.preview.emergentagent.com")
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
FREE_EMAIL = "p1.free.1779113329@example.com"
FREE_PASSWORD = "P1Free#2026!Aa"

BASIC_EMAIL = "f21.basic.1781338672@example.com"
BASIC_PASSWORD = "F21Basic#2026Aa"

ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

APPROVED_EMPLOYER_EMAIL = "feature26.approved.employer.e2e@realaicoach.app"
APPROVED_EMPLOYER_PASSWORD = "Feature26Approved#2026!"

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
        print("TEST SUMMARY")
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

def get_headers():
    """Get headers to bypass Cloudflare"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Origin": BACKEND_URL,
        "Referer": f"{BACKEND_URL}/",
        "X-Requested-With": "XMLHttpRequest"
    }

def login(email, password):
    """Login and return session cookies"""
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": email, "password": password},
            headers=get_headers(),
            timeout=30
        )
        if response.status_code == 200:
            return response.cookies
        else:
            raise Exception(f"Login failed with status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        raise Exception(f"Login request failed: {str(e)}")

def test_locked_metadata():
    """Test 1: Locked metadata - health endpoint"""
    print("\n" + "="*80)
    print("TEST 1: Locked Metadata - Health Endpoint")
    print("="*80)
    
    try:
        response = requests.get(
            f"{API_BASE}/hiring/v2/health",
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check feature_number and feature_id
            if data.get("feature_number") == 26 and data.get("feature_id") == "jobs-portal":
                results.add_pass(
                    "Health endpoint locked metadata",
                    f"feature_number=26, feature_id=jobs-portal ✅"
                )
            else:
                results.add_fail(
                    "Health endpoint locked metadata",
                    f"Expected feature_number=26 and feature_id=jobs-portal, got feature_number={data.get('feature_number')}, feature_id={data.get('feature_id')}"
                )
        else:
            results.add_fail(
                "Health endpoint",
                f"Status {response.status_code}: {response.text[:200]}"
            )
            
    except Exception as e:
        results.add_fail("Health endpoint", str(e))

def test_free_tier():
    """Test 2: Free tier checks"""
    print("\n" + "="*80)
    print("TEST 2: Free Tier Checks")
    print("="*80)
    
    try:
        # Login
        cookies = login(FREE_EMAIL, FREE_PASSWORD)
        results.add_pass("Free tier login", f"Email: {FREE_EMAIL}")
        
        # Test 2.1: GET /api/hiring/v2/dashboard/summary = 200
        response = requests.get(
            f"{API_BASE}/hiring/v2/dashboard/summary",
            cookies=cookies,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            results.add_pass("Free tier - dashboard/summary", "Status 200 ✅")
        else:
            results.add_fail(
                "Free tier - dashboard/summary",
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        # Test 2.2: GET /api/hiring/v2/candidate/jobs/search = 200
        response = requests.get(
            f"{API_BASE}/hiring/v2/candidate/jobs/search",
            cookies=cookies,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            results.add_pass("Free tier - candidate/jobs/search", "Status 200 ✅")
        else:
            results.add_fail(
                "Free tier - candidate/jobs/search",
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        # Test 2.3: GET /api/hiring/v2/admin/workflow-events = 403
        response = requests.get(
            f"{API_BASE}/hiring/v2/admin/workflow-events",
            cookies=cookies,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 403:
            results.add_pass("Free tier - admin/workflow-events blocked", "Status 403 ✅")
        else:
            results.add_fail(
                "Free tier - admin/workflow-events blocked",
                f"Expected 403, got {response.status_code}: {response.text[:200]}"
            )
        
        # Test 2.4: POST /api/hiring/v2/candidate/boost-profile = 403
        response = requests.post(
            f"{API_BASE}/hiring/v2/candidate/boost-profile",
            json={},
            cookies=cookies,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 403:
            results.add_pass("Free tier - candidate/boost-profile blocked", "Status 403 ✅")
        else:
            results.add_fail(
                "Free tier - candidate/boost-profile blocked",
                f"Expected 403, got {response.status_code}: {response.text[:200]}"
            )
            
    except Exception as e:
        results.add_fail("Free tier checks", str(e))

def test_basic_tier():
    """Test 3: Basic tier checks"""
    print("\n" + "="*80)
    print("TEST 3: Basic Tier Checks")
    print("="*80)
    
    try:
        # Login
        cookies = login(BASIC_EMAIL, BASIC_PASSWORD)
        results.add_pass("Basic tier login", f"Email: {BASIC_EMAIL}")
        
        # Test 3.1: GET /api/hiring/v2/dashboard/summary = 200
        response = requests.get(
            f"{API_BASE}/hiring/v2/dashboard/summary",
            cookies=cookies,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            results.add_pass("Basic tier - dashboard/summary", "Status 200 ✅")
        else:
            results.add_fail(
                "Basic tier - dashboard/summary",
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        # Test 3.2: GET /api/hiring/v2/candidate/jobs/search = 200
        response = requests.get(
            f"{API_BASE}/hiring/v2/candidate/jobs/search",
            cookies=cookies,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            results.add_pass("Basic tier - candidate/jobs/search", "Status 200 ✅")
        else:
            results.add_fail(
                "Basic tier - candidate/jobs/search",
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        # Test 3.3: GET /api/hiring/v2/admin/workflow-events = 403
        response = requests.get(
            f"{API_BASE}/hiring/v2/admin/workflow-events",
            cookies=cookies,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 403:
            results.add_pass("Basic tier - admin/workflow-events blocked", "Status 403 ✅")
        else:
            results.add_fail(
                "Basic tier - admin/workflow-events blocked",
                f"Expected 403, got {response.status_code}: {response.text[:200]}"
            )
        
        # Test 3.4: POST /api/hiring/v2/candidate/boost-profile = 200
        response = requests.post(
            f"{API_BASE}/hiring/v2/candidate/boost-profile",
            json={},
            cookies=cookies,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            results.add_pass("Basic tier - candidate/boost-profile allowed", "Status 200 ✅")
        else:
            results.add_fail(
                "Basic tier - candidate/boost-profile allowed",
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
            
    except Exception as e:
        results.add_fail("Basic tier checks", str(e))

def test_premium_admin_tier():
    """Test 4: Premium/Admin tier checks"""
    print("\n" + "="*80)
    print("TEST 4: Premium/Admin Tier Checks")
    print("="*80)
    
    try:
        # Login
        cookies = login(ADMIN_EMAIL, ADMIN_PASSWORD)
        results.add_pass("Premium/Admin tier login", f"Email: {ADMIN_EMAIL}")
        
        # Test 4.1: GET /api/hiring/v2/dashboard/summary = 200
        response = requests.get(
            f"{API_BASE}/hiring/v2/dashboard/summary",
            cookies=cookies,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            results.add_pass("Premium/Admin tier - dashboard/summary", "Status 200 ✅")
        else:
            results.add_fail(
                "Premium/Admin tier - dashboard/summary",
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        # Test 4.2: GET /api/hiring/v2/admin/workflow-events = 200
        response = requests.get(
            f"{API_BASE}/hiring/v2/admin/workflow-events",
            cookies=cookies,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            results.add_pass("Premium/Admin tier - admin/workflow-events", "Status 200 ✅")
        else:
            results.add_fail(
                "Premium/Admin tier - admin/workflow-events",
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        # Test 4.3: GET /api/hiring/v2/admin/employer-conversion-funnel = 200
        response = requests.get(
            f"{API_BASE}/hiring/v2/admin/employer-conversion-funnel",
            cookies=cookies,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            results.add_pass("Premium/Admin tier - admin/employer-conversion-funnel", "Status 200 ✅")
        else:
            results.add_fail(
                "Premium/Admin tier - admin/employer-conversion-funnel",
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
            
    except Exception as e:
        results.add_fail("Premium/Admin tier checks", str(e))

def test_approved_employer():
    """Test 5: Approved employer checks"""
    print("\n" + "="*80)
    print("TEST 5: Approved Employer Checks")
    print("="*80)
    
    try:
        # Login
        cookies = login(APPROVED_EMPLOYER_EMAIL, APPROVED_EMPLOYER_PASSWORD)
        results.add_pass("Approved employer login", f"Email: {APPROVED_EMPLOYER_EMAIL}")
        
        # Test 5.1: GET /api/hiring/v2/dashboard/summary = 200
        response = requests.get(
            f"{API_BASE}/hiring/v2/dashboard/summary",
            cookies=cookies,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            results.add_pass("Approved employer - dashboard/summary", "Status 200 ✅")
        else:
            results.add_fail(
                "Approved employer - dashboard/summary",
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        # Test 5.2: GET /api/hiring/v2/admin/workflow-events = 403
        response = requests.get(
            f"{API_BASE}/hiring/v2/admin/workflow-events",
            cookies=cookies,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 403:
            results.add_pass("Approved employer - admin/workflow-events blocked", "Status 403 ✅")
        else:
            results.add_fail(
                "Approved employer - admin/workflow-events blocked",
                f"Expected 403, got {response.status_code}: {response.text[:200]}"
            )
            
    except Exception as e:
        results.add_fail("Approved employer checks", str(e))

def main():
    print("\n" + "="*80)
    print("FEATURE 26 FINAL CLOSURE LOCKED PROTOCOL BACKEND VALIDATION")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    print("="*80)
    
    # Test 1: Locked metadata
    test_locked_metadata()
    
    # Test 2: Free tier checks
    test_free_tier()
    
    # Test 3: Basic tier checks
    test_basic_tier()
    
    # Test 4: Premium/Admin tier checks
    test_premium_admin_tier()
    
    # Test 5: Approved employer checks
    test_approved_employer()
    
    # Print summary
    success = results.summary()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
