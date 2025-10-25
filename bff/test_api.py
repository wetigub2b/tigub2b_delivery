#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:9000/api"

# Step 1: Login
print("=" * 60)
print("Testing Login API")
print("=" * 60)

login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"phone": "15888888888", "code": "123456"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

login_data = login_response.json()
access_token = login_data.get("accessToken")
print(f"✅ Login successful")
print(f"Token: {access_token[:50]}...")

# Step 2: Test orders/assigned API
print("\n" + "=" * 60)
print("Testing /orders/assigned API")
print("=" * 60)

headers = {"Authorization": f"Bearer {access_token}"}
orders_response = requests.get(f"{BASE_URL}/orders/assigned", headers=headers)

if orders_response.status_code != 200:
    print(f"❌ Orders API failed: {orders_response.status_code}")
    print(orders_response.text)
    exit(1)

orders = orders_response.json()
print(f"✅ Orders API successful")
print(f"Total orders: {len(orders)}")

# Count by status
status_counts = {}
for order in orders:
    status = order['shipping_status']
    status_label = order['shipping_status_label']
    if status not in status_counts:
        status_counts[status] = {'label': status_label, 'count': 0}
    status_counts[status]['count'] += 1

print("\nOrders by status:")
for status, data in sorted(status_counts.items()):
    print(f"  {data['label']} (status={status}): {data['count']} orders")

# Show sample orders
print("\nSample orders:")
for order in orders[:3]:
    print(f"  - {order['order_sn']}: {order['receiver_name']} ({order['shipping_status_label']})")

# Step 3: Test routes/optimize API
print("\n" + "=" * 60)
print("Testing /routes/optimize API")
print("=" * 60)

route_response = requests.post(f"{BASE_URL}/routes/optimize", headers=headers)

if route_response.status_code != 200:
    print(f"❌ Routes API failed: {route_response.status_code}")
    print(route_response.text)
    exit(1)

route_data = route_response.json()
print(f"✅ Routes API successful")
print(f"Total stops in route: {len(route_data.get('stops', []))}")

print("\n" + "=" * 60)
print("All tests passed!")
print("=" * 60)
