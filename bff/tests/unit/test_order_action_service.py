"""
Unit tests for OrderActionService

Tests the order workflow audit trail service including:
- Creating action records
- Linking files to actions
- Querying action history
- Workflow timeline generation
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import order_action_service
from app.services.order_action_service import ActionType
from app.models.order import Order, UploadedFile
from app.models.order_action import OrderAction


@pytest.fixture
def mock_session():
    """Create mock async session"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
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
        order_status=1
    )


@pytest.mark.asyncio
async def test_create_order_action_success(mock_session, sample_order):
    """Test creating order action record successfully"""
    # Mock order query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_order
    mock_session.execute.return_value = mock_result

    # Create action
    result = await order_action_service.create_order_action(
        session=mock_session,
        order_id=101,
        action_type=ActionType.DRIVER_PICKUP,
        create_by=10,  # driver_id
        file_ids=[1001, 1002],
        remark="Picked up from merchant"
    )

    # Verify OrderAction was created
    assert mock_session.add.called
    added_obj = mock_session.add.call_args[0][0]
    assert isinstance(added_obj, OrderAction)
    assert added_obj.order_id == 101
    assert added_obj.action_type == ActionType.DRIVER_PICKUP
    assert added_obj.create_by == 10
    assert added_obj.logistics_voucher_file == "1001,1002"
    assert added_obj.remark == "Picked up from merchant"

    # Verify state snapshot
    assert added_obj.order_status == 1
    assert added_obj.shipping_status == 1
    assert added_obj.shipping_type == 0

    # Verify Snowflake ID generated
    assert added_obj.id > 0

    # Verify commit called
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_create_order_action_order_not_found(mock_session):
    """Test error handling when order not found"""
    # Mock order query returning None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Create action should raise ValueError
    with pytest.raises(ValueError, match="Order not found"):
        await order_action_service.create_order_action(
            session=mock_session,
            order_id=999,
            action_type=ActionType.DRIVER_PICKUP,
            create_by=10
        )


@pytest.mark.asyncio
async def test_create_order_action_without_files(mock_session, sample_order):
    """Test creating action without photo evidence"""
    # Mock order query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_order
    mock_session.execute.return_value = mock_result

    # Create action without files
    result = await order_action_service.create_order_action(
        session=mock_session,
        order_id=101,
        action_type=ActionType.WAREHOUSE_RECEIVE,
        create_by=20,  # warehouse_staff_id
        file_ids=None  # No files
    )

    # Verify OrderAction was created without files
    added_obj = mock_session.add.call_args[0][0]
    assert added_obj.logistics_voucher_file is None


@pytest.mark.asyncio
async def test_link_files_to_action_success(mock_session):
    """Test linking files to action"""
    # Mock update result
    mock_result = MagicMock()
    mock_result.rowcount = 2
    mock_session.execute.return_value = mock_result

    # Link files
    result = await order_action_service.link_files_to_action(
        session=mock_session,
        action_id=5001,
        file_ids=[1001, 1002]
    )

    # Verify result
    assert result == 2
    assert mock_session.execute.called
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_link_files_to_action_empty_list(mock_session):
    """Test linking empty file list"""
    # Link empty files
    result = await order_action_service.link_files_to_action(
        session=mock_session,
        action_id=5001,
        file_ids=[]
    )

    # Verify no database operations
    assert result == 0
    assert not mock_session.execute.called


@pytest.mark.asyncio
async def test_get_order_actions_success(mock_session):
    """Test getting all actions for an order"""
    # Mock actions
    mock_actions = [
        OrderAction(
            id=5001,
            order_id=101,
            action_type=ActionType.GOODS_PREPARED,
            create_by=1,
            create_time=datetime(2025, 11, 9, 10, 0, 0)
        ),
        OrderAction(
            id=5002,
            order_id=101,
            action_type=ActionType.DRIVER_PICKUP,
            create_by=10,
            create_time=datetime(2025, 11, 9, 11, 0, 0)
        ),
    ]

    # Mock database query
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = mock_actions
    mock_session.execute.return_value = mock_result

    # Get actions
    result = await order_action_service.get_order_actions(
        session=mock_session,
        order_id=101
    )

    # Verify result
    assert len(result) == 2
    assert result[0].action_type == ActionType.GOODS_PREPARED
    assert result[1].action_type == ActionType.DRIVER_PICKUP


@pytest.mark.asyncio
async def test_get_order_actions_with_filter(mock_session):
    """Test getting actions filtered by action_type"""
    # Mock actions (only DRIVER_PICKUP)
    mock_actions = [
        OrderAction(
            id=5002,
            order_id=101,
            action_type=ActionType.DRIVER_PICKUP,
            create_by=10,
            create_time=datetime(2025, 11, 9, 11, 0, 0)
        ),
    ]

    # Mock database query
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = mock_actions
    mock_session.execute.return_value = mock_result

    # Get actions with filter
    result = await order_action_service.get_order_actions(
        session=mock_session,
        order_id=101,
        action_type=ActionType.DRIVER_PICKUP
    )

    # Verify result
    assert len(result) == 1
    assert result[0].action_type == ActionType.DRIVER_PICKUP


@pytest.mark.asyncio
async def test_get_latest_action_success(mock_session):
    """Test getting latest action for an order"""
    # Mock latest action
    mock_action = OrderAction(
        id=5002,
        order_id=101,
        action_type=ActionType.DRIVER_PICKUP,
        create_by=10,
        create_time=datetime(2025, 11, 9, 11, 0, 0)
    )

    # Mock database query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_action
    mock_session.execute.return_value = mock_result

    # Get latest action
    result = await order_action_service.get_latest_action(
        session=mock_session,
        order_id=101
    )

    # Verify result
    assert result is not None
    assert result.action_type == ActionType.DRIVER_PICKUP


@pytest.mark.asyncio
async def test_get_latest_action_not_found(mock_session):
    """Test getting latest action when no actions exist"""
    # Mock database query returning None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Get latest action
    result = await order_action_service.get_latest_action(
        session=mock_session,
        order_id=101
    )

    # Verify result
    assert result is None


@pytest.mark.asyncio
async def test_get_action_files_success(mock_session):
    """Test getting files linked to an action"""
    # Mock files
    mock_files = [
        UploadedFile(id=1001, file_url="/uploads/photo1.jpg", biz_type="order_action", biz_id=5001),
        UploadedFile(id=1002, file_url="/uploads/photo2.jpg", biz_type="order_action", biz_id=5001),
    ]

    # Mock database query
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = mock_files
    mock_session.execute.return_value = mock_result

    # Get files
    result = await order_action_service.get_action_files(
        session=mock_session,
        action_id=5001
    )

    # Verify result
    assert len(result) == 2
    assert result[0].file_url == "/uploads/photo1.jpg"
    assert result[1].file_url == "/uploads/photo2.jpg"


@pytest.mark.asyncio
async def test_get_workflow_timeline_success(mock_session):
    """Test getting complete workflow timeline"""
    # Mock actions
    mock_actions = [
        OrderAction(
            id=5001,
            order_id=101,
            action_type=ActionType.GOODS_PREPARED,
            order_status=1,
            shipping_status=1,
            create_by=1,
            remark="Goods prepared",
            create_time=datetime(2025, 11, 9, 10, 0, 0)
        ),
        OrderAction(
            id=5002,
            order_id=101,
            action_type=ActionType.DRIVER_PICKUP,
            order_status=1,
            shipping_status=2,
            create_by=10,
            remark="Driver picked up",
            create_time=datetime(2025, 11, 9, 11, 0, 0)
        ),
    ]

    # Mock files
    mock_files1 = [
        UploadedFile(id=1001, file_url="/uploads/photo1.jpg"),
    ]
    mock_files2 = [
        UploadedFile(id=1002, file_url="/uploads/photo2.jpg"),
        UploadedFile(id=1003, file_url="/uploads/photo3.jpg"),
    ]

    # Mock database queries
    call_count = [0]
    def mock_execute_side_effect(stmt):
        result = MagicMock()
        if call_count[0] == 0:
            # First call: get_order_actions
            result.scalars().all.return_value = mock_actions
        elif call_count[0] == 1:
            # Second call: get_action_files for first action
            result.scalars().all.return_value = mock_files1
        else:
            # Third call: get_action_files for second action
            result.scalars().all.return_value = mock_files2
        call_count[0] += 1
        return result

    mock_session.execute.side_effect = mock_execute_side_effect

    # Get timeline
    result = await order_action_service.get_workflow_timeline(
        session=mock_session,
        order_id=101
    )

    # Verify result
    assert len(result) == 2
    assert result[0]["action_type"] == ActionType.GOODS_PREPARED
    assert len(result[0]["files"]) == 1
    assert result[1]["action_type"] == ActionType.DRIVER_PICKUP
    assert len(result[1]["files"]) == 2


@pytest.mark.asyncio
async def test_record_driver_pickup_helper(mock_session, sample_order):
    """Test record_driver_pickup helper function"""
    # Mock order query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_order
    mock_session.execute.return_value = mock_result

    # Record driver pickup
    result = await order_action_service.record_driver_pickup(
        session=mock_session,
        order_id=101,
        driver_id=10,
        photo_ids=[1001, 1002]
    )

    # Verify action created with correct type
    added_obj = mock_session.add.call_args[0][0]
    assert added_obj.action_type == ActionType.DRIVER_PICKUP
    assert added_obj.create_by == 10
    assert added_obj.logistics_voucher_file == "1001,1002"


@pytest.mark.asyncio
async def test_record_warehouse_receive_helper(mock_session, sample_order):
    """Test record_warehouse_receive helper function"""
    # Mock order query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_order
    mock_session.execute.return_value = mock_result

    # Record warehouse receive (without photos)
    result = await order_action_service.record_warehouse_receive(
        session=mock_session,
        order_id=101,
        warehouse_staff_id=20,
        photo_ids=None
    )

    # Verify action created with correct type
    added_obj = mock_session.add.call_args[0][0]
    assert added_obj.action_type == ActionType.WAREHOUSE_RECEIVE
    assert added_obj.create_by == 20
    assert added_obj.logistics_voucher_file is None


@pytest.mark.asyncio
async def test_action_type_constants():
    """Test ActionType constants are correct"""
    assert ActionType.GOODS_PREPARED == 0
    assert ActionType.DRIVER_PICKUP == 1
    assert ActionType.DRIVER_TO_WAREHOUSE == 2
    assert ActionType.WAREHOUSE_RECEIVE == 3
    assert ActionType.WAREHOUSE_SHIP == 4
    assert ActionType.DELIVERY_COMPLETE == 5
    assert ActionType.REFUND_REQUEST == 6
    assert ActionType.ORDER_CANCELLED == 11


@pytest.mark.asyncio
async def test_file_linking_pattern(mock_session, sample_order):
    """Test complete file linking pattern"""
    # Mock order query
    order_result = MagicMock()
    order_result.scalar_one_or_none.return_value = sample_order

    # Mock file update result
    file_result = MagicMock()
    file_result.rowcount = 2

    # Set up side effects
    call_count = [0]
    def side_effect(stmt):
        if call_count[0] == 0:
            call_count[0] += 1
            return order_result
        else:
            return file_result

    mock_session.execute.side_effect = side_effect

    # Create action with files
    await order_action_service.create_order_action(
        session=mock_session,
        order_id=101,
        action_type=ActionType.DRIVER_PICKUP,
        create_by=10,
        file_ids=[1001, 1002]
    )

    # Verify file linking was called
    # Should have 2 execute calls: 1 for order query, 1 for file update
    assert mock_session.execute.call_count >= 2
