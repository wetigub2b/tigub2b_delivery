from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.driver import Driver
from app.models.order import Order
from app.models.prepare_goods import PrepareGoods
from app.schemas.route import LocationUpdate, RoutePlan
from app.services import order_service, route_service
from app.services.cache import store_driver_location
from app.utils import parse_order_id_list

router = APIRouter()


@router.post("/optimize", response_model=RoutePlan)
async def optimize_route(
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> RoutePlan:
    """
    Build optimized route for driver based on assigned prepare goods packages.

    New workflow:
    1. Get all PrepareGoods packages assigned to driver
    2. Extract order IDs from packages
    3. Filter for active orders (not completed)
    4. Build optimized route
    """
    # Look up driver by phone number to get driver_id
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Get all prepare goods packages assigned to this driver
    # Exclude completed packages (prepare_status = 6)
    packages_result = await session.execute(
        select(PrepareGoods)
        .where(PrepareGoods.driver_id == driver.id)
        .where(PrepareGoods.prepare_status < 6)  # Not completed
    )
    packages = packages_result.scalars().all()

    # Extract all order IDs from packages
    all_order_ids = []
    for pkg in packages:
        order_ids = parse_order_id_list(pkg.order_ids)
        all_order_ids.extend(order_ids)

    # Remove duplicates
    unique_order_ids = list(set(all_order_ids))

    if not unique_order_ids:
        # No orders to route
        return RoutePlan(id="empty", stops=[])

    # Fetch orders with items for route planning
    orders_result = await session.execute(
        select(Order)
        .where(Order.id.in_(unique_order_ids))
        .where(Order.shipping_status < 7)  # Not completed
        .options(selectinload(Order.items))
    )
    orders = orders_result.scalars().all()

    # Build order summaries for route planner
    order_summaries = []
    for order in orders:
        order_summaries.append(await order_service._serialize(session, order))

    return await route_service.build_route_plan(order_summaries)


@router.patch("/{plan_id}/location")
async def update_location(
    plan_id: str,
    payload: LocationUpdate,
    current_user=Depends(deps.get_current_user)
) -> dict:
    await store_driver_location(current_user.user_id, payload.latitude, payload.longitude)
    return {"plan_id": plan_id, "status": "ok"}
