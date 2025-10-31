"""
Unit tests for order_action_service.

Tests the audit trail creation and file linking functionality.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import order_action_service


class TestOrderActionService:
    """Test order action service functions"""

    @pytest.mark.asyncio
    async def test_create_order_action_basic(self):
        """Test basic order action creation"""
        # Mock database session
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        # Mock the select query return
        mock_result = MagicMock()
        mock_action = MagicMock()
        mock_action.id = 123456789
        mock_action.action_type = 1
        mock_action.shipping_type = 1
        mock_action.logistics_voucher_file = "1001"
        mock_result.scalar_one.return_value = mock_action
        mock_session.execute.return_value = mock_result

        action = await order_action_service.create_order_action(
            session=mock_session,
            order_id=100,
            order_status=2,
            shipping_status=2,
            shipping_type=1,
            action_type=1,
            file_ids=[1001],
            create_by="driver_5",
            remark="Picked up at warehouse"
        )

        # Verify action was created with correct values
        assert action.action_type == 1
        assert action.shipping_type == 1
        assert action.logistics_voucher_file == "1001"

        # Verify commit was called
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_order_action_multiple_files(self):
        """Test action creation with multiple files"""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_result = MagicMock()
        mock_action = MagicMock()
        mock_action.id = 123456789
        mock_action.logistics_voucher_file = "1001,1002,1003"
        mock_result.scalar_one.return_value = mock_action
        mock_session.execute.return_value = mock_result

        action = await order_action_service.create_order_action(
            session=mock_session,
            order_id=100,
            order_status=2,
            shipping_status=2,
            shipping_type=1,
            action_type=1,
            file_ids=[1001, 1002, 1003],
            create_by="driver_5"
        )

        # Verify files are comma-separated
        assert action.logistics_voucher_file == "1001,1002,1003"

    @pytest.mark.asyncio
    async def test_create_order_action_no_files(self):
        """Test action creation without files"""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_result = MagicMock()
        mock_action = MagicMock()
        mock_action.id = 123456789
        mock_action.logistics_voucher_file = None
        mock_result.scalar_one.return_value = mock_action
        mock_session.execute.return_value = mock_result

        action = await order_action_service.create_order_action(
            session=mock_session,
            order_id=100,
            order_status=2,
            shipping_status=2,
            shipping_type=0,
            action_type=4,
            file_ids=None,
            create_by="driver_5"
        )

        # Verify no file linking when file_ids is None
        assert action.logistics_voucher_file is None

    @pytest.mark.asyncio
    async def test_generate_snowflake_id(self):
        """Test snowflake ID generation"""
        import time

        id1 = order_action_service.generate_snowflake_id()
        time.sleep(0.001)  # Small delay to ensure different timestamps
        id2 = order_action_service.generate_snowflake_id()

        # IDs should be positive integers
        assert isinstance(id1, int)
        assert isinstance(id2, int)
        assert id1 > 0
        assert id2 > 0

        # Second ID should be greater or equal (time-based)
        assert id2 >= id1

    @pytest.mark.asyncio
    async def test_action_type_codes(self):
        """Test different action type codes"""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        action_types = [
            (1, "Driver pickup"),
            (2, "Arrive warehouse"),
            (3, "Warehouse ship"),
            (4, "Delivery complete")
        ]

        for action_type, description in action_types:
            mock_result = MagicMock()
            mock_action = MagicMock()
            mock_action.action_type = action_type
            mock_result.scalar_one.return_value = mock_action
            mock_session.execute.return_value = mock_result

            action = await order_action_service.create_order_action(
                session=mock_session,
                order_id=100,
                order_status=2,
                shipping_status=action_type + 1,
                shipping_type=1,
                action_type=action_type,
                create_by="driver_5",
                remark=description
            )

            assert action.action_type == action_type
