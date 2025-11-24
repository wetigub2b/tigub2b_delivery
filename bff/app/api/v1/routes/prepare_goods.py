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
    ConfirmPickupRequest,
    CreatePreparePackageRequest,
    PrepareGoodsDetailResponse,
    PrepareGoodsResponse,
    PrepareGoodsSummary,
    UpdatePrepareStatusRequest,
)
from app.services import prepare_goods_service
from app.utils import parse_order_id_list

router = APIRouter()

# Prepare status labels for different shipping types
# shipping_type=0: To warehouse
# shipping_type=1: Direct to user
PREPARE_STATUS_LABELS_TO_WAREHOUSE = {
    None: "待备货",        # Pending Prepare
    0: "已备货",           # Prepared
    1: "司机收货中",        # Driver Pickup
    2: "司机送达仓库",      # Driver to Warehouse
    3: "仓库已收货",        # Warehouse Received
    4: "司机配送用户",      # Driver to User
    5: "已送达",           # Delivered
    6: "司机已认领",        # Driver Claimed
}

PREPARE_STATUS_LABELS_TO_USER = {
    None: "待备货",        # Pending Prepare
    0: "已备货",           # Prepared
    1: "司机收货中",        # Driver Pickup
    2: "司机配送用户",      # Driver to User
    3: "已送达",           # Delivered
    4: "已送达",           # Delivered
    5: "已送达",           # Delivered
    6: "司机已认领",        # Driver Claimed
}

def get_prepare_status_label(status: Optional[int], shipping_type: int) -> str:
    """Get status label based on shipping type."""
    if shipping_type == 0:
        return PREPARE_STATUS_LABELS_TO_WAREHOUSE.get(status, "Unknown")
    else:
        return PREPARE_STATUS_LABELS_TO_USER.get(status, "Unknown")


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
                prepare_status_label=get_prepare_status_label(pkg.prepare_status, pkg.shipping_type),
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
                prepare_status_label=get_prepare_status_label(pkg.prepare_status, pkg.shipping_type),
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
                prepare_status_label=get_prepare_status_label(pkg.prepare_status, pkg.shipping_type),
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
                prepare_status_label=get_prepare_status_label(pkg.prepare_status, pkg.shipping_type),
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
    from app.schemas.prepare_goods import PrepareGoodsItemSchema, UploadedFileSchema
    from app.models.order import UploadedFile

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

    # Fetch pickup photos
    photos_result = await session.execute(
        select(UploadedFile)
        .where(UploadedFile.biz_type == "prepare_good")
        .where(UploadedFile.biz_id == prepare_goods.id)
        .order_by(UploadedFile.create_time.desc())
    )
    pickup_photos = [
        UploadedFileSchema(
            id=photo.id,
            file_name=photo.file_name,
            file_url=photo.file_url,
            file_type=photo.file_type,
            file_size=photo.file_size,
            uploader_name=photo.uploader_name,
            create_time=photo.create_time
        )
        for photo in photos_result.scalars().all()
    ]

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
        order_serial_numbers=order_serial_numbers,
        pickup_photos=pickup_photos
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
    - 1: 司机收货中 (Driver pickup with proof)
    - 2: 司机送达仓库 (Driver to warehouse)
    - 3: 仓库已收货 (Warehouse received)
    - 4: 司机配送用户 (Driver to user)
    - 5: 已送达 (Delivered)
    - 6: 司机已认领 (Driver claimed, pending pickup)

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
    2. Updates status to 6 (Driver claimed)

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

    # Update status to 6 (Driver claimed)
    await prepare_goods_service.update_prepare_status(
        session=session,
        prepare_sn=prepare_sn,
        new_status=6
    )


@router.post("/{prepare_sn}/confirm-pickup", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_pickup(
    prepare_sn: str,
    payload: ConfirmPickupRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> None:
    """
    Confirm driver picked up package with photo proof.

    This action:
    1. Saves photo to tigu_uploaded_files (biz_type='prepare_good', biz_id=package.id)
    2. Creates OrderAction records for each order (action_type=1 - Driver Pickup)
    3. Updates package status to 1 (Driver pickup in progress)

    Args:
        prepare_sn: Prepare goods serial number
        payload: Confirmation request with photo and notes
        current_user: Authenticated driver user
        session: Database session

    Raises:
        HTTPException 404: Driver or package not found
        HTTPException 400: Invalid photo or package status
    """
    import base64
    import os
    from datetime import datetime
    from pathlib import Path
    from app.models.order import UploadedFile
    from app.models.order_action import OrderAction
    from app.models.prepare_goods import PrepareGoods
    from app.utils import generate_snowflake_id

    # Look up driver
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    # Get package
    result = await session.execute(
        select(PrepareGoods).where(PrepareGoods.prepare_sn == prepare_sn)
    )
    package = result.scalars().first()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Package not found: {prepare_sn}"
        )

    # Verify package is in correct status (should be 6 - Driver claimed)
    if package.prepare_status != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Package status must be 6 (Driver claimed), current: {package.prepare_status}"
        )

    # Decode and save photo
    try:
        if payload.photo.startswith('data:'):
            header, encoded = payload.photo.split(',', 1)
            mime_type = header.split(':')[1].split(';')[0]
        else:
            encoded = payload.photo
            mime_type = 'image/jpeg'

        image_bytes = base64.b64decode(encoded)

        # Validate file size (4MB limit)
        if len(image_bytes) > 4 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Photo size exceeds 4MB limit"
            )

        # Create upload directory
        upload_dir = Path("/var/www/deliveries/photos/pickups")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = int(datetime.now().timestamp())
        extension = mime_type.split('/')[-1]
        if extension == 'jpg':
            extension = 'jpeg'
        filename = f"{prepare_sn}_{timestamp}.{extension}"
        file_path = upload_dir / filename

        # Save file
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        os.chmod(file_path, 0o644)

        photo_url = f"/deliveries/photos/pickups/{filename}"

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save photo: {str(e)}"
        )

    # Create UploadedFile record
    uploaded_file = UploadedFile(
        id=generate_snowflake_id(),
        file_name=filename,
        file_url=photo_url,
        file_type=mime_type,
        file_size=len(image_bytes),
        biz_type="prepare_good",
        biz_id=package.id,
        uploader_id=driver.id,
        uploader_name=driver.name,
        create_by=driver.name,
        create_time=datetime.now()
    )
    session.add(uploaded_file)

    # Parse order IDs from package
    order_ids = parse_order_id_list(package.order_ids)

    # Get orders to fetch their current status
    orders_result = await session.execute(
        select(Order).where(Order.id.in_(order_ids))
    )
    orders = orders_result.scalars().all()

    # Create OrderAction record for each order AND update tigu_order
    for order in orders:
        order_action = OrderAction(
            id=generate_snowflake_id(),
            order_id=order.id,
            action_type=1,  # 司机收货 - Driver Pickup
            logistics_voucher_file=str(uploaded_file.id),  # Use file ID, not URL
            create_by=driver.name,
            create_time=datetime.now(),
            order_status=order.order_status,
            shipping_status=order.shipping_status,
            shipping_type=order.shipping_type
        )
        session.add(order_action)
        
        # Update tigu_order: set shipping_status=2 (司机收货中), driver_receive_time, and driver_id
        order.shipping_status = 2
        order.driver_receive_time = datetime.now()
        order.driver_id = driver.id

    # Update package status to 1 (Driver pickup in progress)
    await prepare_goods_service.update_prepare_status(
        session=session,
        prepare_sn=prepare_sn,
        new_status=1
    )

    await session.commit()


@router.post("/{prepare_sn}/confirm-delivery", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_delivery(
    prepare_sn: str,
    payload: ConfirmPickupRequest,
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> None:
    """
    Confirm driver delivered package with photo proof.

    This action:
    1. Saves photo to tigu_uploaded_files (biz_type='prepare_good', biz_id=package.id)
    2. Creates OrderAction records for each order
       - For warehouse delivery (shipping_type=0): action_type=2 - 司机送达仓库
       - For user delivery (shipping_type=1): action_type=5 - 完成
       - logistics_voucher_file contains the file ID from tigu_uploaded_files
    3. Updates package status based on shipping type:
       - shipping_type=0 (Workflow 3): prepare_status to 2 (司机送达仓库 - Driver delivered to warehouse)
       - shipping_type=1 (Workflow 4): prepare_status to 3 (已送达 - Delivered to user, complete)

    Args:
        prepare_sn: Prepare goods serial number
        payload: Confirmation request with photo and notes
        current_user: Authenticated driver user
        session: Database session

    Raises:
        HTTPException 404: Driver or package not found
        HTTPException 400: Invalid photo or package status
    """
    import base64
    import os
    from datetime import datetime
    from pathlib import Path
    from app.models.order import UploadedFile
    from app.models.order_action import OrderAction
    from app.models.prepare_goods import PrepareGoods
    from app.utils import generate_snowflake_id

    # Look up driver
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )

    # Get package
    result = await session.execute(
        select(PrepareGoods).where(PrepareGoods.prepare_sn == prepare_sn)
    )
    package = result.scalars().first()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Package not found: {prepare_sn}"
        )

    # Verify package is in transit status (should be 1, 2, 4, or 5)
    if package.prepare_status not in [1, 2, 4, 5]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Package status must be in transit (1, 2, 4, or 5), current: {package.prepare_status}"
        )

    # Decode and save photo
    try:
        if payload.photo.startswith('data:'):
            header, encoded = payload.photo.split(',', 1)
            mime_type = header.split(':')[1].split(';')[0]
        else:
            encoded = payload.photo
            mime_type = 'image/jpeg'

        image_bytes = base64.b64decode(encoded)

        # Validate file size (4MB limit)
        if len(image_bytes) > 4 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Photo size exceeds 4MB limit"
            )

        # Create upload directory
        upload_dir = Path("/var/www/deliveries/photos/deliveries")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = int(datetime.now().timestamp())
        extension = mime_type.split('/')[-1]
        if extension == 'jpg':
            extension = 'jpeg'
        filename = f"{prepare_sn}_{timestamp}.{extension}"
        file_path = upload_dir / filename

        # Save file
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        os.chmod(file_path, 0o644)

        photo_url = f"/deliveries/photos/deliveries/{filename}"

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save photo: {str(e)}"
        )

    # Create UploadedFile record
    uploaded_file = UploadedFile(
        id=generate_snowflake_id(),
        file_name=filename,
        file_url=photo_url,
        file_type=mime_type,
        file_size=len(image_bytes),
        biz_type="prepare_good",
        biz_id=package.id,
        uploader_id=driver.id,
        uploader_name=driver.name,
        create_by=driver.name,
        create_time=datetime.now()
    )
    session.add(uploaded_file)

    # Parse order IDs from package
    order_ids = parse_order_id_list(package.order_ids)

    # Get orders to fetch their current status
    orders_result = await session.execute(
        select(Order).where(Order.id.in_(order_ids))
    )
    orders = orders_result.scalars().all()

    # Determine action type and new status based on shipping type
    if package.shipping_type == 0:
        # To warehouse workflow (Workflow 3)
        action_type = 2  # 司机送达仓库 - Driver arrives at warehouse (action_type=2)
        new_status = 2  # 司机送达仓库 (Driver delivered to warehouse)
        order_shipping_status = 3  # Update tigu_order.shipping_status to 3
    else:
        # To user workflow (Workflow 4)
        action_type = 5  # 完成 - Delivery complete (action_type=5)
        new_status = 3  # 已送达 - Delivered to user (Workflow 4 complete)
        order_shipping_status = 6  # Update tigu_order.shipping_status to 6 (已送达)

    # Create OrderAction record for each order AND update tigu_order
    # Note: logistics_voucher_file should contain file ID from tigu_uploaded_files
    for order in orders:
        order_action = OrderAction(
            id=generate_snowflake_id(),
            order_id=order.id,
            action_type=action_type,
            logistics_voucher_file=str(uploaded_file.id),  # Use file ID, not URL
            create_by=driver.name,
            create_time=datetime.now(),
            order_status=order.order_status,
            shipping_status=order.shipping_status,
            shipping_type=order.shipping_type
        )
        session.add(order_action)
        
        # Update tigu_order based on shipping type
        order.shipping_status = order_shipping_status
        if package.shipping_type == 0:
            # Driver arrived at warehouse
            order.arrive_warehouse_time = datetime.now()
        else:
            # Delivery completed to user
            order.finish_time = datetime.now()
            order.order_status = 3  # Mark order as completed

    # Update package status
    await prepare_goods_service.update_prepare_status(
        session=session,
        prepare_sn=prepare_sn,
        new_status=new_status
    )

    await session.commit()
