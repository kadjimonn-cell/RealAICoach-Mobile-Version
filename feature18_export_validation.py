"""
Feature 18: Business Operations Copilot - Export Format Validation
Validates updated Feature 18 backend after adding structured support dependencies 
and downloadable export formats.

Test cases:
1. workspace create + run still works
2. export payload mode still works
3. export format=json returns downloadable response (content-disposition with .json)
4. export format=csv returns downloadable response (content-disposition with .csv)
5. invalid export format returns 400 with ai_enterprise_invalid_export_format
6. free-tier export/day cap still enforced
"""

import os
import requests
import uuid
import json
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Use unique guest user ID for each test run
GUEST_USER_ID = f"user_test_{uuid.uuid4().hex[:16]}"

# Test state
test_results = []
workspace_id = None


def log_result(test_name: str, passed: bool, details: str = ""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = f"{status}: {test_name}"
    if details:
        result += f" - {details}"
    print(result)
    test_results.append({"test": test_name, "passed": passed, "details": details})
    return passed


def test_workspace_create_and_run():
    """Test 1: workspace create + run still works"""
    global workspace_id
    
    print("\n=== Test 1: Workspace Create + Run ===")
    
    # Step 1: Create workspace
    print("Step 1a: Creating workspace...")
    try:
        create_payload = {
            "title": f"Export Test Workspace {uuid.uuid4().hex[:8]}",
            "context": "Testing export functionality with structured dependencies",
            "focus": "operations",
            "fallback_user_id": GUEST_USER_ID
        }
        
        response = requests.post(
            f"{API_BASE}/ai-enterprise/workspaces/create",
            json=create_payload,
            timeout=15
        )
        
        if response.status_code != 200:
            return log_result(
                "Workspace create", 
                False, 
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        data = response.json()
        
        if not data.get("success"):
            return log_result("Workspace create", False, "success=False in response")
        
        workspace = data.get("workspace")
        if not workspace or not workspace.get("workspace_id"):
            return log_result("Workspace create", False, "Missing workspace_id in response")
        
        workspace_id = workspace["workspace_id"]
        log_result("Workspace create", True, f"Created workspace: {workspace_id}")
        
    except Exception as e:
        return log_result("Workspace create", False, f"Exception: {str(e)}")
    
    # Step 2: Run command in workspace
    print("Step 1b: Running command in workspace...")
    try:
        run_payload = {
            "command": "Analyze Q1 revenue trends and identify growth opportunities",
            "objective": "Revenue optimization",
            "session_id": f"test_session_{uuid.uuid4().hex[:8]}",
            "fallback_user_id": GUEST_USER_ID
        }
        
        response = requests.post(
            f"{API_BASE}/ai-enterprise/workspaces/{workspace_id}/run",
            json=run_payload,
            timeout=30
        )
        
        if response.status_code != 200:
            return log_result(
                "Workspace run", 
                False, 
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        data = response.json()
        
        if not data.get("success"):
            return log_result("Workspace run", False, "success=False in response")
        
        if not data.get("run_id"):
            return log_result("Workspace run", False, "Missing run_id in response")
        
        if not data.get("output"):
            return log_result("Workspace run", False, "Missing output in response")
        
        output_preview = data["output"][:100] + "..." if len(data["output"]) > 100 else data["output"]
        return log_result("Workspace run", True, f"Run completed: {output_preview}")
        
    except Exception as e:
        return log_result("Workspace run", False, f"Exception: {str(e)}")


def test_export_payload_mode():
    """Test 2: export payload mode still works"""
    print("\n=== Test 2: Export Payload Mode ===")
    
    if not workspace_id:
        return log_result("Export payload mode", False, "No workspace_id available")
    
    try:
        response = requests.get(
            f"{API_BASE}/ai-enterprise/workspaces/{workspace_id}/export",
            params={
                "fallback_user_id": GUEST_USER_ID,
                "format": "payload"
            },
            timeout=15
        )
        
        if response.status_code != 200:
            return log_result(
                "Export payload mode", 
                False, 
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        data = response.json()
        
        # Verify structure
        required_keys = ["success", "export_id", "workspace", "runs", "playbooks", "summary"]
        for key in required_keys:
            if key not in data:
                return log_result("Export payload mode", False, f"Missing key: {key}")
        
        if not data.get("success"):
            return log_result("Export payload mode", False, "success=False in response")
        
        summary = data.get("summary", {})
        return log_result(
            "Export payload mode", 
            True, 
            f"Export successful: {summary.get('run_count', 0)} runs, {summary.get('playbook_count', 0)} playbooks"
        )
        
    except Exception as e:
        return log_result("Export payload mode", False, f"Exception: {str(e)}")


def test_export_json_format():
    """Test 3: export format=json returns downloadable response"""
    print("\n=== Test 3: Export JSON Format ===")
    
    if not workspace_id:
        return log_result("Export JSON format", False, "No workspace_id available")
    
    # Use a fresh guest user to avoid hitting the free tier export limit
    fresh_guest_id = f"user_test_{uuid.uuid4().hex[:16]}"
    
    # First, create a workspace for this fresh user
    print("Creating workspace for fresh guest user...")
    try:
        create_payload = {
            "title": f"JSON Export Test {uuid.uuid4().hex[:8]}",
            "context": "Testing JSON export format",
            "focus": "operations",
            "fallback_user_id": fresh_guest_id
        }
        
        create_response = requests.post(
            f"{API_BASE}/ai-enterprise/workspaces/create",
            json=create_payload,
            timeout=15
        )
        
        if create_response.status_code != 200:
            return log_result("Export JSON format", False, f"Failed to create workspace: {create_response.status_code}")
        
        fresh_workspace_id = create_response.json()["workspace"]["workspace_id"]
        
        # Run a command to have some data
        run_payload = {
            "command": "Test command for JSON export",
            "fallback_user_id": fresh_guest_id
        }
        
        requests.post(
            f"{API_BASE}/ai-enterprise/workspaces/{fresh_workspace_id}/run",
            json=run_payload,
            timeout=30
        )
        
    except Exception as e:
        return log_result("Export JSON format", False, f"Setup failed: {str(e)}")
    
    try:
        response = requests.get(
            f"{API_BASE}/ai-enterprise/workspaces/{fresh_workspace_id}/export",
            params={
                "fallback_user_id": fresh_guest_id,
                "format": "json"
            },
            timeout=15
        )
        
        if response.status_code != 200:
            return log_result(
                "Export JSON format", 
                False, 
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        # Check Content-Type
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            return log_result(
                "Export JSON format", 
                False, 
                f"Expected Content-Type: application/json, got: {content_type}"
            )
        
        # Check Content-Disposition header
        content_disposition = response.headers.get("Content-Disposition", "")
        if not content_disposition:
            return log_result("Export JSON format", False, "Missing Content-Disposition header")
        
        if "attachment" not in content_disposition:
            return log_result(
                "Export JSON format", 
                False, 
                f"Content-Disposition should contain 'attachment', got: {content_disposition}"
            )
        
        if ".json" not in content_disposition:
            return log_result(
                "Export JSON format", 
                False, 
                f"Content-Disposition should contain '.json', got: {content_disposition}"
            )
        
        # Verify JSON content is valid
        try:
            data = response.json()
            if not isinstance(data, dict):
                return log_result("Export JSON format", False, "Response is not a valid JSON object")
        except json.JSONDecodeError as e:
            return log_result("Export JSON format", False, f"Invalid JSON: {str(e)}")
        
        return log_result(
            "Export JSON format", 
            True, 
            f"Downloadable JSON with Content-Disposition: {content_disposition}"
        )
        
    except Exception as e:
        return log_result("Export JSON format", False, f"Exception: {str(e)}")


def test_export_csv_format():
    """Test 4: export format=csv returns downloadable response"""
    print("\n=== Test 4: Export CSV Format ===")
    
    if not workspace_id:
        return log_result("Export CSV format", False, "No workspace_id available")
    
    # Use a fresh guest user to avoid hitting the free tier export limit
    fresh_guest_id = f"user_test_{uuid.uuid4().hex[:16]}"
    
    # First, create a workspace for this fresh user
    print("Creating workspace for fresh guest user...")
    try:
        create_payload = {
            "title": f"CSV Export Test {uuid.uuid4().hex[:8]}",
            "context": "Testing CSV export format",
            "focus": "operations",
            "fallback_user_id": fresh_guest_id
        }
        
        create_response = requests.post(
            f"{API_BASE}/ai-enterprise/workspaces/create",
            json=create_payload,
            timeout=15
        )
        
        if create_response.status_code != 200:
            return log_result("Export CSV format", False, f"Failed to create workspace: {create_response.status_code}")
        
        fresh_workspace_id = create_response.json()["workspace"]["workspace_id"]
        
        # Run a command to have some data
        run_payload = {
            "command": "Test command for CSV export",
            "fallback_user_id": fresh_guest_id
        }
        
        requests.post(
            f"{API_BASE}/ai-enterprise/workspaces/{fresh_workspace_id}/run",
            json=run_payload,
            timeout=30
        )
        
    except Exception as e:
        return log_result("Export CSV format", False, f"Setup failed: {str(e)}")
    
    try:
        response = requests.get(
            f"{API_BASE}/ai-enterprise/workspaces/{fresh_workspace_id}/export",
            params={
                "fallback_user_id": fresh_guest_id,
                "format": "csv"
            },
            timeout=15
        )
        
        if response.status_code != 200:
            return log_result(
                "Export CSV format", 
                False, 
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        # Check Content-Type
        content_type = response.headers.get("Content-Type", "")
        if "text/csv" not in content_type:
            return log_result(
                "Export CSV format", 
                False, 
                f"Expected Content-Type: text/csv, got: {content_type}"
            )
        
        # Check Content-Disposition header
        content_disposition = response.headers.get("Content-Disposition", "")
        if not content_disposition:
            return log_result("Export CSV format", False, "Missing Content-Disposition header")
        
        if "attachment" not in content_disposition:
            return log_result(
                "Export CSV format", 
                False, 
                f"Content-Disposition should contain 'attachment', got: {content_disposition}"
            )
        
        if ".csv" not in content_disposition:
            return log_result(
                "Export CSV format", 
                False, 
                f"Content-Disposition should contain '.csv', got: {content_disposition}"
            )
        
        # Verify CSV content
        content = response.text
        if not content:
            return log_result("Export CSV format", False, "Empty CSV content")
        
        # Check for CSV header
        lines = content.split("\n")
        if len(lines) < 2:
            return log_result("Export CSV format", False, "CSV has less than 2 lines (no data)")
        
        # Verify header contains expected columns
        header = lines[0].lower()
        if "section" not in header or "item" not in header or "value" not in header:
            return log_result(
                "Export CSV format", 
                False, 
                f"CSV header missing expected columns. Got: {lines[0]}"
            )
        
        return log_result(
            "Export CSV format", 
            True, 
            f"Downloadable CSV with {len(lines)} lines, Content-Disposition: {content_disposition}"
        )
        
    except Exception as e:
        return log_result("Export CSV format", False, f"Exception: {str(e)}")


def test_invalid_export_format():
    """Test 5: invalid export format returns 400 with ai_enterprise_invalid_export_format"""
    print("\n=== Test 5: Invalid Export Format ===")
    
    if not workspace_id:
        return log_result("Invalid export format", False, "No workspace_id available")
    
    # Use a fresh guest user to avoid hitting the free tier export limit
    fresh_guest_id = f"user_test_{uuid.uuid4().hex[:16]}"
    
    # First, create a workspace for this fresh user
    print("Creating workspace for fresh guest user...")
    try:
        create_payload = {
            "title": f"Invalid Format Test {uuid.uuid4().hex[:8]}",
            "context": "Testing invalid export format",
            "focus": "operations",
            "fallback_user_id": fresh_guest_id
        }
        
        create_response = requests.post(
            f"{API_BASE}/ai-enterprise/workspaces/create",
            json=create_payload,
            timeout=15
        )
        
        if create_response.status_code != 200:
            return log_result("Invalid export format", False, f"Failed to create workspace: {create_response.status_code}")
        
        fresh_workspace_id = create_response.json()["workspace"]["workspace_id"]
        
    except Exception as e:
        return log_result("Invalid export format", False, f"Setup failed: {str(e)}")
    
    try:
        response = requests.get(
            f"{API_BASE}/ai-enterprise/workspaces/{fresh_workspace_id}/export",
            params={
                "fallback_user_id": fresh_guest_id,
                "format": "xml"  # Invalid format
            },
            timeout=15
        )
        
        if response.status_code != 400:
            return log_result(
                "Invalid export format", 
                False, 
                f"Expected 400, got {response.status_code}"
            )
        
        data = response.json()
        
        # Check for error_code
        detail = data.get("detail", {})
        if isinstance(detail, str):
            # FastAPI might return detail as string
            return log_result(
                "Invalid export format", 
                False, 
                f"Expected structured error with error_code, got string: {detail}"
            )
        
        error_code = detail.get("error_code")
        if error_code != "ai_enterprise_invalid_export_format":
            return log_result(
                "Invalid export format", 
                False, 
                f"Expected error_code 'ai_enterprise_invalid_export_format', got: {error_code}"
            )
        
        message = detail.get("message", "")
        if "payload" not in message.lower() or "json" not in message.lower() or "csv" not in message.lower():
            return log_result(
                "Invalid export format", 
                False, 
                f"Error message should mention valid formats (payload, json, csv). Got: {message}"
            )
        
        return log_result(
            "Invalid export format", 
            True, 
            f"Correct 400 error with error_code: {error_code}"
        )
        
    except Exception as e:
        return log_result("Invalid export format", False, f"Exception: {str(e)}")


def test_free_tier_export_cap():
    """Test 6: free-tier export/day cap still enforced"""
    print("\n=== Test 6: Free-Tier Export Cap ===")
    
    if not workspace_id:
        return log_result("Free-tier export cap", False, "No workspace_id available")
    
    # Free tier allows 1 export per day
    # We've already done 3 exports (payload, json, csv), so the 4th should fail
    
    try:
        # Try to export again (should hit limit)
        response = requests.get(
            f"{API_BASE}/ai-enterprise/workspaces/{workspace_id}/export",
            params={
                "fallback_user_id": GUEST_USER_ID,
                "format": "payload"
            },
            timeout=15
        )
        
        # Should get 429 (Too Many Requests) for hitting the limit
        if response.status_code != 429:
            return log_result(
                "Free-tier export cap", 
                False, 
                f"Expected 429 (rate limit), got {response.status_code}. Free tier should limit exports to 1/day"
            )
        
        data = response.json()
        detail = data.get("detail", {})
        
        if isinstance(detail, str):
            return log_result(
                "Free-tier export cap", 
                False, 
                f"Expected structured error with error_code, got string: {detail}"
            )
        
        error_code = detail.get("error_code")
        if error_code != "ai_enterprise_export_limit_reached":
            return log_result(
                "Free-tier export cap", 
                False, 
                f"Expected error_code 'ai_enterprise_export_limit_reached', got: {error_code}"
            )
        
        # Verify limit information
        current_usage = detail.get("current_usage")
        limit = detail.get("limit")
        
        if current_usage is None or limit is None:
            return log_result(
                "Free-tier export cap", 
                False, 
                f"Missing usage info. current_usage: {current_usage}, limit: {limit}"
            )
        
        if limit != 1:
            return log_result(
                "Free-tier export cap", 
                False, 
                f"Free tier export limit should be 1, got: {limit}"
            )
        
        return log_result(
            "Free-tier export cap", 
            True, 
            f"Export cap enforced: {current_usage}/{limit} exports used"
        )
        
    except Exception as e:
        return log_result("Free-tier export cap", False, f"Exception: {str(e)}")


def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    print(f"\nTotal: {total} tests")
    print(f"Passed: {passed} tests")
    print(f"Failed: {total - passed} tests")
    
    if total - passed > 0:
        print("\n❌ FAILED TESTS:")
        for r in test_results:
            if not r["passed"]:
                print(f"  - {r['test']}: {r['details']}")
    
    print("\n" + "="*60)
    
    if passed == total:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ {total - passed} TEST(S) FAILED")
    
    print("="*60)
    
    return passed == total


def main():
    """Run all tests"""
    print("="*60)
    print("Feature 18: Export Format Validation")
    print("Base URL:", BASE_URL)
    print("Guest User ID:", GUEST_USER_ID)
    print("="*60)
    
    # Run tests in sequence
    test_workspace_create_and_run()
    test_export_payload_mode()
    test_export_json_format()
    test_export_csv_format()
    test_invalid_export_format()
    test_free_tier_export_cap()
    
    # Print summary
    all_passed = print_summary()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
