"""
Feature 20 - Lexicon Intelligence Hub Backend API Tests
Testing all word-forge endpoints with authenticated admin flow
"""

import requests
import json
import os
import sys

# Configuration
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_test(name, status, details=""):
    """Log test result"""
    if status == "PASS":
        test_results["passed"].append({"name": name, "details": details})
        print(f"✅ PASS: {name}")
        if details:
            print(f"   {details}")
    elif status == "FAIL":
        test_results["failed"].append({"name": name, "details": details})
        print(f"❌ FAIL: {name}")
        if details:
            print(f"   {details}")
    elif status == "WARN":
        test_results["warnings"].append({"name": name, "details": details})
        print(f"⚠️  WARN: {name}")
        if details:
            print(f"   {details}")

def login_admin():
    """Login as admin and return session"""
    print("\n" + "="*80)
    print("AUTHENTICATION")
    print("="*80)
    
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    })
    
    try:
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            user_data = response.json()
            log_test("Admin Login", "PASS", f"Logged in as {ADMIN_EMAIL}")
            return session, user_data
        else:
            log_test("Admin Login", "FAIL", f"Status {response.status_code}: {response.text[:200]}")
            return None, None
    except Exception as e:
        log_test("Admin Login", "FAIL", f"Exception: {str(e)}")
        return None, None

def test_health_endpoint(session):
    """Test GET /api/word-forge/health"""
    print("\n" + "="*80)
    print("TEST: Health Endpoint")
    print("="*80)
    
    try:
        response = session.get(f"{BASE_URL}/api/word-forge/health")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy" and data.get("feature_id") == "lexicon-intelligence":
                log_test("GET /api/word-forge/health", "PASS", 
                        f"Status: {data.get('status')}, Feature: {data.get('feature')}")
            else:
                log_test("GET /api/word-forge/health", "FAIL", 
                        f"Unexpected response: {json.dumps(data, indent=2)[:200]}")
        else:
            log_test("GET /api/word-forge/health", "FAIL", 
                    f"Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_test("GET /api/word-forge/health", "FAIL", f"Exception: {str(e)}")

def test_bootstrap_endpoint(session):
    """Test GET /api/word-forge/bootstrap"""
    print("\n" + "="*80)
    print("TEST: Bootstrap Endpoint")
    print("="*80)
    
    try:
        response = session.get(f"{BASE_URL}/api/word-forge/bootstrap")
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["plan", "scope_label", "limits", "daily_word", "saved_words", 
                             "profile", "usage_summary", "capabilities"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if not missing_fields:
                daily_word = data.get("daily_word", {})
                log_test("GET /api/word-forge/bootstrap", "PASS", 
                        f"Plan: {data.get('plan')}, Word: {daily_word.get('word', 'N/A')}")
            else:
                log_test("GET /api/word-forge/bootstrap", "FAIL", 
                        f"Missing fields: {', '.join(missing_fields)}")
        else:
            log_test("GET /api/word-forge/bootstrap", "FAIL", 
                    f"Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_test("GET /api/word-forge/bootstrap", "FAIL", f"Exception: {str(e)}")

def test_templates_endpoints(session):
    """Test template library endpoints"""
    print("\n" + "="*80)
    print("TEST: Template Library Endpoints")
    print("="*80)
    
    # Test GET /api/word-forge/templates
    try:
        response = session.get(f"{BASE_URL}/api/word-forge/templates")
        
        if response.status_code == 200:
            data = response.json()
            if "templates" in data and isinstance(data["templates"], list):
                template_count = len(data["templates"])
                log_test("GET /api/word-forge/templates", "PASS", 
                        f"Found {template_count} templates")
                
                # Test POST /api/word-forge/templates/apply if templates exist
                if data["templates"]:
                    template_id = data["templates"][0].get("template_id")
                    try:
                        apply_response = session.post(f"{BASE_URL}/api/word-forge/templates/apply", 
                                                     json={"template_id": template_id})
                        
                        if apply_response.status_code == 200:
                            apply_data = apply_response.json()
                            if apply_data.get("status") == "applied":
                                log_test("POST /api/word-forge/templates/apply", "PASS", 
                                        f"Applied template: {template_id}")
                            else:
                                log_test("POST /api/word-forge/templates/apply", "FAIL", 
                                        f"Unexpected status: {apply_data.get('status')}")
                        else:
                            log_test("POST /api/word-forge/templates/apply", "FAIL", 
                                    f"Status {apply_response.status_code}: {apply_response.text[:200]}")
                    except Exception as e:
                        log_test("POST /api/word-forge/templates/apply", "FAIL", f"Exception: {str(e)}")
                else:
                    log_test("POST /api/word-forge/templates/apply", "WARN", "No templates to test apply")
            else:
                log_test("GET /api/word-forge/templates", "FAIL", "Missing or invalid templates field")
        else:
            log_test("GET /api/word-forge/templates", "FAIL", 
                    f"Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_test("GET /api/word-forge/templates", "FAIL", f"Exception: {str(e)}")

def test_batch_endpoints(session):
    """Test batch workflow endpoints"""
    print("\n" + "="*80)
    print("TEST: Batch Workflow Endpoints")
    print("="*80)
    
    # Test POST /api/word-forge/batch/generate
    try:
        response = session.post(f"{BASE_URL}/api/word-forge/batch/generate", 
                               json={"domains": ["business", "leadership"], "difficulty": "adaptive"})
        
        if response.status_code == 200:
            data = response.json()
            # Check for ObjectId serialization errors
            response_text = response.text
            if "_id" in response_text and "ObjectId" in response_text:
                log_test("POST /api/word-forge/batch/generate", "FAIL", 
                        "ObjectId serialization error detected in response")
            elif "status" in data:
                log_test("POST /api/word-forge/batch/generate", "PASS", 
                        f"Status: {data.get('status')}, Words: {len(data.get('words', []))}")
            else:
                log_test("POST /api/word-forge/batch/generate", "FAIL", 
                        f"Missing status field: {json.dumps(data, indent=2)[:200]}")
        elif response.status_code == 429:
            log_test("POST /api/word-forge/batch/generate", "WARN", 
                    "Rate limited (expected for some plans)")
        else:
            log_test("POST /api/word-forge/batch/generate", "FAIL", 
                    f"Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_test("POST /api/word-forge/batch/generate", "FAIL", f"Exception: {str(e)}")
    
    # Test GET /api/word-forge/batch/jobs
    try:
        response = session.get(f"{BASE_URL}/api/word-forge/batch/jobs")
        
        if response.status_code == 200:
            data = response.json()
            if "jobs" in data and isinstance(data["jobs"], list):
                log_test("GET /api/word-forge/batch/jobs", "PASS", 
                        f"Found {len(data['jobs'])} batch jobs")
            else:
                log_test("GET /api/word-forge/batch/jobs", "FAIL", "Missing or invalid jobs field")
        else:
            log_test("GET /api/word-forge/batch/jobs", "FAIL", 
                    f"Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_test("GET /api/word-forge/batch/jobs", "FAIL", f"Exception: {str(e)}")

def test_snapshot_endpoints(session):
    """Test snapshot workflow endpoints"""
    print("\n" + "="*80)
    print("TEST: Snapshot Workflow Endpoints")
    print("="*80)
    
    # Test POST /api/word-forge/snapshots
    try:
        import uuid
        snapshot_name = f"Test Snapshot {uuid.uuid4().hex[:8]}"
        response = session.post(f"{BASE_URL}/api/word-forge/snapshots", 
                               json={"name": snapshot_name, "include_saved_words": True, 
                                    "include_leaderboard": False})
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "created":
                log_test("POST /api/word-forge/snapshots", "PASS", 
                        f"Created snapshot: {snapshot_name}")
            else:
                log_test("POST /api/word-forge/snapshots", "FAIL", 
                        f"Unexpected status: {data.get('status')}")
        elif response.status_code == 429:
            log_test("POST /api/word-forge/snapshots", "WARN", 
                    "Rate limited (expected for some plans)")
        else:
            log_test("POST /api/word-forge/snapshots", "FAIL", 
                    f"Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_test("POST /api/word-forge/snapshots", "FAIL", f"Exception: {str(e)}")
    
    # Test GET /api/word-forge/snapshots
    try:
        response = session.get(f"{BASE_URL}/api/word-forge/snapshots")
        
        if response.status_code == 200:
            data = response.json()
            if "snapshots" in data and isinstance(data["snapshots"], list):
                snapshot_count = len(data["snapshots"])
                log_test("GET /api/word-forge/snapshots", "PASS", 
                        f"Found {snapshot_count} snapshots")
                
                # Test POST /api/word-forge/snapshots/restore if snapshots exist
                if data["snapshots"]:
                    snapshot_id = data["snapshots"][0].get("snapshot_id")
                    try:
                        restore_response = session.post(f"{BASE_URL}/api/word-forge/snapshots/restore", 
                                                       json={"snapshot_id": snapshot_id})
                        
                        if restore_response.status_code == 200:
                            restore_data = restore_response.json()
                            if restore_data.get("status") == "restored":
                                log_test("POST /api/word-forge/snapshots/restore", "PASS", 
                                        f"Restored snapshot: {snapshot_id}")
                            else:
                                log_test("POST /api/word-forge/snapshots/restore", "FAIL", 
                                        f"Unexpected status: {restore_data.get('status')}")
                        else:
                            log_test("POST /api/word-forge/snapshots/restore", "FAIL", 
                                    f"Status {restore_response.status_code}: {restore_response.text[:200]}")
                    except Exception as e:
                        log_test("POST /api/word-forge/snapshots/restore", "FAIL", f"Exception: {str(e)}")
                else:
                    log_test("POST /api/word-forge/snapshots/restore", "WARN", "No snapshots to test restore")
            else:
                log_test("GET /api/word-forge/snapshots", "FAIL", "Missing or invalid snapshots field")
        else:
            log_test("GET /api/word-forge/snapshots", "FAIL", 
                    f"Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_test("GET /api/word-forge/snapshots", "FAIL", f"Exception: {str(e)}")

def test_recommendations_endpoint(session):
    """Test GET /api/word-forge/recommendations"""
    print("\n" + "="*80)
    print("TEST: Recommendations Endpoint")
    print("="*80)
    
    try:
        response = session.get(f"{BASE_URL}/api/word-forge/recommendations")
        
        if response.status_code == 200:
            data = response.json()
            if "recommendations" in data and isinstance(data["recommendations"], list):
                log_test("GET /api/word-forge/recommendations", "PASS", 
                        f"Found {len(data['recommendations'])} recommendations")
            else:
                log_test("GET /api/word-forge/recommendations", "FAIL", 
                        "Missing or invalid recommendations field")
        else:
            log_test("GET /api/word-forge/recommendations", "FAIL", 
                    f"Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_test("GET /api/word-forge/recommendations", "FAIL", f"Exception: {str(e)}")

def test_export_endpoints(session):
    """Test export center endpoints"""
    print("\n" + "="*80)
    print("TEST: Export Center Endpoints")
    print("="*80)
    
    # Test GET /api/word-forge/export?format=payload
    try:
        response = session.get(f"{BASE_URL}/api/word-forge/export", params={"format": "payload"})
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["feature_id", "plan", "profile", "summary"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if not missing_fields:
                log_test("GET /api/word-forge/export?format=payload", "PASS", 
                        f"Plan: {data.get('plan')}, Saved words: {data.get('summary', {}).get('saved_words_count', 0)}")
            else:
                log_test("GET /api/word-forge/export?format=payload", "FAIL", 
                        f"Missing fields: {', '.join(missing_fields)}")
        else:
            log_test("GET /api/word-forge/export?format=payload", "FAIL", 
                    f"Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_test("GET /api/word-forge/export?format=payload", "FAIL", f"Exception: {str(e)}")
    
    # Test GET /api/word-forge/export?format=json
    try:
        response = session.get(f"{BASE_URL}/api/word-forge/export", params={"format": "json"})
        
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_disp = response.headers.get("content-disposition", "")
            
            if "application/json" in content_type or "attachment" in content_disp.lower():
                log_test("GET /api/word-forge/export?format=json", "PASS", 
                        f"Content-Type: {content_type}")
            else:
                log_test("GET /api/word-forge/export?format=json", "FAIL", 
                        f"Unexpected content type: {content_type}")
        else:
            log_test("GET /api/word-forge/export?format=json", "FAIL", 
                    f"Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_test("GET /api/word-forge/export?format=json", "FAIL", f"Exception: {str(e)}")
    
    # Test GET /api/word-forge/export?format=csv
    try:
        response = session.get(f"{BASE_URL}/api/word-forge/export", params={"format": "csv"})
        
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_disp = response.headers.get("content-disposition", "")
            
            if "text/csv" in content_type or "attachment" in content_disp.lower():
                log_test("GET /api/word-forge/export?format=csv", "PASS", 
                        f"Content-Type: {content_type}")
            else:
                log_test("GET /api/word-forge/export?format=csv", "FAIL", 
                        f"Unexpected content type: {content_type}")
        else:
            log_test("GET /api/word-forge/export?format=csv", "FAIL", 
                    f"Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log_test("GET /api/word-forge/export?format=csv", "FAIL", f"Exception: {str(e)}")

def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_tests = len(test_results["passed"]) + len(test_results["failed"]) + len(test_results["warnings"])
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    
    if test_results["failed"]:
        print("\n" + "="*80)
        print("FAILED TESTS")
        print("="*80)
        for test in test_results["failed"]:
            print(f"\n❌ {test['name']}")
            if test['details']:
                print(f"   {test['details']}")
    
    if test_results["warnings"]:
        print("\n" + "="*80)
        print("WARNINGS")
        print("="*80)
        for test in test_results["warnings"]:
            print(f"\n⚠️  {test['name']}")
            if test['details']:
                print(f"   {test['details']}")
    
    print("\n" + "="*80)
    
    # Return exit code
    return 0 if not test_results["failed"] else 1

def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("Feature 20 - Lexicon Intelligence Hub Backend API Tests")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Admin Email: {ADMIN_EMAIL}")
    
    # Login
    session, user_data = login_admin()
    if not session:
        print("\n❌ CRITICAL: Failed to authenticate. Cannot proceed with tests.")
        return 1
    
    # Run all tests
    test_health_endpoint(session)
    test_bootstrap_endpoint(session)
    test_templates_endpoints(session)
    test_batch_endpoints(session)
    test_snapshot_endpoints(session)
    test_recommendations_endpoint(session)
    test_export_endpoints(session)
    
    # Print summary and return exit code
    return print_summary()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
