from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Warehouse
from app.schemas.order import WarehouseSnapshot


async def fetch_active_warehouses(session: AsyncSession) -> List[WarehouseSnapshot]:
    stmt = select(Warehouse)
    result = await session.execute(stmt)
    warehouses = result.scalars().all()
    snapshots: List[WarehouseSnapshot] = []
    for warehouse in warehouses:
        snapshots.append(
            WarehouseSnapshot(
                id=warehouse.id,
                name=warehouse.name,
                address=f"{warehouse.line1}, {warehouse.city}, {warehouse.province} {warehouse.postal_code}",
                latitude=float(warehouse.latitude) if warehouse.latitude is not None else None,
                longitude=float(warehouse.longitude) if warehouse.longitude is not None else None
            )
        )
    return snapshots
