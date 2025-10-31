"""
File upload service for handling photo uploads to tigu_uploaded_files table.
"""
import base64
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import UploadedFile

# Configuration
UPLOAD_DIR = Path("/var/www/deliveries/photos")
MAX_FILE_SIZE = 4 * 1024 * 1024  # 4MB in bytes
ALLOWED_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png"}

logger = logging.getLogger(__name__)


def ensure_upload_directory():
    """Create upload directory if it doesn't exist"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(UPLOAD_DIR, 0o755)
    except PermissionError:
        logger.warning("Unable to change permissions for %s; continuing anyway", UPLOAD_DIR)


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


def save_photo(image_bytes: bytes, identifier: str, mime_type: str) -> str:
    """
    Save photo to local filesystem.

    Args:
        image_bytes: Image binary data
        identifier: Unique identifier for filename (e.g., order_sn, action_id)
        mime_type: MIME type of the image

    Returns:
        str: Relative URL path to the photo
    """
    ensure_upload_directory()

    # Generate unique filename
    timestamp = int(datetime.now().timestamp())
    extension = mime_type.split('/')[-1]
    if extension == 'jpg':
        extension = 'jpeg'
    filename = f"{identifier}_{timestamp}.{extension}"

    # Save file
    file_path = UPLOAD_DIR / filename
    with open(file_path, 'wb') as f:
        f.write(image_bytes)

    # Set file permissions
    try:
        os.chmod(file_path, 0o644)
    except PermissionError:
        logger.warning("Unable to change permissions for %s", file_path)

    # Return relative URL (served by nginx)
    return f"/deliveries/photos/{filename}"


async def upload_base64_image(
    session: AsyncSession,
    image_data: str,
    biz_type: str,
    biz_id: Optional[int] = None
) -> int:
    """
    Upload base64 image and save to tigu_uploaded_files table.

    Args:
        session: Database session
        image_data: Base64 encoded image or data URL
        biz_type: Business type (e.g., 'order_action', 'delivery_proof')
        biz_id: Business ID (can be None initially, updated later)

    Returns:
        int: ID of the uploaded file record

    Raises:
        HTTPException: If validation fails
    """
    # Decode and validate photo
    image_bytes, mime_type = decode_base64_image(image_data)

    # Save photo to filesystem
    identifier = f"{biz_type}_{biz_id or int(datetime.now().timestamp())}"
    file_url = save_photo(image_bytes, identifier, mime_type)

    # Prepare file record
    file_record = {
        "file_name": file_url.split('/')[-1],
        "file_url": file_url,
        "file_size": len(image_bytes),
        "file_type": mime_type,
        "biz_type": biz_type,
        "biz_id": biz_id,
        "is_main": 0,
        "create_time": datetime.now(),
        "create_by": "system"
    }

    # Insert into database
    stmt = insert(UploadedFile).values(**file_record)
    result = await session.execute(stmt)
    await session.flush()  # Flush to get the ID without committing

    # Return the inserted file ID
    file_id = result.lastrowid
    return file_id
