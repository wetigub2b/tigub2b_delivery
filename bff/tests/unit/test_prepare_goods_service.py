"""
Unit tests for PrepareGoodsService

Tests the merchant preparation workflow service including:
- Creating prepare packages
- Updating prepare status
- Querying prepare packages
- Assigning drivers
- Single source of truth for delivery_type
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import prepare_goods_service
from app.models.prepare_goods import PrepareGoods, PrepareGoodsItem
from app.models.order import Order, OrderItem


@pytest.fixture
def mock_session():
    """Create mock async session"""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def sample_orders():
    """Sample orders with items"""
    order1 = Order(
        id=101,
        order_sn="ORD101",
        shop_id=1,
        shipping_type=0,
        shipping_status=0,
        order_status=1
    )
    order1.items = [
        OrderItem(id=1001, product_id=1, sku_id=10, quantity=5),
        OrderItem(id=1002, product_id=2, sku_id=20, quantity=3),
    ]

    order2 = Order(
        id=102,
        order_sn="ORD102",
        shop_id=1,
        shipping_type=0,
        shipping_status=0,
        order_status=1
    )
    order2.items = [
        OrderItem(id=1003, product_id=3, sku_id=30, quantity=2),
    ]

    return [order1, order2]


@pytest.mark.asyncio
async def test_create_prepare_package_success(mock_session, sample_orders):
    """Test creating prepare package successfully"""
    # Mock database query to return orders
    mock_result = MagicMock()
    mock_result.scalars().unique().all.return_value = sample_orders
    mock_session.execute.return_value = mock_result

    # Create package
    result = await prepare_goods_service.create_prepare_package(
        session=mock_session,
        order_ids=[101, 102],
        shop_id=1,
        delivery_type=1,  # Third-party
        shipping_type=0,  # To warehouse
        warehouse_id=5
    )

    # Verify PrepareGoods was created
    assert mock_session.add.called
    added_obj = mock_session.add.call_args[0][0]
    assert isinstance(added_obj, PrepareGoods)
    assert added_obj.order_ids == "101,102"
    assert added_obj.delivery_type == 1  # Single source of truth
    assert added_obj.shipping_type == 0
    assert added_obj.shop_id == 1
    assert added_obj.warehouse_id == 5
    assert added_obj.prepare_sn.startswith("PREP")

    # Verify PrepareGoodsItems were created (3 items total)
    assert mock_session.add.call_count == 4  # 1 PrepareGoods + 3 PrepareGoodsItems

    # Verify commit was called
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_create_prepare_package_missing_warehouse_id(mock_session):
    """Test validation: warehouse_id required when shipping_type=0"""
    with pytest.raises(ValueError, match="warehouse_id required"):
        await prepare_goods_service.create_prepare_package(
            session=mock_session,
            order_ids=[101],
            shop_id=1,
            delivery_type=1,
            shipping_type=0,  # To warehouse
            warehouse_id=None  # Missing!
        )


@pytest.mark.asyncio
async def test_create_prepare_package_empty_order_ids(mock_session):
    """Test validation: order_ids cannot be empty"""
    with pytest.raises(ValueError, match="order_ids cannot be empty"):
        await prepare_goods_service.create_prepare_package(
            session=mock_session,
            order_ids=[],  # Empty!
            shop_id=1,
            delivery_type=1,
            shipping_type=1,
        )


@pytest.mark.asyncio
async def test_create_prepare_package_no_orders_found(mock_session):
    """Test error handling: no orders found for given IDs"""
    # Mock database query to return empty list
    mock_result = MagicMock()
    mock_result.scalars().unique().all.return_value = []
    mock_session.execute.return_value = mock_result

    with pytest.raises(ValueError, match="No orders found"):
        await prepare_goods_service.create_prepare_package(
            session=mock_session,
            order_ids=[999],  # Non-existent order
            shop_id=1,
            delivery_type=1,
            shipping_type=1
        )


@pytest.mark.asyncio
async def test_update_prepare_status_success(mock_session):
    """Test updating prepare status successfully"""
    # Mock update result
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_session.execute.return_value = mock_result

    # Update status
    result = await prepare_goods_service.update_prepare_status(
        session=mock_session,
        prepare_sn="PREP123456",
        new_status=1  # Driver pickup
    )

    # Verify result
    assert result is True
    assert mock_session.execute.called
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_update_prepare_status_not_found(mock_session):
    """Test updating status when package not found"""
    # Mock update result with no rows affected
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_session.execute.return_value = mock_result

    # Update status
    result = await prepare_goods_service.update_prepare_status(
        session=mock_session,
        prepare_sn="PREP999999",
        new_status=1
    )

    # Verify result
    assert result is False


@pytest.mark.asyncio
async def test_get_prepare_package_success(mock_session):
    """Test getting prepare package by serial number"""
    # Mock prepare goods
    mock_pkg = PrepareGoods(
        id=1,
        prepare_sn="PREP123456",
        order_ids="101,102",
        delivery_type=1,
        shipping_type=0,
        shop_id=1,
        warehouse_id=5,
        create_time=datetime.now()
    )
    mock_pkg.items = []
    mock_pkg.warehouse = None
    mock_pkg.driver = None

    # Mock database query
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = mock_pkg
    mock_session.execute.return_value = mock_result

    # Get package
    result = await prepare_goods_service.get_prepare_package(
        session=mock_session,
        prepare_sn="PREP123456"
    )

    # Verify result
    assert result is not None
    assert result.prepare_sn == "PREP123456"
    assert result.delivery_type == 1
    assert result.order_ids == "101,102"


@pytest.mark.asyncio
async def test_get_prepare_package_not_found(mock_session):
    """Test getting package when not found"""
    # Mock database query returning None
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    mock_session.execute.return_value = mock_result

    # Get package
    result = await prepare_goods_service.get_prepare_package(
        session=mock_session,
        prepare_sn="PREP999999"
    )

    # Verify result
    assert result is None


@pytest.mark.asyncio
async def test_get_order_delivery_type_success(mock_session):
    """Test getting delivery_type for order (single source of truth)"""
    # Mock result returning delivery_type
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 1  # Third-party delivery
    mock_session.execute.return_value = mock_result

    # Get delivery type
    result = await prepare_goods_service.get_order_delivery_type(
        session=mock_session,
        order_id=101
    )

    # Verify result
    assert result == 1
    assert mock_session.execute.called


@pytest.mark.asyncio
async def test_get_order_delivery_type_not_prepared(mock_session):
    """Test getting delivery_type when order not yet prepared"""
    # Mock result returning None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Get delivery type
    result = await prepare_goods_service.get_order_delivery_type(
        session=mock_session,
        order_id=999
    )

    # Verify result
    assert result is None


@pytest.mark.asyncio
async def test_assign_driver_to_prepare_success(mock_session):
    """Test assigning driver to prepare package"""
    # Mock update result
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_session.execute.return_value = mock_result

    # Assign driver
    result = await prepare_goods_service.assign_driver_to_prepare(
        session=mock_session,
        prepare_sn="PREP123456",
        driver_id=10
    )

    # Verify result
    assert result is True
    assert mock_session.execute.called
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_get_shop_prepare_packages(mock_session):
    """Test getting prepare packages for a shop"""
    # Mock packages
    mock_pkgs = [
        PrepareGoods(
            id=1,
            prepare_sn="PREP123456",
            order_ids="101,102",
            delivery_type=1,
            shipping_type=0,
            prepare_status=0,
            shop_id=1,
            create_time=datetime.now()
        ),
        PrepareGoods(
            id=2,
            prepare_sn="PREP123457",
            order_ids="103",
            delivery_type=0,
            shipping_type=1,
            prepare_status=1,
            shop_id=1,
            create_time=datetime.now()
        ),
    ]
    for pkg in mock_pkgs:
        pkg.items = []
        pkg.warehouse = None
        pkg.driver = None

    # Mock database query
    mock_result = MagicMock()
    mock_result.scalars().unique().all.return_value = mock_pkgs
    mock_session.execute.return_value = mock_result

    # Get packages
    result = await prepare_goods_service.get_shop_prepare_packages(
        session=mock_session,
        shop_id=1,
        status=None,
        limit=50
    )

    # Verify result
    assert len(result) == 2
    assert result[0].prepare_sn == "PREP123456"
    assert result[1].prepare_sn == "PREP123457"


@pytest.mark.asyncio
async def test_get_driver_assigned_packages(mock_session):
    """Test getting packages assigned to driver"""
    # Mock packages (only delivery_type=1)
    mock_pkgs = [
        PrepareGoods(
            id=1,
            prepare_sn="PREP123456",
            order_ids="101,102",
            delivery_type=1,  # Third-party only
            shipping_type=0,
            driver_id=10,
            shop_id=1,
            create_time=datetime.now()
        ),
    ]
    for pkg in mock_pkgs:
        pkg.items = []
        pkg.warehouse = None

    # Mock database query
    mock_result = MagicMock()
    mock_result.scalars().unique().all.return_value = mock_pkgs
    mock_session.execute.return_value = mock_result

    # Get packages
    result = await prepare_goods_service.get_driver_assigned_packages(
        session=mock_session,
        driver_id=10,
        limit=50
    )

    # Verify result
    assert len(result) == 1
    assert result[0].driver_id == 10
    assert result[0].delivery_type == 1


@pytest.mark.asyncio
async def test_prepare_sn_format(mock_session, sample_orders):
    """Test prepare_sn format is PREP{timestamp_ms}"""
    # Mock database query
    mock_result = MagicMock()
    mock_result.scalars().unique().all.return_value = sample_orders
    mock_session.execute.return_value = mock_result

    # Create package
    with patch('app.services.prepare_goods_service.time_ns', return_value=1699564800000000000):
        result = await prepare_goods_service.create_prepare_package(
            session=mock_session,
            order_ids=[101],
            shop_id=1,
            delivery_type=1,
            shipping_type=1
        )

    # Verify prepare_sn format
    added_obj = mock_session.add.call_args[0][0]
    assert added_obj.prepare_sn.startswith("PREP")
    assert len(added_obj.prepare_sn) > 4  # PREP + timestamp


@pytest.mark.asyncio
async def test_single_source_of_truth_pattern(mock_session, sample_orders):
    """Test that delivery_type is set in PrepareGoods (single source of truth)"""
    # Mock database query
    mock_result = MagicMock()
    mock_result.scalars().unique().all.return_value = sample_orders
    mock_session.execute.return_value = mock_result

    # Create package with delivery_type=1
    await prepare_goods_service.create_prepare_package(
        session=mock_session,
        order_ids=[101, 102],
        shop_id=1,
        delivery_type=1,  # This is the ONLY place delivery_type is set
        shipping_type=0,
        warehouse_id=5
    )

    # Verify delivery_type is stored in PrepareGoods
    added_obj = mock_session.add.call_args[0][0]
    assert added_obj.delivery_type == 1

    # Note: Order model does NOT have delivery_type field
    # This implements single source of truth pattern
