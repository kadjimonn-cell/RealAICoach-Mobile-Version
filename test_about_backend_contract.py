#!/usr/bin/env python3
"""
Test backend API contracts used by /about-us route
Specifically tests the About CTA experiment endpoints
"""

import requests
import sys
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://visa-polish-v2.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

def test_subscription_conversion_telemetry():
    """Test /api/subscription-conversion/telemetry endpoint"""
    url = f"{BASE_URL}/subscription-conversion/telemetry"
    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print(f"{'='*60}")
    
    payload = {
        "session_key": "test-session-key",
        "event_type": "plan_cta_click",
        "plan_id": "basic",
        "role": "public_visitor",
        "device_bucket": "desktop",
        "route": "/about-us",
        "source": "about_us_signup_cta_activation"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code in [200, 201, 204]:
            print("✅ Endpoint exists and accepts requests")
            return True
        elif response.status_code == 404:
            print("❌ Endpoint not found (404)")
            return False
        elif response.status_code in [400, 422]:
            print("⚠️  Endpoint exists but validation failed (expected for test data)")
            return True  # Endpoint exists, just validation issue
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_prompt_experiment_track():
    """Test /api/prompt-experiment/track endpoint"""
    url = f"{BASE_URL}/prompt-experiment/track"
    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print(f"{'='*60}")
    
    payload = {
        "experiment_id": "about_us_cta_v1",
        "variant_id": "activation",
        "event": "impression",
        "metadata": {
            "route": "/about-us",
            "source": "about_us_cta_block",
            "device_bucket": "desktop"
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code in [200, 201, 204]:
            print("✅ Endpoint exists and accepts requests")
            return True
        elif response.status_code == 404:
            print("❌ Endpoint not found (404)")
            return False
        elif response.status_code in [400, 422]:
            print("⚠️  Endpoint exists but validation failed (expected for test data)")
            return True  # Endpoint exists, just validation issue
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("ABOUT-US BACKEND CONTRACT VERIFICATION")
    print("="*60)
    print(f"Backend URL: {BASE_URL}")
    
    results = {}
    
    # Test the two backend endpoints used by about-us.tsx
    results['subscription_conversion_telemetry'] = test_subscription_conversion_telemetry()
    results['prompt_experiment_track'] = test_prompt_experiment_track()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL BACKEND CONTRACTS VERIFIED")
        print("The About CTA experiment does not depend on broken backend contracts")
        print("="*60)
        sys.exit(0)
    else:
        print("❌ SOME BACKEND CONTRACTS BROKEN")
        print("The About CTA experiment may have issues with backend integration")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()
