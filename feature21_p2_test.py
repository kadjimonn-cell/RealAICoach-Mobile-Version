#!/usr/bin/env python3
"""
Feature 21 P2 Backend Test Suite
Tests admin observability endpoints with incident_volume_trend_24h and CSV export
"""

import requests
import json
from typing import Dict, Any, Optional

BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(test_name: str):
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}TEST: {test_name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")

def print_pass(message: str):
    print(f"{Colors.GREEN}✓ PASS: {message}{Colors.END}")

def print_fail(message: str):
    print(f"{Colors.RED}✗ FAIL: {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.YELLOW}ℹ INFO: {message}{Colors.END}")

def print_response(response: requests.Response, show_full_body: bool = False):
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
    try:
        body = response.json()
        if show_full_body:
            print(f"Body: {json.dumps(body, indent=2)}")
        else:
            # Show truncated body for large responses
            body_str = json.dumps(body, indent=2)
            if len(body_str) > 1000:
                print(f"Body (truncated): {body_str[:1000]}...")
            else:
                print(f"Body: {body_str}")
    except:
        text = response.text
        if len(text) > 500:
            print(f"Body (text, truncated): {text[:500]}...")
        else:
            print(f"Body (text): {text}")

# Test 1: Admin Login
def test_admin_login():
    print_test("1. POST /api/auth/login -> 200")
    try:
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=payload,
            timeout=10
        )
        print_response(response)
        
        if response.status_code == 200:
            print_pass("Admin login successful")
            cookies = response.cookies
            print_info(f"Session cookies obtained: {list(cookies.keys())}")
            return True, cookies
        else:
            print_fail(f"Expected 200, got {response.status_code}")
            return False, None
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        return False, None

# Test 2: Admin Observability Endpoint with incident_volume_trend_24h
def test_admin_observability(cookies):
    print_test("2. GET /api/videos/admin/observability?lookback_days=7 -> 200")
    try:
        response = requests.get(
            f"{BASE_URL}/api/videos/admin/observability",
            params={"lookback_days": 7},
            cookies=cookies,
            timeout=10
        )
        print_response(response, show_full_body=True)
        
        if response.status_code != 200:
            print_fail(f"Expected 200, got {response.status_code}")
            return False
        
        print_pass("Admin observability endpoint returned 200")
        
        # Validate response structure
        data = response.json()
        
        # Check for incident_volume_trend_24h field
        if 'incident_volume_trend_24h' not in data:
            print_fail("Missing 'incident_volume_trend_24h' field in response")
            return False
        
        print_pass("'incident_volume_trend_24h' field present in response")
        
        # Validate incident_volume_trend_24h structure
        trend_24h = data['incident_volume_trend_24h']
        
        if 'points' not in trend_24h:
            print_fail("Missing 'points' field in incident_volume_trend_24h")
            return False
        
        print_pass("'points' field present in incident_volume_trend_24h")
        
        points = trend_24h['points']
        
        # Check points length (expected 24)
        if len(points) != 24:
            print_fail(f"Expected 24 points, got {len(points)}")
            return False
        
        print_pass(f"incident_volume_trend_24h.points has correct length: 24")
        
        # Validate each point has required keys
        required_keys = ['hour_bucket', 'hour_label', 'total_calls', 'errors', 'quota_rejections', 'incident_events', 'incident_spike']
        
        for i, point in enumerate(points):
            missing_keys = [key for key in required_keys if key not in point]
            if missing_keys:
                print_fail(f"Point {i} missing keys: {missing_keys}")
                return False
        
        print_pass(f"All 24 points contain required keys: {required_keys}")
        
        # Show sample point
        print_info(f"Sample point (index 0): {json.dumps(points[0], indent=2)}")
        
        return True
        
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        return False

# Test 3: CSV Export Endpoint (Authenticated)
def test_csv_export_authenticated(cookies):
    print_test("3. GET /api/videos/admin/observability/incident-timeline.csv?lookback_days=7 -> 200")
    try:
        response = requests.get(
            f"{BASE_URL}/api/videos/admin/observability/incident-timeline.csv",
            params={"lookback_days": 7},
            cookies=cookies,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        # Show first 500 characters of response
        text = response.text
        if len(text) > 500:
            print(f"Body (truncated): {text[:500]}...")
        else:
            print(f"Body: {text}")
        
        if response.status_code != 200:
            print_fail(f"Expected 200, got {response.status_code}")
            return False
        
        print_pass("CSV endpoint returned 200")
        
        # Check content-type contains text/csv
        content_type = response.headers.get('content-type', '')
        if 'text/csv' not in content_type.lower():
            print_fail(f"Expected content-type to contain 'text/csv', got '{content_type}'")
            return False
        
        print_pass(f"Content-Type contains 'text/csv': {content_type}")
        
        # Check CSV header row
        lines = text.strip().split('\n')
        if not lines:
            print_fail("CSV response is empty")
            return False
        
        header = lines[0]
        print_info(f"CSV Header: {header}")
        
        # Check for required columns in header
        required_columns = ['hour_bucket', 'signal_type', 'severity']
        for col in required_columns:
            if col not in header:
                print_fail(f"CSV header missing required column: {col}")
                return False
        
        print_pass(f"CSV header contains required columns: {required_columns}")
        
        print_info(f"Total CSV rows (including header): {len(lines)}")
        
        return True
        
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        return False

# Test 4: CSV Export Endpoint (Unauthenticated)
def test_csv_export_unauthenticated():
    print_test("4. GET /api/videos/admin/observability/incident-timeline.csv (unauthenticated) -> 401")
    try:
        response = requests.get(
            f"{BASE_URL}/api/videos/admin/observability/incident-timeline.csv",
            params={"lookback_days": 7},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        try:
            print(f"Body: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Body: {response.text[:500]}")
        
        if response.status_code == 401:
            print_pass("CSV endpoint correctly returned 401 for unauthenticated request")
            return True
        else:
            print_fail(f"Expected 401, got {response.status_code}")
            return False
        
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        return False

def main():
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}FEATURE 21 P2 BACKEND TEST SUITE{Colors.END}")
    print(f"{Colors.BLUE}Base URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    
    results = {}
    
    # Test 1: Admin Login
    login_success, admin_cookies = test_admin_login()
    results['test_1_admin_login'] = login_success
    
    if not login_success:
        print_fail("Admin login failed. Skipping authenticated tests.")
        admin_cookies = None
    
    # Test 2: Admin Observability with incident_volume_trend_24h
    if admin_cookies:
        results['test_2_admin_observability'] = test_admin_observability(admin_cookies)
    else:
        results['test_2_admin_observability'] = False
    
    # Test 3: CSV Export (Authenticated)
    if admin_cookies:
        results['test_3_csv_export_authenticated'] = test_csv_export_authenticated(admin_cookies)
    else:
        results['test_3_csv_export_authenticated'] = False
    
    # Test 4: CSV Export (Unauthenticated)
    results['test_4_csv_export_unauthenticated'] = test_csv_export_unauthenticated()
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}TEST SUMMARY{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{test_name}: {status}")
    
    print(f"\n{Colors.BLUE}Total: {passed}/{total} tests passed{Colors.END}")
    
    # Pass/Fail Matrix
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}PASS/FAIL MATRIX{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    
    matrix = [
        ("POST /api/auth/login", results['test_1_admin_login']),
        ("GET /api/videos/admin/observability (incident_volume_trend_24h)", results['test_2_admin_observability']),
        ("GET /api/videos/admin/observability/incident-timeline.csv (auth)", results['test_3_csv_export_authenticated']),
        ("GET /api/videos/admin/observability/incident-timeline.csv (unauth)", results['test_4_csv_export_unauthenticated']),
    ]
    
    for test_name, result in matrix:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {test_name}: {status}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{'='*80}{Colors.END}")
        print(f"{Colors.GREEN}ALL TESTS PASSED ✓{Colors.END}")
        print(f"{Colors.GREEN}{'='*80}{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}{'='*80}{Colors.END}")
        print(f"{Colors.RED}SOME TESTS FAILED ✗{Colors.END}")
        print(f"{Colors.RED}{'='*80}{Colors.END}")
        return 1

if __name__ == "__main__":
    exit(main())
