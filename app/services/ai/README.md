# AI Agents Service

This service provides a framework for creating and managing AI agents with different roles in the Pinnacle Copilot system.

## Architecture

The AI Agents service is built around the following key components:

1. **BaseAgent**: Abstract base class that defines the interface for all agents
2. **AgentService**: Manages the lifecycle of agents and provides a unified API for interacting with them
3. **Role-specific Agents**: Specialized agents for different tasks (e.g., CoderAgent, ReviewerAgent)
4. **LLM Integration**: Integration with language models like OpenAI's GPT-4

## Available Agents

### CoderAgent

A specialized agent for code generation, debugging, and optimization.

**Features:**
- Generate code from natural language descriptions
- Debug and fix code issues
- Optimize code for performance and readability
- Support for multiple programming languages

**Usage Example:**

```python
from services.ai.agent_service import get_agent_service
from services.ai.base_agent import AgentRole

# Get the agent service
agent_service = get_agent_service()

# Create a coder agent
agent = agent_service.create_agent(
    agent_id="coder-1",
    role=AgentRole.CODER,
    model="gpt-4",
    project_name="My Project",
    language="python"
)

# Generate some code
response = await agent.process("Create a Python function to calculate factorial")
print(response.content)
```

## API Endpoints

The following endpoints are available for interacting with agents:

- `POST /api/v1/agents/` - Create a new agent
- `POST /api/v1/agents/{agent_id}/message` - Send a message to an agent
- `GET /api/v1/agents/{agent_id}` - Get information about an agent
- `GET /api/v1/agents/` - List all active agents
- `DELETE /api/v1/agents/{agent_id}` - Delete an agent

## Configuration

Agents can be configured using environment variables:

```env
# OpenAI API Key
OPENAI_API_KEY=your-api-key

# Default model to use
DEFAULT_AI_MODEL=gpt-4

# Temperature for model responses
AI_TEMPERATURE=0.7
```

## Adding New Agent Types

To add a new agent type:

1. Create a new class that inherits from `BaseAgent`
2. Implement the required methods (primarily `process`)
3. Register the agent class with the `AgentService` in the `__init__.py` file
4. Update the API endpoints to support the new agent type

## Error Handling

All agents should handle errors gracefully and provide meaningful error messages. The `AgentResponse` class includes a `state` field that indicates whether the operation was successful or not.

## Testing

Run the tests with:

```bash
pytest tests/services/ai/
```

## Monitoring

Agent activity is logged and can be monitored using the application's logging system. Each agent maintains its own state and history, which can be useful for debugging and monitoring.

## Security Considerations

- All API endpoints require authentication
- Sensitive information should not be logged
- Rate limiting is applied to prevent abuse
- Input validation is performed on all API requests
