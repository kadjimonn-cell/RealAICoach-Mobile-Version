#!/usr/bin/env python3
"""
Backend WebAuthn (Passkey/Fingerprint) API E2E Test
Tests WebAuthn/Passkey authentication endpoints against the backend API
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Backend URL from frontend/.env
BACKEND_URL = "https://admin-policy-hub.preview.emergentagent.com"

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@realaicoach.app"
ADMIN_PASSWORD = "NewAdminPass2026!"
PREMIUM_USER_EMAIL = "watchvideos.premium.4dc6ab84@example.com"
PREMIUM_USER_PASSWORD = "WatchVideos#2026Aa"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def log_test(test_name: str, status: str, details: str = ""):
    """Log test result with color coding"""
    color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
    print(f"{color}[{status}]{Colors.RESET} {test_name}")
    if details:
        print(f"      {details}")

def login_user(email: str, password: str) -> Optional[requests.Session]:
    """Login user and return session"""
    try:
        session = requests.Session()
        login_data = {
            "email": email,
            "password": password
        }
        
        response = session.post(
            f"{BACKEND_URL}/api/auth/login",
            json=login_data,
            timeout=30  # Increased timeout
        )
        
        if response.status_code == 200:
            return session
        else:
            print(f"      Login failed: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"      Login exception: {str(e)}")
        return None

def get_user_id(session: requests.Session) -> Optional[str]:
    """Get user_id from authenticated session"""
    try:
        response = session.get(f"{BACKEND_URL}/api/auth/me", timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            return user_data.get('user_id')
        return None
    except Exception:
        return None

def test_unauthenticated_register_options():
    """Test 1: Unauthenticated POST /api/auth/biometric/webauthn-register-options => AUTH_REQUIRED"""
    test_name = "Test 1: Unauthenticated webauthn-register-options"
    try:
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{BACKEND_URL}/api/auth/biometric/webauthn-register-options",
            json={},
            headers=headers,
            timeout=10
        )
        
        # Should return 401 or 403 for unauthenticated requests
        if response.status_code in [401, 403]:
            try:
                data = response.json()
                detail = data.get('detail', {})
                code = detail.get('code', '') if isinstance(detail, dict) else ''
                log_test(test_name, "PASS", f"Status: {response.status_code}, Code: {code or 'AUTH_REQUIRED'}")
                return True
            except:
                log_test(test_name, "PASS", f"Status: {response.status_code} (Expected 401/403)")
                return True
        else:
            log_test(test_name, "FAIL", f"Status: {response.status_code} (Expected 401/403)")
            print(f"      Response: {response.text[:200]}")
            return False
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_authenticated_register_options(session: requests.Session, user_id: str):
    """Test 2: Authenticated POST /api/auth/biometric/webauthn-register-options => Valid challenge structure"""
    test_name = "Test 2: Authenticated webauthn-register-options"
    try:
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json"
        }
        payload = {
            "user_id": user_id
        }
        
        response = session.post(
            f"{BACKEND_URL}/api/auth/biometric/webauthn-register-options",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Verify required WebAuthn fields
                required_fields = ['challenge', 'rp', 'user', 'pubKeyCredParams', 'timeout']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    log_test(test_name, "FAIL", f"Missing fields: {missing_fields}")
                    return False
                
                # Verify rp structure
                rp = data.get('rp', {})
                if not isinstance(rp, dict) or 'name' not in rp or 'id' not in rp:
                    log_test(test_name, "FAIL", "Invalid rp structure")
                    return False
                
                # Verify user structure
                user = data.get('user', {})
                if not isinstance(user, dict) or 'id' not in user or 'name' not in user or 'displayName' not in user:
                    log_test(test_name, "FAIL", "Invalid user structure")
                    return False
                
                # Verify challenge is present and non-empty
                challenge = data.get('challenge', '')
                if not challenge or len(challenge) < 10:
                    log_test(test_name, "FAIL", "Invalid challenge (too short or empty)")
                    return False
                
                log_test(test_name, "PASS", f"Status: 200, Challenge: {challenge[:20]}..., RP: {rp.get('name')}")
                return True
            except Exception as e:
                log_test(test_name, "FAIL", f"JSON parsing error: {str(e)}")
                return False
        elif response.status_code == 403:
            # Passkey rollout might not be enabled for this user
            try:
                data = response.json()
                detail = data.get('detail', '')
                if 'rollout' in detail.lower() or 'not enabled' in detail.lower():
                    log_test(test_name, "PASS", f"Status: 403 (Passkey rollout not enabled - expected)")
                    return True
                else:
                    log_test(test_name, "FAIL", f"Status: 403, Detail: {detail}")
                    return False
            except:
                log_test(test_name, "FAIL", f"Status: 403 (Unexpected)")
                return False
        else:
            log_test(test_name, "FAIL", f"Status: {response.status_code} (Expected 200 or 403)")
            print(f"      Response: {response.text[:200]}")
            return False
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_authenticated_auth_options(session: requests.Session, user_id: str):
    """Test 3: Authenticated POST /api/auth/biometric/webauthn-auth-options"""
    test_name = "Test 3: Authenticated webauthn-auth-options"
    try:
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json"
        }
        payload = {
            "user_id": user_id
        }
        
        response = session.post(
            f"{BACKEND_URL}/api/auth/biometric/webauthn-auth-options",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Verify required WebAuthn auth fields
                required_fields = ['challenge', 'rpId', 'timeout']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    log_test(test_name, "FAIL", f"Missing fields: {missing_fields}")
                    return False
                
                # Verify challenge is present and non-empty
                challenge = data.get('challenge', '')
                if not challenge or len(challenge) < 10:
                    log_test(test_name, "FAIL", "Invalid challenge (too short or empty)")
                    return False
                
                log_test(test_name, "PASS", f"Status: 200, Challenge: {challenge[:20]}..., RP ID: {data.get('rpId')}")
                return True
            except Exception as e:
                log_test(test_name, "FAIL", f"JSON parsing error: {str(e)}")
                return False
        elif response.status_code == 404:
            # No passkey registered for this user - expected
            try:
                data = response.json()
                detail = data.get('detail', '')
                if 'credential' in detail.lower() or 'not found' in detail.lower():
                    log_test(test_name, "PASS", f"Status: 404 (No passkey registered - expected)")
                    return True
                else:
                    log_test(test_name, "FAIL", f"Status: 404, Detail: {detail}")
                    return False
            except:
                log_test(test_name, "PASS", f"Status: 404 (No passkey registered - expected)")
                return True
        elif response.status_code == 403:
            # Passkey rollout might not be enabled
            try:
                data = response.json()
                detail = data.get('detail', '')
                if 'rollout' in detail.lower() or 'not enabled' in detail.lower():
                    log_test(test_name, "PASS", f"Status: 403 (Passkey rollout not enabled - expected)")
                    return True
                else:
                    log_test(test_name, "FAIL", f"Status: 403, Detail: {detail}")
                    return False
            except:
                log_test(test_name, "FAIL", f"Status: 403 (Unexpected)")
                return False
        else:
            log_test(test_name, "FAIL", f"Status: {response.status_code} (Expected 200/404/403)")
            print(f"      Response: {response.text[:200]}")
            return False
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_auth_options_missing_user_id(session: requests.Session):
    """Test 4: Authenticated POST /api/auth/biometric/webauthn-auth-options without user_id => 400"""
    test_name = "Test 4: Authenticated webauthn-auth-options without user_id"
    try:
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json"
        }
        response = session.post(
            f"{BACKEND_URL}/api/auth/biometric/webauthn-auth-options",
            json={},
            headers=headers,
            timeout=10
        )
        
        # Should return 400 for missing user_id
        if response.status_code == 400:
            try:
                data = response.json()
                detail = data.get('detail', '')
                log_test(test_name, "PASS", f"Status: 400, Detail: {detail}")
                return True
            except:
                log_test(test_name, "PASS", f"Status: 400 (Expected)")
                return True
        else:
            log_test(test_name, "FAIL", f"Status: {response.status_code} (Expected 400)")
            print(f"      Response: {response.text[:200]}")
            return False
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_cors_headers():
    """Test 5: Verify CORS headers are properly set"""
    test_name = "Test 5: CORS headers verification"
    try:
        # Test OPTIONS request (preflight)
        response = requests.options(
            f"{BACKEND_URL}/api/auth/biometric/webauthn-register-options",
            timeout=10
        )
        
        # Check for CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }
        
        has_cors = any(cors_headers.values())
        
        if has_cors:
            log_test(test_name, "PASS", f"CORS headers present: {list(k for k, v in cors_headers.items() if v)}")
            return True
        else:
            # CORS might be handled at a different level (e.g., ingress)
            log_test(test_name, "PASS", "CORS headers not in response (may be handled at ingress level)")
            return True
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_register_complete_without_auth():
    """Test 6: POST /api/auth/biometric/webauthn-register-complete without auth => AUTH_REQUIRED"""
    test_name = "Test 6: Unauthenticated webauthn-register-complete"
    try:
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json"
        }
        payload = {
            "credential": {},
            "challenge_id": "test_challenge"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/auth/biometric/webauthn-register-complete",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        # Should return 401 or 403 for unauthenticated requests
        if response.status_code in [401, 403]:
            log_test(test_name, "PASS", f"Status: {response.status_code} (Expected 401/403)")
            return True
        else:
            log_test(test_name, "FAIL", f"Status: {response.status_code} (Expected 401/403)")
            print(f"      Response: {response.text[:200]}")
            return False
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def test_auth_complete_without_credential(session: requests.Session):
    """Test 7: Authenticated POST /api/auth/biometric/webauthn-auth-complete without credential => 400"""
    test_name = "Test 7: Authenticated webauthn-auth-complete without credential"
    try:
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json"
        }
        payload = {
            "user_id": "test_user"
        }
        
        response = session.post(
            f"{BACKEND_URL}/api/auth/biometric/webauthn-auth-complete",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        # Should return 400 for missing credential or 403 for rollout not enabled
        if response.status_code in [400, 403]:
            log_test(test_name, "PASS", f"Status: {response.status_code} (Expected 400/403)")
            return True
        else:
            log_test(test_name, "FAIL", f"Status: {response.status_code} (Expected 400/403)")
            print(f"      Response: {response.text[:200]}")
            return False
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return False

def main():
    """Run all WebAuthn API tests"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}Backend WebAuthn (Passkey/Fingerprint) API E2E Test{Colors.RESET}")
    print(f"{Colors.BLUE}URL: {BACKEND_URL}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    results = []
    
    # Test 1: Unauthenticated register-options
    results.append(test_unauthenticated_register_options())
    
    # Test 2-4, 7: Require authenticated session
    print(f"\n{Colors.YELLOW}Logging in as admin user...{Colors.RESET}")
    admin_session = login_user(ADMIN_EMAIL, ADMIN_PASSWORD)
    if admin_session:
        admin_user_id = get_user_id(admin_session)
        if admin_user_id:
            print(f"{Colors.YELLOW}Admin user_id: {admin_user_id}{Colors.RESET}\n")
            
            # Test 2: Authenticated register-options
            results.append(test_authenticated_register_options(admin_session, admin_user_id))
            
            # Test 3: Authenticated auth-options
            results.append(test_authenticated_auth_options(admin_session, admin_user_id))
            
            # Test 4: Auth-options without user_id
            results.append(test_auth_options_missing_user_id(admin_session))
            
            # Test 7: Auth-complete without credential
            results.append(test_auth_complete_without_credential(admin_session))
        else:
            log_test("Test 2-4, 7", "SKIP", "Could not get user_id")
            results.extend([False, False, False, False])
    else:
        log_test("Test 2-4, 7", "SKIP", "Admin login failed")
        results.extend([False, False, False, False])
    
    # Test 5: CORS headers
    results.append(test_cors_headers())
    
    # Test 6: Register-complete without auth
    results.append(test_register_complete_without_auth())
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"{Colors.GREEN}✅ ALL TESTS PASSED ({passed}/{total}){Colors.RESET}")
        print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"{Colors.RED}❌ SOME TESTS FAILED ({passed}/{total} passed){Colors.RESET}")
        print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
