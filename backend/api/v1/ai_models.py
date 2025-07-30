from typing import List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from ..ai_team.mlops import MLOpsManager, ModelType

router = APIRouter()
mlops_manager = MLOpsManager()

class ModelInfo(BaseModel):
    name: str
    type: str
    provider: str
    model_size: str
    languages: List[str] = []
    is_local: bool = False

class GenerationRequest(BaseModel):
    model_name: str
    input_data: Any
    parameters: Dict[str, Any] = {}
    language: str = "python"  # For code generation

@router.get("/models")
async def list_models() -> Dict[str, List[ModelInfo]]:
    """List all available AI models by type."""
    models_by_type = {}
    for model_name, model in mlops_manager.models.items():
        model_type = model.model_type.value
        if model_type not in models_by_type:
            models_by_type[model_type] = []
            
        models_by_type[model_type].append(ModelInfo(
            name=model.name,
            type=model.model_type.value,
            provider=model.provider.value,
            model_size=model.model_size,
            languages=model.languages,
            is_local=model.is_local
        ))
    return models_by_type

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
        return await mlops_manager.get_embeddings(texts, request.model_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
