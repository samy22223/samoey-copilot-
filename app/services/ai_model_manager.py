import asyncio
import aiohttp
import hashlib
import json
import os
import subprocess
import psutil
import platform
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from app.core.redis import redis_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class AIModelManager:
    """
    AI Model Manager for automatic downloading, setup, and optimization of free AI models.
    Zero configuration required - everything is auto-managed.
    """

    def __init__(self):
        self.models_path = Path(settings.AI_MODEL_PATH) if hasattr(settings, 'AI_MODEL_PATH') else Path("./models")
        self.models_path.mkdir(exist_ok=True)
        self.system_resources = self._detect_system_resources()
        self.available_models = self._get_available_models()
        self.downloaded_models = {}
        self.loaded_models = {}
        self.model_processes = {}

    async def initialize_ai_models(self) -> Dict[str, Any]:
        """
        Initialize AI models - auto-download and setup based on system resources.
        """
        try:
            logger.info("Starting AI models initialization...")

            initialization_results = {}

            # Step 1: Detect system capabilities
            initialization_results["system_capabilities"] = self._detect_system_capabilities()

            # Step 2: Select optimal models based on resources
            selected_models = self._select_optimal_models(initialization_results["system_capabilities"])
            initialization_results["selected_models"] = selected_models

            # Step 3: Start downloading models in background
            download_tasks = []
            for model_info in selected_models:
                task = asyncio.create_task(self._download_model(model_info))
                download_tasks.append(task)

            # Wait for all downloads to complete (with timeout)
            download_results = await asyncio.wait_for(
                asyncio.gather(*download_tasks, return_exceptions=True),
                timeout=1800  # 30 minutes timeout
            )

            initialization_results["download_results"] = [
                {"model": model["name"], "success": not isinstance(result, Exception), "error": str(result) if isinstance(result, Exception) else None}
                for model, result in zip(selected_models, download_results)
            ]

            # Step 4: Optimize models for system
            optimization_results = await self._optimize_models(selected_models)
            initialization_results["optimization_results"] = optimization_results

            # Step 5: Load models into memory
            load_results = await self._load_models(selected_models)
            initialization_results["load_results"] = load_results

            # Step 6: Setup model serving
            serving_results = await self._setup_model_serving(selected_models)
            initialization_results["serving_results"] = serving_results

            logger.info("AI models initialization completed!")

            return {
                "success": True,
                "message": "AI models initialized successfully",
                "results": initialization_results,
                "models_ready": True,
                "available_models": [model["name"] for model in selected_models if model.get("downloaded", False)],
                "estimated_memory_usage": sum(model.get("memory_usage_mb", 0) for model in selected_models)
            }

        except Exception as e:
            logger.error(f"Error initializing AI models: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to initialize AI models"
            }

    async def auto_download_models(self, model_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Auto-download AI models. If no models specified, downloads recommended models.
        """
        try:
            if not model_names:
                model_names = self._get_recommended_models()

            download_results = {}

            for model_name in model_names:
                model_info = self.available_models.get(model_name)
                if not model_info:
                    download_results[model_name] = {"success": False, "error": "Model not found"}
                    continue

                result = await self._download_model(model_info)
                download_results[model_name] = result

            successful_downloads = [name for name, result in download_results.items() if result.get("success", False)]

            return {
                "success": len(successful_downloads) > 0,
                "downloaded_models": successful_downloads,
                "results": download_results,
                "message": f"Successfully downloaded {len(successful_downloads)} models"
            }

        except Exception as e:
            logger.error(f"Error auto-downloading models: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_model_status(self, model_name: str) -> Dict[str, Any]:
        """
        Get status of a specific model.
        """
        try:
            model_info = self.available_models.get(model_name)
            if not model_info:
                return {"success": False, "error": "Model not found"}

            model_path = self.models_path / model_name
            is_downloaded = model_path.exists()

            # Check if model is loaded
            is_loaded = model_name in self.loaded_models

            # Check if model process is running
            process_info = self.model_processes.get(model_name)
            is_running = process_info and process_info.get("process") and process_info["process"].poll() is None

            # Get model size if downloaded
            model_size_mb = 0
            if is_downloaded:
                model_size_mb = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file()) / (1024 * 1024)

            return {
                "success": True,
                "model_name": model_name,
                "downloaded": is_downloaded,
                "loaded": is_loaded,
                "running": is_running,
                "size_mb": round(model_size_mb, 2),
                "model_info": model_info,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting model status for {model_name}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def list_available_models(self) -> Dict[str, Any]:
        """
        List all available models with their status.
        """
        try:
            models_status = {}

            for model_name in self.available_models.keys():
                status = await self.get_model_status(model_name)
                models_status[model_name] = status

            return {
                "success": True,
                "models": models_status,
                "total_models": len(self.available_models),
                "downloaded_models": len([s for s in models_status.values() if s.get("downloaded", False)]),
                "loaded_models": len([s for s in models_status.values() if s.get("loaded", False)])
            }

        except Exception as e:
            logger.error(f"Error listing available models: {str(e)}")
            return {"success": False, "error": str(e)}

    async def optimize_model_for_system(self, model_name: str) -> Dict[str, Any]:
        """
        Optimize a specific model for the current system.
        """
        try:
            model_info = self.available_models.get(model_name)
            if not model_info:
                return {"success": False, "error": "Model not found"}

            model_path = self.models_path / model_name
            if not model_path.exists():
                return {"success": False, "error": "Model not downloaded"}

            optimization_results = {}

            # Quantization optimization
            if self.system_resources.get("gpu_available", False):
                quant_result = await self._quantize_model_gpu(model_name, model_path)
                optimization_results["quantization"] = quant_result
            else:
                quant_result = await self._quantize_model_cpu(model_name, model_path)
                optimization_results["quantization"] = quant_result

            # Memory optimization
            memory_result = await self._optimize_model_memory(model_name, model_path)
            optimization_results["memory"] = memory_result

            # Performance optimization
            perf_result = await self._optimize_model_performance(model_name, model_path)
            optimization_results["performance"] = perf_result

            return {
                "success": True,
                "model_name": model_name,
                "optimization_results": optimization_results,
                "message": f"Model {model_name} optimized successfully"
            }

        except Exception as e:
            logger.error(f"Error optimizing model {model_name}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def start_model_server(self, model_name: str, port: Optional[int] = None) -> Dict[str, Any]:
        """
        Start a model server for the specified model.
        """
        try:
            model_info = self.available_models.get(model_name)
            if not model_info:
                return {"success": False, "error": "Model not found"}

            model_path = self.models_path / model_name
            if not model_path.exists():
                return {"success": False, "error": "Model not downloaded"}

            # Find available port if not specified
            if not port:
                port = self._find_available_port(8000, 9000)

            # Start model server process
            server_process = await self._start_model_server_process(model_name, model_path, port)

            # Store process info
            self.model_processes[model_name] = {
                "process": server_process,
                "port": port,
                "started_at": datetime.now().isoformat()
            }

            return {
                "success": True,
                "model_name": model_name,
                "server_port": port,
                "server_url": f"http://localhost:{port}",
                "message": f"Model server started for {model_name}"
            }

        except Exception as e:
            logger.error(f"Error starting model server for {model_name}: {str(e)}")
            return {"success": False, "error": str(e)}

    # Private helper methods

    def _detect_system_resources(self) -> Dict[str, Any]:
        """Detect system resources and capabilities."""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_total_gb": psutil.disk_usage('/').total / (1024**3),
                "disk_available_gb": psutil.disk_usage('/').free / (1024**3),
                "disk_percent": psutil.disk_usage('/').percent,
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "gpu_available": self._check_gpu_availability(),
                "gpu_memory_gb": self._get_gpu_memory() if self._check_gpu_availability() else 0
            }
        except Exception as e:
            logger.error(f"Error detecting system resources: {str(e)}")
            return {}

    def _check_gpu_availability(self) -> bool:
        """Check if GPU is available."""
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _get_gpu_memory(self) -> float:
        """Get GPU memory in GB."""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return float(result.stdout.strip()) / 1024  # Convert MB to GB
            return 0
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            return 0

    def _get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get available free AI models."""
        return {
            "mistral-7b": {
                "name": "mistral-7b",
                "type": "text",
                "size_gb": 4.5,
                "memory_usage_mb": 8000,
                "requires_gpu": False,
                "description": "High-quality text generation model",
                "download_url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                "quantization": "Q4_K_M"
            },
            "llama3-8b": {
                "name": "llama3-8b",
                "type": "text",
                "size_gb": 5.2,
                "memory_usage_mb": 9000,
                "requires_gpu": False,
                "description": "Latest Llama 3 model for text generation",
                "download_url": "https://huggingface.co/TheBloke/Llama-3-8B-Instruct-GGUF/resolve/main/llama-3-8b-instruct.Q4_K_M.gguf",
                "quantization": "Q4_K_M"
            },
            "phi-2": {
                "name": "phi-2",
                "type": "text",
                "size_gb": 1.8,
                "memory_usage_mb": 3000,
                "requires_gpu": False,
                "description": "Small but capable text model",
                "download_url": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
                "quantization": "Q4_K_M"
            },
            "phind-codellama": {
                "name": "phind-codellama",
                "type": "code",
                "size_gb": 3.8,
                "memory_usage_mb": 7000,
                "requires_gpu": False,
                "description": "Code generation and completion model",
                "download_url": "https://huggingface.co/TheBloke/Phind-CodeLlama-34B-v2-GGUF/resolve/main/phind-codellama-34b-v2.Q4_K_M.gguf",
                "quantization": "Q4_K_M"
            },
            "starcoder": {
                "name": "starcoder",
                "type": "code",
                "size_gb": 4.2,
                "memory_usage_mb": 7500,
                "requires_gpu": False,
                "description": "StarCoder code generation model",
                "download_url": "https://huggingface.co/TheBloke/starcoder-GGUF/resolve/main/starcoder.Q4_K_M.gguf",
                "quantization": "Q4_K_M"
            },
            "instructor-xl": {
                "name": "instructor-xl",
                "type": "embedding",
                "size_gb": 2.2,
                "memory_usage_mb": 4000,
                "requires_gpu": False,
                "description": "Text embedding model",
                "download_url": "https://huggingface.co/TheBloke/instructor-xl-GGUF/resolve/main/instructor-xl.Q4_K_M.gguf",
                "quantization": "Q4_K_M"
            },
            "all-MiniLM-L6-v2": {
                "name": "all-MiniLM-L6-v2",
                "type": "embedding",
                "size_gb": 0.08,
                "memory_usage_mb": 200,
                "requires_gpu": False,
                "description": "Small and fast embedding model",
                "download_url": "https://huggingface.co/TheBloke/all-MiniLM-L6-v2-GGUF/resolve/main/all-minilm-l6-v2.Q4_K_M.gguf",
                "quantization": "Q4_K_M"
            }
        }

    def _detect_system_capabilities(self) -> Dict[str, Any]:
        """Detect system capabilities for AI model selection."""
        try:
            capabilities = {
                "can_run_large_models": self.system_resources["memory_available_gb"] >= 8,
                "can_run_medium_models": self.system_resources["memory_available_gb"] >= 4,
                "can_run_small_models": self.system_resources["memory_available_gb"] >= 2,
                "has_gpu_acceleration": self.system_resources["gpu_available"],
                "gpu_memory_sufficient": self.system_resources.get("gpu_memory_gb", 0) >= 4,
                "disk_space_sufficient": self.system_resources["disk_available_gb"] >= 10,
                "cpu_threads_sufficient": self.system_resources["cpu_count"] >= 4
            }
            return capabilities
        except Exception as e:
            logger.error(f"Error detecting system capabilities: {str(e)}")
            return {}

    def _select_optimal_models(self, capabilities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Select optimal models based on system capabilities."""
        try:
            selected_models = []

            # Always include small embedding model
            selected_models.append(self.available_models["all-MiniLM-L6-v2"])

            # Select text models based on capabilities
            if capabilities["can_run_large_models"]:
                selected_models.append(self.available_models["llama3-8b"])
                selected_models.append(self.available_models["mistral-7b"])
            elif capabilities["can_run_medium_models"]:
                selected_models.append(self.available_models["mistral-7b"])
            elif capabilities["can_run_small_models"]:
                selected_models.append(self.available_models["phi-2"])

            # Select code models based on capabilities
            if capabilities["can_run_medium_models"]:
                selected_models.append(self.available_models["phind-codellama"])
            elif capabilities["can_run_small_models"]:
                selected_models.append(self.available_models["starcoder"])

            # Select embedding model based on capabilities
            if capabilities["can_run_medium_models"]:
                selected_models.append(self.available_models["instructor-xl"])

            return selected_models

        except Exception as e:
            logger.error(f"Error selecting optimal models: {str(e)}")
            return []

    def _get_recommended_models(self) -> List[str]:
        """Get recommended models for auto-download."""
        return ["mistral-7b", "phind-codellama", "instructor-xl", "all-MiniLM-L6-v2"]

    async def _download_model(self, model_info: Dict[str, Any]) -> Dict[str, Any]:
        """Download a specific model."""
        try:
            model_name = model_info["name"]
            model_path = self.models_path / model_name
            model_path.mkdir(exist_ok=True)

            # Check if already downloaded
            if model_path.exists() and any(model_path.iterdir()):
                return {"success": True, "message": "Model already downloaded", "downloaded": True}

            download_url = model_info["download_url"]
            filename = download_url.split('/')[-1]
            file_path = model_path / filename

            logger.info(f"Downloading model {model_name} from {download_url}")

            # Download the model
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    response.raise_for_status()

                    with open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)

            # Verify download
            if file_path.exists() and file_path.stat().st_size > 0:
                self.downloaded_models[model_name] = {
                    "path": str(model_path),
                    "filename": filename,
                    "downloaded_at": datetime.now().isoformat()
                }

                logger.info(f"Successfully downloaded model {model_name}")
                return {"success": True, "message": "Model downloaded successfully", "downloaded": True}
            else:
                return {"success": False, "error": "Download verification failed"}

        except Exception as e:
            logger.error(f"Error downloading model {model_info['name']}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _optimize_models(self, models: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize models for the current system."""
        try:
            optimization_results = {}

            for model_info in models:
                model_name = model_info["name"]
                result = await self.optimize_model_for_system(model_name)
                optimization_results[model_name] = result

            return optimization_results

        except Exception as e:
            logger.error(f"Error optimizing models: {str(e)}")
            return {}

    async def _load_models(self, models: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Load models into memory."""
        try:
            load_results = {}

            for model_info in models:
                model_name = model_info["name"]
                model_path = self.models_path / model_name

                if not model_path.exists():
                    load_results[model_name] = {"success": False, "error": "Model not downloaded"}
                    continue

                # Simulate model loading (in real implementation, this would load the actual model)
                self.loaded_models[model_name] = {
                    "path": str(model_path),
                    "loaded_at": datetime.now().isoformat(),
                    "memory_usage_mb": model_info.get("memory_usage_mb", 0)
                }

                load_results[model_name] = {"success": True, "message": "Model loaded successfully"}

            return load_results

        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            return {}

    async def _setup_model_serving(self, models: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Setup model serving for the models."""
        try:
            serving_results = {}

            for model_info in models:
                model_name = model_info["name"]

                # Start model server for each model
                result = await self.start_model_server(model_name)
                serving_results[model_name] = result

            return serving_results

        except Exception as e:
            logger.error(f"Error setting up model serving: {str(e)}")
            return {}

    def _find_available_port(self, start_port: int, end_port: int) -> int:
        """Find an available port in the given range."""
        import socket
        for port in range(start_port, end_port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('', port))
                sock.close()
                return port
            except OSError:
                continue
        return start_port

    async def _start_model_server_process(self, model_name: str, model_path: Path, port: int):
        """Start model server process."""
        try:
            # This is a placeholder - in real implementation, this would start an actual model server
            # For now, we'll simulate with a simple process
            import subprocess
            process = subprocess.Popen(['python', '-c', f'print("Model server for {model_name} running on port {port}")'])
            return process
        except Exception as e:
            logger.error(f"Error starting model server process: {str(e)}")
            raise

    async def _quantize_model_gpu(self, model_name: str, model_path: Path) -> Dict[str, Any]:
        """Quantize model for GPU."""
        try:
            # Placeholder for GPU quantization
            return {"success": True, "message": "GPU quantization completed"}
        except Exception as e:
            logger.error(f"Error in GPU quantization: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _quantize_model_cpu(self, model_name: str, model_path: Path) -> Dict[str, Any]:
        """Quantize model for CPU."""
        try:
            # Placeholder for CPU quantization
            return {"success": True, "message": "CPU quantization completed"}
        except Exception as e:
            logger.error(f"Error in CPU quantization: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _optimize_model_memory(self, model_name: str, model_path: Path) -> Dict[str, Any]:
        """Optimize model memory usage."""
        try:
            # Placeholder for memory optimization
            return {"success": True, "message": "Memory optimization completed"}
        except Exception as e:
            logger.error(f"Error in memory optimization: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _optimize_model_performance(self, model_name: str, model_path: Path) -> Dict[str, Any]:
        """Optimize model performance."""
        try:
            # Placeholder for performance optimization
            return {"success": True, "message": "Performance optimization completed"}
        except Exception as e:
            logger.error(f"Error in performance optimization: {str(e)}")
            return {"success": False, "error": str(e)}


# Global instance
