from typing import Dict, Any, Optional
import logging
from ..core.config import settings
from .base_agent import BaseAgent, AgentRole, AgentState, AgentMessage, AgentResponse
from ..llm.openai_client import get_openai_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert software engineer with deep knowledge of multiple programming languages and frameworks. 
Your role is to help users write, debug, and improve code. Follow these guidelines:

1. Write clean, efficient, and well-documented code
2. Follow best practices and coding standards for the given language/framework
3. Provide clear explanations for your code
4. Suggest improvements and optimizations
5. Be precise and concise in your responses
6. If you're not sure about something, say so rather than making assumptions

Current project context:
- Project: {project_name}
- Language: {language}
- Framework: {framework}
"""

class CoderAgent(BaseAgent):
    """AI agent specialized in code generation and editing."""
    
    def __init__(self, 
                 agent_id: str, 
                 model: str = "gpt-4",
                 project_name: str = "Unnamed Project",
                 language: str = "python",
                 framework: str = ""):
        """Initialize the coder agent.
        
        Args:
            agent_id: Unique identifier for the agent
            model: The AI model to use
            project_name: Name of the current project
            language: Primary programming language
            framework: Framework being used (if any)
        """
        super().__init__(agent_id, AgentRole.CODER, model)
        self.project_name = project_name
        self.language = language
        self.framework = framework
        self.llm = get_openai_client()
    
    async def process(self, message: str, **kwargs) -> AgentResponse:
        """Process a coding-related message."""
        # Add the user's message to history
        user_message = AgentMessage(role="user", content=message)
        self.add_to_history(user_message)
        
        # Prepare the conversation history for the LLM
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(
                    project_name=self.project_name,
                    language=self.language,
                    framework=self.framework
                )
            }
        ]
        
        # Add conversation history
        for msg in self.get_history():
            messages.append({"role": msg.role, "content": msg.content})
        
        try:
            # Call the LLM
            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract the response
            assistant_message = response.choices[0].message.content
            
            # Add the assistant's response to history
            self.add_to_history(AgentMessage(role="assistant", content=assistant_message))
            
            return AgentResponse(
                content=assistant_message,
                state=AgentState.COMPLETED
            )
            
        except Exception as e:
            logger.error(f"Error in CoderAgent: {str(e)}", exc_info=True)
            self.set_state(AgentState.ERROR)
            return AgentResponse(
                content=f"An error occurred: {str(e)}",
                state=AgentState.ERROR
            )
    
    async def generate_code(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate code based on the given task and context."""
        prompt = f"Task: {task}\n\n"
        
        if context:
            prompt += "Context:\n"
            for key, value in context.items():
                prompt += f"- {key}: {value}\n"
        
        response = await self.process(prompt)
        return response.content
    
    async def debug_code(self, code: str, error: Optional[str] = None) -> str:
        """Debug the given code and fix any issues."""
        prompt = f"Debug the following code"
        if error:
            prompt += f" which is producing this error: {error}"
        prompt += f":\n\n```{self.language}\n{code}\n```"
        
        response = await self.process(prompt)
        return response.content
    
    async def optimize_code(self, code: str, requirements: str = "") -> str:
        """Optimize the given code based on requirements."""
        prompt = "Optimize the following code"
        if requirements:
            prompt += f" with these requirements: {requirements}"
        prompt += f":\n\n```{self.language}\n{code}\n```"
        
        response = await self.process(prompt)
        return response.content
