#!/usr/bin/env python3
"""
Feature 26 Root-Cause Verification Test
Read-only validation of legacy removal readiness endpoints
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

def login_admin() -> str:
    """Login as admin and return session cookies"""
    login_url = f"{BASE_URL}/api/auth/login"
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    print(f"🔐 Logging in as admin: {ADMIN_EMAIL}")
    response = requests.post(login_url, json=payload)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    print(f"✅ Login successful")
    return response.cookies

def test_legacy_removal_readiness(cookies, mode: str, exclude_synthetic: bool) -> Dict[str, Any]:
    """Test legacy removal readiness endpoint"""
    url = f"{BASE_URL}/api/hiring/v2/admin/legacy-removal-readiness"
    params = {
        "mode": mode,
        "exclude_synthetic": str(exclude_synthetic).lower()
    }
    
    print(f"\n📊 Testing: mode={mode}, exclude_synthetic={exclude_synthetic}")
    response = requests.get(url, params=params, cookies=cookies)
    
    if response.status_code != 200:
        print(f"❌ Request failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    data = response.json()
    print(f"✅ Request successful")
    
    # Extract key metrics
    sustained_gate_met = data.get("sustained_gate_met", "N/A")
    ready_for_removal = data.get("ready_for_legacy_code_removal", "N/A")
    
    print(f"   sustained_gate_met: {sustained_gate_met}")
    print(f"   ready_for_legacy_code_removal: {ready_for_removal}")
    
    # Extract jobs/employers 72h metrics
    if "jobs" in data:
        jobs_72h = data["jobs"].get("72h", {})
        print(f"   jobs.72h.total_events: {jobs_72h.get('total_events', 'N/A')}")
        print(f"   jobs.72h.active_users: {jobs_72h.get('active_users', 'N/A')}")
        if "synthetic_excluded_count" in jobs_72h:
            print(f"   jobs.72h.synthetic_excluded_count: {jobs_72h.get('synthetic_excluded_count')}")
    
    if "employers" in data:
        employers_72h = data["employers"].get("72h", {})
        print(f"   employers.72h.total_events: {employers_72h.get('total_events', 'N/A')}")
        print(f"   employers.72h.active_users: {employers_72h.get('active_users', 'N/A')}")
        if "synthetic_excluded_count" in employers_72h:
            print(f"   employers.72h.synthetic_excluded_count: {employers_72h.get('synthetic_excluded_count')}")
    
    return data

def test_deprecation_telemetry(cookies, lookback_days: int, limit: int) -> Dict[str, Any]:
    """Test deprecation telemetry endpoint"""
    url = f"{BASE_URL}/api/hiring/v2/admin/deprecation-telemetry"
    params = {
        "lookback_days": lookback_days,
        "limit": limit
    }
    
    print(f"\n📊 Testing deprecation telemetry: lookback_days={lookback_days}, limit={limit}")
    response = requests.get(url, params=params, cookies=cookies)
    
    if response.status_code != 200:
        print(f"❌ Request failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    data = response.json()
    print(f"✅ Request successful")
    
    # Extract top operations/endpoints
    if "top_operations" in data:
        print(f"   Top operations:")
        for i, op in enumerate(data["top_operations"][:5], 1):
            print(f"      {i}. {op.get('operation', 'N/A')} - {op.get('count', 0)} events")
    
    if "top_endpoints" in data:
        print(f"   Top endpoints:")
        for i, ep in enumerate(data["top_endpoints"][:5], 1):
            print(f"      {i}. {ep.get('endpoint', 'N/A')} - {ep.get('count', 0)} events")
    
    return data

def main():
    print("=" * 80)
    print("Feature 26 Root-Cause Verification Test")
    print("=" * 80)
    
    # Login
    cookies = login_admin()
    if not cookies:
        print("\n❌ FAILED: Unable to login")
        return
    
    # Store results
    results = {}
    
    # Test 1: strict_zero, exclude_synthetic=false
    results["strict_zero_with_synthetic"] = test_legacy_removal_readiness(
        cookies, "strict_zero", False
    )
    
    # Test 2: strict_zero, exclude_synthetic=true
    results["strict_zero_without_synthetic"] = test_legacy_removal_readiness(
        cookies, "strict_zero", True
    )
    
    # Test 3: near_zero, exclude_synthetic=false
    results["near_zero_with_synthetic"] = test_legacy_removal_readiness(
        cookies, "near_zero", False
    )
    
    # Test 4: near_zero, exclude_synthetic=true
    results["near_zero_without_synthetic"] = test_legacy_removal_readiness(
        cookies, "near_zero", True
    )
    
    # Test 5: deprecation telemetry
    results["deprecation_telemetry"] = test_deprecation_telemetry(
        cookies, 14, 1000
    )
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY - Root Cause Analysis")
    print("=" * 80)
    
    # Compare strict_zero results
    if results["strict_zero_with_synthetic"] and results["strict_zero_without_synthetic"]:
        with_syn = results["strict_zero_with_synthetic"]
        without_syn = results["strict_zero_without_synthetic"]
        
        print("\n🔍 STRICT_ZERO Mode Comparison:")
        print(f"   WITH synthetic data:")
        print(f"      sustained_gate_met: {with_syn.get('sustained_gate_met')}")
        print(f"      ready_for_legacy_code_removal: {with_syn.get('ready_for_legacy_code_removal')}")
        
        print(f"   WITHOUT synthetic data:")
        print(f"      sustained_gate_met: {without_syn.get('sustained_gate_met')}")
        print(f"      ready_for_legacy_code_removal: {without_syn.get('ready_for_legacy_code_removal')}")
        
        # Check if excluding synthetic changes the result
        if (with_syn.get('sustained_gate_met') != without_syn.get('sustained_gate_met') or
            with_syn.get('ready_for_legacy_code_removal') != without_syn.get('ready_for_legacy_code_removal')):
            print("\n✅ ROOT CAUSE CONFIRMED: Synthetic/test data is contaminating legacy telemetry")
            print("   Excluding synthetic data changes the gate status")
        else:
            print("\n❌ ROOT CAUSE NOT CONFIRMED: Synthetic data exclusion has no effect")
    
    # Compare near_zero results
    if results["near_zero_with_synthetic"] and results["near_zero_without_synthetic"]:
        with_syn = results["near_zero_with_synthetic"]
        without_syn = results["near_zero_without_synthetic"]
        
        print("\n🔍 NEAR_ZERO Mode Comparison:")
        print(f"   WITH synthetic data:")
        print(f"      sustained_gate_met: {with_syn.get('sustained_gate_met')}")
        print(f"      ready_for_legacy_code_removal: {with_syn.get('ready_for_legacy_code_removal')}")
        
        print(f"   WITHOUT synthetic data:")
        print(f"      sustained_gate_met: {without_syn.get('sustained_gate_met')}")
        print(f"      ready_for_legacy_code_removal: {without_syn.get('ready_for_legacy_code_removal')}")
    
    # Save full results to file
    with open("/app/feature26_rca_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n📄 Full results saved to: /app/feature26_rca_results.json")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
