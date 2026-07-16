#!/usr/bin/env python3
"""
Quick verification test for public frontend routes /welcome and /about-us
Tests that these routes are reachable and don't have broken backend dependencies
"""

import requests
import sys
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://admin-policy-hub.preview.emergentagent.com')
BASE_URL = BACKEND_URL

def test_public_route(route_path):
    """Test if a public route is accessible"""
    url = f"{BASE_URL}{route_path}"
    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        print(f"Status Code: {response.status_code}")
        print(f"Final URL: {response.url}")
        print(f"Content Length: {len(response.content)} bytes")
        
        # Check if response is HTML
        content_type = response.headers.get('content-type', '')
        print(f"Content-Type: {content_type}")
        
        # Check for common error indicators
        if response.status_code == 200:
            # Check if it's actually HTML content
            if 'text/html' in content_type:
                print("✅ Route is accessible and returns HTML")
                
                # Check for common error messages in content
                content_lower = response.text.lower()
                if 'error' in content_lower and 'boundary' not in content_lower:
                    print("⚠️  Warning: 'error' found in page content")
                if '404' in content_lower or 'not found' in content_lower:
                    print("⚠️  Warning: '404' or 'not found' found in page content")
                if 'cannot get' in content_lower:
                    print("⚠️  Warning: 'cannot get' found in page content")
                    
                return True
            else:
                print(f"⚠️  Warning: Expected HTML but got {content_type}")
                return True
        elif response.status_code in [301, 302, 303, 307, 308]:
            print(f"✅ Route redirects to: {response.url}")
            return True
        else:
            print(f"❌ Route returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 10 seconds")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_backend_health():
    """Test if backend API is responding"""
    url = f"{BASE_URL}/api/health"
    print(f"\n{'='*60}")
    print(f"Testing Backend Health: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Backend API is healthy")
            try:
                data = response.json()
                print(f"Response: {data}")
            except:
                print(f"Response: {response.text[:200]}")
            return True
        else:
            print(f"⚠️  Backend health check returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Backend health check failed: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("PUBLIC ROUTES VERIFICATION TEST")
    print("="*60)
    print(f"Backend URL: {BASE_URL}")
    
    results = {}
    
    # Test backend health first
    results['backend_health'] = test_backend_health()
    
    # Test public routes
    results['welcome'] = test_public_route('/welcome')
    results['about_us'] = test_public_route('/about-us')
    
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
        print("✅ ALL TESTS PASSED")
        print("="*60)
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()
