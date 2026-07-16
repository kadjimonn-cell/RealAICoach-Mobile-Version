"""Backend test for global PDF v15 runtime inheritance verification."""

import requests
import sys
from io import BytesIO
from pypdf import PdfReader

# Test configuration
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
USER_EMAIL = "fedapay.prod.notify.done.2f8da905@gmail.com"
USER_PASSWORD = "FedapayLive#2026Aa!"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

# Expected markers in PDF content
EXPECTED_MARKERS = [
    "RealAICoach PDF v15",
    "GLOBAL PDF V15 POLICY ACTIVE",
    "Global PDF v15 enterprise runtime stamp",
]

# Marker that should NOT be present
FORBIDDEN_MARKER = "ENFORCED: GLOBAL PDF V15 VISUAL POLICY"


def login(email: str, password: str) -> tuple[requests.Session, dict]:
    """Login and return session with cookies."""
    session = requests.Session()
    
    # Login
    login_url = f"{BASE_URL}/api/auth/login"
    login_data = {"email": email, "password": password}
    
    print(f"  → Logging in as {email}...")
    response = session.post(login_url, json=login_data)
    
    if response.status_code != 200:
        print(f"  ✗ Login failed: {response.status_code}")
        print(f"    Response: {response.text[:200]}")
        return session, {"success": False, "error": f"Login failed: {response.status_code}"}
    
    result = response.json()
    
    # Check if we got a user_id (successful login)
    if not result.get("user_id"):
        print(f"  ✗ Login failed: {result.get('message', 'No user_id in response')}")
        return session, {"success": False, "error": result.get("message", "No user_id in response")}
    
    print(f"  ✓ Login successful - User: {result.get('name', 'Unknown')}")
    return session, {"success": True, "user": result}


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract all text from PDF."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"ERROR_EXTRACTING_TEXT: {str(e)}"


def verify_pdf_markers(pdf_bytes: bytes, endpoint: str) -> dict:
    """Verify PDF contains expected markers and doesn't contain forbidden markers."""
    print(f"\n  → Verifying PDF content for {endpoint}...")
    
    # Extract text from PDF
    pdf_text = extract_pdf_text(pdf_bytes)
    
    if pdf_text.startswith("ERROR_EXTRACTING_TEXT"):
        print(f"  ✗ Failed to extract PDF text: {pdf_text}")
        return {
            "success": False,
            "endpoint": endpoint,
            "error": pdf_text,
            "markers_found": [],
            "markers_missing": EXPECTED_MARKERS,
            "forbidden_marker_present": False,
        }
    
    # Check for expected markers
    markers_found = []
    markers_missing = []
    
    for marker in EXPECTED_MARKERS:
        if marker in pdf_text:
            markers_found.append(marker)
            print(f"  ✓ Found: '{marker}'")
        else:
            markers_missing.append(marker)
            print(f"  ✗ Missing: '{marker}'")
    
    # Check for forbidden marker
    forbidden_present = FORBIDDEN_MARKER in pdf_text
    if forbidden_present:
        print(f"  ✗ Forbidden marker present: '{FORBIDDEN_MARKER}'")
    else:
        print(f"  ✓ Forbidden marker absent: '{FORBIDDEN_MARKER}'")
    
    success = len(markers_missing) == 0 and not forbidden_present
    
    return {
        "success": success,
        "endpoint": endpoint,
        "markers_found": markers_found,
        "markers_missing": markers_missing,
        "forbidden_marker_present": forbidden_present,
        "pdf_text_length": len(pdf_text),
    }


def test_pdf_endpoint(session: requests.Session, endpoint: str, params: dict = None) -> dict:
    """Test a PDF endpoint and verify content."""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n→ Testing endpoint: {endpoint}")
    if params:
        print(f"  Parameters: {params}")
    
    try:
        response = session.get(url, params=params)
        
        # Check status code
        if response.status_code != 200:
            print(f"  ✗ Request failed: {response.status_code}")
            print(f"    Response: {response.text[:200]}")
            return {
                "success": False,
                "endpoint": endpoint,
                "error": f"HTTP {response.status_code}",
                "response_text": response.text[:500],
            }
        
        # Check content type
        content_type = response.headers.get("Content-Type", "")
        if "application/pdf" not in content_type:
            print(f"  ✗ Wrong content type: {content_type}")
            return {
                "success": False,
                "endpoint": endpoint,
                "error": f"Expected application/pdf, got {content_type}",
                "content_type": content_type,
            }
        
        print(f"  ✓ Content-Type: {content_type}")
        
        # Get PDF bytes
        pdf_bytes = response.content
        print(f"  ✓ PDF size: {len(pdf_bytes)} bytes")
        
        # Verify PDF markers
        verification = verify_pdf_markers(pdf_bytes, endpoint)
        
        return verification
        
    except Exception as e:
        print(f"  ✗ Exception: {str(e)}")
        return {
            "success": False,
            "endpoint": endpoint,
            "error": f"Exception: {str(e)}",
        }


def main():
    """Run all PDF v15 verification tests."""
    print("=" * 80)
    print("Global PDF v15 Runtime Inheritance Verification")
    print("=" * 80)
    
    results = []
    
    # Test 1: User login and WCAG report PDF
    print("\n" + "=" * 80)
    print("TEST 1: User - WCAG Report PDF")
    print("=" * 80)
    
    user_session, login_result = login(USER_EMAIL, USER_PASSWORD)
    if not login_result.get("success"):
        print("\n✗ User login failed, cannot proceed with user tests")
        results.append({
            "test": "User Login",
            "success": False,
            "error": login_result.get("error"),
        })
    else:
        # Test WCAG report PDF
        wcag_result = test_pdf_endpoint(user_session, "/api/accessibility/wcag-report/pdf")
        results.append({
            "test": "User - WCAG Report PDF",
            **wcag_result,
        })
    
    # Test 2: User - Tax Statement PDF
    print("\n" + "=" * 80)
    print("TEST 2: User - Tax Statement PDF")
    print("=" * 80)
    
    if login_result.get("success"):
        tax_result = test_pdf_endpoint(
            user_session,
            "/api/payments/tax-statement/pdf",
            params={"scope": "monthly", "year": 2026, "month": 5}
        )
        results.append({
            "test": "User - Tax Statement PDF",
            **tax_result,
        })
    
    # Test 3: Admin login and Audit Log PDF
    print("\n" + "=" * 80)
    print("TEST 3: Admin - Audit Log Export PDF")
    print("=" * 80)
    
    admin_session, admin_login_result = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not admin_login_result.get("success"):
        print("\n✗ Admin login failed, cannot proceed with admin tests")
        results.append({
            "test": "Admin Login",
            "success": False,
            "error": admin_login_result.get("error"),
        })
    else:
        # Test Audit Log PDF
        audit_result = test_pdf_endpoint(admin_session, "/api/admin/data/audit-log/export/pdf")
        results.append({
            "test": "Admin - Audit Log Export PDF",
            **audit_result,
        })
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.get("success"))
    failed_tests = total_tests - passed_tests
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    print("\n" + "-" * 80)
    print("Detailed Results:")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        test_name = result.get("test", "Unknown")
        success = result.get("success", False)
        status = "✓ PASS" if success else "✗ FAIL"
        
        print(f"\n{i}. {test_name}: {status}")
        
        if success:
            endpoint = result.get("endpoint", "N/A")
            markers_found = result.get("markers_found", [])
            print(f"   Endpoint: {endpoint}")
            print(f"   Markers found: {len(markers_found)}/{len(EXPECTED_MARKERS)}")
            for marker in markers_found:
                print(f"     ✓ {marker}")
            print(f"   Forbidden marker absent: ✓")
        else:
            error = result.get("error", "Unknown error")
            print(f"   Error: {error}")
            
            markers_missing = result.get("markers_missing", [])
            if markers_missing:
                print(f"   Missing markers:")
                for marker in markers_missing:
                    print(f"     ✗ {marker}")
            
            if result.get("forbidden_marker_present"):
                print(f"   ✗ Forbidden marker present: {FORBIDDEN_MARKER}")
    
    print("\n" + "=" * 80)
    
    # Exit with appropriate code
    if failed_tests > 0:
        print(f"\n✗ VERIFICATION FAILED: {failed_tests} test(s) failed")
        sys.exit(1)
    else:
        print("\n✓ VERIFICATION PASSED: All tests passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
