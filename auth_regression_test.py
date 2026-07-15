#!/usr/bin/env python3
"""
Auth Flow Regression Test
Tests backend auth endpoints after frontend-only protected-route refactor
"""

import requests
import json
import sys

# Configuration
BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"
FREE_USER_EMAIL = "p1.free.1779113329@example.com"
FREE_USER_PASSWORD = "P1Free#2026!Aa"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log_test(name, status, details=""):
    """Log test result with color"""
    color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
    print(f"{color}[{status}]{Colors.END} {name}")
    if details:
        print(f"      {details}")

def test_login(email, password, user_type="free"):
    """Test POST /api/auth/login"""
    print(f"\n{Colors.BLUE}=== Testing Login for {user_type} user ==={Colors.END}")
    
    session = requests.Session()
    
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password},
            headers={
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            },
            timeout=30
        )
        
        status_code = response.status_code
        
        if status_code == 200:
            try:
                data = response.json()
                log_test(f"POST /api/auth/login ({user_type})", "PASS", 
                        f"Status: {status_code}, User: {data.get('user', {}).get('email', 'N/A')}")
                
                # Check for cookies
                cookies = session.cookies.get_dict()
                if cookies:
                    print(f"      Cookies set: {', '.join(cookies.keys())}")
                else:
                    print(f"      {Colors.YELLOW}Warning: No cookies set{Colors.END}")
                
                return session, True
            except json.JSONDecodeError:
                log_test(f"POST /api/auth/login ({user_type})", "FAIL", 
                        f"Status: {status_code}, Invalid JSON response")
                return session, False
        elif status_code == 500:
            log_test(f"POST /api/auth/login ({user_type})", "FAIL", 
                    f"Status: 500 - Server Error: {response.text[:200]}")
            return session, False
        else:
            log_test(f"POST /api/auth/login ({user_type})", "FAIL", 
                    f"Status: {status_code}, Response: {response.text[:200]}")
            return session, False
            
    except requests.exceptions.RequestException as e:
        log_test(f"POST /api/auth/login ({user_type})", "FAIL", 
                f"Request exception: {str(e)}")
        return session, False

def test_auth_me(session, user_type="free"):
    """Test GET /api/auth/me"""
    print(f"\n{Colors.BLUE}=== Testing /api/auth/me for {user_type} user ==={Colors.END}")
    
    try:
        response = session.get(
            f"{BASE_URL}/api/auth/me",
            headers={
                "X-Requested-With": "XMLHttpRequest"
            },
            timeout=30
        )
        
        status_code = response.status_code
        
        if status_code == 200:
            try:
                data = response.json()
                user = data.get('user', {})
                log_test(f"GET /api/auth/me ({user_type})", "PASS", 
                        f"Status: {status_code}, User: {user.get('email', 'N/A')}, Plan: {user.get('subscription_plan', 'N/A')}")
                return True
            except json.JSONDecodeError:
                log_test(f"GET /api/auth/me ({user_type})", "FAIL", 
                        f"Status: {status_code}, Invalid JSON response")
                return False
        elif status_code == 401:
            log_test(f"GET /api/auth/me ({user_type})", "FAIL", 
                    f"Status: 401 - Unauthorized (session not persisting)")
            return False
        elif status_code == 500:
            log_test(f"GET /api/auth/me ({user_type})", "FAIL", 
                    f"Status: 500 - Server Error: {response.text[:200]}")
            return False
        else:
            log_test(f"GET /api/auth/me ({user_type})", "FAIL", 
                    f"Status: {status_code}, Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        log_test(f"GET /api/auth/me ({user_type})", "FAIL", 
                f"Request exception: {str(e)}")
        return False

def test_logout(session, user_type="free"):
    """Test POST /api/auth/logout"""
    print(f"\n{Colors.BLUE}=== Testing Logout for {user_type} user ==={Colors.END}")
    
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/logout",
            headers={
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            },
            timeout=30
        )
        
        status_code = response.status_code
        
        if status_code == 200:
            try:
                data = response.json()
                log_test(f"POST /api/auth/logout ({user_type})", "PASS", 
                        f"Status: {status_code}, Success: {data.get('success', False)}")
                return True
            except json.JSONDecodeError:
                log_test(f"POST /api/auth/logout ({user_type})", "FAIL", 
                        f"Status: {status_code}, Invalid JSON response")
                return False
        elif status_code == 500:
            log_test(f"POST /api/auth/logout ({user_type})", "FAIL", 
                    f"Status: 500 - Server Error: {response.text[:200]}")
            return False
        else:
            log_test(f"POST /api/auth/logout ({user_type})", "FAIL", 
                    f"Status: {status_code}, Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        log_test(f"POST /api/auth/logout ({user_type})", "FAIL", 
                f"Request exception: {str(e)}")
        return False

def test_auth_me_after_logout(session, user_type="free"):
    """Test GET /api/auth/me after logout (should be unauthenticated)"""
    print(f"\n{Colors.BLUE}=== Testing /api/auth/me after logout for {user_type} user ==={Colors.END}")
    
    try:
        response = session.get(
            f"{BASE_URL}/api/auth/me",
            headers={
                "X-Requested-With": "XMLHttpRequest"
            },
            timeout=30
        )
        
        status_code = response.status_code
        
        if status_code == 401:
            log_test(f"GET /api/auth/me after logout ({user_type})", "PASS", 
                    f"Status: 401 - Correctly unauthenticated after logout")
            return True
        elif status_code == 200:
            log_test(f"GET /api/auth/me after logout ({user_type})", "FAIL", 
                    f"Status: 200 - Session still active after logout (should be 401)")
            return False
        elif status_code == 500:
            log_test(f"GET /api/auth/me after logout ({user_type})", "FAIL", 
                    f"Status: 500 - Server Error: {response.text[:200]}")
            return False
        else:
            log_test(f"GET /api/auth/me after logout ({user_type})", "FAIL", 
                    f"Status: {status_code}, Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        log_test(f"GET /api/auth/me after logout ({user_type})", "FAIL", 
                f"Request exception: {str(e)}")
        return False

def run_auth_flow_test(email, password, user_type):
    """Run complete auth flow test for a user"""
    results = {
        "login": False,
        "auth_me": False,
        "logout": False,
        "auth_me_after_logout": False
    }
    
    # Test login
    session, login_success = test_login(email, password, user_type)
    results["login"] = login_success
    
    if not login_success:
        print(f"\n{Colors.RED}Login failed for {user_type} user. Skipping remaining tests.{Colors.END}")
        return results
    
    # Test /api/auth/me
    results["auth_me"] = test_auth_me(session, user_type)
    
    # Test logout
    results["logout"] = test_logout(session, user_type)
    
    # Test /api/auth/me after logout
    results["auth_me_after_logout"] = test_auth_me_after_logout(session, user_type)
    
    return results

def main():
    """Run all auth regression tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}Auth Flow Regression Test{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}Backend Auth Endpoints After Frontend Protected-Route Refactor{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"Base URL: {BASE_URL}")
    print(f"Free User: {FREE_USER_EMAIL}")
    print(f"Admin User: {ADMIN_EMAIL}")
    
    all_results = {}
    
    # Test free user
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}Testing Free User Auth Flow{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    all_results["free"] = run_auth_flow_test(FREE_USER_EMAIL, FREE_USER_PASSWORD, "free")
    
    # Test admin user
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}Testing Admin User Auth Flow{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    all_results["admin"] = run_auth_flow_test(ADMIN_EMAIL, ADMIN_PASSWORD, "admin")
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}Test Summary{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for user_type, results in all_results.items():
        print(f"\n{Colors.BOLD}{user_type.upper()} User:{Colors.END}")
        for test_name, result in results.items():
            total_tests += 1
            if result:
                passed_tests += 1
                print(f"  {Colors.GREEN}✓{Colors.END} {test_name}")
            else:
                failed_tests += 1
                print(f"  {Colors.RED}✗{Colors.END} {test_name}")
    
    print(f"\n{Colors.BOLD}Overall Results:{Colors.END}")
    print(f"  Total Tests: {total_tests}")
    print(f"  {Colors.GREEN}Passed: {passed_tests}{Colors.END}")
    print(f"  {Colors.RED}Failed: {failed_tests}{Colors.END}")
    
    if failed_tests == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All auth flow tests passed! No regressions detected.{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ {failed_tests} test(s) failed. Auth flow has regressions.{Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
