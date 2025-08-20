from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from datetime import datetime, timedelta
import json
import os
import secrets
import uuid
import hashlib
from ..ai_team.mlops import MLOpsManager, ModelType
from app.core.config import settings
from app.core.security_metrics import security_metrics
from app.auth import create_access_token, get_current_user

router = APIRouter()
mlops_manager = MLOpsManager()

class ModelInfo(BaseModel):
    name: str
    type: str
    provider: str
    model_size: str
    languages: List[str] = []
    is_local: bool = False
    version: str = "1.0.0"
    status: str = "active"
    performance_metrics: Dict[str, float] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

class GenerationRequest(BaseModel):
    model_name: str
    input_data: Any
    parameters: Dict[str, Any] = {}
    language: str = "python"  # For code generation
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)

class FineTuningRequest(BaseModel):
    model_name: str
    training_data: List[Dict[str, Any]]
    hyperparameters: Dict[str, Any] = {}
    epochs: int = Field(default=3, ge=1, le=100)
    learning_rate: float = Field(default=2e-5, ge=1e-6, le=1e-3)
    batch_size: int = Field(default=8, ge=1, le=64)

class ModelVersion(BaseModel):
    version: str
    model_name: str
    changes: List[str]
    performance_improvements: Dict[str, float]
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True

class ModelComparison(BaseModel):
    models: List[str]
    test_data: List[Dict[str, Any]]
    metrics: List[str] = ["accuracy", "latency", "cost"]

# API Key Management Models
class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., description="Name for the API key")
    description: Optional[str] = Field(None, description="Description of the API key purpose")
    permissions: List[str] = Field(default=["read"], description="Permissions for this API key")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Days until expiration")
    rate_limit: Optional[int] = Field(None, ge=1, le=10000, description="Requests per hour limit")
    allowed_models: Optional[List[str]] = Field(None, description="Specific models this key can access")

class ApiKey(BaseModel):
    id: str
    name: str
    description: Optional[str]
    key_prefix: str
    permissions: List[str]
    rate_limit: Optional[int]
    allowed_models: Optional[List[str]]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int = 0

class ApiKeyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    key: str
    permissions: List[str]
    rate_limit: Optional[int]
    allowed_models: Optional[List[str]]
    created_at: datetime
    expires_at: Optional[datetime]
    message: str = "API key generated successfully. Store this key securely as it won't be shown again."

class ApiKeyUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    rate_limit: Optional[int] = Field(None, ge=1, le=10000)
    allowed_models: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ApiKeyValidationResponse(BaseModel):
    is_valid: bool
    api_key_id: Optional[str]
    permissions: List[str]
    rate_limit_remaining: Optional[int]
    expires_in: Optional[int]
    message: str

@router.get("/models")
async def list_models() -> Dict[str, List[ModelInfo]]:
    """List all available AI models by type with performance metrics."""
    models_by_type = {}
    for model_name, model in mlops_manager.models.items():
        model_type = model.model_type.value
        if model_type not in models_by_type:
            models_by_type[model_type] = []

        # Get performance metrics
        performance_metrics = await mlops_manager.get_model_performance_metrics(model_name)

        models_by_type[model_type].append(ModelInfo(
            name=model.name,
            type=model.model_type.value,
            provider=model.provider.value,
            model_size=model.model_size,
            languages=model.languages,
            is_local=model.is_local,
            version=model.version if hasattr(model, 'version') else "1.0.0",
            status=model.status if hasattr(model, 'status') else "active",
            performance_metrics=performance_metrics,
            created_at=model.created_at if hasattr(model, 'created_at') else datetime.now(),
            last_updated=model.last_updated if hasattr(model, 'last_updated') else datetime.now()
        ))
    return models_by_type

@router.get("/models/{model_name}/details")
async def get_model_details(model_name: str) -> ModelInfo:
    """Get detailed information about a specific model."""
    try:
        model = mlops_manager.models.get(model_name)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        performance_metrics = await mlops_manager.get_model_performance_metrics(model_name)

        return ModelInfo(
            name=model.name,
            type=model.model_type.value,
            provider=model.provider.value,
            model_size=model.model_size,
            languages=model.languages,
            is_local=model.is_local,
            version=model.version if hasattr(model, 'version') else "1.0.0",
            status=model.status if hasattr(model, 'status') else "active",
            performance_metrics=performance_metrics,
            created_at=model.created_at if hasattr(model, 'created_at') else datetime.now(),
            last_updated=model.last_updated if hasattr(model, 'last_updated') else datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/text")
async def generate_text(request: GenerationRequest) -> Dict[str, Any]:
    """Generate text using specified language model."""
    try:
        return await mlops_manager.generate_text(request.input_data, request.model_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/generate/code")
async def generate_code(request: GenerationRequest) -> Dict[str, Any]:
    """Generate code using specified code model."""
    try:
        return await mlops_manager.generate_code(
            request.input_data,
            request.language,
            request.model_name
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/generate/image")
async def generate_image(request: GenerationRequest) -> Dict[str, Any]:
    """Generate image using specified image model."""
    try:
        return await mlops_manager.generate_image(request.input_data, request.model_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/generate/speech")
async def generate_speech(request: GenerationRequest) -> Dict[str, Any]:
    """Generate speech from text using specified audio model."""
    try:
        return await mlops_manager.generate_speech(request.input_data, request.model_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/embeddings")
async def get_embeddings(request: GenerationRequest) -> Dict[str, Any]:
    """Get embeddings for texts using specified embedding model."""
    try:
        texts = request.input_data if isinstance(request.input_data, list) else [request.input_data]
        result = await mlops_manager.get_embeddings(texts, request.model_name)

        return {
            **result,
            "model_used": request.model_name,
            "texts_processed": len(texts),
            "embedding_dimensions": len(result.get("embeddings", [[]])[0]) if result.get("embeddings") else 0
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Advanced AI Features - Model Fine-tuning
@router.post("/models/{model_name}/fine-tune")
async def fine_tune_model(model_name: str, request: FineTuningRequest) -> Dict[str, Any]:
    """Fine-tune a model with custom training data."""
    try:
        # Validate model exists
        if model_name not in mlops_manager.models:
            raise HTTPException(status_code=404, detail="Model not found")

        # Start fine-tuning job
        job_id = await mlops_manager.start_fine_tuning(
            model_name=model_name,
            training_data=request.training_data,
            hyperparameters=request.hyperparameters,
            epochs=request.epochs,
            learning_rate=request.learning_rate,
            batch_size=request.batch_size
        )

        return {
            "job_id": job_id,
            "model_name": model_name,
            "status": "started",
            "estimated_duration": "2-4 hours",
            "training_samples": len(request.training_data),
            "hyperparameters": request.hyperparameters
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_name}/fine-tune/{job_id}")
async def get_fine_tuning_status(model_name: str, job_id: str) -> Dict[str, Any]:
    """Get the status of a fine-tuning job."""
    try:
        status = await mlops_manager.get_fine_tuning_status(job_id)

        if not status:
            raise HTTPException(status_code=404, detail="Fine-tuning job not found")

        return {
            **status,
            "model_name": model_name,
            "job_id": job_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{model_name}/versions")
async def create_model_version(model_name: str, version: ModelVersion) -> Dict[str, Any]:
    """Create a new version of a model."""
    try:
        if model_name not in mlops_manager.models:
            raise HTTPException(status_code=404, detail="Model not found")

        version_id = await mlops_manager.create_model_version(
            model_name=model_name,
            version=version.version,
            changes=version.changes,
            performance_improvements=version.performance_improvements
        )

        return {
            "version_id": version_id,
            "model_name": model_name,
            "version": version.version,
            "status": "created",
            "changes": version.changes,
            "performance_improvements": version.performance_improvements
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_name}/versions")
async def get_model_versions(model_name: str) -> List[Dict[str, Any]]:
    """Get all versions of a model."""
    try:
        if model_name not in mlops_manager.models:
            raise HTTPException(status_code=404, detail="Model not found")

        versions = await mlops_manager.get_model_versions(model_name)
        return versions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/models/{model_name}/versions/{version}/activate")
async def activate_model_version(model_name: str, version: str) -> Dict[str, Any]:
    """Activate a specific version of a model."""
    try:
        success = await mlops_manager.activate_model_version(model_name, version)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to activate version")

        return {
            "model_name": model_name,
            "version": version,
            "status": "activated",
            "message": f"Model {model_name} version {version} is now active"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/compare")
async def compare_models(request: ModelComparison) -> Dict[str, Any]:
    """Compare multiple models on test data."""
    try:
        # Validate all models exist
        for model_name in request.models:
            if model_name not in mlops_manager.models:
                raise HTTPException(status_code=404, detail=f"Model {model_name} not found")

        comparison_results = await mlops_manager.compare_models(
            models=request.models,
            test_data=request.test_data,
            metrics=request.metrics
        )

        return {
            **comparison_results,
            "models_compared": request.models,
            "test_samples": len(request.test_data),
            "metrics_evaluated": request.metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_name}/performance")
async def get_model_performance_history(model_name: str, days: int = 30) -> Dict[str, Any]:
    """Get performance history for a model over specified number of days."""
    try:
        if model_name not in mlops_manager.models:
            raise HTTPException(status_code=404, detail="Model not found")

        performance_history = await mlops_manager.get_model_performance_history(
            model_name, days
        )

        return {
            "model_name": model_name,
            "period_days": days,
            "performance_history": performance_history,
            "summary": await mlops_manager.get_performance_summary(model_name, days)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{model_name}/optimize")
async def optimize_model(model_name: str, optimization_config: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize a model for better performance."""
    try:
        if model_name not in mlops_manager.models:
            raise HTTPException(status_code=404, detail="Model not found")

        optimization_id = await mlops_manager.start_model_optimization(
            model_name=model_name,
            config=optimization_config
        )

        return {
            "optimization_id": optimization_id,
            "model_name": model_name,
            "status": "started",
            "config": optimization_config,
            "estimated_duration": "1-2 hours"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_name}/optimize/{optimization_id}")
async def get_optimization_status(model_name: str, optimization_id: str) -> Dict[str, Any]:
    """Get the status of a model optimization job."""
    try:
        status = await mlops_manager.get_optimization_status(optimization_id)

        if not status:
            raise HTTPException(status_code=404, detail="Optimization job not found")

        return {
            **status,
            "model_name": model_name,
            "optimization_id": optimization_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_name}/analytics")
async def get_model_analytics(model_name: str, period: str = "7d") -> Dict[str, Any]:
    """Get comprehensive analytics for a model."""
    try:
        if model_name not in mlops_manager.models:
            raise HTTPException(status_code=404, detail="Model not found")

        analytics = await mlops_manager.get_model_analytics(model_name, period)

        return {
            "model_name": model_name,
            "period": period,
            "analytics": analytics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{model_name}/export")
async def export_model(model_name: str, export_format: str = "pytorch") -> Dict[str, Any]:
    """Export a model in specified format."""
    try:
        if model_name not in mlops_manager.models:
            raise HTTPException(status_code=404, detail="Model not found")

        export_id = await mlops_manager.export_model(model_name, export_format)

        return {
            "export_id": export_id,
            "model_name": model_name,
            "format": export_format,
            "status": "exporting",
            "estimated_duration": "30 minutes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_name}/export/{export_id}")
async def get_export_status(model_name: str, export_id: str) -> Dict[str, Any]:
    """Get the status of a model export job."""
    try:
        status = await mlops_manager.get_export_status(export_id)

        if not status:
            raise HTTPException(status_code=404, detail="Export job not found")

        return {
            **status,
            "model_name": model_name,
            "export_id": export_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API Key Management Endpoints
@router.post("/api-keys/generate")
async def generate_api_key(
    request: ApiKeyCreateRequest,
    current_user: dict = Depends(get_current_user)
) -> ApiKeyResponse:
    """Generate a new API key automatically with comprehensive security features."""
    try:
        user_id = current_user.username if hasattr(current_user, 'username') else str(current_user)
        api_key_response = await api_key_generator.create_api_key(request, user_id)

        security_metrics.record_security_event("api_key_generated", "info")
        return api_key_response
    except Exception as e:
        security_metrics.record_security_event("api_key_generation_failed", "error")
        raise HTTPException(status_code=500, detail=f"Failed to generate API key: {str(e)}")

@router.get("/api-keys")
async def list_api_keys(
    current_user: dict = Depends(get_current_user)
) -> List[ApiKey]:
    """List all API keys for the authenticated user."""
    try:
        user_id = current_user.username if hasattr(current_user, 'username') else str(current_user)
        api_keys = await api_key_generator.list_api_keys(user_id)
        return api_keys
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list API keys: {str(e)}")

@router.post("/api-keys/validate")
async def validate_api_key(api_key: str) -> ApiKeyValidationResponse:
    """Validate an API key and return its status and permissions."""
    try:
        validation_result = await api_key_generator.validate_api_key(api_key)
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate API key: {str(e)}")

@router.put("/api-keys/{key_id}")
async def update_api_key(
    key_id: str,
    request: ApiKeyUpdateRequest,
    current_user: dict = Depends(get_current_user)
) -> ApiKey:
    """Update API key metadata."""
    try:
        user_id = current_user.username if hasattr(current_user, 'username') else str(current_user)
        updated_key = await api_key_generator.update_api_key(key_id, user_id, request)

        if not updated_key:
            raise HTTPException(status_code=404, detail="API key not found")

        return updated_key
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update API key: {str(e)}")

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """Revoke an API key."""
    try:
        user_id = current_user.username if hasattr(current_user, 'username') else str(current_user)
        success = await api_key_generator.revoke_api_key(key_id, user_id)

        if not success:
            raise HTTPException(status_code=404, detail="API key not found")

        return {"message": "API key revoked successfully", "key_id": key_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke API key: {str(e)}")

@router.get("/api-keys/stats")
async def get_api_key_stats(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get API key usage statistics and analytics."""
    try:
        user_id = current_user.username if hasattr(current_user, 'username') else str(current_user)
        user_keys = await api_key_generator.list_api_keys(user_id)

        total_usage = sum(key.usage_count for key in user_keys)
        active_keys = sum(1 for key in user_keys if key.is_active)
        expired_keys = sum(1 for key in user_keys if key.expires_at and key.expires_at < datetime.utcnow())

        # Get detailed usage breakdown
        usage_by_key = {}
        for key in user_keys:
            usage_by_key[key.id] = {
                "name": key.name,
                "usage_count": key.usage_count,
                "last_used": key.last_used_at,
                "created_at": key.created_at,
                "is_active": key.is_active
            }

        return {
            "total_keys": len(user_keys),
            "active_keys": active_keys,
            "expired_keys": expired_keys,
            "total_usage": total_usage,
            "usage_by_key": usage_by_key,
            "security_metrics": security_metrics.get_current_metrics()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get API key stats: {str(e)}")

@router.post("/api-keys/batch-generate")
async def batch_generate_api_keys(
    requests: List[ApiKeyCreateRequest],
    current_user: dict = Depends(get_current_user)
) -> List[ApiKeyResponse]:
    """Generate multiple API keys in a single request."""
    try:
        user_id = current_user.username if hasattr(current_user, 'username') else str(current_user)
        api_keys = []

        for request in requests:
            api_key_response = await api_key_generator.create_api_key(request, user_id)
            api_keys.append(api_key_response)

        security_metrics.record_security_event("api_keys_batch_generated", "info")
        return api_keys
    except Exception as e:
        security_metrics.record_security_event("api_keys_batch_generation_failed", "error")
        raise HTTPException(status_code=500, detail=f"Failed to batch generate API keys: {str(e)}")

@router.get("/api-keys/audit-log")
async def get_api_key_audit_log(
    current_user: dict = Depends(get_current_user),
    days: int = 7
) -> Dict[str, Any]:
    """Get audit log for API key activities."""
    try:
        user_id = current_user.username if hasattr(current_user, 'username') else str(current_user)
        user_keys = await api_key_generator.list_api_keys(user_id)

        # Generate audit log based on key activities
        audit_log = []
        for key in user_keys:
            audit_log.extend([
                {
                    "event": "key_created",
                    "key_id": key.id,
                    "key_name": key.name,
                    "timestamp": key.created_at,
                    "details": {"permissions": key.permissions, "rate_limit": key.rate_limit}
                },
                {
                    "event": "key_last_used",
                    "key_id": key.id,
                    "key_name": key.name,
                    "timestamp": key.last_used_at,
                    "details": {"usage_count": key.usage_count}
                }
            ])

        # Sort by timestamp and filter by date range
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        audit_log = [
            entry for entry in audit_log
            if entry["timestamp"] and entry["timestamp"] > cutoff_date
        ]
        audit_log.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "period_days": days,
            "total_events": len(audit_log),
            "audit_log": audit_log[:100]  # Limit to last 100 events
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit log: {str(e)}")

# In-memory API key storage (in production, use a database)
api_keys_storage = {}
api_key_usage_tracking = {}

class ApiKeyGenerator:
    """Automatic API key token generator with comprehensive management."""

    def __init__(self):
        self.key_length = 64
        self.prefix = "sk_"
        self.hash_algorithm = "sha256"

    def generate_secure_key(self) -> str:
        """Generate a cryptographically secure API key."""
        # Generate random bytes and convert to base64-like string
        random_bytes = secrets.token_bytes(self.key_length)
        key = self.prefix + secrets.token_urlsafe(48)
        return key

    def hash_key(self, key: str) -> str:
        """Hash the API key for secure storage."""
        return hashlib.sha256(key.encode()).hexdigest()

    def extract_key_prefix(self, key: str) -> str:
        """Extract the prefix from the key for display purposes."""
        return key[:12] + "..."

    async def create_api_key(self, request: ApiKeyCreateRequest, user_id: str) -> ApiKeyResponse:
        """Create a new API key with automatic generation and validation."""
        # Generate the actual API key
        api_key = self.generate_secure_key()
        key_hash = self.hash_key(api_key)

        # Calculate expiration
        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

        # Create API key record
        key_id = str(uuid.uuid4())
        api_key_record = ApiKey(
            id=key_id,
            name=request.name,
            description=request.description,
            key_prefix=self.extract_key_prefix(api_key),
            permissions=request.permissions,
            rate_limit=request.rate_limit,
            allowed_models=request.allowed_models,
            is_active=True,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            last_used_at=None,
            usage_count=0
        )

        # Store the hashed key and metadata
        api_keys_storage[key_hash] = {
            "id": key_id,
            "user_id": user_id,
            "name": request.name,
            "description": request.description,
            "permissions": request.permissions,
            "rate_limit": request.rate_limit,
            "allowed_models": request.allowed_models,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "last_used_at": None,
            "usage_count": 0
        }

        # Initialize usage tracking
        api_key_usage_tracking[key_hash] = {
            "hourly_usage": 0,
            "last_reset": datetime.utcnow(),
            "total_usage": 0
        }

        # Record security event
        security_metrics.record_security_event("api_key_created", "info")

        return ApiKeyResponse(
            id=key_id,
            name=request.name,
            description=request.description,
            key=api_key,
            permissions=request.permissions,
            rate_limit=request.rate_limit,
            allowed_models=request.allowed_models,
            created_at=datetime.utcnow(),
            expires_at=expires_at
        )

    async def validate_api_key(self, api_key: str) -> ApiKeyValidationResponse:
        """Validate an API key and return its permissions and status."""
        key_hash = self.hash_key(api_key)

        if key_hash not in api_keys_storage:
            security_metrics.record_security_event("api_key_invalid", "warning")
            return ApiKeyValidationResponse(
                is_valid=False,
                message="Invalid API key"
            )

        key_data = api_keys_storage[key_hash]

        # Check if key is active
        if not key_data["is_active"]:
            security_metrics.record_security_event("api_key_inactive", "warning")
            return ApiKeyValidationResponse(
                is_valid=False,
                message="API key is inactive"
            )

        # Check expiration
        if key_data["expires_at"] and datetime.utcnow() > key_data["expires_at"]:
            security_metrics.record_security_event("api_key_expired", "warning")
            return ApiKeyValidationResponse(
                is_valid=False,
                message="API key has expired"
            )

        # Check rate limit
        usage_data = api_key_usage_tracking.get(key_hash, {"hourly_usage": 0, "last_reset": datetime.utcnow()})

        # Reset hourly usage if needed
        if datetime.utcnow() - usage_data["last_reset"] > timedelta(hours=1):
            usage_data["hourly_usage"] = 0
            usage_data["last_reset"] = datetime.utcnow()

        rate_limit_remaining = None
        if key_data["rate_limit"]:
            rate_limit_remaining = max(0, key_data["rate_limit"] - usage_data["hourly_usage"])

            if rate_limit_remaining <= 0:
                security_metrics.record_security_event("api_key_rate_limited", "warning")
                return ApiKeyValidationResponse(
                    is_valid=False,
                    message="Rate limit exceeded"
                )

        # Calculate expires in
        expires_in = None
        if key_data["expires_at"]:
            expires_in = int((key_data["expires_at"] - datetime.utcnow()).total_seconds())

        # Update usage
        usage_data["hourly_usage"] += 1
        usage_data["total_usage"] += 1
        api_key_usage_tracking[key_hash] = usage_data

        # Update last used
        key_data["last_used_at"] = datetime.utcnow()
        key_data["usage_count"] += 1
        api_keys_storage[key_hash] = key_data

        # Record successful authentication
        security_metrics.record_auth_attempt("success")
        security_metrics.record_security_event("api_key_validated", "info")

        return ApiKeyValidationResponse(
            is_valid=True,
            api_key_id=key_data["id"],
            permissions=key_data["permissions"],
            rate_limit_remaining=rate_limit_remaining,
            expires_in=expires_in,
            message="API key is valid"
        )

    async def list_api_keys(self, user_id: str) -> List[ApiKey]:
        """List all API keys for a user."""
        user_keys = []
        for key_hash, key_data in api_keys_storage.items():
            if key_data["user_id"] == user_id:
                user_keys.append(ApiKey(
                    id=key_data["id"],
                    name=key_data["name"],
                    description=key_data["description"],
                    key_prefix=key_data["id"][:8] + "...",
                    permissions=key_data["permissions"],
                    rate_limit=key_data["rate_limit"],
                    allowed_models=key_data["allowed_models"],
                    is_active=key_data["is_active"],
                    created_at=key_data["created_at"],
                    expires_at=key_data["expires_at"],
                    last_used_at=key_data["last_used_at"],
                    usage_count=key_data["usage_count"]
                ))
        return user_keys

    async def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """Revoke an API key."""
        for key_hash, key_data in api_keys_storage.items():
            if key_data["id"] == key_id and key_data["user_id"] == user_id:
                key_data["is_active"] = False
                api_keys_storage[key_hash] = key_data

                # Remove from usage tracking
                if key_hash in api_key_usage_tracking:
                    del api_key_usage_tracking[key_hash]

                security_metrics.record_security_event("api_key_revoked", "info")
                return True
        return False

    async def update_api_key(self, key_id: str, user_id: str, update_data: ApiKeyUpdateRequest) -> Optional[ApiKey]:
        """Update API key metadata."""
        for key_hash, key_data in api_keys_storage.items():
            if key_data["id"] == key_id and key_data["user_id"] == user_id:
                if update_data.name is not None:
                    key_data["name"] = update_data.name
                if update_data.description is not None:
                    key_data["description"] = update_data.description
                if update_data.permissions is not None:
                    key_data["permissions"] = update_data.permissions
                if update_data.rate_limit is not None:
                    key_data["rate_limit"] = update_data.rate_limit
                if update_data.allowed_models is not None:
                    key_data["allowed_models"] = update_data.allowed_models
                if update_data.is_active is not None:
                    key_data["is_active"] = update_data.is_active

                api_keys_storage[key_hash] = key_data

                security_metrics.record_security_event("api_key_updated", "info")

                return ApiKey(
                    id=key_data["id"],
                    name=key_data["name"],
                    description=key_data["description"],
                    key_prefix=key_data["id"][:8] + "...",
                    permissions=key_data["permissions"],
                    rate_limit=key_data["rate_limit"],
                    allowed_models=key_data["allowed_models"],
                    is_active=key_data["is_active"],
                    created_at=key_data["created_at"],
                    expires_at=key_data["expires_at"],
                    last_used_at=key_data["last_used_at"],
                    usage_count=key_data["usage_count"]
                )
        return None

# Initialize API key generator
