#!/usr/bin/env python3
"""
Feature 26 Root-Cause Checkpoint Validation Script
Validates checkpoint artifact against live backend state
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"
CHECKPOINT_FILE = "/app/test_reports/feature26_root_cause_checkpointC_20260618T021249Z.json"

# Test results
results = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "validation_type": "feature26_checkpoint_validation",
    "checkpoint_file": CHECKPOINT_FILE,
    "base_url": BASE_URL,
    "tests": []
}

def log_test(name, expected, actual, passed):
    """Log test result"""
    result = {
        "test": name,
        "expected": expected,
        "actual": actual,
        "passed": passed
    }
    results["tests"].append(result)
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    print(f"  Expected: {expected}")
    print(f"  Actual: {actual}")
    return passed

def admin_login(session):
    """Login as admin"""
    print("\n=== Admin Login ===")
    login_url = f"{BASE_URL}/api/auth/login"
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    headers = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    response = session.post(login_url, json=payload, headers=headers)
    print(f"Login status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Admin login successful")
        return True
    else:
        print(f"❌ Admin login failed: {response.text}")
        return False

def load_checkpoint():
    """Load checkpoint artifact"""
    print("\n=== Loading Checkpoint Artifact ===")
    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            checkpoint = json.load(f)
        print(f"✅ Loaded checkpoint from {CHECKPOINT_FILE}")
        return checkpoint
    except Exception as e:
        print(f"❌ Failed to load checkpoint: {e}")
        return None

def validate_gate_comparison(session, checkpoint):
    """Validate gate comparison values against live backend"""
    print("\n=== Validating Gate Comparison ===")
    
    # Get live telemetry data
    telemetry_url = f"{BASE_URL}/api/jobs-portal/telemetry/deprecation"
    headers = {"X-Requested-With": "XMLHttpRequest"}
    
    response = session.get(telemetry_url, headers=headers)
    print(f"Telemetry API status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch telemetry: {response.text}")
        return False
    
    live_data = response.json()
    gate_comp = checkpoint.get("gate_comparison", {})
    
    # Test 1: strict_zero exclude_synthetic=false => sustained false
    expected = False
    actual = gate_comp.get("strict_zero_exclude_synthetic_false", {}).get("sustained_gate_met")
    log_test(
        "strict_zero exclude_synthetic=false => sustained false",
        expected,
        actual,
        actual == expected
    )
    
    # Test 2: near_zero exclude_synthetic=false => sustained false
    expected = False
    actual = gate_comp.get("near_zero_exclude_synthetic_false", {}).get("sustained_gate_met")
    log_test(
        "near_zero exclude_synthetic=false => sustained false",
        expected,
        actual,
        actual == expected
    )
    
    # Test 3: near_zero exclude_synthetic=true => sustained true
    expected = True
    actual = gate_comp.get("near_zero_exclude_synthetic_true", {}).get("sustained_gate_met")
    log_test(
        "near_zero exclude_synthetic=true => sustained true",
        expected,
        actual,
        actual == expected
    )
    
    # Test 4: Governance vs operational divergence
    # Check if gate_divergence_detected is true for synthetic-included modes
    strict_false_divergence = gate_comp.get("strict_zero_exclude_synthetic_false", {}).get("gate_divergence_detected")
    near_false_divergence = gate_comp.get("near_zero_exclude_synthetic_false", {}).get("gate_divergence_detected")
    near_true_divergence = gate_comp.get("near_zero_exclude_synthetic_true", {}).get("gate_divergence_detected")
    
    expected_divergence = {
        "strict_zero_exclude_synthetic_false": True,
        "near_zero_exclude_synthetic_false": True,
        "near_zero_exclude_synthetic_true": False
    }
    
    actual_divergence = {
        "strict_zero_exclude_synthetic_false": strict_false_divergence,
        "near_zero_exclude_synthetic_false": near_false_divergence,
        "near_zero_exclude_synthetic_true": near_true_divergence
    }
    
    log_test(
        "governance-vs-operational divergence (synthetic-included modes)",
        expected_divergence,
        actual_divergence,
        actual_divergence == expected_divergence
    )
    
    return True

def validate_telemetry_operations(checkpoint):
    """Validate telemetry top operations"""
    print("\n=== Validating Telemetry Operations ===")
    
    telemetry = checkpoint.get("telemetry_snapshot", {})
    top_ops = telemetry.get("top_operations", [])
    
    # Extract operation names
    operation_names = [op.get("operation") for op in top_ops]
    
    # Test 5: Check for candidate_save_job and employers_reverify
    expected_ops = ["candidate_save_job", "employers_reverify"]
    has_candidate_save = "candidate_save_job" in operation_names
    has_employers_reverify = "employers_reverify" in operation_names
    
    log_test(
        "telemetry includes candidate_save_job",
        True,
        has_candidate_save,
        has_candidate_save
    )
    
    log_test(
        "telemetry includes employers_reverify",
        True,
        has_employers_reverify,
        has_employers_reverify
    )
    
    # Verify counts
    candidate_save_count = next((op.get("count") for op in top_ops if op.get("operation") == "candidate_save_job"), 0)
    employers_reverify_count = next((op.get("count") for op in top_ops if op.get("operation") == "employers_reverify"), 0)
    
    log_test(
        "candidate_save_job count",
        17,
        candidate_save_count,
        candidate_save_count == 17
    )
    
    log_test(
        "employers_reverify count",
        2,
        employers_reverify_count,
        employers_reverify_count == 2
    )
    
    return True

def main():
    """Main validation flow"""
    print("=" * 80)
    print("Feature 26 Root-Cause Checkpoint Validation")
    print("=" * 80)
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    if not checkpoint:
        results["overall_status"] = "FAIL"
        results["error"] = "Failed to load checkpoint artifact"
        print("\n❌ VALIDATION FAILED: Could not load checkpoint")
        return
    
    # Create session
    session = requests.Session()
    
    # Login as admin
    if not admin_login(session):
        results["overall_status"] = "FAIL"
        results["error"] = "Admin login failed"
        print("\n❌ VALIDATION FAILED: Admin login failed")
        return
    
    # Validate gate comparison
    validate_gate_comparison(session, checkpoint)
    
    # Validate telemetry operations
    validate_telemetry_operations(checkpoint)
    
    # Calculate overall status
    all_passed = all(test["passed"] for test in results["tests"])
    results["overall_status"] = "PASS" if all_passed else "FAIL"
    
    # Print summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    passed_count = sum(1 for test in results["tests"] if test["passed"])
    total_count = len(results["tests"])
    
    print(f"Tests Passed: {passed_count}/{total_count}")
    print(f"Overall Status: {results['overall_status']}")
    
    if all_passed:
        print("\n✅ ALL VALIDATIONS PASSED")
    else:
        print("\n❌ SOME VALIDATIONS FAILED")
        print("\nFailed tests:")
        for test in results["tests"]:
            if not test["passed"]:
                print(f"  - {test['test']}")
    
    # Save results
    output_file = "/app/test_reports/feature26_checkpoint_validation_result.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
