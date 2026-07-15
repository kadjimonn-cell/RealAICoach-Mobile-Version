#!/usr/bin/env python3
"""
Feature 26 Root-Cause Checkpoint Validation Script V2
Validates checkpoint artifact values directly from the JSON file
"""

import json
from datetime import datetime

# Configuration
CHECKPOINT_FILE = "/app/test_reports/feature26_root_cause_checkpointC_20260618T021249Z.json"

# Test results
results = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "validation_type": "feature26_checkpoint_validation_v2",
    "checkpoint_file": CHECKPOINT_FILE,
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

def validate_checkpoint_values(checkpoint):
    """Validate all required checkpoint values"""
    print("\n=== Validating Checkpoint Values ===")
    
    gate_comp = checkpoint.get("gate_comparison", {})
    
    # Test 1: strict_zero exclude_synthetic=false => sustained false
    strict_false = gate_comp.get("strict_zero_exclude_synthetic_false", {})
    expected = False
    actual = strict_false.get("sustained_gate_met")
    log_test(
        "1) strict_zero exclude_synthetic=false => sustained false",
        expected,
        actual,
        actual == expected
    )
    
    # Test 2: near_zero exclude_synthetic=false => sustained false
    near_false = gate_comp.get("near_zero_exclude_synthetic_false", {})
    expected = False
    actual = near_false.get("sustained_gate_met")
    log_test(
        "2) near_zero exclude_synthetic=false => sustained false",
        expected,
        actual,
        actual == expected
    )
    
    # Test 3: near_zero exclude_synthetic=true => sustained true
    near_true = gate_comp.get("near_zero_exclude_synthetic_true", {})
    expected = True
    actual = near_true.get("sustained_gate_met")
    log_test(
        "3) near_zero exclude_synthetic=true => sustained true",
        expected,
        actual,
        actual == expected
    )
    
    # Test 4: Telemetry top operations include candidate_save_job
    telemetry = checkpoint.get("telemetry_snapshot", {})
    top_ops = telemetry.get("top_operations", [])
    operation_names = [op.get("operation") for op in top_ops]
    
    has_candidate_save = "candidate_save_job" in operation_names
    log_test(
        "4) telemetry includes candidate_save_job operation",
        True,
        has_candidate_save,
        has_candidate_save
    )
    
    # Test 5: Telemetry top operations include employers_reverify
    has_employers_reverify = "employers_reverify" in operation_names
    log_test(
        "5) telemetry includes employers_reverify operation",
        True,
        has_employers_reverify,
        has_employers_reverify
    )
    
    # Test 6: Governance vs operational divergence exists
    # Check if gate_divergence_detected is true for synthetic-included modes
    strict_false_divergence = strict_false.get("gate_divergence_detected")
    near_false_divergence = near_false.get("gate_divergence_detected")
    near_true_divergence = near_true.get("gate_divergence_detected")
    
    # Divergence should be true when synthetic is included (governance view)
    # and false when synthetic is excluded (operational view)
    divergence_correct = (
        strict_false_divergence == True and
        near_false_divergence == True and
        near_true_divergence == False
    )
    
    log_test(
        "6) governance-vs-operational divergence pattern correct",
        "strict_false=True, near_false=True, near_true=False",
        f"strict_false={strict_false_divergence}, near_false={near_false_divergence}, near_true={near_true_divergence}",
        divergence_correct
    )
    
    # Additional validation: Check operational signal is green
    operational_signal_strict_false = strict_false.get("operational_signal", {})
    operational_signal_near_true = near_true.get("operational_signal", {})
    
    operational_green = (
        operational_signal_strict_false.get("sustained_gate_met") == True and
        operational_signal_near_true.get("sustained_gate_met") == True
    )
    
    log_test(
        "7) operational signal is green (sustained_gate_met=true)",
        True,
        operational_green,
        operational_green
    )
    
    # Validate specific counts
    candidate_save_count = next((op.get("count") for op in top_ops if op.get("operation") == "candidate_save_job"), 0)
    employers_reverify_count = next((op.get("count") for op in top_ops if op.get("operation") == "employers_reverify"), 0)
    
    log_test(
        "8) candidate_save_job count = 17",
        17,
        candidate_save_count,
        candidate_save_count == 17
    )
    
    log_test(
        "9) employers_reverify count = 2",
        2,
        employers_reverify_count,
        employers_reverify_count == 2
    )
    
    return True

def print_summary():
    """Print detailed summary"""
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    passed_count = sum(1 for test in results["tests"] if test["passed"])
    total_count = len(results["tests"])
    
    print(f"\nTests Passed: {passed_count}/{total_count}")
    
    if passed_count == total_count:
        print("\n✅ ALL VALIDATIONS PASSED")
        results["overall_status"] = "PASS"
    else:
        print("\n❌ SOME VALIDATIONS FAILED")
        results["overall_status"] = "FAIL"
        print("\nFailed tests:")
        for test in results["tests"]:
            if not test["passed"]:
                print(f"  - {test['test']}")
    
    # Print extracted values for reference
    print("\n" + "=" * 80)
    print("EXTRACTED VALUES FROM CHECKPOINT")
    print("=" * 80)
    
    checkpoint = load_checkpoint()
    if checkpoint:
        gate_comp = checkpoint.get("gate_comparison", {})
        
        print("\n1. strict_zero exclude_synthetic=false:")
        print(f"   sustained_gate_met: {gate_comp.get('strict_zero_exclude_synthetic_false', {}).get('sustained_gate_met')}")
        print(f"   gate_divergence_detected: {gate_comp.get('strict_zero_exclude_synthetic_false', {}).get('gate_divergence_detected')}")
        
        print("\n2. near_zero exclude_synthetic=false:")
        print(f"   sustained_gate_met: {gate_comp.get('near_zero_exclude_synthetic_false', {}).get('sustained_gate_met')}")
        print(f"   gate_divergence_detected: {gate_comp.get('near_zero_exclude_synthetic_false', {}).get('gate_divergence_detected')}")
        
        print("\n3. near_zero exclude_synthetic=true:")
        print(f"   sustained_gate_met: {gate_comp.get('near_zero_exclude_synthetic_true', {}).get('sustained_gate_met')}")
        print(f"   gate_divergence_detected: {gate_comp.get('near_zero_exclude_synthetic_true', {}).get('gate_divergence_detected')}")
        
        print("\n4. Telemetry top operations:")
        telemetry = checkpoint.get("telemetry_snapshot", {})
        for op in telemetry.get("top_operations", []):
            print(f"   - {op.get('operation')}: {op.get('count')}")

def main():
    """Main validation flow"""
    print("=" * 80)
    print("Feature 26 Root-Cause Checkpoint Validation V2")
    print("=" * 80)
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    if not checkpoint:
        results["overall_status"] = "FAIL"
        results["error"] = "Failed to load checkpoint artifact"
        print("\n❌ VALIDATION FAILED: Could not load checkpoint")
        return
    
    # Validate checkpoint values
    validate_checkpoint_values(checkpoint)
    
    # Print summary
    print_summary()
    
    # Save results
    output_file = "/app/test_reports/feature26_checkpoint_validation_result_v2.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
