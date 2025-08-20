from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, SystemConfiguration, ConfigurationHistory
from app.schemas.system_config import (
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemConfigResponse,
    ConfigHistoryResponse
)
from app.core.security import get_current_active_user
from app.core.security_metrics import security_metrics
from app.services.system_config import system_config_service
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[SystemConfigResponse])
async def list_system_configs(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, description="Filter by category"),
    is_sensitive: Optional[bool] = Query(None, description="Filter by sensitive status"),
    search: Optional[str] = Query(None, description="Search in key or description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List system configurations."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(SystemConfiguration)

    # Filter by category
    if category:
        query = query.filter(SystemConfiguration.category == category)

    # Filter by sensitive status
    if is_sensitive is not None:
        query = query.filter(SystemConfiguration.is_sensitive == is_sensitive)

    # Search in key or description
    if search:
        query = query.filter(
            (SystemConfiguration.key.ilike(f"%{search}%")) |
            (SystemConfiguration.description.ilike(f"%{search}%"))
        )

    configs = query.order_by(SystemConfiguration.category, SystemConfiguration.key).offset(skip).limit(limit).all()
    return configs

@router.post("/", response_model=SystemConfigResponse)
async def create_system_config(
    config: SystemConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new system configuration."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Check if key already exists
        existing = db.query(SystemConfiguration).filter(SystemConfiguration.key == config.key).first()
        if existing:
            raise HTTPException(status_code=400, detail="Configuration key already exists")

        # Validate value type
        if not system_config_service.validate_config_value(config.value_type, config.value):
            raise HTTPException(status_code=400, detail=f"Invalid value for type {config.value_type}")

        # Create configuration
        db_config = SystemConfiguration(
            key=config.key,
            value=config.value,
            value_type=config.value_type,
            category=config.category,
            description=config.description,
            is_sensitive=config.is_sensitive,
            is_active=config.is_active,
            validation_rules=config.validation_rules or {},
            options=config.options or [],
            created_by=current_user.id
        )

        db.add(db_config)
        db.commit()
        db.refresh(db_config)

        # Log configuration change
        await system_config_service.log_config_change(
            db, db_config.id, "created", None, config.value, current_user.id
        )

        # Log security event
        security_metrics.record_security_event("system_config_created", "info", {
            "user_id": current_user.id,
            "config_id": db_config.id,
            "config_key": config.key,
            "category": config.category
        })

        return db_config

    except Exception as e:
        logger.error(f"Error creating system config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create configuration")

@router.get("/{config_id}", response_model=SystemConfigResponse)
async def get_system_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific system configuration."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    config = db.query(SystemConfiguration).filter(SystemConfiguration.id == config_id).first()
    if config is None:
        raise HTTPException(status_code=404, detail="Configuration not found")

    return config

@router.put("/{config_id}", response_model=SystemConfigResponse)
async def update_system_config(
    config_id: int,
    config_update: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update system configuration."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    config = db.query(SystemConfiguration).filter(SystemConfiguration.id == config_id).first()
    if config is None:
        raise HTTPException(status_code=404, detail="Configuration not found")

    old_value = config.value
    old_is_active = config.is_active

    # Update fields
    for field, value in config_update.dict(exclude_unset=True).items():
        if field == "value":
            # Validate new value
            if not system_config_service.validate_config_value(config.value_type, value):
                raise HTTPException(status_code=400, detail=f"Invalid value for type {config.value_type}")
        setattr(config, field, value)

    config.updated_at = datetime.utcnow()
    config.updated_by = current_user.id
    db.commit()
    db.refresh(config)

    # Log configuration change
    await system_config_service.log_config_change(
        db, config.id, "updated", old_value, config.value, current_user.id
    )

    # Log security event
    security_metrics.record_security_event("system_config_updated", "info", {
        "user_id": current_user.id,
        "config_id": config_id,
        "config_key": config.key,
        "category": config.category
    })

    return config

@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_system_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete system configuration."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    config = db.query(SystemConfiguration).filter(SystemConfiguration.id == config_id).first()
    if config is None:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Don't allow deletion of system-critical configurations
    if config.key in ["system.maintenance_mode", "system.debug_mode", "security.enabled"]:
        raise HTTPException(status_code=400, detail="Cannot delete system-critical configuration")

    old_value = config.value
    config_key = config.key

    db.delete(config)
    db.commit()

    # Log configuration change
    await system_config_service.log_config_change(
        db, config_id, "deleted", old_value, None, current_user.id
    )

    # Log security event
    security_metrics.record_security_event("system_config_deleted", "warning", {
        "user_id": current_user.id,
        "config_id": config_id,
        "config_key": config_key
    })

    return None

@router.get("/{config_id}/history", response_model=List[ConfigHistoryResponse])
async def get_config_history(
    config_id: int,
    skip: int = 0,
    limit: int = 100,
    days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get configuration change history."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    config = db.query(SystemConfiguration).filter(SystemConfiguration.id == config_id).first()
    if config is None:
        raise HTTPException(status_code=404, detail="Configuration not found")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    history = db.query(ConfigurationHistory).filter(
        ConfigurationHistory.config_id == config_id,
        ConfigurationHistory.created_at >= start_date,
        ConfigurationHistory.created_at <= end_date
    ).order_by(ConfigurationHistory.created_at.desc()).offset(skip).limit(limit).all()

    return history

@router.post("/refresh-cache")
async def refresh_config_cache(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Refresh configuration cache."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        await system_config_service.refresh_cache()

        # Log security event
        security_metrics.record_security_event("config_cache_refreshed", "info", {
            "user_id": current_user.id
        })

        return {"message": "Configuration cache refreshed successfully"}

    except Exception as e:
        logger.error(f"Error refreshing config cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to refresh configuration cache")

@router.get("/categories")
async def get_config_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all configuration categories."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    categories = db.query(SystemConfiguration.category).distinct().all()
    return {"categories": [cat[0] for cat in categories]}

@router.get("/export")
async def export_configurations(
    format: str = Query("json", description="Export format: json, yaml"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export system configurations."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(SystemConfiguration)

    if category:
        query = query.filter(SystemConfiguration.category == category)

    configs = query.all()

    # Format configurations for export
    export_data = {}
    for config in configs:
        if config.category not in export_data:
            export_data[config.category] = {}

        export_data[config.category][config.key] = {
            "value": config.value,
            "value_type": config.value_type,
            "description": config.description,
            "is_sensitive": config.is_sensitive,
            "is_active": config.is_active
        }

    if format == "yaml":
        import yaml
        content = yaml.dump(export_data, default_flow_style=False)
        media_type = "application/x-yaml"
        filename = "system_config.yaml"
    else:
        content = json.dumps(export_data, indent=2)
        media_type = "application/json"
        filename = "system_config.json"

    from fastapi.responses import Response
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/import")
async def import_configurations(
    file_content: str,
    format: str = Query("json", description="Import format: json, yaml"),
    merge_strategy: str = Query("replace", description="Merge strategy: replace, merge"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Import system configurations."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Parse import data
        if format == "yaml":
            import yaml
            import_data = yaml.safe_load(file_content)
        else:
            import_data = json.loads(file_content)

        imported_count = 0
        updated_count = 0

        for category, configs in import_data.items():
            for key, config_data in configs.items():
                existing = db.query(SystemConfiguration).filter(
                    SystemConfiguration.key == key
                ).first()

                if existing:
                    if merge_strategy == "replace":
                        # Update existing configuration
                        old_value = existing.value
                        existing.value = config_data["value"]
                        existing.description = config_data.get("description", existing.description)
                        existing.is_sensitive = config_data.get("is_sensitive", existing.is_sensitive)
                        existing.is_active = config_data.get("is_active", existing.is_active)
                        existing.updated_at = datetime.utcnow()
                        existing.updated_by = current_user.id

                        await system_config_service.log_config_change(
                            db, existing.id, "imported", old_value, existing.value, current_user.id
                        )
                        updated_count += 1
                else:
                    # Create new configuration
                    new_config = SystemConfiguration(
                        key=key,
                        value=config_data["value"],
                        value_type=config_data.get("value_type", "string"),
                        category=category,
                        description=config_data.get("description", ""),
                        is_sensitive=config_data.get("is_sensitive", False),
                        is_active=config_data.get("is_active", True),
                        created_by=current_user.id
                    )
                    db.add(new_config)
                    imported_count += 1

        db.commit()

        # Log security event
        security_metrics.record_security_event("system_config_imported", "info", {
            "user_id":
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, SystemConfiguration, ConfigurationHistory
from app.schemas.system_config import (
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemConfigResponse,
    ConfigHistoryResponse
)
from app.core.security import get_current_active_user
from app.core.security_metrics import security_metrics
from app.services.system_config import system_config_service
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[SystemConfigResponse])
async def list_system_configs(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, description="Filter by category"),
    is_sensitive: Optional[bool] = Query(None, description="Filter by sensitive status"),
    search: Optional[str] = Query(None, description="Search in key or description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List system configurations."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(SystemConfiguration)

    # Filter by category
    if category:
        query = query.filter(SystemConfiguration.category == category)

    # Filter by sensitive status
    if is_sensitive is not None:
        query = query.filter(SystemConfiguration.is_sensitive == is_sensitive)

    # Search in key or description
    if search:
        query = query.filter(
            (SystemConfiguration.key.ilike(f"%{search}%")) |
            (SystemConfiguration.description.ilike(f"%{search}%"))
        )

    configs = query.order_by(SystemConfiguration.category, SystemConfiguration.key).offset(skip).limit(limit).all()
    return configs

@router.post("/", response_model=SystemConfigResponse)
async def create_system_config(
    config: SystemConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new system configuration."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Check if key already exists
        existing = db.query(SystemConfiguration).filter(SystemConfiguration.key == config.key).first()
        if existing:
            raise HTTPException(status_code=400, detail="Configuration key already exists")

        # Validate value type
        if not system_config_service.validate_config_value(config.value_type, config.value):
            raise HTTPException(status_code=400, detail=f"Invalid value for type {config.value_type}")

        # Create configuration
        db_config = SystemConfiguration(
            key=config.key,
            value=config.value,
            value_type=config.value_type,
            category=config.category,
            description=config.description,
            is_sensitive=config.is_sensitive,
            is_active=config.is_active,
            validation_rules=config.validation_rules or {},
            options=config.options or [],
            created_by=current_user.id
        )

        db.add(db_config)
        db.commit()
        db.refresh(db_config)

        # Log configuration change
        await system_config_service.log_config_change(
            db, db_config.id, "created", None, config.value, current_user.id
        )

        # Log security event
        security_metrics.record_security_event("system_config_created", "info", {
            "user_id": current_user.id,
            "config_id": db_config.id,
            "config_key": config.key,
            "category": config.category
        })

        return db_config

    except Exception as e:
        logger.error(f"Error creating system config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create configuration")

@router.get("/{config_id}", response_model=SystemConfigResponse)
async def get_system_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific system configuration."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    config = db.query(SystemConfiguration).filter(SystemConfiguration.id == config_id).first()
    if config is None:
        raise HTTPException(status_code=404, detail="Configuration not found")

    return config

@router.put("/{config_id}", response_model=SystemConfigResponse)
async def update_system_config(
    config_id: int,
    config_update: SystemConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update system configuration."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    config = db.query
