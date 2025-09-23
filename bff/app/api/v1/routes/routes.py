from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.route import LocationUpdate, RoutePlan
from app.services import order_service, route_service
from app.services.cache import store_driver_location

router = APIRouter()


@router.post("/optimize", response_model=RoutePlan)
async def optimize_route(
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> RoutePlan:
    orders = await order_service.fetch_assigned_orders(session, current_user.user_id)
    return await route_service.build_route_plan(orders)


@router.patch("/{plan_id}/location")
async def update_location(
    plan_id: str,
    payload: LocationUpdate,
    current_user=Depends(deps.get_current_user)
) -> dict:
    await store_driver_location(current_user.user_id, payload.latitude, payload.longitude)
    return {"plan_id": plan_id, "status": "ok"}
