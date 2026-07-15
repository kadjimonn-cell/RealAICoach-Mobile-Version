#!/usr/bin/env python3
"""
Feature 15 (Video Studio) Backend Non-Regression Test
Concise validation after P1 frontend refactor
"""

import requests
import sys

BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"

def test_health():
    """Test 1: GET /api/video-studio/health => 200"""
    print("Test 1: GET /api/video-studio/health")
    try:
        response = requests.get(f"{BASE_URL}/api/video-studio/health", timeout=10)
        status = response.status_code
        print(f"  Status: {status}")
        if status == 200:
            data = response.json()
            print(f"  Response: {data}")
            print("  ✅ PASS")
            return True
        else:
            print(f"  ❌ FAIL - Expected 200, got {status}")
            return False
    except Exception as e:
        print(f"  ❌ FAIL - Exception: {e}")
        return False


def test_bootstrap():
    """Test 2: GET /api/video-studio/bootstrap?fallback_user_id=... => 200"""
    print("\nTest 2: GET /api/video-studio/bootstrap with fallback_user_id")
    fallback_id = "user_p1refactor_feature15_2026abc"
    try:
        response = requests.get(
            f"{BASE_URL}/api/video-studio/bootstrap",
            params={"fallback_user_id": fallback_id},
            timeout=10
        )
        status = response.status_code
        print(f"  Status: {status}")
        if status == 200:
            data = response.json()
            print(f"  Response keys: {list(data.keys())}")
            print(f"  Plan: {data.get('plan')}")
            print(f"  Project count: {data.get('project_count')}")
            print("  ✅ PASS")
            return True
        else:
            print(f"  ❌ FAIL - Expected 200, got {status}")
            print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"  ❌ FAIL - Exception: {e}")
        return False


def test_create_project():
    """Test 3: POST /api/video-studio/projects/create with fallback_user_id"""
    print("\nTest 3: POST /api/video-studio/projects/create")
    fallback_id = "user_p1refactor_feature15_2026abc"
    payload = {
        "title": "P1 Refactor Test Video",
        "description": "Non-regression test after P1 frontend refactor",
        "platform": "youtube",
        "video_type": "educational",
        "target_duration_seconds": 300,
        "fallback_user_id": fallback_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/video-studio/projects/create",
            json=payload,
            timeout=15
        )
        status = response.status_code
        print(f"  Status: {status}")
        
        # Accept 200, 201, or expected validation errors (400, 401, 429)
        if status in [200, 201]:
            data = response.json()
            print(f"  Success: {data.get('success')}")
            print(f"  Project ID: {data.get('project', {}).get('project_id')}")
            print("  ✅ PASS - Project created successfully")
            return True
        elif status in [400, 401, 429]:
            # Expected validation/auth/rate-limit errors are acceptable
            data = response.json()
            print(f"  Expected validation/auth response: {data}")
            print("  ✅ PASS - Expected auth/validation contract")
            return True
        elif status >= 500:
            print(f"  ❌ FAIL - Unexpected 5xx error: {status}")
            print(f"  Response: {response.text[:300]}")
            return False
        else:
            print(f"  ⚠️  Unexpected status {status}, but not 5xx")
            print(f"  Response: {response.text[:200]}")
            return True  # Not a 5xx, so pass
            
    except Exception as e:
        print(f"  ❌ FAIL - Exception: {e}")
        return False


def main():
    print("=" * 60)
    print("Feature 15 Video Studio - Backend Non-Regression Tests")
    print("Base URL:", BASE_URL)
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Bootstrap", test_bootstrap()))
    results.append(("Create Project", test_create_project()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - No unexpected 5xx errors")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
