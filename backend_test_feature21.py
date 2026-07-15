#!/usr/bin/env python3
"""
Feature 21 (Watch Videos) Backend E2E Test
Tests Phase-0 contract stabilization after backend updates
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Base URL from environment
BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

# Test results
test_results = []
session_token = None
csrf_token = None


def log_test(name: str, passed: bool, details: str = "", response: Optional[requests.Response] = None):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = {
        "test": name,
        "status": status,
        "passed": passed,
        "details": details
    }
    
    if response:
        result["status_code"] = response.status_code
        result["url"] = response.url
        try:
            result["response_body"] = response.json()
        except:
            result["response_body"] = response.text[:500]
    
    test_results.append(result)
    print(f"{status} | {name}")
    if details:
        print(f"    {details}")
    if response:
        print(f"    Status: {response.status_code}, URL: {response.url}")


def test_unauth_access():
    """Test 1: Unauthenticated access should return 401"""
    print("\n=== Test 1: Unauthenticated Access (401 Expected) ===")
    
    # Test /api/videos/health
    try:
        resp = requests.get(f"{API_BASE}/videos/health", timeout=10)
        if resp.status_code == 401:
            log_test("GET /api/videos/health (unauth)", True, "Correctly returned 401", resp)
        else:
            log_test("GET /api/videos/health (unauth)", False, f"Expected 401, got {resp.status_code}", resp)
    except Exception as e:
        log_test("GET /api/videos/health (unauth)", False, f"Request failed: {str(e)}")
    
    # Test /api/videos/bootstrap
    try:
        resp = requests.get(f"{API_BASE}/videos/bootstrap", timeout=10)
        if resp.status_code == 401:
            log_test("GET /api/videos/bootstrap (unauth)", True, "Correctly returned 401", resp)
        else:
            log_test("GET /api/videos/bootstrap (unauth)", False, f"Expected 401, got {resp.status_code}", resp)
    except Exception as e:
        log_test("GET /api/videos/bootstrap (unauth)", False, f"Request failed: {str(e)}")


def login() -> bool:
    """Login and get session token"""
    global session_token, csrf_token
    
    print("\n=== Login ===")
    
    try:
        # First get CSRF token
        csrf_resp = requests.get(f"{API_BASE}/auth/csrf", timeout=10)
        if csrf_resp.status_code == 200:
            csrf_data = csrf_resp.json()
            csrf_token = csrf_data.get("csrf_token")
            print(f"✅ Got CSRF token: {csrf_token[:20]}...")
        
        # Login
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        headers = {}
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token
        
        resp = requests.post(
            f"{API_BASE}/auth/login",
            json=login_data,
            headers=headers,
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            session_token = data.get("session_token") or data.get("access_token")
            
            # Try to get from cookies if not in response
            if not session_token and resp.cookies:
                session_token = resp.cookies.get("session_token") or resp.cookies.get("access_token")
            
            log_test("POST /api/auth/login", True, f"Login successful", resp)
            return True
        else:
            log_test("POST /api/auth/login", False, f"Login failed with status {resp.status_code}", resp)
            return False
            
    except Exception as e:
        log_test("POST /api/auth/login", False, f"Login request failed: {str(e)}")
        return False


def get_auth_headers() -> Dict[str, str]:
    """Get headers with authentication"""
    headers = {
        "Content-Type": "application/json"
    }
    
    if session_token:
        headers["Authorization"] = f"Bearer {session_token}"
    
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token
    
    return headers


def test_authenticated_access():
    """Test 2: Authenticated access"""
    print("\n=== Test 2: Authenticated Access ===")
    
    headers = get_auth_headers()
    
    # Test /api/videos/health
    try:
        resp = requests.get(f"{API_BASE}/videos/health", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                if data.get("status") == "healthy" and data.get("feature_id") == "watch-videos":
                    log_test("GET /api/videos/health (auth)", True, 
                            f"status={data.get('status')}, feature_id={data.get('feature_id')}", resp)
                else:
                    log_test("GET /api/videos/health (auth)", False, 
                            f"Missing expected fields: status={data.get('status')}, feature_id={data.get('feature_id')}", resp)
            except json.JSONDecodeError:
                log_test("GET /api/videos/health (auth)", False, "Response not valid JSON", resp)
        else:
            log_test("GET /api/videos/health (auth)", False, f"Expected 200, got {resp.status_code}", resp)
    except Exception as e:
        log_test("GET /api/videos/health (auth)", False, f"Request failed: {str(e)}")
    
    # Test /api/videos/bootstrap
    try:
        resp = requests.get(f"{API_BASE}/videos/bootstrap", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                has_plan = "plan" in data or "subscription_plan" in data
                has_quota = "quota" in data or "usage" in data
                has_catalog = "catalog" in data or "categories" in data
                
                if has_plan and has_quota and has_catalog:
                    log_test("GET /api/videos/bootstrap (auth)", True, 
                            f"Has plan/quota/catalog keys", resp)
                else:
                    log_test("GET /api/videos/bootstrap (auth)", False, 
                            f"Missing keys: plan={has_plan}, quota={has_quota}, catalog={has_catalog}", resp)
            except json.JSONDecodeError:
                log_test("GET /api/videos/bootstrap (auth)", False, "Response not valid JSON", resp)
        else:
            log_test("GET /api/videos/bootstrap (auth)", False, f"Expected 200, got {resp.status_code}", resp)
    except Exception as e:
        log_test("GET /api/videos/bootstrap (auth)", False, f"Request failed: {str(e)}")
    
    # Test /api/videos/catalog
    try:
        resp = requests.get(
            f"{API_BASE}/videos/catalog?sort_by=latest&limit=12", 
            headers=headers, 
            timeout=10
        )
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                items = data.get("items") or data.get("videos") or data.get("catalog") or []
                
                if isinstance(items, list) and len(items) > 0:
                    log_test("GET /api/videos/catalog", True, 
                            f"Returned {len(items)} items", resp)
                else:
                    log_test("GET /api/videos/catalog", False, 
                            f"Empty or invalid items list", resp)
            except json.JSONDecodeError:
                log_test("GET /api/videos/catalog", False, "Response not valid JSON", resp)
        else:
            log_test("GET /api/videos/catalog", False, f"Expected 200, got {resp.status_code}", resp)
    except Exception as e:
        log_test("GET /api/videos/catalog", False, f"Request failed: {str(e)}")
    
    # Test /api/videos/recommendations/reasons
    try:
        resp = requests.get(
            f"{API_BASE}/videos/recommendations/reasons?limit=8", 
            headers=headers, 
            timeout=10
        )
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                success = data.get("success", False)
                items = data.get("items") or data.get("reasons") or []
                
                if success and isinstance(items, list):
                    log_test("GET /api/videos/recommendations/reasons", True, 
                            f"success=true, {len(items)} items", resp)
                else:
                    log_test("GET /api/videos/recommendations/reasons", False, 
                            f"success={success}, items={len(items) if isinstance(items, list) else 'invalid'}", resp)
            except json.JSONDecodeError:
                log_test("GET /api/videos/recommendations/reasons", False, "Response not valid JSON", resp)
        else:
            log_test("GET /api/videos/recommendations/reasons", False, f"Expected 200, got {resp.status_code}", resp)
    except Exception as e:
        log_test("GET /api/videos/recommendations/reasons", False, f"Request failed: {str(e)}")


def test_core_writes():
    """Test 3: Core write operations"""
    print("\n=== Test 3: Core Write Operations ===")
    
    headers = get_auth_headers()
    
    # First, get a video ID from catalog
    video_id = None
    try:
        resp = requests.get(f"{API_BASE}/videos/catalog?limit=1", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items") or data.get("videos") or data.get("catalog") or []
            if items and len(items) > 0:
                video_id = items[0].get("id") or items[0].get("video_id")
                print(f"✅ Got video ID for testing: {video_id}")
    except Exception as e:
        print(f"⚠️  Could not get video ID: {str(e)}")
    
    # Test POST /api/videos/watch
    if video_id:
        try:
            watch_data = {
                "video_id": video_id,
                "duration": 120,
                "completed": False
            }
            
            resp = requests.post(
                f"{API_BASE}/videos/watch",
                json=watch_data,
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    has_quota = "quota" in data or "usage" in data or "remaining" in data
                    has_history = "history" in data or "watch_history" in data or "watched" in data
                    
                    if has_quota or has_history:
                        log_test("POST /api/videos/watch", True, 
                                f"Has quota/history in response", resp)
                    else:
                        log_test("POST /api/videos/watch", True, 
                                f"Request successful (200)", resp)
                except json.JSONDecodeError:
                    log_test("POST /api/videos/watch", False, "Response not valid JSON", resp)
            else:
                log_test("POST /api/videos/watch", False, f"Expected 200, got {resp.status_code}", resp)
        except Exception as e:
            log_test("POST /api/videos/watch", False, f"Request failed: {str(e)}")
    else:
        log_test("POST /api/videos/watch", False, "No video ID available for testing")
    
    # Test POST /api/videos/feedback (like)
    if video_id:
        try:
            feedback_data = {
                "video_id": video_id,
                "action": "like"
            }
            
            resp = requests.post(
                f"{API_BASE}/videos/feedback",
                json=feedback_data,
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                log_test("POST /api/videos/feedback (like)", True, "Request successful", resp)
            else:
                log_test("POST /api/videos/feedback (like)", False, f"Expected 200, got {resp.status_code}", resp)
        except Exception as e:
            log_test("POST /api/videos/feedback (like)", False, f"Request failed: {str(e)}")
    else:
        log_test("POST /api/videos/feedback (like)", False, "No video ID available for testing")
    
    # Test POST /api/videos/feedback (clear)
    if video_id:
        try:
            feedback_data = {
                "video_id": video_id,
                "action": "clear"
            }
            
            resp = requests.post(
                f"{API_BASE}/videos/feedback",
                json=feedback_data,
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                log_test("POST /api/videos/feedback (clear)", True, "Request successful", resp)
            else:
                log_test("POST /api/videos/feedback (clear)", False, f"Expected 200, got {resp.status_code}", resp)
        except Exception as e:
            log_test("POST /api/videos/feedback (clear)", False, f"Request failed: {str(e)}")
    else:
        log_test("POST /api/videos/feedback (clear)", False, "No video ID available for testing")
    
    # Test POST /api/videos/watchlist/toggle
    if video_id:
        try:
            watchlist_data = {
                "video_id": video_id
            }
            
            resp = requests.post(
                f"{API_BASE}/videos/watchlist/toggle",
                json=watchlist_data,
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                log_test("POST /api/videos/watchlist/toggle", True, "Request successful", resp)
            else:
                log_test("POST /api/videos/watchlist/toggle", False, f"Expected 200, got {resp.status_code}", resp)
        except Exception as e:
            log_test("POST /api/videos/watchlist/toggle", False, f"Request failed: {str(e)}")
    else:
        log_test("POST /api/videos/watchlist/toggle", False, "No video ID available for testing")


def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['test']}")
                if result.get("details"):
                    print(f"    {result['details']}")
    
    # Check for 500 errors
    has_500 = any(r.get("status_code") == 500 for r in test_results)
    if has_500:
        print("\n⚠️  WARNING: 500 errors detected!")
    else:
        print("\n✅ No 500 errors detected")
    
    # Save results to file
    with open("/app/feature21_test_results.json", "w") as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "has_500_errors": has_500
            },
            "tests": test_results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/feature21_test_results.json")
    
    return failed == 0


def main():
    """Main test execution"""
    print("="*80)
    print("Feature 21 (Watch Videos) Backend E2E Test")
    print("Phase-0 Contract Stabilization Validation")
    print("="*80)
    
    # Test 1: Unauthenticated access
    test_unauth_access()
    
    # Login
    if not login():
        print("\n❌ Login failed, cannot continue with authenticated tests")
        print_summary()
        sys.exit(1)
    
    # Test 2: Authenticated access
    test_authenticated_access()
    
    # Test 3: Core writes
    test_core_writes()
    
    # Print summary
    success = print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
