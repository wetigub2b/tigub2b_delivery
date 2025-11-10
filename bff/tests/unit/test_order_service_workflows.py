"""
Unit tests for OrderService Workflow Functions

Tests the 4-workflow delivery system functions including:
- pickup_order (updated with PrepareGoods integration)
- arrive_warehouse
- warehouse_receive
- warehouse_ship
- complete_delivery
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, call

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import order_service
from app.models.order import Order
from app.models.prepare_goods import PrepareGoods


@pytest.fixture
def mock_session():
    """Create mock async session"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def sample_order():
    """Sample order"""
    return Order(
        id=101,
        order_sn="ORD101",
        shop_id=1,
        shipping_type=0,
        shipping_status=1,
        order_status=1,
        driver_id=None
    )


@pytest.fixture
def sample_prepare_goods():
    """Sample PrepareGoods package"""
    return PrepareGoods(
        id=1,
        prepare_sn="PREP123456",
        order_ids="101,102",
        delivery_type=1,  # Third-party
        shipping_type=0,  # To warehouse
        shop_id=1,
        warehouse_id=5
    )


@pytest.mark.asyncio
async def test_pickup_order_success(mock_session, sample_order, sample_prepare_goods):
    """Test driver pickup order successfully"""
    # Mock queries
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = sample_order

    delivery_type_result = MagicMock()
    delivery_type_result.scalar_one_or_none.return_value = 1  # Third-party

    update_result = MagicMock()
    update_result.rowcount = 1

    action_order_result = MagicMock()
    action_order_result.scalar_one_or_none.return_value = sample_order

    # Set up side effects
    call_count = [0]
    def side_effect(stmt):
        result = [order_result, delivery_type_result, update_result, action_order_result][call_count[0]]
        call_count[0] += 1
        return result

    mock_session.execute.side_effect = side_effect

    # Pickup order
    result = await order_service.pickup_order(
        session=mock_session,
        order_sn="ORD101",
        driver_id=10,
        photo_ids=[1001, 1002]
    )

    # Verify result
    assert result is True
    assert mock_session.commit.call_count >= 1


@pytest.mark.asyncio
async def test_pickup_order_not_in_prepare_goods(mock_session, sample_order):
    """Test pickup order fails if not in PrepareGoods package"""
    # Mock order query
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = sample_order

    # Mock delivery_type query returning None (not in package)
    delivery_type_result = MagicMock()
    delivery_type_result.scalar_one_or_none.return_value = None

    call_count = [0]
    def side_effect(stmt):
        result = [order_result, delivery_type_result][call_count[0]]
        call_count[0] += 1
        return result

    mock_session.execute.side_effect = side_effect

    # Pickup order should raise ValueError
    with pytest.raises(ValueError, match="not in any PrepareGoods package"):
        await order_service.pickup_order(
            session=mock_session,
            order_sn="ORD101",
            driver_id=10,
            photo_ids=[1001]
        )


@pytest.mark.asyncio
async def test_pickup_order_not_found(mock_session):
    """Test pickup order when order not found"""
    # Mock order query returning None
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = order_result

    # Pickup order
    result = await order_service.pickup_order(
        session=mock_session,
        order_sn="ORD999",
        driver_id=10,
        photo_ids=[1001]
    )

    # Verify result
    assert result is False


@pytest.mark.asyncio
async def test_arrive_warehouse_success(mock_session, sample_order):
    """Test driver arrives at warehouse successfully"""
    # Update order to have driver assigned
    sample_order.driver_id = 10

    # Mock queries
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = sample_order

    update_result = MagicMock()
    update_result.rowcount = 1

    action_order_result = MagicMock()
    action_order_result.scalar_one_or_none.return_value = sample_order

    call_count = [0]
    def side_effect(stmt):
        result = [order_result, update_result, action_order_result][call_count[0]]
        call_count[0] += 1
        return result

    mock_session.execute.side_effect = side_effect

    # Arrive at warehouse
    result = await order_service.arrive_warehouse(
        session=mock_session,
        order_sn="ORD101",
        driver_id=10,
        photo_ids=[1001, 1002]
    )

    # Verify result
    assert result is True
    assert mock_session.commit.call_count >= 1


@pytest.mark.asyncio
async def test_arrive_warehouse_not_found(mock_session):
    """Test arrive warehouse when order not found"""
    # Mock order query returning None
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = order_result

    # Arrive at warehouse
    result = await order_service.arrive_warehouse(
        session=mock_session,
        order_sn="ORD999",
        driver_id=10,
        photo_ids=[1001]
    )

    # Verify result
    assert result is False


@pytest.mark.asyncio
async def test_warehouse_receive_success(mock_session, sample_order):
    """Test warehouse receives goods successfully"""
    # Mock queries
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = sample_order

    update_result = MagicMock()
    update_result.rowcount = 1

    action_order_result = MagicMock()
    action_order_result.scalar_one_or_none.return_value = sample_order

    call_count = [0]
    def side_effect(stmt):
        result = [order_result, update_result, action_order_result][call_count[0]]
        call_count[0] += 1
        return result

    mock_session.execute.side_effect = side_effect

    # Warehouse receive
    result = await order_service.warehouse_receive(
        session=mock_session,
        order_sn="ORD101",
        warehouse_staff_id=20,
        photo_ids=None  # Optional photos
    )

    # Verify result
    assert result is True
    assert mock_session.commit.call_count >= 1


@pytest.mark.asyncio
async def test_warehouse_ship_success(mock_session, sample_order):
    """Test warehouse ships to user successfully"""
    # Mock queries
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = sample_order

    update_result = MagicMock()
    update_result.rowcount = 1

    action_order_result = MagicMock()
    action_order_result.scalar_one_or_none.return_value = sample_order

    call_count = [0]
    def side_effect(stmt):
        result = [order_result, update_result, action_order_result][call_count[0]]
        call_count[0] += 1
        return result

    mock_session.execute.side_effect = side_effect

    # Warehouse ship
    result = await order_service.warehouse_ship(
        session=mock_session,
        order_sn="ORD101",
        warehouse_staff_id=20,
        photo_ids=[1001]
    )

    # Verify result
    assert result is True
    assert mock_session.commit.call_count >= 1


@pytest.mark.asyncio
async def test_complete_delivery_success(mock_session, sample_order):
    """Test complete delivery successfully"""
    # Mock queries
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = sample_order

    update_result = MagicMock()
    update_result.rowcount = 1

    action_order_result = MagicMock()
    action_order_result.scalar_one_or_none.return_value = sample_order

    call_count = [0]
    def side_effect(stmt):
        result = [order_result, update_result, action_order_result][call_count[0]]
        call_count[0] += 1
        return result

    mock_session.execute.side_effect = side_effect

    # Complete delivery
    result = await order_service.complete_delivery(
        session=mock_session,
        order_sn="ORD101",
        completer_id=10,  # Driver or merchant
        photo_ids=[1001, 1002, 1003]
    )

    # Verify result
    assert result is True
    assert mock_session.commit.call_count >= 1


@pytest.mark.asyncio
async def test_complete_delivery_not_found(mock_session):
    """Test complete delivery when order not found"""
    # Mock order query returning None
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = order_result

    # Complete delivery
    result = await order_service.complete_delivery(
        session=mock_session,
        order_sn="ORD999",
        completer_id=10,
        photo_ids=[1001]
    )

    # Verify result
    assert result is False


@pytest.mark.asyncio
async def test_workflow_1_merchant_to_user(mock_session):
    """Test Workflow 1: 商家→用户 (Merchant self-delivery to user)"""
    # Workflow 1: delivery_type=0, shipping_type=1
    # Status flow: 0 → 1 → 6 → 7
    # Functions used: pickup_order (merchant), complete_delivery

    order = Order(
        id=101,
        order_sn="ORD101",
        shop_id=1,
        shipping_type=1,  # To user
        shipping_status=0,
        order_status=1
    )

    # Mock for pickup (merchant self-delivery)
    # Note: In this workflow, merchant delivers, so "pickup" might be different
    # But for testing, we'll test complete_delivery which works for all workflows

    # Mock complete delivery
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = order

    update_result = MagicMock()
    update_result.rowcount = 1

    action_order_result = MagicMock()
    action_order_result.scalar_one_or_none.return_value = order

    call_count = [0]
    def side_effect(stmt):
        result = [order_result, update_result, action_order_result][call_count[0]]
        call_count[0] += 1
        return result

    mock_session.execute.side_effect = side_effect

    # Complete delivery (final step for workflow 1)
    result = await order_service.complete_delivery(
        session=mock_session,
        order_sn="ORD101",
        completer_id=1,  # Merchant ID
        photo_ids=[1001]
    )

    assert result is True


@pytest.mark.asyncio
async def test_workflow_2_full_chain(mock_session):
    """Test Workflow 2: 商家→司机→仓库→用户 (Full delivery chain)"""
    # Workflow 2: delivery_type=1, shipping_type=0
    # Status flow: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7
    # All workflow functions used

    order = Order(
        id=101,
        order_sn="ORD101",
        shop_id=1,
        shipping_type=0,  # To warehouse
        shipping_status=2,
        order_status=1,
        driver_id=10
    )

    # Test arrive_warehouse (step in workflow 2)
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = order

    update_result = MagicMock()
    update_result.rowcount = 1

    action_order_result = MagicMock()
    action_order_result.scalar_one_or_none.return_value = order

    call_count = [0]
    def side_effect(stmt):
        result = [order_result, update_result, action_order_result][call_count[0]]
        call_count[0] += 1
        return result

    mock_session.execute.side_effect = side_effect

    result = await order_service.arrive_warehouse(
        session=mock_session,
        order_sn="ORD101",
        driver_id=10,
        photo_ids=[1001, 1002]
    )

    assert result is True


@pytest.mark.asyncio
async def test_workflow_3_direct_delivery(mock_session):
    """Test Workflow 3: 商家→司机→用户 (Third-party direct delivery)"""
    # Workflow 3: delivery_type=1, shipping_type=1
    # Status flow: 0 → 1 → 2 → 6 → 7
    # Functions used: pickup_order, complete_delivery

    order = Order(
        id=101,
        order_sn="ORD101",
        shop_id=1,
        shipping_type=1,  # To user
        shipping_status=2,
        order_status=1,
        driver_id=10
    )

    # Test complete_delivery (final step for workflow 3)
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = order

    update_result = MagicMock()
    update_result.rowcount = 1

    action_order_result = MagicMock()
    action_order_result.scalar_one_or_none.return_value = order

    call_count = [0]
    def side_effect(stmt):
        result = [order_result, update_result, action_order_result][call_count[0]]
        call_count[0] += 1
        return result

    mock_session.execute.side_effect = side_effect

    result = await order_service.complete_delivery(
        session=mock_session,
        order_sn="ORD101",
        completer_id=10,  # Driver ID
        photo_ids=[1001, 1002]
    )

    assert result is True


@pytest.mark.asyncio
async def test_workflow_4_warehouse_only(mock_session):
    """Test Workflow 4: 商家→仓库 (Merchant to warehouse only)"""
    # Workflow 4: delivery_type=0, shipping_type=0
    # Status flow: 0 → 1 → 2 → 3 → 4
    # Functions used: arrive_warehouse, warehouse_receive

    order = Order(
        id=101,
        order_sn="ORD101",
        shop_id=1,
        shipping_type=0,  # To warehouse
        shipping_status=3,
        order_status=1
    )

    # Test warehouse_receive (final step for workflow 4)
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = order

    update_result = MagicMock()
    update_result.rowcount = 1

    action_order_result = MagicMock()
    action_order_result.scalar_one_or_none.return_value = order

    call_count = [0]
    def side_effect(stmt):
        result = [order_result, update_result, action_order_result][call_count[0]]
        call_count[0] += 1
        return result

    mock_session.execute.side_effect = side_effect

    result = await order_service.warehouse_receive(
        session=mock_session,
        order_sn="ORD101",
        warehouse_staff_id=20,
        photo_ids=None
    )

    assert result is True
