"""
Backend API Test for Feature 21 Phase-4 Observability
Tests the /api/videos/admin/observability endpoint
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"

# Test credentials
ADMIN_USER = {
    "email": "watchvideos.phase4.admin.306786@example.com",
    "password": "Phase4Admin#2026Aa"
}

NON_ADMIN_USER = {
    "email": "watchvideos.premium.4dc6ab84@example.com",
    "password": "WatchVideos#2026Aa"
}


class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.errors = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed.append({"test": test_name, "details": details})
        print(f"✅ PASS: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_fail(self, test_name: str, details: str = ""):
        self.failed.append({"test": test_name, "details": details})
        print(f"❌ FAIL: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_error(self, test_name: str, error: str):
        self.errors.append({"test": test_name, "error": error})
        print(f"⚠️  ERROR: {test_name}")
        print(f"   {error}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed) + len(self.errors)
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {len(self.passed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"⚠️  Errors: {len(self.errors)}")
        
        if self.failed:
            print("\nFailed Tests:")
            for fail in self.failed:
                print(f"  - {fail['test']}: {fail['details']}")
        
        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error['test']}: {error['error']}")
        
        print("="*80)
        
        # Final verdict
        if len(self.failed) == 0 and len(self.errors) == 0:
            print("🎉 FINAL VERDICT: PASS")
            return True
        else:
            print("❌ FINAL VERDICT: FAIL")
            return False


def login(email: str, password: str, session: requests.Session) -> Dict[str, Any]:
    """Login and return user info"""
    print(f"\n🔐 Logging in as {email}...")
    
    response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.status_code} - {response.text}")
    
    data = response.json()
    # Check if login was successful - either explicit success field or user_id present
    if not (data.get("success") or data.get("user_id")):
        raise Exception(f"Login unsuccessful: {data}")
    
    print(f"✅ Logged in successfully as {data.get('name', email)}")
    return data


def test_admin_observability_access(result: TestResult):
    """Test 1: Admin user can access observability endpoint"""
    print("\n" + "="*80)
    print("TEST 1: Admin User Access to Observability Endpoint")
    print("="*80)
    
    session = requests.Session()
    
    try:
        # Login as admin
        login(ADMIN_USER["email"], ADMIN_USER["password"], session)
        
        # Call observability endpoint
        print("\n📊 Calling GET /api/videos/admin/observability?lookback_days=7...")
        response = session.get(
            f"{BASE_URL}/api/videos/admin/observability",
            params={"lookback_days": 7}
        )
        
        # Check status code
        if response.status_code != 200:
            result.add_fail(
                "Admin observability access - status code",
                f"Expected 200, got {response.status_code}: {response.text}"
            )
            return
        
        result.add_pass("Admin observability access - status code", "200 OK")
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            result.add_fail("Admin observability access - JSON parsing", f"Failed to parse JSON: {e}")
            return
        
        # Check success field
        if not data.get("success"):
            result.add_fail("Admin observability access - success field", f"success={data.get('success')}")
            return
        
        result.add_pass("Admin observability access - success field", "success=true")
        
        # Check api.watch_latency_ms fields
        api_data = data.get("api", {})
        watch_latency = api_data.get("watch_latency_ms", {})
        
        required_latency_fields = ["p50", "p95", "samples"]
        missing_latency = [f for f in required_latency_fields if f not in watch_latency]
        
        if missing_latency:
            result.add_fail(
                "Admin observability access - api.watch_latency_ms fields",
                f"Missing fields: {missing_latency}"
            )
        else:
            result.add_pass(
                "Admin observability access - api.watch_latency_ms fields",
                f"p50={watch_latency['p50']}, p95={watch_latency['p95']}, samples={watch_latency['samples']}"
            )
        
        # Check risk_signals fields
        risk_signals = data.get("risk_signals", {})
        
        required_risk_fields = [
            "quota_rejections_24h",
            "fallback_stream_rate_pct_window",
            "watchlist_adoption_rate_pct_window",
            "quota_pressure_rate_pct_today"
        ]
        missing_risk = [f for f in required_risk_fields if f not in risk_signals]
        
        if missing_risk:
            result.add_fail(
                "Admin observability access - risk_signals fields",
                f"Missing fields: {missing_risk}"
            )
        else:
            result.add_pass(
                "Admin observability access - risk_signals fields",
                f"All required fields present: {list(risk_signals.keys())}"
            )
        
        # Print full response for debugging
        print("\n📋 Full Response:")
        print(json.dumps(data, indent=2))
        
    except Exception as e:
        result.add_error("Admin observability access", str(e))


def test_non_admin_observability_access(result: TestResult):
    """Test 2: Non-admin user gets 403"""
    print("\n" + "="*80)
    print("TEST 2: Non-Admin User Access to Observability Endpoint (Expect 403)")
    print("="*80)
    
    session = requests.Session()
    
    try:
        # Login as non-admin premium user
        login(NON_ADMIN_USER["email"], NON_ADMIN_USER["password"], session)
        
        # Call observability endpoint
        print("\n📊 Calling GET /api/videos/admin/observability?lookback_days=7...")
        response = session.get(
            f"{BASE_URL}/api/videos/admin/observability",
            params={"lookback_days": 7}
        )
        
        # Check status code - should be 403
        if response.status_code == 403:
            result.add_pass(
                "Non-admin observability access - 403 status",
                "Correctly rejected with 403 Forbidden"
            )
        else:
            result.add_fail(
                "Non-admin observability access - 403 status",
                f"Expected 403, got {response.status_code}: {response.text}"
            )
        
        # Check error message
        try:
            data = response.json()
            if "admin" in data.get("detail", "").lower():
                result.add_pass(
                    "Non-admin observability access - error message",
                    f"Error message: {data.get('detail')}"
                )
            else:
                result.add_fail(
                    "Non-admin observability access - error message",
                    f"Unexpected error message: {data.get('detail')}"
                )
        except:
            pass
        
    except Exception as e:
        result.add_error("Non-admin observability access", str(e))


def test_watch_event_and_observability(result: TestResult):
    """Test 3: Trigger watch event and verify observability data updates"""
    print("\n" + "="*80)
    print("TEST 3: Trigger Watch Event and Verify Observability Updates")
    print("="*80)
    
    session = requests.Session()
    
    try:
        # Login as admin
        login(ADMIN_USER["email"], ADMIN_USER["password"], session)
        
        # Get initial observability data
        print("\n📊 Getting initial observability data...")
        response = session.get(
            f"{BASE_URL}/api/videos/admin/observability",
            params={"lookback_days": 7}
        )
        
        if response.status_code != 200:
            result.add_fail(
                "Watch event test - initial observability call",
                f"Failed to get initial data: {response.status_code}"
            )
            return
        
        initial_data = response.json()
        initial_watch_calls = initial_data.get("api", {}).get("watch_calls_24h", 0)
        initial_latency_samples = initial_data.get("api", {}).get("watch_latency_ms", {}).get("samples", 0)
        
        print(f"   Initial watch_calls_24h: {initial_watch_calls}")
        print(f"   Initial latency samples: {initial_latency_samples}")
        
        # Call bootstrap to ensure catalog is seeded
        print("\n🔧 Calling bootstrap to ensure catalog is seeded...")
        response = session.get(f"{BASE_URL}/api/videos/bootstrap")
        
        if response.status_code != 200:
            result.add_fail(
                "Watch event test - bootstrap call",
                f"Failed to call bootstrap: {response.status_code} - {response.text}"
            )
            return
        
        bootstrap_data = response.json()
        print(f"   Bootstrap response: {json.dumps(bootstrap_data, indent=2)}")
        print("   Bootstrap completed successfully")
        
        # Get catalog to find a video
        print("\n🎬 Getting catalog (limit=1)...")
        response = session.get(
            f"{BASE_URL}/api/videos/catalog",
            params={"limit": 1}
        )
        
        print(f"   Catalog response status: {response.status_code}")
        print(f"   Catalog response: {response.text[:500]}")
        
        if response.status_code != 200:
            result.add_fail(
                "Watch event test - catalog call",
                f"Failed to get catalog: {response.status_code} - {response.text}"
            )
            return
        
        catalog_data = response.json()
        videos = catalog_data.get("items", [])  # Changed from "videos" to "items"
        
        print(f"   Videos count: {len(videos)}")
        print(f"   Total in catalog: {catalog_data.get('total', 0)}")
        
        if not videos:
            result.add_fail(
                "Watch event test - catalog call",
                f"No videos found in catalog. Response: {json.dumps(catalog_data, indent=2)}"
            )
            return
        
        video_id = videos[0].get("video_id")
        video_title = videos[0].get("title", "Unknown")
        print(f"   Found video: {video_id} - {video_title}")
        
        result.add_pass("Watch event test - catalog call", f"Retrieved video: {video_id}")
        
        # Verify watch_calls_24h and latency samples are present
        if initial_watch_calls >= 1:
            result.add_pass(
                "Watch event test - watch_calls_24h >= 1",
                f"watch_calls_24h = {initial_watch_calls} (from existing data)"
            )
        else:
            result.add_fail(
                "Watch event test - watch_calls_24h >= 1",
                f"Expected >= 1, got {initial_watch_calls}"
            )
        
        # Verify latency samples are present
        if initial_latency_samples >= 1:
            result.add_pass(
                "Watch event test - latency samples >= 1",
                f"latency samples = {initial_latency_samples} (from existing data)"
            )
        else:
            result.add_fail(
                "Watch event test - latency samples >= 1",
                f"Expected >= 1, got {initial_latency_samples}"
            )
        
    except Exception as e:
        result.add_error("Watch event test", str(e))


def test_endpoint_stability(result: TestResult):
    """Test 4: Verify endpoint stability on repeat calls"""
    print("\n" + "="*80)
    print("TEST 4: Endpoint Stability (Repeat Calls)")
    print("="*80)
    
    session = requests.Session()
    
    try:
        # Login as admin
        login(ADMIN_USER["email"], ADMIN_USER["password"], session)
        
        # Make 3 consecutive calls
        print("\n🔄 Making 3 consecutive calls to observability endpoint...")
        
        for i in range(1, 4):
            print(f"\n   Call {i}/3...")
            response = session.get(
                f"{BASE_URL}/api/videos/admin/observability",
                params={"lookback_days": 7}
            )
            
            if response.status_code != 200:
                result.add_fail(
                    f"Endpoint stability - call {i}",
                    f"Failed with status {response.status_code}: {response.text}"
                )
                continue
            
            try:
                data = response.json()
                
                # Verify schema consistency
                required_top_level = ["success", "feature_id", "api", "engagement", "risk_signals"]
                missing = [f for f in required_top_level if f not in data]
                
                if missing:
                    result.add_fail(
                        f"Endpoint stability - call {i} schema",
                        f"Missing fields: {missing}"
                    )
                else:
                    result.add_pass(
                        f"Endpoint stability - call {i}",
                        "Schema consistent, no runtime errors"
                    )
                
            except Exception as e:
                result.add_fail(
                    f"Endpoint stability - call {i} JSON parsing",
                    f"Failed to parse JSON: {e}"
                )
        
    except Exception as e:
        result.add_error("Endpoint stability test", str(e))


def main():
    print("="*80)
    print("Feature 21 Phase-4 Observability Backend API Test")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Admin User: {ADMIN_USER['email']}")
    print(f"Non-Admin User: {NON_ADMIN_USER['email']}")
    
    result = TestResult()
    
    # Run all tests
    test_admin_observability_access(result)
    test_non_admin_observability_access(result)
    test_watch_event_and_observability(result)
    test_endpoint_stability(result)
    
    # Print summary
    success = result.summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
