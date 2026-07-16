#!/usr/bin/env python3
"""
Auth Continuity Validation Test
Tests auth flow continuity after latest fix as per review request
"""

import requests
import sys
from typing import Optional

# Test configuration
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = "watchvideos.premium.4dc6ab84@example.com"
TEST_PASSWORD = "WatchVideos#2026Aa"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*80}{Colors.RESET}")

def print_test(name: str):
    print(f"\n{Colors.YELLOW}TEST {name}{Colors.RESET}")

def print_pass(message: str, code: Optional[int] = None):
    code_str = f" [{code}]" if code else ""
    print(f"{Colors.GREEN}✅ PASS{code_str}: {message}{Colors.RESET}")

def print_fail(message: str, code: Optional[int] = None):
    code_str = f" [{code}]" if code else ""
    print(f"{Colors.RED}❌ FAIL{code_str}: {message}{Colors.RESET}")

def print_info(message: str):
    print(f"   {message}")

def main():
    """Run auth continuity validation tests"""
    print_header("AUTH CONTINUITY VALIDATION")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_EMAIL}")
    
    results = []
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    })
    
    # Test 1: POST /api/auth/login returns 200 and session cookie set
    print_test("1: POST /api/auth/login")
    try:
        response = session.post(
            f"{API_BASE}/auth/login",
            json={'email': TEST_EMAIL, 'password': TEST_PASSWORD},
            timeout=15
        )
        
        cookies = session.cookies.get_dict()
        has_session = any('session' in k.lower() for k in cookies.keys())
        
        if response.status_code == 200 and has_session:
            print_pass("Login successful, session cookie set", response.status_code)
            print_info(f"Cookies: {list(cookies.keys())}")
            results.append(True)
        else:
            print_fail(f"Login failed or no session cookie", response.status_code)
            print_info(f"Cookies: {list(cookies.keys())}")
            results.append(False)
    except Exception as e:
        print_fail(f"Request error: {str(e)}")
        results.append(False)
    
    # Test 2: GET /api/auth/me with cookie returns 200
    print_test("2: GET /api/auth/me (with cookie)")
    try:
        response = session.get(f"{API_BASE}/auth/me", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            user_email = data.get('email', 'N/A')
            print_pass(f"Auth/me successful, user: {user_email}", response.status_code)
            results.append(True)
        else:
            print_fail("Auth/me failed", response.status_code)
            print_info(f"Response: {response.text[:200]}")
            results.append(False)
    except Exception as e:
        print_fail(f"Request error: {str(e)}")
        results.append(False)
    
    # Test 3: GET /api/videos/bootstrap with same cookie returns 200
    print_test("3: GET /api/videos/bootstrap (with same cookie)")
    try:
        response = session.get(f"{API_BASE}/videos/bootstrap", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print_pass("Videos bootstrap successful", response.status_code)
            print_info(f"Response keys: {list(data.keys())[:5]}")
            results.append(True)
        else:
            print_fail("Videos bootstrap failed", response.status_code)
            print_info(f"Response: {response.text[:200]}")
            results.append(False)
    except Exception as e:
        print_fail(f"Request error: {str(e)}")
        results.append(False)
    
    # Test 4: POST /api/auth/logout invalidates session
    print_test("4: POST /api/auth/logout")
    try:
        response = session.post(
            f"{API_BASE}/auth/logout",
            json={},
            headers={'X-Requested-With': 'XMLHttpRequest'},
            timeout=15
        )
        
        if response.status_code in [200, 204]:
            print_pass("Logout successful", response.status_code)
            results.append(True)
        else:
            print_fail("Logout failed", response.status_code)
            print_info(f"Response: {response.text[:200]}")
            results.append(False)
    except Exception as e:
        print_fail(f"Request error: {str(e)}")
        results.append(False)
    
    # Test 5: After logout, GET /api/auth/me returns 401 (expected)
    print_test("5: GET /api/auth/me (after logout, expect 401)")
    try:
        response = session.get(f"{API_BASE}/auth/me", timeout=15)
        
        if response.status_code == 401:
            print_pass("Auth/me correctly returns 401 after logout", response.status_code)
            results.append(True)
        else:
            print_fail(f"Expected 401, got {response.status_code}", response.status_code)
            print_info(f"Response: {response.text[:200]}")
            results.append(False)
    except Exception as e:
        print_fail(f"Request error: {str(e)}")
        results.append(False)
    
    # Test 6: Validate no unexpected auth loop behavior at API layer
    print_test("6: Auth loop detection (re-login and multiple requests)")
    try:
        # Re-login
        login_response = session.post(
            f"{API_BASE}/auth/login",
            json={'email': TEST_EMAIL, 'password': TEST_PASSWORD},
            timeout=15
        )
        
        if login_response.status_code != 200:
            print_fail("Re-login failed", login_response.status_code)
            results.append(False)
        else:
            # Make multiple /auth/me requests to check for loops
            auth_responses = []
            for i in range(3):
                r = session.get(f"{API_BASE}/auth/me", timeout=15)
                auth_responses.append(r.status_code)
            
            # All should return 200 without requiring refresh
            if all(status == 200 for status in auth_responses):
                print_pass(f"No auth loop detected, all requests returned 200", 200)
                print_info(f"Response codes: {auth_responses}")
                results.append(True)
            else:
                print_fail(f"Auth loop detected or inconsistent responses", None)
                print_info(f"Response codes: {auth_responses}")
                results.append(False)
    except Exception as e:
        print_fail(f"Request error: {str(e)}")
        results.append(False)
    
    # Summary
    print_header("TEST SUMMARY")
    
    test_names = [
        "1. POST /api/auth/login (200 + cookie)",
        "2. GET /api/auth/me (200)",
        "3. GET /api/videos/bootstrap (200)",
        "4. POST /api/auth/logout (invalidates)",
        "5. GET /api/auth/me after logout (401)",
        "6. No auth loop behavior"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if result else f"{Colors.RED}❌ FAIL{Colors.RESET}"
        print(f"{status} - {name}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n{Colors.BLUE}Total: {total} | Passed: {Colors.GREEN}{passed}{Colors.RESET} | Failed: {Colors.RED}{total - passed}{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{'='*80}{Colors.RESET}")
        print(f"{Colors.GREEN}ALL AUTH CONTINUITY TESTS PASSED ✅{Colors.RESET}")
        print(f"{Colors.GREEN}{'='*80}{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{'='*80}{Colors.RESET}")
        print(f"{Colors.RED}SOME TESTS FAILED ❌{Colors.RESET}")
        print(f"{Colors.RED}{'='*80}{Colors.RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
