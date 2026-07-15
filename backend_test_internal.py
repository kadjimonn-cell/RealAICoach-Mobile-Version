#!/usr/bin/env python3
"""
Backend Security Verification for Security Iteration 56 - Internal Testing
Tests WebSocket security, query-param token rejection using internal backend
"""

import requests
import os
import time
import websocket
import threading
import sys

# Use internal backend URL
BASE_URL = "http://localhost:8001"
print(f"Testing against internal backend: {BASE_URL}")

# Test credentials
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"

# Test results
results = {
    "passed": [],
    "failed": [],
    "errors": []
}


def log_pass(test_name, details=""):
    msg = f"✅ PASS: {test_name}"
    if details:
        msg += f" - {details}"
    print(msg)
    results["passed"].append(test_name)


def log_fail(test_name, details=""):
    msg = f"❌ FAIL: {test_name}"
    if details:
        msg += f" - {details}"
    print(msg)
    results["failed"].append(f"{test_name}: {details}")


def log_error(test_name, error):
    msg = f"⚠️  ERROR: {test_name} - {error}"
    print(msg)
    results["errors"].append(f"{test_name}: {error}")


def get_authenticated_session():
    """Login and return authenticated session with user_id"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    })
    
    try:
        resp = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        if resp.status_code != 200:
            raise Exception(f"Login failed: {resp.status_code} - {resp.text[:200]}")
        
        data = resp.json()
        user_id = data.get("user_id")
        if not user_id:
            raise Exception("No user_id in login response")
        
        return session, user_id
    except Exception as e:
        raise Exception(f"Authentication failed: {e}")


# Test 1: POST /api/auth/ws-ticket - 401 unauthenticated
def test_ws_ticket_unauthenticated():
    print("\n[Test 1] POST /api/auth/ws-ticket - 401 unauthenticated")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/ws-ticket",
            headers={"Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest"},
            timeout=15
        )
        if resp.status_code == 401:
            log_pass("POST /api/auth/ws-ticket rejects unauthenticated", f"Status: {resp.status_code}")
        else:
            log_fail("POST /api/auth/ws-ticket should return 401", f"Got {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log_error("POST /api/auth/ws-ticket unauthenticated test", str(e))


# Test 2: POST /api/auth/ws-ticket - 200 authenticated with ticket + expires_in_seconds=90 + user_id
def test_ws_ticket_authenticated():
    print("\n[Test 2] POST /api/auth/ws-ticket - 200 authenticated with ticket")
    try:
        session, user_id = get_authenticated_session()
        resp = session.post(
            f"{BASE_URL}/api/auth/ws-ticket",
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=15
        )
        
        if resp.status_code != 200:
            log_fail("POST /api/auth/ws-ticket authenticated", f"Expected 200, got {resp.status_code}: {resp.text[:200]}")
            return None, None
        
        data = resp.json()
        
        # Verify all required fields
        checks = []
        if "ticket" not in data:
            checks.append("Missing 'ticket' field")
        elif len(data["ticket"]) < 32:
            checks.append(f"Ticket too short: {len(data['ticket'])} chars")
        
        if "expires_in_seconds" not in data:
            checks.append("Missing 'expires_in_seconds' field")
        elif data["expires_in_seconds"] != 90:
            checks.append(f"Expected expires_in_seconds=90, got {data['expires_in_seconds']}")
        
        if "user_id" not in data:
            checks.append("Missing 'user_id' field")
        elif data["user_id"] != user_id:
            checks.append(f"User ID mismatch: {data['user_id']} != {user_id}")
        
        if checks:
            log_fail("POST /api/auth/ws-ticket response validation", "; ".join(checks))
            return None, None
        
        log_pass("POST /api/auth/ws-ticket authenticated", 
                f"ticket={data['ticket'][:20]}..., expires_in_seconds={data['expires_in_seconds']}, user_id={data['user_id']}")
        return data["ticket"], user_id
    except Exception as e:
        log_error("POST /api/auth/ws-ticket authenticated test", str(e))
        return None, None


# Test 3: WS /api/ws/notifications/{user_id} - reject no ticket
def test_ws_reject_no_ticket():
    print("\n[Test 3] WS /api/ws/notifications/{user_id} - reject no ticket")
    try:
        session, user_id = get_authenticated_session()
        ws_endpoint = f"ws://localhost:8001/api/ws/notifications/{user_id}"
        
        close_code = None
        connected = False
        
        def on_open(ws):
            nonlocal connected
            connected = True
        
        def on_close(ws, code, msg):
            nonlocal close_code
            close_code = code
        
        ws = websocket.WebSocketApp(
            ws_endpoint,
            on_open=on_open,
            on_close=on_close
        )
        ws_thread = threading.Thread(target=ws.run_forever, kwargs={"ping_timeout": 3})
        ws_thread.daemon = True
        ws_thread.start()
        time.sleep(2)
        ws.close()
        ws_thread.join(timeout=2)
        
        if not connected and (close_code == 4001 or close_code is None):
            log_pass("WS rejects connection without ticket", f"connected={connected}, close_code={close_code}")
        else:
            log_fail("WS should reject connection without ticket", f"connected={connected}, close_code={close_code}")
    except Exception as e:
        log_error("WS reject no ticket test", str(e))


# Test 4: WS /api/ws/notifications/{user_id} - reject invalid ticket
def test_ws_reject_invalid_ticket():
    print("\n[Test 4] WS /api/ws/notifications/{user_id} - reject invalid ticket")
    try:
        session, user_id = get_authenticated_session()
        ws_endpoint = f"ws://localhost:8001/api/ws/notifications/{user_id}?ticket=invalid_fake_ticket_12345"
        
        close_code = None
        connected = False
        
        def on_open(ws):
            nonlocal connected
            connected = True
        
        def on_close(ws, code, msg):
            nonlocal close_code
            close_code = code
        
        ws = websocket.WebSocketApp(
            ws_endpoint,
            on_open=on_open,
            on_close=on_close
        )
        ws_thread = threading.Thread(target=ws.run_forever, kwargs={"ping_timeout": 3})
        ws_thread.daemon = True
        ws_thread.start()
        time.sleep(2)
        ws.close()
        ws_thread.join(timeout=2)
        
        if not connected and (close_code == 4001 or close_code is None):
            log_pass("WS rejects connection with invalid ticket", f"connected={connected}, close_code={close_code}")
        else:
            log_fail("WS should reject connection with invalid ticket", f"connected={connected}, close_code={close_code}")
    except Exception as e:
        log_error("WS reject invalid ticket test", str(e))


# Test 5: WS /api/ws/notifications/{user_id} - accept valid one-time ticket
def test_ws_accept_valid_ticket():
    print("\n[Test 5] WS /api/ws/notifications/{user_id} - accept valid one-time ticket")
    try:
        session, user_id = get_authenticated_session()
        
        # Get a valid ticket
        ticket_resp = session.post(
            f"{BASE_URL}/api/auth/ws-ticket",
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=15
        )
        if ticket_resp.status_code != 200:
            log_fail("Failed to get WS ticket", ticket_resp.text[:200])
            return
        
        ticket = ticket_resp.json()["ticket"]
        
        ws_endpoint = f"ws://localhost:8001/api/ws/notifications/{user_id}?ticket={ticket}"
        
        connected = False
        close_code = None
        
        def on_open(ws):
            nonlocal connected
            connected = True
            time.sleep(0.5)
            ws.close()
        
        def on_close(ws, code, msg):
            nonlocal close_code
            close_code = code
        
        ws = websocket.WebSocketApp(
            ws_endpoint,
            on_open=on_open,
            on_close=on_close
        )
        ws_thread = threading.Thread(target=ws.run_forever, kwargs={"ping_timeout": 5})
        ws_thread.daemon = True
        ws_thread.start()
        time.sleep(3)
        ws.close()
        ws_thread.join(timeout=2)
        
        if connected:
            log_pass("WS accepts connection with valid ticket", f"connected={connected}")
        else:
            log_fail("WS should accept connection with valid ticket", f"connected={connected}, close_code={close_code}")
    except Exception as e:
        log_error("WS accept valid ticket test", str(e))


# Test 6: WS /api/ws/notifications/{user_id} - reject replay with same ticket
def test_ws_reject_replay():
    print("\n[Test 6] WS /api/ws/notifications/{user_id} - reject replay with same ticket")
    try:
        session, user_id = get_authenticated_session()
        
        # Get a valid ticket
        ticket_resp = session.post(
            f"{BASE_URL}/api/auth/ws-ticket",
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=15
        )
        if ticket_resp.status_code != 200:
            log_fail("Failed to get WS ticket", ticket_resp.text[:200])
            return
        
        ticket = ticket_resp.json()["ticket"]
        
        ws_endpoint = f"ws://localhost:8001/api/ws/notifications/{user_id}?ticket={ticket}"
        
        # First connection - should succeed
        first_connected = False
        def on_open_first(ws):
            nonlocal first_connected
            first_connected = True
            time.sleep(0.5)
            ws.close()
        
        ws1 = websocket.WebSocketApp(ws_endpoint, on_open=on_open_first)
        ws_thread1 = threading.Thread(target=ws1.run_forever, kwargs={"ping_timeout": 3})
        ws_thread1.daemon = True
        ws_thread1.start()
        time.sleep(2)
        ws1.close()
        ws_thread1.join(timeout=2)
        
        if not first_connected:
            log_fail("First WS connection should succeed", "First connection failed")
            return
        
        # Second connection with same ticket - should be rejected
        second_connected = False
        second_close_code = None
        
        def on_open_second(ws):
            nonlocal second_connected
            second_connected = True
        
        def on_close_second(ws, code, msg):
            nonlocal second_close_code
            second_close_code = code
        
        ws2 = websocket.WebSocketApp(ws_endpoint, on_open=on_open_second, on_close=on_close_second)
        ws_thread2 = threading.Thread(target=ws2.run_forever, kwargs={"ping_timeout": 3})
        ws_thread2.daemon = True
        ws_thread2.start()
        time.sleep(2)
        ws2.close()
        ws_thread2.join(timeout=2)
        
        if not second_connected and (second_close_code == 4001 or second_close_code is None):
            log_pass("WS rejects replay with same ticket", f"second_connected={second_connected}, close_code={second_close_code}")
        else:
            log_fail("WS should reject replay with same ticket", f"second_connected={second_connected}, close_code={second_close_code}")
    except Exception as e:
        log_error("WS reject replay test", str(e))


# Test 7: Query-param token auth rejection - /api/auth/me?token=<valid_session_token> should be 401
def test_query_param_token_rejected():
    print("\n[Test 7] Query-param token auth rejection - /api/auth/me?token=<valid_session_token> should be 401")
    try:
        session, user_id = get_authenticated_session()
        
        # Get the session token from cookies
        session_token = session.cookies.get("session_token")
        if not session_token:
            # Try to extract from response headers or make a request to get it
            me_resp = session.get(f"{BASE_URL}/api/auth/me", timeout=15)
            if me_resp.status_code == 200:
                # Session is valid via cookie, try to get token
                session_token = session.cookies.get("session_token")
        
        if not session_token:
            log_error("Query-param token test", "Could not extract session_token from cookies")
            return
        
        # Now try to access with token in query param only (no cookie/header)
        new_session = requests.Session()
        resp = new_session.get(
            f"{BASE_URL}/api/auth/me?token={session_token}",
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=15
        )
        
        if resp.status_code == 401:
            log_pass("Query-param token rejected", f"/api/auth/me?token=... returned 401")
        else:
            log_fail("Query-param token should be rejected", f"Expected 401, got {resp.status_code}")
    except Exception as e:
        log_error("Query-param token rejection test", str(e))


# Test 8: /api/auth/me with Authorization: Bearer <same_token> should be 200
def test_bearer_token_accepted():
    print("\n[Test 8] /api/auth/me with Authorization: Bearer <same_token> should be 200")
    try:
        session, user_id = get_authenticated_session()
        
        # Get the session token from cookies
        session_token = session.cookies.get("session_token")
        if not session_token:
            me_resp = session.get(f"{BASE_URL}/api/auth/me", timeout=15)
            if me_resp.status_code == 200:
                session_token = session.cookies.get("session_token")
        
        if not session_token:
            log_error("Bearer token test", "Could not extract session_token from cookies")
            return
        
        # Try to access with Authorization header
        new_session = requests.Session()
        resp = new_session.get(
            f"{BASE_URL}/api/auth/me",
            headers={
                "Authorization": f"Bearer {session_token}",
                "X-Requested-With": "XMLHttpRequest"
            },
            timeout=15
        )
        
        if resp.status_code == 200:
            log_pass("Bearer token accepted", f"/api/auth/me with Authorization: Bearer returned 200")
        else:
            log_fail("Bearer token should be accepted", f"Expected 200, got {resp.status_code}")
    except Exception as e:
        log_error("Bearer token acceptance test", str(e))


def main():
    print("=" * 80)
    print("Backend Security Verification for Security Iteration 56 (Internal)")
    print("=" * 80)
    
    # Run all tests
    test_ws_ticket_unauthenticated()
    test_ws_ticket_authenticated()
    test_ws_reject_no_ticket()
    test_ws_reject_invalid_ticket()
    test_ws_accept_valid_ticket()
    test_ws_reject_replay()
    test_query_param_token_rejected()
    test_bearer_token_accepted()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {len(results['passed'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"⚠️  Errors: {len(results['errors'])}")
    
    if results['failed']:
        print("\nFailed Tests:")
        for failure in results['failed']:
            print(f"  - {failure}")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("=" * 80)
    
    # Exit with appropriate code
    if results['failed'] or results['errors']:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
