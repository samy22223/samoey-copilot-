from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import List, Optional
from app.models import User
from app.core.security import get_current_active_user
from app.services.file_storage import file_storage_service

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file."""
    try:
        file_record = await file_storage_service.upload_file(
            file=file,
            user_id=current_user.id,
            description=description
        )
        return {
            "message": "File uploaded successfully",
            "file_id": file_record["id"],
            "filename": file_record["original_filename"],
            "file_size": file_record["file_size"],
            "uploaded_at": file_record["uploaded_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("/")
async def list_files(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """List user files."""
    try:
        files = await file_storage_service.get_user_files(
            user_id=current_user.id,
            limit=limit,
            offset=skip
        )
        return {"files": files}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve files: {str(e)}"
        )

@router.get("/{file_id}")
async def get_file_info(
    file_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get file information."""
    try:
        file_info = await file_storage_service.get_file_info(
            file_id=file_id,
            user_id=current_user.id
        )
        if not file_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        return file_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve file info: {str(e)}"
        )

@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Download a file."""
    try:
        download_info = await file_storage_service.download_file(
            file_id=file_id,
            user_id=current_user.id
        )
        if not download_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        return download_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a file."""
    try:
        success = await file_storage_service.delete_file(
            file_id=file_id,
            user_id=current_user.id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        return {"message": "File deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

@router.put("/{file_id}")
async def update_file_description(
    file_id: int,
    description: str,
    current_user: User = Depends(get_current_active_user)
):
    """Update file description."""
    try:
        success = await file_storage_service.update_file_description(
            file_id=file_id,
            user_id=current_user.id,
            description=description
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        return {"message": "File description updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update file description: {str(e)}"
        )

@router.get("/stats/storage")
async def get_storage_stats(current_user: User = Depends(get_current_active_user)):
    """Get storage statistics for current user."""
    try:
        stats = await file_storage_service.get_storage_stats(user_id=current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve storage stats: {str(e)}"
        )
