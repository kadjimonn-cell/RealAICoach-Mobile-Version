#!/bin/bash

# Workflow Builder API Smoke Test
# Testing Feature 4 Workflow Builder API endpoints

BASE_URL="https://visa-polish-v2.preview.emergentagent.com"
FALLBACK_USER_ID="guest123456789012"

echo "=========================================="
echo "Workflow Builder API Smoke Test"
echo "Base URL: $BASE_URL"
echo "Fallback User ID: $FALLBACK_USER_ID"
echo "=========================================="
echo ""

# Test 1: GET /api/workflows/templates
echo "Test 1: GET /api/workflows/templates"
echo "Expected: 200 status with templates payload"
echo "---"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$BASE_URL/api/workflows/templates")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')
echo "Status: $HTTP_STATUS"
echo "Response: $BODY" | head -c 500
echo ""
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ PASS: GET /api/workflows/templates returned 200"
else
    echo "❌ FAIL: GET /api/workflows/templates returned $HTTP_STATUS (expected 200)"
fi
echo ""
echo "=========================================="
echo ""

# Test 2: GET /api/workflows/usage/stats with fallback_user_id
echo "Test 2: GET /api/workflows/usage/stats?fallback_user_id=$FALLBACK_USER_ID"
echo "Expected: 200 status with usage stats"
echo "---"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$BASE_URL/api/workflows/usage/stats?fallback_user_id=$FALLBACK_USER_ID")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')
echo "Status: $HTTP_STATUS"
echo "Response: $BODY"
echo ""
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ PASS: GET /api/workflows/usage/stats returned 200"
else
    echo "❌ FAIL: GET /api/workflows/usage/stats returned $HTTP_STATUS (expected 200)"
fi
echo ""
echo "=========================================="
echo ""

# Test 3: POST /api/workflows with fallback_user_id and minimal payload
echo "Test 3: POST /api/workflows?fallback_user_id=$FALLBACK_USER_ID"
echo "Expected: 200 status with workflow_id"
echo "---"
PAYLOAD='{"name":"Test Workflow","description":"Smoke test workflow","nodes":[],"edges":[],"enabled":false,"fallback_user_id":"'$FALLBACK_USER_ID'"}'
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$BASE_URL/api/workflows?fallback_user_id=$FALLBACK_USER_ID" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')
echo "Status: $HTTP_STATUS"
echo "Response: $BODY"
echo ""

# Extract workflow_id for next tests
WORKFLOW_ID=$(echo "$BODY" | grep -o '"workflow_id":"[^"]*"' | cut -d'"' -f4)
echo "Extracted workflow_id: $WORKFLOW_ID"
echo ""

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "201" ]; then
    echo "✅ PASS: POST /api/workflows returned $HTTP_STATUS"
else
    echo "❌ FAIL: POST /api/workflows returned $HTTP_STATUS (expected 200/201)"
fi
echo ""
echo "=========================================="
echo ""

# Test 4: POST /api/workflows/{workflow_id}/execute with fallback_user_id
if [ -n "$WORKFLOW_ID" ]; then
    echo "Test 4: POST /api/workflows/$WORKFLOW_ID/execute?fallback_user_id=$FALLBACK_USER_ID"
    echo "Expected: 200 status with execution_id/status"
    echo "---"
    
    # First, enable the workflow
    echo "Enabling workflow first..."
    ENABLE_PAYLOAD='{"enabled":true}'
    curl -s -X PUT "$BASE_URL/api/workflows/$WORKFLOW_ID?fallback_user_id=$FALLBACK_USER_ID" \
      -H "Content-Type: application/json" \
      -d "$ENABLE_PAYLOAD" > /dev/null
    
    EXEC_PAYLOAD='{"input_data":{},"fallback_user_id":"'$FALLBACK_USER_ID'"}'
    RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$BASE_URL/api/workflows/$WORKFLOW_ID/execute?fallback_user_id=$FALLBACK_USER_ID" \
      -H "Content-Type: application/json" \
      -d "$EXEC_PAYLOAD")
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')
    echo "Status: $HTTP_STATUS"
    echo "Response: $BODY"
    echo ""
    
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "✅ PASS: POST /api/workflows/{workflow_id}/execute returned 200"
    else
        echo "❌ FAIL: POST /api/workflows/{workflow_id}/execute returned $HTTP_STATUS (expected 200)"
    fi
else
    echo "⚠️  SKIP: Test 4 skipped - no workflow_id from Test 3"
fi
echo ""
echo "=========================================="
echo ""

# Test 5: DELETE /api/workflows/{workflow_id} with fallback_user_id
if [ -n "$WORKFLOW_ID" ]; then
    echo "Test 5: DELETE /api/workflows/$WORKFLOW_ID?fallback_user_id=$FALLBACK_USER_ID"
    echo "Expected: 200 status with success message"
    echo "---"
    RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X DELETE "$BASE_URL/api/workflows/$WORKFLOW_ID?fallback_user_id=$FALLBACK_USER_ID")
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')
    echo "Status: $HTTP_STATUS"
    echo "Response: $BODY"
    echo ""
    
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "✅ PASS: DELETE /api/workflows/{workflow_id} returned 200"
    else
        echo "❌ FAIL: DELETE /api/workflows/{workflow_id} returned $HTTP_STATUS (expected 200)"
    fi
else
    echo "⚠️  SKIP: Test 5 skipped - no workflow_id from Test 3"
fi
echo ""
echo "=========================================="
echo ""
echo "Smoke Test Complete"
echo "=========================================="
