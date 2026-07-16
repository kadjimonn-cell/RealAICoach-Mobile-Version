#!/usr/bin/env python3
"""
Feature 26 P1 Periodic Monitoring Cycle
Locked protocol: feature_number=26, feature_id=jobs-portal
Mode: monitoring-only (no pruning/deletion)
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

# Test results storage
results = {
    "test_timestamp": datetime.utcnow().isoformat() + "Z",
    "base_url": BASE_URL,
    "feature_number": 26,
    "feature_id": "jobs-portal",
    "mode": "monitoring-only",
    "tests": {},
    "summary": {}
}

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def login():
    """Login and get session"""
    print_section("STEP 1: Admin Login")
    
    url = f"{BASE_URL}/api/auth/login"
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    print(f"POST {url}")
    print(f"Credentials: {ADMIN_EMAIL}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login successful")
            results["tests"]["login"] = {
                "status": "PASS",
                "status_code": 200
            }
            return response.cookies
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            results["tests"]["login"] = {
                "status": "FAIL",
                "status_code": response.status_code,
                "error": response.text[:500]
            }
            return None
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        results["tests"]["login"] = {
            "status": "ERROR",
            "error": str(e)
        }
        return None

def test_health_lock_contract(cookies):
    """Test 1: /api/hiring/v2/health lock contract"""
    print_section("TEST 1: Health Lock Contract")
    
    url = f"{BASE_URL}/api/hiring/v2/health"
    
    print(f"GET {url}")
    
    try:
        response = requests.get(url, cookies=cookies, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check for lock contract fields
            has_feature_number = "feature_number" in data or "feature" in data
            has_feature_id = "feature_id" in data or "service" in data
            
            results["tests"]["health_lock_contract"] = {
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "response": data,
                "has_feature_number": has_feature_number,
                "has_feature_id": has_feature_id
            }
            
            print("✅ Health endpoint returned 200")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            results["tests"]["health_lock_contract"] = {
                "status": "FAIL",
                "status_code": response.status_code,
                "error": response.text[:500]
            }
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {str(e)}")
        results["tests"]["health_lock_contract"] = {
            "status": "ERROR",
            "error": str(e)
        }
        return False

def test_deprecation_telemetry(cookies):
    """Test 2: /api/hiring/v2/admin/deprecation-telemetry"""
    print_section("TEST 2: Deprecation Telemetry")
    
    url = f"{BASE_URL}/api/hiring/v2/admin/deprecation-telemetry"
    
    print(f"GET {url}")
    
    try:
        response = requests.get(url, cookies=cookies, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            results["tests"]["deprecation_telemetry"] = {
                "status": "PASS",
                "status_code": response.status_code,
                "response": data
            }
            
            print("✅ Deprecation telemetry returned 200")
            return True
        else:
            print(f"❌ Deprecation telemetry failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            results["tests"]["deprecation_telemetry"] = {
                "status": "FAIL",
                "status_code": response.status_code,
                "error": response.text[:500]
            }
            return False
    except Exception as e:
        print(f"❌ Deprecation telemetry error: {str(e)}")
        results["tests"]["deprecation_telemetry"] = {
            "status": "ERROR",
            "error": str(e)
        }
        return False

def test_legacy_retirement_readiness(cookies):
    """Test 3: /api/hiring/v2/admin/legacy-retirement-readiness"""
    print_section("TEST 3: Legacy Retirement Readiness")
    
    url = f"{BASE_URL}/api/hiring/v2/admin/legacy-retirement-readiness"
    
    print(f"GET {url}")
    
    try:
        response = requests.get(url, cookies=cookies, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            results["tests"]["legacy_retirement_readiness"] = {
                "status": "PASS",
                "status_code": response.status_code,
                "response": data
            }
            
            print("✅ Legacy retirement readiness returned 200")
            return True
        else:
            print(f"❌ Legacy retirement readiness failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            results["tests"]["legacy_retirement_readiness"] = {
                "status": "FAIL",
                "status_code": response.status_code,
                "error": response.text[:500]
            }
            return False
    except Exception as e:
        print(f"❌ Legacy retirement readiness error: {str(e)}")
        results["tests"]["legacy_retirement_readiness"] = {
            "status": "ERROR",
            "error": str(e)
        }
        return False

def test_legacy_removal_readiness(cookies):
    """Test 4: /api/hiring/v2/admin/legacy-removal-readiness (strict_zero, near_zero)"""
    print_section("TEST 4: Legacy Removal Readiness")
    
    # Test with strict_zero
    print("\n--- Testing with strict_zero mode ---")
    url_strict = f"{BASE_URL}/api/hiring/v2/admin/legacy-removal-readiness?mode=strict_zero"
    
    print(f"GET {url_strict}")
    
    try:
        response_strict = requests.get(url_strict, cookies=cookies, timeout=30)
        print(f"Status: {response_strict.status_code}")
        
        if response_strict.status_code == 200:
            data_strict = response_strict.json()
            print(f"Response (strict_zero): {json.dumps(data_strict, indent=2)}")
            
            results["tests"]["legacy_removal_readiness_strict_zero"] = {
                "status": "PASS",
                "status_code": response_strict.status_code,
                "mode": "strict_zero",
                "response": data_strict,
                "operational_near_zero_excluding_synthetic": data_strict.get("operational_near_zero_excluding_synthetic", {}),
                "gate_divergence_detected": data_strict.get("gate_divergence_detected", False),
            }
            
            print("✅ Legacy removal readiness (strict_zero) returned 200")
        else:
            print(f"❌ Legacy removal readiness (strict_zero) failed: {response_strict.status_code}")
            print(f"Response: {response_strict.text[:500]}")
            results["tests"]["legacy_removal_readiness_strict_zero"] = {
                "status": "FAIL",
                "status_code": response_strict.status_code,
                "mode": "strict_zero",
                "error": response_strict.text[:500]
            }
    except Exception as e:
        print(f"❌ Legacy removal readiness (strict_zero) error: {str(e)}")
        results["tests"]["legacy_removal_readiness_strict_zero"] = {
            "status": "ERROR",
            "mode": "strict_zero",
            "error": str(e)
        }
    
    # Test with near_zero
    print("\n--- Testing with near_zero mode ---")
    url_near = f"{BASE_URL}/api/hiring/v2/admin/legacy-removal-readiness?mode=near_zero"
    
    print(f"GET {url_near}")
    
    try:
        response_near = requests.get(url_near, cookies=cookies, timeout=30)
        print(f"Status: {response_near.status_code}")
        
        if response_near.status_code == 200:
            data_near = response_near.json()
            print(f"Response (near_zero): {json.dumps(data_near, indent=2)}")
            
            results["tests"]["legacy_removal_readiness_near_zero"] = {
                "status": "PASS",
                "status_code": response_near.status_code,
                "mode": "near_zero",
                "response": data_near,
                "operational_near_zero_excluding_synthetic": data_near.get("operational_near_zero_excluding_synthetic", {}),
                "gate_divergence_detected": data_near.get("gate_divergence_detected", False),
            }
            
            print("✅ Legacy removal readiness (near_zero) returned 200")
            return True
        else:
            print(f"❌ Legacy removal readiness (near_zero) failed: {response_near.status_code}")
            print(f"Response: {response_near.text[:500]}")
            results["tests"]["legacy_removal_readiness_near_zero"] = {
                "status": "FAIL",
                "status_code": response_near.status_code,
                "mode": "near_zero",
                "error": response_near.text[:500]
            }
            return False
    except Exception as e:
        print(f"❌ Legacy removal readiness (near_zero) error: {str(e)}")
        results["tests"]["legacy_removal_readiness_near_zero"] = {
            "status": "ERROR",
            "mode": "near_zero",
            "error": str(e)
        }
        return False

def generate_summary():
    """Generate summary report"""
    print_section("SUMMARY REPORT")
    
    # Count pass/fail
    total_tests = len(results["tests"])
    passed_tests = sum(1 for test in results["tests"].values() if test.get("status") == "PASS")
    failed_tests = sum(1 for test in results["tests"].values() if test.get("status") == "FAIL")
    error_tests = sum(1 for test in results["tests"].values() if test.get("status") == "ERROR")
    
    results["summary"] = {
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "errors": error_tests,
        "overall_status": "PASS" if failed_tests == 0 and error_tests == 0 else "FAIL"
    }
    
    # Extract key values for sustained_gate_met and ready_for_legacy_code_removal
    sustained_gate_met = None
    ready_for_legacy_code_removal = None
    operational_sustained = None
    operational_ready = None
    divergence_detected = False
    
    # Check legacy removal readiness responses
    if "legacy_removal_readiness_strict_zero" in results["tests"]:
        strict_data = results["tests"]["legacy_removal_readiness_strict_zero"].get("response", {})
        if isinstance(strict_data, dict):
            sustained_gate_met = strict_data.get("sustained_gate_met", strict_data.get("ready", None))
            ready_for_legacy_code_removal = strict_data.get("ready_for_legacy_code_removal", strict_data.get("ready", None))
            op = strict_data.get("operational_near_zero_excluding_synthetic", {}) if isinstance(strict_data.get("operational_near_zero_excluding_synthetic", {}), dict) else {}
            if op:
                operational_sustained = op.get("sustained_gate_met")
                operational_ready = op.get("ready_for_legacy_code_removal")
            divergence_detected = divergence_detected or bool(strict_data.get("gate_divergence_detected", False))
    
    if "legacy_removal_readiness_near_zero" in results["tests"]:
        near_data = results["tests"]["legacy_removal_readiness_near_zero"].get("response", {})
        if isinstance(near_data, dict):
            if sustained_gate_met is None:
                sustained_gate_met = near_data.get("sustained_gate_met", near_data.get("ready", None))
            if ready_for_legacy_code_removal is None:
                ready_for_legacy_code_removal = near_data.get("ready_for_legacy_code_removal", near_data.get("ready", None))
            op = near_data.get("operational_near_zero_excluding_synthetic", {}) if isinstance(near_data.get("operational_near_zero_excluding_synthetic", {}), dict) else {}
            if op and operational_sustained is None:
                operational_sustained = op.get("sustained_gate_met")
                operational_ready = op.get("ready_for_legacy_code_removal")
            divergence_detected = divergence_detected or bool(near_data.get("gate_divergence_detected", False))
    
    results["summary"]["sustained_gate_met"] = sustained_gate_met
    results["summary"]["ready_for_legacy_code_removal"] = ready_for_legacy_code_removal
    results["summary"]["operational_near_zero_excluding_synthetic_sustained_gate_met"] = operational_sustained
    results["summary"]["operational_near_zero_excluding_synthetic_ready_for_legacy_code_removal"] = operational_ready
    results["summary"]["gate_divergence_detected"] = divergence_detected
    
    # Determine hard pruning gate status
    if sustained_gate_met is True and ready_for_legacy_code_removal is True:
        hard_pruning_gate = "OPEN"
    else:
        hard_pruning_gate = "CONTINUE_MONITORING"
    
    results["summary"]["hard_pruning_gate"] = hard_pruning_gate
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Errors: {error_tests}")
    print(f"\nOverall Status: {results['summary']['overall_status']}")
    print("\n--- Key Metrics ---")
    print(f"sustained_gate_met: {sustained_gate_met}")
    print(f"ready_for_legacy_code_removal: {ready_for_legacy_code_removal}")
    print(f"operational_near_zero_excluding_synthetic_sustained_gate_met: {operational_sustained}")
    print(f"operational_near_zero_excluding_synthetic_ready_for_legacy_code_removal: {operational_ready}")
    print(f"gate_divergence_detected: {divergence_detected}")
    print(f"hard_pruning_gate: {hard_pruning_gate}")
    
    # Print test results
    print("\n--- Test Results ---")
    for test_name, test_data in results["tests"].items():
        status_icon = "✅" if test_data.get("status") == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {test_data.get('status')}")
    
    # Save results to file
    output_file = "/app/feature26_monitoring_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Full results saved to: {output_file}")

def main():
    """Main test execution"""
    print_section("Feature 26 P1 Periodic Monitoring Cycle")
    print(f"Base URL: {BASE_URL}")
    print("Feature: jobs-portal (Feature 26)")
    print("Mode: monitoring-only")
    print(f"Timestamp: {results['test_timestamp']}")
    
    # Step 1: Login
    cookies = login()
    if not cookies:
        print("\n❌ CRITICAL: Login failed. Cannot proceed with monitoring tests.")
        generate_summary()
        return
    
    # Step 2: Test health lock contract
    test_health_lock_contract(cookies)
    
    # Step 3: Test deprecation telemetry
    test_deprecation_telemetry(cookies)
    
    # Step 4: Test legacy retirement readiness
    test_legacy_retirement_readiness(cookies)
    
    # Step 5: Test legacy removal readiness (strict_zero and near_zero)
    test_legacy_removal_readiness(cookies)
    
    # Generate summary
    generate_summary()

if __name__ == "__main__":
    main()
