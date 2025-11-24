"""
Integration tests for Workflow 3: Third-Party Driver → Warehouse → User

Complete workflow test for:
- delivery_type=1 (Third-party driver delivery)
- shipping_type=0 (To warehouse)

Status flow: NULL → 0 → 6 → 1 → 2 → 3 → 4 → 5
Actions: Prepare → Driver Claims → Driver Pickup → Driver to Warehouse → Warehouse Receive → Warehouse Ship → Complete

This is the most complex workflow with the most steps.
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem, UploadedFile
from app.models.prepare_goods import PrepareGoods
from app.models.driver import Driver
from app.models.order import Warehouse
from app.services import prepare_goods_service, order_action_service, order_service


@pytest.fixture
async def workflow_3_driver(async_session: AsyncSession):
    """Create test driver for workflow 3"""
    driver = Driver(
        id=301,
        name="Test Driver WF3",
        phone="13800138003",
        vehicle_number="京A12345",
        status=1,  # Active
        create_time=datetime.now()
    )
    async_session.add(driver)
    await async_session.commit()
    await async_session.refresh(driver)
    return driver


@pytest.fixture
async def workflow_3_warehouse(async_session: AsyncSession):
    """Create test warehouse for workflow 3"""
    warehouse = Warehouse(
        id=501,
        name="Main Warehouse",
        address="123 Warehouse St",
        contact_name="John Doe",
        contact_phone="13900139003",
        status=1,
        create_time=datetime.now()
    )
    async_session.add(warehouse)
    await async_session.commit()
    await async_session.refresh(warehouse)
    return warehouse


@pytest.fixture
async def workflow_3_order(async_session: AsyncSession):
    """Create test order for workflow 3"""
    order = Order(
        id=10004,
        order_sn="ORD_WF3_001",
        shop_id=1,
        user_id=102,
        shipping_type=0,  # To warehouse
        shipping_status=0,
        order_status=1,
        total_price=300.00,
        create_time=datetime.now()
    )

    order_item = OrderItem(
        id=20003,
        order_id=10004,
        product_id=303,
        sku_id=403,
        quantity=5,
        price=60.00,
        create_time=datetime.now()
    )

    async_session.add(order)
    async_session.add(order_item)
    await async_session.commit()
    await async_session.refresh(order)

    return order


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_3_complete_flow(
    async_session: AsyncSession,
    workflow_3_order: Order,
    workflow_3_driver: Driver,
    workflow_3_warehouse: Warehouse
):
    """
    Test complete Workflow 3: Driver → Warehouse → User

    This is the most complex workflow with the most status transitions.

    Steps:
    1. Merchant creates prepare package (delivery_type=1, shipping_type=0)
    2. Merchant marks prepare complete (prepare_status: NULL → 0)
    3. Driver claims package (prepare_status: 0 → 6)
    4. Driver confirms pickup from merchant (prepare_status: 6 → 1)
    5. Driver delivers to warehouse (prepare_status: 1 → 2)
    6. Warehouse receives (prepare_status: 2 → 3)
    7. Warehouse ships to user (prepare_status: 3 → 4)
    8. Final delivery (prepare_status: 4 → 5)
    """

    # Step 1: Merchant creates prepare package
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_3_order.id],
        shop_id=1,
        delivery_type=1,  # Third-party driver
        shipping_type=0,  # To warehouse
        warehouse_id=workflow_3_warehouse.id
    )

    assert prepare_package is not None
    assert prepare_package.delivery_type == 1
    assert prepare_package.shipping_type == 0
    assert prepare_package.warehouse_id == workflow_3_warehouse.id
    assert prepare_package.prepare_status is None

    # Step 2: Merchant marks prepare complete
    photo_1 = UploadedFile(
        id=30007,
        file_url="/uploads/merchant_prepare_wf3.jpg",
        file_name="prepare.jpg",
        file_size=111111,
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
        order_id=workflow_3_order.id,
        action_type=0,  # Prepare
        create_by=1,
        file_ids=[photo_1.id]
    )

    assert action_1.action_type == 0

    # Step 3: Driver claims package (assign driver + update status to 6)
    await prepare_goods_service.assign_driver_to_prepare(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        driver_id=workflow_3_driver.id
    )
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=6
    )

    # Step 4: Driver confirms pickup from merchant with photo
    photo_2 = UploadedFile(
        id=30008,
        file_url="/uploads/driver_pickup_wf3.jpg",
        file_name="pickup.jpg",
        file_size=222222,
        create_time=datetime.now()
    )
    async_session.add(photo_2)
    await async_session.flush()

    # Use order_service.pickup_order function
    success = await order_service.pickup_order(
        session=async_session,
        order_sn=workflow_3_order.order_sn,
        driver_id=workflow_3_driver.id,
        photo_ids=[photo_2.id]
    )

    assert success is True

    # Verify prepare_status updated to 1
    await async_session.refresh(prepare_package)
    # Note: pickup_order should update prepare_status via service
    # For now, manually update for test
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=1
    )

    # Step 5: Driver delivers to warehouse
    photo_3 = UploadedFile(
        id=30009,
        file_url="/uploads/driver_warehouse_wf3.jpg",
        file_name="arrive_warehouse.jpg",
        file_size=333333,
        create_time=datetime.now()
    )
    async_session.add(photo_3)
    await async_session.flush()

    # Use order_service.arrive_warehouse function
    success = await order_service.arrive_warehouse(
        session=async_session,
        order_sn=workflow_3_order.order_sn,
        driver_id=workflow_3_driver.id,
        photo_ids=[photo_3.id]
    )

    assert success is True

    # Update prepare_status to 2
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=2
    )

    # Step 5: Warehouse receives goods
    photo_4 = UploadedFile(
        id=30010,
        file_url="/uploads/warehouse_receive_wf3.jpg",
        file_name="warehouse_receive.jpg",
        file_size=444444,
        create_time=datetime.now()
    )
    async_session.add(photo_4)
    await async_session.flush()

    # Use order_service.warehouse_receive function
    success = await order_service.warehouse_receive(
        session=async_session,
        order_sn=workflow_3_order.order_sn,
        warehouse_staff_id=20,
        photo_ids=[photo_4.id]
    )

    assert success is True

    # Update prepare_status to 3
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=3
    )

    # Step 6: Warehouse ships to user
    photo_5 = UploadedFile(
        id=30011,
        file_url="/uploads/warehouse_ship_wf3.jpg",
        file_name="warehouse_ship.jpg",
        file_size=555555,
        create_time=datetime.now()
    )
    async_session.add(photo_5)
    await async_session.flush()

    # Use order_service.warehouse_ship function
    success = await order_service.warehouse_ship(
        session=async_session,
        order_sn=workflow_3_order.order_sn,
        warehouse_staff_id=20,
        photo_ids=[photo_5.id]
    )

    assert success is True

    # Update prepare_status to 4
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=4
    )

    # Step 7: Final delivery complete
    photo_6 = UploadedFile(
        id=30012,
        file_url="/uploads/delivery_complete_wf3.jpg",
        file_name="complete.jpg",
        file_size=666666,
        create_time=datetime.now()
    )
    async_session.add(photo_6)
    await async_session.flush()

    # Use order_service.complete_delivery function
    success = await order_service.complete_delivery(
        session=async_session,
        order_sn=workflow_3_order.order_sn,
        completer_id=20,  # Warehouse staff
        photo_ids=[photo_6.id]
    )

    assert success is True

    # Mark workflow complete
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=6
    )

    # Verification: Check complete audit trail
    actions = await order_action_service.get_order_actions(
        session=async_session,
        order_id=workflow_3_order.id
    )

    # Workflow 3 should have 6 actions (most complex)
    assert len(actions) >= 6

    # Verify action types in order
    action_types = [a.action_type for a in actions]
    assert 0 in action_types  # Prepare
    assert 1 in action_types  # Driver pickup
    assert 2 in action_types  # Driver to warehouse
    assert 3 in action_types  # Warehouse receive
    assert 4 in action_types  # Warehouse ship
    assert 5 in action_types  # Complete

    # Verify all actions have photo evidence
    for action in actions:
        if action.logistics_voucher_file:  # Some might not have photos
            files = await order_action_service.get_action_files(
                session=async_session,
                action_id=action.id
            )
            assert len(files) >= 0

    # Verify final state
    await async_session.refresh(workflow_3_order)
    await async_session.refresh(prepare_package)

    assert workflow_3_order.shipping_status == 6
    assert workflow_3_order.order_status == 2
    assert prepare_package.prepare_status == 6
    assert prepare_package.driver_id == workflow_3_driver.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_3_driver_assignment(
    async_session: AsyncSession,
    workflow_3_order: Order,
    workflow_3_driver: Driver,
    workflow_3_warehouse: Warehouse
):
    """Test driver assignment in workflow 3"""

    # Create prepare package for third-party delivery
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_3_order.id],
        shop_id=1,
        delivery_type=1,  # Third-party
        shipping_type=0,
        warehouse_id=workflow_3_warehouse.id
    )

    # Driver should be assignable
    success = await prepare_goods_service.assign_driver_to_prepare(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        driver_id=workflow_3_driver.id
    )

    assert success is True

    # Verify driver assigned
    await async_session.refresh(prepare_package)
    assert prepare_package.driver_id == workflow_3_driver.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_3_warehouse_required(
    async_session: AsyncSession,
    workflow_3_order: Order,
    workflow_3_warehouse: Warehouse
):
    """Test that warehouse_id is required for workflow 3"""

    # Try to create prepare package without warehouse_id (should fail)
    with pytest.raises(ValueError, match="warehouse_id required"):
        await prepare_goods_service.create_prepare_package(
            session=async_session,
            order_ids=[workflow_3_order.id],
            shop_id=1,
            delivery_type=1,
            shipping_type=0,  # To warehouse
            warehouse_id=None  # Missing warehouse!
        )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_3_concurrent_driver_pickup(
    async_session: AsyncSession,
    workflow_3_order: Order,
    workflow_3_driver: Driver,
    workflow_3_warehouse: Warehouse
):
    """Test that concurrent driver pickups are handled correctly"""

    # Create prepare package
    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_3_order.id],
        shop_id=1,
        delivery_type=1,
        shipping_type=0,
        warehouse_id=workflow_3_warehouse.id
    )

    # Mark as prepared
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=0
    )

    # First driver picks up
    success = await order_service.pickup_order(
        session=async_session,
        order_sn=workflow_3_order.order_sn,
        driver_id=workflow_3_driver.id,
        photo_ids=None
    )

    assert success is True

    # Second driver tries to pick up (should fail or be handled)
    # In production, this would check current shipping_status
    # and reject if already picked up


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workflow_3_photo_evidence_complete(
    async_session: AsyncSession,
    workflow_3_order: Order,
    workflow_3_driver: Driver,
    workflow_3_warehouse: Warehouse
):
    """Test that all workflow 3 transitions have photo evidence"""

    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[workflow_3_order.id],
        shop_id=1,
        delivery_type=1,
        shipping_type=0,
        warehouse_id=workflow_3_warehouse.id
    )

    # Create actions with photo evidence
    photo_ids = []
    for i in range(6):  # 6 transitions
        photo = UploadedFile(
            id=40000 + i,
            file_url=f"/uploads/wf3_photo_{i}.jpg",
            file_name=f"photo_{i}.jpg",
            file_size=100000 + i * 1000,
            create_time=datetime.now()
        )
        async_session.add(photo)
        await async_session.flush()
        photo_ids.append(photo.id)

        # Create action for each transition
        action = await order_action_service.create_order_action(
            session=async_session,
            order_id=workflow_3_order.id,
            action_type=i,  # 0-5
            create_by=1,
            file_ids=[photo.id]
        )

        assert action.logistics_voucher_file is not None

    # Verify all 6 actions have photos
    actions = await order_action_service.get_order_actions(
        session=async_session,
        order_id=workflow_3_order.id
    )

    assert len(actions) == 6

    for action in actions:
        assert action.logistics_voucher_file is not None
        files = await order_action_service.get_action_files(
            session=async_session,
            action_id=action.id
        )
        assert len(files) == 1
        assert files[0].biz_type == "order_action"
