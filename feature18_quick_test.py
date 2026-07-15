#!/usr/bin/env python3
"""
Feature 18 (AI Enterprise) Backend Regression Test
Quick validation after frontend parser/button updates

Tests:
1. GET /api/ai-enterprise/health
2. Export endpoint format modes: payload, json, csv
3. Invalid format handling
"""

import requests
import json
import uuid

BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"

def test_health():
    """Test 1: Health endpoint"""
    print("\n=== Test 1: GET /api/ai-enterprise/health ===")
    
    response = requests.get(f"{BASE_URL}/api/ai-enterprise/health", timeout=10)
    
    if response.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        return False
    
    data = response.json()
    
    if data.get("status") != "healthy":
        print(f"❌ FAIL: status is not 'healthy': {data.get('status')}")
        return False
    
    if data.get("feature_id") != "ai-enterprise":
        print(f"❌ FAIL: feature_id is not 'ai-enterprise': {data.get('feature_id')}")
        return False
    
    print(f"✅ PASS: Health endpoint working correctly")
    return True


def create_workspace_and_export(format_type):
    """Create a workspace and test export with given format"""
    guest_id = f"user_{uuid.uuid4().hex[:16]}"
    
    # Create workspace
    response = requests.post(
        f"{BASE_URL}/api/ai-enterprise/workspaces/create",
        json={
            "title": f"Test Workspace {uuid.uuid4().hex[:8]}",
            "context": f"Test for format={format_type}",
            "focus": "testing",
            "fallback_user_id": guest_id
        },
        timeout=15
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create workspace: {response.status_code}")
        return None, None
    
    workspace_id = response.json().get("workspace", {}).get("workspace_id")
    return workspace_id, guest_id


def test_export_payload():
    """Test 2: Export with format=payload"""
    print("\n=== Test 2: Export format=payload ===")
    
    workspace_id, guest_id = create_workspace_and_export("payload")
    if not workspace_id:
        print("❌ FAIL: Could not create workspace")
        return False
    
    response = requests.get(
        f"{BASE_URL}/api/ai-enterprise/workspaces/{workspace_id}/export",
        params={"fallback_user_id": guest_id, "format": "payload"},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        return False
    
    data = response.json()
    
    if not data.get("success"):
        print(f"❌ FAIL: success is not True")
        return False
    
    if "export_id" not in data:
        print(f"❌ FAIL: Missing export_id")
        return False
    
    print(f"✅ PASS: Payload format working, export_id={data.get('export_id')}")
    return True


def test_export_json():
    """Test 3: Export with format=json"""
    print("\n=== Test 3: Export format=json ===")
    
    workspace_id, guest_id = create_workspace_and_export("json")
    if not workspace_id:
        print("❌ FAIL: Could not create workspace")
        return False
    
    response = requests.get(
        f"{BASE_URL}/api/ai-enterprise/workspaces/{workspace_id}/export",
        params={"fallback_user_id": guest_id, "format": "json"},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        return False
    
    content_type = response.headers.get("Content-Type", "")
    if "application/json" not in content_type:
        print(f"❌ FAIL: Wrong Content-Type: {content_type}")
        return False
    
    content_disposition = response.headers.get("Content-Disposition", "")
    if "attachment" not in content_disposition or ".json" not in content_disposition:
        print(f"❌ FAIL: Wrong Content-Disposition: {content_disposition}")
        return False
    
    try:
        data = json.loads(response.text)
        if not data.get("success"):
            print(f"❌ FAIL: JSON content success is not True")
            return False
    except:
        print(f"❌ FAIL: Response is not valid JSON")
        return False
    
    print(f"✅ PASS: JSON format working, size={len(response.text)} bytes")
    return True


def test_export_csv():
    """Test 4: Export with format=csv"""
    print("\n=== Test 4: Export format=csv ===")
    
    workspace_id, guest_id = create_workspace_and_export("csv")
    if not workspace_id:
        print("❌ FAIL: Could not create workspace")
        return False
    
    response = requests.get(
        f"{BASE_URL}/api/ai-enterprise/workspaces/{workspace_id}/export",
        params={"fallback_user_id": guest_id, "format": "csv"},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        return False
    
    content_type = response.headers.get("Content-Type", "")
    if "text/csv" not in content_type:
        print(f"❌ FAIL: Wrong Content-Type: {content_type}")
        return False
    
    content_disposition = response.headers.get("Content-Disposition", "")
    if "attachment" not in content_disposition or ".csv" not in content_disposition:
        print(f"❌ FAIL: Wrong Content-Disposition: {content_disposition}")
        return False
    
    content = response.text
    if "section,item,value" not in content:
        print(f"❌ FAIL: CSV missing expected header")
        return False
    
    if "workspace" not in content or workspace_id not in content:
        print(f"❌ FAIL: CSV missing workspace data")
        return False
    
    print(f"✅ PASS: CSV format working, size={len(content)} bytes")
    return True


def test_export_invalid():
    """Test 5: Export with invalid format"""
    print("\n=== Test 5: Export format=xml (invalid) ===")
    
    workspace_id, guest_id = create_workspace_and_export("xml")
    if not workspace_id:
        print("❌ FAIL: Could not create workspace")
        return False
    
    response = requests.get(
        f"{BASE_URL}/api/ai-enterprise/workspaces/{workspace_id}/export",
        params={"fallback_user_id": guest_id, "format": "xml"},
        timeout=10
    )
    
    if response.status_code != 400:
        print(f"❌ FAIL: Expected 400, got {response.status_code}")
        return False
    
    data = response.json()
    error_code = data.get("detail", {}).get("error_code")
    
    if error_code != "ai_enterprise_invalid_export_format":
        print(f"❌ FAIL: Wrong error_code: {error_code}")
        return False
    
    message = data.get("detail", {}).get("message", "")
    if "payload, json, csv" not in message:
        print(f"❌ FAIL: Error message doesn't list valid formats: {message}")
        return False
    
    print(f"✅ PASS: Invalid format correctly rejected with 400")
    return True


def main():
    """Run all tests"""
    print("="*70)
    print("Feature 18 (AI Enterprise) Backend Regression Test")
    print(f"Base URL: {BASE_URL}")
    print("="*70)
    
    results = []
    
    results.append(("Health endpoint", test_health()))
    results.append(("Export format=payload", test_export_payload()))
    results.append(("Export format=json", test_export_json()))
    results.append(("Export format=csv", test_export_csv()))
    results.append(("Export invalid format", test_export_invalid()))
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - NO REGRESSION DETECTED")
        return True
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED - REGRESSION DETECTED")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
