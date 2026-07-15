"""
Nova Platform-Wide Consistency Test Suite
Tests Nova surfaces across Home, Help & Support, and Settings
"""
import requests
import os
import json
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://visa-polish-v2.preview.emergentagent.com').rstrip('/')

# Test credentials
FREE_USER_EMAIL = "p1.free.1779113329@example.com"
FREE_USER_PASSWORD = "P1Free#2026!Aa"
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

def login(email, password):
    """Login and return session with cookies"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    })
    
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password},
            timeout=30
        )
        if response.status_code == 200:
            print(f"✓ Login successful for {email}")
            return session
        else:
            print(f"✗ Login failed for {email}: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print(f"✗ Login error for {email}: {e}")
        return None

def test_nova_health():
    """Test Nova health endpoint"""
    print("\n=== Testing Nova Health Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/api/support/nova/health?hours=1", timeout=15)
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Status: {data.get('status')}")
        print(f"GPS Live: {data.get('gps_live')}")
        print(f"GPS Source: {data.get('gps_source')}")
        print(f"GPS Failed Checks: {data.get('gps_failed_checks')}")
        
        # Assertions
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert data.get('status') == 'healthy', f"Expected healthy, got {data.get('status')}"
        assert data.get('gps_live') == True, f"Expected gps_live=True, got {data.get('gps_live')}"
        assert data.get('gps_source') == 'live', f"Expected gps_source=live, got {data.get('gps_source')}"
        assert len(data.get('gps_failed_checks', [])) == 0, f"Expected no failed checks, got {data.get('gps_failed_checks')}"
        
        print("✓ Nova health check PASSED - GPS is LIVE and healthy")
        return True
    except Exception as e:
        print(f"✗ Nova health check FAILED: {e}")
        return False

def test_nova_chat_authenticated(session):
    """Test Nova chat with authenticated session"""
    print("\n=== Testing Nova Chat (Authenticated) ===")
    try:
        # Send a message
        response = session.post(
            f"{BASE_URL}/api/support/chat",
            json={"message": "What features are available on this platform?"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Conversation ID: {data.get('conversation_id')}")
            print(f"Message received: {data.get('message', '')[:100]}...")
            print(f"GPS Context: {data.get('gps_context')}")
            
            gps_context = data.get('gps_context', {})
            if gps_context:
                print(f"  - GPS Live: {gps_context.get('gps_live')}")
                print(f"  - GPS Source: {gps_context.get('gps_source')}")
                print(f"  - GPS Version: {gps_context.get('gps_version')}")
                print(f"  - GPS Freshness: {gps_context.get('gps_freshness_sec')}s")
                
                # Check GPS is live
                if gps_context.get('gps_live') and gps_context.get('gps_source') == 'live':
                    print("✓ Nova chat GPS context shows LIVE status")
                else:
                    print("✗ Nova chat GPS context shows DEGRADED status")
            
            print("✓ Nova chat PASSED")
            return True, data.get('conversation_id')
        else:
            print(f"✗ Nova chat FAILED: {response.text[:200]}")
            return False, None
    except Exception as e:
        print(f"✗ Nova chat error: {e}")
        return False, None

def test_nova_conversation_history(session, conversation_id):
    """Test Nova conversation history retrieval"""
    print("\n=== Testing Nova Conversation History ===")
    if not conversation_id:
        print("✗ No conversation ID to test")
        return False
    
    try:
        response = session.get(
            f"{BASE_URL}/api/support/chat/history?conversation_id={conversation_id}",
            timeout=15
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            messages = data.get('messages', [])
            print(f"Messages count: {len(messages)}")
            
            # Check for both user and assistant messages
            user_msgs = [m for m in messages if m.get('role') == 'user']
            assistant_msgs = [m for m in messages if m.get('role') == 'assistant']
            
            print(f"User messages: {len(user_msgs)}")
            print(f"Assistant messages: {len(assistant_msgs)}")
            
            if len(assistant_msgs) > 0:
                print("✓ Nova conversation history PASSED")
                return True
            else:
                print("✗ No assistant messages found")
                return False
        else:
            print(f"✗ Conversation history FAILED: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ Conversation history error: {e}")
        return False

def test_gps_state():
    """Test GPS state endpoint"""
    print("\n=== Testing GPS State Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/api/gps/state", timeout=15)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            runtime = data.get('_gps_runtime', {})
            
            print(f"GPS Version: {data.get('version')}")
            print(f"GPS Runtime Mode: {runtime.get('mode')}")
            print(f"GPS Runtime Source: {runtime.get('source')}")
            print(f"GPS Last Success: {runtime.get('last_success_at')}")
            
            # Check runtime is live
            if runtime.get('source') == 'live' and runtime.get('mode') == 'live':
                print("✓ GPS state shows LIVE runtime")
                return True
            else:
                print(f"✗ GPS state shows non-live: mode={runtime.get('mode')}, source={runtime.get('source')}")
                return False
        else:
            print(f"✗ GPS state FAILED: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ GPS state error: {e}")
        return False

def test_nova_favorites_pins(session, conversation_id):
    """Test Nova favorites and pins endpoints"""
    print("\n=== Testing Nova Favorites & Pins ===")
    
    # Test favorites
    try:
        response = session.get(
            f"{BASE_URL}/api/support/chat/messages/favorites",
            timeout=15
        )
        print(f"Favorites Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Favorites count: {len(data.get('favorites', []))}")
            print("✓ Favorites endpoint accessible")
        else:
            print(f"✗ Favorites endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Favorites error: {e}")
    
    # Test pins
    try:
        response = session.get(
            f"{BASE_URL}/api/support/chat/conversations/pins",
            timeout=15
        )
        print(f"Pins Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Pins count: {len(data.get('pins', []))}")
            print("✓ Pins endpoint accessible")
        else:
            print(f"✗ Pins endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Pins error: {e}")

def run_tests():
    """Run all Nova platform tests"""
    print("=" * 60)
    print("NOVA PLATFORM-WIDE CONSISTENCY TEST SUITE")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "tests": {}
    }
    
    # Test 1: Nova Health (unauthenticated)
    results["tests"]["nova_health"] = test_nova_health()
    
    # Test 2: GPS State
    results["tests"]["gps_state"] = test_gps_state()
    
    # Test 3: Login as free user
    session = login(FREE_USER_EMAIL, FREE_USER_PASSWORD)
    results["tests"]["login"] = session is not None
    
    if session:
        # Test 4: Nova Chat
        chat_passed, conversation_id = test_nova_chat_authenticated(session)
        results["tests"]["nova_chat"] = chat_passed
        
        # Test 5: Conversation History
        if conversation_id:
            results["tests"]["conversation_history"] = test_nova_conversation_history(session, conversation_id)
        
        # Test 6: Favorites & Pins
        test_nova_favorites_pins(session, conversation_id)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results["tests"].values() if v)
    total = len(results["tests"])
    
    for test_name, passed_flag in results["tests"].items():
        status = "✓ PASS" if passed_flag else "✗ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return results

if __name__ == "__main__":
    results = run_tests()
    
    # Save results
    with open("/app/test_reports/nova_platform_backend_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to /app/test_reports/nova_platform_backend_results.json")
