from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, File as FileModel
from app.schemas.file import FileCreate, FileUpdate, FileResponse
from app.core.security import get_current_active_user
from app.core.security_metrics import security_metrics
from app.services.file_storage import file_storage_service
from pathlib import Path
import os
import uuid
import shutil
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp',
    'mp3', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm',
    'zip', 'rar', '7z', 'tar', 'gz'
}

def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return filename.split('.')[-1].lower() if '.' in filename else ''

def is_file_allowed(filename: str) -> bool:
    """Check if file extension is allowed."""
    extension = get_file_extension(filename)
    return extension in ALLOWED_EXTENSIONS

def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    return os.path.getsize(file_path)

@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    is_public: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file."""
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    if not is_file_allowed(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check file size (50MB limit)
    max_size = 50 * 1024 * 1024  # 50MB
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset position

    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is 50MB"
        )

    try:
        # Generate unique filename
        file_extension = get_file_extension(file.filename)
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Create upload directory if it doesn't exist
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        # Save file
        file_path = upload_dir / unique_filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create file record in database
        db_file = FileModel(
            filename=file.filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
            description=description,
            is_public=is_public,
            uploaded_by=current_user.id
        )

        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        # Log security event
        security_metrics.record_security_event("file_uploaded", "info", {
            "user_id": current_user.id,
            "file_id": db_file.id,
            "filename": file.filename,
            "file_size": file_size
        })

        return db_file

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

@router.get("/", response_model=List[FileResponse])
async def list_files(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search files by filename or description"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List files with optional filtering and search."""
    query = db.query(FileModel)

    # If not superuser, only show user's files and public files
    if not current_user.is_superuser:
        query = query.filter(
            (FileModel.uploaded_by == current_user.id) | (FileModel.is_public == True)
        )

    if search:
        query = query.filter(
            (FileModel.filename.ilike(f"%{search}%")) |
            (FileModel.description.ilike(f"%{search}%"))
        )

    if content_type:
        query = query.filter(FileModel.content_type == content_type)

    if is_public is not None:
        query = query.filter(FileModel.is_public == is_public)

    files = query.order_by(FileModel.created_at.desc()).offset(skip).limit(limit).all()
    return files

@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get file metadata."""
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    # Check permissions
    if not file.is_public and file.uploaded_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    return file

@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download a file."""
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    # Check permissions
    if not file.is_public and file.uploaded_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if file exists
    if not os.path.exists(file.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Log download event
    security_metrics.record_security_event("file_downloaded", "info", {
        "user_id": current_user.id,
        "file_id": file.id,
        "filename": file.filename
    })

    return FileResponse(
        path=file.file_path,
        filename=file.original_filename,
        media_type=file.content_type
    )

@router.put("/{file_id}", response_model=FileResponse)
async def update_file(
    file_id: int,
    file_update: FileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update file metadata."""
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    # Check permissions
    if file.uploaded_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update fields
    for field, value in file_update.dict(exclude_unset=True).items():
        setattr(file, field, value)

    file.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(file)

    return file

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a file."""
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    # Check permissions
    if file.uploaded_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Delete file from disk
        if os.path.exists(file.file_path):
            os.remove(file.file_path)

        # Delete from database
        db.delete(file)
        db.commit()

        # Log deletion event
        security_metrics.record_security_event("file_deleted", "warning", {
            "user_id": current_user.id,
            "file_id": file.id,
            "filename": file.filename
        })

        return None

    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete file")

@router.post("/{file_id}/share")
async def share_file(
    file_id: int,
    is_public: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Share or unshare a file."""
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    # Check permissions
    if file.uploaded_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    file.is_public = is_public
    file.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(file)

    action = "shared" if is_public else "unshared"
    security_metrics.record_security_event(f"file_{action}", "info", {
        "user_id": current_user.id,
        "file_id": file.id,
        "filename": file.filename
    })

    return {"message": f"File {action} successfully"}

@router.get("/stats/summary")
async def get_file_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get file upload statistics."""
    # Base query
    if current_user.is_superuser:
        query = db.query(FileModel)
    else:
        query = db.query(FileModel).filter(FileModel.uploaded_by == current_user.id)

    total_files = query.count()
    total_size = sum(f.file_size for f in query.all())

    # Files by content type
    content_types = db.query(
        FileModel.content_type,
        db.func.count(FileModel.id).label('count')
    ).group_by(FileModel.content_type).all()

    # Recent uploads (last 7 days)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_uploads = query.filter(FileModel.created_at >= week_ago).count()

    return {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "content_types": [
            {"type": ct.content_type, "count": ct.count}
            for ct in content_types
        ],
        "recent_uploads_7days": recent_uploads
    }
