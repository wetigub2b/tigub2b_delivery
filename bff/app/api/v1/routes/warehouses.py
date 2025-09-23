from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.order import WarehouseSnapshot
from app.services.warehouse_service import fetch_active_warehouses

router = APIRouter()


@router.get("/active", response_model=list[WarehouseSnapshot])
async def list_active_warehouses(
    current_user=Depends(deps.get_current_user),
    session: AsyncSession = Depends(deps.get_db_session)
) -> list[WarehouseSnapshot]:
    return await fetch_active_warehouses(session)
