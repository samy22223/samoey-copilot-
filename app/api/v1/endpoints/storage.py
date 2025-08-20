from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.core.auth import get_current_user
from app.models import User
from app.services.storage_optimizer import StorageOptimizer
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/optimize", response_model=Dict[str, Any])
async def optimize_storage(
    current_user: User = Depends(get_current_user)
):
    """
    Run full storage optimization.
    Only accessible by authenticated users.
    """
    try:
        optimizer = StorageOptimizer()
        results = optimizer.run_full_optimization()

        logger.info(f"Storage optimization completed by user {current_user.id}")
        return {
            "success": True,
            "message": "Storage optimization completed successfully",
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in storage optimization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize storage"
        )

@router.post("/optimize/cache", response_model=Dict[str, Any])
async def optimize_cache(
    current_user: User = Depends(get_current_user)
):
    """
    Clean up Python cache files.
    Only accessible by authenticated users.
    """
    try:
        optimizer = StorageOptimizer()
        results = optimizer.cleanup_python_cache()

        return {
            "success": True,
            "message": "Python cache cleanup completed",
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in cache optimization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean up cache"
        )

@router.post("/optimize/logs", response_model=Dict[str, Any])
async def optimize_logs(
    days: int = 7,
    current_user: User = Depends(get_current_user)
):
    """
    Clean up old log files.
    Only accessible by authenticated users.
    """
    try:
        optimizer = StorageOptimizer()
        results = optimizer.cleanup_log_files(days=days)

        return {
            "success": True,
            "message": f"Log files cleanup completed (older than {days} days)",
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in log optimization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean up logs"
        )

@router.post("/optimize/uploads", response_model=Dict[str, Any])
async def optimize_uploads(
    current_user: User = Depends(get_current_user)
):
    """
    Optimize file uploads storage.
    Only accessible by authenticated users.
    """
    try:
        optimizer = StorageOptimizer()
        results = optimizer.optimize_uploads_storage()

        return {
            "success": True,
            "message": "Uploads storage optimization completed",
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in uploads optimization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize uploads storage"
        )

@router.post("/optimize/database", response_model=Dict[str, Any])
async def optimize_database(
    current_user: User = Depends(get_current_user)
):
    """
    Optimize database storage by cleaning old records.
    Only accessible by authenticated users.
    """
    try:
        optimizer = StorageOptimizer()
        results = optimizer.optimize_database_storage()

        return {
            "success": True,
            "message": "Database storage optimization completed",
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in database optimization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize database storage"
        )

@router.get("/stats", response_model=Dict[str, Any])
async def get_storage_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get current storage statistics.
    Only accessible by authenticated users.
    """
    try:
        from app.services.file_storage import FileStorageService

        file_storage = FileStorageService()
        upload_stats = file_storage.get_storage_stats()

        return {
            "success": True,
            "storage_stats": upload_stats
        }

    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get storage statistics"
        )
