"""
Service layer for map markers.
Handles business logic for marker retrieval and management.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.schemas.marks import Mark


async def fetch_marks(session: AsyncSession, active_only: bool = True) -> List[Mark]:
    """
    Fetch all markers from database with order counts.
    
    Args:
        session: Database session
        active_only: If True, return only active markers
    
    Returns:
        List of Mark objects with order_count for each location
        
    Order count logic:
        - For shop/vendor marks: Count packages with prepare_status=0 (ready for merchant pickup)
        - For warehouse marks: Count packages with type=1, prepare_status=0, shipping_type=0 (ready for warehouse pickup)
    """
    query = """
        SELECT
            m.id,
            m.name,
            m.latitude,
            m.longitude,
            m.type,
            m.description,
            m.shop_id,
            m.warehouse_id,
            m.is_active,
            m.created_at,
            m.updated_at,
            COALESCE(COUNT(pg.id), 0) as order_count
        FROM tigu_driver_marks m
        LEFT JOIN tigu_prepare_goods pg ON (
            -- Shop/vendor marks: packages ready for merchant pickup (prepare_status=0)
            (m.shop_id IS NOT NULL AND pg.shop_id = m.shop_id AND pg.type = 0
             AND pg.prepare_status = 0 AND pg.driver_id IS NULL AND pg.delivery_type = 1)
            OR
            -- Warehouse marks: packages ready for warehouse pickup (type=1, prepare_status=0, shipping_type=0)
            (m.warehouse_id IS NOT NULL AND pg.warehouse_id = m.warehouse_id
             AND pg.type = 1 AND pg.prepare_status = 0 AND pg.shipping_type = 0
             AND pg.driver_id IS NULL AND pg.delivery_type = 1)
        )
    """
    
    if active_only:
        query += " WHERE m.is_active = 1"
    
    query += " GROUP BY m.id ORDER BY m.name ASC"
    
    result = await session.execute(text(query))
    rows = result.fetchall()
    
    marks = []
    for row in rows:
        marks.append(Mark(
            id=row.id,
            name=row.name,
            latitude=float(row.latitude),
            longitude=float(row.longitude),
            type=row.type,
            description=row.description,
            # Convert bigint IDs to strings to preserve precision in JavaScript
            shop_id=str(row.shop_id) if row.shop_id else None,
            warehouse_id=str(row.warehouse_id) if row.warehouse_id else None,
            order_count=row.order_count,
            is_active=bool(row.is_active),
            created_at=row.created_at,
            updated_at=row.updated_at
        ))
    
    return marks


async def fetch_mark_by_id(session: AsyncSession, mark_id: int) -> Optional[Mark]:
    """
    Fetch a specific marker by ID with order count.
    
    Args:
        session: Database session
        mark_id: Marker ID
    
    Returns:
        Mark object or None if not found
        
    Order count logic:
        - For shop/vendor marks: Count packages with prepare_status=0 (ready for merchant pickup)
        - For warehouse marks: Count packages with type=1, prepare_status=0, shipping_type=0 (ready for warehouse pickup)
    """
    query = """
        SELECT
            m.id,
            m.name,
            m.latitude,
            m.longitude,
            m.type,
            m.description,
            m.shop_id,
            m.warehouse_id,
            m.is_active,
            m.created_at,
            m.updated_at,
            COALESCE(COUNT(pg.id), 0) as order_count
        FROM tigu_driver_marks m
        LEFT JOIN tigu_prepare_goods pg ON (
            -- Shop/vendor marks: packages ready for merchant pickup (prepare_status=0)
            (m.shop_id IS NOT NULL AND pg.shop_id = m.shop_id AND pg.type = 0
             AND pg.prepare_status = 0 AND pg.driver_id IS NULL AND pg.delivery_type = 1)
            OR
            -- Warehouse marks: packages ready for warehouse pickup (type=1, prepare_status=0, shipping_type=0)
            (m.warehouse_id IS NOT NULL AND pg.warehouse_id = m.warehouse_id
             AND pg.type = 1 AND pg.prepare_status = 0 AND pg.shipping_type = 0
             AND pg.driver_id IS NULL AND pg.delivery_type = 1)
        )
        WHERE m.id = :mark_id
        GROUP BY m.id
    """
    
    result = await session.execute(text(query), {"mark_id": mark_id})
    row = result.fetchone()
    
    if not row:
        return None
    
    return Mark(
        id=row.id,
        name=row.name,
        latitude=float(row.latitude),
        longitude=float(row.longitude),
        type=row.type,
        description=row.description,
        # Convert bigint IDs to strings to preserve precision in JavaScript
        shop_id=str(row.shop_id) if row.shop_id else None,
        warehouse_id=str(row.warehouse_id) if row.warehouse_id else None,
        order_count=row.order_count,
        is_active=bool(row.is_active),
        created_at=row.created_at,
        updated_at=row.updated_at
    )
