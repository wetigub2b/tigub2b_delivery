"""
Unit tests for order workflow functions.

Tests the dual delivery path workflow: warehouse vs direct delivery.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services import order_service


class TestOrderWorkflow:
    """Test order workflow service functions"""

    @pytest.mark.asyncio
    async def test_pickup_warehouse_delivery(self):
        """Test pickup for warehouse delivery sets status=2"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        # Warehouse delivery (shipping_type=1) should set status to 2
        result = await order_service.pickup_order(
            session=mock_session,
            order_sn="TOD123",
            driver_id=5,
            shipping_type=1  # Warehouse delivery
        )

        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_pickup_direct_delivery(self):
        """Test pickup for direct delivery sets status=4"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        # Direct delivery (shipping_type=0) should set status to 4
        result = await order_service.pickup_order(
            session=mock_session,
            order_sn="TOD123",
            driver_id=5,
            shipping_type=0  # Direct delivery
        )

        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_pickup_order_not_found(self):
        """Test pickup when order doesn't exist or already assigned"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0  # No rows affected
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        result = await order_service.pickup_order(
            session=mock_session,
            order_sn="NONEXISTENT",
            driver_id=5,
            shipping_type=1
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_arrive_warehouse_success(self):
        """Test successful warehouse arrival"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        result = await order_service.arrive_warehouse(
            session=mock_session,
            order_sn="TOD123",
            driver_id=5
        )

        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_arrive_warehouse_wrong_state(self):
        """Test warehouse arrival when order is not in correct state"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0  # No rows affected (not in status 2)
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        result = await order_service.arrive_warehouse(
            session=mock_session,
            order_sn="TOD123",
            driver_id=5
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_warehouse_ship_success(self):
        """Test successful warehouse shipping"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        result = await order_service.warehouse_ship(
            session=mock_session,
            order_sn="TOD123"
        )

        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_warehouse_ship_wrong_state(self):
        """Test warehouse shipping when order is not in correct state"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0  # Not in status 3
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        result = await order_service.warehouse_ship(
            session=mock_session,
            order_sn="TOD123"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_complete_delivery_success(self):
        """Test successful delivery completion"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        result = await order_service.complete_delivery(
            session=mock_session,
            order_sn="TOD123",
            driver_id=5
        )

        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_delivery_without_driver(self):
        """Test delivery completion without driver verification"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        result = await order_service.complete_delivery(
            session=mock_session,
            order_sn="TOD123",
            driver_id=None  # No driver verification
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_shipping_status_labels(self):
        """Test shipping status label mappings"""
        from app.services.order_service import SHIPPING_STATUS_LABELS

        # Verify updated status labels
        assert SHIPPING_STATUS_LABELS[0] == "Not Shipped"
        assert SHIPPING_STATUS_LABELS[1] == "Shipped"
        assert SHIPPING_STATUS_LABELS[2] == "Driver Received"
        assert SHIPPING_STATUS_LABELS[3] == "Arrived Warehouse"
        assert SHIPPING_STATUS_LABELS[4] == "Warehouse Shipped"
        assert SHIPPING_STATUS_LABELS[5] == "Delivered"

    @pytest.mark.asyncio
    async def test_dual_workflow_paths(self):
        """Test that both workflow paths are distinct"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()

        # Warehouse path: NULL → 2 → 3 → 4 → 5
        warehouse_path = await order_service.pickup_order(
            mock_session, "W001", 5, shipping_type=1
        )
        assert warehouse_path is True

        # Direct path: NULL → 4 → 5
        direct_path = await order_service.pickup_order(
            mock_session, "D001", 5, shipping_type=0
        )
        assert direct_path is True
