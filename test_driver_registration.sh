#!/bin/bash

# Test script for driver registration endpoint
# No authentication required - this is a public registration endpoint

echo "==================================="
echo "Driver Registration Test"
echo "==================================="
echo ""

# Generate unique phone number for testing
TIMESTAMP=$(date +%s)
TEST_PHONE="1$(printf "%010d" $TIMESTAMP | tail -c 10)"

echo "Testing driver registration with:"
echo "  Phone: $TEST_PHONE"
echo "  Name: Test Driver $TIMESTAMP"
echo ""

# Make the API call
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
  https://testdelivery.wetigu.com/api/auth/register-driver \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Driver $TIMESTAMP\",
    \"phone\": \"$TEST_PHONE\",
    \"email\": \"testdriver${TIMESTAMP}@example.com\",
    \"password\": \"test123456\",
    \"license_number\": \"DL${TIMESTAMP}\",
    \"vehicle_type\": \"van\",
    \"vehicle_plate\": \"ABC${TIMESTAMP:6}\",
    \"vehicle_model\": \"Test Van Model\"
  }")

# Extract HTTP code and body
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')

echo "Response (HTTP $HTTP_CODE):"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ SUCCESS: Driver registration endpoint is working!"
  echo ""
  echo "Note: The driver account is created as INACTIVE and requires admin approval."
  echo "Check the database with: sudo mysql -e 'USE tigu_b2b; SELECT * FROM sys_user WHERE phonenumber=\"$TEST_PHONE\";'"
else
  echo "❌ FAILED: Registration returned HTTP $HTTP_CODE"
  echo ""
  echo "Troubleshooting:"
  echo "1. Make sure the BFF server is running (check: ps aux | grep uvicorn)"
  echo "2. Update the port in this script if server runs on different port"
  echo "3. Check server logs for errors"
  echo "4. Verify database connectivity"
fi

echo ""
echo "==================================="
