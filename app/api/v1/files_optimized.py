from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from app.models import User
from app.core.security import get_current_active_user
from app.services.file_storage import file_storage_service
from app.core.logging import logger
from app.middleware.rate_limiter import rate_limit
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

router = APIRouter()

# Response Models for better API documentation
class FileInfoResponse(BaseModel):
    id: str
    original_filename: str
    stored_filename: str
    file_size: int
    content_type: str
    description: Optional[str] = None
    uploaded_at: datetime
    downloads: int

class FileUploadResponse(BaseModel):
    message: str
    file_id: str
    filename: str
    file_size: int
    uploaded_at: datetime

class FileListResponse(BaseModel):
    files: List[FileInfoResponse]
    total: int
    page: int
    limit: int

class StorageStatsResponse(BaseModel):
    total_files: int
    total_size_bytes: int
    total_size_mb: float
    total_downloads: int
    by_file_type: dict

class DownloadResponse(BaseModel):
    file_path: str
    filename: str
    content_type: str
    downloads: int

# Request validation models
class FileUpdateRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)

# Error handler decorator
def handle_api_errors(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except ValueError as e:
            logger.warning(f"Validation error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except PermissionError as e:
            logger.warning(f"Permission error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )
    return wrapper

# Validation helpers
def validate_file_id(file_id: str) -> str:
    """Validate file ID format."""
    if not file_id or not file_id.strip():
        raise ValueError("File ID is required")
    return file_id.strip()

def validate_file_size(file: UploadFile) -> UploadFile:
    """Validate file size (max 100MB)."""
    max_size = 100 * 1024 * 1024  # 100MB
    if file.size and file.size > max_size:
        raise ValueError(f"File size exceeds maximum limit of 100MB")
    return file

@router.post("/upload", response_model=FileUploadResponse)
@rate_limit(calls=10, period=60)  # 10 uploads per minute
@handle_api_errors
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Field(None, max_length=500),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file with validation and rate limiting."""
    logger.info(f"User {current_user.id} uploading file: {file.filename}")

    # Validate file
    file = validate_file_size(file)

    if not file.filename:
        raise ValueError("Filename is required")

    # Validate file type
    allowed_types = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'text/plain', 'application/json',
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }

    if file.content_type not in allowed_types:
        raise ValueError(f"File type {file.content_type} not allowed")

    file_record = await file_storage_service.upload_file(
        file=file,
        user_id=current_user.id,
        description=description
    )

    logger.info(f"File uploaded successfully: {file_record['id']}")

    return FileUploadResponse(
        message="File uploaded successfully",
        file_id=file_record["id"],
        filename=file_record["original_filename"],
        file_size=file_record["file_size"],
        uploaded_at=file_record["uploaded_at"]
    )

@router.get("/", response_model=FileListResponse)
@rate_limit(calls=100, period=60)  # 100 requests per minute
@handle_api_errors
@cache(expire=60)  # Cache for 1 minute
async def list_files(
    skip: int = Query(0, ge=0, description="Number of files to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of files to return"),
    current_user: User = Depends(get_current_active_user)
):
    """List user files with pagination and caching."""
    logger.info(f"User {current_user.id} listing files: skip={skip}, limit={limit}")

    files = await file_storage_service.get_user_files(
        user_id=current_user.id,
        limit=limit,
        offset=skip
    )

    # Get total count for pagination
    total_files = await file_storage_service.get_user_files_count(user_id=current_user.id)

    return FileListResponse(
        files=files,
        total=total_files,
        page=skip // limit + 1,
        limit=limit
    )

@router.get("/{file_id}", response_model=FileInfoResponse)
@rate_limit(calls=200, period=60)
@handle_api_errors
@cache(expire=300)  # Cache for 5 minutes
async def get_file_info(
    file_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get file information with caching."""
    file_id = validate_file_id(file_id)
    logger.info(f"User {current_user.id} requesting file info: {file_id}")

    file_info = await file_storage_service.get_file_info(
        file_id=file_id,
        user_id=current_user.id
    )

    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileInfoResponse(**file_info)

@router.get("/{file_id}/download", response_model=DownloadResponse)
@rate_limit(calls=50, period=60)
@handle_api_errors
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Download a file with rate limiting."""
    file_id = validate_file_id(file_id)
    logger.info(f"User {current_user.id} downloading file: {file_id}")

    download_info = await file_storage_service.download_file(
        file_id=file_id,
        user_id=current_user.id
    )

    if not download_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    logger.info(f"File downloaded successfully: {file_id}")
    return DownloadResponse(**download_info)

@router.delete("/{file_id}")
@rate_limit(calls=30, period=60)
@handle_api_errors
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a file with validation."""
    file_id = validate_file_id(file_id)
    logger.info(f"User {current_user.id} deleting file: {file_id}")

    success = await file_storage_service.delete_file(
        file_id=file_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Clear cache for this user's files
    await FastAPICache.clear(namespace=f"user_files_{current_user.id}")

    logger.info(f"File deleted successfully: {file_id}")
    return {"message": "File deleted successfully"}

@router.put("/{file_id}")
@rate_limit(calls=30, period=60)
@handle_api_errors
async def update_file_description(
    file_id: str,
    request: FileUpdateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Update file description with validation."""
    file_id = validate_file_id(file_id)
    logger.info(f"User {current_user.id} updating file description: {file_id}")

    success = await file_storage_service.update_file_description(
        file_id=file_id,
        user_id=current_user.id,
        description=request.description
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Clear cache for this file
    await FastAPICache.clear(namespace=f"file_{file_id}")

    logger.info(f"File description updated successfully: {file_id}")
    return {"message": "File description updated successfully"}

@router.get("/stats/storage", response_model=StorageStatsResponse)
@rate_limit(calls=30, period=60)
@handle_api_errors
@cache(expire=300)  # Cache for 5 minutes
async def get_storage_stats(current_user: User = Depends(get_current_active_user)):
    """Get storage statistics with caching."""
    logger.info(f"User {current_user.id} requesting storage stats")

    stats = await file_storage_service.get_storage_stats(user_id=current_user.id)

    return StorageStatsResponse(
        total_files=stats["total_files"],
        total_size_bytes=stats["total_size_bytes"],
        total_size_mb=stats["total_size_mb"],
        total_downloads=stats["total_downloads"],
        by_file_type=stats["by_file_type"]
    )
