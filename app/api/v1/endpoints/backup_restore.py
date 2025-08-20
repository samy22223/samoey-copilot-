from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, BackupJob, BackupLog
from app.schemas.backup import (
    BackupCreate,
    BackupResponse,
    BackupLogResponse,
    RestoreRequest
)
from app.core.security import get_current_active_user
from app.core.security_metrics import security_metrics
from app.services.backup import backup_service
from datetime import datetime, timedelta
import logging
import os
import shutil

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/backup", response_model=BackupResponse)
async def create_backup(
    backup: BackupCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new backup job."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Create backup job
        db_backup = BackupJob(
            name=backup.name,
            backup_type=backup.backup_type,
            include_tables=backup.include_tables or [],
            exclude_tables=backup.exclude_tables or [],
            include_files=backup.include_files or [],
            exclude_files=backup.exclude_files or [],
            compression=backup.compression,
            encryption=backup.encryption,
            destination=backup.destination,
            retention_days=backup.retention_days,
            scheduled_time=backup.scheduled_time,
            status="pending",
            created_by=current_user.id
        )

        db.add(db_backup)
        db.commit()
        db.refresh(db_backup)

        # Start backup process in background
        background_tasks.add_task(
            backup_service.execute_backup,
            db_backup.id
        )

        # Log security event
        security_metrics.record_security_event("backup_created", "info", {
            "user_id": current_user.id,
            "backup_id": db_backup.id,
            "backup_name": backup.name,
            "backup_type": backup.backup_type
        })

        return db_backup

    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create backup")

@router.get("/backups", response_model=List[BackupResponse])
async def list_backups(
    skip: int = 0,
    limit: int = 100,
    backup_type: Optional[str] = Query(None, description="Filter by backup type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List backup jobs."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = db.query(BackupJob).filter(
        BackupJob.created_at >= start_date,
        BackupJob.created_at <= end_date
    )

    if backup_type:
        query = query.filter(BackupJob.backup_type == backup_type)

    if status:
        query = query.filter(BackupJob.status == status)

    backups = query.order_by(BackupJob.created_at.desc()).offset(skip).limit(limit).all()
    return backups

@router.get("/backups/{backup_id}", response_model=BackupResponse)
async def get_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific backup job."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    backup = db.query(BackupJob).filter(BackupJob.id == backup_id).first()
    if backup is None:
        raise HTTPException(status_code=404, detail="Backup not found")

    return backup

@router.get("/backups/{backup_id}/logs", response_model=List[BackupLogResponse])
async def get_backup_logs(
    backup_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get backup job logs."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    logs = db.query(BackupLog).filter(
        BackupLog.backup_id == backup_id
    ).order_by(BackupLog.created_at.desc()).offset(skip).limit(limit).all()

    return logs

@router.post("/backups/{backup_id}/cancel")
async def cancel_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cancel a running backup job."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    backup = db.query(BackupJob).filter(BackupJob.id == backup_id).first()
    if backup is None:
        raise HTTPException(status_code=404, detail="Backup not found")

    if backup.status not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail="Backup cannot be cancelled")

    backup.status = "cancelled"
    backup.completed_at = datetime.utcnow()
    db.commit()

    # Log cancellation
    backup_log = BackupLog(
        backup_id=backup.id,
        level="info",
        message="Backup cancelled by user",
        details={"cancelled_by": current_user.id}
    )
    db.add(backup_log)
    db.commit()

    # Log security event
    security_metrics.record_security_event("backup_cancelled", "warning", {
        "user_id": current_user.id,
        "backup_id": backup_id
    })

    return {"message": "Backup cancelled successfully"}

@router.post("/restore")
async def restore_backup(
    restore_request: RestoreRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Restore from a backup."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Validate backup exists
        backup = db.query(BackupJob).filter(BackupJob.id == restore_request.backup_id).first()
        if backup is None:
            raise HTTPException(status_code=404, detail="Backup not found")

        if backup.status != "completed":
            raise HTTPException(status_code=400, detail="Backup is not completed and cannot be restored")

        # Create restore job
        restore_job = BackupJob(
            name=f"Restore from {backup.name}",
            backup_type="restore",
            source_backup_id=restore_request.backup_id,
            restore_options=restore_request.restore_options or {},
            status="pending",
            created_by=current_user.id
        )

        db.add(restore_job)
        db.commit()
        db.refresh(restore_job)

        # Start restore process in background
        background_tasks.add_task(
            backup_service.execute_restore,
            restore_job.id
        )

        # Log security event
        security_metrics.record_security_event("restore_started", "info", {
            "user_id": current_user.id,
            "backup_id": restore_request.backup_id,
            "restore_job_id": restore_job.id
        })

        return {
            "message": "Restore job started successfully",
            "restore_job_id": restore_job.id,
            "backup_id": restore_request.backup_id
        }

    except Exception as e:
        logger.error(f"Error starting restore: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start restore")

@router.get("/restore/{restore_id}/status")
async def get_restore_status(
    restore_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get restore job status."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    restore_job = db.query(BackupJob).filter(BackupJob.id == restore_id).first()
    if restore_job is None:
        raise HTTPException(status_code=404, detail="Restore job not found")

    return {
        "restore_job_id": restore_id,
        "status": restore_job.status,
        "progress": restore_job.progress,
        "started_at": restore_job.started_at,
        "completed_at": restore_job.completed_at,
        "error_message": restore_job.error_message
    }

@router.post("/cleanup")
async def cleanup_old_backups(
    days: int = Query(30, description="Delete backups older than N days"),
    keep_latest: int = Query(5, description="Always keep the latest N backups"),
    dry_run: bool = Query(False, description="Show what would be deleted without actually deleting"),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Clean up old backup files."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get backups to delete
        backups_to_delete = db.query(BackupJob).filter(
            BackupJob.created_at < cutoff_date,
            BackupJob.status == "completed"
        ).order_by(BackupJob.created_at.asc()).all()

        # Keep the latest N backups
        if keep_latest > 0:
            latest_backups = db.query(BackupJob).filter(
                BackupJob.status == "completed"
            ).order_by(BackupJob.created_at.desc()).limit(keep_latest).all()
            latest_backup_ids = [b.id for b in latest_backups]
            backups_to_delete = [b for b in backups_to_delete if b.id not in latest_backup_ids]

        if dry_run:
            return {
                "message": "Dry run completed",
                "backups_to_delete": len(backups_to_delete),
                "backups": [
                    {
                        "id": b.id,
                        "name": b.name,
                        "created_at": b.created_at,
                        "file_path": b.file_path
                    }
                    for b in backups_to_delete
                ]
            }

        # Delete backup files in background
        if backups_to_delete:
            background_tasks.add_task(
                backup_service.cleanup_backup_files,
                [b.id for b in backups_to_delete]
            )

            # Mark backups as deleted in database
            for backup in backups_to_delete:
                backup.status = "deleted"
                backup.deleted_at = datetime.utcnow()
                backup.deleted_by = current_user.id

            db.commit()

        # Log security event
        security_metrics.record_security_event("backup_cleanup_completed", "info", {
            "user_id": current_user.id,
            "backups_deleted": len(backups_to_delete),
            "days_threshold": days
        })

        return {
            "message": f"Cleanup job started for {len(backups_to_delete)} backups",
            "backups_deleted": len(backups_to_delete)
        }

    except Exception as e:
        logger.error(f"Error during backup cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to perform backup cleanup")

@router.get("/stats")
async def get_backup_stats(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get backup statistics."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Backup statistics
    total_backups = db.query(BackupJob).filter(
        BackupJob.created_at >= start_date,
        BackupJob.created_at <= end_date
    ).count()

    completed_backups = db.query(BackupJob).filter(
        BackupJob.created_at >= start_date,
        BackupJob.created_at <= end_date,
        BackupJob.status == "completed"
    ).count()

    failed_backups = db.query(BackupJob).filter(
        BackupJob.created_at >= start_date,
        BackupJob.created_at <= end_date,
        BackupJob.status == "failed"
    ).count()

    # Storage statistics
    from app.services.file_storage import file_storage_service
    storage_stats = file_storage_service.get_storage_stats()

    # Recent backup activity
    recent_backups = db.query(BackupJob).filter(
        BackupJob.created_at
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, BackupJob, BackupLog
from app.schemas.backup import (
    BackupCreate,
    BackupResponse,
    BackupLogResponse,
    RestoreRequest
)
from app.core.security import get_current_active_user
from app.core.security_metrics import security_metrics
from app.services.backup import backup_service
from datetime import datetime, timedelta
import logging
import os
import shutil

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/backup", response_model=BackupResponse)
async def create_backup(
    backup: BackupCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new backup job."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Create backup job
        db_backup = BackupJob(
            name=backup.name,
            backup_type=backup.backup_type,
            include_tables=backup.include_tables or [],
            exclude_tables=backup.exclude_tables or [],
            include_files=backup.include_files or [],
            exclude_files=backup.exclude_files or [],
            compression=backup.compression,
            encryption=backup.encryption,
            destination=backup.destination,
            retention_days=backup.retention_days,
            scheduled_time=backup.scheduled_time,
            status="pending",
            created_by=current_user.id
        )

        db.add(db_backup)
        db.commit()
        db.refresh(db_backup)

        # Start backup process in background
        background_tasks.add_task(
            backup_service.execute_backup,
            db_backup.id
        )

        # Log security event
        security_metrics.record_security_event("backup_created", "info", {
            "user_id": current_user.id,
            "backup_id": db_backup.id,
            "backup_name": backup.name,
            "backup_type": backup.backup_type
        })

        return db_backup

    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create backup")

@router.get("/backups", response_model=List[BackupResponse])
async def list_backups(
    skip: int = 0,
    limit: int = 100,
    backup_type: Optional[str] = Query(None, description="Filter by backup type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List backup jobs."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = db.query(BackupJob).filter(
        BackupJob.created_at >= start_date,
        BackupJob.created_at <= end_date
    )

    if backup_type:
        query = query.filter(BackupJob.backup_type == backup_type)

    if status:
        query = query.filter(BackupJob.status == status)

    backups = query.order_by(BackupJob.created_at.desc()).offset(skip).limit(limit).all()
    return backups

@router.get("/backups/{backup_id}", response_model=BackupResponse)
async def get_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific backup job."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    backup = db.query(BackupJob).filter(BackupJob.id == backup_id).first()
    if backup is None:
        raise HTTPException(status_code=404, detail="Backup not found")

    return backup

@router.get("/backups/{backup_id}/logs", response_model=List[BackupLogResponse])
async def get_backup_logs(
    backup_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get backup job logs."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    logs = db.query(BackupLog).filter(
        BackupLog.backup_id == backup_id
    ).order_by(BackupLog.created_at.desc()).offset(skip).limit(limit).all()

    return logs

@router.post("/backups/{backup_id}/cancel")
async def cancel_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cancel a running backup job."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    backup = db.query(BackupJob).filter(BackupJob.id == backup_id).first()
    if backup is None:
        raise HTTPException(status_code=404, detail="Backup not found")

    if backup.status not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail="Backup cannot be cancelled")

    backup.status = "cancelled"
    backup.completed_at = datetime.utcnow()
    db.commit()

    # Log cancellation
    backup_log = BackupLog(
        backup_id=backup.id,
        level="info",
        message="Backup cancelled by user",
        details={"cancelled_by": current_user.id}
    )
    db.add(backup_log)
    db.commit()

    # Log security event
    security_metrics.record_security_event("backup_cancelled", "warning", {
        "user_id": current_user.id,
        "backup_id": backup_id
    })

    return {"message": "Backup cancelled successfully"}

@router.post("/restore")
async def restore_backup(
    restore_request: RestoreRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Restore from a backup."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Validate backup exists
        backup = db.query(BackupJob).filter(BackupJob.id == restore_request.backup_id).first()
        if backup is None:
            raise HTTPException(status_code=404, detail="Backup not found")

        if backup.status != "completed":
            raise HTTPException(status_code=400, detail="Backup is not completed and cannot be restored")

        # Create restore job
        restore_job = BackupJob(
            name=f"Restore from {backup.name}",
            backup_type="restore",
            source_backup_id=restore_request.backup_id,
            restore_options=restore_request.restore_options or {},
            status="pending",
            created_by=current_user.id
        )

        db.add(restore_job)
