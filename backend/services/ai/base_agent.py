from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from pydantic import BaseModel
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AgentRole(str, Enum):
    """Defines the role of an agent in the system."""
    CODER = "coder"
    REVIEWER = "reviewer"
    ARCHITECT = "architect"
    TESTER = "tester"
    SECURITY = "security"
    MANAGER = "manager"

class AgentState(str, Enum):
    """Defines the state of an agent."""
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    COMPLETED = "completed"

class AgentMessage(BaseModel):
    """A message in the conversation with an agent."""
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    """Response from an agent."""
    content: str
    metadata: Optional[Dict[str, Any]] = None
    state: AgentState = AgentState.COMPLETED

class BaseAgent(ABC):
    """Base class for all AI agents."""
    
    def __init__(self, 
                 agent_id: str, 
                 role: AgentRole, 
                 model: str = "gpt-4"):
        """Initialize the agent.
        
        Args:
            agent_id: Unique identifier for the agent
            role: The role this agent plays in the system
            model: The AI model to use for this agent
        """
        self.agent_id = agent_id
        self.role = role
        self.model = model
        self.state = AgentState.IDLE
        self.history: List[AgentMessage] = []
    
    @abstractmethod
    async def process(self, message: str, **kwargs) -> AgentResponse:
        """Process a message and return a response.
        
        Args:
            message: The message to process
            **kwargs: Additional arguments specific to the agent
            
        Returns:
            AgentResponse: The agent's response
        """
        pass
    
    def add_to_history(self, message: AgentMessage) -> None:
        """Add a message to the agent's conversation history."""
        self.history.append(message)
    
    def clear_history(self) -> None:
        """Clear the agent's conversation history."""
        self.history = []
    
    def get_history(self) -> List[AgentMessage]:
        """Get the agent's conversation history."""
        return self.history.copy()
    
    def set_state(self, state: AgentState) -> None:
        """Set the agent's state."""
        self.state = state
        logger.info(f"Agent {self.agent_id} state changed to {state}")
    
    def get_state(self) -> AgentState:
        """Get the agent's current state."""
        return self.state
