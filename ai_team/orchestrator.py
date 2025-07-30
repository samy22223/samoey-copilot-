from typing import List, Dict, Any
import asyncio
from pydantic import BaseModel
from .team import AITeam, TeamRole

class Task(BaseModel):
    name: str
    description: str
    assigned_role: TeamRole
    dependencies: List[str] = []
    status: str = "pending"
    artifacts: Dict[str, Any] = {}

class AIOrchestrator:
    def __init__(self):
        self.team = AITeam()
        self.tasks: List[Task] = []
        self.current_phase: str = "planning"

    async def execute_phase(self, phase_name: str, tasks: List[Task]):
        """Execute a project phase with multiple tasks."""
        self.current_phase = phase_name
        running_tasks = []
        
        for task in tasks:
            self.team.assign_task(task.assigned_role, task.name)
            running_tasks.append(self.execute_task(task))
        
        return await asyncio.gather(*running_tasks)

    async def execute_task(self, task: Task):
        """Execute a single task."""
        # Check dependencies
        for dep in task.dependencies:
            dep_task = next((t for t in self.tasks if t.name == dep), None)
            if dep_task and dep_task.status != "completed":
                raise ValueError(f"Dependency {dep} not completed for task {task.name}")

        # Simulate AI agent working on task
        await asyncio.sleep(1)  # Simulated work
        task.status = "completed"
        return task

    def create_project_plan(self) -> List[Dict[str, Any]]:
        """Generate a project plan with phases and tasks."""
        return [
            {
                "phase": "Planning",
                "tasks": [
                    {"name": "Architecture Design", "role": TeamRole.ARCHITECT},
                    {"name": "Tech Stack Selection", "role": TeamRole.ARCHITECT},
                    {"name": "Project Setup", "role": TeamRole.BACKEND_DEV}
                ]
            },
            {
                "phase": "Development",
                "tasks": [
                    {"name": "Database Schema", "role": TeamRole.BACKEND_DEV},
                    {"name": "API Development", "role": TeamRole.BACKEND_DEV},
                    {"name": "UI Components", "role": TeamRole.FRONTEND_DEV},
                    {"name": "AI Integration", "role": TeamRole.MLOPS}
                ]
            },
            {
                "phase": "Testing",
                "tasks": [
                    {"name": "Unit Tests", "role": TeamRole.QA},
                    {"name": "Integration Tests", "role": TeamRole.QA},
                    {"name": "Security Audit", "role": TeamRole.QA}
                ]
            }
        ]

    def get_team_status(self) -> Dict[str, List[str]]:
        """Get current status of all team members and their tasks."""
        return self.team.get_team_status()
