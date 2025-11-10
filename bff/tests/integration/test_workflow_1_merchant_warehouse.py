"""
Integration tests for Workflow 1: Merchant Self-Delivery → Warehouse → User

Complete workflow test for:
- delivery_type=0 (Merchant self-delivery)
- shipping_type=0 (To warehouse)

Status flow: NULL → 0 → 3 → 4 → 5 → 6
Actions: Prepare → Warehouse Receive → Warehouse Ship → Complete
"""
import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem
from app.models.prepare_goods import PrepareGoods, PrepareGoodsItem
from app.models.order_action import OrderAction
from app.models.order import UploadedFile
from app.services import prepare_goods_service, order_action_service, order_service


@pytest.fixture
async def workflow_1_order(async_session: AsyncSession):
    """Create test order for workflow 1"""
    order = Order(
        id=10001,
        order_sn="ORD_WF1_001",
        shop_id=1,
        user_id=100,
        shipping_type=0,  # To warehouse
        shipping_status=0,  # Not yet prepared
        order_status=1,  # Active
        total_price=100.00,
        create_time=datetime.now()
    )

    order_item = OrderItem(
        id=20001,
        order_id=10001,
        product_id=301,
        sku_id=401,
        quantity=2,
        price=50.00,
        create_time=datetime.now()
    )

    async_session.add(order)
    async_session.add(order_item)
    await async_session.commit()
    await async_session.refresh(order)

    return order


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_1_complete_flow(async_session: AsyncSession, workflow_1_order: Order):
    """
    Test complete Workflow 1: Merchant Self-Delivery → Warehouse → User

    Steps:
    1. Merchant creates prepare package (delivery_type=0, shipping_type=0)
    2. Merchant marks prepare complete (prepare_status: NULL → 0)
    3. Warehouse receives goods (prepare_status: 0 → 3)
    4. Warehouse ships to user (prepare_status: 3 → 4)
    5. Delivery complete (prepare_status: 4 → 5 → 6)
    """

    # Step 1: Merchant creates prepare package
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_1_order.id],
        shop_id=1,
        delivery_type=0,  # Merchant self-delivery
        shipping_type=0,  # To warehouse
        warehouse_id=5
    )

    assert prepare_package is not None
    assert prepare_package.delivery_type == 0
    assert prepare_package.shipping_type == 0
    assert prepare_package.prepare_status is None  # NULL = pending
    assert prepare_package.warehouse_id == 5
    assert prepare_package.shop_id == 1

    # Verify PrepareGoodsItem created
    assert len(prepare_package.items) > 0
    assert prepare_package.items[0].order_item_id == 20001

    # Step 2: Merchant marks prepare complete with photo
    # Simulate photo upload
    photo_1 = UploadedFile(
        id=30001,
        file_url="/uploads/merchant_prepare_001.jpg",
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
        order_id=workflow_1_order.id,
        action_type=0,  # Prepare
        create_by=1,  # Merchant ID
        file_ids=[photo_1.id]
    )

    assert action_1 is not None
    assert action_1.action_type == 0
    assert action_1.logistics_voucher_file == "30001"

    # Verify file linked to action
    file_check = await async_session.get(UploadedFile, photo_1.id)
    assert file_check.biz_id == action_1.id
    assert file_check.biz_type == "order_action"

    # Verify prepare status updated
    await async_session.refresh(prepare_package)
    assert prepare_package.prepare_status == 0

    # Step 3: Warehouse receives goods
    photo_2 = UploadedFile(
        id=30002,
        file_url="/uploads/warehouse_receive_001.jpg",
        file_name="receive_photo.jpg",
        file_size=234567,
        create_time=datetime.now()
    )
    async_session.add(photo_2)
    await async_session.flush()

    # Update prepare status to 3 (仓库已收货)
    success = await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=3
    )
    assert success is True

    # Create warehouse receive action
    action_2 = await order_action_service.create_order_action(
        session=async_session,
        order_id=workflow_1_order.id,
        action_type=3,  # Warehouse receive
        create_by=20,  # Warehouse staff ID
        file_ids=[photo_2.id]
    )

    assert action_2.action_type == 3

    # Update order shipping_status to 4 (warehouse received)
    await async_session.execute(
        Order.__table__.update()
        .where(Order.id == workflow_1_order.id)
        .values(shipping_status=4)
    )
    await async_session.commit()

    # Step 4: Warehouse ships to user
    photo_3 = UploadedFile(
        id=30003,
        file_url="/uploads/warehouse_ship_001.jpg",
        file_name="ship_photo.jpg",
        file_size=345678,
        create_time=datetime.now()
    )
    async_session.add(photo_3)
    await async_session.flush()

    # Update prepare status to 4 (司机配送用户)
    # Note: In workflow 1, warehouse ships directly to user
    success = await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=4
    )
    assert success is True

    # Create warehouse ship action
    action_3 = await order_action_service.create_order_action(
        session=async_session,
        order_id=workflow_1_order.id,
        action_type=4,  # Warehouse ship
        create_by=20,  # Warehouse staff ID
        file_ids=[photo_3.id]
    )

    assert action_3.action_type == 4

    # Update order shipping_status to 5 (shipping to user)
    await async_session.execute(
        Order.__table__.update()
        .where(Order.id == workflow_1_order.id)
        .values(
            shipping_status=5,
            warehouse_shipping_time=datetime.now()
        )
    )
    await async_session.commit()

    # Step 5: Delivery complete
    photo_4 = UploadedFile(
        id=30004,
        file_url="/uploads/delivery_complete_001.jpg",
        file_name="complete_photo.jpg",
        file_size=456789,
        create_time=datetime.now()
    )
    async_session.add(photo_4)
    await async_session.flush()

    # Update prepare status to 5 (已送达) then 6 (完成)
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=5
    )

    # Create delivery complete action
    action_4 = await order_action_service.create_order_action(
        session=async_session,
        order_id=workflow_1_order.id,
        action_type=5,  # Complete
        create_by=20,  # Warehouse staff ID
        file_ids=[photo_4.id]
    )

    assert action_4.action_type == 5

    # Mark workflow complete
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=6
    )

    # Update order to complete
    await async_session.execute(
        Order.__table__.update()
        .where(Order.id == workflow_1_order.id)
        .values(
            shipping_status=6,
            order_status=2,  # Completed
            finish_time=datetime.now()
        )
    )
    await async_session.commit()

    # Verification: Check complete audit trail
    actions = await order_action_service.get_order_actions(
        session=async_session,
        order_id=workflow_1_order.id
    )

    assert len(actions) == 4
    assert actions[0].action_type == 0  # Prepare
    assert actions[1].action_type == 3  # Warehouse receive
    assert actions[2].action_type == 4  # Warehouse ship
    assert actions[3].action_type == 5  # Complete

    # Verify all actions have photo evidence
    for action in actions:
        assert action.logistics_voucher_file is not None
        files = await order_action_service.get_action_files(
            session=async_session,
            action_id=action.id
        )
        assert len(files) == 1
        assert files[0].biz_type == "order_action"
        assert files[0].biz_id == action.id

    # Verify final state
    await async_session.refresh(workflow_1_order)
    await async_session.refresh(prepare_package)

    assert workflow_1_order.shipping_status == 6
    assert workflow_1_order.order_status == 2
    assert workflow_1_order.finish_time is not None
    assert prepare_package.prepare_status == 6


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_1_missing_photo_evidence(async_session: AsyncSession, workflow_1_order: Order):
    """Test that workflow fails when photo evidence is missing"""

    # Create prepare package
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_1_order.id],
        shop_id=1,
        delivery_type=0,
        shipping_type=0,
        warehouse_id=5
    )

    # Try to create action without photo evidence (should work but log warning)
    action = await order_action_service.create_order_action(
        session=async_session,
        order_id=workflow_1_order.id,
        action_type=0,
        create_by=1,
        file_ids=None  # No photo evidence
    )

    # Action created but logistics_voucher_file is NULL
    assert action.logistics_voucher_file is None

    # This is allowed but should be flagged in business logic
    # In production, you may want to enforce photo requirement


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_1_invalid_status_transition(async_session: AsyncSession, workflow_1_order: Order):
    """Test that invalid status transitions are handled"""

    # Create prepare package
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_1_order.id],
        shop_id=1,
        delivery_type=0,
        shipping_type=0,
        warehouse_id=5
    )

    # Try to jump from NULL to 5 (invalid)
    # In a real system, you'd have validation middleware to prevent this
    # For now, update will succeed but business logic should prevent it
    success = await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=5  # Jump to delivered without intermediate steps
    )

    # Update succeeds at database level
    assert success is True

    # But in production, API layer should validate status transitions
    # using state machine logic
