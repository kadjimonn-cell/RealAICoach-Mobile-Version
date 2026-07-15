#!/usr/bin/env python3
"""
Feature 26 (Jobs Portal) Backend Monitoring Verification
Testing locked monitoring cycle endpoints
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

def login_admin():
    """Login as admin and return session"""
    session = requests.Session()
    
    # Login
    login_url = f"{BASE_URL}/api/auth/login"
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    print(f"🔐 Logging in as admin: {ADMIN_EMAIL}")
    response = session.post(login_url, json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    print(f"✅ Login successful")
    return session

def test_health_endpoint(session):
    """Test /api/hiring/v2/health for lock contract"""
    print("\n" + "="*80)
    print("TEST 1: /api/hiring/v2/health - Lock Contract")
    print("="*80)
    
    url = f"{BASE_URL}/api/hiring/v2/health"
    
    try:
        response = session.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Health endpoint returned 200")
            print(f"\nResponse Data:")
            print(json.dumps(data, indent=2))
            
            # Check for lock contract fields
            if "feature_number" in data and "feature_id" in data:
                print(f"\n✅ Lock contract present:")
                print(f"   - feature_number: {data.get('feature_number')}")
                print(f"   - feature_id: {data.get('feature_id')}")
                
                if data.get('feature_number') == 26 and data.get('feature_id') == 'jobs-portal':
                    print(f"✅ Lock contract matches expected values (26, jobs-portal)")
                    return True, data
                else:
                    print(f"⚠️ Lock contract values don't match expected (26, jobs-portal)")
                    return False, data
            else:
                print(f"❌ Lock contract fields missing")
                return False, data
        else:
            print(f"❌ FAIL - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ FAIL - Exception: {str(e)}")
        return False, None

def test_legacy_retirement_readiness(session):
    """Test /api/hiring/v2/admin/legacy-retirement-readiness"""
    print("\n" + "="*80)
    print("TEST 2: /api/hiring/v2/admin/legacy-retirement-readiness?lookback_hours=72")
    print("="*80)
    
    url = f"{BASE_URL}/api/hiring/v2/admin/legacy-retirement-readiness?lookback_hours=72"
    
    try:
        response = session.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Endpoint returned 200")
            print(f"\nResponse Data:")
            print(json.dumps(data, indent=2))
            
            # Check for observe phase
            if "retirement_phase" in data:
                phase = data.get("retirement_phase")
                print(f"\n✅ retirement_phase field present: {phase}")
                
                if phase == "observe":
                    print(f"✅ retirement_phase is 'observe' as expected")
                    return True, data
                else:
                    print(f"⚠️ retirement_phase is '{phase}', expected 'observe'")
                    return False, data
            else:
                print(f"❌ retirement_phase field missing")
                return False, data
        else:
            print(f"❌ FAIL - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ FAIL - Exception: {str(e)}")
        return False, None

def test_legacy_removal_readiness_strict_zero(session):
    """Test /api/hiring/v2/admin/legacy-removal-readiness with strict_zero mode"""
    print("\n" + "="*80)
    print("TEST 3: /api/hiring/v2/admin/legacy-removal-readiness?mode=strict_zero&exclude_synthetic=false")
    print("="*80)
    
    url = f"{BASE_URL}/api/hiring/v2/admin/legacy-removal-readiness?mode=strict_zero&exclude_synthetic=false"
    
    try:
        response = session.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Endpoint returned 200")
            print(f"\nResponse Data:")
            print(json.dumps(data, indent=2))
            
            # Check for sustained_gate_met field
            if "sustained_gate_met" in data:
                sustained = data.get("sustained_gate_met")
                print(f"\n✅ sustained_gate_met field present: {sustained}")
                
                if sustained == False:
                    print(f"✅ sustained_gate_met is False as expected")
                    return True, data
                else:
                    print(f"⚠️ sustained_gate_met is {sustained}, expected False")
                    return False, data
            else:
                print(f"❌ sustained_gate_met field missing")
                return False, data
        else:
            print(f"❌ FAIL - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ FAIL - Exception: {str(e)}")
        return False, None

def test_legacy_removal_readiness_near_zero(session):
    """Test /api/hiring/v2/admin/legacy-removal-readiness with near_zero mode"""
    print("\n" + "="*80)
    print("TEST 4: /api/hiring/v2/admin/legacy-removal-readiness?mode=near_zero&exclude_synthetic=false")
    print("="*80)
    
    url = f"{BASE_URL}/api/hiring/v2/admin/legacy-removal-readiness?mode=near_zero&exclude_synthetic=false"
    
    try:
        response = session.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Endpoint returned 200")
            print(f"\nResponse Data:")
            print(json.dumps(data, indent=2))
            
            # Check for sustained_gate_met field
            if "sustained_gate_met" in data:
                sustained = data.get("sustained_gate_met")
                print(f"\n✅ sustained_gate_met field present: {sustained}")
                
                if sustained == False:
                    print(f"✅ sustained_gate_met is False as expected")
                else:
                    print(f"⚠️ sustained_gate_met is {sustained}, expected False")
                
                # Check for operational signal fields
                operational_signals_present = False
                if "operational_near_zero_excluding_synthetic" in data:
                    operational_data = data.get("operational_near_zero_excluding_synthetic")
                    print(f"\n✅ operational_near_zero_excluding_synthetic present:")
                    print(json.dumps(operational_data, indent=2))
                    
                    if "sustained_gate_met" in operational_data:
                        print(f"✅ sustained_gate_met field present: {operational_data.get('sustained_gate_met')}")
                        operational_signals_present = True
                    else:
                        print(f"❌ sustained_gate_met field missing")
                else:
                    print(f"❌ operational_near_zero_excluding_synthetic field missing")
                
                if "gate_divergence_detected" in data:
                    print(f"✅ gate_divergence_detected field present: {data.get('gate_divergence_detected')}")
                    operational_signals_present = True
                else:
                    print(f"❌ gate_divergence_detected field missing")
                
                if operational_signals_present and sustained == False:
                    print(f"\n✅ All required fields present and sustained_gate_met is False")
                    return True, data
                else:
                    print(f"\n⚠️ Some required fields missing or sustained_gate_met is not False")
                    return False, data
            else:
                print(f"❌ sustained_gate_met field missing")
                return False, data
        else:
            print(f"❌ FAIL - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ FAIL - Exception: {str(e)}")
        return False, None

def main():
    """Main test execution"""
    print("="*80)
    print("Feature 26 (Jobs Portal) Backend Monitoring Verification")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print("="*80)
    
    # Login
    session = login_admin()
    if not session:
        print("\n❌ OVERALL RESULT: FAIL - Could not login")
        return
    
    # Run tests
    results = {}
    
    # Test 1: Health endpoint
    test1_pass, test1_data = test_health_endpoint(session)
    results["health_endpoint"] = {
        "pass": test1_pass,
        "data": test1_data
    }
    
    # Test 2: Legacy retirement readiness
    test2_pass, test2_data = test_legacy_retirement_readiness(session)
    results["legacy_retirement_readiness"] = {
        "pass": test2_pass,
        "data": test2_data
    }
    
    # Test 3: Legacy removal readiness (strict_zero)
    test3_pass, test3_data = test_legacy_removal_readiness_strict_zero(session)
    results["legacy_removal_readiness_strict_zero"] = {
        "pass": test3_pass,
        "data": test3_data
    }
    
    # Test 4: Legacy removal readiness (near_zero)
    test4_pass, test4_data = test_legacy_removal_readiness_near_zero(session)
    results["legacy_removal_readiness_near_zero"] = {
        "pass": test4_pass,
        "data": test4_data
    }
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    all_passed = all([
        test1_pass,
        test2_pass,
        test3_pass,
        test4_pass
    ])
    
    print(f"\n1. Health Endpoint (Lock Contract): {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"2. Legacy Retirement Readiness (Observe Phase): {'✅ PASS' if test2_pass else '❌ FAIL'}")
    print(f"3. Legacy Removal Readiness (strict_zero, sustained=false): {'✅ PASS' if test3_pass else '❌ FAIL'}")
    print(f"4. Legacy Removal Readiness (near_zero, sustained=false + operational signals): {'✅ PASS' if test4_pass else '❌ FAIL'}")
    
    print(f"\n{'='*80}")
    if all_passed:
        print("✅ OVERALL RESULT: PASS - All tests passed")
    else:
        print("❌ OVERALL RESULT: FAIL - Some tests failed")
    print("="*80)
    
    # Save results to file
    results_file = "/app/feature26_monitoring_verification_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "overall_pass": all_passed,
            "results": results
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")

if __name__ == "__main__":
    main()
