"""
Feature 15 ACL Fix Verification
Focused backend verification for Feature 15 ACL fix on video-studio/bootstrap endpoint.

Tests:
1. POST /api/auth/login returns 200 and sets cookie
2. GET /api/video-studio/bootstrap with auth cookie returns 200 (not 403)
3. Response JSON has expected keys: success, plan, limits, usage, projects, templates, features
4. Confirm unauthenticated bootstrap returns 401/403
"""

import requests
import json
from typing import Dict, Optional

# Configuration
API_BASE = "https://admin-policy-hub.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

# Test Results
results = {
    "passed": [],
    "failed": []
}


def log_result(test_name: str, passed: bool, details: str = ""):
    """Log test result with details."""
    status = "✅ PASS" if passed else "❌ FAIL"
    result_entry = f"{status}: {test_name}"
    if details:
        result_entry += f"\n   Details: {details}"
    
    if passed:
        results["passed"].append(result_entry)
    else:
        results["failed"].append(result_entry)
    
    print(result_entry)


def test_1_login_returns_200_and_sets_cookie() -> Optional[requests.Session]:
    """Test 1: POST /api/auth/login returns 200 and sets cookie."""
    print("\n" + "="*70)
    print("TEST 1: POST /api/auth/login returns 200 and sets cookie")
    print("="*70)
    
    session = requests.Session()
    
    try:
        response = session.post(
            f"{API_BASE}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        
        # Check status code
        if response.status_code != 200:
            log_result(
                "Login returns 200",
                False,
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
            return None
        
        log_result("Login returns 200", True, f"Status code: {response.status_code}")
        
        # Check if cookies are set
        cookies = session.cookies.get_dict()
        if not cookies:
            log_result("Login sets cookie", False, "No cookies set in response")
            return None
        
        # Check for session cookie (common names: session, auth_token, etc.)
        cookie_names = list(cookies.keys())
        log_result(
            "Login sets cookie",
            True,
            f"Cookies set: {', '.join(cookie_names)}"
        )
        
        # Verify response data
        try:
            data = response.json()
            user_email = data.get("email", "")
            user_plan = data.get("subscription_plan", "")
            log_result(
                "Login response data",
                True,
                f"User: {user_email}, Plan: {user_plan}"
            )
        except Exception as e:
            log_result("Login response data", False, f"Failed to parse JSON: {e}")
        
        return session
        
    except Exception as e:
        log_result("Login returns 200", False, f"Exception: {str(e)}")
        return None


def test_2_authenticated_bootstrap_returns_200(session: requests.Session) -> Optional[Dict]:
    """Test 2: GET /api/video-studio/bootstrap with auth cookie returns 200 (not 403)."""
    print("\n" + "="*70)
    print("TEST 2: GET /api/video-studio/bootstrap with auth returns 200 (not 403)")
    print("="*70)
    
    try:
        response = session.get(
            f"{API_BASE}/video-studio/bootstrap",
            timeout=10
        )
        
        # Check status code is 200 (not 403)
        if response.status_code == 403:
            log_result(
                "Authenticated bootstrap returns 200 (not 403)",
                False,
                f"Got 403 Forbidden - ACL blocking authenticated user: {response.text[:200]}"
            )
            return None
        
        if response.status_code != 200:
            log_result(
                "Authenticated bootstrap returns 200 (not 403)",
                False,
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
            return None
        
        log_result(
            "Authenticated bootstrap returns 200 (not 403)",
            True,
            f"Status code: {response.status_code} (ACL allows authenticated access)"
        )
        
        # Parse response
        try:
            data = response.json()
            return data
        except Exception as e:
            log_result("Bootstrap response parsing", False, f"Failed to parse JSON: {e}")
            return None
        
    except Exception as e:
        log_result("Authenticated bootstrap returns 200", False, f"Exception: {str(e)}")
        return None


def test_3_bootstrap_response_has_expected_keys(data: Dict):
    """Test 3: Response JSON has expected keys: success, plan, limits, usage, projects, templates, features."""
    print("\n" + "="*70)
    print("TEST 3: Response has expected keys")
    print("="*70)
    
    # Expected keys from review request
    expected_keys = ["success", "plan", "limits", "usage", "projects", "templates", "features"]
    
    missing_keys = []
    present_keys = []
    
    for key in expected_keys:
        if key in data:
            present_keys.append(key)
        else:
            missing_keys.append(key)
    
    if missing_keys:
        log_result(
            "Bootstrap response has expected keys",
            False,
            f"Missing keys: {', '.join(missing_keys)}"
        )
    else:
        log_result(
            "Bootstrap response has expected keys",
            True,
            f"All expected keys present: {', '.join(expected_keys)}"
        )
    
    # Log details of each key
    print("\n   Key details:")
    for key in expected_keys:
        if key in data:
            value = data[key]
            if isinstance(value, (list, dict)):
                print(f"   - {key}: {type(value).__name__} (length: {len(value)})")
            else:
                print(f"   - {key}: {value}")
        else:
            print(f"   - {key}: MISSING")


def test_4_unauthenticated_bootstrap_returns_401_or_403():
    """Test 4: Confirm unauthenticated bootstrap returns 401/403."""
    print("\n" + "="*70)
    print("TEST 4: Unauthenticated bootstrap returns 401/403")
    print("="*70)
    
    try:
        # Create new session without authentication
        response = requests.get(
            f"{API_BASE}/video-studio/bootstrap",
            timeout=10
        )
        
        # Check status code is 401 or 403
        if response.status_code in [401, 403]:
            log_result(
                "Unauthenticated bootstrap returns 401/403",
                True,
                f"Status code: {response.status_code} (correctly rejects unauthenticated access)"
            )
        else:
            log_result(
                "Unauthenticated bootstrap returns 401/403",
                False,
                f"Expected 401 or 403, got {response.status_code} - endpoint allows unauthenticated access!"
            )
        
    except Exception as e:
        log_result("Unauthenticated bootstrap returns 401/403", False, f"Exception: {str(e)}")


def print_summary():
    """Print test summary."""
    print("\n" + "="*70)
    print("FEATURE 15 ACL FIX VERIFICATION SUMMARY")
    print("="*70)
    
    passed_count = len(results["passed"])
    failed_count = len(results["failed"])
    total_tests = passed_count + failed_count
    
    print(f"\n✅ Passed: {passed_count}/{total_tests}")
    print(f"❌ Failed: {failed_count}/{total_tests}")
    
    if results["passed"]:
        print("\n✅ PASSED TESTS:")
        for test in results["passed"]:
            print(f"   {test}")
    
    if results["failed"]:
        print("\n❌ FAILED TESTS:")
        for test in results["failed"]:
            print(f"   {test}")
    
    print("\n" + "="*70)
    
    if failed_count == 0:
        print("🎉 ALL TESTS PASSED - Feature 15 ACL fix verified successfully!")
        print("="*70)
        return 0
    else:
        print(f"⚠️  {failed_count} TEST(S) FAILED - ACL fix needs attention")
        print("="*70)
        return 1


def main():
    """Main test execution."""
    print("="*70)
    print("FEATURE 15 ACL FIX VERIFICATION")
    print("="*70)
    print(f"URL: {API_BASE}")
    print(f"Credentials: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print("="*70)
    
    # Test 1: Login returns 200 and sets cookie
    session = test_1_login_returns_200_and_sets_cookie()
    if not session:
        print("\n❌ FATAL: Login failed. Cannot proceed with authenticated tests.")
        print_summary()
        return 1
    
    # Test 2: Authenticated bootstrap returns 200 (not 403)
    bootstrap_data = test_2_authenticated_bootstrap_returns_200(session)
    if not bootstrap_data:
        print("\n❌ FATAL: Bootstrap endpoint failed. Cannot verify response structure.")
        # Continue to test 4 even if test 2 fails
    else:
        # Test 3: Response has expected keys
        test_3_bootstrap_response_has_expected_keys(bootstrap_data)
    
    # Test 4: Unauthenticated bootstrap returns 401/403
    test_4_unauthenticated_bootstrap_returns_401_or_403()
    
    # Print summary
    return print_summary()


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
