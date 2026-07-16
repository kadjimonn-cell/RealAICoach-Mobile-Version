# Learning Hub Access Issue - Test Report

## Test Information
- **Date**: 2026-05-20 05:04 UTC
- **URL**: https://admin-policy-hub.preview.emergentagent.com
- **Objective**: Reproduce Learning Hub access behavior showing "Please sign in" error for authenticated users
- **Tester**: Testing Agent (E2)
- **Test Credentials**: fedapay.prod.retest.219df6d8@gmail.com / FedapayLive#2026Aa!

## Test Results Summary

### ❌ CRITICAL ISSUE CONFIRMED

| Test Case | Expected Result | Actual Result | Status |
|-----------|-----------------|---------------|--------|
| Login | Successful login | ✅ Logged in successfully | PASS |
| User Authentication | User appears authenticated | ✅ Notification bell (4 unread), User badge visible, PREMIUM status shown | PASS |
| Navigate to Learning Hub | Access granted | ❌ Error: "Please sign in to access AI Learning Hub." | **FAIL** |
| Retry Button | Should not appear for authenticated users | ❌ Retry button present | **FAIL** |
| Final URL | /ai-learning-hub | ✅ https://admin-policy-hub.preview.emergentagent.com/ai-learning-hub | PASS |

## Detailed Test Evidence

### Step 1: Login Flow
- ✅ Successfully logged in with provided credentials
- ✅ Redirected to home page after login
- ✅ Session established (cookies set)

### Step 2: Authentication Verification
**User appears fully authenticated:**
- ✅ Notification bell visible with "4" unread notifications
- ✅ User profile visible in sidebar: "FedaPay Prod Retest User"
- ✅ Email shown: fedapay.prod.retest.219df6d8@gmail.com
- ✅ Premium badge displayed: "⭐ PREMIUM"
- ✅ Sidebar shows "Unlimited" access
- ✅ All authenticated features accessible (Home, Features, etc.)

### Step 3: Learning Hub Access
**Navigation:**
- ✅ Learning Hub link visible in sidebar under "AI TOOLS" section
- ✅ Successfully navigated to /ai-learning-hub
- ✅ Final URL: https://admin-policy-hub.preview.emergentagent.com/ai-learning-hub

**Error State:**
- ❌ Page displays error icon (alert circle)
- ❌ Error message: "Please sign in to access AI Learning Hub."
- ❌ Retry button present with testid: `ai-learning-hub-retry-btn`
- ❌ Learning Hub content NOT loaded

### Step 4: Retry Button Test
- ✅ Retry button is clickable
- ❌ Error persists after clicking Retry
- ❌ Learning Hub still shows "Please sign in" message

## Root Cause Analysis

### Issue: Cookie-Based Auth vs Token-Based Auth Check

**Location**: `/app/frontend/src/components/learning-hub/EnterpriseLearningHubScreen.tsx` (lines 424-427)

**Problem Code**:
```typescript
if (!user?.user_id) { setHasSessionToken(false); setError(tx('learningHub.auth.signInRequired', 'Please sign in to access AI Learning Hub.')); setLoading(false); return; }
const token = await ensureAuthTokenLoaded();
setHasSessionToken(Boolean(token));
if (!token) { setError(tx('learningHub.auth.signInRequired', 'Please sign in to access AI Learning Hub.')); setLoading(false); return; }
```

**Root Cause**:
1. **App Configuration**: `/app/frontend/src/services/api.ts` line 18 sets `WEB_COOKIE_ONLY_AUTH = true`
2. **Token Function Behavior**: When `WEB_COOKIE_ONLY_AUTH` is true, `getAuthToken()` always returns `null` on web (lines 45-48):
   ```typescript
   async function getAuthToken(): Promise<string | null> {
     if (WEB_COOKIE_ONLY_AUTH && typeof window !== 'undefined') {
       cachedToken = null;
       return null;
     }
     // ... rest of function
   }
   ```
3. **Learning Hub Check**: The component calls `ensureAuthTokenLoaded()` which calls `getAuthToken()`, getting `null`
4. **Error Trigger**: Since token is `null`, the component shows the error message even though the user IS authenticated via cookies

### Why This Happens

The Learning Hub component is checking for a **session token** (token-based auth) when the application uses **cookie-based authentication**. The user is fully authenticated (cookies are valid), but the Learning Hub incorrectly requires a token that doesn't exist in cookie-only auth mode.

### Evidence

**From api.ts (line 18)**:
```typescript
const WEB_COOKIE_ONLY_AUTH = true;
```

**From api.ts (lines 45-48)**:
```typescript
if (WEB_COOKIE_ONLY_AUTH && typeof window !== 'undefined') {
  cachedToken = null;
  return null;
}
```

**From EnterpriseLearningHubScreen.tsx (lines 425-427)**:
```typescript
const token = await ensureAuthTokenLoaded();
setHasSessionToken(Boolean(token));
if (!token) { setError(tx('learningHub.auth.signInRequired', 'Please sign in to access AI Learning Hub.')); setLoading(false); return; }
```

## Impact Assessment

### Severity: **CRITICAL**
- **Affected Users**: All web users (100% of web traffic)
- **Feature Impact**: Learning Hub is completely inaccessible
- **User Experience**: Confusing - users are authenticated but told to sign in
- **Business Impact**: Premium feature (Learning Hub) is unusable

### Affected Components
- ❌ Learning Hub (EnterpriseLearningHubScreen)
- ✅ All other features work correctly with cookie-based auth

## Recommended Fix

### Solution: Use AuthContext Instead of Token Check

**Current (Broken)**:
```typescript
const token = await ensureAuthTokenLoaded();
setHasSessionToken(Boolean(token));
if (!token) { 
  setError(tx('learningHub.auth.signInRequired', 'Please sign in to access AI Learning Hub.')); 
  setLoading(false); 
  return; 
}
```

**Recommended Fix**:
```typescript
// Remove token check - rely on user from AuthContext
// The component already has: const { user, loading: authLoading } = useAuth();
if (!user?.user_id) { 
  setError(tx('learningHub.auth.signInRequired', 'Please sign in to access AI Learning Hub.')); 
  setLoading(false); 
  return; 
}
// Remove ensureAuthTokenLoaded() call and hasSessionToken state
// The user object from AuthContext is sufficient for cookie-based auth
```

### Alternative Fix (If Token is Required for API Calls)

If the Learning Hub API endpoints require a token in the Authorization header, then the issue is deeper:
1. The API client needs to support cookie-based auth for Learning Hub endpoints
2. OR the auth system needs to provide tokens even in cookie-only mode
3. OR Learning Hub endpoints need to accept cookie-based auth

**Note**: Backend logs show successful API calls to Learning Hub endpoints, suggesting cookie-based auth works for the API. The issue is purely in the frontend check.

## Test Verdict

### ❌ FAIL - Critical Authentication Bug

**Summary**:
- User is fully authenticated (cookies valid, session active)
- User appears authenticated in UI (notification bell, profile badge, premium status)
- Learning Hub incorrectly blocks access due to missing token
- Token doesn't exist because app uses cookie-only authentication
- Error message is misleading - user IS signed in

**Recommendation**: 
1. Remove token check from Learning Hub component
2. Rely on `user` object from AuthContext (which works with cookies)
3. Test fix with same credentials to verify Learning Hub loads correctly

## Screenshots

1. **learning-hub-authenticated-state.png**: Shows user is authenticated (home page with user profile)
2. **learning-hub-final-state.png**: Shows error message on Learning Hub page despite authentication

## Console Logs

No JavaScript errors detected. The issue is a logic error in authentication checking, not a runtime error.

## Backend Logs

Backend logs show successful authentication:
- `/api/auth/login` - 200 OK
- `/api/auth/me` - 200 OK (after initial 401)
- `/api/auth/renew-session` - 200 OK
- `/api/ai-learn/*` endpoints - 200 OK

This confirms the backend accepts cookie-based authentication. The issue is frontend-only.

---

**Test Completed**: 2026-05-20 05:04 UTC  
**Issue Status**: ❌ CONFIRMED - Critical authentication bug  
**Blocking**: Learning Hub completely inaccessible for all web users  
**Priority**: P0 - Immediate fix required
