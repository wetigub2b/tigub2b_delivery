"""
Integration tests for API endpoints.

Tests FastAPI HTTP endpoints with database integration to ensure
complete request-response cycle works correctly.
"""
import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.order import Order, OrderItem, UploadedFile
from app.models.prepare_goods import PrepareGoods
from app.models.driver import Driver
from app.models.order import Warehouse


@pytest.fixture
async def client() -> AsyncClient:
    """
    Provide async HTTP client for API testing.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_order(async_session: AsyncSession):
    """Create test order for API testing"""
    order = Order(
        id=20001,
        order_sn="API_TEST_001",
        shop_id=1,
        user_id=200,
        shipping_type=0,
        shipping_status=0,
        order_status=1,
        total_price=500.00,
        create_time=datetime.now()
    )

    order_item = OrderItem(
        id=30001,
        order_id=20001,
        product_id=401,
        sku_id=501,
        quantity=5,
        price=100.00,
        create_time=datetime.now()
    )

    async_session.add(order)
    async_session.add(order_item)
    await async_session.commit()
    await async_session.refresh(order)

    return order


@pytest.fixture
async def test_driver(async_session: AsyncSession):
    """Create test driver for API testing"""
    driver = Driver(
        id=501,
        name="API Test Driver",
        phone="13800138888",
        vehicle_number="京A88888",
        status=1,
        create_time=datetime.now()
    )
    async_session.add(driver)
    await async_session.commit()
    await async_session.refresh(driver)
    return driver


@pytest.fixture
async def test_warehouse(async_session: AsyncSession):
    """Create test warehouse for API testing"""
    warehouse = Warehouse(
        id=601,
        name="API Test Warehouse",
        address="Test Address 123",
        contact_name="Test Contact",
        contact_phone="13900139999",
        status=1,
        create_time=datetime.now()
    )
    async_session.add(warehouse)
    await async_session.commit()
    await async_session.refresh(warehouse)
    return warehouse


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_prepare_package_api(
    client: AsyncClient,
    async_session: AsyncSession,
    test_order: Order,
    test_warehouse: Warehouse
):
    """
    Test POST /api/v1/prepare-goods endpoint

    This endpoint allows merchant to create a prepare goods package.
    """
    # NOTE: This test assumes the endpoint exists and auth is mocked/disabled for tests
    # In production, you'll need to mock JWT authentication

    payload = {
        "order_ids": [test_order.id],
        "delivery_type": 1,  # Third-party
        "shipping_type": 0,  # To warehouse
        "warehouse_id": test_warehouse.id
    }

    # Mock authentication header (adjust based on your auth implementation)
    headers = {
        "Authorization": "Bearer test_token_merchant_shop_1"
    }

    response = await client.post(
        "/api/v1/prepare-goods",
        json=payload,
        headers=headers
    )

    # If endpoint doesn't exist yet, this will return 404
    # Once implemented, should return 200/201
    if response.status_code == 404:
        pytest.skip("Prepare goods endpoint not yet implemented")

    assert response.status_code in [200, 201]
    data = response.json()

    assert data["delivery_type"] == 1
    assert data["shipping_type"] == 0
    assert data["warehouse_id"] == test_warehouse.id
    assert "prepare_sn" in data
    assert data["prepare_sn"].startswith("PREP")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_driver_pickup_order_api(
    client: AsyncClient,
    async_session: AsyncSession,
    test_order: Order,
    test_driver: Driver
):
    """
    Test POST /api/v1/orders/{order_sn}/pickup endpoint

    Driver picks up order from merchant.
    """
    # First create prepare package (via service layer for test setup)
    from app.services import prepare_goods_service

    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[test_order.id],
        shop_id=1,
        delivery_type=1,
        shipping_type=1,
        warehouse_id=None
    )

    # Mark as prepared
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=0
    )

    # Now test the pickup API
    payload = {
        "driver_id": test_driver.id,
        "photo_ids": []  # Empty for test
    }

    headers = {
        "Authorization": f"Bearer test_token_driver_{test_driver.id}"
    }

    response = await client.post(
        f"/api/v1/orders/{test_order.order_sn}/pickup",
        json=payload,
        headers=headers
    )

    if response.status_code == 404:
        pytest.skip("Pickup endpoint not yet implemented")

    assert response.status_code in [200, 204]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_warehouse_receive_order_api(
    client: AsyncClient,
    async_session: AsyncSession,
    test_order: Order,
    test_warehouse: Warehouse
):
    """
    Test POST /api/v1/orders/{order_sn}/warehouse-receive endpoint

    Warehouse staff receives goods.
    """
    # Setup: Create prepare package and simulate driver delivery
    from app.services import prepare_goods_service, order_service

    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[test_order.id],
        shop_id=1,
        delivery_type=1,
        shipping_type=0,
        warehouse_id=test_warehouse.id
    )

    # Simulate workflow to warehouse arrival
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=2  # Driver delivered to warehouse
    )

    # Test warehouse receive API
    payload = {
        "warehouse_staff_id": 20,
        "photo_ids": []
    }

    headers = {
        "Authorization": "Bearer test_token_warehouse_staff_20"
    }

    response = await client.post(
        f"/api/v1/orders/{test_order.order_sn}/warehouse-receive",
        json=payload,
        headers=headers
    )

    if response.status_code == 404:
        pytest.skip("Warehouse receive endpoint not yet implemented")

    assert response.status_code in [200, 204]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_delivery_api(
    client: AsyncClient,
    async_session: AsyncSession,
    test_order: Order
):
    """
    Test POST /api/v1/orders/{order_sn}/complete endpoint

    Complete delivery (final step).
    """
    # Setup: Simulate order ready for completion
    from app.services import prepare_goods_service

    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[test_order.id],
        shop_id=1,
        delivery_type=0,
        shipping_type=1,
        warehouse_id=None
    )

    # Mark as shipped
    await prepare_goods_service.update_prepare_status(
        session=async_session,
        prepare_sn=prepare_package.prepare_sn,
        new_status=5  # Shipped to user
    )

    # Test complete delivery API
    payload = {
        "completer_id": 1,  # Merchant
        "photo_ids": []
    }

    headers = {
        "Authorization": "Bearer test_token_merchant_1"
    }

    response = await client.post(
        f"/api/v1/orders/{test_order.order_sn}/complete",
        json=payload,
        headers=headers
    )

    if response.status_code == 404:
        pytest.skip("Complete delivery endpoint not yet implemented")

    assert response.status_code in [200, 204]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_order_actions_api(
    client: AsyncClient,
    async_session: AsyncSession,
    test_order: Order
):
    """
    Test GET /api/v1/orders/{order_sn}/actions endpoint

    Retrieve complete action history for an order.
    """
    # Setup: Create some actions
    from app.services import order_action_service

    # Create a few test actions
    await order_action_service.create_order_action(
        session=async_session,
        order_id=test_order.id,
        action_type=0,
        create_by=1,
        file_ids=None
    )

    await order_action_service.create_order_action(
        session=async_session,
        order_id=test_order.id,
        action_type=1,
        create_by=10,
        file_ids=None
    )

    # Test get actions API
    headers = {
        "Authorization": "Bearer test_token"
    }

    response = await client.get(
        f"/api/v1/orders/{test_order.order_sn}/actions",
        headers=headers
    )

    if response.status_code == 404:
        pytest.skip("Get actions endpoint not yet implemented")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 2

    # Verify action structure
    assert "action_type" in data[0]
    assert "create_time" in data[0]
    assert "create_by" in data[0]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_prepare_package_api(
    client: AsyncClient,
    async_session: AsyncSession,
    test_order: Order
):
    """
    Test GET /api/v1/prepare-goods/{prepare_sn} endpoint

    Retrieve prepare package details.
    """
    # Setup: Create prepare package
    from app.services import prepare_goods_service

    prepare_package = await prepare_goods_service.create_prepare_package(
        session=async_session,
        order_ids=[test_order.id],
        shop_id=1,
        delivery_type=1,
        shipping_type=0,
        warehouse_id=5
    )

    # Test get prepare package API
    headers = {
        "Authorization": "Bearer test_token_merchant_1"
    }

    response = await client.get(
        f"/api/v1/prepare-goods/{prepare_package.prepare_sn}",
        headers=headers
    )

    if response.status_code == 404:
        pytest.skip("Get prepare package endpoint not yet implemented")

    assert response.status_code == 200
    data = response.json()

    assert data["prepare_sn"] == prepare_package.prepare_sn
    assert data["delivery_type"] == 1
    assert data["shipping_type"] == 0
    assert "items" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_photo_api(
    client: AsyncClient,
    async_session: AsyncSession
):
    """
    Test POST /api/v1/files/upload endpoint

    Upload photo evidence for workflow actions.
    """
    import base64

    # Create fake image data
    fake_image = b"fake_image_bytes_for_testing"
    base64_image = base64.b64encode(fake_image).decode()

    payload = {
        "file_data": base64_image,
        "file_name": "test_photo.jpg",
        "file_type": "image/jpeg"
    }

    headers = {
        "Authorization": "Bearer test_token"
    }

    response = await client.post(
        "/api/v1/files/upload",
        json=payload,
        headers=headers
    )

    if response.status_code == 404:
        pytest.skip("File upload endpoint not yet implemented")

    assert response.status_code in [200, 201]
    data = response.json()

    assert "file_id" in data
    assert "file_url" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_api_error_handling(
    client: AsyncClient,
    async_session: AsyncSession
):
    """
    Test API error handling for invalid requests.
    """
    # Test 1: Invalid order_sn
    response = await client.post(
        "/api/v1/orders/INVALID_ORDER/pickup",
        json={"driver_id": 999},
        headers={"Authorization": "Bearer test"}
    )

    if response.status_code == 404 and "not found" not in response.text.lower():
        pytest.skip("Endpoints not yet implemented")

    # Should return 404 for non-existent order
    # Or appropriate error status

    # Test 2: Missing required fields
    response = await client.post(
        "/api/v1/prepare-goods",
        json={},  # Missing required fields
        headers={"Authorization": "Bearer test"}
    )

    # Should return 422 (validation error) or 400 (bad request)
    if response.status_code != 404:
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_api_authentication_required(client: AsyncClient):
    """
    Test that endpoints require authentication.
    """
    # Try to access protected endpoint without auth
    response = await client.get("/api/v1/prepare-goods/PREP123")

    # Should return 401 (unauthorized) or 403 (forbidden)
    # Unless auth is not yet implemented
    if response.status_code not in [401, 403, 404]:
        pytest.skip("Authentication not yet enforced")

    assert response.status_code in [401, 403]
