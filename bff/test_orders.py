#!/usr/bin/env python3
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.order import Order
from app.services import order_service

async def test_fetch_orders():
    async with AsyncSessionLocal() as session:
        try:
            # Test the exact same query the service uses
            orders = await order_service.fetch_assigned_orders(session, driver_id=1)
            print(f"✓ Successfully fetched {len(orders)} orders")
            if orders:
                print(f"First order: {orders[0].order_sn}")
        except Exception as e:
            print(f"✗ Error fetching orders:")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fetch_orders())
