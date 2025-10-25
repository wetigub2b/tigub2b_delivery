from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.driver import Driver
from app.schemas.route import LocationUpdate, RoutePlan
from app.services import order_service, route_service
from app.services.cache import store_driver_location

router = APIRouter()


@router.post("/optimize", response_model=RoutePlan)
async def optimize_route(
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> RoutePlan:
    # Look up driver by phone number to get driver_id
    result = await session.execute(select(Driver).where(Driver.phone == current_user.phonenumber))
    driver = result.scalars().first()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Only get active orders (not completed) for route planning
    orders = await order_service.fetch_assigned_orders(session, driver.id, include_completed=False)
    return await route_service.build_route_plan(orders)


@router.patch("/{plan_id}/location")
async def update_location(
    plan_id: str,
    payload: LocationUpdate,
    current_user=Depends(deps.get_current_user)
) -> dict:
    await store_driver_location(current_user.user_id, payload.latitude, payload.longitude)
    return {"plan_id": plan_id, "status": "ok"}
