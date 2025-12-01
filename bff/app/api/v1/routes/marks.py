"""
Map markers API endpoints.
Provides location markers for driver map display.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api import deps
from app.schemas.marks import Mark, MarkList

router = APIRouter()


@router.get("", response_model=MarkList)
async def get_marks(
    session: AsyncSession = Depends(deps.get_db_session),
    active_only: bool = True
) -> MarkList:
    """
    Get all map markers.
    
    Args:
        active_only: If True, return only active markers (default: True)
    
    Returns:
        MarkList: List of markers with metadata
    """
    from app.services import marks_service
    
    marks = await marks_service.fetch_marks(session, active_only=active_only)
    return MarkList(
        marks=marks,
        total=len(marks)
    )


@router.get("/{mark_id}", response_model=Mark)
async def get_mark(
    mark_id: int,
    session: AsyncSession = Depends(deps.get_db_session)
) -> Mark:
    """
    Get a specific marker by ID.
    
    Args:
        mark_id: Marker ID
    
    Returns:
        Mark: Marker details
    """
    from app.services import marks_service
    
    mark = await marks_service.fetch_mark_by_id(session, mark_id)
    if not mark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mark with id {mark_id} not found"
        )
    return mark
