from enum import Enum
from typing import Any, Dict, List, Optional
import os
from pydantic import BaseModel
import httpx

class ModelType(Enum):
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    AUDIO = "audio"
    EMBEDDING = "embedding"

class ModelProvider(Enum):
    MISTRAL = "mistral"
    LLAMA = "llama"
    STABLE_DIFFUSION = "stable_diffusion"
    BARK = "bark"
    INSTRUCTOR = "instructor"
    PHIND = "phind"

class AIModel(BaseModel):
    name: str
    model_type: ModelType
    provider: ModelProvider
    endpoint: str
    model_size: str
    languages: List[str] = []
    api_key: str = ""
    parameters: Dict[str, Any] = {}
    local_path: Optional[str] = None
    is_local: bool = False

class MLOpsManager:
    def __init__(self):
        self.models: Dict[str, AIModel] = {}
        self.huggingface_token = os.getenv("HUGGINGFACE_TOKEN", "")
        self._initialize_models()

    def _initialize_models(self):
        """Initialize free and open-source AI models."""
        # Text Models
        self.models["mistral"] = AIModel(
            name="mistral-7b",
            model_type=ModelType.TEXT,
            provider=ModelProvider.MISTRAL,
            model_size="7B",
            endpoint="https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
            parameters={"temperature": 0.7, "max_length": 512},
            languages=["en", "fr", "es", "de", "it"]
        )
        
        self.models["llama3"] = AIModel(
            name="llama-3-8b",
            model_type=ModelType.TEXT,
            provider=ModelProvider.LLAMA,
            model_size="8B",
            endpoint="https://api-inference.huggingface.co/models/meta-llama/Llama-2-8b-chat-hf",
            parameters={"temperature": 0.7, "max_length": 512}
        )

        # Code Models
        self.models["phind-codellama"] = AIModel(
            name="phind-codellama",
            model_type=ModelType.CODE,
            provider=ModelProvider.PHIND,
            model_size="34B",
            endpoint="https://api-inference.huggingface.co/models/Phind/Phind-CodeLlama-34B",
            parameters={"temperature": 0.1, "max_length": 1024},
            languages=["python", "javascript", "java", "cpp", "go"]
        )

        # Image Models
        self.models["stable-diffusion-xl"] = AIModel(
            name="sdxl",
            model_type=ModelType.IMAGE,
            provider=ModelProvider.STABLE_DIFFUSION,
            model_size="6.6B",
            endpoint="https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            parameters={"num_inference_steps": 30, "guidance_scale": 7.5}
        )

        # Audio Models
        self.models["bark"] = AIModel(
            name="bark",
            model_type=ModelType.AUDIO,
            provider=ModelProvider.BARK,
            model_size="1.2B",
            endpoint="https://api-inference.huggingface.co/models/suno/bark",
            parameters={"voice_preset": "v2/en_speaker_6"}
        )

        # Embedding Models
        self.models["instructor-xl"] = AIModel(
            name="instructor-xl",
            model_type=ModelType.EMBEDDING,
            provider=ModelProvider.INSTRUCTOR,
            model_size="1.3B",
            endpoint="https://api-inference.huggingface.co/models/hkunlp/instructor-xl",
            parameters={"pooling": "mean", "normalize": True}
        )

    async def query_model(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """Query an AI model with a prompt."""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        model = self.models[model_name]
        headers = {"Authorization": f"Bearer {self.huggingface_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                model.endpoint,
                headers=headers,
                json={"inputs": prompt, **model.parameters}
            )
            return response.json()

    def add_model(self, model: AIModel):
        """Add a new AI model to the manager."""
        self.models[model.name] = model

    def get_available_models(self) -> List[str]:
        """Get list of available AI models."""
        return list(self.models.keys())

    async def generate_text(self, prompt: str, model_name: str = "mistral") -> Dict[str, Any]:
        """Generate text using specified language model."""
        model = self.models.get(model_name)
        if not model or model.model_type != ModelType.TEXT:
            raise ValueError(f"Invalid text model: {model_name}")
        return await self.query_model(model_name, prompt)

    async def generate_code(self, prompt: str, language: str = "python", model_name: str = "phind-codellama") -> Dict[str, Any]:
        """Generate code using specified code model."""
        model = self.models.get(model_name)
        if not model or model.model_type != ModelType.CODE:
            raise ValueError(f"Invalid code model: {model_name}")
        
        # Add language context to prompt
        prompt = f"Generate {language} code:\n{prompt}"
        return await self.query_model(model_name, prompt)

    async def generate_image(self, prompt: str, model_name: str = "stable-diffusion-xl") -> Dict[str, Any]:
        """Generate image using specified image model."""
        model = self.models.get(model_name)
        if not model or model.model_type != ModelType.IMAGE:
            raise ValueError(f"Invalid image model: {model_name}")
        return await self.query_model(model_name, prompt)

    async def generate_speech(self, text: str, model_name: str = "bark") -> Dict[str, Any]:
        """Generate speech from text using specified audio model."""
        model = self.models.get(model_name)
        if not model or model.model_type != ModelType.AUDIO:
            raise ValueError(f"Invalid audio model: {model_name}")
        return await self.query_model(model_name, text)

    async def get_embeddings(self, texts: List[str], model_name: str = "instructor-xl") -> Dict[str, Any]:
        """Get embeddings for texts using specified embedding model."""
        model = self.models.get(model_name)
        if not model or model.model_type != ModelType.EMBEDDING:
            raise ValueError(f"Invalid embedding model: {model_name}")
        return await self.query_model(model_name, texts)

    async def run_inference_pipeline(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run a pipeline of AI tasks with different model types."""
        results = []
        for task in tasks:
            task_type = task.get("type", "text")
            model_name = task.get("model")
            input_data = task.get("input", "")
            
            try:
                if task_type == "text":
                    result = await self.generate_text(input_data, model_name)
                elif task_type == "code":
                    language = task.get("language", "python")
                    result = await self.generate_code(input_data, language, model_name)
                elif task_type == "image":
                    result = await self.generate_image(input_data, model_name)
                elif task_type == "audio":
                    result = await self.generate_speech(input_data, model_name)
                elif task_type == "embedding":
                    texts = input_data if isinstance(input_data, list) else [input_data]
                    result = await self.get_embeddings(texts, model_name)
                else:
                    raise ValueError(f"Unsupported task type: {task_type}")
                
                results.append({
                    "task": task,
                    "result": result,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "task": task,
                    "error": str(e),
                    "status": "error"
                })
        
        return results
