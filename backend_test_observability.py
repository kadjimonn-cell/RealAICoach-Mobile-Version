#!/usr/bin/env python3
"""
Backend Test: Watch Videos Admin Observability Incident Timeline
Test Date: 2026-06-10
Objective: Validate admin observability endpoint with incident timeline
"""

import requests
import json
from typing import Dict, Any

# Base URL from frontend/.env
BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"
PREMIUM_EMAIL = "watchvideos.premium.4dc6ab84@example.com"
PREMIUM_PASSWORD = "WatchVideos#2026Aa"


class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def add_pass(self, test_name: str, details: str = ""):
        self.passed.append({"test": test_name, "details": details})
        print(f"✅ PASS: {test_name}")
        if details:
            print(f"   {details}")

    def add_fail(self, test_name: str, details: str):
        self.failed.append({"test": test_name, "details": details})
        print(f"❌ FAIL: {test_name}")
        print(f"   {details}")

    def add_warning(self, test_name: str, details: str):
        self.warnings.append({"test": test_name, "details": details})
        print(f"⚠️  WARNING: {test_name}")
        print(f"   {details}")

    def summary(self):
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {len(self.passed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print("=" * 80)
        return len(self.failed) == 0


def login(email: str, password: str) -> Dict[str, Any]:
    """Login and return session cookies"""
    print(f"\n🔐 Logging in as: {email}")
    
    url = f"{BASE_URL}/api/auth/login"
    payload = {
        "email": email,
        "password": password
    }
    headers = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login successful")
            return {
                "cookies": response.cookies,
                "data": data
            }
        else:
            print(f"   ❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Login error: {str(e)}")
        return None


def test_admin_observability(session_cookies, result: TestResult):
    """Test 1: Admin login and GET /api/videos/admin/observability?lookback_days=7"""
    print("\n" + "=" * 80)
    print("TEST 1: Admin Observability Endpoint")
    print("=" * 80)
    
    url = f"{BASE_URL}/api/videos/admin/observability?lookback_days=7"
    headers = {
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        response = requests.get(url, cookies=session_cookies, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        # Test 1.1: Expect 200
        if response.status_code != 200:
            result.add_fail(
                "Admin Observability - Status Code",
                f"Expected 200, got {response.status_code}. Response: {response.text[:500]}"
            )
            return
        
        result.add_pass("Admin Observability - Status Code", "200 OK")
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            result.add_fail(
                "Admin Observability - JSON Parse",
                f"Failed to parse JSON: {str(e)}"
            )
            return
        
        print(f"\nResponse Keys: {list(data.keys())}")
        
        # Test 1.2: Response contains incident_timeline (array)
        if "incident_timeline" not in data:
            result.add_fail(
                "Admin Observability - incident_timeline",
                "Response does not contain 'incident_timeline' key"
            )
        else:
            incident_timeline = data["incident_timeline"]
            if not isinstance(incident_timeline, list):
                result.add_fail(
                    "Admin Observability - incident_timeline type",
                    f"Expected array, got {type(incident_timeline)}"
                )
            else:
                result.add_pass(
                    "Admin Observability - incident_timeline",
                    f"Array with {len(incident_timeline)} incidents"
                )
                
                # Test 1.3: Each incident should include required keys
                if len(incident_timeline) > 0:
                    required_keys = ["hour_bucket", "signal_type", "severity", "title", "metrics", "suggested_actions"]
                    for idx, incident in enumerate(incident_timeline):
                        missing_keys = [key for key in required_keys if key not in incident]
                        if missing_keys:
                            result.add_fail(
                                f"Admin Observability - Incident {idx} structure",
                                f"Missing keys: {missing_keys}. Incident: {json.dumps(incident, indent=2)}"
                            )
                        else:
                            result.add_pass(
                                f"Admin Observability - Incident {idx} structure",
                                f"All required keys present: {incident.get('signal_type')} - {incident.get('severity')}"
                            )
                else:
                    result.add_warning(
                        "Admin Observability - incident_timeline content",
                        "No incidents in timeline (this is OK if system is healthy)"
                    )
        
        # Test 1.4: Response contains incident_timeline_summary (object)
        if "incident_timeline_summary" not in data:
            result.add_fail(
                "Admin Observability - incident_timeline_summary",
                "Response does not contain 'incident_timeline_summary' key"
            )
        else:
            summary = data["incident_timeline_summary"]
            if not isinstance(summary, dict):
                result.add_fail(
                    "Admin Observability - incident_timeline_summary type",
                    f"Expected object, got {type(summary)}"
                )
            else:
                result.add_pass(
                    "Admin Observability - incident_timeline_summary",
                    f"Object with keys: {list(summary.keys())}"
                )
                print(f"\nIncident Timeline Summary:")
                print(json.dumps(summary, indent=2))
        
        # Additional validation: Check other expected fields
        expected_top_level_keys = ["success", "feature_id", "feature_route", "lookback_days", "generated_at", "api", "engagement", "risk_signals"]
        for key in expected_top_level_keys:
            if key not in data:
                result.add_warning(
                    f"Admin Observability - {key}",
                    f"Expected key '{key}' not found in response"
                )
        
        print(f"\nFull Response Structure:")
        print(json.dumps(data, indent=2)[:2000])  # Print first 2000 chars
        
    except Exception as e:
        result.add_fail(
            "Admin Observability - Request",
            f"Exception: {str(e)}"
        )


def test_premium_user_403(session_cookies, result: TestResult):
    """Test 2: Premium user login and expect 403 admin-only block"""
    print("\n" + "=" * 80)
    print("TEST 2: Premium User 403 Block")
    print("=" * 80)
    
    url = f"{BASE_URL}/api/videos/admin/observability?lookback_days=7"
    headers = {
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        response = requests.get(url, cookies=session_cookies, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        # Test 2.1: Expect 403
        if response.status_code != 403:
            result.add_fail(
                "Premium User 403 Block - Status Code",
                f"Expected 403, got {response.status_code}. Response: {response.text[:500]}"
            )
        else:
            result.add_pass(
                "Premium User 403 Block - Status Code",
                "403 Forbidden (admin-only endpoint correctly blocked)"
            )
            
            # Check error message
            try:
                data = response.json()
                if "detail" in data:
                    print(f"Error Detail: {data['detail']}")
                    if "admin" in data["detail"].lower():
                        result.add_pass(
                            "Premium User 403 Block - Error Message",
                            f"Correct error message: {data['detail']}"
                        )
            except:
                pass
    
    except Exception as e:
        result.add_fail(
            "Premium User 403 Block - Request",
            f"Exception: {str(e)}"
        )


def test_bootstrap_non_regression(session_cookies, result: TestResult):
    """Test 3: Non-regression sanity - premium GET /api/videos/bootstrap"""
    print("\n" + "=" * 80)
    print("TEST 3: Bootstrap Non-Regression Sanity")
    print("=" * 80)
    
    url = f"{BASE_URL}/api/videos/bootstrap"
    headers = {
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        response = requests.get(url, cookies=session_cookies, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        # Test 3.1: Expect 200
        if response.status_code != 200:
            result.add_fail(
                "Bootstrap Non-Regression - Status Code",
                f"Expected 200, got {response.status_code}. Response: {response.text[:500]}"
            )
            return
        
        result.add_pass("Bootstrap Non-Regression - Status Code", "200 OK")
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            result.add_fail(
                "Bootstrap Non-Regression - JSON Parse",
                f"Failed to parse JSON: {str(e)}"
            )
            return
        
        # Test 3.2: retention_profile.streak_rewards present
        if "retention_profile" not in data:
            result.add_fail(
                "Bootstrap Non-Regression - retention_profile",
                "Response does not contain 'retention_profile' key"
            )
            return
        
        retention_profile = data["retention_profile"]
        if "streak_rewards" not in retention_profile:
            result.add_fail(
                "Bootstrap Non-Regression - streak_rewards",
                "retention_profile does not contain 'streak_rewards' key"
            )
        else:
            streak_rewards = retention_profile["streak_rewards"]
            result.add_pass(
                "Bootstrap Non-Regression - streak_rewards",
                f"Present with keys: {list(streak_rewards.keys()) if isinstance(streak_rewards, dict) else 'array'}"
            )
            print(f"\nStreak Rewards:")
            print(json.dumps(streak_rewards, indent=2)[:500])
    
    except Exception as e:
        result.add_fail(
            "Bootstrap Non-Regression - Request",
            f"Exception: {str(e)}"
        )


def main():
    print("=" * 80)
    print("WATCH VIDEOS ADMIN OBSERVABILITY BACKEND TEST")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Date: 2026-06-10")
    
    result = TestResult()
    
    # Test 1: Admin login and observability endpoint
    print("\n" + "=" * 80)
    print("PHASE 1: ADMIN TESTS")
    print("=" * 80)
    
    admin_session = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not admin_session:
        result.add_fail("Admin Login", "Failed to login as admin")
        result.summary()
        return 1
    
    result.add_pass("Admin Login", "Successfully logged in")
    test_admin_observability(admin_session["cookies"], result)
    
    # Test 2: Premium user login and expect 403
    print("\n" + "=" * 80)
    print("PHASE 2: PREMIUM USER TESTS")
    print("=" * 80)
    
    premium_session = login(PREMIUM_EMAIL, PREMIUM_PASSWORD)
    if not premium_session:
        result.add_fail("Premium User Login", "Failed to login as premium user")
        result.summary()
        return 1
    
    result.add_pass("Premium User Login", "Successfully logged in")
    test_premium_user_403(premium_session["cookies"], result)
    
    # Test 3: Non-regression sanity
    print("\n" + "=" * 80)
    print("PHASE 3: NON-REGRESSION SANITY")
    print("=" * 80)
    
    test_bootstrap_non_regression(premium_session["cookies"], result)
    
    # Summary
    all_passed = result.summary()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
