"""
Integration tests for Workflow 2: Merchant Self-Delivery → User

Complete workflow test for:
- delivery_type=0 (Merchant self-delivery)
- shipping_type=1 (To user)

Status flow: NULL → 0 → 5 → 6
Actions: Prepare → Complete
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem, UploadedFile
from app.models.prepare_goods import PrepareGoods
from app.models.order_action import OrderAction
from app.services import prepare_goods_service, order_action_service


@pytest.fixture
async def workflow_2_order(async_session: AsyncSession):
    """Create test order for workflow 2"""
    order = Order(
        id=10002,
        order_sn="ORD_WF2_001",
        shop_id=1,
        user_id=100,
        shipping_type=1,  # To user (direct)
        shipping_status=0,
        order_status=1,
        total_price=200.00,
        create_time=datetime.now()
    )

    order_item = OrderItem(
        id=20002,
        order_id=10002,
        product_id=302,
        sku_id=402,
        quantity=3,
        price=66.67,
        create_time=datetime.now()
    )

    async_session.add(order)
    async_session.add(order_item)
    await async_session.commit()
    await async_session.refresh(order)

    return order


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_2_complete_flow(async_session: AsyncSession, workflow_2_order: Order):
    """
    Test complete Workflow 2: Merchant Self-Delivery → User

    This is the simplest workflow - merchant prepares and delivers directly to user.

    Steps:
    1. Merchant creates prepare package (delivery_type=0, shipping_type=1)
    2. Merchant marks prepare complete (prepare_status: NULL → 0)
    3. Merchant delivers to user (prepare_status: 0 → 5 → 6)
    """

    # Step 1: Merchant creates prepare package
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_2_order.id],
        shop_id=1,
        delivery_type=0,  # Merchant self-delivery
        shipping_type=1,  # To user (direct)
        warehouse_id=None  # No warehouse in this workflow
    )

    assert prepare_package is not None
    assert prepare_package.delivery_type == 0
    assert prepare_package.shipping_type == 1
    assert prepare_package.prepare_status is None
    assert prepare_package.warehouse_id is None  # No warehouse
    assert prepare_package.shop_id == 1

    # Step 2: Merchant marks prepare complete with photo
    photo_1 = UploadedFile(
        id=30005,
        file_url="/uploads/merchant_prepare_wf2_001.jpg",
        file_name="prepare_photo.jpg",
        file_size=123456,
        create_time=datetime.now()
    )
    async_session.add(photo_1)
    await async_session.flush()

    # Update prepare status to 0 (已备货)
    success = await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=0
    )
    assert success is True

    # Create order action for merchant prepare
    action_1 = await order_action_service.create_order_action(
        session=async_session,
        order_id=workflow_2_order.id,
        action_type=0,  # Prepare
        create_by=1,  # Merchant ID
        file_ids=[photo_1.id]
    )

    assert action_1.action_type == 0

    # Update order shipping_status to 1 (prepared)
    await async_session.execute(
        Order.__table__.update()
        .where(Order.id == workflow_2_order.id)
        .values(shipping_status=1)
    )
    await async_session.commit()

    # Step 3: Merchant delivers directly to user
    photo_2 = UploadedFile(
        id=30006,
        file_url="/uploads/merchant_delivery_wf2_001.jpg",
        file_name="delivery_photo.jpg",
        file_size=234567,
        create_time=datetime.now()
    )
    async_session.add(photo_2)
    await async_session.flush()

    # Update prepare status to 5 (已送达)
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=5
    )

    # Create delivery complete action
    action_2 = await order_action_service.create_order_action(
        session=async_session,
        order_id=workflow_2_order.id,
        action_type=5,  # Complete
        create_by=1,  # Merchant ID
        file_ids=[photo_2.id]
    )

    assert action_2.action_type == 5

    # Mark workflow complete
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=6
    )

    # Update order to complete
    await async_session.execute(
        Order.__table__.update()
        .where(Order.id == workflow_2_order.id)
        .values(
            shipping_status=6,
            order_status=2,  # Completed
            finish_time=datetime.now()
        )
    )
    await async_session.commit()

    # Verification: Check audit trail
    actions = await order_action_service.get_order_actions(
        session=async_session,
        order_id=workflow_2_order.id
    )

    # Workflow 2 should only have 2 actions (simplest workflow)
    assert len(actions) == 2
    assert actions[0].action_type == 0  # Prepare
    assert actions[1].action_type == 5  # Complete

    # Verify all actions have photo evidence
    for action in actions:
        assert action.logistics_voucher_file is not None
        files = await order_action_service.get_action_files(
            session=async_session,
            action_id=action.id
        )
        assert len(files) == 1

    # Verify final state
    await async_session.refresh(workflow_2_order)
    await async_session.refresh(prepare_package)

    assert workflow_2_order.shipping_status == 6
    assert workflow_2_order.order_status == 2
    assert workflow_2_order.finish_time is not None
    assert prepare_package.prepare_status == 6


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_2_no_warehouse_required(async_session: AsyncSession, workflow_2_order: Order):
    """Test that workflow 2 does not require warehouse_id"""

    # Create prepare package without warehouse_id (should succeed)
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_2_order.id],
        shop_id=1,
        delivery_type=0,
        shipping_type=1,  # To user
        warehouse_id=None  # Should be None for direct delivery
    )

    assert prepare_package.warehouse_id is None
    assert prepare_package.delivery_type == 0
    assert prepare_package.shipping_type == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_2_multiple_orders_in_package(async_session: AsyncSession, workflow_2_order: Order):
    """Test merchant can prepare multiple orders in one package"""

    # Create second order
    order_2 = Order(
        id=10003,
        order_sn="ORD_WF2_002",
        shop_id=1,
        user_id=101,
        shipping_type=1,
        shipping_status=0,
        order_status=1,
        total_price=150.00,
        create_time=datetime.now()
    )
    async_session.add(order_2)
    await async_session.commit()

    # Create prepare package with multiple orders
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_2_order.id, order_2.id],  # Multiple orders
        shop_id=1,
        delivery_type=0,
        shipping_type=1,
        warehouse_id=None
    )

    assert prepare_package is not None
    # order_ids should be comma-separated
    assert "10002" in prepare_package.order_ids
    assert "10003" in prepare_package.order_ids
    assert "," in prepare_package.order_ids

    # Verify items from both orders
    assert len(prepare_package.items) >= 1  # At least one item from the orders


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_2_action_timeline_order(async_session: AsyncSession, workflow_2_order: Order):
    """Test that action timeline is correctly ordered"""

    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_2_order.id],
        shop_id=1,
        delivery_type=0,
        shipping_type=1,
        warehouse_id=None
    )

    # Create multiple actions with time gaps
    import asyncio

    # Action 1: Prepare
    action_1 = await order_action_service.create_order_action(
        session=async_session,
        order_id=workflow_2_order.id,
        action_type=0,
        create_by=1,
        file_ids=None
    )

    await asyncio.sleep(0.1)  # Small delay

    # Action 2: Complete
    action_2 = await order_action_service.create_order_action(
        session=async_session,
        order_id=workflow_2_order.id,
        action_type=5,
        create_by=1,
        file_ids=None
    )

    # Retrieve actions
    actions = await order_action_service.get_order_actions(
        session=async_session,
        order_id=workflow_2_order.id
    )

    # Should be ordered by create_time ascending
    assert len(actions) == 2
    assert actions[0].id == action_1.id
    assert actions[1].id == action_2.id
    assert actions[0].create_time <= actions[1].create_time
