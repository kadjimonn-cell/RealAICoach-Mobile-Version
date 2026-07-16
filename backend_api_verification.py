#!/usr/bin/env python3
"""
Backend API Verification - Retention Profile & Streak Rewards
Tests specific requirements from review request:
1. POST /api/auth/login with premium user
2. GET /api/videos/bootstrap - verify retention_profile with streak_rewards structure
3. Unauthenticated GET /api/videos/bootstrap should be unauthorized
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Backend URL from frontend/.env
BACKEND_URL = "https://admin-policy-hub.preview.emergentagent.com"

# Test credentials from test_credentials.md
PREMIUM_USER_EMAIL = "watchvideos.premium.4dc6ab84@example.com"
PREMIUM_USER_PASSWORD = "WatchVideos#2026Aa"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_section(text: str):
    """Print formatted section"""
    print(f"\n{Colors.CYAN}{'─'*80}{Colors.RESET}")
    print(f"{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'─'*80}{Colors.RESET}")

def log_test(test_name: str, status: str, details: str = ""):
    """Log test result with color coding"""
    color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
    symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{color}{symbol} [{status}]{Colors.RESET} {test_name}")
    if details:
        for line in details.split('\n'):
            if line.strip():
                print(f"      {line}")

def print_json_snippet(data: Any, max_lines: int = 10):
    """Print formatted JSON snippet"""
    try:
        json_str = json.dumps(data, indent=2)
        lines = json_str.split('\n')
        for i, line in enumerate(lines[:max_lines]):
            print(f"      {line}")
        if len(lines) > max_lines:
            print(f"      ... ({len(lines) - max_lines} more lines)")
    except:
        print(f"      {str(data)[:200]}")

def test_unauthenticated_videos_bootstrap():
    """Test 1: Unauthenticated GET /api/videos/bootstrap should return 401"""
    print_section("Test 1: Unauthenticated Access Control")
    test_name = "GET /api/videos/bootstrap (unauthenticated)"
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/videos/bootstrap",
            timeout=10
        )
        
        print(f"   Request: GET {BACKEND_URL}/api/videos/bootstrap")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 401:
            log_test(test_name, "PASS", f"Correctly returned 401 Unauthorized")
            return True
        elif response.status_code == 403:
            log_test(test_name, "PASS", f"Correctly returned 403 Forbidden")
            return True
        else:
            log_test(test_name, "FAIL", 
                    f"Expected 401/403, got {response.status_code}\n"
                    f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_premium_login() -> Optional[requests.Session]:
    """Test 2: POST /api/auth/login with premium user"""
    print_section("Test 2: Premium User Authentication")
    test_name = "POST /api/auth/login (premium user)"
    
    try:
        session = requests.Session()
        
        login_data = {
            "email": PREMIUM_USER_EMAIL,
            "password": PREMIUM_USER_PASSWORD
        }
        
        print(f"   Request: POST {BACKEND_URL}/api/auth/login")
        print(f"   Email: {PREMIUM_USER_EMAIL}")
        
        response = session.post(
            f"{BACKEND_URL}/api/auth/login",
            json=login_data,
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                user_id = data.get('user_id', 'N/A')
                email = data.get('email', 'N/A')
                plan = data.get('subscription_plan', 'N/A')
                
                log_test(test_name, "PASS", 
                        f"Login successful\n"
                        f"User ID: {user_id}\n"
                        f"Email: {email}\n"
                        f"Plan: {plan}")
                return session
            except:
                log_test(test_name, "PASS", "Login successful (session established)")
                return session
        else:
            log_test(test_name, "FAIL", 
                    f"Expected 200, got {response.status_code}\n"
                    f"Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return None

def test_authenticated_videos_bootstrap(session: requests.Session):
    """Test 3: GET /api/videos/bootstrap with authentication - verify structure"""
    print_section("Test 3: Authenticated Bootstrap with Retention Profile Validation")
    test_name = "GET /api/videos/bootstrap (authenticated)"
    
    try:
        print(f"   Request: GET {BACKEND_URL}/api/videos/bootstrap")
        
        response = session.get(
            f"{BACKEND_URL}/api/videos/bootstrap",
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code != 200:
            log_test(test_name, "FAIL", 
                    f"Expected 200, got {response.status_code}\n"
                    f"Response: {response.text[:200]}")
            return False
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            log_test(test_name, "FAIL", f"Failed to parse JSON response: {str(e)}")
            return False
        
        print(f"\n   Response structure:")
        print_json_snippet(data, max_lines=15)
        
        # Validation checks
        validation_results = []
        
        # Check 1: Response is 200
        validation_results.append(("Response status 200", True, "✓"))
        
        # Check 2: retention_profile exists
        has_retention_profile = 'retention_profile' in data
        validation_results.append((
            "retention_profile object exists",
            has_retention_profile,
            "✓" if has_retention_profile else "✗"
        ))
        
        if not has_retention_profile:
            print(f"\n   {Colors.RED}❌ CRITICAL: retention_profile not found in response{Colors.RESET}")
            print(f"   Available keys: {list(data.keys())}")
            log_test(test_name, "FAIL", "retention_profile object missing from response")
            return False
        
        retention_profile = data['retention_profile']
        
        # Check 3: streak_rewards exists in retention_profile
        has_streak_rewards = 'streak_rewards' in retention_profile
        validation_results.append((
            "streak_rewards object exists in retention_profile",
            has_streak_rewards,
            "✓" if has_streak_rewards else "✗"
        ))
        
        if not has_streak_rewards:
            print(f"\n   {Colors.RED}❌ CRITICAL: streak_rewards not found in retention_profile{Colors.RESET}")
            print(f"   retention_profile keys: {list(retention_profile.keys())}")
            log_test(test_name, "FAIL", "streak_rewards object missing from retention_profile")
            return False
        
        streak_rewards = retention_profile['streak_rewards']
        
        # Check 4: Required keys in streak_rewards
        required_keys = [
            'current_streak_days',
            'streak_status',
            'points',
            'current_badge',
            'badges_unlocked',
            'next_milestone'
        ]
        
        print(f"\n   {Colors.CYAN}Validating streak_rewards structure:{Colors.RESET}")
        print(f"   streak_rewards content:")
        print_json_snippet(streak_rewards, max_lines=20)
        
        all_keys_present = True
        for key in required_keys:
            key_exists = key in streak_rewards
            validation_results.append((
                f"streak_rewards.{key}",
                key_exists,
                f"✓ = {streak_rewards.get(key)}" if key_exists else "✗ MISSING"
            ))
            if not key_exists:
                all_keys_present = False
        
        # Print validation summary
        print(f"\n   {Colors.CYAN}Validation Results:{Colors.RESET}")
        for check_name, passed, detail in validation_results:
            color = Colors.GREEN if passed else Colors.RED
            symbol = "✅" if passed else "❌"
            print(f"   {color}{symbol} {check_name}: {detail}{Colors.RESET}")
        
        # Final verdict
        if all_keys_present:
            log_test(test_name, "PASS", 
                    f"All required fields present in response\n"
                    f"✓ retention_profile exists\n"
                    f"✓ streak_rewards exists\n"
                    f"✓ All 6 required keys present: {', '.join(required_keys)}")
            return True
        else:
            missing_keys = [k for k in required_keys if k not in streak_rewards]
            log_test(test_name, "FAIL", 
                    f"Missing required keys in streak_rewards: {', '.join(missing_keys)}\n"
                    f"Found keys: {list(streak_rewards.keys())}")
            return False
            
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        import traceback
        print(f"   {Colors.RED}Traceback:{Colors.RESET}")
        print(f"   {traceback.format_exc()}")
        return False

def main():
    """Run all backend API verification tests"""
    print_header("Backend API Verification - Retention Profile & Streak Rewards")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User: {PREMIUM_USER_EMAIL}")
    
    results = []
    
    # Test 1: Unauthenticated access should be blocked
    results.append(("Unauthenticated RBAC", test_unauthenticated_videos_bootstrap()))
    
    # Test 2: Login with premium user
    session = test_premium_login()
    if session:
        results.append(("Premium Login", True))
        
        # Test 3: Authenticated bootstrap with structure validation
        results.append(("Bootstrap Structure Validation", test_authenticated_videos_bootstrap(session)))
    else:
        results.append(("Premium Login", False))
        results.append(("Bootstrap Structure Validation", False))
        print(f"\n{Colors.YELLOW}⚠️  Skipping bootstrap validation due to login failure{Colors.RESET}")
    
    # Final Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Results:")
    for test_name, result in results:
        color = Colors.GREEN if result else Colors.RED
        symbol = "✅" if result else "❌"
        status = "PASS" if result else "FAIL"
        print(f"  {color}{symbol} {test_name}: {status}{Colors.RESET}")
    
    print(f"\n{Colors.BLUE}{'─'*80}{Colors.RESET}")
    
    if passed == total:
        print(f"{Colors.GREEN}✅ ALL TESTS PASSED ({passed}/{total}){Colors.RESET}")
        print(f"{Colors.BLUE}{'='*80}{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"{Colors.RED}❌ SOME TESTS FAILED ({passed}/{total} passed, {total-passed} failed){Colors.RESET}")
        print(f"{Colors.BLUE}{'='*80}{Colors.RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
