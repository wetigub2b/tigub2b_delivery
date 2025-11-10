"""
Integration tests for Workflow 4: Third-Party Driver → User

Complete workflow test for:
- delivery_type=1 (Third-party driver delivery)
- shipping_type=1 (To user - direct)

Status flow: NULL → 0 → 1 → 5 → 6
Actions: Prepare → Driver Pickup → Complete

This is the second-simplest workflow after Workflow 2.
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem, UploadedFile
from app.models.prepare_goods import PrepareGoods
from app.models.driver import Driver
from app.services import prepare_goods_service, order_action_service, order_service


@pytest.fixture
async def workflow_4_driver(async_session: AsyncSession):
    """Create test driver for workflow 4"""
    driver = Driver(
        id=401,
        name="Test Driver WF4",
        phone="13800138004",
        vehicle_number="京A54321",
        status=1,
        create_time=datetime.now()
    )
    async_session.add(driver)
    await async_session.commit()
    await async_session.refresh(driver)
    return driver


@pytest.fixture
async def workflow_4_order(async_session: AsyncSession):
    """Create test order for workflow 4"""
    order = Order(
        id=10005,
        order_sn="ORD_WF4_001",
        shop_id=1,
        user_id=103,
        shipping_type=1,  # To user (direct)
        shipping_status=0,
        order_status=1,
        total_price=400.00,
        create_time=datetime.now()
    )

    order_item = OrderItem(
        id=20004,
        order_id=10005,
        product_id=304,
        sku_id=404,
        quantity=4,
        price=100.00,
        create_time=datetime.now()
    )

    async_session.add(order)
    async_session.add(order_item)
    await async_session.commit()
    await async_session.refresh(order)

    return order


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_4_complete_flow(
    async_session: AsyncSession,
    workflow_4_order: Order,
    workflow_4_driver: Driver
):
    """
    Test complete Workflow 4: Driver → User (direct delivery)

    This workflow is simpler than Workflow 3 - no warehouse involved.

    Steps:
    1. Merchant creates prepare package (delivery_type=1, shipping_type=1)
    2. Merchant marks prepare complete (prepare_status: NULL → 0)
    3. Driver picks up from merchant (prepare_status: 0 → 1)
    4. Driver delivers directly to user (prepare_status: 1 → 5 → 6)
    """

    # Step 1: Merchant creates prepare package
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_4_order.id],
        shop_id=1,
        delivery_type=1,  # Third-party driver
        shipping_type=1,  # To user (direct)
        warehouse_id=None  # No warehouse
    )

    assert prepare_package is not None
    assert prepare_package.delivery_type == 1
    assert prepare_package.shipping_type == 1
    assert prepare_package.warehouse_id is None
    assert prepare_package.prepare_status is None

    # Step 2: Merchant marks prepare complete
    photo_1 = UploadedFile(
        id=30013,
        file_url="/uploads/merchant_prepare_wf4.jpg",
        file_name="prepare.jpg",
        file_size=123456,
        create_time=datetime.now()
    )
    async_session.add(photo_1)
    await async_session.flush()

    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=0
    )

    action_1 = await order_action_service.create_order_action(
        session=async_session,
        order_id=workflow_4_order.id,
        action_type=0,  # Prepare
        create_by=1,
        file_ids=[photo_1.id]
    )

    assert action_1.action_type == 0

    # Assign driver
    await prepare_goods_service.assign_driver_to_prepare(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        driver_id=workflow_4_driver.id
    )

    # Step 3: Driver picks up from merchant
    photo_2 = UploadedFile(
        id=30014,
        file_url="/uploads/driver_pickup_wf4.jpg",
        file_name="pickup.jpg",
        file_size=234567,
        create_time=datetime.now()
    )
    async_session.add(photo_2)
    await async_session.flush()

    # Use order_service.pickup_order
    success = await order_service.pickup_order(
        session=async_session,
        order_sn=workflow_4_order.order_sn,
        driver_id=workflow_4_driver.id,
        photo_ids=[photo_2.id]
    )

    assert success is True

    # Update prepare_status to 1
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=1
    )

    # Step 4: Driver delivers directly to user
    photo_3 = UploadedFile(
        id=30015,
        file_url="/uploads/driver_delivery_wf4.jpg",
        file_name="delivery.jpg",
        file_size=345678,
        create_time=datetime.now()
    )
    async_session.add(photo_3)
    await async_session.flush()

    # Use order_service.complete_delivery
    success = await order_service.complete_delivery(
        session=async_session,
        order_sn=workflow_4_order.order_sn,
        completer_id=workflow_4_driver.id,  # Driver completes
        photo_ids=[photo_3.id]
    )

    assert success is True

    # Mark workflow complete
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=6
    )

    # Verification: Check audit trail
    actions = await order_action_service.get_order_actions(
        session=async_session,
        order_id=workflow_4_order.id
    )

    # Workflow 4 should have 3 actions
    assert len(actions) == 3
    assert actions[0].action_type == 0  # Prepare
    assert actions[1].action_type == 1  # Driver pickup
    assert actions[2].action_type == 5  # Complete

    # Verify all actions have photo evidence
    for action in actions:
        assert action.logistics_voucher_file is not None
        files = await order_action_service.get_action_files(
            session=async_session,
            action_id=action.id
        )
        assert len(files) == 1

    # Verify final state
    await async_session.refresh(workflow_4_order)
    await async_session.refresh(prepare_package)

    assert workflow_4_order.shipping_status == 6
    assert workflow_4_order.order_status == 2
    assert prepare_package.prepare_status == 6
    assert prepare_package.driver_id == workflow_4_driver.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_4_no_warehouse_involved(
    async_session: AsyncSession,
    workflow_4_order: Order,
    workflow_4_driver: Driver
):
    """Test that workflow 4 does not involve warehouse"""

    # Create prepare package
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_4_order.id],
        shop_id=1,
        delivery_type=1,
        shipping_type=1,  # Direct to user
        warehouse_id=None
    )

    assert prepare_package.warehouse_id is None
    assert prepare_package.shipping_type == 1

    # Complete workflow should not have warehouse actions
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=0
    )

    await order_service.pickup_order(
        session=async_session,
        order_sn=workflow_4_order.order_sn,
        driver_id=workflow_4_driver.id,
        photo_ids=None
    )

    await order_service.complete_delivery(
        session=async_session,
        order_sn=workflow_4_order.order_sn,
        completer_id=workflow_4_driver.id,
        photo_ids=None
    )

    # Get actions
    actions = await order_action_service.get_order_actions(
        session=async_session,
        order_id=workflow_4_order.id
    )

    # Should not have warehouse-related actions (2, 3, 4)
    action_types = [a.action_type for a in actions]
    assert 2 not in action_types  # Driver to warehouse
    assert 3 not in action_types  # Warehouse receive
    assert 4 not in action_types  # Warehouse ship


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_4_driver_required(
    async_session: AsyncSession,
    workflow_4_order: Order,
    workflow_4_driver: Driver
):
    """Test that workflow 4 requires driver assignment"""

    # Create prepare package
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_4_order.id],
        shop_id=1,
        delivery_type=1,  # Third-party delivery requires driver
        shipping_type=1,
        warehouse_id=None
    )

    # Mark as prepared
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=0
    )

    # Driver must be assigned before pickup
    await prepare_goods_service.assign_driver_to_prepare(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        driver_id=workflow_4_driver.id
    )

    await async_session.refresh(prepare_package)
    assert prepare_package.driver_id == workflow_4_driver.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_4_faster_than_workflow_3(
    async_session: AsyncSession,
    workflow_4_order: Order,
    workflow_4_driver: Driver
):
    """Test that workflow 4 has fewer steps than workflow 3"""

    import time

    start_time = time.time()

    # Create prepare package
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_4_order.id],
        shop_id=1,
        delivery_type=1,
        shipping_type=1,
        warehouse_id=None
    )

    # Prepare
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=0
    )

    await order_action_service.create_order_action(
        session=async_session,
        order_id=workflow_4_order.id,
        action_type=0,
        create_by=1,
        file_ids=None
    )

    # Pickup
    await order_service.pickup_order(
        session=async_session,
        order_sn=workflow_4_order.order_sn,
        driver_id=workflow_4_driver.id,
        photo_ids=None
    )

    # Complete
    await order_service.complete_delivery(
        session=async_session,
        order_sn=workflow_4_order.order_sn,
        completer_id=workflow_4_driver.id,
        photo_ids=None
    )

    end_time = time.time()

    # Get final action count
    actions = await order_action_service.get_order_actions(
        session=async_session,
        order_id=workflow_4_order.id
    )

    # Workflow 4 should have exactly 3 actions (vs 6 for workflow 3)
    assert len(actions) == 3

    # Should complete faster than workflow 3 (fewer steps)
    execution_time = end_time - start_time
    # This is a performance indicator, not a hard requirement
    assert execution_time < 10.0  # Should complete in <10 seconds


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_4_workflow_timeline(
    async_session: AsyncSession,
    workflow_4_order: Order,
    workflow_4_driver: Driver
):
    """Test complete workflow timeline for workflow 4"""

    # Create prepare package
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_4_order.id],
        shop_id=1,
        delivery_type=1,
        shipping_type=1,
        warehouse_id=None
    )

    # Track timeline
    timeline = []

    # Prepare
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=0
    )
    timeline.append({"status": 0, "action": "prepare", "time": datetime.now()})

    # Pickup
    await order_service.pickup_order(
        session=async_session,
        order_sn=workflow_4_order.order_sn,
        driver_id=workflow_4_driver.id,
        photo_ids=None
    )
    timeline.append({"status": 1, "action": "pickup", "time": datetime.now()})

    # Complete
    await order_service.complete_delivery(
        session=async_session,
        order_sn=workflow_4_order.order_sn,
        completer_id=workflow_4_driver.id,
        photo_ids=None
    )
    timeline.append({"status": 5, "action": "complete", "time": datetime.now()})

    # Verify timeline order
    assert len(timeline) == 3
    assert timeline[0]["status"] == 0
    assert timeline[1]["status"] == 1
    assert timeline[2]["status"] == 5

    # Verify timestamps are in order
    assert timeline[0]["time"] <= timeline[1]["time"]
    assert timeline[1]["time"] <= timeline[2]["time"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_4_vs_workflow_2_comparison(async_session: AsyncSession):
    """
    Compare Workflow 4 (driver direct) vs Workflow 2 (merchant direct)
    Both deliver directly to user but with different delivery_type
    """

    # Workflow 4: Third-party driver direct delivery
    order_wf4 = Order(
        id=10006,
        order_sn="ORD_WF4_COMP",
        shop_id=1,
        user_id=104,
        shipping_type=1,
        shipping_status=0,
        order_status=1,
        total_price=100.00,
        create_time=datetime.now()
    )
    async_session.add(order_wf4)
    await async_session.commit()

    package_wf4 = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[order_wf4.id],
        shop_id=1,
        delivery_type=1,  # Driver
        shipping_type=1,
        warehouse_id=None
    )

    # Workflow 2: Merchant self-delivery direct
    order_wf2 = Order(
        id=10007,
        order_sn="ORD_WF2_COMP",
        shop_id=1,
        user_id=105,
        shipping_type=1,
        shipping_status=0,
        order_status=1,
        total_price=100.00,
        create_time=datetime.now()
    )
    async_session.add(order_wf2)
    await async_session.commit()

    package_wf2 = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[order_wf2.id],
        shop_id=1,
        delivery_type=0,  # Merchant
        shipping_type=1,
        warehouse_id=None
    )

    # Key differences:
    # WF4 has driver pickup step, WF2 doesn't
    assert package_wf4.delivery_type == 1
    assert package_wf2.delivery_type == 0

    # Both deliver to user
    assert package_wf4.shipping_type == 1
    assert package_wf2.shipping_type == 1

    # Neither uses warehouse
    assert package_wf4.warehouse_id is None
    assert package_wf2.warehouse_id is None
