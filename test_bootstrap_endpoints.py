#!/usr/bin/env python3
"""
Backend API Testing for Feature Bootstrap Endpoints
Tests bootstrap endpoints with valid fallback_user_id
"""

import requests
import json
import sys

# Base URL from frontend/.env
BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"

# Valid fallback_user_id format: user_[a-zA-Z0-9_-]{12,80}
VALID_FALLBACK_USER_ID = "user_test12345678"

def test_endpoint(endpoint_name, endpoint_path):
    """Test a bootstrap endpoint with valid fallback_user_id"""
    print("\n" + "="*80)
    print(f"TEST: {endpoint_name}")
    print("="*80)
    
    url = f"{BASE_URL}{endpoint_path}?fallback_user_id={VALID_FALLBACK_USER_ID}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ PASS: {endpoint_name}")
                
                # Handle both dict and list responses
                if isinstance(data, dict):
                    print(f"Response keys: {list(data.keys())}")
                    
                    # Show some key fields if available
                    if "tier" in data:
                        print(f"  - tier: {data.get('tier')}")
                    if "usage" in data:
                        print(f"  - usage: {data.get('usage')}")
                    if "limits" in data:
                        print(f"  - limits: {data.get('limits')}")
                elif isinstance(data, list):
                    print(f"Response type: list with {len(data)} items")
                    if len(data) > 0:
                        print(f"  - First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")
                else:
                    print(f"Response type: {type(data).__name__}")
                
                return True
            except json.JSONDecodeError:
                print(f"⚠️ WARNING: Response is not valid JSON")
                print(f"Response text: {response.text[:200]}")
                return False
        else:
            print(f"❌ FAIL: {endpoint_name}")
            print(f"Expected status 200, got {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ FAIL: {endpoint_name} - Request timeout")
        return False
    except Exception as e:
        print(f"❌ FAIL: {endpoint_name} - Exception: {str(e)}")
        return False

def main():
    """Run all bootstrap endpoint tests"""
    print("\n" + "="*80)
    print("FEATURE BOOTSTRAP ENDPOINTS SANITY CHECK")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Fallback User ID: {VALID_FALLBACK_USER_ID}")
    
    results = {}
    
    # Test 1: Writing Studio Bootstrap
    results["writing_studio"] = test_endpoint(
        "GET /api/writing-studio/bootstrap",
        "/api/writing-studio/bootstrap"
    )
    
    # Test 2: Personal Assistant Bootstrap
    results["personal_assistant"] = test_endpoint(
        "GET /api/personal-assistant/bootstrap",
        "/api/personal-assistant/bootstrap"
    )
    
    # Test 3: Research Navigator Bootstrap
    results["research_navigator"] = test_endpoint(
        "GET /api/research-navigator/bootstrap",
        "/api/research-navigator/bootstrap"
    )
    
    # Test 4: Workflows
    results["workflows"] = test_endpoint(
        "GET /api/workflows",
        "/api/workflows"
    )
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for endpoint_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{endpoint_name.upper()}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*80)
    if all_passed:
        print("OVERALL RESULT: ✅ ALL TESTS PASSED")
    else:
        failed_count = sum(1 for v in results.values() if not v)
        print(f"OVERALL RESULT: ❌ {failed_count} TEST(S) FAILED")
    print("="*80)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
