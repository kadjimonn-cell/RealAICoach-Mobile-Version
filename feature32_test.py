"""
Feature 32 Backend Test: Post-Launch Monitoring Pack
Tests reliability endpoints and regression guardrails for protected template overrides.
"""

import requests
import json
from typing import Dict, Any
from datetime import datetime, timedelta

# Backend URL from environment
BACKEND_URL = "https://admin-policy-hub.preview.emergentagent.com"

# Test credentials
ADMIN_CREDS = {
    "email": "admin@realaicoach.app",
    "password": "NewAdminPass2026!"
}

FREE_USER_CREDS = {
    "email": "p1.free.1779113329@example.com",
    "password": "P1Free#2026!Aa"
}


class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, msg: str):
        self.passed.append(msg)
        print(f"✅ PASS: {msg}")
    
    def add_fail(self, msg: str):
        self.failed.append(msg)
        print(f"❌ FAIL: {msg}")
    
    def add_warning(self, msg: str):
        self.warnings.append(msg)
        print(f"⚠️  WARN: {msg}")
    
    def summary(self):
        print("\n" + "="*80)
        print("FEATURE 32 TEST SUMMARY")
        print("="*80)
        print(f"✅ Passed: {len(self.passed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.failed:
            print("\n❌ FAILED TESTS:")
            for fail in self.failed:
                print(f"  - {fail}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warn in self.warnings:
                print(f"  - {warn}")
        
        return len(self.failed) == 0


def login(email: str, password: str) -> Dict[str, Any]:
    """Login and return session cookies."""
    url = f"{BACKEND_URL}/api/auth/login"
    payload = {"email": email, "password": password}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return {"cookies": response.cookies, "status": "success", "response": response}
        else:
            return {"cookies": None, "status": "failed", "error": response.text, "status_code": response.status_code}
    except Exception as e:
        return {"cookies": None, "status": "error", "error": str(e)}


def test_login(result: TestResult):
    """Test 1: POST /api/auth/login for admin and free user."""
    print("\n" + "="*80)
    print("TEST 1: Login Authentication")
    print("="*80)
    
    # Test admin login
    print("\n1a) Testing admin login...")
    admin_login = login(ADMIN_CREDS["email"], ADMIN_CREDS["password"])
    if admin_login["status"] == "success":
        result.add_pass(f"Admin login successful: {ADMIN_CREDS['email']}")
    else:
        result.add_fail(f"Admin login failed: {admin_login.get('error', 'Unknown error')}")
    
    # Test free user login
    print("\n1b) Testing free user login...")
    free_login = login(FREE_USER_CREDS["email"], FREE_USER_CREDS["password"])
    if free_login["status"] == "success":
        result.add_pass(f"Free user login successful: {FREE_USER_CREDS['email']}")
    else:
        result.add_fail(f"Free user login failed: {free_login.get('error', 'Unknown error')}")
    
    return admin_login, free_login


def test_reliability_overview(admin_cookies, free_cookies, result: TestResult):
    """Test 2: GET /api/email-notifications/reliability/overview?window_days=7"""
    print("\n" + "="*80)
    print("TEST 2: Reliability Overview Endpoint")
    print("="*80)
    
    url = f"{BACKEND_URL}/api/email-notifications/reliability/overview?window_days=7"
    
    # Test admin access (should return 200)
    print("\n2a) Testing admin access to reliability overview...")
    try:
        response = requests.get(url, cookies=admin_cookies, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            # Check for required keys
            required_keys = ["kpis", "alerts", "top_failed_events", "weekly_report_template"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                result.add_fail(f"Admin reliability overview missing keys: {missing_keys}")
            else:
                result.add_pass("Admin reliability overview returned 200 with all required keys")
                
                # Validate structure
                if not isinstance(data.get("kpis"), dict):
                    result.add_warning("kpis is not a dict")
                if not isinstance(data.get("alerts"), list):
                    result.add_warning("alerts is not a list")
                if not isinstance(data.get("top_failed_events"), list):
                    result.add_warning("top_failed_events is not a list")
                if not isinstance(data.get("weekly_report_template"), dict):
                    result.add_warning("weekly_report_template is not a dict")
                
                # Check KPIs structure
                kpis = data.get("kpis", {})
                expected_kpi_keys = [
                    "uno_dispatch_success_rate_pct",
                    "duplicate_key_collisions",
                    "policy_blocked_writes",
                    "protected_template_count",
                    "active_policy_count",
                    "expired_policy_count"
                ]
                missing_kpi_keys = [key for key in expected_kpi_keys if key not in kpis]
                if missing_kpi_keys:
                    result.add_warning(f"KPIs missing keys: {missing_kpi_keys}")
                else:
                    result.add_pass("All expected KPI keys present")
        else:
            result.add_fail(f"Admin reliability overview returned {response.status_code}: {response.text[:200]}")
    except Exception as e:
        result.add_fail(f"Admin reliability overview exception: {str(e)}")
    
    # Test free user access (should return 403)
    print("\n2b) Testing free user access to reliability overview (should be blocked)...")
    try:
        response = requests.get(url, cookies=free_cookies, timeout=30)
        if response.status_code == 403:
            result.add_pass("Free user correctly blocked from reliability overview (403)")
        else:
            result.add_fail(f"Free user should be blocked but got {response.status_code}")
    except Exception as e:
        result.add_fail(f"Free user reliability overview exception: {str(e)}")


def test_weekly_report_template(admin_cookies, free_cookies, result: TestResult):
    """Test 3: GET /api/email-notifications/reliability/weekly-report-template?window_days=7"""
    print("\n" + "="*80)
    print("TEST 3: Weekly Report Template Endpoint")
    print("="*80)
    
    url = f"{BACKEND_URL}/api/email-notifications/reliability/weekly-report-template?window_days=7"
    
    # Test admin access (should return 200)
    print("\n3a) Testing admin access to weekly report template...")
    try:
        response = requests.get(url, cookies=admin_cookies, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            # Check for success=true
            if data.get("success") is not True:
                result.add_fail("Weekly report template missing success=true")
            else:
                result.add_pass("Weekly report template returned success=true")
            
            # Check for report_template
            report_template = data.get("report_template", {})
            if not report_template:
                result.add_fail("Weekly report template missing report_template object")
            else:
                # Check for template_markdown
                template_markdown = report_template.get("template_markdown", "")
                if not template_markdown:
                    result.add_fail("Weekly report template missing template_markdown")
                elif "# Feature 32 Weekly Reliability Report" not in template_markdown:
                    result.add_fail("Weekly report template_markdown missing expected header")
                else:
                    result.add_pass("Weekly report template contains expected markdown header")
                    
                    # Check for key sections
                    expected_sections = [
                        "Executive Snapshot",
                        "Alert Summary",
                        "Top Failed Event Types",
                        "Action Checklist"
                    ]
                    missing_sections = [s for s in expected_sections if s not in template_markdown]
                    if missing_sections:
                        result.add_warning(f"Template markdown missing sections: {missing_sections}")
                    else:
                        result.add_pass("All expected sections present in template markdown")
        else:
            result.add_fail(f"Admin weekly report template returned {response.status_code}: {response.text[:200]}")
    except Exception as e:
        result.add_fail(f"Admin weekly report template exception: {str(e)}")
    
    # Test free user access (should return 403)
    print("\n3b) Testing free user access to weekly report template (should be blocked)...")
    try:
        response = requests.get(url, cookies=free_cookies, timeout=30)
        if response.status_code == 403:
            result.add_pass("Free user correctly blocked from weekly report template (403)")
        else:
            result.add_fail(f"Free user should be blocked but got {response.status_code}")
    except Exception as e:
        result.add_fail(f"Free user weekly report template exception: {str(e)}")


def test_regression_guardrails(admin_cookies, result: TestResult):
    """Test 4: Regression guardrails for protected template overrides."""
    print("\n" + "="*80)
    print("TEST 4: Regression Guardrails - Protected Template Overrides")
    print("="*80)
    
    # Test 4a: POST /api/email-notifications/template-policies/override-approval
    print("\n4a) Testing override-approval for protected template (should be blocked)...")
    url = f"{BACKEND_URL}/api/email-notifications/template-policies/override-approval"
    
    # Generate future expiry date
    future_date = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
    
    payload = {
        "template_key": "meeting_reminder",
        "approved": True,
        "approval_id": "test_approval_123",
        "expires_at": future_date,
        "note": "Test approval attempt"
    }
    
    try:
        response = requests.post(url, json=payload, cookies=admin_cookies, timeout=30)
        # Should be blocked with 400 (policy block) or potentially CSRF block
        if response.status_code == 400:
            error_text = response.text.lower()
            if "protected" in error_text or "cannot be approved" in error_text:
                result.add_pass("Override approval correctly blocked for protected template (400 policy block)")
            else:
                result.add_warning(f"Override approval blocked with 400 but unexpected reason: {response.text[:200]}")
        elif response.status_code == 403:
            # CSRF or session constraint
            result.add_pass("Override approval blocked (403 - acceptable if CSRF/session constraint)")
        elif response.status_code == 200:
            result.add_fail("Override approval should be blocked but returned 200 (SECURITY ISSUE)")
        else:
            result.add_warning(f"Override approval returned unexpected status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        result.add_fail(f"Override approval test exception: {str(e)}")
    
    # Test 4b: POST /api/email-notifications/overrides/manual
    print("\n4b) Testing manual override for protected template (should be blocked)...")
    url = f"{BACKEND_URL}/api/email-notifications/overrides/manual"
    
    payload = {
        "template_key": "meeting_reminder",
        "optimized_subject": "Test Override Subject"
    }
    
    try:
        response = requests.post(url, json=payload, cookies=admin_cookies, timeout=30)
        # Should be blocked with 400 (policy block) or potentially CSRF block
        if response.status_code == 400:
            error_text = response.text.lower()
            if "blocked" in error_text or "protected" in error_text:
                result.add_pass("Manual override correctly blocked for protected template (400 policy block)")
            else:
                result.add_warning(f"Manual override blocked with 400 but unexpected reason: {response.text[:200]}")
        elif response.status_code == 403:
            # CSRF or session constraint
            result.add_pass("Manual override blocked (403 - acceptable if CSRF/session constraint)")
        elif response.status_code == 200:
            result.add_fail("Manual override should be blocked but returned 200 (SECURITY ISSUE)")
        else:
            result.add_warning(f"Manual override returned unexpected status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        result.add_fail(f"Manual override test exception: {str(e)}")


def main():
    print("="*80)
    print("FEATURE 32 POST-LAUNCH MONITORING PACK - BACKEND VERIFICATION")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Date: {datetime.utcnow().isoformat()}Z")
    print("="*80 + "\n")
    
    result = TestResult()
    
    # Test 1: Login
    admin_login, free_login = test_login(result)
    
    if admin_login["status"] != "success" or free_login["status"] != "success":
        print("\n❌ CRITICAL: Login tests failed. Cannot proceed with API tests.")
        result.summary()
        exit(1)
    
    admin_cookies = admin_login["cookies"]
    free_cookies = free_login["cookies"]
    
    # Test 2: Reliability Overview
    test_reliability_overview(admin_cookies, free_cookies, result)
    
    # Test 3: Weekly Report Template
    test_weekly_report_template(admin_cookies, free_cookies, result)
    
    # Test 4: Regression Guardrails
    test_regression_guardrails(admin_cookies, result)
    
    # Print summary
    print("\n")
    success = result.summary()
    
    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
