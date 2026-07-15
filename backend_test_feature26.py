#!/usr/bin/env python3
"""
Feature 26 (Jobs Portal) Backend Verification - Latest Cycle
Test Date: 2026-06-18
Objective: Independent backend verification for Feature 26 locked protocol
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

# Test results storage
test_results = {
    "test_date": "2026-06-18",
    "feature": "Feature 26 (Jobs Portal)",
    "base_url": BASE_URL,
    "tests": []
}

def log_test(name: str, status: str, details: Dict[str, Any]):
    """Log test result"""
    test_results["tests"].append({
        "name": name,
        "status": status,
        "details": details
    })
    status_icon = "✅" if status == "PASS" else "❌"
    print(f"{status_icon} {name}: {status}")
    if details.get("error"):
        print(f"   Error: {details['error']}")

def admin_login() -> requests.Session:
    """Login as admin and return session"""
    session = requests.Session()
    
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            headers={
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            }
        )
        
        if response.status_code == 200:
            log_test(
                "Admin Login",
                "PASS",
                {
                    "status_code": response.status_code,
                    "email": ADMIN_EMAIL
                }
            )
            return session
        else:
            log_test(
                "Admin Login",
                "FAIL",
                {
                    "status_code": response.status_code,
                    "error": f"Login failed with status {response.status_code}",
                    "response": response.text[:200]
                }
            )
            return None
    except Exception as e:
        log_test(
            "Admin Login",
            "FAIL",
            {
                "error": str(e)
            }
        )
        return None

def test_health_endpoint(session: requests.Session):
    """Test /api/hiring/v2/health lock contract"""
    try:
        response = session.get(
            f"{BASE_URL}/api/hiring/v2/health",
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            feature_number = data.get("feature_number")
            feature_id = data.get("feature_id")
            
            if feature_number == 26 and feature_id == "jobs-portal":
                log_test(
                    "Health Endpoint Lock Contract",
                    "PASS",
                    {
                        "status_code": response.status_code,
                        "feature_number": feature_number,
                        "feature_id": feature_id,
                        "service": data.get("service"),
                        "version": data.get("version")
                    }
                )
            else:
                log_test(
                    "Health Endpoint Lock Contract",
                    "FAIL",
                    {
                        "status_code": response.status_code,
                        "error": f"Expected feature_number=26 and feature_id=jobs-portal, got {feature_number} and {feature_id}",
                        "response": data
                    }
                )
        else:
            log_test(
                "Health Endpoint Lock Contract",
                "FAIL",
                {
                    "status_code": response.status_code,
                    "error": f"Expected 200, got {response.status_code}",
                    "response": response.text[:200]
                }
            )
    except Exception as e:
        log_test(
            "Health Endpoint Lock Contract",
            "FAIL",
            {
                "error": str(e)
            }
        )

def test_legacy_retirement_readiness(session: requests.Session):
    """Test /api/hiring/v2/admin/legacy-retirement-readiness?lookback_hours=72"""
    try:
        response = session.get(
            f"{BASE_URL}/api/hiring/v2/admin/legacy-retirement-readiness?lookback_hours=72",
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for retirement phase
            retirement_phase = data.get("retirement_phase")
            
            log_test(
                "Legacy Retirement Readiness (lookback_hours=72)",
                "PASS",
                {
                    "status_code": response.status_code,
                    "retirement_phase": retirement_phase,
                    "generated_at": data.get("generated_at"),
                    "lookback_hours": data.get("lookback_hours")
                }
            )
        else:
            log_test(
                "Legacy Retirement Readiness (lookback_hours=72)",
                "FAIL",
                {
                    "status_code": response.status_code,
                    "error": f"Expected 200, got {response.status_code}",
                    "response": response.text[:200]
                }
            )
    except Exception as e:
        log_test(
            "Legacy Retirement Readiness (lookback_hours=72)",
            "FAIL",
            {
                "error": str(e)
            }
        )

def test_legacy_removal_readiness_strict_zero(session: requests.Session):
    """Test /api/hiring/v2/admin/legacy-removal-readiness?mode=strict_zero&exclude_synthetic=false"""
    try:
        response = session.get(
            f"{BASE_URL}/api/hiring/v2/admin/legacy-removal-readiness?mode=strict_zero&exclude_synthetic=false",
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for sustained gate
            sustained_gate_met = data.get("sustained_gate_met")
            
            log_test(
                "Legacy Removal Readiness (strict_zero, exclude_synthetic=false)",
                "PASS",
                {
                    "status_code": response.status_code,
                    "sustained_gate_met": sustained_gate_met,
                    "ready_for_legacy_code_removal": data.get("ready_for_legacy_code_removal"),
                    "mode": data.get("mode"),
                    "exclude_synthetic": data.get("exclude_synthetic")
                }
            )
        else:
            log_test(
                "Legacy Removal Readiness (strict_zero, exclude_synthetic=false)",
                "FAIL",
                {
                    "status_code": response.status_code,
                    "error": f"Expected 200, got {response.status_code}",
                    "response": response.text[:200]
                }
            )
    except Exception as e:
        log_test(
            "Legacy Removal Readiness (strict_zero, exclude_synthetic=false)",
            "FAIL",
            {
                "error": str(e)
            }
        )

def test_legacy_removal_readiness_near_zero(session: requests.Session):
    """Test /api/hiring/v2/admin/legacy-removal-readiness?mode=near_zero&exclude_synthetic=false"""
    try:
        response = session.get(
            f"{BASE_URL}/api/hiring/v2/admin/legacy-removal-readiness?mode=near_zero&exclude_synthetic=false",
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for operational near zero excluding synthetic
            operational_near_zero = data.get("operational_near_zero_excluding_synthetic", {})
            operational_sustained_gate = operational_near_zero.get("sustained_gate_met")
            gate_divergence_detected = data.get("gate_divergence_detected")
            
            log_test(
                "Legacy Removal Readiness (near_zero, exclude_synthetic=false)",
                "PASS",
                {
                    "status_code": response.status_code,
                    "sustained_gate_met": data.get("sustained_gate_met"),
                    "operational_near_zero_excluding_synthetic.sustained_gate_met": operational_sustained_gate,
                    "gate_divergence_detected": gate_divergence_detected,
                    "mode": data.get("mode"),
                    "exclude_synthetic": data.get("exclude_synthetic")
                }
            )
        else:
            log_test(
                "Legacy Removal Readiness (near_zero, exclude_synthetic=false)",
                "FAIL",
                {
                    "status_code": response.status_code,
                    "error": f"Expected 200, got {response.status_code}",
                    "response": response.text[:200]
                }
            )
    except Exception as e:
        log_test(
            "Legacy Removal Readiness (near_zero, exclude_synthetic=false)",
            "FAIL",
            {
                "error": str(e)
            }
        )

def main():
    """Run all tests"""
    print("=" * 80)
    print("Feature 26 (Jobs Portal) Backend Verification - Latest Cycle")
    print("=" * 80)
    print()
    
    # Login as admin
    session = admin_login()
    if not session:
        print("\n❌ FAILED: Admin login failed, cannot proceed with tests")
        return
    
    print()
    
    # Run tests
    test_health_endpoint(session)
    test_legacy_retirement_readiness(session)
    test_legacy_removal_readiness_strict_zero(session)
    test_legacy_removal_readiness_near_zero(session)
    
    # Summary
    print()
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    passed = sum(1 for t in test_results["tests"] if t["status"] == "PASS")
    failed = sum(1 for t in test_results["tests"] if t["status"] == "FAIL")
    total = len(test_results["tests"])
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    # Expected values check
    print("=" * 80)
    print("Expected Values Verification")
    print("=" * 80)
    
    # Find specific test results
    health_test = next((t for t in test_results["tests"] if "Health Endpoint" in t["name"]), None)
    retirement_test = next((t for t in test_results["tests"] if "Retirement Readiness" in t["name"]), None)
    strict_zero_test = next((t for t in test_results["tests"] if "strict_zero" in t["name"]), None)
    near_zero_test = next((t for t in test_results["tests"] if "near_zero" in t["name"]), None)
    
    if health_test and health_test["status"] == "PASS":
        details = health_test["details"]
        print(f"✅ health 200 with feature_number={details.get('feature_number')} feature_id={details.get('feature_id')}")
    else:
        print("❌ health endpoint check failed")
    
    if retirement_test and retirement_test["status"] == "PASS":
        details = retirement_test["details"]
        print(f"✅ retirement phase: {details.get('retirement_phase')}")
    else:
        print("❌ retirement readiness check failed")
    
    if strict_zero_test and strict_zero_test["status"] == "PASS":
        details = strict_zero_test["details"]
        print(f"✅ strict_zero sustained_gate_met: {details.get('sustained_gate_met')}")
    else:
        print("❌ strict_zero check failed")
    
    if near_zero_test and near_zero_test["status"] == "PASS":
        details = near_zero_test["details"]
        print(f"✅ near_zero sustained_gate_met: {details.get('sustained_gate_met')}")
        print(f"✅ operational_near_zero_excluding_synthetic.sustained_gate_met: {details.get('operational_near_zero_excluding_synthetic.sustained_gate_met')}")
        print(f"✅ gate_divergence_detected: {details.get('gate_divergence_detected')}")
    else:
        print("❌ near_zero check failed")
    
    print()
    
    # Final verdict
    if failed == 0:
        print("=" * 80)
        print("✅ PASS - All Feature 26 backend tests passed")
        print("=" * 80)
    else:
        print("=" * 80)
        print("❌ FAIL - Some Feature 26 backend tests failed")
        print("=" * 80)
    
    # Save results to file
    with open("/app/feature26_backend_test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    print()
    print(f"Detailed results saved to: /app/feature26_backend_test_results.json")

if __name__ == "__main__":
    main()
