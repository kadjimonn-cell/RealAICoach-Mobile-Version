#!/usr/bin/env python3
"""
i18n Backend Validation - Focused Test
Validates i18n persistence after frontend-side recoverable error refactor
"""

import requests
import json
import time

BASE_URL = "https://visa-polish-v2.preview.emergentagent.com"
EMAIL = "p1.free.1779113329@example.com"
PASSWORD = "P1Free#2026!Aa"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_result(test_num, description, status, details=""):
    symbol = "✅ PASS" if status else "❌ FAIL"
    print(f"\n{test_num}) {description}")
    print(f"   {symbol}")
    if details:
        print(f"   {details}")

def main():
    print_section("i18n Backend Validation Test")
    print(f"Backend URL: {BASE_URL}")
    print(f"Credentials: {EMAIL}")
    
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    })
    
    # Test 1: Login success
    print_section("Test 1: Login Success")
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
            timeout=10
        )
        login_success = response.status_code == 200
        print_result(1, "Login", login_success, 
                    f"Status: {response.status_code}, User: {response.json().get('user_id', 'N/A') if login_success else 'N/A'}")
        
        if not login_success:
            print("\n❌ Cannot proceed without login")
            return
    except Exception as e:
        print_result(1, "Login", False, f"Error: {str(e)}")
        return
    
    # Test 2: GET /api/i18n/user-preference returns language + source
    print_section("Test 2: GET /api/i18n/user-preference")
    try:
        response = session.get(f"{BASE_URL}/api/i18n/user-preference", timeout=10)
        data = response.json() if response.status_code == 200 else {}
        
        has_fields = "language" in data and "source" in data
        print_result(2, "GET user-preference returns language + source", 
                    response.status_code == 200 and has_fields,
                    f"Status: {response.status_code}, Language: {data.get('language')}, Source: {data.get('source')}")
    except Exception as e:
        print_result(2, "GET user-preference", False, f"Error: {str(e)}")
    
    # Small delay to avoid rate limiting
    time.sleep(0.5)
    
    # Test 3: POST language=fr then GET reflects fr
    print_section("Test 3: POST language=fr, verify GET reflects fr")
    try:
        # POST fr
        post_resp = session.post(
            f"{BASE_URL}/api/i18n/user-preference",
            json={"language": "fr"},
            timeout=10
        )
        post_data = post_resp.json() if post_resp.status_code == 200 else {}
        post_success = post_resp.status_code == 200 and post_data.get("language") == "fr"
        
        print(f"   POST Status: {post_resp.status_code}, Response: {json.dumps(post_data)}")
        
        time.sleep(0.5)
        
        # GET to verify
        get_resp = session.get(f"{BASE_URL}/api/i18n/user-preference", timeout=10)
        get_data = get_resp.json() if get_resp.status_code == 200 else {}
        get_success = get_resp.status_code == 200 and get_data.get("language") == "fr"
        
        print(f"   GET Status: {get_resp.status_code}, Language: {get_data.get('language')}")
        
        print_result(3, "POST fr + GET verification", post_success and get_success,
                    f"POST: {post_data.get('language')}, GET: {get_data.get('language')}")
    except Exception as e:
        print_result(3, "POST fr + GET", False, f"Error: {str(e)}")
    
    time.sleep(0.5)
    
    # Test 4: GET /api/auth/me language_preference reflects fr
    print_section("Test 4: GET /api/auth/me reflects language_preference=fr")
    try:
        response = session.get(f"{BASE_URL}/api/auth/me", timeout=10)
        data = response.json() if response.status_code == 200 else {}
        lang_pref = data.get("language_preference")
        
        print_result(4, "Profile language_preference=fr", 
                    response.status_code == 200 and lang_pref == "fr",
                    f"Status: {response.status_code}, language_preference: {lang_pref}")
    except Exception as e:
        print_result(4, "GET /api/auth/me", False, f"Error: {str(e)}")
    
    time.sleep(0.5)
    
    # Test 5: Switch to de then GET reflects de
    print_section("Test 5: Switch to de, verify GET reflects de")
    try:
        # POST de
        post_resp = session.post(
            f"{BASE_URL}/api/i18n/user-preference",
            json={"language": "de"},
            timeout=10
        )
        post_data = post_resp.json() if post_resp.status_code == 200 else {}
        post_success = post_resp.status_code == 200 and post_data.get("language") == "de"
        
        print(f"   POST Status: {post_resp.status_code}, Response: {json.dumps(post_data)}")
        
        time.sleep(0.5)
        
        # GET to verify
        get_resp = session.get(f"{BASE_URL}/api/i18n/user-preference", timeout=10)
        get_data = get_resp.json() if get_resp.status_code == 200 else {}
        get_success = get_resp.status_code == 200 and get_data.get("language") == "de"
        
        print(f"   GET Status: {get_resp.status_code}, Language: {get_data.get('language')}")
        
        print_result(5, "POST de + GET verification", post_success and get_success,
                    f"POST: {post_data.get('language')}, GET: {get_data.get('language')}")
    except Exception as e:
        print_result(5, "POST de + GET", False, f"Error: {str(e)}")
    
    time.sleep(0.5)
    
    # Test 6: Reset language to en
    print_section("Test 6: Reset to en")
    try:
        # POST en
        post_resp = session.post(
            f"{BASE_URL}/api/i18n/user-preference",
            json={"language": "en"},
            timeout=10
        )
        post_data = post_resp.json() if post_resp.status_code == 200 else {}
        post_success = post_resp.status_code == 200 and post_data.get("language") == "en"
        
        print(f"   POST Status: {post_resp.status_code}, Response: {json.dumps(post_data)}")
        
        time.sleep(0.5)
        
        # GET to verify
        get_resp = session.get(f"{BASE_URL}/api/i18n/user-preference", timeout=10)
        get_data = get_resp.json() if get_resp.status_code == 200 else {}
        get_success = get_resp.status_code == 200 and get_data.get("language") == "en"
        
        print(f"   GET Status: {get_resp.status_code}, Language: {get_data.get('language')}")
        
        print_result(6, "POST en + GET verification", post_success and get_success,
                    f"POST: {post_data.get('language')}, GET: {get_data.get('language')}")
    except Exception as e:
        print_result(6, "POST en + GET", False, f"Error: {str(e)}")
    
    print_section("Test Complete")
    print("\n✅ All i18n backend contract tests completed")
    print("Focus: No backend regression in i18n endpoints after frontend refactor\n")

if __name__ == "__main__":
    main()
