# Backend Auth CORS Regression Test Report
**Date**: 2026-06-12 07:42 UTC  
**Tester**: Testing Agent (E2)  
**Backend URL**: https://admin-policy-hub.preview.emergentagent.com

## Executive Summary

**CRITICAL ISSUE FOUND**: Auth endpoints are returning wildcard CORS origin with credentials enabled, which violates browser security policy.

**Test Results**: 3/7 PASS (42.9%)

## Test Validation Points

### ✅ PASS: Telemetry Endpoint CORS Safety
- `/api/auth/session-bootstrap-telemetry` correctly returns wildcard WITHOUT credentials
- No browser security violation on this endpoint
- Status: **RESOLVED** (as reported in previous test on 2026-06-12 07:37 UTC)

### ✅ PASS: Unknown Origin Not Reflected
- Unknown/malicious origins are NOT reflected in `Access-Control-Allow-Origin`
- Wildcard is used instead of reflecting untrusted origins
- This prevents origin reflection attacks

### ❌ FAIL: Auth Login Endpoint CORS Headers
**Endpoint**: `/api/auth/login`

**Issue**: Returns wildcard origin WITH credentials enabled

**Evidence**:
```
access-control-allow-origin: *
access-control-allow-credentials: true
```

**Impact**: CRITICAL - Browsers will reject responses with this combination per CORS specification

**Affected Origins**:
- Shell origins (https://app.emergent.sh, https://www.emergent.sh)
- Backend origin (https://admin-policy-hub.preview.emergentagent.com)
- All other origins

### ❌ FAIL: Auth Register Endpoint CORS Headers
**Endpoint**: `/api/auth/register`

**Issue**: Preflight (OPTIONS) returns wildcard origin, but should return specific allowed origin

**Evidence**:
```
OPTIONS /api/auth/register
Origin: https://app.emergent.sh

Response:
access-control-allow-origin: *
access-control-allow-credentials: (not present)
```

**Expected**:
```
access-control-allow-origin: https://app.emergent.sh
access-control-allow-credentials: true
```

## Root Cause Analysis

### Backend Code Configuration (CORRECT)
The FastAPI CORS middleware in `/app/backend/middleware.py` is correctly configured:

```python
ALLOWED_ORIGINS = _build_allowed_origins()  # Specific origins including shell origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # NOT wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)
```

Shell origins are explicitly added:
```python
shell_origins = [
    "https://app.emergent.sh",
    "https://www.emergent.sh",
    "https://app.emergentagent.com",
    "https://www.emergentagent.com",
]
```

### Suspected Root Cause: Ingress/Proxy Layer Override

The CORS headers being returned suggest an **ingress or proxy layer** is overriding the backend CORS configuration:

**Evidence**:
1. Headers include `access-control-max-age: 300` (not set by FastAPI middleware)
2. Headers include `access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH` (includes HEAD which is not in backend config)
3. Wildcard is being applied uniformly across all origins

**Likely Culprit**: Kubernetes Ingress annotations or nginx proxy configuration adding CORS headers

## Detailed Test Results

### Test 1: Login with Shell Origin (app.emergent.sh)
- **Status Code**: 200 ✅
- **CORS Headers**: ❌ FAIL
  - `Access-Control-Allow-Origin: *`
  - `Access-Control-Allow-Credentials: true`
  - **Issue**: Wildcard + credentials = browser security violation

### Test 2: Login with Shell Origin (www.emergent.sh)
- **Status Code**: 200 ✅
- **CORS Headers**: ❌ FAIL
  - Same issue as Test 1

### Test 3: Login with Backend Origin
- **Status Code**: 200 ✅
- **CORS Headers**: ❌ FAIL
  - Same issue as Test 1

### Test 4: Register Preflight + POST
- **Preflight Status**: 204 ✅
- **Preflight CORS**: ❌ FAIL
  - Expected: `Access-Control-Allow-Origin: https://app.emergent.sh`
  - Actual: `Access-Control-Allow-Origin: *`
- **POST Status**: 422 ✅ (validation error, expected)
- **POST CORS**: ❌ FAIL (same wildcard issue)

### Test 5: Telemetry Endpoint (Backend Origin)
- **Status Code**: 403 ✅ (expected for unauthenticated)
- **CORS Headers**: ✅ PASS
  - `Access-Control-Allow-Origin: *`
  - `Access-Control-Allow-Credentials: (not present)`
  - **Safe**: Wildcard without credentials is allowed

### Test 6: Telemetry Endpoint (Shell Origin)
- **Status Code**: 403 ✅
- **CORS Headers**: ✅ PASS
  - Same as Test 5

### Test 7: Unknown Origin Not Reflected
- **Status Code**: 200 ✅
- **CORS Headers**: ✅ PASS
  - `Access-Control-Allow-Origin: *`
  - Unknown origin NOT reflected (good)

## Recommendations

### CRITICAL: Fix Wildcard + Credentials on Auth Endpoints

**Priority**: P0 - CRITICAL

**Action Required**: 
1. Identify the ingress/proxy layer adding wildcard CORS headers
2. Configure ingress to either:
   - **Option A**: Remove CORS headers entirely (let FastAPI middleware handle it)
   - **Option B**: Configure ingress with specific allowed origins (not wildcard)

**Affected Endpoints**:
- `/api/auth/login`
- `/api/auth/register`
- Potentially other `/api/auth/*` endpoints

**Expected Behavior**:
For allowed origins (shell origins, backend origin):
```
Request Origin: https://app.emergent.sh
Response:
  Access-Control-Allow-Origin: https://app.emergent.sh
  Access-Control-Allow-Credentials: true
```

For unknown origins:
```
Request Origin: https://malicious-site.com
Response:
  (No CORS headers, or specific allowed origin, NOT wildcard with credentials)
```

### Investigation Steps

1. Check Kubernetes Ingress annotations:
   ```bash
   kubectl get ingress -n <namespace> -o yaml | grep -A 10 "cors"
   ```

2. Check nginx configuration:
   ```bash
   kubectl get configmap -n <namespace> | grep nginx
   kubectl describe configmap <nginx-config> -n <namespace>
   ```

3. Look for annotations like:
   - `nginx.ingress.kubernetes.io/enable-cors: "true"`
   - `nginx.ingress.kubernetes.io/cors-allow-origin: "*"`
   - `nginx.ingress.kubernetes.io/cors-allow-credentials: "true"`

## Conclusion

**Status**: ❌ CRITICAL ISSUE FOUND

The backend auth regression test has identified a **critical CORS security violation** on auth endpoints. While the telemetry endpoint has been correctly fixed (as reported in previous test), the main auth endpoints (`/api/auth/login`, `/api/auth/register`) are still returning wildcard origin with credentials enabled.

**Impact**: 
- Browsers will reject auth responses due to CORS policy violation
- Users attempting to authenticate from shell origins will experience auth failures
- This is a blocking issue for production deployment

**Next Steps**:
1. Investigate and fix ingress/proxy CORS configuration
2. Re-run this test suite to verify fix
3. Ensure all auth endpoints return specific origins (not wildcard) when credentials are enabled

---

**Test Script**: `/app/backend_test.py`  
**Test Report**: `/app/auth_cors_test_report.md`
