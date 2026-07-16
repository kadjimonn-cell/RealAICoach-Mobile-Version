#!/usr/bin/env python3
"""
Issue 12 i18n Backend Testing - Auto-Translate Endpoints
Tests:
1. POST /api/i18n/auto-translate with payload {"texts":["Welcome","Start now"],"target_language":"fr"} -> expect 200 and translations object
2. POST /api/i18n/auto-translate/jobs with payload {"languages":["fr"]} -> expect 200 and job_id
3. GET /api/i18n/auto-translate/jobs/status/{job_id} -> expect status JSON (queued/completed) and results shape
4. Ensure no ObjectId serialization errors or 500s in responses
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "https://admin-policy-hub.preview.emergentagent.com"

def test_auto_translate_batch() -> Dict[str, Any]:
    """Test 1: POST /api/i18n/auto-translate with texts and target_language"""
    print("\n" + "="*60)
    print("TEST 1: POST /api/i18n/auto-translate (batch translation)")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/api/i18n/auto-translate"
        # Note: Review request says "target_language" but endpoint code uses "lang"
        # Testing with "target_language" as per review request
        payload = {
            "texts": ["Welcome", "Start now"],
            "target_language": "fr"
        }
        
        print(f"Request URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print(f"Note: Testing with 'target_language' as per review request")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"Response Body: {json.dumps(response_json, indent=2)}")
            
            # Check for translations object
            has_translations = 'translations' in response_json
            print(f"Has 'translations' key: {has_translations}")
            
            if has_translations:
                translations = response_json.get('translations', {})
                print(f"Translations count: {len(translations)}")
                print(f"Translations: {translations}")
        except Exception as e:
            print(f"Response Body (text): {response.text[:500]}")
            print(f"JSON parse error: {str(e)}")
        
        # Check for ObjectId serialization errors
        if "ObjectId" in response.text:
            print("❌ FAIL: ObjectId serialization error detected in response")
            return {"status": "FAIL", "code": response.status_code, "error": "ObjectId serialization error"}
        
        if response.status_code == 200:
            if 'response_json' in locals() and has_translations:
                print("✅ PASS: Auto-translate batch returned 200 with translations object")
                return {
                    "status": "PASS", 
                    "code": response.status_code, 
                    "body": response_json,
                    "translations": translations
                }
            else:
                print("⚠️ WARNING: 200 returned but missing translations object")
                return {"status": "FAIL", "code": response.status_code, "error": "Missing translations object"}
        elif response.status_code == 500:
            print(f"❌ FAIL: Server error 500")
            return {"status": "FAIL", "code": response.status_code, "body": response.text[:500]}
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return {"status": "FAIL", "code": response.status_code, "body": response.text[:500]}
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return {"status": "FAIL", "error": str(e)}


def test_auto_translate_jobs_create() -> Dict[str, Any]:
    """Test 2: POST /api/i18n/auto-translate/jobs with languages array"""
    print("\n" + "="*60)
    print("TEST 2: POST /api/i18n/auto-translate/jobs (create job)")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/api/i18n/auto-translate/jobs"
        payload = {
            "languages": ["fr"]
        }
        
        print(f"Request URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"Response Body: {json.dumps(response_json, indent=2)}")
            
            # Check for job_id
            has_job_id = 'job_id' in response_json
            job_id = response_json.get('job_id', '')
            print(f"Has 'job_id' key: {has_job_id}")
            print(f"Job ID: {job_id}")
        except Exception as e:
            print(f"Response Body (text): {response.text[:500]}")
            print(f"JSON parse error: {str(e)}")
        
        # Check for ObjectId serialization errors
        if "ObjectId" in response.text:
            print("❌ FAIL: ObjectId serialization error detected in response")
            return {"status": "FAIL", "code": response.status_code, "error": "ObjectId serialization error"}
        
        if response.status_code == 200:
            if 'response_json' in locals() and has_job_id and job_id:
                print("✅ PASS: Auto-translate job created with job_id")
                return {
                    "status": "PASS", 
                    "code": response.status_code, 
                    "body": response_json,
                    "job_id": job_id
                }
            else:
                print("⚠️ WARNING: 200 returned but missing job_id")
                return {"status": "FAIL", "code": response.status_code, "error": "Missing job_id"}
        elif response.status_code == 500:
            print(f"❌ FAIL: Server error 500")
            return {"status": "FAIL", "code": response.status_code, "body": response.text[:500]}
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return {"status": "FAIL", "code": response.status_code, "body": response.text[:500]}
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return {"status": "FAIL", "error": str(e)}


def test_auto_translate_jobs_status(job_id: str) -> Dict[str, Any]:
    """Test 3: GET /api/i18n/auto-translate/jobs/status/{job_id}"""
    print("\n" + "="*60)
    print(f"TEST 3: GET /api/i18n/auto-translate/jobs/status/{job_id}")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/api/i18n/auto-translate/jobs/status/{job_id}"
        
        print(f"Request URL: {url}")
        
        # Poll for status (max 3 attempts with 2 second delay)
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            print(f"\nAttempt {attempt}/{max_attempts}...")
            
            response = requests.get(url, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            
            try:
                response_json = response.json()
                print(f"Response Body: {json.dumps(response_json, indent=2)}")
                
                # Check for status field
                has_status = 'status' in response_json
                job_status = response_json.get('status', '')
                has_results = 'results' in response_json
                
                print(f"Has 'status' key: {has_status}")
                print(f"Job Status: {job_status}")
                print(f"Has 'results' key: {has_results}")
                
                # Check for ObjectId serialization errors
                if "ObjectId" in response.text:
                    print("❌ FAIL: ObjectId serialization error detected in response")
                    return {"status": "FAIL", "code": response.status_code, "error": "ObjectId serialization error"}
                
                if response.status_code == 200:
                    if has_status and job_status in ['queued', 'running', 'completed', 'error']:
                        print(f"✅ PASS: Job status endpoint returned valid status: {job_status}")
                        return {
                            "status": "PASS", 
                            "code": response.status_code, 
                            "body": response_json,
                            "job_status": job_status,
                            "has_results": has_results
                        }
                    else:
                        print("⚠️ WARNING: 200 returned but invalid/missing status")
                        return {"status": "FAIL", "code": response.status_code, "error": "Invalid or missing status"}
                elif response.status_code == 404:
                    print(f"❌ FAIL: Job not found (404)")
                    return {"status": "FAIL", "code": response.status_code, "error": "Job not found"}
                elif response.status_code == 500:
                    print(f"❌ FAIL: Server error 500")
                    return {"status": "FAIL", "code": response.status_code, "body": response.text[:500]}
                else:
                    print(f"❌ FAIL: Expected 200, got {response.status_code}")
                    return {"status": "FAIL", "code": response.status_code, "body": response.text[:500]}
                    
            except Exception as e:
                print(f"Response Body (text): {response.text[:500]}")
                print(f"JSON parse error: {str(e)}")
                return {"status": "FAIL", "error": f"JSON parse error: {str(e)}"}
            
            # Wait before next attempt if not completed
            if attempt < max_attempts and job_status in ['queued', 'running']:
                print(f"Job still {job_status}, waiting 2 seconds...")
                time.sleep(2)
        
        print("⚠️ Job did not complete within polling window")
        return {"status": "PASS", "code": 200, "note": "Job queued/running but not completed"}
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return {"status": "FAIL", "error": str(e)}


def main():
    """Run all i18n backend tests for Issue 12"""
    print("\n" + "="*60)
    print("ISSUE 12 i18n BACKEND TESTING - AUTO-TRANSLATE ENDPOINTS")
    print(f"Base URL: {BASE_URL}")
    print("="*60)
    
    results = {}
    
    # Test 1: Auto-translate batch
    results['auto_translate_batch'] = test_auto_translate_batch()
    
    # Test 2: Create translation job
    results['auto_translate_jobs_create'] = test_auto_translate_jobs_create()
    
    # Test 3: Check job status (if job was created)
    if results['auto_translate_jobs_create']['status'] == 'PASS' and 'job_id' in results['auto_translate_jobs_create']:
        job_id = results['auto_translate_jobs_create']['job_id']
        results['auto_translate_jobs_status'] = test_auto_translate_jobs_status(job_id)
    else:
        print("\n⚠️ Skipping job status test - job creation failed")
        results['auto_translate_jobs_status'] = {"status": "SKIPPED", "reason": "Job creation failed"}
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = result.get('status', 'UNKNOWN')
        code = result.get('code', 'N/A')
        
        # Format test name
        display_name = test_name.replace('_', ' ').title()
        
        # Status emoji
        if status == 'PASS':
            emoji = "✅"
        elif status == 'FAIL':
            emoji = "❌"
        elif status == 'SKIPPED':
            emoji = "⏭️"
        else:
            emoji = "❓"
        
        print(f"{emoji} {display_name}: {status} (HTTP {code})")
    
    print("\n" + "="*60)
    print("DETAILED RESULTS")
    print("="*60)
    
    # Count results
    total = len([r for r in results.values() if r.get('status') != 'SKIPPED'])
    passed = len([r for r in results.values() if r.get('status') == 'PASS'])
    failed = len([r for r in results.values() if r.get('status') == 'FAIL'])
    
    print(f"\nTotal Tests Run: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    
    if total > 0:
        print(f"Success Rate: {(passed/total*100):.1f}%")
    
    # Check for ObjectId errors
    has_objectid_error = any('ObjectId' in str(r.get('error', '')) or 'ObjectId' in str(r.get('body', '')) for r in results.values())
    if has_objectid_error:
        print("\n⚠️ WARNING: ObjectId serialization errors detected!")
    
    # Check for 500 errors
    has_500_error = any(r.get('code') == 500 for r in results.values())
    if has_500_error:
        print("\n⚠️ WARNING: Server 500 errors detected!")
    
    # Detailed failure info
    if failed > 0:
        print("\n" + "-"*60)
        print("FAILED TESTS DETAILS:")
        print("-"*60)
        for test_name, result in results.items():
            if result.get('status') == 'FAIL':
                print(f"\n❌ {test_name.replace('_', ' ').title()}")
                print(f"   Status Code: {result.get('code', 'N/A')}")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                if 'body' in result:
                    print(f"   Response: {str(result['body'])[:300]}")
    
    print("\n" + "="*60)
    
    # Return exit code
    all_passed = all(r.get('status') in ['PASS', 'SKIPPED'] for r in results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
