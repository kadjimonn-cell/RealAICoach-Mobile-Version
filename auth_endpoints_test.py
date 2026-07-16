"""
Backend Auth Endpoints Verification Test
Tests auth endpoints for proper error handling, especially email delivery failures.

Required checks:
1. /api/auth/password/reset/request - must return 200, 429, or 503 (NOT 500)
2. /api/auth/otp/request - must return 200, 404, 429, or 503 (NOT 500)
3. /api/auth/login - regression test for invalid credentials (401/400)
4. /api/auth/otp/verify - regression test for invalid code (400/401/404)
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

# Test results
test_results = []
all_passed = True


def log_test(name, passed, status_code=None, detail=None, response_data=None, expected_codes=None):
    """Log test result"""
    global all_passed
    result = {
        "test": name,
        "passed": passed,
        "status_code": status_code,
        "detail": detail,
        "expected_codes": expected_codes,
        "response_data": response_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    test_results.append(result)
    
    if not passed:
        all_passed = False
    
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status}: {name}")
    if status_code:
        print(f"  Status Code: {status_code}")
    if expected_codes:
        print(f"  Expected Codes: {expected_codes}")
    if detail:
        print(f"  Detail: {detail}")
    if response_data and not passed:
        print(f"  Response: {json.dumps(response_data, indent=2)[:500]}")


def test_password_reset_request():
    """
    Test /api/auth/password/reset/request
    Must return 200 (success), 429 (rate limited), or 503 (service unavailable)
    Must NOT return 500 for email delivery failures
    """
    print("\n" + "="*80)
    print("TEST 1: Password Reset Request")
    print("="*80)
    
    url = f"{API_BASE}/auth/password/reset/request"
    payload = {"email": ADMIN_EMAIL}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        status_code = response.status_code
        
        try:
            response_data = response.json()
        except:
            response_data = {"raw": response.text}
        
        # Expected status codes: 200, 429, 503
        # NOT acceptable: 500
        expected_codes = [200, 429, 503]
        
        if status_code in expected_codes:
            log_test(
                "Password Reset Request - Proper Status Code",
                True,
                status_code=status_code,
                detail=f"Returned acceptable status code: {status_code}",
                expected_codes=expected_codes,
                response_data=response_data
            )
        elif status_code == 500:
            log_test(
                "Password Reset Request - Proper Status Code",
                False,
                status_code=status_code,
                detail="❌ CRITICAL: Returned 500 instead of 503 for email delivery failure",
                expected_codes=expected_codes,
                response_data=response_data
            )
        else:
            log_test(
                "Password Reset Request - Proper Status Code",
                False,
                status_code=status_code,
                detail=f"Unexpected status code: {status_code}",
                expected_codes=expected_codes,
                response_data=response_data
            )
        
        return status_code in expected_codes
        
    except Exception as e:
        log_test(
            "Password Reset Request - Proper Status Code",
            False,
            detail=f"Request failed with exception: {str(e)}"
        )
        return False


def test_otp_request():
    """
    Test /api/auth/otp/request
    Must return 200 (success), 404 (user not found), 429 (rate limited), or 503 (service unavailable)
    Must NOT return 500 for email delivery failures
    """
    print("\n" + "="*80)
    print("TEST 2: OTP Request")
    print("="*80)
    
    url = f"{API_BASE}/auth/otp/request"
    payload = {"email": ADMIN_EMAIL}
    headers = {"X-Requested-With": "XMLHttpRequest"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        status_code = response.status_code
        
        try:
            response_data = response.json()
        except:
            response_data = {"raw": response.text}
        
        # Expected status codes: 200, 404, 429, 503
        # NOT acceptable: 500
        expected_codes = [200, 404, 429, 503]
        
        if status_code in expected_codes:
            log_test(
                "OTP Request - Proper Status Code",
                True,
                status_code=status_code,
                detail=f"Returned acceptable status code: {status_code}",
                expected_codes=expected_codes,
                response_data=response_data
            )
        elif status_code == 500:
            log_test(
                "OTP Request - Proper Status Code",
                False,
                status_code=status_code,
                detail="❌ CRITICAL: Returned 500 instead of 503 for email delivery failure",
                expected_codes=expected_codes,
                response_data=response_data
            )
        else:
            log_test(
                "OTP Request - Proper Status Code",
                False,
                status_code=status_code,
                detail=f"Unexpected status code: {status_code}",
                expected_codes=expected_codes,
                response_data=response_data
            )
        
        return status_code in expected_codes
        
    except Exception as e:
        log_test(
            "OTP Request - Proper Status Code",
            False,
            detail=f"Request failed with exception: {str(e)}"
        )
        return False


def test_login_invalid_credentials():
    """
    Test /api/auth/login with invalid credentials
    Regression test: must return 401 or 400 for invalid credentials
    """
    print("\n" + "="*80)
    print("TEST 3: Login with Invalid Credentials (Regression)")
    print("="*80)
    
    url = f"{API_BASE}/auth/login"
    payload = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword123!"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        status_code = response.status_code
        
        try:
            response_data = response.json()
        except:
            response_data = {"raw": response.text}
        
        # Expected status codes: 401, 400
        expected_codes = [401, 400]
        
        if status_code in expected_codes:
            log_test(
                "Login Invalid Credentials - Proper Error Code",
                True,
                status_code=status_code,
                detail=f"Correctly returned {status_code} for invalid credentials",
                expected_codes=expected_codes,
                response_data=response_data
            )
        else:
            log_test(
                "Login Invalid Credentials - Proper Error Code",
                False,
                status_code=status_code,
                detail=f"Expected 401/400, got {status_code}",
                expected_codes=expected_codes,
                response_data=response_data
            )
        
        return status_code in expected_codes
        
    except Exception as e:
        log_test(
            "Login Invalid Credentials - Proper Error Code",
            False,
            detail=f"Request failed with exception: {str(e)}"
        )
        return False


def test_otp_verify_invalid_code():
    """
    Test /api/auth/otp/verify with invalid code
    Regression test: must return 400, 401, or 404 for invalid code
    """
    print("\n" + "="*80)
    print("TEST 4: OTP Verify with Invalid Code (Regression)")
    print("="*80)
    
    url = f"{API_BASE}/auth/otp/verify"
    payload = {
        "email": ADMIN_EMAIL,
        "code": "999999"  # Invalid code
    }
    headers = {"X-Requested-With": "XMLHttpRequest"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        status_code = response.status_code
        
        try:
            response_data = response.json()
        except:
            response_data = {"raw": response.text}
        
        # Expected status codes: 400, 401, 404
        expected_codes = [400, 401, 404]
        
        if status_code in expected_codes:
            log_test(
                "OTP Verify Invalid Code - Proper Error Code",
                True,
                status_code=status_code,
                detail=f"Correctly returned {status_code} for invalid code",
                expected_codes=expected_codes,
                response_data=response_data
            )
        else:
            log_test(
                "OTP Verify Invalid Code - Proper Error Code",
                False,
                status_code=status_code,
                detail=f"Expected 400/401/404, got {status_code}",
                expected_codes=expected_codes,
                response_data=response_data
            )
        
        return status_code in expected_codes
        
    except Exception as e:
        log_test(
            "OTP Verify Invalid Code - Proper Error Code",
            False,
            detail=f"Request failed with exception: {str(e)}"
        )
        return False


def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for r in test_results if r["passed"])
    total_count = len(test_results)
    
    print(f"\nTotal Tests: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nFailed Tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['test']}")
                print(f"    Status: {result.get('status_code', 'N/A')}")
                print(f"    Detail: {result.get('detail', 'N/A')}")
    
    # Save results to file
    with open("/app/auth_endpoints_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "base_url": BASE_URL,
            "total_tests": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "all_passed": all_passed,
            "results": test_results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/auth_endpoints_test_results.json")


def main():
    """Run all tests"""
    print("="*80)
    print("BACKEND AUTH ENDPOINTS VERIFICATION TEST")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Test User: {ADMIN_EMAIL}")
    print("="*80)
    
    # Run tests
    test_password_reset_request()
    test_otp_request()
    test_login_invalid_credentials()
    test_otp_verify_invalid_code()
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
