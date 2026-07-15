"""Feature 31 ACL Validation - Locked Protocol Evidence
Test ACL for AI Solver endpoints across free/basic/admin tiers.

Requirements:
1) /api/ai-solver/bootstrap (free/basic/admin) => 200
2) /api/ai-problem-solver/bootstrap (free/basic/admin) => 200
3) admin_control_plane should be null/absent for free/basic, present for admin
4) /api/ai-problem-solver/admin/control-plane => free/basic 403, admin 200
5) /api/ai-solver/insights/weekly and /api/ai-solver/playbooks => 200 for all tiers
"""

import requests
import json
from typing import Dict, Any, Optional, List, Tuple

# Base URL
BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"

# Test credentials
CREDENTIALS = {
    "free": {"email": "p1.free.1779113329@example.com", "password": "P1Free#2026!Aa"},
    "basic": {"email": "f21.basic.1781338672@example.com", "password": "F21Basic#2026Aa"},
    "admin": {"email": "admin@realaicoach.app", "password": "NewAdminPass2026!"}
}

# Test results storage
results = []


def create_session(role: str) -> Optional[requests.Session]:
    """Create authenticated session for a user role."""
    creds = CREDENTIALS[role]
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    })
    
    try:
        resp = session.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=10)
        if resp.status_code == 200:
            print(f"✅ Login successful for {role} user ({creds['email']})")
            return session
        else:
            print(f"❌ Login failed for {role} user: {resp.status_code} - {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Login exception for {role} user: {e}")
        return None


def test_endpoint(session: requests.Session, role: str, endpoint: str, expected_status: int) -> Tuple[bool, int, Any]:
    """Test an endpoint and return (success, status_code, response_data)."""
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = session.get(url, timeout=10)
        status = resp.status_code
        
        # Parse response data if JSON
        data = None
        try:
            data = resp.json()
        except:
            data = resp.text[:200]
        
        success = (status == expected_status)
        return success, status, data
    except Exception as e:
        print(f"❌ Exception testing {endpoint} for {role}: {e}")
        return False, 0, str(e)


def validate_admin_control_plane(role: str, data: Any) -> Tuple[bool, str]:
    """Validate admin_control_plane field in bootstrap response."""
    if not isinstance(data, dict):
        return False, "Response is not a dict"
    
    has_field = "admin_control_plane" in data
    field_value = data.get("admin_control_plane")
    
    if role in ["free", "basic"]:
        # Should be null or absent
        if not has_field or field_value is None:
            return True, "null/absent (correct)"
        else:
            return False, f"present with value (incorrect): {field_value}"
    elif role == "admin":
        # Should be present
        if has_field and field_value is not None:
            return True, f"present (correct)"
        else:
            return False, "null/absent (incorrect)"
    
    return False, "Unknown role"


def run_acl_tests():
    """Run all ACL validation tests."""
    print("="*100)
    print("FEATURE 31 ACL VALIDATION - LOCKED PROTOCOL EVIDENCE")
    print("="*100)
    print(f"Base URL: {BASE_URL}")
    print()
    
    # Create sessions for all roles
    sessions = {}
    for role in ["free", "basic", "admin"]:
        sessions[role] = create_session(role)
        if not sessions[role]:
            print(f"⚠️  WARNING: Could not create session for {role} user")
    
    print()
    print("="*100)
    print("TEST RESULTS")
    print("="*100)
    print()
    
    # Test 1: /api/ai-solver/bootstrap (all roles => 200)
    print("1) Testing /api/ai-solver/bootstrap")
    print("-" * 100)
    for role in ["free", "basic", "admin"]:
        if sessions[role]:
            success, status, data = test_endpoint(sessions[role], role, "/api/ai-solver/bootstrap", 200)
            
            # Validate admin_control_plane field
            acp_valid, acp_msg = validate_admin_control_plane(role, data)
            
            result = {
                "test": "ai-solver/bootstrap",
                "role": role,
                "expected_status": 200,
                "actual_status": status,
                "status_match": success,
                "admin_control_plane": acp_msg,
                "acp_valid": acp_valid
            }
            results.append(result)
            
            status_icon = "✅" if success else "❌"
            acp_icon = "✅" if acp_valid else "❌"
            print(f"  {status_icon} {role:6s} | Status: {status} (expected 200) | admin_control_plane: {acp_icon} {acp_msg}")
    print()
    
    # Test 2: /api/ai-problem-solver/bootstrap (all roles => 200)
    print("2) Testing /api/ai-problem-solver/bootstrap")
    print("-" * 100)
    for role in ["free", "basic", "admin"]:
        if sessions[role]:
            success, status, data = test_endpoint(sessions[role], role, "/api/ai-problem-solver/bootstrap", 200)
            
            # Validate admin_control_plane field
            acp_valid, acp_msg = validate_admin_control_plane(role, data)
            
            result = {
                "test": "ai-problem-solver/bootstrap",
                "role": role,
                "expected_status": 200,
                "actual_status": status,
                "status_match": success,
                "admin_control_plane": acp_msg,
                "acp_valid": acp_valid
            }
            results.append(result)
            
            status_icon = "✅" if success else "❌"
            acp_icon = "✅" if acp_valid else "❌"
            print(f"  {status_icon} {role:6s} | Status: {status} (expected 200) | admin_control_plane: {acp_icon} {acp_msg}")
    print()
    
    # Test 3: /api/ai-problem-solver/admin/control-plane (free/basic => 403, admin => 200)
    print("3) Testing /api/ai-problem-solver/admin/control-plane")
    print("-" * 100)
    for role in ["free", "basic", "admin"]:
        if sessions[role]:
            expected = 403 if role in ["free", "basic"] else 200
            success, status, data = test_endpoint(sessions[role], role, "/api/ai-problem-solver/admin/control-plane", expected)
            
            result = {
                "test": "admin/control-plane",
                "role": role,
                "expected_status": expected,
                "actual_status": status,
                "status_match": success
            }
            results.append(result)
            
            icon = "✅" if success else "❌"
            print(f"  {icon} {role:6s} | Status: {status} (expected {expected})")
    print()
    
    # Test 4: /api/ai-solver/insights/weekly (all roles => 200)
    print("4) Testing /api/ai-solver/insights/weekly")
    print("-" * 100)
    for role in ["free", "basic", "admin"]:
        if sessions[role]:
            success, status, data = test_endpoint(sessions[role], role, "/api/ai-solver/insights/weekly", 200)
            
            result = {
                "test": "insights/weekly",
                "role": role,
                "expected_status": 200,
                "actual_status": status,
                "status_match": success
            }
            results.append(result)
            
            icon = "✅" if success else "❌"
            print(f"  {icon} {role:6s} | Status: {status} (expected 200)")
    print()
    
    # Test 5: /api/ai-solver/playbooks (all roles => 200)
    print("5) Testing /api/ai-solver/playbooks")
    print("-" * 100)
    for role in ["free", "basic", "admin"]:
        if sessions[role]:
            success, status, data = test_endpoint(sessions[role], role, "/api/ai-solver/playbooks", 200)
            
            result = {
                "test": "playbooks",
                "role": role,
                "expected_status": 200,
                "actual_status": status,
                "status_match": success
            }
            results.append(result)
            
            icon = "✅" if success else "❌"
            print(f"  {icon} {role:6s} | Status: {status} (expected 200)")
    print()


def print_summary_table():
    """Print summary table of all test results."""
    print("="*100)
    print("SUMMARY TABLE - FEATURE 31 ACL VALIDATION")
    print("="*100)
    print()
    
    # Group results by endpoint
    endpoints = {}
    for result in results:
        test = result["test"]
        if test not in endpoints:
            endpoints[test] = []
        endpoints[test].append(result)
    
    # Print table header
    print(f"{'Endpoint':<40} | {'Role':<6} | {'Expected':<8} | {'Actual':<8} | {'Status':<6} | {'admin_control_plane':<30}")
    print("-" * 130)
    
    # Print results
    for endpoint, endpoint_results in endpoints.items():
        for i, result in enumerate(endpoint_results):
            endpoint_name = endpoint if i == 0 else ""
            role = result["role"]
            expected = result["expected_status"]
            actual = result["actual_status"]
            status = "✅ PASS" if result["status_match"] else "❌ FAIL"
            
            # admin_control_plane column
            acp = ""
            if "admin_control_plane" in result:
                acp_valid = result.get("acp_valid", False)
                acp_icon = "✅" if acp_valid else "❌"
                acp = f"{acp_icon} {result['admin_control_plane']}"
            
            print(f"{endpoint_name:<40} | {role:<6} | {expected:<8} | {actual:<8} | {status:<6} | {acp:<30}")
    
    print()
    
    # Calculate pass/fail counts
    total = len(results)
    passed = sum(1 for r in results if r["status_match"])
    failed = total - passed
    
    # For admin_control_plane validation
    acp_tests = [r for r in results if "acp_valid" in r]
    acp_passed = sum(1 for r in acp_tests if r["acp_valid"])
    acp_failed = len(acp_tests) - acp_passed
    
    print("="*100)
    print("FINAL RESULTS")
    print("="*100)
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print()
    print(f"admin_control_plane Validation:")
    print(f"  Total: {len(acp_tests)}")
    print(f"  ✅ Passed: {acp_passed}")
    print(f"  ❌ Failed: {acp_failed}")
    print()
    
    if failed == 0 and acp_failed == 0:
        print("🎉 ALL TESTS PASSED - Feature 31 ACL validation complete!")
    else:
        print("⚠️  SOME TESTS FAILED - Review results above")
    
    print("="*100)


def main():
    """Main entry point."""
    run_acl_tests()
    print_summary_table()


if __name__ == "__main__":
    main()
