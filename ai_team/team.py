from typing import List, Dict
from enum import Enum
from pydantic import BaseModel

class TeamRole(Enum):
    ARCHITECT = "AI Chief Architect"
    FRONTEND_DEV = "Frontend Developer"
    BACKEND_DEV = "Backend Developer"
    FULLSTACK_DEV = "Full-Stack Developer"
    MLOPS = "MLOps & AI Engineer"
    QA = "QA & Security Agent"
    PRODUCT_MANAGER = "Product Manager"
    UI_DESIGNER = "UI/UX Designer"
    GROWTH_HACKER = "Growth Hacker"
    DOCUMENTATION = "Documentation Agent"

class TeamMember(BaseModel):
    role: TeamRole
    specialization: List[str]
    tasks: List[str]
    tools: List[str]

class AITeam:
    def __init__(self):
        self.members: Dict[TeamRole, TeamMember] = self._initialize_team()

    def _initialize_team(self) -> Dict[TeamRole, TeamMember]:
        return {
            TeamRole.ARCHITECT: TeamMember(
                role=TeamRole.ARCHITECT,
                specialization=["System Design", "Tech Stack Selection", "Architecture Planning"],
                tasks=["Design System Architecture", "Select Technologies", "Plan Integration"],
                tools=["CrewAI", "AutoGen", "LLaMA 3"]
            ),
            TeamRole.FRONTEND_DEV: TeamMember(
                role=TeamRole.FRONTEND_DEV,
                specialization=["Next.js", "React", "TailwindCSS"],
                tasks=["Build UI Components", "Implement Frontend Logic", "Optimize Performance"],
                tools=["Next.js", "React", "TailwindCSS", "TypeScript"]
            ),
            TeamRole.BACKEND_DEV: TeamMember(
                role=TeamRole.BACKEND_DEV,
                specialization=["FastAPI", "SQLAlchemy", "Redis"],
                tasks=["Build APIs", "Database Design", "Cache Implementation"],
                tools=["FastAPI", "SQLAlchemy", "Redis", "PostgreSQL"]
            ),
            TeamRole.MLOPS: TeamMember(
                role=TeamRole.MLOPS,
                specialization=["AI Integration", "Model Deployment", "Performance Optimization"],
                tasks=["Deploy AI Models", "Optimize AI Performance", "Monitor AI Systems"],
                tools=["Hugging Face", "LLaMA 3", "PyTorch"]
            ),
            TeamRole.QA: TeamMember(
                role=TeamRole.QA,
                specialization=["Testing", "Security", "Quality Assurance"],
                tasks=["Run Tests", "Security Audits", "Performance Testing"],
                tools=["PyTest", "Jest", "GitHub Actions"]
            )
        }

    def get_team_member(self, role: TeamRole) -> TeamMember:
        return self.members.get(role)

    def assign_task(self, role: TeamRole, task: str):
        if member := self.members.get(role):
            member.tasks.append(task)

    def get_team_status(self) -> Dict[str, List[str]]:
        return {str(role): member.tasks for role, member in self.members.items()}
