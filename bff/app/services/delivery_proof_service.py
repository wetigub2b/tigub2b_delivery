import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery_proof import DeliveryProof
from app.models.order import Order

# Configuration
UPLOAD_DIR = Path("/var/www/deliveries/photos")
MAX_FILE_SIZE = 4 * 1024 * 1024  # 4MB in bytes
ALLOWED_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png"}


def ensure_upload_directory():
    """Create upload directory if it doesn't exist"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # Set permissions
    os.chmod(UPLOAD_DIR, 0o755)


def decode_base64_image(data_url: str) -> tuple[bytes, str]:
    """
    Decode base64 image from data URL.

    Returns:
        tuple: (image_bytes, mime_type)

    Raises:
        HTTPException: If format is invalid or size exceeds limit
    """
    try:
        # Handle data URL format: data:image/jpeg;base64,/9j/4AAQ...
        if data_url.startswith('data:'):
            header, encoded = data_url.split(',', 1)
            mime_type = header.split(':')[1].split(';')[0]
        else:
            # Assume raw base64
            encoded = data_url
            mime_type = 'image/jpeg'  # Default

        # Validate MIME type
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image type. Allowed: {', '.join(ALLOWED_MIME_TYPES)}"
            )

        # Decode base64
        image_bytes = base64.b64decode(encoded)

        # Validate file size
        if len(image_bytes) > MAX_FILE_SIZE:
            size_mb = len(image_bytes) / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Photo size ({size_mb:.1f}MB) exceeds 4MB limit"
            )

        return image_bytes, mime_type

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format"
        )


def save_photo(image_bytes: bytes, order_sn: str, mime_type: str) -> str:
    """
    Save photo to local filesystem.

    Returns:
        str: Relative URL path to the photo
    """
    ensure_upload_directory()

    # Generate unique filename
    timestamp = int(datetime.now().timestamp())
    extension = mime_type.split('/')[-1]
    if extension == 'jpg':
        extension = 'jpeg'
    filename = f"{order_sn}_{timestamp}.{extension}"

    # Save file
    file_path = UPLOAD_DIR / filename
    with open(file_path, 'wb') as f:
        f.write(image_bytes)

    # Set file permissions
    os.chmod(file_path, 0o644)

    # Return relative URL (served by nginx)
    return f"/deliveries/photos/{filename}"


async def upload_delivery_proof(
    session: AsyncSession,
    order_sn: str,
    driver_id: int,
    photo_data: str,
    notes: Optional[str] = None
) -> DeliveryProof:
    """
    Upload delivery proof photo and create database record.

    Args:
        session: Database session
        order_sn: Order serial number
        driver_id: Driver ID
        photo_data: Base64 encoded photo or data URL
        notes: Optional delivery notes

    Returns:
        DeliveryProof: Created delivery proof record

    Raises:
        HTTPException: If order not found or validation fails
    """
    # Verify order exists and belongs to driver
    stmt = select(Order).where(Order.order_sn == order_sn)
    result = await session.execute(stmt)
    order = result.scalars().first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Order not assigned to this driver"
        )

    # Decode and validate photo
    image_bytes, mime_type = decode_base64_image(photo_data)

    # Save photo to filesystem
    photo_url = save_photo(image_bytes, order_sn, mime_type)

    # Create database record
    delivery_proof = DeliveryProof(
        order_id=order.id,
        order_sn=order_sn,
        driver_id=driver_id,
        photo_url=photo_url,
        notes=notes,
        file_size=len(image_bytes),
        mime_type=mime_type,
        created_at=datetime.now()
    )

    session.add(delivery_proof)
    await session.commit()
    await session.refresh(delivery_proof)

    return delivery_proof
