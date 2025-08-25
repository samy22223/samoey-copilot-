from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
import uuid

from ...services.ai.agent_service import get_agent_service, AgentService
from ...services.ai.base_agent import AgentRole, AgentState, AgentMessage
from ...services.ai.coder_agent import CoderAgent
from ...core.security import get_current_active_user
from ...models.user import User

router = APIRouter()

class AgentCreate(BaseModel):
    role: AgentRole
    model: str = "gpt-4"
    config: Optional[dict] = {}

class AgentResponse(BaseModel):
    agent_id: str
    role: AgentRole
    state: AgentState
    model: str

class MessageRequest(BaseModel):
    message: str
    agent_id: str
    config: Optional[dict] = {}

class MessageResponse(BaseModel):
    content: str
    state: AgentState

@router.post("/agents/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_active_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Create a new agent with the specified role."""
    agent_id = str(uuid.uuid4())

    # Create the appropriate agent based on role
    if agent_data.role == AgentRole.CODER:
        agent = CoderAgent(
            agent_id=agent_id,
            model=agent_data.model,
            **agent_data.config
        )
    else:
        # Add other agent types here as they're implemented
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent role not supported: {agent_data.role}"
        )

    # Register the agent with the service
    agent_service.agents[agent_id] = agent

    return {
        "agent_id": agent_id,
        "role": agent.role,
        "state": agent.state,
        "model": agent.model
    }

@router.post("/agents/{agent_id}/message", response_model=MessageResponse)
async def send_message(
    message_data: MessageRequest,
    current_user: User = Depends(get_current_active_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Send a message to an agent and get a response."""
    agent = agent_service.get_agent(message_data.agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    try:
        response = await agent.process(
            message_data.message,
            **message_data.config
        )

        return {
            "content": response.content,
            "state": response.state
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_active_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Get information about a specific agent."""
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    return {
        "agent_id": agent.agent_id,
        "role": agent.role,
        "state": agent.state,
        "model": agent.model
    }

@router.get("/agents/", response_model=List[AgentResponse])
async def list_agents(
    current_user: User = Depends(get_current_active_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """List all active agents."""
    return [
        {
            "agent_id": agent_id,
            "role": agent.role,
            "state": agent.state,
            "model": agent.model
        }
        for agent_id, agent in agent_service.agents.items()
    ]

@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_active_user),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Delete an agent."""
    if not agent_service.remove_agent(agent_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    return None
