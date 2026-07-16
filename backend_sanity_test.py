#!/usr/bin/env python3
"""
Backend Sanity Validation Test
Tests basic health endpoints and bootstrap functionality
"""

import requests
import json
import sys

BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"

def test_health_endpoint():
    """Test GET /api/health returns 200"""
    url = f"{BASE_URL}/api/health"
    try:
        response = requests.get(url, timeout=10)
        status = response.status_code
        print(f"✓ GET /api/health - Status: {status}")
        return status == 200
    except Exception as e:
        print(f"✗ GET /api/health - Error: {e}")
        return False

def test_ai_enterprise_health():
    """Test GET /api/ai-enterprise/health returns 200"""
    url = f"{BASE_URL}/api/ai-enterprise/health"
    try:
        response = requests.get(url, timeout=10)
        status = response.status_code
        print(f"✓ GET /api/ai-enterprise/health - Status: {status}")
        return status == 200
    except Exception as e:
        print(f"✗ GET /api/ai-enterprise/health - Error: {e}")
        return False

def test_bootstrap_endpoint():
    """Test GET /api/ai-enterprise/bootstrap with fallback_user_id"""
    url = f"{BASE_URL}/api/ai-enterprise/bootstrap"
    params = {"fallback_user_id": "user_backend_sanity_2026"}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        status = response.status_code
        
        if status != 200:
            print(f"✗ GET /api/ai-enterprise/bootstrap - Status: {status}")
            return False
        
        # Validate JSON payload
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"✗ GET /api/ai-enterprise/bootstrap - Invalid JSON response")
            return False
        
        # Validate required fields
        required_fields = ["success", "feature_id", "plan", "limits", "usage", "features"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"✗ GET /api/ai-enterprise/bootstrap - Missing fields: {missing_fields}")
            return False
        
        print(f"✓ GET /api/ai-enterprise/bootstrap - Status: {status}")
        print(f"  - Valid JSON payload with all required fields")
        print(f"  - success: {data.get('success')}")
        print(f"  - feature_id: {data.get('feature_id')}")
        print(f"  - plan: {data.get('plan')}")
        return True
        
    except Exception as e:
        print(f"✗ GET /api/ai-enterprise/bootstrap - Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Backend Sanity Validation Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: /api/health
    print("Test 1: Health Endpoint")
    results.append(test_health_endpoint())
    print()
    
    # Test 2: /api/ai-enterprise/health
    print("Test 2: AI Enterprise Health Endpoint")
    results.append(test_ai_enterprise_health())
    print()
    
    # Test 3: /api/ai-enterprise/bootstrap
    print("Test 3: Bootstrap Endpoint")
    results.append(test_bootstrap_endpoint())
    print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests PASSED")
        sys.exit(0)
    else:
        print("✗ Some tests FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
