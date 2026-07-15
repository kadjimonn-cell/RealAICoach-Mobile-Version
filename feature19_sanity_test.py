"""Feature 19 Bill Generator - P0 Closure Sanity Verification

Test Scope (as per review request):
1. GET /api/bill-generator/health - should return healthy and feature_number 19
2. GET /api/bill-generator/bootstrap with guest fallback_user_id - should return workspace payload (no 500)
3. GET /api/bill-generator/export?format=json with fallback_user_id - should work
4. GET /api/bill-generator/export?format=csv with fallback_user_id - should work
5. GET /api/bill-generator/export?format=payload with fallback_user_id - should work
"""

import os
import requests

# Get backend URL from environment
BASE_URL = str(os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
if not BASE_URL:
    raise RuntimeError("REACT_APP_BACKEND_URL is required")

API_BASE = f"{BASE_URL}/api"

# Guest ID for testing (valid pattern: user_<12-80 alphanumeric chars>)
GUEST_ID = "user_test_feature19_sanity"

# Test results
results = {"total": 0, "passed": 0, "failed": 0, "details": []}


def log_result(test_name: str, passed: bool, detail: str = ""):
    """Log test result"""
    results["total"] += 1
    if passed:
        results["passed"] += 1
        status = "✅ PASS"
    else:
        results["failed"] += 1
        status = "❌ FAIL"
    
    results["details"].append(f"{status}: {test_name}")
    if detail:
        results["details"].append(f"   {detail}")
    
    print(f"{status}: {test_name}")
    if detail:
        print(f"   {detail}")


def test_health_endpoint():
    """Test 1: GET /api/bill-generator/health"""
    print("\n=== Test 1: Health Endpoint ===")
    
    try:
        resp = requests.get(f"{API_BASE}/bill-generator/health", timeout=10)
        
        if resp.status_code != 200:
            log_result(
                "Health endpoint status code",
                False,
                f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
            )
            return
        
        log_result("Health endpoint status code", True, "200 OK")
        
        data = resp.json()
        
        # Check status=healthy
        if data.get("status") == "healthy":
            log_result("Health status=healthy", True)
        else:
            log_result("Health status=healthy", False, f"Got: {data.get('status')}")
        
        # Check feature_number=19
        if data.get("feature_number") == 19:
            log_result("Health feature_number=19", True)
        else:
            log_result("Health feature_number=19", False, f"Got: {data.get('feature_number')}")
        
    except Exception as e:
        log_result("Health endpoint", False, f"Exception: {str(e)}")


def test_bootstrap_guest():
    """Test 2: GET /api/bill-generator/bootstrap with guest fallback_user_id"""
    print("\n=== Test 2: Bootstrap with Guest Fallback ===")
    
    try:
        resp = requests.get(
            f"{API_BASE}/bill-generator/bootstrap",
            params={"fallback_user_id": GUEST_ID},
            timeout=10
        )
        
        if resp.status_code != 200:
            log_result(
                "Bootstrap guest status code",
                False,
                f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
            )
            return
        
        log_result("Bootstrap guest status code", True, "200 OK (no 500)")
        
        data = resp.json()
        
        # Check workspace payload structure
        required_fields = ["plan", "limits", "clients", "bills", "insights"]
        missing_fields = [f for f in required_fields if f not in data]
        
        if not missing_fields:
            log_result("Bootstrap workspace payload structure", True, f"All required fields present")
        else:
            log_result(
                "Bootstrap workspace payload structure",
                False,
                f"Missing fields: {', '.join(missing_fields)}"
            )
        
    except Exception as e:
        log_result("Bootstrap guest", False, f"Exception: {str(e)}")


def test_export_json():
    """Test 3: GET /api/bill-generator/export?format=json"""
    print("\n=== Test 3: Export format=json ===")
    
    try:
        resp = requests.get(
            f"{API_BASE}/bill-generator/export",
            params={"format": "json", "fallback_user_id": GUEST_ID},
            timeout=10
        )
        
        if resp.status_code != 200:
            log_result(
                "Export format=json status code",
                False,
                f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
            )
            return
        
        log_result("Export format=json status code", True, "200 OK")
        
        data = resp.json()
        
        # Check basic structure
        if "export_format" in data and data.get("export_format") == "json":
            log_result("Export format=json structure", True, "Valid JSON export")
        else:
            log_result("Export format=json structure", False, f"Invalid structure")
        
    except Exception as e:
        log_result("Export format=json", False, f"Exception: {str(e)}")


def test_export_csv():
    """Test 4: GET /api/bill-generator/export?format=csv"""
    print("\n=== Test 4: Export format=csv ===")
    
    try:
        resp = requests.get(
            f"{API_BASE}/bill-generator/export",
            params={"format": "csv", "fallback_user_id": GUEST_ID},
            timeout=10
        )
        
        if resp.status_code != 200:
            log_result(
                "Export format=csv status code",
                False,
                f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
            )
            return
        
        log_result("Export format=csv status code", True, "200 OK")
        
        # Check content type
        content_type = resp.headers.get("content-type", "")
        if "text/csv" in content_type:
            log_result("Export format=csv content-type", True, f"text/csv")
        else:
            log_result("Export format=csv content-type", False, f"Got: {content_type}")
        
    except Exception as e:
        log_result("Export format=csv", False, f"Exception: {str(e)}")


def test_export_payload():
    """Test 5: GET /api/bill-generator/export?format=payload"""
    print("\n=== Test 5: Export format=payload ===")
    
    try:
        resp = requests.get(
            f"{API_BASE}/bill-generator/export",
            params={"format": "payload", "fallback_user_id": GUEST_ID},
            timeout=10
        )
        
        if resp.status_code != 200:
            log_result(
                "Export format=payload status code",
                False,
                f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
            )
            return
        
        log_result("Export format=payload status code", True, "200 OK")
        
        data = resp.json()
        
        # Check basic structure
        if "export_format" in data and data.get("export_format") == "payload":
            log_result("Export format=payload structure", True, "Valid payload export")
        else:
            log_result("Export format=payload structure", False, f"Invalid structure")
        
    except Exception as e:
        log_result("Export format=payload", False, f"Exception: {str(e)}")


def print_summary():
    """Print test summary"""
    print("\n" + "=" * 80)
    print("FEATURE 19 BILL GENERATOR - P0 CLOSURE SANITY VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Backend URL: {BASE_URL}")
    print(f"Total Tests: {results['total']}")
    print(f"✅ Passed:   {results['passed']}")
    print(f"❌ Failed:   {results['failed']}")
    
    if results["failed"] == 0:
        print("\n🎉 ALL TESTS PASSED - P0 CLOSURE VERIFIED")
    else:
        print(f"\n⚠️  {results['failed']} TEST(S) FAILED - NEEDS ATTENTION")
    
    print("=" * 80 + "\n")


if __name__ == "__main__":
    print("=" * 80)
    print("Feature 19 Bill Generator - P0 Closure Sanity Verification")
    print("=" * 80)
    print(f"Backend URL: {BASE_URL}")
    print(f"Guest ID: {GUEST_ID}")
    print("=" * 80)
    
    # Run all tests
    test_health_endpoint()
    test_bootstrap_guest()
    test_export_json()
    test_export_csv()
    test_export_payload()
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    exit(0 if results["failed"] == 0 else 1)
