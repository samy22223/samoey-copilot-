from typing import Dict, List, Optional, Type, Any
import logging
from ..core.config import settings
from .base_agent import BaseAgent, AgentRole, AgentState, AgentMessage, AgentResponse

logger = logging.getLogger(__name__)

class AgentService:
    """Service for managing AI agents."""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_registry: Dict[AgentRole, Type[BaseAgent]] = {}
    
    def register_agent(self, role: AgentRole, agent_class: Type[BaseAgent]) -> None:
        """Register an agent class for a specific role."""
        self.agent_registry[role] = agent_class
        logger.info(f"Registered agent class {agent_class.__name__} for role {role}")
    
    def create_agent(self, agent_id: str, role: AgentRole, **kwargs) -> BaseAgent:
        """Create a new agent instance."""
        if role not in self.agent_registry:
            raise ValueError(f"No agent registered for role: {role}")
        
        agent_class = self.agent_registry[role]
        agent = agent_class(agent_id=agent_id, role=role, **kwargs)
        self.agents[agent_id] = agent
        
        logger.info(f"Created agent {agent_id} with role {role}")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Removed agent {agent_id}")
            return True
        return False
    
    async def process_message(
        self, 
        agent_id: str, 
        message: str, 
        **kwargs
    ) -> AgentResponse:
        """Process a message with the specified agent."""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        try:
            agent.set_state(AgentState.PROCESSING)
            response = await agent.process(message, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Error processing message with agent {agent_id}: {str(e)}", exc_info=True)
            agent.set_state(AgentState.ERROR)
            raise
        finally:
            if agent.get_state() != AgentState.ERROR:
                agent.set_state(AgentState.IDLE)
    
    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get the current state of an agent."""
        agent = self.get_agent(agent_id)
        return agent.get_state() if agent else None
    
    def get_agent_history(self, agent_id: str) -> List[AgentMessage]:
        """Get the conversation history of an agent."""
        agent = self.get_agent(agent_id)
        return agent.get_history() if agent else []
    
    def clear_agent_history(self, agent_id: str) -> bool:
        """Clear the conversation history of an agent."""
        agent = self.get_agent(agent_id)
        if agent:
            agent.clear_history()
            return True
        return False

# Global instance of the agent service
agent_service = AgentService()

def get_agent_service() -> AgentService:
    """Get the global agent service instance."""
    return agent_service
