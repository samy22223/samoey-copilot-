"""
AI Agents for Pinnacle Copilot

This module provides a framework for creating and managing AI agents with different roles.
"""

from .base_agent import (
    BaseAgent,
    AgentRole,
    AgentState,
    AgentMessage,
    AgentResponse
)
from .agent_service import AgentService, get_agent_service
from .coder_agent import CoderAgent

# Register agent types with the agent service
agent_service = get_agent_service()
agent_service.register_agent(AgentRole.CODER, CoderAgent)

__all__ = [
    'BaseAgent',
    'AgentRole',
    'AgentState',
    'AgentMessage',
    'AgentResponse',
    'AgentService',
    'get_agent_service',
    'CoderAgent',
]
