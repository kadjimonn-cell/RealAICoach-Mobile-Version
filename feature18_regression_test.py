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

BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
GUEST_USER_ID = f"user_{uuid.uuid4().hex[:16]}"

test_results = []


def log_result(test_name, passed, details=""):
    """Log test result"""
    test_results.append({"test": test_name, "passed": passed, "details": details})
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"  Details: {details}")


def test_health_endpoint():
    """Test 1: GET /api/ai-enterprise/health"""
    print("\n=== Test 1: Health Endpoint ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/ai-enterprise/health", timeout=10)
        
        if response.status_code != 200:
            log_result("Health endpoint status", False, f"Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        
        # Verify required fields
        checks = [
            (data.get("status") == "healthy", "status is 'healthy'"),
            (data.get("feature") == "Business Operations Copilot", "feature name correct"),
            (data.get("feature_id") == "ai-enterprise", "feature_id correct"),
        ]
        
        all_passed = True
        for check, desc in checks:
            if not check:
                log_result(f"Health endpoint - {desc}", False, f"Check failed: {desc}")
                all_passed = False
        
        if all_passed:
            log_result("Health endpoint", True, "All checks passed")
        
        return all_passed
        
    except Exception as e:
        log_result("Health endpoint", False, f"Exception: {str(e)}")
        return False


def setup_workspace():
    """Setup: Create a workspace for export testing"""
    print("\n=== Setup: Creating Workspace ===")
    
    try:
        # Create workspace
        response = requests.post(
            f"{BASE_URL}/api/ai-enterprise/workspaces/create",
            json={
                "title": f"Regression Test Workspace {uuid.uuid4().hex[:8]}",
                "context": "Test workspace for export format validation",
                "focus": "testing",
                "fallback_user_id": GUEST_USER_ID
            },
            timeout=15
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to create workspace: {response.status_code}")
            return None
        
        data = response.json()
        workspace_id = data.get("workspace", {}).get("workspace_id")
        
        if not workspace_id:
            print("❌ No workspace_id in response")
            return None
        
        print(f"✅ Workspace created: {workspace_id}")
        return workspace_id
        
    except Exception as e:
        print(f"❌ Exception during setup: {str(e)}")
        return None


def test_export_format_payload(workspace_id, guest_user_id):
    """Test 2: Export with format=payload (default)"""
    print("\n=== Test 2: Export Format - Payload ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/ai-enterprise/workspaces/{workspace_id}/export",
            params={
                "fallback_user_id": guest_user_id,
                "format": "payload"
            },
            timeout=10
        )
        
        if response.status_code != 200:
            log_result("Export format=payload", False, f"Expected 200, got {response.status_code}")
            return False
        
        # Verify it's JSON response
        try:
            data = response.json()
        except:
            log_result("Export format=payload", False, "Response is not valid JSON")
            return False
        
        # Verify structure
        required_keys = ["success", "export_id", "workspace", "runs", "playbooks", "summary"]
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            log_result("Export format=payload", False, f"Missing keys: {missing_keys}")
            return False
        
        if not data.get("success"):
            log_result("Export format=payload", False, "success is not True")
            return False
        
        log_result("Export format=payload", True, f"Export ID: {data.get('export_id')}")
        return True
        
    except Exception as e:
        log_result("Export format=payload", False, f"Exception: {str(e)}")
        return False


def test_export_format_json(workspace_id):
    """Test 3: Export with format=json (file download)"""
    print("\n=== Test 3: Export Format - JSON ===")
    
    # Use unique guest user to avoid rate limit conflicts
    guest_id = f"user_{uuid.uuid4().hex[:16]}"
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/ai-enterprise/workspaces/{workspace_id}/export",
            params={
                "fallback_user_id": guest_id,
                "format": "json"
            },
            timeout=10
        )
        
        if response.status_code != 200:
            log_result("Export format=json", False, f"Expected 200, got {response.status_code}")
            return False
        
        # Verify Content-Type
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            log_result("Export format=json", False, f"Wrong Content-Type: {content_type}")
            return False
        
        # Verify Content-Disposition header
        content_disposition = response.headers.get("Content-Disposition", "")
        if "attachment" not in content_disposition or ".json" not in content_disposition:
            log_result("Export format=json", False, f"Wrong Content-Disposition: {content_disposition}")
            return False
        
        # Verify content is valid JSON
        try:
            data = json.loads(response.text)
        except:
            log_result("Export format=json", False, "Response is not valid JSON")
            return False
        
        # Verify structure
        if not data.get("success"):
            log_result("Export format=json", False, "success is not True in JSON content")
            return False
        
        log_result("Export format=json", True, f"JSON file download working, size: {len(response.text)} bytes")
        return True
        
    except Exception as e:
        log_result("Export format=json", False, f"Exception: {str(e)}")
        return False


def test_export_format_csv(workspace_id):
    """Test 4: Export with format=csv (file download)"""
    print("\n=== Test 4: Export Format - CSV ===")
    
    # Use unique guest user to avoid rate limit conflicts
    guest_id = f"user_{uuid.uuid4().hex[:16]}"
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/ai-enterprise/workspaces/{workspace_id}/export",
            params={
                "fallback_user_id": guest_id,
                "format": "csv"
            },
            timeout=10
        )
        
        if response.status_code != 200:
            log_result("Export format=csv", False, f"Expected 200, got {response.status_code}")
            return False
        
        # Verify Content-Type
        content_type = response.headers.get("Content-Type", "")
        if "text/csv" not in content_type:
            log_result("Export format=csv", False, f"Wrong Content-Type: {content_type}")
            return False
        
        # Verify Content-Disposition header
        content_disposition = response.headers.get("Content-Disposition", "")
        if "attachment" not in content_disposition or ".csv" not in content_disposition:
            log_result("Export format=csv", False, f"Wrong Content-Disposition: {content_disposition}")
            return False
        
        # Verify content has CSV structure
        content = response.text
        if not content or "section,item,value" not in content:
            log_result("Export format=csv", False, "CSV content missing expected header")
            return False
        
        # Verify workspace data is in CSV
        if "workspace" not in content or workspace_id not in content:
            log_result("Export format=csv", False, "CSV missing workspace data")
            return False
        
        log_result("Export format=csv", True, f"CSV file download working, size: {len(content)} bytes")
        return True
        
    except Exception as e:
        log_result("Export format=csv", False, f"Exception: {str(e)}")
        return False


def test_export_invalid_format(workspace_id):
    """Test 5: Export with invalid format (should return 400)"""
    print("\n=== Test 5: Export Format - Invalid ===")
    
    # Use unique guest user to avoid rate limit conflicts
    guest_id = f"user_{uuid.uuid4().hex[:16]}"
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/ai-enterprise/workspaces/{workspace_id}/export",
            params={
                "fallback_user_id": guest_id,
                "format": "xml"  # Invalid format
            },
            timeout=10
        )
        
        if response.status_code != 400:
            log_result("Export invalid format", False, f"Expected 400, got {response.status_code}")
            return False
        
        # Verify error response
        try:
            data = response.json()
        except:
            log_result("Export invalid format", False, "Error response is not valid JSON")
            return False
        
        # Verify error structure
        detail = data.get("detail", {})
        error_code = detail.get("error_code")
        message = detail.get("message", "")
        
        if error_code != "ai_enterprise_invalid_export_format":
            log_result("Export invalid format", False, f"Wrong error_code: {error_code}")
            return False
        
        if "payload, json, csv" not in message:
            log_result("Export invalid format", False, f"Error message doesn't list valid formats: {message}")
            return False
        
        log_result("Export invalid format", True, "Invalid format correctly rejected with 400")
        return True
        
    except Exception as e:
        log_result("Export invalid format", False, f"Exception: {str(e)}")
        return False


def print_summary():
    """Print test summary"""
    print("\n" + "="*70)
    print("FEATURE 18 BACKEND REGRESSION TEST - SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    print("Detailed Results:")
    print("-" * 70)
    for result in test_results:
        status = "✅" if result["passed"] else "❌"
        print(f"{status} {result['test']}")
        if result["details"]:
            print(f"   {result['details']}")
    
    print("\n" + "="*70)
    
    if passed == total:
        print("✅ ALL TESTS PASSED - REGRESSION CHECK SUCCESSFUL")
    else:
        print(f"❌ {total - passed} TEST(S) FAILED - REGRESSION DETECTED")
    
    print("="*70 + "\n")
    
    return passed == total


def main():
    """Run all regression tests"""
    print("="*70)
    print("Feature 18 (AI Enterprise) Backend Regression Test")
    print("Base URL:", BASE_URL)
    print("="*70)
    
    # Test 1: Health endpoint
    test_health_endpoint()
    
    # Setup: Create workspace for export tests
    workspace_id = setup_workspace()
    
    if not workspace_id:
        print("\n❌ CRITICAL: Cannot proceed without workspace")
        print_summary()
        return False
    
    # Test 2-5: Export format tests
    test_export_format_payload(workspace_id)
    test_export_format_json(workspace_id)
    test_export_format_csv(workspace_id)
    test_export_invalid_format(workspace_id)
    
    # Print summary
    all_passed = print_summary()
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
