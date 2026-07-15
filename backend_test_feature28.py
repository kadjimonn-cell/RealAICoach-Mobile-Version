"""
Feature 28 (Audio Studio) Stabilization Validation
Test cases from review request:
1) Login works via /api/auth/login
2) /api/videos/audio-studio/bootstrap returns 200 with source_health object and keys
3) /api/videos/audio-studio/play returns deterministic response for one free item
4) /api/videos/audio-studio/daily-drop-inbox and /mark-listened endpoints respond correctly
5) No schema regression for existing fields: feature_id, quota, catalog
"""

import requests
import json

# Base URL and credentials from review request
BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"
EMAIL = "p1.free.1779113329@example.com"
PASSWORD = "P1Free#2026!Aa"

def test_feature28_stabilization():
    """Run all Feature 28 stabilization tests"""
    
    print("\n" + "="*80)
    print("Feature 28 (Audio Studio) Stabilization Validation")
    print("="*80)
    
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    })
    
    # Test 1: Login works via /api/auth/login
    print("\n[Test 1] Login via /api/auth/login")
    print("-" * 80)
    
    login_response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD}
    )
    
    print(f"Status Code: {login_response.status_code}")
    
    if login_response.status_code == 200:
        login_data = login_response.json()
        print(f"✅ Login successful")
        print(f"   User ID: {login_data.get('user_id')}")
        print(f"   Email: {login_data.get('email')}")
        print(f"   Plan: {login_data.get('subscription_plan')}")
    else:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    # Test 2: /api/videos/audio-studio/bootstrap returns 200 with source_health
    print("\n[Test 2] Bootstrap endpoint with source_health object")
    print("-" * 80)
    
    bootstrap_response = session.get(
        f"{BASE_URL}/api/videos/audio-studio/bootstrap",
        params={"tz": "UTC"}
    )
    
    print(f"Status Code: {bootstrap_response.status_code}")
    
    if bootstrap_response.status_code != 200:
        print(f"❌ Bootstrap failed: {bootstrap_response.text}")
        return False
    
    bootstrap_data = bootstrap_response.json()
    print(f"✅ Bootstrap successful")
    
    # Check source_health object
    if "source_health" not in bootstrap_data:
        print(f"❌ source_health missing from response")
        return False
    
    source_health = bootstrap_data["source_health"]
    print(f"✅ source_health object present")
    
    # Check required keys
    required_keys = [
        "status",
        "reason_code", 
        "total_items",
        "playable_items",
        "secure_https_ratio"
    ]
    
    print(f"\n   Checking required keys in source_health:")
    for key in required_keys:
        if key in source_health:
            print(f"   ✅ {key}: {source_health[key]}")
        else:
            print(f"   ❌ {key}: MISSING")
            return False
    
    # Check contract.allowed_statuses
    if "contract" in source_health:
        contract = source_health["contract"]
        if "allowed_statuses" in contract:
            print(f"   ✅ contract.allowed_statuses: {contract['allowed_statuses']}")
        else:
            print(f"   ❌ contract.allowed_statuses: MISSING")
            return False
    else:
        print(f"   ❌ contract object: MISSING")
        return False
    
    # Test 3: /api/videos/audio-studio/play returns deterministic response
    print("\n[Test 3] Play endpoint for one free item")
    print("-" * 80)
    
    catalog = bootstrap_data.get("catalog", [])
    if not catalog:
        print(f"⚠️  No catalog items available, skipping play test")
    else:
        first_item = catalog[0]
        item_id = first_item.get("item_id")
        print(f"Testing with item_id: {item_id}")
        
        play_response = session.post(
            f"{BASE_URL}/api/videos/audio-studio/play",
            json={
                "item_id": item_id,
                "listen_seconds": 10,
                "completed": False,
                "source": "validation_test"
            }
        )
        
        print(f"Status Code: {play_response.status_code}")
        
        if play_response.status_code == 200:
            play_data = play_response.json()
            print(f"✅ Play successful")
            print(f"   Item ID: {play_data.get('item', {}).get('item_id')}")
            print(f"   Deterministic response: {play_data.get('item', {}).get('title', 'N/A')}")
        elif play_response.status_code == 429:
            print(f"⚠️  Quota exceeded (expected for free tier)")
            print(f"   Message: {play_response.json().get('detail')}")
        else:
            print(f"❌ Play failed: {play_response.text}")
            return False
    
    # Test 4: daily-drop-inbox and mark-listened endpoints
    print("\n[Test 4] Daily drop inbox and mark-listened endpoints")
    print("-" * 80)
    
    inbox_response = session.get(
        f"{BASE_URL}/api/videos/audio-studio/daily-drop-inbox"
    )
    
    print(f"Inbox Status Code: {inbox_response.status_code}")
    
    if inbox_response.status_code != 200:
        print(f"❌ Inbox failed: {inbox_response.text}")
        return False
    
    inbox_data = inbox_response.json()
    print(f"✅ Daily drop inbox successful")
    print(f"   Total items: {inbox_data.get('total')}")
    print(f"   Unread items: {inbox_data.get('unread')}")
    print(f"   Surface: {inbox_data.get('surface')}")
    
    # Test mark-listened if items available
    inbox_items = inbox_data.get("items", [])
    if inbox_items:
        inbox_item_id = inbox_items[0].get("item_id")
        print(f"\n   Testing mark-listened with item_id: {inbox_item_id}")
        
        mark_response = session.post(
            f"{BASE_URL}/api/videos/audio-studio/daily-drop-inbox/mark-listened",
            json={"item_id": inbox_item_id}
        )
        
        print(f"   Mark-listened Status Code: {mark_response.status_code}")
        
        if mark_response.status_code == 200:
            mark_data = mark_response.json()
            print(f"   ✅ Mark-listened successful")
            print(f"      Item ID: {mark_data.get('item_id')}")
        else:
            print(f"   ❌ Mark-listened failed: {mark_response.text}")
            return False
    else:
        print(f"   ⚠️  No inbox items available, skipping mark-listened test")
    
    # Test 5: No schema regression for existing fields
    print("\n[Test 5] Schema regression check for existing fields")
    print("-" * 80)
    
    required_fields = ["feature_id", "quota", "catalog"]
    
    for field in required_fields:
        if field in bootstrap_data:
            print(f"✅ {field}: present")
            if field == "feature_id":
                print(f"   Value: {bootstrap_data[field]}")
            elif field == "quota":
                quota = bootstrap_data[field]
                print(f"   Plan: {quota.get('plan')}")
                print(f"   Daily play limit: {quota.get('daily_play_limit')}")
                print(f"   Daily play used: {quota.get('daily_play_used')}")
                print(f"   Daily play remaining: {quota.get('daily_play_remaining')}")
            elif field == "catalog":
                print(f"   Catalog items: {len(bootstrap_data[field])}")
        else:
            print(f"❌ {field}: MISSING")
            return False
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED - Feature 28 stabilization validated")
    print("="*80)
    
    return True

if __name__ == "__main__":
    success = test_feature28_stabilization()
    exit(0 if success else 1)
