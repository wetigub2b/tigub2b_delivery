"""
PrepareGoods API Routes

Endpoints for merchant preparation workflow:
- Create prepare packages
- Update prepare status
- Query prepare packages
- Assign drivers
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.driver import Driver
from app.models.order import Order
from app.schemas.prepare_goods import (
    AssignDriverRequest,
    CreatePreparePackageRequest,
    PrepareGoodsDetailResponse,
    PrepareGoodsResponse,
    PrepareGoodsSummary,
    UpdatePrepareStatusRequest,
)
from app.services import prepare_goods_service
from app.utils import parse_order_id_list

router = APIRouter()

# Prepare status labels
PREPARE_STATUS_LABELS = {
    None: "待备货",        # Pending Prepare
    0: "已备货",           # Prepared
    1: "司机收货中",        # Driver Pickup
    2: "司机送达仓库",      # Driver to Warehouse
    3: "仓库已收货",        # Warehouse Received
    4: "司机配送用户",      # Driver to User
    5: "已送达",           # Delivered
    6: "完成",             # Complete
}


@router.post("", response_model=PrepareGoodsResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_prepare_package(
    payload: CreatePreparePackageRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> PrepareGoodsResponse:
    """
    Merchant creates prepare goods package for one or more orders.

    This sets delivery_type as the SINGLE SOURCE OF TRUTH for delivery configuration.

    Args:
        payload: Package creation request
        current_user: Authenticated user
        session: Database session

    Returns:
        Created PrepareGoods package

    Raises:
        HTTPException 400: Invalid input (missing warehouse_id when shipping_type=0)
        HTTPException 404: No orders found
    """
    try:
        prepare_goods = await prepare_goods_service.create_prepare_package(
            session=session,
            order_ids=payload.order_ids,
            shop_id=payload.shop_id,
            delivery_type=payload.delivery_type,
            shipping_type=payload.shipping_type,
            warehouse_id=payload.warehouse_id
        )

        return PrepareGoodsResponse(
            id=prepare_goods.id,
            prepare_sn=prepare_goods.prepare_sn,
            order_ids=prepare_goods.order_ids,
            delivery_type=prepare_goods.delivery_type,
            shipping_type=prepare_goods.shipping_type,
            prepare_status=prepare_goods.prepare_status,
            shop_id=prepare_goods.shop_id,
            warehouse_id=prepare_goods.warehouse_id,
            driver_id=prepare_goods.driver_id,
            create_time=prepare_goods.create_time,
            update_time=prepare_goods.update_time
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/available", response_model=List[PrepareGoodsSummary], response_model_by_alias=True)
async def list_available_packages(
    limit: int = Query(default=50, ge=1, le=100),
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> List[PrepareGoodsSummary]:
    """
    Get available packages ready for driver pickup.

    Returns packages that are:
    - prepare_status = 0 (prepared, ready for pickup)
    - driver_id IS NULL (not assigned to any driver yet)
    - delivery_type = 1 (third-party delivery)

    Args:
        limit: Maximum number of records (default 50, max 100)
        current_user: Authenticated user
        session: Database session

    Returns:
        List of available PrepareGoods packages
    """
    packages = await prepare_goods_service.get_available_packages(
        session=session,
        limit=limit
    )

    # Build summary responses
    summaries = []
    for pkg in packages:
        order_ids = parse_order_id_list(pkg.order_ids)
        summaries.append(
            PrepareGoodsSummary(
                prepare_sn=pkg.prepare_sn,
                order_count=len(order_ids),
                delivery_type=pkg.delivery_type,
                shipping_type=pkg.shipping_type,
                prepare_status=pkg.prepare_status,
                prepare_status_label=PREPARE_STATUS_LABELS.get(pkg.prepare_status, "Unknown"),
                warehouse_name=pkg.warehouse.name if pkg.warehouse else None,
                driver_name=None,  # Available packages have no driver assigned
                create_time=pkg.create_time
            )
        )

    return summaries


@router.get("/driver/me", response_model=List[PrepareGoodsSummary], response_model_by_alias=True)
async def list_my_driver_packages(
    limit: int = Query(default=50, ge=1, le=100),
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> List[PrepareGoodsSummary]:
    """
    Get prepare packages assigned to the current logged-in driver.

    Only returns packages with delivery_type=1 (third-party delivery).

    Args:
        limit: Maximum number of records (default 50, max 100)
        current_user: Authenticated user
        session: Database session

    Returns:
        List of PrepareGoods packages assigned to current driver
    """
    # Look up driver by phone number
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    packages = await prepare_goods_service.get_driver_assigned_packages(
        session=session,
        driver_id=driver.id,
        limit=limit
    )

    # Build summary responses
    summaries = []
    for pkg in packages:
        order_ids = parse_order_id_list(pkg.order_ids)
        summaries.append(
            PrepareGoodsSummary(
                prepare_sn=pkg.prepare_sn,
                order_count=len(order_ids),
                delivery_type=pkg.delivery_type,
                shipping_type=pkg.shipping_type,
                prepare_status=pkg.prepare_status,
                prepare_status_label=PREPARE_STATUS_LABELS.get(pkg.prepare_status, "Unknown"),
                warehouse_name=pkg.warehouse.name if pkg.warehouse else None,
                driver_name=pkg.driver.name if pkg.driver else None,
                create_time=pkg.create_time
            )
        )

    return summaries


@router.get("/driver/{driver_id}", response_model=List[PrepareGoodsSummary], response_model_by_alias=True)
async def list_driver_packages(
    driver_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> List[PrepareGoodsSummary]:
    """
    Get prepare packages assigned to a driver.

    Only returns packages with delivery_type=1 (third-party delivery).

    Args:
        driver_id: Driver ID
        limit: Maximum number of records (default 50, max 100)
        current_user: Authenticated user
        session: Database session

    Returns:
        List of PrepareGoods packages assigned to driver
    """
    packages = await prepare_goods_service.get_driver_assigned_packages(
        session=session,
        driver_id=driver_id,
        limit=limit
    )

    # Build summary responses
    summaries = []
    for pkg in packages:
        order_ids = parse_order_id_list(pkg.order_ids)
        summaries.append(
            PrepareGoodsSummary(
                prepare_sn=pkg.prepare_sn,
                order_count=len(order_ids),
                delivery_type=pkg.delivery_type,
                shipping_type=pkg.shipping_type,
                prepare_status=pkg.prepare_status,
                prepare_status_label=PREPARE_STATUS_LABELS.get(pkg.prepare_status, "Unknown"),
                warehouse_name=pkg.warehouse.name if pkg.warehouse else None,
                driver_name=pkg.driver.name if pkg.driver else None,
                create_time=pkg.create_time
            )
        )

    return summaries


@router.get("/shop/{shop_id}", response_model=List[PrepareGoodsSummary], response_model_by_alias=True)
async def list_shop_prepare_packages(
    shop_id: int,
    status: Optional[int] = Query(default=None, ge=0, le=6),
    limit: int = Query(default=50, ge=1, le=100),
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> List[PrepareGoodsSummary]:
    """
    Get prepare packages for a merchant shop.

    Args:
        shop_id: Merchant shop ID
        status: Optional filter by prepare_status (None = all statuses)
        limit: Maximum number of records (default 50, max 100)
        current_user: Authenticated user
        session: Database session

    Returns:
        List of PrepareGoods packages
    """
    packages = await prepare_goods_service.get_shop_prepare_packages(
        session=session,
        shop_id=shop_id,
        status=status,
        limit=limit
    )

    # Build summary responses
    summaries = []
    for pkg in packages:
        order_ids = parse_order_id_list(pkg.order_ids)
        summaries.append(
            PrepareGoodsSummary(
                prepare_sn=pkg.prepare_sn,
                order_count=len(order_ids),
                delivery_type=pkg.delivery_type,
                shipping_type=pkg.shipping_type,
                prepare_status=pkg.prepare_status,
                prepare_status_label=PREPARE_STATUS_LABELS.get(pkg.prepare_status, "Unknown"),
                warehouse_name=pkg.warehouse.name if pkg.warehouse else None,
                driver_name=pkg.driver.name if pkg.driver else None,
                create_time=pkg.create_time
            )
        )

    return summaries


@router.get("/{prepare_sn}", response_model=PrepareGoodsDetailResponse, response_model_by_alias=True)
async def get_prepare_package(
    prepare_sn: str,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> PrepareGoodsDetailResponse:
    """
    Get prepare package by serial number with all items loaded.

    Args:
        prepare_sn: Prepare goods serial number
        current_user: Authenticated user
        session: Database session

    Returns:
        PrepareGoods package with items

    Raises:
        HTTPException 404: Package not found
    """
    prepare_goods = await prepare_goods_service.get_prepare_package(session, prepare_sn)

    if not prepare_goods:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prepare package not found: {prepare_sn}"
        )

    # Build response with items
    from app.schemas.prepare_goods import PrepareGoodsItemSchema

    items = [
        PrepareGoodsItemSchema(
            prepare_id=item.prepare_id,
            order_item_id=item.order_item_id,
            product_id=item.product_id,
            sku_id=item.sku_id,
            quantity=item.quantity
        )
        for item in prepare_goods.items
    ]

    # Fetch order serial numbers
    order_ids = parse_order_id_list(prepare_goods.order_ids)
    order_serial_numbers = []
    if order_ids:
        result = await session.execute(
            select(Order.order_sn).where(Order.id.in_(order_ids))
        )
        order_serial_numbers = [row[0] for row in result.fetchall()]

    return PrepareGoodsDetailResponse(
        id=prepare_goods.id,
        prepare_sn=prepare_goods.prepare_sn,
        order_ids=prepare_goods.order_ids,
        delivery_type=prepare_goods.delivery_type,
        shipping_type=prepare_goods.shipping_type,
        prepare_status=prepare_goods.prepare_status,
        shop_id=prepare_goods.shop_id,
        warehouse_id=prepare_goods.warehouse_id,
        driver_id=prepare_goods.driver_id,
        create_time=prepare_goods.create_time,
        update_time=prepare_goods.update_time,
        items=items,
        warehouse_name=prepare_goods.warehouse.name if prepare_goods.warehouse else None,
        driver_name=prepare_goods.driver.name if prepare_goods.driver else None,
        order_serial_numbers=order_serial_numbers
    )


@router.put("/{prepare_sn}/status", status_code=status.HTTP_204_NO_CONTENT)
async def update_prepare_status(
    prepare_sn: str,
    payload: UpdatePrepareStatusRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> None:
    """
    Update prepare goods status.

    Status Flow:
    - NULL: 待备货 (Pending prepare)
    - 0: 已备货 (Prepared)
    - 1: 司机收货中 (Driver pickup)
    - 2: 司机送达仓库 (Driver to warehouse)
    - 3: 仓库已收货 (Warehouse received)
    - 4: 司机配送用户 (Driver to user)
    - 5: 已送达 (Delivered)
    - 6: 完成 (Complete)

    Args:
        prepare_sn: Prepare goods serial number
        payload: Status update request
        current_user: Authenticated user
        session: Database session

    Raises:
        HTTPException 404: Package not found
    """
    updated = await prepare_goods_service.update_prepare_status(
        session=session,
        prepare_sn=prepare_sn,
        new_status=payload.new_status
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prepare package not found: {prepare_sn}"
        )


@router.post("/{prepare_sn}/assign-driver", status_code=status.HTTP_204_NO_CONTENT)
async def assign_driver(
    prepare_sn: str,
    payload: AssignDriverRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> None:
    """
    Assign a driver to a prepare goods package (for third-party delivery).

    Only applicable when delivery_type=1 (third-party delivery).

    Args:
        prepare_sn: Prepare goods serial number
        payload: Driver assignment request
        current_user: Authenticated user
        session: Database session

    Raises:
        HTTPException 404: Package not found
    """
    assigned = await prepare_goods_service.assign_driver_to_prepare(
        session=session,
        prepare_sn=prepare_sn,
        driver_id=payload.driver_id
    )

    if not assigned:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prepare package not found: {prepare_sn}"
        )


@router.post("/{prepare_sn}/pickup", status_code=status.HTTP_204_NO_CONTENT)
async def pickup_package(
    prepare_sn: str,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> None:
    """
    Driver picks up a package.

    This action:
    1. Assigns the driver to the package
    2. Updates status to 1 (Driver pickup)

    Args:
        prepare_sn: Prepare goods serial number
        current_user: Authenticated driver user
        session: Database session

    Raises:
        HTTPException 404: Driver or package not found
    """
    # Look up driver by phone number
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    # Assign driver to package
    assigned = await prepare_goods_service.assign_driver_to_prepare(
        session=session,
        prepare_sn=prepare_sn,
        driver_id=driver.id
    )

    if not assigned:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prepare package not found: {prepare_sn}"
        )

    # Update status to 1 (Driver pickup)
    await prepare_goods_service.update_prepare_status(
        session=session,
        prepare_sn=prepare_sn,
        new_status=1
    )
