"""
Feature 26 Periodic Backend Monitoring Check
Locked Protocol: feature_number=26, feature_id=jobs-portal

This script validates:
1. /api/hiring/v2/health lock contract
2. /api/hiring/v2/admin/legacy-retirement-readiness?lookback_hours=72
3. /api/hiring/v2/admin/legacy-removal-readiness?mode=strict_zero&exclude_synthetic=false
4. /api/hiring/v2/admin/legacy-removal-readiness?mode=near_zero&exclude_synthetic=false
5. Sustained gate criteria status
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

# Expected lock contract values
EXPECTED_FEATURE_NUMBER = 26
EXPECTED_FEATURE_ID = "jobs-portal"


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_result(status: str, message: str, details: str = ""):
    """Print a test result"""
    symbols = {"PASS": "✅", "FAIL": "❌", "INFO": "ℹ️", "WARN": "⚠️"}
    symbol = symbols.get(status, "•")
    print(f"{symbol} {status}: {message}")
    if details:
        print(f"   {details}")


def login_admin() -> dict:
    """Login as admin and return session cookies"""
    url = f"{BASE_URL}/api/auth/login"
    payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            print_result("PASS", "Admin login successful")
            return {"cookies": response.cookies, "user": response.json()}
        else:
            print_result("FAIL", f"Admin login failed with status {response.status_code}")
            return {"cookies": None, "user": None}
    except Exception as e:
        print_result("FAIL", f"Admin login error: {str(e)}")
        return {"cookies": None, "user": None}


def test_health_lock_contract(cookies) -> bool:
    """Test 1: Verify /api/hiring/v2/health lock contract"""
    print_header("TEST 1: Health Lock Contract")
    
    url = f"{BASE_URL}/api/hiring/v2/health"
    
    try:
        response = requests.get(url, cookies=cookies, timeout=30)
        
        if response.status_code != 200:
            print_result("FAIL", f"Health endpoint returned {response.status_code}")
            return False
        
        data = response.json()
        
        # Verify lock contract fields
        checks = [
            ("ok", True),
            ("service", "hiring-v2"),
            ("version", "v2"),
            ("feature_id", EXPECTED_FEATURE_ID),
            ("feature_number", EXPECTED_FEATURE_NUMBER)
        ]
        
        all_pass = True
        for field, expected in checks:
            actual = data.get(field)
            if actual == expected:
                print_result("PASS", f"Field '{field}' = {actual}")
            else:
                print_result("FAIL", f"Field '{field}' mismatch", f"Expected: {expected}, Got: {actual}")
                all_pass = False
        
        return all_pass
    
    except Exception as e:
        print_result("FAIL", f"Health endpoint error: {str(e)}")
        return False


def test_legacy_retirement_readiness(cookies) -> dict:
    """Test 2: Verify /api/hiring/v2/admin/legacy-retirement-readiness?lookback_hours=72"""
    print_header("TEST 2: Legacy Retirement Readiness (72h lookback)")
    
    url = f"{BASE_URL}/api/hiring/v2/admin/legacy-retirement-readiness?lookback_hours=72"
    
    try:
        response = requests.get(url, cookies=cookies, timeout=30)
        
        if response.status_code != 200:
            print_result("FAIL", f"Endpoint returned {response.status_code}")
            return {"success": False}
        
        data = response.json()
        
        # Verify response structure
        print_result("PASS", "Endpoint returned 200 OK")
        
        # Check key fields
        feature_number = data.get("feature_number")
        feature_id = data.get("feature_id")
        lookback_hours = data.get("lookback_hours")
        retirement_phase = data.get("retirement_phase")
        target_phase_gate_ready = data.get("target_phase_gate_ready")
        
        print_result("INFO", f"Feature Number: {feature_number}")
        print_result("INFO", f"Feature ID: {feature_id}")
        print_result("INFO", f"Lookback Hours: {lookback_hours}")
        print_result("INFO", f"Retirement Phase: {retirement_phase}")
        print_result("INFO", f"Target Phase Gate Ready: {target_phase_gate_ready}")
        
        # Check family readiness
        family_readiness = data.get("family_readiness", [])
        for family in family_readiness:
            route_family = family.get("route_family")
            gate_met = family.get("gate_met")
            total_events = family.get("total_events", 0)
            print_result("INFO", f"Family '{route_family}': gate_met={gate_met}, events={total_events}")
        
        return {
            "success": True,
            "data": data,
            "target_phase_gate_ready": target_phase_gate_ready
        }
    
    except Exception as e:
        print_result("FAIL", f"Endpoint error: {str(e)}")
        return {"success": False}


def test_legacy_removal_readiness(cookies, mode: str, exclude_synthetic: bool) -> dict:
    """Test 3 & 4: Verify /api/hiring/v2/admin/legacy-removal-readiness"""
    print_header(f"TEST: Legacy Removal Readiness (mode={mode}, exclude_synthetic={exclude_synthetic})")
    
    url = f"{BASE_URL}/api/hiring/v2/admin/legacy-removal-readiness?mode={mode}&exclude_synthetic={str(exclude_synthetic).lower()}"
    
    try:
        response = requests.get(url, cookies=cookies, timeout=30)
        
        if response.status_code != 200:
            print_result("FAIL", f"Endpoint returned {response.status_code}")
            return {"success": False}
        
        data = response.json()
        
        # Verify response structure
        print_result("PASS", "Endpoint returned 200 OK")
        
        # Check key fields
        feature_number = data.get("feature_number")
        feature_id = data.get("feature_id")
        sustained_gate_met = data.get("sustained_gate_met")
        ready_for_removal = data.get("ready_for_legacy_code_removal")
        recommendation = data.get("recommendation", "")
        operational_signal = data.get("operational_near_zero_excluding_synthetic", {})
        divergence = data.get("gate_divergence_detected", False)
        
        print_result("INFO", f"Feature Number: {feature_number}")
        print_result("INFO", f"Feature ID: {feature_id}")
        print_result("INFO", f"Mode: {data.get('mode')}")
        print_result("INFO", f"Exclude Synthetic: {data.get('exclude_synthetic')}")
        print_result("INFO", f"Sustained Gate Met: {sustained_gate_met}")
        print_result("INFO", f"Ready for Removal: {ready_for_removal}")
        if isinstance(operational_signal, dict):
            print_result("INFO", f"Operational Near-Zero (exclude synthetic) Sustained: {operational_signal.get('sustained_gate_met')}")
            print_result("INFO", f"Operational Near-Zero Ready: {operational_signal.get('ready_for_legacy_code_removal')}")
        print_result("INFO", f"Gate Divergence Detected: {divergence}")
        
        # Check windows
        windows = data.get("windows", [])
        failing_windows = data.get("failing_windows", [])
        
        print_result("INFO", f"Total Windows: {len(windows)}")
        print_result("INFO", f"Failing Windows: {len(failing_windows)}")
        
        for window in windows:
            label = window.get("window_label")
            gate_met = window.get("gate_met")
            status_symbol = "✅" if gate_met else "❌"
            print_result("INFO", f"  Window {label}: {status_symbol} gate_met={gate_met}")
            
            # Show family details
            for family in window.get("family_readiness", []):
                route_family = family.get("route_family")
                family_gate = family.get("gate_met")
                events = family.get("total_events", 0)
                users = family.get("active_users", 0)
                print_result("INFO", f"    {route_family}: gate={family_gate}, events={events}, users={users}")
        
        print_result("INFO", f"Recommendation: {recommendation}")
        
        return {
            "success": True,
            "data": data,
            "sustained_gate_met": sustained_gate_met,
            "ready_for_removal": ready_for_removal,
            "failing_windows_count": len(failing_windows),
            "operational_near_zero_excluding_synthetic": operational_signal,
            "gate_divergence_detected": divergence,
        }
    
    except Exception as e:
        print_result("FAIL", f"Endpoint error: {str(e)}")
        return {"success": False}


def determine_gate_status(results: dict) -> str:
    """Determine if sustained gate criteria are met"""
    print_header("GATE STATUS DETERMINATION")
    
    # Check if all tests passed
    if not all(r.get("success", False) for r in results.values()):
        print_result("FAIL", "Not all monitoring endpoints are operational")
        return "FAIL - Endpoints not operational"
    
    # Check sustained gate status from both modes
    strict_zero_result = results.get("strict_zero", {})
    near_zero_result = results.get("near_zero", {})
    
    strict_sustained = strict_zero_result.get("sustained_gate_met", False)
    near_sustained = near_zero_result.get("sustained_gate_met", False)
    strict_operational = (strict_zero_result.get("operational_near_zero_excluding_synthetic") or {}).get("sustained_gate_met", False)
    near_operational = (near_zero_result.get("operational_near_zero_excluding_synthetic") or {}).get("sustained_gate_met", False)
    
    print_result("INFO", f"Strict Zero Mode - Sustained Gate Met: {strict_sustained}")
    print_result("INFO", f"Near Zero Mode - Sustained Gate Met: {near_sustained}")
    print_result("INFO", f"Operational Signal via Strict Endpoint: {strict_operational}")
    print_result("INFO", f"Operational Signal via Near Endpoint: {near_operational}")
    
    if strict_sustained and near_sustained:
        print_result("PASS", "Sustained gate criteria MET in both modes")
        return "PASS - Gate criteria MET"
    else:
        print_result("INFO", "Sustained gate criteria NOT MET - Continue monitoring")
        return "CONTINUE MONITORING"


def main():
    """Main test execution"""
    print_header("FEATURE 26 PERIODIC BACKEND MONITORING CHECK")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"Locked Protocol: feature_number={EXPECTED_FEATURE_NUMBER}, feature_id={EXPECTED_FEATURE_ID}")
    
    # Login
    print_header("AUTHENTICATION")
    session = login_admin()
    
    if not session["cookies"]:
        print_result("FAIL", "Cannot proceed without admin authentication")
        return 1
    
    cookies = session["cookies"]
    
    # Run tests
    results = {}
    
    # Test 1: Health lock contract
    health_pass = test_health_lock_contract(cookies)
    results["health"] = {"success": health_pass}
    
    # Test 2: Legacy retirement readiness
    retirement_result = test_legacy_retirement_readiness(cookies)
    results["retirement"] = retirement_result
    
    # Test 3: Legacy removal readiness (strict_zero)
    strict_result = test_legacy_removal_readiness(cookies, "strict_zero", False)
    results["strict_zero"] = strict_result
    
    # Test 4: Legacy removal readiness (near_zero)
    near_result = test_legacy_removal_readiness(cookies, "near_zero", False)
    results["near_zero"] = near_result
    
    # Determine gate status
    gate_status = determine_gate_status(results)
    
    # Final summary
    print_header("FINAL SUMMARY")
    
    test_results = [
        ("Health Lock Contract", results["health"]["success"]),
        ("Legacy Retirement Readiness", results["retirement"]["success"]),
        ("Legacy Removal Readiness (strict_zero)", results["strict_zero"]["success"]),
        ("Legacy Removal Readiness (near_zero)", results["near_zero"]["success"])
    ]
    
    all_pass = all(result for _, result in test_results)
    
    for test_name, passed in test_results:
        status = "PASS" if passed else "FAIL"
        print_result(status, test_name)
    
    print("\n" + "-" * 80)
    print(f"Gate Status: {gate_status}")
    print("-" * 80)
    
    if all_pass:
        print_result("PASS", "All monitoring endpoints operational")
        return 0
    else:
        print_result("FAIL", "Some monitoring endpoints failed")
        return 1


if __name__ == "__main__":
    exit(main())
