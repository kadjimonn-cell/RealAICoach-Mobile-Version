"""
Backend Pagination Test for P2-03
Tests admin pagination endpoints to verify they return proper pagination keys
"""
import requests
import json

# Configuration
BASE_URL = "https://admin-policy-hub.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

# Test endpoints
ENDPOINTS = [
    {
        "name": "Referrals Admin Challenges",
        "url": f"{BASE_URL}/referrals/admin/challenges",
        "params": {"page": 1, "page_size": 5}
    },
    {
        "name": "Referrals Admin Fraud Alerts",
        "url": f"{BASE_URL}/referrals/admin/fraud-alerts",
        "params": {"page": 1, "page_size": 5}
    },
    {
        "name": "Support FAQ Admin List",
        "url": f"{BASE_URL}/support/faq/admin/list",
        "params": {"lang": "en", "page": 1, "page_size": 5}
    },
    {
        "name": "Admin Submissions",
        "url": f"{BASE_URL}/admin/submissions",
        "params": {"type": "all", "status": "all", "page": 1, "page_size": 5}
    }
]

# Required pagination keys
REQUIRED_KEYS = ["data", "total_count", "page", "page_size"]

def login_admin():
    """Login as admin and return session with cookies"""
    session = requests.Session()
    login_url = f"{BASE_URL}/auth/login"
    
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    print(f"\n🔐 Logging in as admin: {ADMIN_EMAIL}")
    response = session.post(login_url, json=payload)
    
    if response.status_code == 200:
        print(f"✅ Login successful (Status: {response.status_code})")
        return session
    else:
        print(f"❌ Login failed (Status: {response.status_code})")
        print(f"Response: {response.text}")
        return None

def test_pagination_endpoint(session, endpoint_config):
    """Test a single pagination endpoint"""
    name = endpoint_config["name"]
    url = endpoint_config["url"]
    params = endpoint_config["params"]
    
    print(f"\n📋 Testing: {name}")
    print(f"   URL: {url}")
    print(f"   Params: {params}")
    
    try:
        response = session.get(url, params=params)
        status_code = response.status_code
        
        print(f"   Status Code: {status_code}")
        
        if status_code != 200:
            print(f"   ❌ FAIL: Expected HTTP 200, got {status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
        
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"   ❌ FAIL: Invalid JSON response")
            print(f"   Error: {e}")
            print(f"   Response: {response.text[:500]}")
            return False
        
        # Check for required pagination keys
        missing_keys = []
        for key in REQUIRED_KEYS:
            if key not in data:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"   ❌ FAIL: Missing required keys: {missing_keys}")
            print(f"   Available keys: {list(data.keys())}")
            return False
        
        # Validate pagination values
        print(f"   ✅ PASS: All required keys present")
        print(f"   Pagination Info:")
        print(f"      - page: {data.get('page')}")
        print(f"      - page_size: {data.get('page_size')}")
        print(f"      - total_count: {data.get('total_count')}")
        print(f"      - data items: {len(data.get('data', []))}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Exception occurred")
        print(f"   Error: {e}")
        return False

def main():
    """Main test execution"""
    print("=" * 80)
    print("Backend Pagination Test - P2-03")
    print("=" * 80)
    
    # Login as admin
    session = login_admin()
    if not session:
        print("\n❌ TEST SUITE FAILED: Unable to login as admin")
        return
    
    # Test each endpoint
    results = {}
    for endpoint in ENDPOINTS:
        result = test_pagination_endpoint(session, endpoint)
        results[endpoint["name"]] = result
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED")
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")

if __name__ == "__main__":
    main()
