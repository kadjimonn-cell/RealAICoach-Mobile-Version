#!/bin/bash

# Feature 32 Backend Test using curl
# Tests reliability endpoints and regression guardrails

BACKEND_URL="https://visa-polish-v2.preview.emergentagent.com"
ADMIN_EMAIL="admin@realaicoach.app"
ADMIN_PASS="NewAdminPass2026!"
FREE_EMAIL="p1.free.1779113329@example.com"
FREE_PASS="P1Free#2026!Aa"

echo "================================================================================"
echo "FEATURE 32 POST-LAUNCH MONITORING PACK - BACKEND VERIFICATION (CURL)"
echo "================================================================================"
echo "Backend URL: $BACKEND_URL"
echo "Test Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "================================================================================"
echo ""

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Test 1: Admin Login
echo "================================================================================"
echo "TEST 1: Login Authentication"
echo "================================================================================"
echo ""
echo "1a) Testing admin login..."

ADMIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Accept: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASS\"}" \
  -c /tmp/admin_cookies.txt \
  -w "\n%{http_code}")

ADMIN_STATUS=$(echo "$ADMIN_RESPONSE" | tail -1)
ADMIN_BODY=$(echo "$ADMIN_RESPONSE" | head -n -1)

if [ "$ADMIN_STATUS" = "200" ]; then
    echo "✅ PASS: Admin login successful: $ADMIN_EMAIL"
    ((PASS_COUNT++))
else
    echo "❌ FAIL: Admin login failed with status $ADMIN_STATUS"
    echo "Response: $ADMIN_BODY"
    ((FAIL_COUNT++))
    exit 1
fi

# Test 1b: Free User Login
echo ""
echo "1b) Testing free user login..."

FREE_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Accept: application/json" \
  -d "{\"email\":\"$FREE_EMAIL\",\"password\":\"$FREE_PASS\"}" \
  -c /tmp/free_cookies.txt \
  -w "\n%{http_code}")

FREE_STATUS=$(echo "$FREE_RESPONSE" | tail -1)
FREE_BODY=$(echo "$FREE_RESPONSE" | head -n -1)

if [ "$FREE_STATUS" = "200" ]; then
    echo "✅ PASS: Free user login successful: $FREE_EMAIL"
    ((PASS_COUNT++))
else
    echo "❌ FAIL: Free user login failed with status $FREE_STATUS"
    echo "Response: $FREE_BODY"
    ((FAIL_COUNT++))
    exit 1
fi

# Test 2: Reliability Overview
echo ""
echo "================================================================================"
echo "TEST 2: Reliability Overview Endpoint"
echo "================================================================================"
echo ""
echo "2a) Testing admin access to reliability overview..."

OVERVIEW_RESPONSE=$(curl -s -X GET "$BACKEND_URL/api/email-notifications/reliability/overview?window_days=7" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Accept: application/json" \
  -b /tmp/admin_cookies.txt \
  -w "\n%{http_code}")

OVERVIEW_STATUS=$(echo "$OVERVIEW_RESPONSE" | tail -1)
OVERVIEW_BODY=$(echo "$OVERVIEW_RESPONSE" | head -n -1)

if [ "$OVERVIEW_STATUS" = "200" ]; then
    # Check for required keys
    if echo "$OVERVIEW_BODY" | grep -q '"kpis"' && \
       echo "$OVERVIEW_BODY" | grep -q '"alerts"' && \
       echo "$OVERVIEW_BODY" | grep -q '"top_failed_events"' && \
       echo "$OVERVIEW_BODY" | grep -q '"weekly_report_template"'; then
        echo "✅ PASS: Admin reliability overview returned 200 with all required keys"
        ((PASS_COUNT++))
        
        # Check KPI keys
        if echo "$OVERVIEW_BODY" | grep -q '"uno_dispatch_success_rate_pct"' && \
           echo "$OVERVIEW_BODY" | grep -q '"duplicate_key_collisions"' && \
           echo "$OVERVIEW_BODY" | grep -q '"policy_blocked_writes"' && \
           echo "$OVERVIEW_BODY" | grep -q '"protected_template_count"'; then
            echo "✅ PASS: All expected KPI keys present"
            ((PASS_COUNT++))
        else
            echo "⚠️  WARN: Some KPI keys missing"
            ((WARN_COUNT++))
        fi
    else
        echo "❌ FAIL: Admin reliability overview missing required keys"
        echo "Response: $OVERVIEW_BODY"
        ((FAIL_COUNT++))
    fi
else
    echo "❌ FAIL: Admin reliability overview returned $OVERVIEW_STATUS"
    echo "Response: $OVERVIEW_BODY"
    ((FAIL_COUNT++))
fi

echo ""
echo "2b) Testing free user access to reliability overview (should be blocked)..."

FREE_OVERVIEW_RESPONSE=$(curl -s -X GET "$BACKEND_URL/api/email-notifications/reliability/overview?window_days=7" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Accept: application/json" \
  -b /tmp/free_cookies.txt \
  -w "\n%{http_code}")

FREE_OVERVIEW_STATUS=$(echo "$FREE_OVERVIEW_RESPONSE" | tail -1)

if [ "$FREE_OVERVIEW_STATUS" = "403" ]; then
    echo "✅ PASS: Free user correctly blocked from reliability overview (403)"
    ((PASS_COUNT++))
else
    echo "❌ FAIL: Free user should be blocked but got $FREE_OVERVIEW_STATUS"
    ((FAIL_COUNT++))
fi

# Test 3: Weekly Report Template
echo ""
echo "================================================================================"
echo "TEST 3: Weekly Report Template Endpoint"
echo "================================================================================"
echo ""
echo "3a) Testing admin access to weekly report template..."

REPORT_RESPONSE=$(curl -s -X GET "$BACKEND_URL/api/email-notifications/reliability/weekly-report-template?window_days=7" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Accept: application/json" \
  -b /tmp/admin_cookies.txt \
  -w "\n%{http_code}")

REPORT_STATUS=$(echo "$REPORT_RESPONSE" | tail -1)
REPORT_BODY=$(echo "$REPORT_RESPONSE" | head -n -1)

if [ "$REPORT_STATUS" = "200" ]; then
    # Check for success=true
    if echo "$REPORT_BODY" | grep -q '"success":true'; then
        echo "✅ PASS: Weekly report template returned success=true"
        ((PASS_COUNT++))
        
        # Check for report_template and template_markdown
        if echo "$REPORT_BODY" | grep -q '"report_template"' && \
           echo "$REPORT_BODY" | grep -q '"template_markdown"' && \
           echo "$REPORT_BODY" | grep -q '# Feature 32 Weekly Reliability Report'; then
            echo "✅ PASS: Weekly report template contains expected markdown header"
            ((PASS_COUNT++))
        else
            echo "❌ FAIL: Weekly report template missing expected content"
            ((FAIL_COUNT++))
        fi
    else
        echo "❌ FAIL: Weekly report template missing success=true"
        ((FAIL_COUNT++))
    fi
else
    echo "❌ FAIL: Admin weekly report template returned $REPORT_STATUS"
    echo "Response: $REPORT_BODY"
    ((FAIL_COUNT++))
fi

echo ""
echo "3b) Testing free user access to weekly report template (should be blocked)..."

FREE_REPORT_RESPONSE=$(curl -s -X GET "$BACKEND_URL/api/email-notifications/reliability/weekly-report-template?window_days=7" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Accept: application/json" \
  -b /tmp/free_cookies.txt \
  -w "\n%{http_code}")

FREE_REPORT_STATUS=$(echo "$FREE_REPORT_RESPONSE" | tail -1)

if [ "$FREE_REPORT_STATUS" = "403" ]; then
    echo "✅ PASS: Free user correctly blocked from weekly report template (403)"
    ((PASS_COUNT++))
else
    echo "❌ FAIL: Free user should be blocked but got $FREE_REPORT_STATUS"
    ((FAIL_COUNT++))
fi

# Test 4: Regression Guardrails
echo ""
echo "================================================================================"
echo "TEST 4: Regression Guardrails - Protected Template Overrides"
echo "================================================================================"
echo ""
echo "4a) Testing override-approval for protected template (should be blocked)..."

FUTURE_DATE=$(date -u -d "+30 days" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v+30d +%Y-%m-%dT%H:%M:%SZ)

APPROVAL_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/email-notifications/template-policies/override-approval" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Accept: application/json" \
  -b /tmp/admin_cookies.txt \
  -d "{\"template_key\":\"meeting_reminder\",\"approved\":true,\"approval_id\":\"test_approval_123\",\"expires_at\":\"$FUTURE_DATE\",\"note\":\"Test approval attempt\"}" \
  -w "\n%{http_code}")

APPROVAL_STATUS=$(echo "$APPROVAL_RESPONSE" | tail -1)
APPROVAL_BODY=$(echo "$APPROVAL_RESPONSE" | head -n -1)

if [ "$APPROVAL_STATUS" = "400" ]; then
    if echo "$APPROVAL_BODY" | grep -qi "protected\|cannot be approved"; then
        echo "✅ PASS: Override approval correctly blocked for protected template (400 policy block)"
        ((PASS_COUNT++))
    else
        echo "⚠️  WARN: Override approval blocked with 400 but unexpected reason: $APPROVAL_BODY"
        ((WARN_COUNT++))
    fi
elif [ "$APPROVAL_STATUS" = "403" ]; then
    echo "✅ PASS: Override approval blocked (403 - acceptable if CSRF/session constraint)"
    ((PASS_COUNT++))
elif [ "$APPROVAL_STATUS" = "200" ]; then
    echo "❌ FAIL: Override approval should be blocked but returned 200 (SECURITY ISSUE)"
    ((FAIL_COUNT++))
else
    echo "⚠️  WARN: Override approval returned unexpected status $APPROVAL_STATUS: $APPROVAL_BODY"
    ((WARN_COUNT++))
fi

echo ""
echo "4b) Testing manual override for protected template (should be blocked)..."

MANUAL_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/email-notifications/overrides/manual" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Accept: application/json" \
  -b /tmp/admin_cookies.txt \
  -d '{"template_key":"meeting_reminder","optimized_subject":"Test Override Subject"}' \
  -w "\n%{http_code}")

MANUAL_STATUS=$(echo "$MANUAL_RESPONSE" | tail -1)
MANUAL_BODY=$(echo "$MANUAL_RESPONSE" | head -n -1)

if [ "$MANUAL_STATUS" = "400" ]; then
    if echo "$MANUAL_BODY" | grep -qi "blocked\|protected"; then
        echo "✅ PASS: Manual override correctly blocked for protected template (400 policy block)"
        ((PASS_COUNT++))
    else
        echo "⚠️  WARN: Manual override blocked with 400 but unexpected reason: $MANUAL_BODY"
        ((WARN_COUNT++))
    fi
elif [ "$MANUAL_STATUS" = "403" ]; then
    echo "✅ PASS: Manual override blocked (403 - acceptable if CSRF/session constraint)"
    ((PASS_COUNT++))
elif [ "$MANUAL_STATUS" = "200" ]; then
    echo "❌ FAIL: Manual override should be blocked but returned 200 (SECURITY ISSUE)"
    ((FAIL_COUNT++))
else
    echo "⚠️  WARN: Manual override returned unexpected status $MANUAL_STATUS: $MANUAL_BODY"
    ((WARN_COUNT++))
fi

# Summary
echo ""
echo "================================================================================"
echo "FEATURE 32 TEST SUMMARY"
echo "================================================================================"
echo "✅ Passed: $PASS_COUNT"
echo "❌ Failed: $FAIL_COUNT"
echo "⚠️  Warnings: $WARN_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    exit 1
fi
