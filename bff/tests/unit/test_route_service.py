import pytest

from app.schemas.order import OrderItem, OrderSummary, WarehouseSnapshot
from app.services.route_service import build_route_plan


@pytest.mark.asyncio
async def test_build_route_plan_generates_sequence():
    orders = [
        OrderSummary(
            order_sn="TOD1",
            shipping_status=0,
            order_status=1,
            receiver_name="Jane",
            receiver_phone="555",
            receiver_address="123 Main St",
            receiver_city="Toronto",
            receiver_province="ON",
            receiver_postal_code="M5J",
            shipping_status_label="Not Shipped",
            order_status_label="Pending",
            pickup_location=WarehouseSnapshot(
                id=1,
                name="Warehouse A",
                address="45 Depot Ave, Toronto, ON",
                latitude=43.7,
                longitude=-79.4
            ),
            items=[
                OrderItem(sku_id=1, sku_code="SKU-1", product_name="Cement", quantity=2)
            ]
        )
    ]

    plan = await build_route_plan(orders)

    assert plan.id
    assert plan.stops[0].sequence == 1
    assert plan.stops[0].order_sn == "TOD1"
