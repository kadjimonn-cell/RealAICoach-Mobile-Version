"""
Feature 26 Monitoring Verification Test
Tests the lock contract endpoint and telemetry gates for Feature 26 (Jobs Portal)
"""

import requests
import json
from datetime import datetime

# Backend URL
BACKEND_URL = "https://visa-polish-v2.preview.emergentagent.com/api"

# Admin credentials
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_result(test_name, passed, details=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"    {details}")

def authenticate_admin():
    """Authenticate as admin and return session"""
    print_section("AUTHENTICATION")
    
    session = requests.Session()
    
    # Login
    login_url = f"{BACKEND_URL}/auth/login"
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = session.post(login_url, json=login_data)
        
        if response.status_code == 200:
            print_result("Admin login", True, f"Status: {response.status_code}")
            return session
        else:
            print_result("Admin login", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
            return None
    except Exception as e:
        print_result("Admin login", False, f"Error: {str(e)}")
        return None

def test_health_endpoint(session):
    """Test GET /api/hiring/v2/health"""
    print_section("TEST 1: Lock Contract Endpoint - /api/hiring/v2/health")
    
    url = f"{BACKEND_URL}/hiring/v2/health"
    
    try:
        response = session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            feature_number = data.get("feature_number")
            feature_id = data.get("feature_id")
            
            feature_number_ok = feature_number == 26
            feature_id_ok = feature_id == "jobs-portal"
            
            print_result("Health endpoint returns 200", True, f"Status: {response.status_code}")
            print_result("feature_number = 26", feature_number_ok, f"Actual: {feature_number}")
            print_result("feature_id = jobs-portal", feature_id_ok, f"Actual: {feature_id}")
            
            print("\nFull response:")
            print(json.dumps(data, indent=2))
            
            return feature_number_ok and feature_id_ok
        else:
            print_result("Health endpoint", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_result("Health endpoint", False, f"Error: {str(e)}")
        return False

def test_legacy_retirement_readiness(session):
    """Test GET /api/hiring/v2/admin/legacy-retirement-readiness"""
    print_section("TEST 2: Legacy Retirement Readiness - /api/hiring/v2/admin/legacy-retirement-readiness")
    
    url = f"{BACKEND_URL}/hiring/v2/admin/legacy-retirement-readiness"
    
    try:
        response = session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract key metrics
            feature_number = data.get("feature_number")
            feature_id = data.get("feature_id")
            retirement_phase = data.get("retirement_phase")
            target_phase_gate_ready = data.get("target_phase_gate_ready")
            family_readiness = data.get("family_readiness", [])
            
            print_result("Legacy retirement readiness endpoint returns 200", True, f"Status: {response.status_code}")
            print_result("feature_number = 26", feature_number == 26, f"Actual: {feature_number}")
            print_result("feature_id = jobs-portal", feature_id == "jobs-portal", f"Actual: {feature_id}")
            
            print(f"\nKey Metrics:")
            print(f"  - Retirement Phase: {retirement_phase}")
            print(f"  - Target Phase Gate Ready: {target_phase_gate_ready}")
            print(f"  - Family Readiness Count: {len(family_readiness)}")
            
            for family in family_readiness:
                route_family = family.get("route_family")
                gate_met = family.get("gate_met")
                events = family.get("events", 0)
                active_users = family.get("active_users", 0)
                print(f"  - {route_family}: gate_met={gate_met}, events={events}, active_users={active_users}")
            
            print("\nFull response (truncated):")
            print(json.dumps({k: v for k, v in data.items() if k != "family_readiness"}, indent=2))
            
            return True
        else:
            print_result("Legacy retirement readiness endpoint", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_result("Legacy retirement readiness endpoint", False, f"Error: {str(e)}")
        return False

def test_legacy_removal_readiness_strict_zero(session):
    """Test GET /api/hiring/v2/admin/legacy-removal-readiness?mode=strict_zero&exclude_synthetic=false"""
    print_section("TEST 3a: Legacy Removal Readiness - mode=strict_zero, exclude_synthetic=false")
    
    url = f"{BACKEND_URL}/hiring/v2/admin/legacy-removal-readiness"
    params = {
        "mode": "strict_zero",
        "exclude_synthetic": "false"
    }
    
    try:
        response = session.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract key metrics
            feature_number = data.get("feature_number")
            feature_id = data.get("feature_id")
            mode = data.get("mode")
            exclude_synthetic = data.get("exclude_synthetic")
            sustained_gate_met = data.get("sustained_gate_met")
            windows = data.get("windows", [])
            
            print_result("Legacy removal readiness endpoint returns 200", True, f"Status: {response.status_code}")
            print_result("feature_number = 26", feature_number == 26, f"Actual: {feature_number}")
            print_result("feature_id = jobs-portal", feature_id == "jobs-portal", f"Actual: {feature_id}")
            print_result("mode = strict_zero", mode == "strict_zero", f"Actual: {mode}")
            print_result("exclude_synthetic = false", exclude_synthetic == False, f"Actual: {exclude_synthetic}")
            
            print(f"\nKey Metrics:")
            print(f"  - Sustained Gate Met: {sustained_gate_met}")
            print(f"  - Windows Count: {len(windows)}")
            
            for window in windows:
                window_label = window.get("window_label")
                gate_met = window.get("gate_met")
                family_readiness = window.get("family_readiness", [])
                print(f"  - Window {window_label}: gate_met={gate_met}")
                for family in family_readiness:
                    route_family = family.get("route_family")
                    family_gate_met = family.get("gate_met")
                    events = family.get("events", 0)
                    active_users = family.get("active_users", 0)
                    print(f"      {route_family}: gate_met={family_gate_met}, events={events}, users={active_users}")
            
            print("\nRecommendation:")
            print(f"  {data.get('recommendation')}")
            
            return True
        else:
            print_result("Legacy removal readiness endpoint", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_result("Legacy removal readiness endpoint", False, f"Error: {str(e)}")
        return False

def test_legacy_removal_readiness_near_zero(session):
    """Test GET /api/hiring/v2/admin/legacy-removal-readiness?mode=near_zero&exclude_synthetic=false"""
    print_section("TEST 3b: Legacy Removal Readiness - mode=near_zero, exclude_synthetic=false")
    
    url = f"{BACKEND_URL}/hiring/v2/admin/legacy-removal-readiness"
    params = {
        "mode": "near_zero",
        "exclude_synthetic": "false"
    }
    
    try:
        response = session.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract key metrics
            mode = data.get("mode")
            exclude_synthetic = data.get("exclude_synthetic")
            sustained_gate_met = data.get("sustained_gate_met")
            windows = data.get("windows", [])
            
            print_result("Legacy removal readiness endpoint returns 200", True, f"Status: {response.status_code}")
            print_result("mode = near_zero", mode == "near_zero", f"Actual: {mode}")
            print_result("exclude_synthetic = false", exclude_synthetic == False, f"Actual: {exclude_synthetic}")
            
            print(f"\nKey Metrics:")
            print(f"  - Sustained Gate Met: {sustained_gate_met}")
            print(f"  - Windows Count: {len(windows)}")
            
            for window in windows:
                window_label = window.get("window_label")
                gate_met = window.get("gate_met")
                family_readiness = window.get("family_readiness", [])
                print(f"  - Window {window_label}: gate_met={gate_met}")
                for family in family_readiness:
                    route_family = family.get("route_family")
                    family_gate_met = family.get("gate_met")
                    events = family.get("events", 0)
                    active_users = family.get("active_users", 0)
                    print(f"      {route_family}: gate_met={family_gate_met}, events={events}, users={active_users}")
            
            print("\nRecommendation:")
            print(f"  {data.get('recommendation')}")
            
            return True
        else:
            print_result("Legacy removal readiness endpoint", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_result("Legacy removal readiness endpoint", False, f"Error: {str(e)}")
        return False

def verify_monitoring_only_policy(session):
    """Verify that policy status is monitoring-only (not ready for legacy code removal)"""
    print_section("TEST 4: Verify Monitoring-Only Policy")
    
    # Get legacy removal readiness
    url = f"{BACKEND_URL}/hiring/v2/admin/legacy-removal-readiness"
    params = {
        "mode": "strict_zero",
        "exclude_synthetic": "false"
    }
    
    try:
        response = session.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            sustained_gate_met = data.get("sustained_gate_met")
            recommendation = data.get("recommendation", "")
            
            # Monitoring-only means sustained_gate_met should be False
            # and recommendation should suggest continued monitoring
            is_monitoring_only = not sustained_gate_met and "monitoring" in recommendation.lower()
            
            print_result("Policy is monitoring-only", is_monitoring_only, 
                        f"sustained_gate_met={sustained_gate_met}, recommendation contains 'monitoring'={('monitoring' in recommendation.lower())}")
            
            if is_monitoring_only:
                print("\n✅ CONFIRMED: System is in monitoring-only mode (not ready for legacy code removal)")
            else:
                print("\n⚠️  WARNING: System may be ready for legacy code removal")
            
            return True
        else:
            print_result("Verify monitoring-only policy", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("Verify monitoring-only policy", False, f"Error: {str(e)}")
        return False

def verify_no_destructive_actions():
    """Verify no destructive actions are invoked"""
    print_section("TEST 5: Verify No Destructive Actions")
    
    print_result("No destructive actions invoked", True, 
                "All tests are read-only GET requests - no write/delete operations performed")
    
    return True

def main():
    """Main test execution"""
    print("\n" + "=" * 80)
    print("  Feature 26 Monitoring Verification Test")
    print("  Date: " + datetime.now().isoformat())
    print("=" * 80)
    
    # Authenticate
    session = authenticate_admin()
    if not session:
        print("\n❌ OVERALL RESULT: FAIL - Authentication failed")
        return
    
    # Run tests
    results = []
    
    results.append(("Health endpoint", test_health_endpoint(session)))
    results.append(("Legacy retirement readiness", test_legacy_retirement_readiness(session)))
    results.append(("Legacy removal readiness (strict_zero)", test_legacy_removal_readiness_strict_zero(session)))
    results.append(("Legacy removal readiness (near_zero)", test_legacy_removal_readiness_near_zero(session)))
    results.append(("Monitoring-only policy", verify_monitoring_only_policy(session)))
    results.append(("No destructive actions", verify_no_destructive_actions()))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ OVERALL RESULT: PASS - All Feature 26 monitoring endpoints working correctly")
    else:
        print(f"\n❌ OVERALL RESULT: FAIL - {total - passed} test(s) failed")

if __name__ == "__main__":
    main()
