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
    Fetch all markers from database.
    
    Args:
        session: Database session
        active_only: If True, return only active markers
    
    Returns:
        List of Mark objects
    """
    query = """
        SELECT 
            id,
            name,
            latitude,
            longitude,
            type,
            description,
            is_active,
            created_at,
            updated_at
        FROM tigu_driver_marks
    """
    
    if active_only:
        query += " WHERE is_active = 1"
    
    query += " ORDER BY name ASC"
    
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
            is_active=bool(row.is_active),
            created_at=row.created_at,
            updated_at=row.updated_at
        ))
    
    return marks


async def fetch_mark_by_id(session: AsyncSession, mark_id: int) -> Optional[Mark]:
    """
    Fetch a specific marker by ID.
    
    Args:
        session: Database session
        mark_id: Marker ID
    
    Returns:
        Mark object or None if not found
    """
    query = """
        SELECT 
            id,
            name,
            latitude,
            longitude,
            type,
            description,
            is_active,
            created_at,
            updated_at
        FROM tigu_driver_marks
        WHERE id = :mark_id
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
        is_active=bool(row.is_active),
        created_at=row.created_at,
        updated_at=row.updated_at
    )
