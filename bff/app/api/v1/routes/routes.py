from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.driver import Driver
from app.models.prepare_goods import PrepareGoods
from app.schemas.route import LocationUpdate, RoutePlan, RouteStop
from app.services.cache import store_driver_location

router = APIRouter()


@router.post("/optimize", response_model=RoutePlan)
async def optimize_route(
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> RoutePlan:
    """
    Build optimized route for driver based on assigned prepare goods packages.

    Uses receiver addresses from tigu_prepare_goods table for in-transit packages.
    
    Workflow:
    1. Get all in-transit PrepareGoods packages assigned to driver
    2. Use receiver address from prepare_goods table
    3. Build optimized route
    """
    # Look up driver by phone number to get driver_id
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Get all prepare goods packages assigned to this driver
    # Only show in-transit packages (prepare_status 2-5)
    packages_result = await session.execute(
        select(PrepareGoods)
        .where(PrepareGoods.driver_id == driver.id)
        .where(PrepareGoods.prepare_status >= 2)  # In-transit
        .where(PrepareGoods.prepare_status < 6)  # Not completed
    )
    packages = packages_result.scalars().all()

    if not packages:
        # No packages to route
        return RoutePlan(id="empty", stops=[])

    # Build route stops from prepare goods packages
    stops = []
    for idx, pkg in enumerate(packages, start=1):
        # Use receiver address from prepare_goods table
        if pkg.receiver_address:
            stops.append(
                RouteStop(
                    order_sn=pkg.prepare_sn,  # Use prepare_sn as identifier
                    sequence=idx,
                    address=pkg.receiver_address,
                    receiver_name=pkg.receiver_name or "Unknown",
                    eta=None,  # ETA provided by Google Maps
                    latitude=None,
                    longitude=None
                )
            )

    # Generate unique plan ID based on package sequence
    import hashlib
    plan_id = hashlib.md5("".join(stop.order_sn for stop in stops).encode()).hexdigest()
    return RoutePlan(id=plan_id, stops=stops)


@router.patch("/{plan_id}/location")
async def update_location(
    plan_id: str,
    payload: LocationUpdate,
    current_user=Depends(deps.get_current_user)
) -> dict:
    await store_driver_location(current_user.user_id, payload.latitude, payload.longitude)
    return {"plan_id": plan_id, "status": "ok"}
