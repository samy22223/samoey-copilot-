"""
Routes for AI team management and orchestration
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any
from ..ai_team.orchestrator import AIOrchestrator
from ..ai_team.team import TeamRole
from ..ai_team.mlops import MLOpsManager

router = APIRouter()
orchestrator = AIOrchestrator()
mlops = MLOpsManager()

@router.get("/team/status")
async def get_team_status() -> Dict[str, List[str]]:
    """Get current status of all AI team members."""
    return orchestrator.get_team_status()

@router.post("/project/plan")
async def create_project_plan() -> List[Dict[str, Any]]:
    """Generate a new project plan."""
    return orchestrator.create_project_plan()

@router.get("/ai/models")
async def list_ai_models() -> List[str]:
    """List available AI models."""
    return mlops.get_available_models()

@router.post("/ai/inference")
async def run_inference(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run AI inference tasks."""
    try:
        return await mlops.run_inference_pipeline(tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/task/execute")
async def execute_task(task_data: Dict[str, Any]):
    """Execute a specific task with the AI team."""
    try:
        task = {
            "name": task_data["name"],
            "description": task_data.get("description", ""),
            "assigned_role": TeamRole[task_data["role"]],
            "dependencies": task_data.get("dependencies", [])
        }
        return await orchestrator.execute_task(task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
